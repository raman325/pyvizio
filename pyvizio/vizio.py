import logging
from urllib.parse import urlsplit

import asyncio
import requests
from requests.packages import urllib3
import xmltodict
import warnings

from .cmd_input import GetInputsListCommand, GetCurrentInputCommand, ChangeInputCommand
from .cmd_pair import BeginPairCommand, CancelPairCommand, PairChallengeCommand
from .cmd_power import GetPowerStateCommand
from .cmd_remote import EmulateRemoteCommand
from .cmd_settings import GetCurrentAudioCommand, GetESNCommand
from .discovery import discover
from .protocol import async_invoke_api, async_invoke_api_auth, KeyCodes

_LOGGER = logging.getLogger(__name__)

MAX_VOLUME = {"tv": 100, "soundbar": 31}


class DeviceDescription(object):
    def __init__(self, ip, name, model, udn):
        self.ip = ip
        self.name = name
        self.model = model
        self.udn = udn


class VizioAsync(object):
    def __init__(
        self, device_id, ip, name, auth_token="", device_type="tv", session=None
    ):
        self._device_type = device_type.lower()
        if self._device_type != "tv" and self._device_type != "soundbar":
            raise Exception(
                "Invalid device type specified. Use either 'tv' or 'soundbar'"
            )

        self._ip = ip
        self._name = name
        self._device_id = device_id
        self._auth_token = auth_token
        self._session = session

    async def __invoke_api(self, cmd, log_exception=True):
        return await async_invoke_api(
            self._ip, cmd, _LOGGER, log_exception=log_exception, session=self._session
        )

    async def __invoke_api_may_need_auth(self, cmd, log_exception=True):
        if self._auth_token is None or "" == self._auth_token:
            if self._device_type == "soundbar":
                return await async_invoke_api(
                    self._ip,
                    cmd,
                    _LOGGER,
                    log_exception=log_exception,
                    session=self._session,
                )
            else:
                raise Exception(
                    "Empty auth token. To target a soundbar and bypass auth requirements, pass 'soundbar' as device_type"
                )
        return await async_invoke_api_auth(
            self._ip,
            cmd,
            self._auth_token,
            _LOGGER,
            log_exception=log_exception,
            session=self._session,
        )

    async def __remote(self, key_list):
        key_codes = []
        if isinstance(key_list, list) is False:
            key_list = [key_list]

        for key in key_list:
            if key not in KeyCodes.CODES[self._device_type]:
                _LOGGER.error(
                    "Key Code of '%s' not found for device type of '%s'",
                    key,
                    self._device_type,
                )
                return False
            else:
                key_codes.append(KeyCodes.CODES[self._device_type][key])
        cmd = EmulateRemoteCommand(key_codes, self._device_type)
        result = await self.__invoke_api_may_need_auth(cmd)
        return result is not None

    async def __remote_multiple(self, key_code, num):
        key_codes = []
        for ii in range(0, num):
            key_codes.append(key_code)
        return await self.__remote(key_codes)

    @staticmethod
    def discovery():
        results = []
        devices = discover("urn:dial-multiscreen-org:device:dial:1")
        for dev in devices:
            with warnings.catch_warnings():
                # Ignores InsecureRequestWarning for JUST this request so that warning doesn't have to be excluded globally
                warnings.filterwarnings(
                    "ignore", category=urllib3.exceptions.InsecureRequestWarning
                )
                data = xmltodict.parse(requests.get(dev.location, verify=False).text)

            if "root" not in data or "device" not in data["root"]:
                continue

            root = data["root"]["device"]
            manufacturer = root["manufacturer"]
            if manufacturer is None or "VIZIO" != manufacturer:
                continue
            split_url = urlsplit(dev.location)
            device = DeviceDescription(
                split_url.hostname, root["friendlyName"], root["modelName"], root["UDN"]
            )
            results.append(device)

        return results

    @staticmethod
    async def validate_config(ip, auth_token, device_type):
        return await VizioAsync("", ip, "", auth_token, device_type).can_connect()

    async def can_connect(self):
        try:
            if await self.__invoke_api_may_need_auth(
                GetPowerStateCommand(self._device_type), False
            ):
                return True
            else:
                return False
        except Exception:
            return False

    async def get_esn(self):
        try:
            return await self.__invoke_api_may_need_auth(
                GetESNCommand(self._device_type)
            )
        except Exception:
            _LOGGER.error(
                "ESN unable to be retrieved, please submit issue to https://github.com/vkorn/pyvizio/issues with logs",
                exc_info=True,
            )
            return None

    async def start_pair(self):
        return await self.__invoke_api(
            BeginPairCommand(self._device_id, self._name, self._device_type)
        )

    async def stop_pair(self):
        return await self.__invoke_api(
            CancelPairCommand(self._device_id, self._name, self._device_type)
        )

    async def pair(self, ch_type, token, pin):
        return await self.__invoke_api(
            PairChallengeCommand(
                self._device_id, ch_type, token, pin, self._device_type
            )
        )

    async def get_inputs(self):
        return await self.__invoke_api_may_need_auth(
            GetInputsListCommand(self._device_type)
        )

    async def get_current_input(self):
        return await self.__invoke_api_may_need_auth(
            GetCurrentInputCommand(self._device_type)
        )

    async def get_power_state(self):
        return await self.__invoke_api_may_need_auth(
            GetPowerStateCommand(self._device_type)
        )

    async def pow_on(self):
        return await self.__remote("POW_ON")

    async def pow_off(self):
        return await self.__remote("POW_OFF")

    async def pow_toggle(self):
        return await self.__remote("POW_TOGGLE")

    async def vol_up(self, num=1):
        return await self.__remote_multiple("VOL_UP", num)

    async def vol_down(self, num=1):
        return await self.__remote_multiple("VOL_DOWN", num)

    async def get_current_volume(self):
        return await self.__invoke_api_may_need_auth(
            GetCurrentAudioCommand(self._device_type)
        )

    def get_max_volume(self):
        return MAX_VOLUME[self._device_type]

    async def ch_up(self, num=1):
        return await self.__remote_multiple("CH_UP", num)

    async def ch_down(self, num=1):
        return await self.__remote_multiple("CH_DOWN", num)

    async def ch_prev(self):
        return await self.__remote("CH_PREV")

    async def mute_on(self):
        return await self.__remote("MUTE_ON")

    async def mute_off(self):
        return await self.__remote("MUTE_OFF")

    async def mute_toggle(self):
        return await self.__remote("MUTE_TOGGLE")

    async def input_next(self):
        # HACK: Single call just invoking overlay menu with current input
        return await self.__remote_multiple("INPUT_NEXT", 2)

    async def input_switch(self, name):
        cur_input = await self.get_current_input()
        if cur_input is None:
            _LOGGER.error("Couldn't detect current input")
            return False
        return await self.__invoke_api_may_need_auth(
            ChangeInputCommand(cur_input.id, name, self._device_type)
        )

    async def play(self):
        return await self.__remote("PLAY")

    async def pause(self):
        return await self.__remote("PAUSE")

    async def remote(self, key):
        return await self.__remote(key)

    def get_device_keys(self):
        return KeyCodes.CODES[self._device_type].keys()


async def async_guess_device_type(ip, port=None):
    """
    Attempts to guess the device type by getting power state with no auth
    token.

    NOTE:
    The `ip` and `port` values passed in have to be valid for the device in
    order for this to work. This function is being used as part of a zeroconf
    discovery workflow in HomeAssistant which is why it is safe to assume that
    `ip` and `port` are valid.
    """

    if port:
        if ":" in ip:
            raise Exception("Port can't be included in both `ip` and `port` parameters")

        device = VizioAsync("test", ip + ":" + port, "test", "", "soundbar")
    else:
        if ":" not in ip:
            _LOGGER.warning(
                "May not return correct device type since a port was not specified."
            )
        device = VizioAsync("test", ip, "test", "", "soundbar")

    if await device.can_connect():
        return "soundbar"
    else:
        return "tv"


class Vizio(VizioAsync):
    def __init__(self, device_id, ip, name, auth_token="", device_type="tv"):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        super(Vizio, self).__init__(device_id, ip, name, auth_token, device_type, None)

    @staticmethod
    def discovery():
        return VizioAsync.discovery()

    @staticmethod
    def validate_config(ip, auth_token, device_type):
        return Vizio("", ip, "", auth_token, device_type).can_connect()

    def can_connect(self):
        return self.loop.run_until_complete(super(Vizio, self).can_connect())

    def get_esn(self):
        return self.loop.run_until_complete(super(Vizio, self).get_esn())

    def start_pair(self):
        return self.loop.run_until_complete(super(Vizio, self).start_pair())

    def stop_pair(self):
        return self.loop.run_until_complete(super(Vizio, self).stop_pair())

    def pair(self, ch_type, token, pin):
        return self.loop.run_until_complete(
            super(Vizio, self).pair(ch_type, token, pin)
        )

    def get_inputs(self):
        return self.loop.run_until_complete(super(Vizio, self).get_inputs())

    def get_current_input(self):
        return self.loop.run_until_complete(super(Vizio, self).get_current_input())

    def get_power_state(self):
        return self.loop.run_until_complete(super(Vizio, self).get_power_state())

    def pow_on(self):
        return self.loop.run_until_complete(super(Vizio, self).pow_on())

    def pow_off(self):
        return self.loop.run_until_complete(super(Vizio, self).pow_off())

    def pow_toggle(self):
        return self.loop.run_until_complete(super(Vizio, self).pow_toggle())

    def vol_up(self, num=1):
        return self.loop.run_until_complete(super(Vizio, self).vol_up(num))

    def vol_down(self, num=1):
        return self.loop.run_until_complete(super(Vizio, self).vol_down(num))

    def get_current_volume(self):
        return self.loop.run_until_complete(super(Vizio, self).get_current_volume())

    def get_max_volume(self):
        return super(Vizio, self).get_max_volume()

    def ch_up(self, num=1):
        return self.loop.run_until_complete(super(Vizio, self).ch_up(num))

    def ch_down(self, num=1):
        return self.loop.run_until_complete(super(Vizio, self).ch_down(num))

    def ch_prev(self):
        return self.loop.run_until_complete(super(Vizio, self).ch_prev())

    def mute_on(self):
        return self.loop.run_until_complete(super(Vizio, self).mute_on())

    def mute_off(self):
        return self.loop.run_until_complete(super(Vizio, self).mute_off())

    def mute_toggle(self):
        return self.loop.run_until_complete(super(Vizio, self).mute_toggle())

    def input_next(self):
        return self.loop.run_until_complete(super(Vizio, self).input_next())

    def input_switch(self, name):
        return self.loop.run_until_complete(super(Vizio, self).input_switch(name))

    def play(self):
        return self.loop.run_until_complete(super(Vizio, self).play())

    def pause(self):
        return self.loop.run_until_complete(super(Vizio, self).pause())

    def remote(self, key):
        return self.loop.run_until_complete(super(Vizio, self).remote(key))

    def get_device_keys(self):
        return super(Vizio, self).get_device_keys()


def guess_device_type(ip, port=None):
    """
    Attempts to guess the device type by getting power state with no auth
    token.

    NOTE:
    The `ip` and `port` values passed in have to be valid for the device in
    order for this to work. This function is being used as part of a zeroconf
    discovery workflow in HomeAssistant which is why it is safe to assume that
    `ip` and `port` are valid.
    """

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(async_guess_device_type(ip, port))
