"""Low-level HTTP transport for Vizio SmartCast API.

Owns the aiohttp session, auth token, and semaphore.
Constructs URLs, adds auth headers, validates responses,
and maps failures to typed exceptions.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import json
import logging
from typing import Any

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client import DEFAULT_TIMEOUT as AIOHTTP_DEFAULT_TIMEOUT

from pyvizio._parse import _ci_get
from pyvizio.errors import (
    VizioConnectionError,
    VizioInvalidParameterError,
    VizioResponseError,
)

_LOGGER = logging.getLogger(__name__)

HEADER_AUTH = "AUTH"
STATUS_SUCCESS = "success"
STATUS_INVALID_PARAMETER = "invalid_parameter"
HTTP_OK = 200


@dataclass
class SmartCastClient:
    """Low-level HTTP client for SmartCast devices."""

    host: str
    auth_token: str | None = None
    timeout: int | None = None
    session: ClientSession | None = None
    max_concurrent: int = 1
    _semaphore: asyncio.Semaphore | None = field(default=None, repr=False, init=False)

    def _get_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self._semaphore

    def _client_timeout(self) -> ClientTimeout:
        if self.timeout is not None:
            return ClientTimeout(total=self.timeout)
        return AIOHTTP_DEFAULT_TIMEOUT

    async def get(self, path: str) -> dict[str, Any]:
        """GET endpoint, validate, return JSON. Raises on failure."""
        return await self._request("get", path)

    async def put(
        self, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """PUT with JSON body, validate, return JSON. Raises on failure."""
        return await self._request("put", path, body)

    async def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"https://{self.host}{path}"
        headers: dict[str, str] = {}
        if self.auth_token:
            headers[HEADER_AUTH] = self.auth_token
        timeout = self._client_timeout()

        async with self._get_semaphore():
            if self.session:
                return await self._do_request(
                    self.session, method, url, headers, body, timeout
                )
            else:
                async with ClientSession() as local_session:
                    return await self._do_request(
                        local_session, method, url, headers, body, timeout
                    )

    async def _do_request(
        self,
        session: ClientSession,
        method: str,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
        timeout: ClientTimeout,
    ) -> dict[str, Any]:
        try:
            if method == "get":
                _LOGGER.debug("GET %s headers=%s", url, headers)
                resp = await session.get(
                    url=url, headers=headers, ssl=False, timeout=timeout
                )
            else:
                data = json.dumps(body or {})
                headers["Content-Type"] = "application/json"
                _LOGGER.debug("PUT %s headers=%s body=%s", url, headers, body)
                resp = await session.put(
                    url=url, data=data, headers=headers, ssl=False, timeout=timeout
                )

            return await self._validate_response(resp)
        except (VizioConnectionError, VizioResponseError, VizioInvalidParameterError):
            raise
        except Exception as e:
            raise VizioConnectionError(f"Connection failed: {e}") from e

    @staticmethod
    async def _validate_response(resp) -> dict[str, Any]:
        if HTTP_OK != resp.status:
            raise VizioConnectionError(
                f"Device is unreachable? Status code: {resp.status}"
            )

        try:
            data = json.loads(await resp.text())
            _LOGGER.debug("Response: %s", data)
        except Exception as err:
            raise VizioResponseError(
                f"Failed to parse response: {resp.content}"
            ) from err

        status_obj = _ci_get(data, "status")
        if not status_obj:
            raise VizioResponseError("Unknown response")

        result_status = _ci_get(status_obj, "result")
        if result_status and result_status.lower() == STATUS_INVALID_PARAMETER:
            raise VizioInvalidParameterError("invalid value specified")
        elif not result_status or result_status.lower() != STATUS_SUCCESS:
            raise VizioResponseError(
                f"unexpected status {result_status}: {_ci_get(status_obj, 'detail')}"
            )

        return data

    async def close(self) -> None:
        """Close owned session if we created it (no-op if external session)."""
        pass
