# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2018 The OctoPrint Project - Released under terms of the AGPLv3 License"

import textwrap

import flask
import octoprint.plugin
from flask_babel import gettext
from octoprint.access import USER_GROUP
from octoprint.access.permissions import Permissions
from octoprint.events import Events
from octoprint.util import to_unicode
from octoprint.util.version import is_octoprint_compatible

from .checks import Severity
from .checks.firmware_broken import FirmwareBrokenChecks
from .checks.firmware_development import FirmwareDevelopmentChecks
from .checks.firmware_unsafe import FirmwareUnsafeChecks

TERMINAL_WARNING = """
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
{message}

Learn more at {url}
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

"""

TERMINAL_INFO = """
---------------------------------------------------------------------------
{message}

Learn more at {url}
---------------------------------------------------------------------------

"""

FIRMWARE_CHECKS = {
    "firmware-unsafe": FirmwareUnsafeChecks.as_dict(),
    "firmware-broken": FirmwareBrokenChecks.as_dict(),
    "firmware-development": FirmwareDevelopmentChecks.as_dict(),
}


class FirmwareCheckPlugin(
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SettingsPlugin,
):

    # noinspection PyMissingConstructor
    def __init__(self):
        self._warnings = dict()
        self._scan_received = True

    ##~~ TemplatePlugin API

    def get_template_configs(self):
        return [
            dict(
                type="sidebar",
                name=gettext("Attention!"),
                data_bind="visible: printerState.isOperational() && loginState.isAdmin() && warnings().length > 0",
                icon="exclamation-triangle",
                styles_wrapper=["display: none"],
                template="firmware_check_sidebar_warning.jinja2",
                suffix="_warning",
            ),
            dict(
                type="sidebar",
                name=gettext("Info"),
                data_bind="visible: printerState.isOperational() && loginState.isAdmin() && infos().length > 0",
                icon="info-circle",
                styles_wrapper=["display: none"],
                template="firmware_check_sidebar_info.jinja2",
                suffix="_info",
            ),
            dict(type="settings", name=gettext("Firmware Check"), custom_bindings=False),
        ]

    ##~~ AssetPlugin API

    def get_assets(self):
        return dict(
            js=("js/firmware_check.js",),
            clientjs=("clientjs/firmware_check.js",),
            css=("css/firmware_check.css",),
            less=("less/firmware_check.less",),
        )

    ##~~ EventHandlerPlugin API

    def on_event(self, event, payload):
        if event == Events.DISCONNECTED:
            self._reset_warnings()
            self._reset_state()
            self._reset_checks()

    ##~~ SimpleApiPlugin API

    def on_api_get(self, request):
        if not Permissions.PLUGIN_FIRMWARE_CHECK_DISPLAY.can():
            return flask.make_response("Insufficient rights", 403)
        return flask.jsonify(self._warnings)

    ##~~ SettingsPlugin API

    def get_settings_defaults(self):
        return {"ignore_infos": False}

    ##~~ GCODE received hook handler

    def on_gcode_received(self, comm_instance, line, *args, **kwargs):
        if self._scan_received:
            self._run_checks("received", to_unicode(line, errors="replace"))
        return line

    ##~~ Firmware info hook handler

    def on_firmware_info_received(self, comm_instance, firmware_name, firmware_data):
        self._run_checks(
            "m115",
            to_unicode(firmware_name, errors="replace"),
            dict(
                (to_unicode(key, errors="replace"), to_unicode(value, errors="replace"))
                for key, value in firmware_data.items()
            ),
        )

    ##~~ Firmware capability hook handler

    def on_firmware_cap_received(self, comm_instance, cap, enabled, all_caps):
        self._run_checks("cap", to_unicode(cap, errors="replace"), enabled)

    ##~~ Additional permissions hook handler

    def get_additional_permissions(self):
        return [
            dict(
                key="DISPLAY",
                name="Display firmware check warnings",
                description=gettext("Allows to see firmware check warnings"),
                roles=["display"],
                default_groups=[USER_GROUP],
            )
        ]

    ##~~ Softwareupdate hook

    def get_update_information(self):
        return dict(
            firmware_check=dict(
                displayName="Firmware Check Plugin",
                displayVersion=self._plugin_version,
                # version check: github repository
                type="github_release",
                user="OctoPrint",
                repo="OctoPrint-FirmwareCheck",
                current=self._plugin_version,
                stable_branch={
                    "name": "Stable",
                    "branch": "master",
                    "commitish": ["devel", "master"],
                },
                prerelease_branches=[
                    {
                        "name": "Prerelease",
                        "branch": "devel",
                        "commitish": ["devel", "master"],
                    }
                ],
                # update method: pip
                pip="https://github.com/OctoPrint/OctoPrint-FirmwareCheck/archive/{target_version}.zip",
            )
        )

    ##~~ Helpers

    def _run_checks(self, check_type, *args, **kwargs):
        changes = False

        still_active = False
        for warning_type, check_data in FIRMWARE_CHECKS.items():
            checks = check_data.get("checks")
            message = check_data.get("message")
            severity = check_data.get("severity", Severity.CRITICAL)
            url = "https://faq.octoprint.org/warning-{warning_type}".format(
                warning_type=warning_type
            )
            if not checks or not message:
                continue

            for check in checks:
                if not check.active:
                    # skip non active checks
                    continue

                method = getattr(check, check_type, None)
                if not callable(method):
                    # skip uncallable checks
                    continue

                # execute method
                try:
                    method(*args, **kwargs)
                except Exception:
                    self._logger.exception(
                        "There was an error running method {} on check {!r}".format(
                            check_type, check
                        )
                    )
                    continue

                # check if now triggered
                if check.triggered:
                    if check.url is not None:
                        url = check.url

                    self._register_warning(warning_type, message, severity, url)

                    # noinspection PyUnresolvedReferences
                    self._event_bus.fire(
                        Events.PLUGIN_FIRMWARE_CHECK_WARNING,
                        dict(
                            check_name=check.name,
                            warning_type=warning_type,
                            severity=severity,
                            url=url,
                        ),
                    )
                    changes = True
                    break

                check.evaluate_timeout()
                self._logger.debug("Check {} active? {}".format(check, check.active))

            still_active = any(check.active for check in checks) or still_active

        self._scan_received = still_active
        self._logger.debug(
            "Scanning received lines enabled? {}".format(self._scan_received)
        )

        if changes:
            self._ping_clients()

    def _register_warning(self, warning_type, message, severity, url):
        output = TERMINAL_WARNING
        if severity == Severity.INFO:
            output = TERMINAL_INFO

        self._log_to_terminal(
            output.format(
                message="\n".join(textwrap.wrap(message, 75)),
                warning_type=warning_type,
                url=url,
            )
        )
        self._warnings[warning_type] = dict(message=message, severity=severity, url=url)

        logline = "{}. More information at {}".format(message, url)
        if severity == Severity.INFO:
            self._logger.info(logline)
        else:
            self._logger.warning(logline)

    def _reset_warnings(self):
        self._warnings.clear()
        self._ping_clients()

    def _reset_state(self):
        self._scan_received = True

    def _reset_checks(self):
        for _, check_data in FIRMWARE_CHECKS.items():
            checks = check_data.get("checks")
            if not checks:
                continue

            for check in checks:
                check.reset()

    def _log_to_terminal(self, message):
        if self._printer:
            lines = message.split("\n")
            self._printer.log_lines(*lines)

    def _ping_clients(self):
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="update"))


def register_custom_events(*args, **kwargs):
    return [
        "warning",
    ]


__plugin_name__ = "Firmware Check"
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3
__plugin_disabling_discouraged__ = gettext(
    "Without this plugin OctoPrint will no longer be able to "
    "check if the printer it is connected to has a known safety "
    "issue or otherwise broken firmware and inform you about that fact."
)
__plugin_implementation__ = FirmwareCheckPlugin()
__plugin_hooks__ = {
    "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
    "octoprint.comm.protocol.gcode.received": (
        __plugin_implementation__.on_gcode_received,
        100,
    ),
    "octoprint.comm.protocol.firmware.info": (
        __plugin_implementation__.on_firmware_info_received,
        100,
    ),
    "octoprint.comm.protocol.firmware.capabilities": (
        __plugin_implementation__.on_firmware_cap_received,
        100,
    ),
    "octoprint.events.register_custom_events": register_custom_events,
    "octoprint.access.permissions": __plugin_implementation__.get_additional_permissions,
}

if is_octoprint_compatible("<1.6"):
    __plugin_settings_overlay__ = {
        "appearance": {
            "components": {
                "order": {
                    "sidebar": [
                        "plugin_firmware_check_warning",
                        "plugin_firmware_check_info",
                        "connection",
                        "state",
                        "files",
                    ]
                }
            }
        }
    }
