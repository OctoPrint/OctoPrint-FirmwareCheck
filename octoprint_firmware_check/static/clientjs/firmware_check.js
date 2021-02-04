(function (global, factory) {
    if (typeof define === "function" && define.amd) {
        define(["OctoPrintClient"], factory);
    } else {
        factory(global.OctoPrintClient);
    }
})(this, function (OctoPrintClient) {
    var OctoPrintFirmwareCheckClient = function (base) {
        this.base = base;
    };

    OctoPrintFirmwareCheckClient.prototype.get = function (opts) {
        return this.base.get(this.base.getSimpleApiUrl("firmware_check"), opts);
    };

    OctoPrintClient.registerPluginComponent(
        "firmware_check",
        OctoPrintFirmwareCheckClient
    );
    return OctoPrintFirmwareCheckClient;
});
