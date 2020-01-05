from abc import abstractmethod

import requests
import jsonpickle
import json

HTTP_OK = 200


class CommandBase(object):
    def __init__(self):
        self._url = ""

    @property
    def _method(self):
        return "PUT"

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, new_url):
        self._url = new_url

    def get_url(self):
        return self._url

    def get_method(self):
        return self._method

    @abstractmethod
    def process_response(self, json_obj):
        return None


class InfoCommandBase(CommandBase):
    def __init__(self):
        super(InfoCommandBase, self).__init__()

    @property
    def _method(self):
        return "GET"

    @property
    def url(self):
        return CommandBase.url.fget(self)

    @url.setter
    def url(self, new_url):
        CommandBase.url.fset(self, new_url)


class ProtoConstants(object):
    ACTION_MODIFY = "MODIFY"
    HEADER_AUTH = "AUTH"
    STATUS_SUCCESS = "success"
    RESPONSE_ITEM = "item"
    RESPONSE_ITEMS = "items"
    AUTH_TOKEN = "auth_token"
    CHALLENGE_TYPE = "challenge_type"
    PAIRING_REQ_TOKEN = "pairing_req_token"

    class Item(object):
        HASHVAL = "hashval"
        CNAME = "cname"
        TYPE = "type"
        NAME = "name"
        VALUE = "value"
        METADATA = "metadata"
        ELEMENTS = "elements"


class KeyCodes(object):
    CODES = {
        "tv": {
            "SEEK_FWD": (2, 0),
            "SEEK_BACK": (2, 1),
            "PAUSE": (2, 2),
            "PLAY": (2, 3),
            "DOWN": (3, 0),
            "LEFT": (3, 1),
            "OK": (3, 2),
            "UP": (3, 3),
            "LEFT2": (3, 4),
            "RIGHT": (3, 5),
            "BACK": (4, 0),
            "SMARTCAST": (4, 3),
            "CC_TOGGLE": (4, 4),
            "INFO": (4, 6),
            "MENU": (4, 8),
            "HOME": (4, 15),
            "VOL_DOWN": (5, 0),
            "VOL_UP": (5, 1),
            "MUTE_OFF": (5, 2),
            "MUTE_ON": (5, 3),
            "MUTE_TOGGLE": (5, 4),
            "PIC_MODE": (6, 0),
            "PIC_SIZE": (6, 2),
            "INPUT_NEXT": (7, 1),
            "CH_DOWN": (8, 0),
            "CH_UP": (8, 1),
            "CH_PREV": (8, 2),
            "EXIT": (9, 0),
            "POW_OFF": (11, 0),
            "POW_ON": (11, 1),
            "POW_TOGGLE": (11, 2),
        },
        "soundbar": {
            "PAUSE": (2, 2),
            "PLAY": (2, 3),
            "VOL_DOWN": (5, 0),
            "VOL_UP": (5, 1),
            "MUTE_OFF": (5, 2),
            "MUTE_ON": (5, 3),
            "MUTE_TOGGLE": (5, 4),
            "POW_OFF": (11, 0),
            "POW_ON": (11, 1),
            "POW_TOGGLE": (11, 2),
        },
    }

    class KeyPressActions(object):
        KEY_DOWN = "KEYDOWN"
        KEY_UP = "KEYUP"
        KEY_PRESS = "KEYPRESS"


class Endpoints(object):
    ENDPOINTS = {
        "tv": {
            "BEGIN_PAIR": "/pairing/start",
            "FINISH_PAIR": "/pairing/pair",
            "CANCEL_PAIR": "/pairing/cancel",
            "INPUTS": "/menu_native/dynamic/tv_settings/devices/name_input",
            "CURR_INPUT": "/menu_native/dynamic/tv_settings/devices/current_input",
            "SET_INPUT": "/menu_native/dynamic/tv_settings/devices/current_input",
            "ESN": "/menu_native/dynamic/tv_settings/system/system_information/uli_information/esn",
            "POWER": "/state/device/power_mode",
            "KEY_PRESS": "/key_command/",
            "VOLUME": "/menu_native/dynamic/tv_settings/audio/volume",
        },
        "soundbar": {
            "BEGIN_PAIR": "/pairing/start",
            "FINISH_PAIR": "/pairing/pair",
            "CANCEL_PAIR": "/pairing/cancel",
            "INPUTS": "/menu_native/dynamic/audio_settings/input",
            "CURR_INPUT": "/menu_native/dynamic/audio_settings/input/current_input",
            "SET_INPUT": "/menu_native/dynamic/audio_settings/input/current_input",
            "ESN": "/menu_native/dynamic/audio_settings/system/system_information/uli_information/esn",
            "POWER": "/state/device/power_mode",
            "KEY_PRESS": "/key_command/",
            "VOLUME": "/menu_native/dynamic/audio_settings/audio/volume",
        },
    }


class CNames(object):
    class Audio(object):
        VOLUME = "volume"

    class ESN(object):
        ESN = "esn"


def get_json_obj(json_obj, key):
    key = key.lower()
    for k, v in json_obj.items():
        if k.lower() == key:
            return v
    return None


def validate_response(web_response):
    if HTTP_OK != web_response.status_code:
        raise Exception(
            "TV is unreachable? Status code: {0}".format(web_response.status_code)
        )
    try:
        data = json.loads(web_response.text)
    except:
        raise Exception("Failed to parse response: {0}".format(web_response.content))
    status_obj = get_json_obj(data, "status")
    if status_obj is None:
        raise Exception("Unknown response")
    result_status = get_json_obj(status_obj, "result")
    if result_status is None or result_status.lower() != ProtoConstants.STATUS_SUCCESS:
        raise Exception(
            "Unexpected response {0}: {1}".format(
                result_status, get_json_obj(status_obj, "detail")
            )
        )
    return data


def invoke_api(ip, command, logger, headers=None):
    if headers is None:
        headers = {}

    try:
        method = command.get_method()
        if ":" not in ip:
            ip = ip + ":7345"
        url = "https://{0}{1}".format(ip, command.get_url())
        data = jsonpickle.encode(command, unpicklable=False)
        if "get" == method.lower():
            response = requests.get(url=url, headers=headers, verify=False)
        else:
            headers["Content-Type"] = "application/json"
            response = requests.request(
                method=method, data=str(data), url=url, headers=headers, verify=False
            )
        json_obj = validate_response(response)
        return command.process_response(json_obj)
    except Exception as e:
        logger.error("Failed to execute command: %s", e)
        return None


def invoke_api_auth(ip, command, auth_token, logger):
    headers = {ProtoConstants.HEADER_AUTH: auth_token}
    return invoke_api(ip, command, logger, headers)
