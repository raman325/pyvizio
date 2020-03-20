| NOTE: The device type `soundbar` has been deprecated in favor of `speaker`. Support will be removed soon.

## Description

Simple cli and API implementation for Vizio SmartCast TVs and Speakers (Sound Bars). Mainly created for 
integration with [HASS](http://home-assistant.io). Note that some of the interaction commands are not supported by 
speakers.

## Installation

Use `pip`: 
```bash
pip3 install pyvizio
```
or
```bash
pip install pyvizio
```
if `pip3` is not found.

## Upgrade

Use `pip`: 
```bash
pip3 install --upgrade pyvizio
```
or
```bash
pip install --upgrade pyvizio
```
if `pip3` is not found.

## CLI Usage

To avoid repeating IP (`--ip`), Auth (`--auth`), and Device Type (`--device_type`) params in each CLI call, you can add them to environment variables as `VIZIO_IP`, `VIZIO_AUTH`, and `VIZIO_DEVICE_TYPE` respectively

`--device-type` options are `tv` and `speaker`. If the parameter is not included, the device type is assumed to be `tv`. Note that TVs always require a pairing process to get an auth token. Speakers may not always need an auth token but YMMV based on your particular model.

### Find your device

First, find your device (yeah, I'm too lazy to add another cli group)
```bash
pyvizio --ip=0 discover
```

and note its IP address and port number. If you have trouble finding a device you were expecting to, you can try increasing the discovery timeout period by adding the `--timeout` option.

### Pairing

Using your device's IP address and port number, request pairing procedure:

```bash
pyvizio --ip={ip:port} --device_type={device_type} pair
```
After running the above command:
- For TVs, lookup the PIN code on your TV and note challenge token and type in console
- For speakers, press the physical "Volume Up" and note challenge token and type in console

> It's better to have your device turned on as it's "forgetting" the PIN sometimes if it was turned off prior to pairing command.

Using these data points, finalize pairing procedure: (a pin is not necessary for speakers as they appear to always use `0000`)
```bash
pyvizio --ip={ip:port} --device_type={device_type} pair-finish --ch_type={challenge_type} --token={challenge_token} --pin={pin}
```
If everything done correctly, you should see new connected device named `Python Vizio` 
in Vizio SmartCast mobile APP 


> For a TV, you'll need auth code for any further commands. If you are interacting with a Speaker, and skipped the pairing process, you don't need to include the `--auth` parameter in any of the following calls since you don't have an auth code.

### Turning on/off

```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} power {on|off|toggle}
```

To get current power state simply call

```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-power-state
```

### Volume operations

You could change volume
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} volume {up|down} amount
```

and get current level (0-100)
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-volume-level
```

In addition mute command is available
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} mute {on|off|toggle}
```

### Switching channels (TVs only)
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} channel {up|down|prev} amount
```

### Input sources

You can get current source (if the value is SMARTCAST, then an app is currently runniing)

```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-current-input
```

List all connected devices

```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-inputs-list
```

And using `Name` column from this list, you can switch input:

```bash
pyvizio --ip={ip:port}  --device_type={device_type} --auth={auth_code} input {input_name}
```

Other options is to circle through all inputs
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} next-input
```

### Managing audio settings
> You may have to experiment to find the available options for a given setting. For example, numeric settings have a finite range. I've also found that certain ranges returned by the API aren't correct

List available audio setting names and their current values
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-all-audio-settings
```

Get the current value of a given audio setting
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-audio-setting {setting_name}
```

List available audio setting names and their available choices/ranges
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-all-audio-settings-options
```

Get the choices/range of a given audio setting
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-audio-setting-options {setting_name}
```

Set a new value for a given audio setting
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} audio-setting {setting_name} {new_value}
```

### Managing any setting type
List all available setting types
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-setting-types-list
```

List available setting names and their current values for a given setting type
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-all-settings {setting_type}
```

Get the current value of a given setting (must specify setting type)
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-setting {setting_type} {setting_name}
```

List available setting names and their available choices/ranges for a given setting type
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-all-settings-options {setting_type}
```

Get the choices/range of a given setting (must specify setting type)
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-setting-options {setting_type} {setting_name}
```

Set a new value for a given setting (must specify setting type)
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} setting {setting_type} {setting_name} {new_value}
```

### Apps (TVs with app support only)

Get a list of available apps by name (this list is static and is from the Vizio SmartCast Android source code. If you would like to add apps to this list and can retrieve the latest source code, you can use `pyvizio.util.gen_apps_list_from_src("path/to/root/of/source")` to retrieve the latest list. The list is stored in `APPS` in `pyvizio/_api/apps.py` and you are welcome to submit a PR with updates)
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-apps-list
```

Get currently running app (if value is `_NO_APP_RUNNING` then no app is currently running, and if the value is `_UNKNOWN_APP` then the app name couldn't be determined from the current `APPS` list)
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-current-app
```

Launch an app (app names must match the names listed in the `get-apps-list` command but are not case sensitive. Be sure to use quotes if the app name has a space)
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} launch-app "{app_name}"
```

If an app isn't found by name, but you know the config required to launch it, you can specify the config
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} launch-app-config {APP_ID} {NAME_SPACE} {MESSAGE}
```

One way to get the config of an app that is not already stored in the APPS list is to launch the app on your device and then run
```bash
pyvizio --ip={ip:port} --device_type={device_type} --auth={auth_code} get-current-app-config
```

## Contribution

Thanks for great research uploaded [here](https://github.com/exiva/Vizio_SmartCast_API) and 
absolutely awesome SSDP discovery [snippet](https://gist.github.com/dankrause/6000248)
