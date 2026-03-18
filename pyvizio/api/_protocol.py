"""Vizio SmartCast API protocol constants and get and set functions."""

from __future__ import annotations

import json
from logging import Logger, getLogger
from typing import Any

from aiohttp import ClientResponse, ClientSession, ClientTimeout
from aiohttp.client import DEFAULT_TIMEOUT as AIOHTTP_DEFAULT_TIMEOUT

from pyvizio.api.base import CommandBase
from pyvizio.const import DEVICE_CLASS_SPEAKER, DEVICE_CLASS_TV, DEVICE_CONFIGS
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

# Derived from DEVICE_CONFIGS — single source of truth in const.py
ENDPOINT = {k: v.endpoints for k, v in DEVICE_CONFIGS.items()}

ITEM_CNAME = {
    "CURRENT_INPUT": "current_input",
    "ESN": "esn",
    "EQ": "eq",
    "POWER_MODE": "power_mode",
    "CHARGING_STATUS": "charging_status",
    "BATTERY_LEVEL": "battery_level",
    "SERIAL_NUMBER": "serial_number",
    "VERSION": "version",
}

KEY_ACTION = {"DOWN": "KEYDOWN", "UP": "KEYUP", "PRESS": "KEYPRESS"}

# Derived from DEVICE_CONFIGS — single source of truth in const.py
KEY_CODE = {k: v.key_codes for k, v in DEVICE_CONFIGS.items()}

PATH_MODEL = {
    DEVICE_CLASS_SPEAKER: [["name"]],
    DEVICE_CLASS_TV: [["model_name"], ["system_info", "model_name"]],
}


class PairingResponseKey:
    """Key names in responses to pairing commands."""

    AUTH_TOKEN = "auth_token"
    CHALLENGE_TYPE = "challenge_type"
    PAIRING_REQ_TOKEN = "pairing_req_token"


class ResponseKey:
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


async def async_validate_response(web_response: ClientResponse) -> dict[str, Any]:
    """Validate response to API command is as expected and return response."""
    if HTTP_OK != web_response.status:
        raise Exception(f"Device is unreachable? Status code: {web_response.status}")

    try:
        data = json.loads(await web_response.text())
        _LOGGER.debug("Response: %s", data)
    except Exception as err:
        raise Exception(f"Failed to parse response: {web_response.content}") from err

    status_obj = dict_get_case_insensitive(data, "status")

    if not status_obj:
        raise Exception("Unknown response")

    result_status = dict_get_case_insensitive(status_obj, "result")

    if result_status and result_status.lower() == STATUS_INVALID_PARAMETER:
        raise Exception("invalid value specified")
    elif not result_status or result_status.lower() != STATUS_SUCCESS:
        raise Exception(
            "unexpected status {}: {}".format(
                result_status, dict_get_case_insensitive(status_obj, "detail")
            )
        )

    return data


async def _do_request(
    active_session: ClientSession,
    method: str,
    url: str,
    headers: dict[str, Any],
    data: str,
    timeout: ClientTimeout,
) -> ClientResponse:
    """Execute a single GET or PUT request on the given session."""
    if method == "get":
        _LOGGER.debug(
            "Using Request: %s", {"method": "get", "url": url, "headers": headers}
        )
        return await active_session.get(
            url=url, headers=headers, ssl=False, timeout=timeout
        )

    headers["Content-Type"] = "application/json"
    _LOGGER.debug(
        "Using Request: %s",
        {"method": "put", "url": url, "headers": headers, "data": json.loads(data)},
    )
    return await active_session.put(
        url=url, data=data, headers=headers, ssl=False, timeout=timeout
    )


async def async_invoke_api(
    ip: str,
    command: CommandBase,
    logger: Logger,
    custom_timeout: int = None,
    headers: dict[str, Any] = None,
    log_api_exception: bool = True,
    session: ClientSession = None,
) -> Any:
    """Call API endpoints with appropriate request bodies and headers."""
    if headers is None:
        headers = {}
    url = f"https://{ip}{command.get_url()}"
    data = json.dumps(command.to_dict())
    method = command.get_method().lower()
    timeout = (
        ClientTimeout(total=custom_timeout)
        if custom_timeout
        else AIOHTTP_DEFAULT_TIMEOUT
    )
    _LOGGER.debug("Using Command: %s", command)

    try:
        if session:
            response = await _do_request(session, method, url, headers, data, timeout)
            json_obj = await async_validate_response(response)
        else:
            async with ClientSession() as local_session:
                response = await _do_request(
                    local_session, method, url, headers, data, timeout
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
