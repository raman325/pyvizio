import logging
from urllib.parse import urlsplit

import requests
import xmltodict

from .cmd_input import GetInputsListCommand, GetCurrentInputCommand, ChangeInputCommand
from .cmd_pair import BeginPairCommand, CancelPairCommand, PairChallengeCommand
from .cmd_power import GetPowerStateCommand
from .cmd_remote import EmulateRemoteCommand
from .cmd_settings import GetCurrentAudioCommand
from .discovery import discover
from .protocol import invoke_api, invoke_api_auth, KeyCodes

_LOGGER = logging.getLogger(__name__)


class DeviceDescription(object):
    def __init__(self, ip, name, model, udn):
        self.ip = ip
        self.name = name
        self.model = model
        self.udn = udn


class Vizio(object):
    def __init__(self, device_id, ip, name, auth_token=""):
        self._ip = ip
        self._name = name
        self._device_id = device_id
        self._auth_token = auth_token

    def __invoke_api(self, cmd):
        return invoke_api(self._ip, cmd, _LOGGER)

    def __invoke_api_auth(self, cmd):
        if self._auth_token is None or "" == self._auth_token:
            raise Exception("Empty auth token")
        return invoke_api_auth(self._ip, cmd, self._auth_token, _LOGGER)

    def __remote(self, key_code):
        if isinstance(key_code, list) is False:
            key_code = [key_code]
        cmd = EmulateRemoteCommand(key_code)
        result = self.__invoke_api_auth(cmd)
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
            device = DeviceDescription(split_url.hostname, root["friendlyName"], root["modelName"], root["UDN"])
            results.append(device)

        return results

    def start_pair(self):
        return self.__invoke_api(BeginPairCommand(self._device_id, self._name))

    def stop_pair(self):
        return self.__invoke_api(CancelPairCommand(self._device_id, self._name))

    def pair(self, ch_type, token, pin):
        return self.__invoke_api(PairChallengeCommand(self._device_id, ch_type, token, pin))

    def get_inputs(self):
        return self.__invoke_api_auth(GetInputsListCommand())

    def get_current_input(self):
        return self.__invoke_api_auth(GetCurrentInputCommand())

    def get_power_state(self):
        return self.__invoke_api_auth(GetPowerStateCommand())

    def pow_on(self):
        return self.__remote(KeyCodes.POW_ON)

    def pow_off(self):
        return self.__remote(KeyCodes.POW_OFF)

    def pow_toggle(self):
        return self.__remote(KeyCodes.POW_TOGGLE)

    def vol_up(self, num=1):
        return self.__remote_multiple(KeyCodes.VOL_UP, num)

    def vol_down(self, num=1):
        return self.__remote_multiple(KeyCodes.VOL_DOWN, num)

    def get_current_volume(self):
        return self.__invoke_api_auth(GetCurrentAudioCommand())

    def ch_up(self, num=1):
        return self.__remote_multiple(KeyCodes.CH_UP, num)

    def ch_down(self, num=1):
        return self.__remote_multiple(KeyCodes.CH_DOWN, num)

    def ch_prev(self):
        return self.__remote(KeyCodes.CH_PREV)

    def mute_on(self):
        return self.__remote(KeyCodes.MUTE_ON)

    def mute_off(self):
        return self.__remote(KeyCodes.MUTE_OFF)

    def mute_toggle(self):
        return self.__remote(KeyCodes.MUTE_TOGGLE)

    def input_next(self):
        # HACK: Single call just invoking overlay menu with current input
        return self.__remote_multiple(KeyCodes.INPUT_NEXT, 2)
    
    def remotekey(self, state):
        return self.__remote(KeyCodes.__dict__.get(state))

    def input_switch(self, name):
        cur_input = self.get_current_input()
        if cur_input is None:
            _LOGGER.error("Couldn't detect current input")
            return False
        return self.__invoke_api_auth(ChangeInputCommand(cur_input.id, name))
