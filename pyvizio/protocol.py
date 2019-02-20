from abc import abstractmethod

import requests
import jsonpickle
import json

HTTP_OK = 200


class CommandBase(object):
    @property
    def _method(self):
        return "PUT"

    @property
    @abstractmethod
    def _url(self):
        return ""

    def get_url(self):
        return self._url

    def get_method(self):
        return self._method

    @abstractmethod
    def process_response(self, json_obj):
        return None


class InfoCommandBase(CommandBase):
    @property
    def _method(self):
        return "GET"


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
    VOL_DOWN = (5, 0)
    VOL_UP = (5, 1)
    MUTE_OFF = (5, 2)
    MUTE_ON = (5, 3)
    MUTE_TOGGLE = (5, 4)
    INPUT_NEXT = (7, 1)
    CH_DOWN = (8, 0)
    CH_UP = (8, 1)
    CH_PREV = (8, 2)
    POW_OFF = (11, 0)
    POW_ON = (11, 1)
    POW_TOGGLE = (11, 2)
    DP_DOWN = (3, 0)
    DP_LEFT = (3, 1)
    DP_RIGHT = (3, 7)
    DP_UP = (3, 8)
    DP_ENTER = (3, 2)
    BACK = (4, 0)
    INFO = (4, 6)
    MENU = (4, 8)
    HOME = (4, 15)

    class KeyPressActions(object):
        KEY_DOWN = "KEYDOWN"
        KEY_UP = "KEYUP"
        KEY_PRESS = "KEYPRESS"


class CNames(object):
    class Audio(object):
        VOLUME = "volume"


def get_json_obj(json_obj, key):
    key = key.lower()
    for k, v in json_obj.items():
        if k.lower() == key:
            return v
    return None


def validate_response(web_response):
    if HTTP_OK != web_response.status_code:
        raise Exception("TV is unreachable? Status code: {0}".format(web_response.status_code))
    try:
        data = json.loads(web_response.text)
    except:
        raise Exception("Failed to parse response: {0}".format(web_response.content))
    status_obj = get_json_obj(data, "status")
    if status_obj is None:
        raise Exception("Unknown response")
    result_status = get_json_obj(status_obj, "result")
    if result_status is None or result_status.lower() != ProtoConstants.STATUS_SUCCESS:
        raise Exception("Unexpected response {0}: {1}".format(result_status, get_json_obj(status_obj, "detail")))
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
            response = requests.request(method=method, data=str(data), url=url, headers=headers, verify=False)
        json_obj = validate_response(response)
        return command.process_response(json_obj)
    except Exception as e:
        logger.error("Failed to execute command: %s", e)
        return None


def invoke_api_auth(ip, command, auth_token, logger):
    headers = {ProtoConstants.HEADER_AUTH: auth_token}
    return invoke_api(ip, command, logger, headers)
