import logging
import sys
from typing import Union

import click
from tabulate import tabulate

from pyvizio import VizioAsync, guess_device_type
from pyvizio.api.apps import find_app_name
from pyvizio.const import (
    APP_HOME,
    APPS,
    DEFAULT_DEVICE_CLASS,
    DEFAULT_DEVICE_ID,
    DEFAULT_DEVICE_NAME,
    DEFAULT_TIMEOUT,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
    NO_APP_RUNNING,
    UNKNOWN_APP,
)
from pyvizio.helpers import async_to_sync
from pyvizio.util import gen_apps_list_from_url

if sys.version_info < (3, 7):
    print("To use this script you need python 3.7 or newer, got %s" % sys.version_info)
    sys.exit(1)

_LOGGER = logging.getLogger(__name__)

pass_vizio = click.make_pass_decorator(VizioAsync)


@click.group(invoke_without_command=False)
@click.option(
    "--ip",
    envvar="VIZIO_IP",
    required=True,
    help=(
        "IP of the device to connect to (optionally add custom port by specifying "
        "'<IP>:<PORT>')"
    ),
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--auth",
    envvar="VIZIO_AUTH",
    required=False,
    default="",
    help=(
        "Auth token for the device to connect to (refer to documentation on how to "
        "obtain auth token)"
    ),
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--device_type",
    envvar="VIZIO_DEVICE_TYPE",
    required=False,
    default=DEFAULT_DEVICE_CLASS,
    type=click.Choice([DEVICE_CLASS_TV, DEVICE_CLASS_SPEAKER]),
    show_default=True,
    show_envvar=True,
)
@click.pass_context
def cli(ctx, ip: str, auth: str, device_type: str) -> None:
    logging.basicConfig(level=logging.INFO)

    ctx.obj = VizioAsync(DEFAULT_DEVICE_ID, ip, DEFAULT_DEVICE_NAME, auth, device_type)


@cli.command()
@click.option(
    "--include_device_type",
    required=False,
    default=False,
    type=click.BOOL,
    help="Include guessed device type (not guaranteed to be correct)",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--timeout",
    required=False,
    default=DEFAULT_TIMEOUT,
    type=click.IntRange(min=1),
    help="Number of seconds to wait for devices to be discovered",
    show_default=True,
    show_envvar=True,
)
def discover(include_device_type: bool, timeout: int) -> None:
    devices = VizioAsync.discovery_zeroconf(timeout)

    if include_device_type:
        table = tabulate(
            [
                [
                    dev.ip,
                    dev.port,
                    dev.model,
                    dev.name,
                    guess_device_type(dev.ip, dev.port),
                ]
                for dev in devices
            ],
            headers=["IP", "Port", "Model", "Name", "Guessed Device Type"],
        )
    else:
        table = tabulate(
            [[dev.ip, dev.port, dev.model, dev.name] for dev in devices],
            headers=["IP", "Port", "Model", "Name"],
        )

    _LOGGER.info("\n%s", table)


@cli.command()
@async_to_sync
@pass_vizio
async def pair(vizio: VizioAsync) -> None:
    _LOGGER.info("Initiating pairing process, check your device for pin upon success")

    pair_data = await vizio.start_pair()

    if pair_data is not None:
        _LOGGER.info("Challenge type: %s", pair_data.ch_type)
        _LOGGER.info("Challenge token: %s", pair_data.token)
    else:
        _LOGGER.info("ERROR")


@cli.command()
@async_to_sync
@pass_vizio
async def pair_stop(vizio: VizioAsync) -> None:
    _LOGGER.info("Sending stop pair command")

    result = await vizio.stop_pair()

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@click.option(
    "--ch_type",
    required=True,
    type=click.INT,
    help="Challenge type obtained from pair command",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--token",
    required=True,
    type=click.INT,
    help="Challenge token obtained from pair command",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--pin",
    required=False,
    type=click.STRING,
    default="",
    help="PIN obtained from device after running pair command. Not needed for speaker devices.",
    show_default=True,
    show_envvar=True,
)
@async_to_sync
@pass_vizio
async def pair_finish(vizio: VizioAsync, ch_type: int, token: int, pin: str) -> None:
    _LOGGER.info("Finishing pairing")

    pair_data = await vizio.pair(ch_type, token, pin)

    if pair_data is not None:
        _LOGGER.info("Authorization token: %s", pair_data.auth_token)
    else:
        _LOGGER.info("ERROR")


@cli.command()
@async_to_sync
@pass_vizio
async def get_inputs_list(vizio: VizioAsync) -> None:
    inputs = await vizio.get_inputs_list()

    if inputs:
        table = tabulate(
            [[input.name, input.meta_name] for input in inputs],
            headers=["Name", "Nickname"],
        )

        _LOGGER.info("\n%s", table)
    else:
        _LOGGER.error("Couldn't get list of inputs")


@cli.command()
@async_to_sync
@pass_vizio
async def get_current_input(vizio: VizioAsync) -> None:
    data = await vizio.get_current_input()

    if data is not None:
        _LOGGER.info("Current input: %s", data)
    else:
        _LOGGER.error("Couldn't get current input")


@cli.command()
@async_to_sync
@pass_vizio
async def get_power_state(vizio: VizioAsync) -> None:
    if await vizio.get_power_state():
        _LOGGER.info("Device is on")
    else:
        _LOGGER.info("Device is off")


@cli.command()
@click.argument(
    "state",
    required=False,
    default="toggle",
    type=click.Choice(["toggle", "on", "off"]),
)
@async_to_sync
@pass_vizio
async def power(vizio: VizioAsync, state: str) -> None:
    if "on" == state:
        _LOGGER.info("Turning ON")
        result = await vizio.pow_on()
    elif "off" == state:
        _LOGGER.info("Turning OFF")
        result = await vizio.pow_off()
    else:
        _LOGGER.info("Toggling Power")
        result = await vizio.pow_toggle()

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@click.argument(
    "state", required=False, default="up", type=click.Choice(["up", "down"])
)
@click.argument(
    "amount", required=False, default=1, type=click.IntRange(1, 100, clamp=True)
)
@async_to_sync
@pass_vizio
async def volume(vizio: VizioAsync, state: str, amount: int) -> None:
    if "up" == state:
        _LOGGER.info("Increasing volume")
        result = await vizio.vol_up(amount)
    else:
        _LOGGER.info("Decreasing volume")
        result = await vizio.vol_down(amount)

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@async_to_sync
@pass_vizio
async def get_volume_level(vizio: VizioAsync) -> None:
    _LOGGER.info("Current volume: %s", await vizio.get_current_volume())


@cli.command()
@pass_vizio
def get_volume_max(vizio: VizioAsync) -> None:
    _LOGGER.info("Max volume: %s", vizio.get_max_volume())


@cli.command()
@click.argument(
    "state",
    required=False,
    default="previous",
    type=click.Choice(["up", "down", "previous"]),
)
@click.argument(
    "amount", required=False, default=1, type=click.IntRange(1, 100, clamp=True)
)
@async_to_sync
@pass_vizio
async def channel(vizio: VizioAsync, state: str, amount: int) -> None:
    if "up" == state:
        _LOGGER.info("Channel up")
        result = await vizio.ch_up(amount)
    elif "down" == state:
        _LOGGER.info("Channel down")
        result = await vizio.ch_down(amount)
    else:
        _LOGGER.info("Previous channel")
        result = await vizio.ch_prev()

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@click.argument(
    "state",
    required=False,
    default="toggle",
    type=click.Choice(["toggle", "on", "off"]),
)
@async_to_sync
@pass_vizio
async def mute(vizio: VizioAsync, state: str) -> None:
    if "on" == state:
        _LOGGER.info("Muting")
        result = await vizio.mute_on()
    elif "off" == state:
        _LOGGER.info("Unmuting")
        result = await vizio.mute_off()
    else:
        _LOGGER.info("Toggling mute")
        result = await vizio.mute_toggle()

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@async_to_sync
@pass_vizio
async def next_input(vizio: VizioAsync) -> None:
    _LOGGER.info("Circling input")

    result = await vizio.next_input()

    _LOGGER.info("OK" if result else "ERROR")


@cli.command(name="input")
@click.argument("input_name", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def input(vizio: VizioAsync, input_name: str) -> None:
    _LOGGER.info("Switching input")

    result = await vizio.set_input(input_name)

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@async_to_sync
@pass_vizio
async def play(vizio: VizioAsync) -> None:
    result = await vizio.play()

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@async_to_sync
@pass_vizio
async def pause(vizio: VizioAsync) -> None:
    result = await vizio.pause()

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@click.argument("key", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def key_press(vizio: VizioAsync, key: str) -> None:
    _LOGGER.info("Emulating pressing of '%s' key", key)

    result = await vizio.remote(key.upper())

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@pass_vizio
async def get_remote_keys_list(vizio: VizioAsync) -> None:
    table = tabulate(vizio.get_remote_keys_list(), headers=["App Name"])
    _LOGGER.info("\n%s", table)


@cli.command()
@async_to_sync
@pass_vizio
async def get_all_audio_settings(vizio: VizioAsync) -> None:
    audio_settings = await vizio.get_all_audio_settings()
    if audio_settings:
        table = tabulate(
            [[k, v] for k, v in audio_settings.items()], headers=["Name", "Value"]
        )
        _LOGGER.info("\n%s", table)
    else:
        _LOGGER.error("Couldn't get list of audio settings")


@cli.command()
@async_to_sync
@pass_vizio
async def get_all_audio_settings_options(vizio: VizioAsync) -> None:
    audio_settings_options = await vizio.get_all_audio_settings_options()
    if audio_settings_options:
        options = []
        for k, v in audio_settings_options.items():
            if isinstance(v, dict):
                options.append([k, v.get("default"), v["min"], v["max"], None])
            else:
                options.append([k, None, None, None, ", ".join(v)])
        table = tabulate(options, headers=["Name", "Default", "Min", "Max", "Choices"])
        _LOGGER.info("\n%s", table)
    else:
        _LOGGER.error("Couldn't get list of audio settings options")


@cli.command()
@click.argument("setting_name", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def get_audio_setting(vizio: VizioAsync, setting_name: str) -> None:
    value = await vizio.get_audio_setting(setting_name)

    if value is not None:
        _LOGGER.info("Current '%s' setting: %s", setting_name, value)
    else:
        _LOGGER.error("Couldn't get value for '%s' setting", setting_name)


@cli.command()
@click.argument("setting_type", required=True, type=click.STRING)
@click.argument("setting_name", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def get_setting_options(
    vizio: VizioAsync, setting_type: str, setting_name: str
) -> None:
    value = await vizio.get_setting_options(setting_type, setting_name)

    _LOGGER.error(value)
    if value is not None:
        if isinstance(value, dict):
            if value.get("default") is not None:
                table = tabulate(
                    [[value["default"], value["min"], value["max"]]],
                    headers=["Default", "Min", "Max"],
                )
            else:
                table = tabulate([[value["min"], value["max"]]], headers=["Min", "Max"])
            _LOGGER.info("For '%s' setting:\n%s", setting_name, table)
        else:
            _LOGGER.info("Options for '%s' setting: %s", setting_name, ", ".join(value))
    else:
        _LOGGER.error("Couldn't get options for '%s' setting", setting_name)


@cli.command()
@click.argument("setting_type", required=True, type=click.STRING)
@click.argument("setting_name", required=True, type=click.STRING)
@click.argument("new_value", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def setting(
    vizio: VizioAsync, setting_type: str, setting_name: str, new_value: Union[int, str]
) -> None:
    _LOGGER.info("Attempting to set '%s' to '%s'", setting_name, new_value)

    try:
        result = await vizio.set_setting(setting_type, setting_name, int(new_value))
    except ValueError:
        result = await vizio.set_setting(setting_type, setting_name, new_value)

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@click.argument("setting_type", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def get_all_settings(vizio: VizioAsync, setting_type: str) -> None:
    settings = await vizio.get_all_settings(setting_type)
    if settings:
        table = tabulate(
            [[k, v] for k, v in settings.items()], headers=["Name", "Value"]
        )
        _LOGGER.info("\n%s", table)
    else:
        _LOGGER.error("Couldn't get list of settings for %s setting type", setting_type)


@cli.command()
@click.argument("setting_type", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def get_all_settings_options(vizio: VizioAsync, setting_type: str) -> None:
    settings_options = await vizio.get_all_settings_options(setting_type)
    if settings_options:
        options = []
        for k, v in settings_options.items():
            if isinstance(v, dict):
                options.append([k, v.get("default"), v["min"], v["max"], None])
            else:
                options.append([k, None, None, None, ", ".join(v)])
        table = tabulate(options, headers=["Name", "Default", "Min", "Max", "Choices"])
        _LOGGER.info("\n%s", table)
    else:
        _LOGGER.error(
            "Couldn't get list of settings options for %s setting type", setting_type
        )


@cli.command()
@click.argument("setting_type", required=True, type=click.STRING)
@click.argument("setting_name", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def get_setting(vizio: VizioAsync, setting_type: str, setting_name: str) -> None:
    value = await vizio.get_setting(setting_type, setting_name)

    if value is not None:
        _LOGGER.info("Current '%s' setting: %s", setting_name, value)
    else:
        _LOGGER.error(
            "Couldn't get value for '%s' setting of %s setting type",
            setting_name,
            setting_type,
        )


@cli.command()
@async_to_sync
@pass_vizio
async def get_setting_types_list(vizio: VizioAsync) -> None:
    value = await vizio.get_setting_types_list()

    if value is not None:
        table = tabulate(
            [[setting_type] for setting_type in value], headers=["Setting Type"]
        )
        _LOGGER.info("\n%s", table)
    else:
        _LOGGER.error("Couldn't get setting types")


@cli.command()
@click.argument("setting_name", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def get_audio_setting_options(vizio: VizioAsync, setting_name: str) -> None:
    value = await vizio.get_audio_setting_options(setting_name)

    _LOGGER.error(value)
    if value is not None:
        if isinstance(value, dict):
            if value.get("default") is not None:
                table = tabulate(
                    [[value["default"], value["min"], value["max"]]],
                    headers=["Default", "Min", "Max"],
                )
            else:
                table = tabulate([[value["min"], value["max"]]], headers=["Min", "Max"])
            _LOGGER.info("For '%s' setting:\n%s", setting_name, table)
        else:
            _LOGGER.info("Options for '%s' setting: %s", setting_name, ", ".join(value))
    else:
        _LOGGER.error("Couldn't get options for '%s' setting", setting_name)


@cli.command()
@click.argument("setting_name", required=True, type=click.STRING)
@click.argument("new_value", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def audio_setting(
    vizio: VizioAsync, setting_name: str, new_value: Union[int, str]
) -> None:
    _LOGGER.info("Attempting to set '%s' to '%s'", setting_name, new_value)

    try:
        result = await vizio.set_audio_setting(setting_name, int(new_value))
    except ValueError:
        result = await vizio.set_audio_setting(setting_name, new_value)

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@click.option(
    "--country",
    required=False,
    type=click.Choice(["usa", "can", "mexico", "all"]),
    default="all",
    help="Only apps supported in the specified country will be returned",
    show_default=True,
    show_envvar=True,
)
@async_to_sync
@pass_vizio
async def get_apps_list(vizio: VizioAsync, country: str = "all") -> None:
    apps = await VizioAsync.get_apps_list(country)
    if apps:
        table = tabulate([{"Name": app} for app in apps], headers="keys")
        _LOGGER.info("\n%s", table)
    else:
        _LOGGER.error("Couldn't get list of apps")


@cli.command()
@click.argument("app_name", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def launch_app(vizio: VizioAsync, app_name: str) -> None:
    _LOGGER.info("Attempting to launch '%s' app", app_name)
    apps_list = await gen_apps_list_from_url()
    if not apps_list:
        apps_list = APPS

    result = await vizio.launch_app(app_name, apps_list)

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@click.argument("APP_ID", required=True, type=click.STRING)
@click.argument("NAME_SPACE", required=True, type=click.IntRange(min=0))
@click.argument("MESSAGE", required=False, type=click.STRING, default=None)
@async_to_sync
@pass_vizio
async def launch_app_config(
    vizio: VizioAsync, APP_ID: str, NAME_SPACE: int, MESSAGE: str
) -> None:
    _LOGGER.info(
        "Attempting to launch app using config %s",
        {"APP_ID": APP_ID, "NAME_SPACE": NAME_SPACE, "MESSAGE": MESSAGE},
    )

    result = await vizio.launch_app_config(APP_ID, NAME_SPACE, MESSAGE)

    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@async_to_sync
@pass_vizio
async def get_current_app(vizio: VizioAsync) -> None:
    app_config = await vizio.get_current_app_config()
    apps_list = await gen_apps_list_from_url()
    if not apps_list:
        apps_list = APPS
    app_name = find_app_name(app_config, [APP_HOME, *apps_list])

    if app_name:
        if app_name == NO_APP_RUNNING:
            _LOGGER.info("No currently running app")
        elif app_name == UNKNOWN_APP:
            _LOGGER.info(
                "Can't determine the name of the app, the currently running app's config is %s",
                app_config,
            )
        else:
            _LOGGER.info("Currently running app: %s", app_name)
    else:
        _LOGGER.error("Couldn't get currently running app")


@cli.command()
@async_to_sync
@pass_vizio
async def get_current_app_config(vizio: VizioAsync) -> None:
    app_config = await vizio.get_current_app_config()

    if app_config is None:
        _LOGGER.error("Couldn't get currently running app")
    elif app_config:
        _LOGGER.info("Currently running app's config: %s", app_config)
    else:
        _LOGGER.info("No currently running app")


if __name__ == "__main__":
    cli()
