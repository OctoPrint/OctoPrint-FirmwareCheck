$(function () {
    function FirmwareCheckViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.printerState = parameters[1];
        self.access = parameters[2];
        self.settings = parameters[3];

        self.warnings = ko.observableArray([]);
        self.infos = ko.observableArray([]);

        self.disablingInfos = ko.observable(false);

        self.requestData = function () {
            if (
                !self.loginState.hasPermission(
                    self.access.permissions.PLUGIN_FIRMWARE_CHECK_DISPLAY
                )
            ) {
                self.warnings([]);
                return;
            }

            OctoPrint.plugins.firmware_check
                .get()
                .done(self.fromResponse)
                .fail(function () {
                    self.warnings([]);
                });
        };

        self.fromResponse = function (data) {
            var warnings = [];
            var infos = [];
            _.each(data, function (data, warning_type) {
                var item = {
                    type: warning_type,
                    message: gettext(data.message),
                    severity: data.severity,
                    url: data.url
                };
                if (data.severity === "info") {
                    if (!self.settings.settings.plugins.firmware_check.ignore_infos()) {
                        infos.push(item);
                    }
                } else {
                    warnings.push(item);
                }
            });
            self.warnings(warnings);
            self.infos(infos);
        };

        self.onStartup = function () {
            self.requestData();
        };

        var subbed = false;
        self.onStartup =
            self.onUserPermissionsChanged =
            self.onUserLoggedIn =
            self.onUserLoggedOut =
                function () {
                    if (
                        self.settings &&
                        self.settings.settings &&
                        self.settings.settings.plugins &&
                        self.settings.settings.plugins.firmware_check &&
                        !subbed
                    ) {
                        subbed = true;
                        self.settings.settings.plugins.firmware_check.ignore_infos.subscribe(
                            function () {
                                self.requestData();
                            }
                        );
                    }

                    self.requestData();
                };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "firmware_check") return;
            if (!data.hasOwnProperty("type")) return;

            if (data.type === "update") {
                self.requestData();
            }
        };

        self.cssClass = function (data) {
            if (data.severity) {
                return "firmware_check_warning_" + data.severity;
            } else {
                return undefined;
            }
        };

        self.warningText = function (data) {
            switch (data.type) {
                case "firmware-unsafe":
                    return gettext("Critical Warning: Firmware Unsafe");
                case "firmware-broken":
                    return gettext("Warning: Firmware Broken");
                case "firmware-development":
                    return gettext("Info: Firmware Development Build");
                default:
                    return data.severity === "critical"
                        ? gettext("Critical Warning")
                        : data.severity === "warning"
                        ? gettext("Warning")
                        : gettext("Info");
            }
        };

        self.disableInfos = function () {
            if (self.loginState.hasPermission(self.access.permissions.SETTINGS)) {
                self.disablingInfos(true);
                OctoPrint.settings
                    .savePluginSettings("firmware_check", {ignore_infos: true})
                    .always(function () {
                        self.disablingInfos(false);
                    });
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: FirmwareCheckViewModel,
        dependencies: [
            "loginStateViewModel",
            "printerStateViewModel",
            "accessViewModel",
            "settingsViewModel"
        ],
        elements: [
            "#sidebar_plugin_firmware_check_warning_wrapper",
            "#sidebar_plugin_firmware_check_info_wrapper"
        ]
    });
});
