# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2019 The OctoPrint Project - Released under terms of the AGPLv3 License"

import logging

from octoprint.util import monotonic_time


class Check(object):
    name = None
    url = None

    ACTIVE_TIMEOUT = 30.0

    def __init__(self):
        self._active = True
        self._triggered = False
        self._start_time = None

    def received(self, line):
        """Called when receiving a new line from the printer"""
        pass

    def m115(self, name, data):
        """Called when receiving the response to an M115 from the printer"""
        pass

    def cap(self, cap, enabled):
        """Called when receiving a capability report line"""
        pass

    @property
    def active(self):
        """Whether this check is still active"""
        return self._active

    @property
    def triggered(self):
        """Whether the check has been triggered"""
        return self._triggered

    def evaluate_timeout(self):
        if self._start_time is None:
            self._start_time = monotonic_time()
        else:
            if monotonic_time() > self._start_time + self.ACTIVE_TIMEOUT:
                # timeout ran out, this is now inactive
                self._active = False
                logging.getLogger(__name__).info(
                    "Deactivated {} due to timeout after {}s".format(
                        __name__, self.ACTIVE_TIMEOUT
                    )
                )

    def reset(self):
        self._active = True
        self._triggered = False
        self._start_time = None


class LineCheck(Check):
    def __init__(self):
        Check.__init__(self)
        self._matches = None

    def received(self, line):
        if not line:
            return

        if self._is_match(line):
            self._matches = True
        elif self._is_ruled_out(line):
            self._matches = False

        self._evaluate()

    def m115(self, name, data):
        # M115 usually means we stop scanning received lines
        if self._matches is None:
            self._matches = False
        self._evaluate()

    def _evaluate(self):
        if self._matches is None:
            return
        self._triggered = self._matches
        self._active = False

    def reset(self):
        Check.reset(self)
        self._matches = None

    def _is_match(self, line):
        return False

    def _is_ruled_out(self, line):
        return False


class CapCheck(Check):
    CAP = None

    def __init__(self):
        Check.__init__(self)
        self.cap_seen = False

    def cap(self, cap, enabled):
        self.cap_seen = True
        if cap == self.CAP:
            self._triggered = self._eval(enabled)
            self._active = False

    def received(self, line):
        if self.cap_seen and not line.startswith("Cap:"):
            # first non cap line after cap report: cap report over, deactivate
            self._active = False

    def _eval(self, enabled):
        # trigger when enabled
        return enabled


class NegativeCapCheck(CapCheck):
    def _eval(self, enabled):
        # trigger when NOT enabled
        return not enabled


class AuthorCheck(Check):
    authors = ()

    AUTHOR = "| Author: ".lower()

    def m115(self, name, data):
        # M115 usually means we stop scanning received lines
        self._active = False

    def received(self, line):
        if not line:
            return

        lower_line = line.lower()
        if self.AUTHOR in lower_line:
            self._triggered = any(map(lambda x: x in lower_line, self.authors))
            self._active = False


class Severity(object):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
