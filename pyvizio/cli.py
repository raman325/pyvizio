import asyncio
from functools import wraps
import logging
import sys

import click
from tabulate import tabulate

from . import VizioAsync
from .const import (
    DEFAULT_DEVICE_CLASS,
    DEVICE_CLASS_SOUNDBAR,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
)

if sys.version_info < (3, 7):
    print("To use this script you need python 3.7 or newer, got %s" % sys.version_info)
    sys.exit(1)

_LOGGER = logging.getLogger(__name__)
DEVICE_ID = "pyvizio"
DEVICE_NAME = "Python Vizio"

pass_vizio = click.make_pass_decorator(VizioAsync)


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group(invoke_without_command=False)
@click.option(
    "--ip",
    envvar="VIZIO_IP",
    required=True,
    help="IP of the device to connect to (optionally add custom port by specifying '<IP>:<PORT>')",
)
@click.option(
    "--auth",
    envvar="VIZIO_AUTH",
    required=False,
    help="Auth token for the device to connect to (refer to documentation on how to obtain auth token)",
)
@click.option(
    "--device_type",
    envvar="VIZIO_DEVICE_TYPE",
    required=False,
    default=DEFAULT_DEVICE_CLASS,
    type=click.Choice([DEVICE_CLASS_TV, DEVICE_CLASS_SPEAKER, DEVICE_CLASS_SOUNDBAR]),
)
@click.pass_context
def cli(ctx, ip: str, auth: str, device_type: str) -> None:
    logging.basicConfig(level=logging.INFO)
    ctx.obj = VizioAsync(DEVICE_ID, ip, DEVICE_NAME, auth, device_type)


@cli.command()
@click.argument("timeout", required=False, default=10, type=click.IntRange(min=1))
def discover(timeout: int) -> None:
    logging.basicConfig(level=logging.INFO)
    devices = VizioAsync.discovery(timeout)
    table = tabulate(
        [[dev.ip, dev.port, dev.model, dev.name] for dev in devices],
        headers=["IP", "Port", "Model", "Name"],
    )
    _LOGGER.info("\n%s", table)


@cli.command()
@coro
@pass_vizio
async def pair(vizio: VizioAsync) -> None:
    _LOGGER.info(
        "Initiating pairing process, please check your device for pin upon success"
    )
    pair_data = await vizio.start_pair()
    if pair_data is not None:
        _LOGGER.info("Challenge type: %s", pair_data.ch_type)
        _LOGGER.info("Challenge token: %s", pair_data.token)


@cli.command()
@coro
@pass_vizio
async def pair_stop(vizio: VizioAsync) -> None:
    _LOGGER.info("Sending stop pair command")
    await vizio.stop_pair()


@cli.command()
@click.option(
    "--ch_type",
    required=False,
    default=1,
    type=click.INT,
    help="Challenge type obtained from pair command",
)
@click.option(
    "--token",
    required=True,
    type=click.INT,
    help="Challenge token obtained from pair command",
)
@click.option(
    "--pin",
    required=True,
    type=click.STRING,
    help="PIN obtained from device after running pair command",
)
@coro
@pass_vizio
async def pair_finish(vizio: VizioAsync, ch_type: int, token: int, pin: str) -> None:
    _LOGGER.info("Finishing pairing")
    pair_data = await vizio.pair(ch_type, token, pin)
    if pair_data is not None:
        _LOGGER.info("Authorization token: %s", pair_data.auth_token)


@cli.command()
@coro
@pass_vizio
async def input_list(vizio: VizioAsync) -> None:
    inputs = await vizio.get_inputs()
    if inputs:
        table = tabulate(
            [[input.name, input.meta_name, input.type, input.id] for input in inputs],
            headers=["Name", "Friendly Name", "Type", "ID"],
        )
        _LOGGER.info("\n%s", table)
    else:
        _LOGGER.error("Couldn't get available inputs")


@cli.command()
@coro
@pass_vizio
async def input_get(vizio: VizioAsync) -> None:
    data = await vizio.get_current_input()
    if data:
        _LOGGER.info("Current input: %s", data.meta_name)
    else:
        _LOGGER.error("Couldn't get current input")


@cli.command()
@coro
@pass_vizio
async def power_get(vizio: VizioAsync) -> None:
    is_on = await vizio.get_power_state()
    _LOGGER.info("Device is on" if is_on else "Device is off")


@cli.command()
@click.argument(
    "state",
    required=False,
    default="toggle",
    type=click.Choice(["toggle", "on", "off"]),
)
@coro
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
@coro
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
@coro
@pass_vizio
async def volume_current(vizio: VizioAsync) -> None:
    _LOGGER.info("Current volume: %s", await vizio.get_current_volume())


@cli.command()
@coro
@pass_vizio
async def volume_max(vizio: VizioAsync) -> None:
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
@coro
@pass_vizio
async def channel(vizio: VizioAsync, state: str, amount: str) -> None:
    amount = int(amount)
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
@coro
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
@coro
@pass_vizio
async def input_next(vizio: VizioAsync) -> None:
    result = await vizio.input_next()
    _LOGGER.info("Circling input")
    _LOGGER.info("OK" if result else "ERROR")


@cli.command(name="input")
@click.option(
    "--name", required=True, type=click.STRING, help="Input name to switch to"
)
@coro
@pass_vizio
async def input(vizio: VizioAsync, name: str) -> None:
    result = await vizio.input_switch(name)
    _LOGGER.info("Switching input")
    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@coro
@pass_vizio
async def play(vizio: VizioAsync) -> None:
    result = await vizio.play()
    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@coro
@pass_vizio
async def pause(vizio: VizioAsync) -> None:
    result = await vizio.pause()
    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@click.argument("key", required=True, type=click.STRING)
@coro
@pass_vizio
async def key_press(vizio: VizioAsync, key: str) -> None:
    _LOGGER.info("Emulating pressing of '%s' key", key)
    result = await vizio.remote(key.upper())
    _LOGGER.info("OK" if result else "ERROR")


if __name__ == "__main__":
    cli()
