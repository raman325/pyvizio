import logging
from urllib.parse import urlsplit

import requests
import xmltodict

from .cmd_input import GetInputsListCommand, GetCurrentInputCommand, ChangeInputCommand
from .cmd_pair import BeginPairCommand, CancelPairCommand, PairChallengeCommand
from .cmd_power import GetPowerStateCommand
from .cmd_remote import EmulateRemoteCommand
from .cmd_settings import GetCurrentAudioCommand, GetESNCommand
from .discovery import discover
from .protocol import invoke_api, invoke_api_auth, KeyCodes

_LOGGER = logging.getLogger(__name__)

MAX_VOLUME = {"tv": 100, "soundbar": 31}


class DeviceDescription(object):
    def __init__(self, ip, name, model, udn):
        self.ip = ip
        self.name = name
        self.model = model
        self.udn = udn


class Vizio(object):
    def __init__(self, device_id, ip, name, auth_token="", device_type="tv"):
        self._device_type = device_type.lower()
        if self._device_type != "tv" and self._device_type != "soundbar":
            raise Exception(
                "Invalid device type specified. Use either 'tv' or 'soundbar'"
            )

        self._ip = ip
        self._name = name
        self._device_id = device_id
        self._auth_token = auth_token
        self._esn = self.get_esn()

    def __invoke_api(self, cmd):
        return invoke_api(self._ip, cmd, _LOGGER)

    def __invoke_api_may_need_auth(self, cmd):
        if self._auth_token is None or "" == self._auth_token:
            if self._device_type == "soundbar":
                return invoke_api(self._ip, cmd, _LOGGER)
            else:
                raise Exception(
                    "Empty auth token. To target a soundbar and bypass auth requirements, pass 'soundbar' as device_type"
                )
        return invoke_api_auth(self._ip, cmd, self._auth_token, _LOGGER)

    def __remote(self, key_list):
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
        result = self.__invoke_api_may_need_auth(cmd)
        return result is not None

    def __remote_multiple(self, key_code, num):
        key_codes = []
        for ii in range(0, num):
            key_codes.append(key_code)
        return self.__remote(key_codes)

    @staticmethod
    def discovery():
        results = []
        devices = discover("urn:dial-multiscreen-org:device:dial:1")
        for dev in devices:
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

    def get_esn(self):
        return self.__invoke_api_may_need_auth(GetESNCommand(self._device_type))

    def start_pair(self):
        return self.__invoke_api(
            BeginPairCommand(self._device_id, self._name, self._device_type)
        )

    def stop_pair(self):
        return self.__invoke_api(
            CancelPairCommand(self._device_id, self._name, self._device_type)
        )

    def pair(self, ch_type, token, pin):
        return self.__invoke_api(
            PairChallengeCommand(
                self._device_id, ch_type, token, pin, self._device_type
            )
        )

    def get_inputs(self):
        return self.__invoke_api_may_need_auth(GetInputsListCommand(self._device_type))

    def get_current_input(self):
        return self.__invoke_api_may_need_auth(
            GetCurrentInputCommand(self._device_type)
        )

    def get_power_state(self):
        return self.__invoke_api_may_need_auth(GetPowerStateCommand(self._device_type))

    def pow_on(self):
        return self.__remote("POW_ON")

    def pow_off(self):
        return self.__remote("POW_OFF")

    def pow_toggle(self):
        return self.__remote("POW_TOGGLE")

    def vol_up(self, num=1):
        return self.__remote_multiple("VOL_UP", num)

    def vol_down(self, num=1):
        return self.__remote_multiple("VOL_DOWN", num)

    def get_current_volume(self):
        return self.__invoke_api_may_need_auth(
            GetCurrentAudioCommand(self._device_type)
        )

    def get_max_volume(self):
        return MAX_VOLUME[self._device_type]

    def ch_up(self, num=1):
        return self.__remote_multiple("CH_UP", num)

    def ch_down(self, num=1):
        return self.__remote_multiple("CH_DOWN", num)

    def ch_prev(self):
        return self.__remote("CH_PREV")

    def mute_on(self):
        return self.__remote("MUTE_ON")

    def mute_off(self):
        return self.__remote("MUTE_OFF")

    def mute_toggle(self):
        return self.__remote("MUTE_TOGGLE")

    def input_next(self):
        # HACK: Single call just invoking overlay menu with current input
        return self.__remote_multiple("INPUT_NEXT", 2)

    def input_switch(self, name):
        cur_input = self.get_current_input()
        if cur_input is None:
            _LOGGER.error("Couldn't detect current input")
            return False
        return self.__invoke_api_may_need_auth(
            ChangeInputCommand(cur_input.id, name, self._device_type)
        )

    def play(self):
        return self.__remote("PLAY")

    def pause(self):
        return self.__remote("PAUSE")

    def remote(self, key):
        return self.__remote(key)

    def get_device_keys(self):
        return KeyCodes.CODES[self._device_type].keys()
