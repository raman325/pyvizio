"""Vizio SmartCast API protocol constants and response validation."""

from __future__ import annotations

import json
from logging import getLogger
from typing import Any

from aiohttp import ClientResponse

from pyvizio.const import DEVICE_CONFIGS
from pyvizio.errors import (
    VizioAuthError,
    VizioBusyError,
    VizioConnectionError,
    VizioInvalidParameterError,
    VizioNotFoundError,
    VizioResponseError,
)
from pyvizio.helpers import dict_get_case_insensitive

_LOGGER = getLogger(__name__)

HTTP_OK = 200

HEADER_AUTH = "AUTH"

STATUS_SUCCESS = "success"
STATUS_INVALID_PARAMETER = "invalid_parameter"
STATUS_URI_NOT_FOUND = "uri_not_found"
STATUS_HASHVAL_ERROR = "hashval_error"
STATUS_BLOCKED = "blocked"
STATUS_REQUIRES_PAIRING = "requires_pairing"
STATUS_PAIRING_DENIED = "pairing_denied"

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
    """Validate response to API command is as expected and return response.

    Mirrors :meth:`pyvizio._client.SmartCastClient._validate_response` so
    callers using either the new or compat path see the same exception
    types for the same device replies. Without this parity, code paths
    that still call ``async_validate_response`` would collapse every
    non-SUCCESS into ``VizioResponseError`` while the new client raised
    typed exceptions for the same status strings.
    """
    # Auth-related rejections come back as raw HTTP 401/403 (not as
    # SCPL envelope errors). Verified live: re-pair invalidation
    # surfaces this way.
    if web_response.status in (401, 403):
        raise VizioAuthError(
            f"device returned HTTP {web_response.status} — token rejected "
            f"(may have been invalidated by re-pair)"
        )
    if HTTP_OK != web_response.status:
        raise VizioConnectionError(
            f"Device is unreachable? Status code: {web_response.status}"
        )

    try:
        body_text = await web_response.text()
    except Exception as err:
        raise VizioResponseError(
            "Failed to read response body (transport error)"
        ) from err
    try:
        data = json.loads(body_text)
        _LOGGER.debug("Response: %s", data)
    except ValueError as err:
        raise VizioResponseError(
            f"Failed to parse response body (truncated to 200 chars): {body_text[:200]}"
        ) from err

    status_obj = dict_get_case_insensitive(data, "status")

    if not status_obj:
        raise VizioResponseError("Unknown response")

    result_status = dict_get_case_insensitive(status_obj, "result")
    result_lower = result_status.lower() if result_status else ""
    detail = dict_get_case_insensitive(status_obj, "detail") or ""

    # Both INVALID_PARAMETER and HASHVAL_ERROR map to the same exception
    # so any caller's existing retry logic fires for both.
    if result_lower in (STATUS_INVALID_PARAMETER, STATUS_HASHVAL_ERROR):
        raise VizioInvalidParameterError(detail or "invalid value specified")
    if result_lower == STATUS_URI_NOT_FOUND:
        raise VizioNotFoundError(detail or "endpoint not found on device")
    if result_lower == STATUS_BLOCKED:
        raise VizioBusyError(detail or "device blocked the request")
    if result_lower in (STATUS_REQUIRES_PAIRING, STATUS_PAIRING_DENIED):
        raise VizioAuthError(detail or result_lower)
    if result_lower != STATUS_SUCCESS:
        raise VizioResponseError(f"unexpected status {result_status}: {detail}")

    return data
