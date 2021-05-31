# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2021 The OctoPrint Project - Released under terms of the AGPLv3 License"

from flask_babel import gettext

from . import NegativeCapCheck, Severity


class FirmwareHostcommandsChecks(object):
    @classmethod
    def as_dict(cls):
        return {
            "checks": (FirmwareHostcommandsCapCheck(),),
            "message": gettext(
                "Your printer's firmware supports host action commands, but they are "
                "disabled. The firmware will not inform OctoPrint about job pause & "
                "cancellations, filament runouts, and similar firmware-side events. If "
                "you want this functionality, you need to change your firmware's "
                "configuration."
            ),
            "severity": Severity.INFO,
        }


class FirmwareHostcommandsCapCheck(NegativeCapCheck):
    """
    Firmware reporting disabled HOST_ACTION_COMMANDS capability
    """

    name = "capability"
    CAP = "HOST_ACTION_COMMANDS"
