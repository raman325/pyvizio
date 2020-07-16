"""Vizio SmartCast API protocol constants and get and set functions."""

import json
from logging import getLogger, Logger
from typing import Any, Dict

from aiohttp import ClientResponse, ClientSession, ClientTimeout
from aiohttp.client import DEFAULT_TIMEOUT as AIOHTTP_DEFAULT_TIMEOUT
import jsonpickle
from pyvizio.api.base import CommandBase
from pyvizio.const import DEVICE_CLASS_SPEAKER, DEVICE_CLASS_TV
from pyvizio.helpers import dict_get_case_insensitive

_LOGGER = getLogger(__name__)

HTTP_OK = 200

ACTION_MODIFY = "MODIFY"

HEADER_AUTH = "AUTH"

STATUS_SUCCESS = "success"
STATUS_URI_NOT_FOUND = "uri_not_found"
STATUS_INVALID_PARAMETER = "invalid_parameter"

TYPE_SLIDER = "t_value_abs_v1"
TYPE_LIST = "t_list_v1"
TYPE_VALUE = "t_value_v1"
TYPE_MENU = "t_menu_v1"
TYPE_X_LIST = "t_list_x_v1"

ENDPOINT = {
    DEVICE_CLASS_TV: {
        "BEGIN_PAIR": "/pairing/start",
        "FINISH_PAIR": "/pairing/pair",
        "CANCEL_PAIR": "/pairing/cancel",
        "INPUTS": "/menu_native/dynamic/tv_settings/devices/name_input",
        "CURRENT_INPUT": "/menu_native/dynamic/tv_settings/devices/current_input",
        "ESN": "/menu_native/dynamic/tv_settings/system/system_information/uli_information/esn",
        "SERIAL_NUMBER": "/menu_native/dynamic/tv_settings/system/system_information/tv_information/serial_number",
        "VERSION": "/menu_native/dynamic/tv_settings/system/system_information/tv_information/version",
        "DEVICE_INFO": "/state/device/deviceinfo",
        "POWER_MODE": "/state/device/power_mode",
        "KEY_PRESS": "/key_command/",
        "SETTINGS": "/menu_native/dynamic/tv_settings",
        "SETTINGS_OPTIONS": "/menu_native/static/tv_settings",
        "CURRENT_APP": "/app/current",
        "LAUNCH_APP": "/app/launch",
    },
    DEVICE_CLASS_SPEAKER: {
        "BEGIN_PAIR": "/pairing/start",
        "FINISH_PAIR": "/pairing/pair",
        "CANCEL_PAIR": "/pairing/cancel",
        "INPUTS": "/menu_native/dynamic/audio_settings/input",
        "CURRENT_INPUT": "/menu_native/dynamic/audio_settings/input/current_input",
        "ESN": "/menu_native/dynamic/audio_settings/system/system_information/uli_information/esn",
        "SERIAL_NUMBER": "/menu_native/dynamic/audio_settings/system/system_information/speaker_information/serial_number",
        "VERSION": "/menu_native/dynamic/audio_settings/system/system_information/speaker_information/version",
        "DEVICE_INFO": "/state/device/deviceinfo",
        "POWER_MODE": "/state/device/power_mode",
        "KEY_PRESS": "/key_command/",
        "SETTINGS": "/menu_native/dynamic/audio_settings",
        "SETTINGS_OPTIONS": "/menu_native/static/audio_settings",
    },
}

ITEM_CNAME = {
    "CURRENT_INPUT": "current_input",
    "ESN": "esn",
    "EQ": "eq",
    "POWER_MODE": "power_mode",
    "SERIAL_NUMBER": "serial_number",
    "VERSION": "version",
}

KEY_ACTION = {"DOWN": "KEYDOWN", "UP": "KEYUP", "PRESS": "KEYPRESS"}

KEY_CODE = {
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

PATH_MODEL = {
    DEVICE_CLASS_SPEAKER: [["name"]],
    DEVICE_CLASS_TV: [["model_name"], ["system_info", "model_name"]],
}


class PairingResponseKey(object):
    """Key names in responses to pairing commands."""

    AUTH_TOKEN = "auth_token"
    CHALLENGE_TYPE = "challenge_type"
    PAIRING_REQ_TOKEN = "pairing_req_token"


class ResponseKey(object):
    """Key names in responses to API commands."""

    HASHVAL = "hashval"
    CNAME = "cname"
    TYPE = "type"
    NAME = "name"
    VALUE = "value"
    METADATA = "metadata"
    ELEMENTS = "elements"
    ITEM = "item"
    ITEMS = "items"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    CENTER = "center"


async def async_validate_response(web_response: ClientResponse) -> Dict[str, Any]:
    """Validate response to API command is as expected and return response."""
    if HTTP_OK != web_response.status:
        raise Exception(
            "Device is unreachable? Status code: {0}".format(web_response.status)
        )

    try:
        data = json.loads(await web_response.text())
        _LOGGER.debug("Response: %s", data)
    except Exception:
        raise Exception("Failed to parse response: {0}".format(web_response.content))

    status_obj = dict_get_case_insensitive(data, "status")

    if not status_obj:
        raise Exception("Unknown response")

    result_status = dict_get_case_insensitive(status_obj, "result")

    if result_status and result_status.lower() == STATUS_INVALID_PARAMETER:
        raise Exception("invalid value specified")
    elif not result_status or result_status.lower() != STATUS_SUCCESS:
        raise Exception(
            "unexpected status {0}: {1}".format(
                result_status, dict_get_case_insensitive(status_obj, "detail")
            )
        )

    return data


async def async_invoke_api(
    ip: str,
    command: CommandBase,
    logger: Logger,
    custom_timeout: int = None,
    headers: Dict[str, Any] = {},
    log_api_exception: bool = True,
    session: ClientSession = None,
) -> Any:
    """Call API endpoints with appropriate request bodies and headers."""
    method = command.get_method()
    url = f"https://{ip}{command.get_url()}"
    data = jsonpickle.encode(command, unpicklable=False)
    _LOGGER.debug("Using Command: %s", command)

    if not custom_timeout:
        timeout = AIOHTTP_DEFAULT_TIMEOUT
    else:
        timeout = ClientTimeout(total=custom_timeout)

    if not headers:
        headers = {}

    try:
        if session:
            if "get" == method.lower():
                _LOGGER.debug(
                    "Using Request: %s",
                    {"method": "get", "url": url, "headers": headers},
                )
                response = await session.get(
                    url=url, headers=headers, ssl=False, timeout=timeout
                )
            else:
                timeout = AIOHTTP_DEFAULT_TIMEOUT
                headers["Content-Type"] = "application/json"
                _LOGGER.debug(
                    "Using Request: %s",
                    {
                        "method": "put",
                        "url": url,
                        "headers": headers,
                        "data": json.loads(data),
                    },
                )
                response = await session.put(
                    url=url, data=str(data), headers=headers, ssl=False, timeout=timeout
                )

            json_obj = await async_validate_response(response)
        else:
            async with ClientSession() as local_session:
                if "get" == method.lower():
                    _LOGGER.debug(
                        "Using Request: %s",
                        {"method": "get", "url": url, "headers": headers},
                    )
                    response = await local_session.get(
                        url=url, headers=headers, ssl=False, timeout=timeout
                    )
                else:
                    timeout = AIOHTTP_DEFAULT_TIMEOUT
                    headers["Content-Type"] = "application/json"
                    _LOGGER.debug(
                        "Using Request: %s",
                        {
                            "method": "put",
                            "url": url,
                            "headers": headers,
                            "data": json.loads(data),
                        },
                    )
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
    logger: Logger,
    auth_token: str = None,
    custom_timeout: int = None,
    log_api_exception: bool = True,
    session: ClientSession = None,
) -> Any:
    """Call auth protected API endpoints using CommandBase and subclass request bodies."""

    return await async_invoke_api(
        ip,
        command,
        logger,
        custom_timeout=custom_timeout,
        headers={HEADER_AUTH: auth_token},
        log_api_exception=log_api_exception,
        session=session,
    )
