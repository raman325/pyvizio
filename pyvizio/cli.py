import logging
import click
import sys
import pyvizio

if sys.version_info < (3, 4):
    print("To use this script you need python 3.4 or newer, got %s" %
          sys.version_info)
    sys.exit(1)

_LOGGER = logging.getLogger(__name__)
DEVICE_ID = "pyvizio"
DEVICE_NAME = "Python Vizio"

pass_tv = click.make_pass_decorator(pyvizio.Vizio)


@click.group(invoke_without_command=False)
@click.option('--ip', envvar="VIZIO_IP", required=True)
@click.option('--auth', envvar="VIZIO_AUTH", required=False)
@click.pass_context
def cli(ctx, ip, auth):
    logging.basicConfig(level=logging.INFO)
    ctx.obj = pyvizio.Vizio(DEVICE_ID, ip, DEVICE_NAME, auth)


@cli.command()
def discover():
    logging.basicConfig(level=logging.INFO)
    devices = pyvizio.Vizio.discovery()
    log_data = "Available devices:" \
               "\nIP\tModel\tFriendly name"
    for dev in devices:
        log_data += "\n{0}\t{1}\t{2}".format(dev.ip, dev.model, dev.name)
    _LOGGER.info(log_data)


@cli.command()
@pass_tv
def pair(vizio):
    _LOGGER.info("Initiating pairing process, please check your TV for pin upon success")
    pair_data = vizio.start_pair()
    if pair_data is not None:
        _LOGGER.info("Challenge type: %s", pair_data.ch_type)
        _LOGGER.info("Challenge token: %s", pair_data.token)


@cli.command()
@pass_tv
def pair_stop(vizio):
    _LOGGER.info("Sending stop pair command")
    vizio.stop_pair()


@cli.command()
@click.option('--ch_type', required=False, default=1)
@click.option('--token', required=True)
@click.option('--pin', required=True)
@pass_tv
def pair_finish(vizio, ch_type, token, pin):
    _LOGGER.info("Finishing pairing")
    pair_data = vizio.pair(ch_type, token, pin)
    if pair_data is not None:
        _LOGGER.info("Authorization token: %s", pair_data.auth_token)


@cli.command()
@pass_tv
def input_list(vizio):
    inputs = vizio.get_inputs()
    if inputs is None:
        return
    log_data = "Available inputs:" \
               "\nName\tFriendly name\tType\tID"
    for v_input in inputs:
        log_data += "\n{0}\t{1}\t{2}\t{3}".format(v_input.name, v_input.meta_name, v_input.type, v_input.id)

    _LOGGER.info(log_data)


@cli.command()
@pass_tv
def input_get(vizio):
    data = vizio.get_current_input()
    if data is None:
        return
    _LOGGER.info(data.meta_name)


@cli.command()
@click.argument("state", required=False)
@pass_tv
def power(vizio, state):
    if state:
        if "on" == state:
            txt = "Turning ON"
            result = vizio.pow_on()
        elif "off" == state:
            txt = "Turning OFF"
            result = vizio.pow_off()
        else:
            txt = "Toggling power"
            result = vizio.pow_toggle()
        _LOGGER.info(txt)
        _LOGGER.info("OK" if result else "ERROR")

    else:
        is_on = vizio.get_power_state()
        _LOGGER.info("TV is on" if is_on else "TV is off")


@cli.command()
@click.argument("state", required=False)
@click.argument("amount", required=False)
@pass_tv
def volume(vizio, state, amount):
    if not amount:
        amount = 1
    else:
        amount = int(amount)
    if not state:
        state = "up"
    if "up" == state:
        txt = "Increasing volume"
        result = vizio.vol_up(amount)
    else:
        txt = "Decreasing volume"
        result = vizio.vol_down(abs(amount))
    _LOGGER.info(txt)
    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@pass_tv
def volume_current(vizio):
    _LOGGER.info("Current volume: %s", vizio.get_current_volume())


@cli.command()
@click.argument("state", required=False)
@click.argument("amount", required=False)
@pass_tv
def channel(vizio, state, amount):
    if not amount:
        amount = 1
    else:
        amount = int(amount)
    if "up" == state:
        txt = "Channel up"
        result = vizio.ch_up(amount)
    elif "down" == state:
        txt = "Channel down"
        result = vizio.ch_down(amount)
    else:
        txt = "Previous channel"
        result = vizio.ch_prev()
    _LOGGER.info(txt)
    _LOGGER.info("OK" if result else "ERROR")

@cli.command()
@click.argument("state", required=False)
@pass_tv
def remotekey(vizio, state):
    _LOGGER.info(state)
    _LOGGER.info("OK" if vizio.remotekey(state) else "ERROR")

@cli.command()
@click.argument("state", required=False)
@pass_tv
def mute(vizio, state):
    if "on" == state:
        txt = "Muting"
        result = vizio.mute_on()
    elif "off" == state:
        txt = "Un-muting"
        result = vizio.mute_off()
    else:
        txt = "Toggling mute"
        result = vizio.mute_toggle()
    _LOGGER.info(txt)
    _LOGGER.info("OK" if result else "ERROR")


@cli.command()
@pass_tv
def input_next(vizio):
    result = vizio.input_next()
    _LOGGER.info("Circling input")
    _LOGGER.info("OK" if result else "ERROR")


@cli.command(name="input")
@click.option('--name', required=True)
@pass_tv
def input_(vizio, name):
    result = vizio.input_switch(name)
    _LOGGER.info("Switching input")
    _LOGGER.info("OK" if result else "ERROR")


if __name__ == "__main__":
    cli()
