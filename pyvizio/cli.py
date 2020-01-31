import logging
import sys

import click
from pyvizio import VizioAsync, guess_device_type
from pyvizio.const import (
    DEFAULT_DEVICE_CLASS,
    DEFAULT_DEVICE_ID,
    DEFAULT_DEVICE_NAME,
    DEFAULT_TIMEOUT,
    DEVICE_CLASS_SOUNDBAR,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
)
from pyvizio.helpers import async_to_sync
from tabulate import tabulate

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
    type=click.Choice([DEVICE_CLASS_TV, DEVICE_CLASS_SPEAKER, DEVICE_CLASS_SOUNDBAR]),
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


@cli.command()
@async_to_sync
@pass_vizio
async def pair_stop(vizio: VizioAsync) -> None:
    _LOGGER.info("Sending stop pair command")

    await vizio.stop_pair()


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


@cli.command()
@async_to_sync
@pass_vizio
async def get_inputs_list(vizio: VizioAsync) -> None:
    inputs = await vizio.get_inputs()

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

    if data:
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
        txt = "Turning ON"
        result = await vizio.pow_on()
    elif "off" == state:
        txt = "Turning OFF"
        result = await vizio.pow_off()
    else:
        txt = "Toggling power"
        result = await vizio.pow_toggle()

    _LOGGER.info(txt)
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
        txt = "Increasing volume"
        result = await vizio.vol_up(amount)
    else:
        txt = "Decreasing volume"
        result = await vizio.vol_down(amount)

    _LOGGER.info(txt)
    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@async_to_sync
@pass_vizio
async def get_volume_level(vizio: VizioAsync) -> None:
    _LOGGER.info("Current volume: %s", await vizio.get_current_volume())


@cli.command()
@async_to_sync
@pass_vizio
async def get_volume_max(vizio: VizioAsync) -> None:
    _LOGGER.info("Max volume: %s", await vizio.get_max_volume())


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
        txt = "Channel up"
        result = await vizio.ch_up(amount)
    elif "down" == state:
        txt = "Channel down"
        result = await vizio.ch_down(amount)
    else:
        txt = "Previous channel"
        result = await vizio.ch_prev()

    _LOGGER.info(txt)
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
        txt = "Muting"
        result = await vizio.mute_on()
    elif "off" == state:
        txt = "Unmuting"
        result = await vizio.mute_off()
    else:
        txt = "Toggling mute"
        result = await vizio.mute_toggle()

    _LOGGER.info(txt)
    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@async_to_sync
@pass_vizio
async def next_input(vizio: VizioAsync) -> None:
    result = await vizio.next_input()

    _LOGGER.info("Circling input")
    _LOGGER.info("OK" if result else "ERROR")


@cli.command(name="input")
@click.argument("name", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def input(vizio: VizioAsync, name: str) -> None:
    result = await vizio.set_input(name)

    _LOGGER.info("Switching input")
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
    result = await vizio.remote(key.upper())

    _LOGGER.info("Emulating pressing of '%s' key", key)
    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@async_to_sync
@pass_vizio
async def get_audio_settings_list(vizio: VizioAsync) -> None:
    my_list = await vizio.get_audio_settings_list()
    if my_list:
        table = tabulate(my_list, headers=["Audio Setting Name"])
        _LOGGER.info("\n%s", table)
    else:
        _LOGGER.error("Couldn't get list of audio settings")


@cli.command()
@click.argument("setting_name", required=True, type=click.STRING)
@async_to_sync
@pass_vizio
async def get_audio_setting(vizio: VizioAsync, setting_name: str) -> None:
    value = await vizio.get_audio_setting(setting_name)

    if value:
        _LOGGER.info("Current '%s' setting: %s", setting_name, value)
    else:
        _LOGGER.error("Couldn't get value for '%s' setting", setting_name)


@cli.command()
@click.argument("setting_name", required=True, type=click.STRING)
@click.argument("new_value", required=True)
@async_to_sync
@pass_vizio
async def audio_setting(vizio: VizioAsync, setting_name: str, new_value) -> None:
    result = await vizio.set_audio_setting(setting_name, new_value)

    _LOGGER.info("Attemping to set '%s' to '%s'", setting_name, new_value)
    _LOGGER.info("OK" if result else "ERROR")


if __name__ == "__main__":
    cli()
