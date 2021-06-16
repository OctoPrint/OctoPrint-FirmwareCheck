# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2019 The OctoPrint Project - Released under terms of the AGPLv3 License"

import datetime
import re

from flask_babel import gettext

from . import Check, Severity


class FirmwareDevelopmentChecks(object):
    @classmethod
    def as_dict(cls):
        return dict(
            checks=(
                MarlinBugfixCheck(),
                MarlinMfsBugfixCheck(),
            ),
            message=gettext(
                "Your printer's firmware is a {buildtype} build of {firmware} "
                "(build date {builddate}). It might be more unstable "
                "than a release version and should be kept up-to-date."
            ),
            severity=Severity.INFO,
        )


class MarlinBugfixCheck(Check):
    """
    Marlin bugfix builds.

    Identified by firmware name that contains "Marlin bugfix-<version> (<builddate>)"
    """

    name = "marlin_bugfix"

    pattern = re.compile(
        r"marlin (?P<version>bugfix-[^-]*)\s\((?P<builddate>.*)\)",
    )

    def __init__(self):
        super().__init__()
        self.placeholders = {
            "firmware": "Marlin",
            "version": "unknown",
            "builddate": "unknown",
            "buildtype": "development",
        }

    def m115(self, name, data):
        match = self.pattern.match(name.lower())
        if match:
            self.placeholders["version"] = match.group("version")
            self.placeholders["builddate"] = match.group("builddate")

            try:
                self.placeholders["builddate"] = datetime.datetime.strptime(
                    match.group("builddate"), "%b %d %Y %H:%M:%S"
                ).strftime("%Y%m%d")
            except Exception:
                pass

        self._triggered = name and match
        self._active = False


class MarlinMfsBugfixCheck(MarlinBugfixCheck):
    """
    Marlin MFS bugfix builds.

    Identified by firmware name that matches "Marlin bugfix-<version>-mfs (<builddate>)"
    """

    name = "marlin_bugfix_mfs"
    url = "https://faq.octoprint.org/warning-firmware-development-mfs"

    pattern = re.compile(
        r"marlin (?P<version>bugfix-.*-mfs)\s\((?P<builddate>.*)\)",
    )

    def __init__(self):
        super().__init__()
        self.placeholders["firmware"] = "Marlin by the Marlin Firmware Service"
        self.placeholders["buildtype"] = "nightly"
