# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2019 The OctoPrint Project - Released under terms of the AGPLv3 License"

from octoprint.util import monotonic_time
import logging

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
				logging.getLogger(__name__).info("Deactivated {} due to timeout after {}s".format(__name__, self.ACTIVE_TIMEOUT))

	def reset(self):
		self._active = True
		self._triggered = False
		self._start_time = None



class AuthorCheck(Check):
	authors = ()

	AUTHOR = "| Author: ".lower()

	def received(self, line):
		if not line:
			return

		lower_line = line.lower()
		if self.AUTHOR in lower_line:
			self._triggered = any(map(lambda x: x in lower_line, self.authors))
			self._active = False


class Severity(object):
	INFO = "info"
	CRITICAL = "critical"
