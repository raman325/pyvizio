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
from .const import (
    DEFAULT_DEVICE_CLASS,
    DEFAULT_TIMEOUT,
    DEVICE_CLASS_SOUNDBAR,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
)
from .discovery import discover
from .protocol import KeyCodes, async_invoke_api, async_invoke_api_auth

_LOGGER = logging.getLogger(__name__)

MAX_VOLUME = {DEVICE_CLASS_TV: 100, DEVICE_CLASS_SPEAKER: 31}


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
        device_type=DEFAULT_DEVICE_CLASS,
        session=None,
    ):
        self._device_type = device_type.lower()
        if self._device_type == DEVICE_CLASS_SOUNDBAR:
            _LOGGER.error(
                f"The '{DEVICE_CLASS_SOUNDBAR}' device type has been deprecated and will be removed soon. Please use the '{DEVICE_CLASS_SPEAKER}' device type going forward"
            )
            self._device_type = DEVICE_CLASS_SPEAKER

        if (
            self._device_type != DEVICE_CLASS_TV
            and self._device_type != DEVICE_CLASS_SPEAKER
        ):
            raise Exception(
                f"Invalid device type specified. Use either '{DEVICE_CLASS_TV}' or '{DEVICE_CLASS_SPEAKER}'"
            )

        self._ip = ip
        self._name = name
        self._device_id = device_id
        self._auth_token = auth_token
        self._session = session

    async def __invoke_api(self, cmd, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await async_invoke_api(
            self._ip,
            cmd,
            _LOGGER,
            timeout,
            log_api_exception=log_api_exception,
            session=self._session,
        )

    async def __invoke_api_may_need_auth(
        self, cmd, timeout=DEFAULT_TIMEOUT, log_api_exception=True
    ):
        if self._auth_token is None or "" == self._auth_token:
            if self._device_type == DEVICE_CLASS_SPEAKER:
                return await async_invoke_api(
                    self._ip,
                    cmd,
                    _LOGGER,
                    timeout,
                    log_api_exception=log_api_exception,
                    session=self._session,
                )
            else:
                raise Exception(
                    f"Empty auth token. To target a speaker and bypass auth requirements, pass '{DEVICE_CLASS_SPEAKER}' as device_type"
                )
        return await async_invoke_api_auth(
            self._ip,
            cmd,
            self._auth_token,
            _LOGGER,
            timeout,
            log_api_exception=log_api_exception,
            session=self._session,
        )

    async def __remote(self, key_list, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
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
            EmulateRemoteCommand(key_codes, self._device_type),
            timeout,
            log_api_exception,
        )
        return result is not None

    async def __remote_multiple(
        self, key_code, num, timeout=DEFAULT_TIMEOUT, log_api_exception=True
    ):
        key_codes = []
        for ii in range(0, num):
            key_codes.append(key_code)
        return await self.__remote(key_codes, timeout, log_api_exception)

    @staticmethod
    def discovery(timeout=DEFAULT_TIMEOUT):
        results = []
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
    async def validate_ha_config(ip, auth_token, device_type, timeout=DEFAULT_TIMEOUT):
        return await VizioAsync("", ip, "", auth_token, device_type).can_connect(
            timeout
        )

    @staticmethod
    async def get_unique_id(
        ip, auth_token, device_type, timeout=DEFAULT_TIMEOUT, log_api_exception=True
    ):
        return await VizioAsync("", ip, "", auth_token, device_type).get_esn(
            timeout, log_api_exception
        )

    async def can_connect(self, timeout=DEFAULT_TIMEOUT):
        try:
            if await self.__invoke_api_may_need_auth(
                GetCurrentAudioCommand(self._device_type), timeout, False
            ):
                return True
            else:
                return False
        except Exception:
            return False

    async def get_esn(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        try:
            return await self.__invoke_api_may_need_auth(
                GetESNCommand(self._device_type), timeout, log_api_exception
            )
        except Exception:
            _LOGGER.error(
                "ESN unable to be retrieved, please submit issue to https://github.com/vkorn/pyvizio/issues with logs",
                exc_info=True,
            )
            return None

    async def start_pair(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__invoke_api(
            BeginPairCommand(self._device_id, self._name, self._device_type),
            timeout,
            log_api_exception,
        )

    async def stop_pair(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__invoke_api(
            CancelPairCommand(self._device_id, self._name, self._device_type),
            timeout,
            log_api_exception,
        )

    async def pair(
        self, ch_type, token, pin, timeout=DEFAULT_TIMEOUT, log_api_exception=True
    ):
        return await self.__invoke_api(
            PairChallengeCommand(
                self._device_id, ch_type, token, pin, self._device_type
            ),
            timeout,
            log_api_exception,
        )

    async def get_inputs(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__invoke_api_may_need_auth(
            GetInputsListCommand(self._device_type), timeout, log_api_exception
        )

    async def get_current_input(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__invoke_api_may_need_auth(
            GetCurrentInputCommand(self._device_type), timeout, log_api_exception
        )

    async def get_power_state(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__invoke_api_may_need_auth(
            GetPowerStateCommand(self._device_type), timeout, log_api_exception
        )

    async def pow_on(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote("POW_ON", timeout, log_api_exception)

    async def pow_off(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote("POW_OFF", timeout, log_api_exception)

    async def pow_toggle(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote("POW_TOGGLE", timeout, log_api_exception)

    async def vol_up(self, num=1, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote_multiple("VOL_UP", num, log_api_exception)

    async def vol_down(self, num=1, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote_multiple("VOL_DOWN", num, timeout, log_api_exception)

    async def get_current_volume(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__invoke_api_may_need_auth(
            GetCurrentAudioCommand(self._device_type), timeout, log_api_exception
        )

    def get_max_volume(self):
        return MAX_VOLUME[self._device_type]

    async def ch_up(self, num=1, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote_multiple("CH_UP", num, timeout, log_api_exception)

    async def ch_down(self, num=1, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote_multiple("CH_DOWN", num, timeout, log_api_exception)

    async def ch_prev(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote("CH_PREV", timeout, log_api_exception)

    async def mute_on(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote("MUTE_ON", timeout, log_api_exception)

    async def mute_off(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote("MUTE_OFF", timeout, log_api_exception)

    async def mute_toggle(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote("MUTE_TOGGLE", timeout, log_api_exception)

    async def input_next(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        # HACK: Single call just invoking overlay menu with current input
        return await self.__remote_multiple("INPUT_NEXT", 2, timeout, log_api_exception)

    async def input_switch(self, name, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        cur_input = await self.get_current_input(timeout, log_api_exception)
        if cur_input is None:
            _LOGGER.error("Couldn't detect current input")
            return False
        return await self.__invoke_api_may_need_auth(
            ChangeInputCommand(cur_input.id, name, self._device_type),
            timeout,
            log_api_exception,
        )

    async def play(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote("PLAY", timeout, log_api_exception)

    async def pause(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote("PAUSE", timeout, log_api_exception)

    async def remote(self, key, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return await self.__remote(key, timeout, log_api_exception)

    def get_device_keys(self):
        return KeyCodes.CODES[self._device_type].keys()


async def async_guess_device_type(ip, port=None, timeout=DEFAULT_TIMEOUT):
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

        device = VizioAsync("test", ip + ":" + port, "test", "", DEVICE_CLASS_SPEAKER)
    else:
        if ":" not in ip:
            _LOGGER.warning(
                "May not return correct device type since a port was not specified."
            )
        device = VizioAsync("test", ip, "test", "", DEVICE_CLASS_SPEAKER)

    if await device.can_connect(timeout):
        return DEVICE_CLASS_SPEAKER
    else:
        return DEVICE_CLASS_TV


class Vizio(VizioAsync):
    def __init__(
        self, device_id, ip, name, auth_token="", device_type=DEFAULT_DEVICE_CLASS
    ):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        super(Vizio, self).__init__(
            device_id, ip, name, auth_token, device_type, session=None
        )

    @staticmethod
    def discovery(timeout=DEFAULT_TIMEOUT):
        return VizioAsync.discovery(timeout)

    @staticmethod
    def validate_ha_config(ip, auth_token, device_type, timeout=DEFAULT_TIMEOUT):
        return Vizio("", ip, "", auth_token, device_type).can_connect(timeout)

    @staticmethod
    def get_unique_id(
        ip, auth_token, device_type, timeout=DEFAULT_TIMEOUT, log_api_exception=True
    ):
        return Vizio("", ip, "", auth_token, device_type).get_esn(
            timeout, log_api_exception
        )

    def can_connect(self, timeout=DEFAULT_TIMEOUT):
        return self.loop.run_until_complete(
            self.loop.create_task(super(Vizio, self).can_connect(timeout))
        )

    def get_esn(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).get_esn(timeout, log_api_exception)
            )
        )

    def start_pair(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).start_pair(timeout, log_api_exception)
            )
        )

    def stop_pair(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).stop_pair(timeout, log_api_exception)
            )
        )

    def pair(
        self, ch_type, token, pin, timeout=DEFAULT_TIMEOUT, log_api_exception=True
    ):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).pair(ch_type, token, pin, timeout, log_api_exception)
            )
        )

    def get_inputs(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).get_inputs(timeout, log_api_exception)
            )
        )

    def get_current_input(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).get_current_input(timeout, log_api_exception)
            )
        )

    def get_power_state(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).get_power_state(timeout, log_api_exception)
            )
        )

    def pow_on(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(super(Vizio, self).pow_on(timeout, log_api_exception))
        )

    def pow_off(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).pow_off(timeout, log_api_exception)
            )
        )

    def pow_toggle(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).pow_toggle(timeout, log_api_exception)
            )
        )

    def vol_up(self, num=1, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).vol_up(num, timeout, log_api_exception)
            )
        )

    def vol_down(self, num=1, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).vol_down(num, timeout, log_api_exception)
            )
        )

    def get_current_volume(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).get_current_volume(timeout, log_api_exception)
            )
        )

    def get_max_volume(self):
        return super(Vizio, self).get_max_volume()

    def ch_up(self, num=1, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).ch_up(num, timeout, log_api_exception)
            )
        )

    def ch_down(self, num=1, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).ch_down(num, timeout, log_api_exception)
            )
        )

    def ch_prev(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).ch_prev(timeout, log_api_exception)
            )
        )

    def mute_on(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).mute_on(timeout, log_api_exception)
            )
        )

    def mute_off(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).mute_off(timeout, log_api_exception)
            )
        )

    def mute_toggle(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).mute_toggle(timeout, log_api_exception)
            )
        )

    def input_next(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).input_next(timeout, log_api_exception)
            )
        )

    def input_switch(self, name, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).input_switch(name, timeout, log_api_exception)
            )
        )

    def play(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(super(Vizio, self).play(timeout, log_api_exception))
        )

    def pause(self, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(super(Vizio, self).pause(timeout, log_api_exception))
        )

    def remote(self, key, timeout=DEFAULT_TIMEOUT, log_api_exception=True):
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).remote(key, timeout, log_api_exception)
            )
        )

    def get_device_keys(self):
        return super(Vizio, self).get_device_keys()


def guess_device_type(ip, port=None, timeout=DEFAULT_TIMEOUT):
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
    return loop.run_until_complete(
        self.loop.create_task(async_guess_device_type(ip, port, timeout))
    )
