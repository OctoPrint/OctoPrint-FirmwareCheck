__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2019 The OctoPrint Project - Released under terms of the AGPLv3 License"

from flask_babel import gettext
from octoprint.util.version import get_comparable_version

from . import AuthorCheck, Check, NegativeCapCheck, Severity


class FirmwareUnsafeChecks:
    @classmethod
    def as_dict(cls):
        return {
            "checks": (
                AnetA8Check(),
                AnycubicCheck(),
                CrealityCR10sCheck(),
                CrealityEnder3Check(),
                FlashforgeVoxelabAquilaCheck(),
                MalyanM200Check(),
                Micro3DIMECheck(),
                Micro3DStockCheck(),
                RepetierBefore092Check(),
                ThermalProtectionCapCheck(),
            ),
            "message": gettext(
                "Your printer's firmware is known to lack mandatory safety features (e.g. "
                "thermal runaway protection). This is a fire risk."
            ),
            "severity": Severity.CRITICAL,
        }


class AnetA8Check(Check):
    """
    Anet A8 stock firmware

    Identified through firmware name "ANET_A8_".
    """

    name = "anet_a8"

    def m115(self, name, data):
        self._triggered = name and name.lower().startswith("anet_a8_")
        self._active = False


class AnycubicCheck(Check):
    """
    Anycubic MEGA stock firmware

    Identified through "Author: (Jolly, xxxxxxxx.CO.)" or "| Author: (**Jolly, xxxxxxxx.CO.**)" in startup messages
    combined with "echo:Vx.y.z" in startup messages, with x.y.z < 1.1.2.
    """

    name = "anycubic"

    AUTHOR = "| Author: ".lower()
    VERSION = "echo:V"

    CRITICAL_AUTHOR1 = "| Author: (Jolly, xxxxxxxx.CO.)".lower()
    CRITICAL_AUTHOR2 = "| Author: (**Jolly, xxxxxxxx.CO.**)".lower()

    FIXED_VERSION = get_comparable_version("1.1.2")

    def __init__(self):
        Check.__init__(self)
        self._author_matches = None
        self._version_matches = None

    def m115(self, name, data):
        # make sure we stop scanning once we see the response to M115
        if self._author_matches is None:
            self._author_matches = False
        if self._version_matches is None:
            self._version_matches = False
        self._evaluate()

    def received(self, line):
        if not line:
            return

        lower_line = line.lower()
        if self.AUTHOR in lower_line:
            self._author_matches = (
                self.CRITICAL_AUTHOR1 in lower_line or self.CRITICAL_AUTHOR2 in lower_line
            )
        elif line.startswith(self.VERSION):
            self._version_matches = self._broken_version(line)
        else:
            return

        self._evaluate()

    def _broken_version(self, line):
        version_str = line[len(self.VERSION) :]
        try:
            version = get_comparable_version(version_str, base=True)
        except Exception:
            version = None

        if version is not None and version < self.FIXED_VERSION:
            return True
        else:
            return False

    def _evaluate(self):
        if self._author_matches is None or self._version_matches is None:
            return
        self._triggered = self._author_matches and self._version_matches
        self._active = False

    def reset(self):
        Check.reset(self)
        self._author_matches = None
        self._version_matches = None


class CrealityCR10sCheck(AuthorCheck):
    """
    Creality CR10s

    Identified through " | Author: (CR-10Slanguage)" in startup messages.
    """

    name = "creality_cr10s"
    authors = (" | Author: (CR-10Slanguage)".lower(),)


class CrealityEnder3Check(AuthorCheck):
    """
    Creality Ender3

    Identified through " | Author: (Ender3)" in startup messages.
    """

    name = "creality_ender3"
    authors = (" | Author: (Ender3)".lower(),)


class FlashforgeVoxelabAquilaCheck(Check):
    """
    Flashforge Voxelab Aquila stock firmware

    Identified through "MACHINE_TYPE:Voxlab-1 V1" (sic!) in M115 response.
    """

    name = "flashforge_voxelab_aquila"
    MACHINE_TYPE = "Voxlab-1 V1"  # sic!

    def m115(self, name, data):
        self._triggered = data.get("MACHINE_TYPE") == self.MACHINE_TYPE
        self._active = False


class MalyanM200Check(Check):
    """
    Malyan M200 stock firmware prior to version 4.0

    Identified through firmware name "Malyan*", model "M200" and version < 4.0.
    """

    name = "malyan_m200"

    FIXED_VERSION = get_comparable_version("4.0")

    def m115(self, name, data):
        try:
            version = get_comparable_version(data.get("VER", "0"))
        except Exception:
            version = None

        self._triggered = (
            name
            and name.lower().startswith("malyan")
            and data.get("MODEL") == "M200"
            and version is not None
            and version < self.FIXED_VERSION
        )
        self._active = False


class Micro3DIMECheck(Check):
    """
    Micro3D with IME firmware

    Identified through firmware name "iME*".
    """

    name = "micro3d_ime"

    def m115(self, name, data):
        self._triggered = name and name.lower().startswith("ime")
        self._active = False


class Micro3DStockCheck(Check):
    """
    Micro3D with IME firmware

    Identified through firmware name "Micro3D*".
    """

    name = "micro3d"

    def m115(self, name, data):
        self._triggered = name and name.lower().startswith("micro3d")
        self._active = False


class RepetierBefore092Check(Check):
    """
    Repetier firmware prior to version 0.92

    Identified through firmware name "Repetier_x.y.z" with x.y.z < 0.92
    """

    name = "repetier_before_092"

    FIXED_VERSION = get_comparable_version("0.92")

    def m115(self, name, data):
        if name and name.lower().startswith("repetier"):
            version = self._extract_repetier_version(name)
            self._triggered = version is not None and version < self.FIXED_VERSION
        self._active = False

    def _extract_repetier_version(self, name):
        """
        Extracts the Repetier version number from the firmware name.

        Example: "Repetier_0.91" => 0.91
        """
        version = None
        if "_" in name:
            _, version = name.split("_", 1)
            try:
                version = get_comparable_version(version, base=True)
            except Exception:
                pass
        return version


class ThermalProtectionCapCheck(NegativeCapCheck):
    """
    Firmware reporting disabled THERMAL_PROTECTION capability
    """

    name = "capability"
    CAP = "THERMAL_PROTECTION"
