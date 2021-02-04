# Firmware Check

The Firmware Check plugin tries to identify printers or rather printer firmware with known safety issues, such as
disabled thermal runaway protection, or other kinds of severe issues, like known communication crippling bugs, and
displays a warning box to logged in users on identification of such a firmware.

![Screenshot of two warnings](https://raw.githubusercontent.com/OctoPrint/OctoPrint-FirmwareCheck/master/extras/screenshot.png)

Since version 2021-2-4 it also displays info/"heads-ups" messages if a development firmware build
is detected. This kind of message can be disabled.

![Screenshot of an info](https://raw.githubusercontent.com/OctoPrint/OctoPrint-FirmwareCheck/master/extras/screenshot2.png)

It was formerly called "Printer Safety Check" and used to be bundled with OctoPrint since version
1.3.7. It was unbundled in 1.4.1 and turned into an install dependency to allow for a separate release cycle. It is
still considered a core plugin of OctoPrint, treated as if bundled and thus also active in [safe mode](https://docs.octoprint.org/en/master/features/safemode.html).

## Setup

The plugin is part of the core dependencies of OctoPrint 1.4.1+ and will be installed automatically alongside it.

In case you want to manually install it into an older version for whatever reason, install via the bundled
[Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/OctoPrint/OctoPrint-FirmwareCheck/archive/master.zip

To install and/or rollback to a specific version `<version>`, either use this URL in the plugin manager:

    https://github.com/OctoPrint/OctoPrint-FirmwareCheck/archive/<version>.zip

or run

    pip install OctoPrint-FirmwareCheck==<version>

in your OctoPrint virtual environment, substituting `<version>` accordingly.

## Events

### plugin_firmware_check_warning

*(as `Events.PLUGIN_FIRMWARE_CHECK_WARNING`)*

A firmware check warning was triggered.

Payload:
  * `warning_type`: type of warning that was triggered (currently `firmware-unsafe` or `firmware-broken`)
  * `check_name`: name of check that was triggered (e.g. `aneta8`, `cbd`)
  * `check_type`: type of check that was triggered (e.g. `m115`, `received` or `cap`)

## Detected issues

The plugin currently issues three types of warnings: `firmware-unsafe` for firmware known to have severe safety issues,
`firmware-broken` for firmware known to have a broken implementation of the communication protocol
and `firmware-development` for detected development builds of firmware.

### Unsafe firmware

Please refer to the [entry on the "unsafe firmware" warning in OctoPrint's FAQ](https://faq.octoprint.org/warning-firmware-unsafe)
for a list of currently known to be affected printers.

### Broken firmware

#### "CBD"/"ZWLF" firmware

Please refer to the [entry on the "broken CBD firmware" warning in OctoPrint's FAQ](https://faq.octoprint.org/warning-firmware-broken-cbd)
for a list of currently known to be affected printers.

#### Creality firmware with broken temperature reporting

Please refer to the [entry on the this warning in OctoPrint's FAQ](https://faq.octoprint.org/warning-firmware-broken-creality-temp)
for variants of this and a list of currently known to be affected printers.

### Development firmware

Please refer to the [entry on the "development firmware" warning in OctoPrint's FAQ](https://faq.octoprint.org/warning-firmware-development)
for a list of currently detected firmware variants.
