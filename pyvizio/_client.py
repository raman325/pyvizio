"""Low-level HTTP transport for Vizio SmartCast API.

Owns the aiohttp session, auth token, and semaphore.
Constructs URLs, adds auth headers, validates responses,
and maps failures to typed exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client import DEFAULT_TIMEOUT as AIOHTTP_DEFAULT_TIMEOUT

from pyvizio._parse import _ci_get
from pyvizio.errors import (
    VizioAuthError,
    VizioBusyError,
    VizioConnectionError,
    VizioInvalidParameterError,
    VizioNotFoundError,
    VizioResponseError,
)

_LOGGER = logging.getLogger(__name__)

HEADER_AUTH = "AUTH"
STATUS_SUCCESS = "success"
STATUS_INVALID_PARAMETER = "invalid_parameter"
STATUS_URI_NOT_FOUND = "uri_not_found"
"""Modern firmware (~3.7+) returns this for paths the device doesn't
expose. Mapped to :class:`VizioNotFoundError`. Verified live on
VHD24M-0810 fw 3.720.9.1-1: per-field identity paths
(``.../tv_information/esn``, etc.) return this status while the
aggregate parent path returns SUCCESS."""

STATUS_HASHVAL_ERROR = "hashval_error"
"""Modern firmware distinguishes stale-hashval errors from generic
``invalid_parameter``. Both surface as
:class:`VizioInvalidParameterError` so any caller's existing retry
logic fires for either code."""

STATUS_BLOCKED = "blocked"
"""Device temporarily refused — another writer holds a lock, or the
device is mid-update."""

STATUS_REQUIRES_PAIRING = "requires_pairing"
STATUS_PAIRING_DENIED = "pairing_denied"

HTTP_OK = 200


@dataclass
class SmartCastClient:
    """Low-level HTTP client for SmartCast devices.

    Throttling is the caller's concern — :class:`pyvizio.VizioAsync`
    owns the semaphore that serializes its own requests. We
    deliberately don't add a second per-client semaphore here because
    ``VizioAsync._make_client`` instantiates a fresh ``SmartCastClient``
    per request, which would make a per-client semaphore dead weight
    (it would throttle a single request against itself, never across
    requests).
    """

    host: str
    auth_token: str | None = None
    timeout: int | None = None
    session: ClientSession | None = None

    def _client_timeout(self) -> ClientTimeout:
        if self.timeout is not None:
            return ClientTimeout(total=self.timeout)
        return AIOHTTP_DEFAULT_TIMEOUT

    async def get(self, path: str) -> dict[str, Any]:
        """GET endpoint, validate, return JSON. Raises on failure."""
        return await self._request("get", path)

    async def get_raw_json(self, path: str) -> dict[str, Any]:
        """GET an endpoint that returns a non-standard envelope.

        Used for ``/state_extended``, which returns flat top-level
        keys (``POWER_MODE``, ``APP_CURRENT``, …) with no
        ``STATUS``/``ITEMS`` wrapper. The HTTP-level checks (200 vs
        401/403/etc.) still apply, but envelope-status validation is
        skipped — the caller is responsible for shape validation.
        """
        return await self._request("get", path, skip_envelope=True)

    async def put(
        self, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """PUT with JSON body, validate, return JSON. Raises on failure."""
        return await self._request("put", path, body)

    async def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        skip_envelope: bool = False,
    ) -> dict[str, Any]:
        url = f"https://{self.host}{path}"
        headers: dict[str, str] = {}
        if self.auth_token:
            headers[HEADER_AUTH] = self.auth_token
        timeout = self._client_timeout()

        if self.session:
            return await self._do_request(
                self.session,
                method,
                url,
                headers,
                body,
                timeout,
                skip_envelope=skip_envelope,
            )
        async with ClientSession() as local_session:
            return await self._do_request(
                local_session,
                method,
                url,
                headers,
                body,
                timeout,
                skip_envelope=skip_envelope,
            )

    async def _do_request(
        self,
        session: ClientSession,
        method: str,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
        timeout: ClientTimeout,
        *,
        skip_envelope: bool = False,
    ) -> dict[str, Any]:
        try:
            # ``async with`` ensures the response is released on every
            # exit path, including when ``_validate_response`` raises.
            # Without this, errors leak the connection back to the pool
            # uncleared and the pool eventually exhausts on long-running
            # callers (HA polling).
            if method == "get":
                _LOGGER.debug("GET %s headers=%s", url, headers)
                async with session.get(
                    url=url, headers=headers, ssl=False, timeout=timeout
                ) as resp:
                    return await self._validate_response(
                        resp, skip_envelope=skip_envelope
                    )
            else:
                data = json.dumps(body or {})
                headers["Content-Type"] = "application/json"
                _LOGGER.debug("PUT %s headers=%s body=%s", url, headers, body)
                async with session.put(
                    url=url, data=data, headers=headers, ssl=False, timeout=timeout
                ) as resp:
                    return await self._validate_response(
                        resp, skip_envelope=skip_envelope
                    )
        except (
            VizioAuthError,
            VizioBusyError,
            VizioConnectionError,
            VizioInvalidParameterError,
            VizioNotFoundError,
            VizioResponseError,
        ):
            raise
        except Exception as e:
            raise VizioConnectionError(f"Connection failed: {e}") from e

    @staticmethod
    async def _validate_response(
        resp, *, skip_envelope: bool = False
    ) -> dict[str, Any]:
        # Auth-related rejections come back as raw HTTP 401/403 (not as
        # SCPL envelope errors), so they need to surface as
        # VizioAuthError. Verified live on VHD24M-0810 fw 3.720.9.1-1:
        # re-pairing with the same device_id invalidates the previous
        # token, and subsequent calls with the old token return HTTP 403.
        if resp.status in (401, 403):
            raise VizioAuthError(
                f"device returned HTTP {resp.status} — token rejected "
                f"(may have been invalidated by re-pair)"
            )
        if HTTP_OK != resp.status:
            raise VizioConnectionError(
                f"Device is unreachable? Status code: {resp.status}"
            )

        # Capture the body text first so the parse-failure exception
        # can include a useful snippet of what came back. The previous
        # version interpolated ``resp.content`` (a stream object) into
        # the message, which printed as ``<StreamReader ...>`` and was
        # useless for debugging.
        try:
            body_text = await resp.text()
        except Exception as err:
            raise VizioResponseError(
                "Failed to read response body (transport error)"
            ) from err
        try:
            data = json.loads(body_text)
            _LOGGER.debug("Response: %s", data)
        except ValueError as err:
            raise VizioResponseError(
                f"Failed to parse response body (truncated to 200 chars): "
                f"{body_text[:200]}"
            ) from err

        # Endpoints with non-standard envelope shape (currently only
        # ``/state_extended``) skip the STATUS/ITEMS validation —
        # caller is responsible for shape interpretation.
        if skip_envelope:
            return data

        status_obj = _ci_get(data, "status")
        if not status_obj:
            raise VizioResponseError("Unknown response")

        result_status = _ci_get(status_obj, "result")
        result_lower = result_status.lower() if result_status else ""
        detail = _ci_get(status_obj, "detail") or ""

        # Both INVALID_PARAMETER and the more-specific HASHVAL_ERROR map
        # to the same exception so any hashval-race retry logic fires
        # for both. Captured live: stale-hashval PUTs return HASHVAL_ERROR
        # on modern firmware, INVALID_PARAMETER on older.
        if result_lower in (STATUS_INVALID_PARAMETER, STATUS_HASHVAL_ERROR):
            raise VizioInvalidParameterError(detail or "invalid value specified")

        # URI_NOT_FOUND is HTTP-200-with-status, not HTTP 404. Modern
        # firmware uses it for paths that don't exist (per-field
        # identity leaves on firmwares that only expose the aggregate).
        # Surface as VizioNotFoundError so multi-path-fallback callers
        # can chain to the next candidate path.
        if result_lower == STATUS_URI_NOT_FOUND:
            raise VizioNotFoundError(detail or "endpoint not found on device")

        if result_lower == STATUS_BLOCKED:
            raise VizioBusyError(detail or "device blocked the request")

        if result_lower in (STATUS_REQUIRES_PAIRING, STATUS_PAIRING_DENIED):
            raise VizioAuthError(detail or result_lower)

        if result_lower != STATUS_SUCCESS:
            raise VizioResponseError(f"unexpected status {result_status}: {detail}")

        return data

    async def close(self) -> None:
        """Close owned session if we created it (no-op if external session)."""
        pass
