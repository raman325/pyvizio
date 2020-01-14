import asyncio
import logging
import warnings
from urllib.parse import urlsplit

import requests
import xmltodict
from requests.packages import urllib3

from .cmd_input import ChangeInputCommand, GetCurrentInputCommand, GetInputsListCommand
from .cmd_pair import BeginPairCommand, CancelPairCommand, PairChallengeCommand
from .cmd_power import GetPowerStateCommand
from .cmd_remote import EmulateRemoteCommand
from .cmd_settings import GetCurrentAudioCommand, GetESNCommand
from .const import DEFAULT_TIMEOUT
from .discovery import discover
from .protocol import KeyCodes, async_invoke_api, async_invoke_api_auth

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
        self,
        device_id,
        ip,
        name,
        auth_token="",
        device_type="tv",
        timeout=None,
        session=None,
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
        if not timeout:
            timeout = DEFAULT_TIMEOUT
        self._timeout = timeout

    async def __invoke_api(self, cmd, log_api_exception=True):
        return await async_invoke_api(
            self._ip,
            cmd,
            _LOGGER,
            self._timeout,
            log_api_exception=log_api_exception,
            session=self._session,
        )

    async def __invoke_api_may_need_auth(self, cmd, log_api_exception=True):
        if self._auth_token is None or "" == self._auth_token:
            if self._device_type == "soundbar":
                return await async_invoke_api(
                    self._ip,
                    cmd,
                    _LOGGER,
                    self._timeout,
                    log_api_exception=log_api_exception,
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
            self._timeout,
            log_api_exception=log_api_exception,
            session=self._session,
        )

    async def __remote(self, key_list, log_api_exception=True):
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

        result = await self.__invoke_api_may_need_auth(
            EmulateRemoteCommand(key_codes, self._device_type), log_api_exception
        )
        return result is not None

    async def __remote_multiple(self, key_code, num, log_api_exception=True):
        key_codes = []
        for ii in range(0, num):
            key_codes.append(key_code)
        return await self.__remote(key_codes, log_api_exception)

    @staticmethod
    def discovery(timeout=None):
        results = []
        if not timeout:
            timeout = DEFAULT_TIMEOUT
        devices = discover("urn:dial-multiscreen-org:device:dial:1")
        for dev in devices:
            with warnings.catch_warnings():
                # Ignores InsecureRequestWarning for JUST this request so that warning doesn't have to be excluded globally
                warnings.filterwarnings(
                    "ignore", category=urllib3.exceptions.InsecureRequestWarning
                )
                data = xmltodict.parse(
                    requests.get(dev.location, verify=False, timeout=timeout).text
                )

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
    async def validate_ha_config(ip, auth_token, device_type):
        return await VizioAsync("", ip, "", auth_token, device_type).can_connect()

    @staticmethod
    async def get_unique_id(ip, auth_token, device_type, log_api_exception=True):
        return await VizioAsync("", ip, "", auth_token, device_type).get_esn(
            log_api_exception
        )

    async def can_connect(self):
        try:
            if await self.__invoke_api_may_need_auth(
                GetCurrentAudioCommand(self._device_type), False
            ):
                return True
            else:
                return False
        except Exception:
            return False

    async def get_esn(self, log_api_exception=True):
        try:
            return await self.__invoke_api_may_need_auth(
                GetESNCommand(self._device_type), log_api_exception
            )
        except Exception:
            _LOGGER.error(
                "ESN unable to be retrieved, please submit issue to https://github.com/vkorn/pyvizio/issues with logs",
                exc_info=True,
            )
            return None

    async def start_pair(self, log_api_exception=True):
        return await self.__invoke_api(
            BeginPairCommand(self._device_id, self._name, self._device_type),
            log_api_exception,
        )

    async def stop_pair(self, log_api_exception=True):
        return await self.__invoke_api(
            CancelPairCommand(self._device_id, self._name, self._device_type),
            log_api_exception,
        )

    async def pair(self, ch_type, token, pin, log_api_exception=True):
        return await self.__invoke_api(
            PairChallengeCommand(
                self._device_id, ch_type, token, pin, self._device_type
            ),
            log_api_exception,
        )

    async def get_inputs(self, log_api_exception=True):
        return await self.__invoke_api_may_need_auth(
            GetInputsListCommand(self._device_type), log_api_exception
        )

    async def get_current_input(self, log_api_exception=True):
        return await self.__invoke_api_may_need_auth(
            GetCurrentInputCommand(self._device_type), log_api_exception
        )

    async def get_power_state(self, log_api_exception=True):
        return await self.__invoke_api_may_need_auth(
            GetPowerStateCommand(self._device_type), log_api_exception
        )

    async def pow_on(self, log_api_exception=True):
        return await self.__remote("POW_ON", log_api_exception)

    async def pow_off(self, log_api_exception=True):
        return await self.__remote("POW_OFF", log_api_exception)

    async def pow_toggle(self, log_api_exception=True):
        return await self.__remote("POW_TOGGLE", log_api_exception)

    async def vol_up(self, num=1, log_api_exception=True):
        return await self.__remote_multiple("VOL_UP", num, log_api_exception)

    async def vol_down(self, num=1, log_api_exception=True):
        return await self.__remote_multiple("VOL_DOWN", num, log_api_exception)

    async def get_current_volume(self, log_api_exception=True):
        return await self.__invoke_api_may_need_auth(
            GetCurrentAudioCommand(self._device_type), log_api_exception
        )

    def get_max_volume(self):
        return MAX_VOLUME[self._device_type]

    async def ch_up(self, num=1, log_api_exception=True):
        return await self.__remote_multiple("CH_UP", num, log_api_exception)

    async def ch_down(self, num=1, log_api_exception=True):
        return await self.__remote_multiple("CH_DOWN", num, log_api_exception)

    async def ch_prev(self, log_api_exception=True):
        return await self.__remote("CH_PREV", log_api_exception)

    async def mute_on(self, log_api_exception=True):
        return await self.__remote("MUTE_ON", log_api_exception)

    async def mute_off(self, log_api_exception=True):
        return await self.__remote("MUTE_OFF", log_api_exception)

    async def mute_toggle(self, log_api_exception=True):
        return await self.__remote("MUTE_TOGGLE", log_api_exception)

    async def input_next(self, log_api_exception=True):
        # HACK: Single call just invoking overlay menu with current input
        return await self.__remote_multiple("INPUT_NEXT", 2, log_api_exception)

    async def input_switch(self, name, log_api_exception=True):
        cur_input = await self.get_current_input(log_api_exception)
        if cur_input is None:
            _LOGGER.error("Couldn't detect current input")
            return False
        return await self.__invoke_api_may_need_auth(
            ChangeInputCommand(cur_input.id, name, self._device_type), log_api_exception
        )

    async def play(self, log_api_exception=True):
        return await self.__remote("PLAY", log_api_exception)

    async def pause(self, log_api_exception=True):
        return await self.__remote("PAUSE", log_api_exception)

    async def remote(self, key, log_api_exception=True):
        return await self.__remote(key, log_api_exception)

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
    def __init__(
        self, device_id, ip, name, auth_token="", device_type="tv", timeout=None
    ):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        super(Vizio, self).__init__(
            device_id, ip, name, auth_token, device_type, timeout=timeout, session=None
        )

    @staticmethod
    def discovery():
        return VizioAsync.discovery()

    @staticmethod
    def validate_ha_config(ip, auth_token, device_type):
        return Vizio("", ip, "", auth_token, device_type).can_connect()

    @staticmethod
    def get_unique_id(ip, auth_token, device_type, log_api_exception=True):
        return Vizio("", ip, "", auth_token, device_type).get_esn(log_api_exception)

    def can_connect(self):
        return self.loop.run_until_complete(super(Vizio, self).can_connect())

    def get_esn(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).get_esn(log_api_exception)
        )

    def start_pair(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).start_pair(log_api_exception)
        )

    def stop_pair(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).stop_pair(log_api_exception)
        )

    def pair(self, ch_type, token, pin, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).pair(ch_type, token, pin, log_api_exception)
        )

    def get_inputs(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).get_inputs(log_api_exception)
        )

    def get_current_input(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).get_current_input(log_api_exception)
        )

    def get_power_state(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).get_power_state(log_api_exception)
        )

    def pow_on(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).pow_on(log_api_exception)
        )

    def pow_off(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).pow_off(log_api_exception)
        )

    def pow_toggle(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).pow_toggle(log_api_exception)
        )

    def vol_up(self, num=1, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).vol_up(num, log_api_exception)
        )

    def vol_down(self, num=1, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).vol_down(num, log_api_exception)
        )

    def get_current_volume(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).get_current_volume(log_api_exception)
        )

    def get_max_volume(self):
        return super(Vizio, self).get_max_volume()

    def ch_up(self, num=1, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).ch_up(num, log_api_exception)
        )

    def ch_down(self, num=1, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).ch_down(num, log_api_exception)
        )

    def ch_prev(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).ch_prev(log_api_exception)
        )

    def mute_on(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).mute_on(log_api_exception)
        )

    def mute_off(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).mute_off(log_api_exception)
        )

    def mute_toggle(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).mute_toggle(log_api_exception)
        )

    def input_next(self, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).input_next(log_api_exception)
        )

    def input_switch(self, name, log_api_exception=True):
        return self.loop.run_until_complete(super(Vizio, self).input_switch(name, log_api_exception))

    def play(self, log_api_exception=True):
        return self.loop.run_until_complete(super(Vizio, self).play(log_api_exception))

    def pause(self, log_api_exception=True):
        return self.loop.run_until_complete(super(Vizio, self).pause(log_api_exception))

    def remote(self, key, log_api_exception=True):
        return self.loop.run_until_complete(
            super(Vizio, self).remote(key, log_api_exception)
        )

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
