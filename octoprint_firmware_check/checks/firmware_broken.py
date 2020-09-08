# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2020 The OctoPrint Project - Released under terms of the AGPLv3 License"

from flask_babel import gettext
from . import LineCheck, Severity

class FirmwareBrokenChecks(object):
	@classmethod
	def as_dict(cls):
		return dict(checks=(CbdCheck(),),
		            message=gettext("Your printer's firmware is known to have a broken implementation of the "
		                            "communication protocol. This will cause print failures. You'll need to "
		                            "take additional steps for OctoPrint to work with it."),
		            severity=Severity.INFO)


class CbdCheck(LineCheck):
	name = "cbd"
	url = "https://faq.octoprint.org/warning-firmware-broken-cbd"
	FRAGMENT = "CBD make it".lower()

	def _is_match(self, line):
		return self.FRAGMENT in line.lower()


class ZwlfCheck(CbdCheck):
	name = "zwlf"
	FRAGMENT = "ZWLF make it".lower()
