from abc import abstractmethod
import json
from logging import Logger
from typing import Any, Dict, Optional

from aiohttp import ClientResponse, ClientSession, ClientTimeout
from aiohttp.client import DEFAULT_TIMEOUT
import jsonpickle

from .const import DEVICE_CLASS_SPEAKER, DEVICE_CLASS_TV

HTTP_OK = 200


class CommandBase(object):
    def __init__(self) -> None:
        self._url = ""

    @property
    def _method(self) -> str:
        return "PUT"

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, new_url: str) -> None:
        self._url = new_url

    def get_url(self) -> str:
        return self._url

    def get_method(self) -> str:
        return self._method

    @abstractmethod
    def process_response(self, json_obj: Dict[str, Any]) -> None:
        return None


class InfoCommandBase(CommandBase):
    def __init__(self) -> None:
        super(InfoCommandBase, self).__init__()

    @property
    def _method(self) -> str:
        return "GET"

    @property
    def url(self) -> str:
        return CommandBase.url.fget(self)

    @url.setter
    def url(self, new_url: str) -> None:
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
    URI_NOT_FOUND = "URI_NOT_FOUND"

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
        DEVICE_CLASS_TV: {
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
        DEVICE_CLASS_SPEAKER: {
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
        DEVICE_CLASS_TV: {
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
        DEVICE_CLASS_SPEAKER: {
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


def get_json_obj(json_obj: Dict[str, Any], key: str) -> Any:
    key = key.lower()
    for k, v in json_obj.items():
        if k.lower() == key:
            return v
    return None


async def async_validate_response(web_response: ClientResponse) -> Dict[str, Any]:
    if HTTP_OK != web_response.status:
        raise Exception(
            "Device is unreachable? Status code: {0}".format(web_response.status)
        )
    try:
        data = json.loads(await web_response.text())
    except Exception:
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


async def async_invoke_api(
    ip: str,
    command: CommandBase,
    logger: Logger,
    timeout: int,
    headers: Optional[Dict[str, Any]] = None,
    log_api_exception: bool = True,
    session: Optional[ClientSession] = None,
) -> Any:
    if timeout:
        timeout = ClientTimeout(total=timeout)
    else:
        timeout = DEFAULT_TIMEOUT

    if headers is None:
        headers = {}

    try:
        method = command.get_method()
        if ":" not in ip:
            ip = ip + ":7345"
        url = "https://{0}{1}".format(ip, command.get_url())
        data = jsonpickle.encode(command, unpicklable=False)

        if session:
            if "get" == method.lower():
                response = await session.get(
                    url=url, headers=headers, ssl=False, timeout=timeout
                )
            else:
                headers["Content-Type"] = "application/json"
                response = await session.put(
                    url=url, data=str(data), headers=headers, ssl=False, timeout=timeout
                )

            json_obj = await async_validate_response(response)
        else:
            async with ClientSession() as local_session:
                if "get" == method.lower():
                    response = await local_session.get(
                        url=url, headers=headers, ssl=False, timeout=timeout
                    )
                else:
                    headers["Content-Type"] = "application/json"
                    response = await local_session.put(
                        url=url,
                        data=str(data),
                        headers=headers,
                        ssl=False,
                        timeout=timeout,
                    )

                json_obj = await async_validate_response(response)

        return command.process_response(json_obj)
    except Exception as e:
        if log_api_exception:
            logger.error("Failed to execute command: %s", e)
        return None


async def async_invoke_api_auth(
    ip: str,
    command: CommandBase,
    auth_token: str,
    logger: Logger,
    timeout: int,
    log_api_exception: bool = True,
    session: Optional[ClientSession] = None,
) -> Any:
    headers = {ProtoConstants.HEADER_AUTH: auth_token}
    return await async_invoke_api(
        ip,
        command,
        logger,
        timeout,
        headers,
        log_api_exception=log_api_exception,
        session=session,
    )
