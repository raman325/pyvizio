"""Vizio SmartCast API protocol constants and get and set functions."""

from __future__ import annotations

import json
from logging import Logger, getLogger
from typing import Any

from aiohttp import ClientResponse, ClientSession, ClientTimeout
from aiohttp.client import DEFAULT_TIMEOUT as AIOHTTP_DEFAULT_TIMEOUT

from pyvizio.api.base import CommandBase
from pyvizio.const import DEVICE_CLASS_SPEAKER, DEVICE_CLASS_TV, DEVICE_CONFIGS
from pyvizio.errors import (
    VizioAuthError,
    VizioBusyError,
    VizioConnectionError,
    VizioError,
    VizioHashvalError,
    VizioInvalidParameterError,
    VizioNotFoundError,
    VizioResponseError,
)
from pyvizio.helpers import dict_get_case_insensitive

_LOGGER = getLogger(__name__)

HTTP_OK = 200

ACTION_MODIFY = "MODIFY"

HEADER_AUTH = "AUTH"

STATUS_SUCCESS = "success"
STATUS_URI_NOT_FOUND = "uri_not_found"
STATUS_INVALID_PARAMETER = "invalid_parameter"
STATUS_HASHVAL_ERROR = "hashval_error"
STATUS_BLOCKED = "blocked"
STATUS_REQUIRES_PAIRING = "requires_pairing"
STATUS_PAIRING_DENIED = "pairing_denied"

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


async def async_validate_response(
    web_response: ClientResponse, *, skip_envelope: bool = False
) -> dict[str, Any]:
    """Validate response to API command is as expected and return response.

    When ``skip_envelope`` is True the HTTP-level checks still apply
    (200 vs 401/403/etc.) but the SCPL ``STATUS``/``ITEMS`` envelope
    validation is skipped — used for non-standard endpoints like
    ``/state_extended`` whose payloads use flat top-level keys with
    no envelope wrapper.
    """
    # Auth-related rejections come back as raw HTTP 401/403 (not as
    # SCPL envelope errors). Verified live on VHD24M-0810 fw 3.720.9.1-1:
    # re-pairing with the same device_id immediately invalidates the
    # previous token, and subsequent calls with the old token return
    # raw HTTP 403 (not the PAIRING_DENIED envelope).
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

    if skip_envelope:
        return data

    status_obj = dict_get_case_insensitive(data, "status")

    if not status_obj:
        raise VizioResponseError("Unknown response")

    result_status = dict_get_case_insensitive(status_obj, "result")
    result_lower = result_status.lower() if result_status else ""
    detail = dict_get_case_insensitive(status_obj, "detail") or ""

    # HASHVAL_ERROR gets a more specific subclass so callers that want
    # to retry on stale-hashval (refetch + resend) can do so without
    # broadening to all invalid-parameter errors. Existing
    # ``except VizioInvalidParameterError`` blocks still catch it via
    # the parent. Captured live: stale-hashval PUTs return HASHVAL_ERROR
    # on modern firmware, INVALID_PARAMETER on older.
    if result_lower == STATUS_HASHVAL_ERROR:
        raise VizioHashvalError(detail or "stale hashval — refetch and retry")
    if result_lower == STATUS_INVALID_PARAMETER:
        raise VizioInvalidParameterError(detail or "invalid value specified")
    # URI_NOT_FOUND is HTTP-200-with-status, not HTTP 404. Modern
    # firmware uses it for paths that don't exist (per-field identity
    # leaves on firmwares that only expose the aggregate). Surface as
    # VizioNotFoundError so callers using ``propagate_errors=True``
    # (currently only the multi-path-fallback in
    # ``__get_identity_aggregate``) can distinguish it from transient
    # failures and chain to the next candidate path. Default callers
    # see ``None`` via the standard swallow path.
    if result_lower == STATUS_URI_NOT_FOUND:
        raise VizioNotFoundError(detail or "endpoint not found on device")
    if result_lower == STATUS_BLOCKED:
        raise VizioBusyError(detail or "device blocked the request")
    if result_lower in (STATUS_REQUIRES_PAIRING, STATUS_PAIRING_DENIED):
        raise VizioAuthError(detail or result_lower)
    if result_lower != STATUS_SUCCESS:
        raise VizioResponseError(f"unexpected status {result_status}: {detail}")

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
    skip_envelope: bool = False,
    propagate_errors: bool = False,
) -> Any:
    """Call API endpoints with appropriate request bodies and headers.

    ``skip_envelope=True`` forwards to :func:`async_validate_response` to
    skip SCPL ``STATUS``/``ITEMS`` validation for endpoints with
    non-standard response shapes (e.g. ``/state_extended``).

    ``propagate_errors=True`` re-raises every :class:`VizioError` instead
    of returning ``None``. Used by callers (e.g. multi-path-fallback
    helpers like ``__get_identity_aggregate``) that need to distinguish
    typed failure modes — ``VizioNotFoundError`` for "not exposed at
    this path, try next" vs transport/busy errors that should not poison
    a cache. ``VizioAuthError`` always propagates regardless of this
    flag.
    """
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
            json_obj = await async_validate_response(
                response, skip_envelope=skip_envelope
            )
        else:
            async with ClientSession() as local_session:
                response = await _do_request(
                    local_session, method, url, headers, data, timeout
                )
                json_obj = await async_validate_response(
                    response, skip_envelope=skip_envelope
                )

        return command.process_response(json_obj)
    except VizioAuthError:
        # Always propagate auth errors — callers like
        # ``can_connect_with_auth_check`` rely on the typed exception to
        # distinguish "token invalidated, re-pair needed" from generic
        # network / device failures, and that distinction would be lost
        # if we returned None.
        raise
    except VizioError as e:
        if propagate_errors:
            raise
        if log_api_exception:
            logger.error("Failed to execute command: %s", e)
        return None
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
    skip_envelope: bool = False,
    propagate_errors: bool = False,
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
        skip_envelope=skip_envelope,
        propagate_errors=propagate_errors,
    )
