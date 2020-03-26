$(function() {
    function FirmwareCheckViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.printerState = parameters[1];
        self.access = parameters[2];

        self.warnings = ko.observableArray([]);

        self.requestData = function() {
            if (!self.loginState.hasPermission(self.access.permissions.PLUGIN_FIRMWARE_CHECK_DISPLAY)) {
                self.warnings([]);
                return;
            }

            OctoPrint.plugins.firmware_check.get()
                .done(self.fromResponse)
                .fail(function() {
                    self.warnings([]);
                });
        };

        self.fromResponse = function(data) {
            var warnings = [];
            _.each(data, function(data, warning_type) {
                warnings.push({
                    type: warning_type,
                    message: gettext(data.message),
                    severity: data.severity,
                    url: data.url
                });
            });
            self.warnings(warnings);
        };

        self.onStartup = function() {
            self.requestData();
        };

        self.onUserPermissionsChanged = self.onUserLoggedIn = self.onUserLoggedOut = function() {
            self.requestData();
        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin !== "firmware_check") return;
            if (!data.hasOwnProperty("type")) return;

            if (data.type === "update") {
                self.requestData();
            }
        };

        self.cssClass = function(data) {
            if (data.severity) {
                return "firmware_check_warning_" + data.severity;
            } else {
                return undefined;
            }
        };

        self.warningText = function(data) {
            switch (data.type) {
                case "firmware-unsafe": return gettext("Critical Warning: Firmware Unsafe");
                case "firmware-broken": return gettext("Warning: Firmware Broken");
                default: return (data.severity === "critical") ? gettext("Critical Warning") : gettext("Warning");
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: FirmwareCheckViewModel,
        dependencies: ["loginStateViewModel", "printerStateViewModel", "accessViewModel"],
        elements: ["#sidebar_plugin_firmware_check_wrapper"]
    });
});

