"""Vizio SmartCast API protocol constants and response validation."""

from __future__ import annotations

import json
from logging import getLogger
from typing import Any

from aiohttp import ClientResponse

from pyvizio.const import DEVICE_CONFIGS
from pyvizio.errors import (
    VizioConnectionError,
    VizioInvalidParameterError,
    VizioResponseError,
)
from pyvizio.helpers import dict_get_case_insensitive

_LOGGER = getLogger(__name__)

HTTP_OK = 200

HEADER_AUTH = "AUTH"

STATUS_SUCCESS = "success"
STATUS_INVALID_PARAMETER = "invalid_parameter"

# Derived from DEVICE_CONFIGS — single source of truth in const.py
ENDPOINT = {k: v.endpoints for k, v in DEVICE_CONFIGS.items()}

# Derived from DEVICE_CONFIGS — single source of truth in const.py
KEY_CODE = {k: v.key_codes for k, v in DEVICE_CONFIGS.items()}


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
        raise VizioConnectionError(
            f"Device is unreachable? Status code: {web_response.status}"
        )

    try:
        data = json.loads(await web_response.text())
        _LOGGER.debug("Response: %s", data)
    except Exception as err:
        raise VizioResponseError(
            f"Failed to parse response: {web_response.content}"
        ) from err

    status_obj = dict_get_case_insensitive(data, "status")

    if not status_obj:
        raise VizioResponseError("Unknown response")

    result_status = dict_get_case_insensitive(status_obj, "result")

    if result_status and result_status.lower() == STATUS_INVALID_PARAMETER:
        raise VizioInvalidParameterError("invalid value specified")
    elif not result_status or result_status.lower() != STATUS_SUCCESS:
        raise VizioResponseError(
            "unexpected status {}: {}".format(
                result_status, dict_get_case_insensitive(status_obj, "detail")
            )
        )

    return data
