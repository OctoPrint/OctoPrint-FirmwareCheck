# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2019 The OctoPrint Project - Released under terms of the AGPLv3 License"

from flask_babel import gettext

from . import Check, Severity


class FirmwareDevelopmentChecks(object):
    @classmethod
    def as_dict(cls):
        return dict(
            checks=(MarlinBugfixCheck(),),
            message=gettext(
                "Your printer's firmware is a development build. It might be more unstable "
                "than a release version and should be updated regularly."
            ),
            severity=Severity.INFO,
        )


class MarlinBugfixCheck(Check):
    """
    Marlin bugfix builds.

    Identified by firmware name that contains "Marlin bugfix-"
    """

    name = "marlin_bugfix"

    def m115(self, name, data):
        self._triggered = name and "marlin bugfix-" in name.lower()
        self._active = False
