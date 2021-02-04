# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2020 The OctoPrint Project - Released under terms of the AGPLv3 License"

from flask_babel import gettext

from . import LineCheck, Severity


class FirmwareBrokenChecks(object):
    @classmethod
    def as_dict(cls):
        return dict(
            checks=(CbdCheck(), ZwlfCheck(), CrealityDoubleTempCheck()),
            message=gettext(
                "Your printer's firmware is known to have a broken implementation of the "
                "communication protocol. This may cause print failures or other annoyances. "
                "You'll need to take additional steps for OctoPrint to fully work with it."
            ),
            severity=Severity.WARNING,
        )


class CbdCheck(LineCheck):
    name = "cbd"
    url = "https://faq.octoprint.org/warning-firmware-broken-cbd"
    FRAGMENT = "CBD make it".lower()

    def _is_match(self, line):
        return self.FRAGMENT in line.lower()


class ZwlfCheck(CbdCheck):
    name = "zwlf"
    FRAGMENT = "ZWLF make it".lower()


class CrealityDoubleTempCheck(LineCheck):
    name = "creality_double_temp"
    url = "https://faq.octoprint.org/warning-firmware-broken-creality-double-temp"

    def m115(self, name, data):
        # we cannot stop scanning after an M115 report as we might not yet have seen a temperature report then
        pass

    def _is_match(self, line):
        # broken report: TT::27.9327.93 //0.000.00 BB::39.6739.67 //0.000.00 @@::00 BB@@::00
        return "TT::" in line

    def _is_ruled_out(self, line):
        # first thing that looks like a proper report stops scanning
        return (
            " T:" in line
            or line.startswith("T:")
            or " T0:" in line
            or line.startswith("T0:")
            or ((" B:" in line or line.startswith("B:")) and "A:" not in line)
        )


class CrealityEqualsTempCheck(CrealityDoubleTempCheck):
    name = "creality_equals_temp"
    url = "https://faq.octoprint.org/warning-firmware-broken-creality-equals-temp"

    def _is_match(self, line):
        # broken report: ==T:145.66 /210.00 ==B:60.15 /60.00 @:127 B@:0
        return "==T:" in line
