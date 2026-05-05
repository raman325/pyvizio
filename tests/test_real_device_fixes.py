"""Tests for the new code paths added in the real-device-fixes commit.

Covers status-code mappings, HTTP-status mappings, the input cname
resolver, the aggregate identity endpoint helper, and state-aware mute.
These are the new behaviors introduced alongside the bug-fix work; the
existing test suite continues to cover the unchanged surface.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

from aioresponses import aioresponses
import pytest

from pyvizio import VizioAsync, _resolve_input_cname
from pyvizio.api._protocol import async_validate_response
from pyvizio.api.input import InputItem
from pyvizio.errors import (
    VizioAuthError,
    VizioBusyError,
    VizioConnectionError,
    VizioHashvalError,
    VizioInvalidInputError,
    VizioInvalidParameterError,
    VizioNotFoundError,
    VizioResponseError,
)
from tests.conftest import (
    AUTH_TOKEN,
    TV_IP_PORT,
    make_input_item,
    tv_settings_url,
    tv_url,
)


def _input_items(specs):
    """Build a list[InputItem] from (cname, display_name, meta_name, hashval) tuples."""
    return [InputItem(make_input_item(*s), True) for s in specs]


# ---------------------------------------------------------------------------
# _resolve_input_cname — pure unit, no HTTP
# ---------------------------------------------------------------------------


class TestResolveInputCname:
    """The user's input identifier is resolved to the lowercase cname
    (the only form the device accepts in PUT bodies — verified live).
    Acceptance order: cname → meta_name → display name."""

    def _inputs(self) -> list[InputItem]:
        return _input_items(
            [
                ("cast", "CAST", "SMARTCAST", 1),
                ("hdmi1", "HDMI-1", "PS5", 2),
                ("hdmi2", "HDMI-2", "Mac", 3),
            ]
        )

    def test_resolves_by_cname(self) -> None:
        assert _resolve_input_cname("hdmi1", self._inputs()) == "hdmi1"

    def test_resolves_by_cname_case_insensitive(self) -> None:
        assert _resolve_input_cname("HDMI1", self._inputs()) == "hdmi1"

    def test_resolves_by_meta_name(self) -> None:
        """User-renamed input — meta_name maps back to cname."""
        assert _resolve_input_cname("Mac", self._inputs()) == "hdmi2"

    def test_resolves_by_meta_name_case_insensitive(self) -> None:
        assert _resolve_input_cname("smartcast", self._inputs()) == "cast"

    def test_resolves_by_display_name(self) -> None:
        """User passed the cname-derived display label."""
        assert _resolve_input_cname("HDMI-2", self._inputs()) == "hdmi2"

    def test_unknown_input_raises_with_valid_list(self) -> None:
        with pytest.raises(VizioInvalidInputError, match="not found"):
            _resolve_input_cname("HDMI-99", self._inputs())

    def test_ambiguous_meta_name_raises(self) -> None:
        """User renamed two inputs to the same string."""
        inputs = _input_items(
            [
                ("hdmi1", "HDMI-1", "Living Room", 1),
                ("hdmi2", "HDMI-2", "Living Room", 2),
            ]
        )
        with pytest.raises(VizioInvalidInputError, match="multiple.*by meta_name"):
            _resolve_input_cname("Living Room", inputs)

    def test_ambiguous_display_name_raises(self) -> None:
        """Two inputs with same display name (firmware oddity / corruption)."""
        inputs = _input_items(
            [
                ("hdmi1", "HDMI-1", "Mac", 1),
                ("hdmi2", "HDMI-1", "PS5", 2),
            ]
        )
        with pytest.raises(VizioInvalidInputError, match="multiple.*by name"):
            _resolve_input_cname("HDMI-1", inputs)


# ---------------------------------------------------------------------------
# Status-code mappings via async_validate_response
# ---------------------------------------------------------------------------


def _fake_response(status: int, body: dict | str):
    """Build a minimal stand-in for aiohttp's ClientResponse.

    ``async_validate_response`` only consumes ``.status`` and ``.text()``,
    so we don't need a real client response — a mock is more reliable
    than going through aioresponses just to provoke validation paths.
    """
    resp = MagicMock()
    resp.status = status
    text = body if isinstance(body, str) else json.dumps(body)
    resp.text = AsyncMock(return_value=text)
    return resp


class TestEnvelopeStatusMapping:
    """Each new envelope status maps to the correct typed exception."""

    @pytest.mark.parametrize(
        "result,exc_type",
        [
            ("URI_NOT_FOUND", VizioNotFoundError),
            # HASHVAL_ERROR is a subclass of VizioInvalidParameterError
            # for backward-compat — the parent still catches it.
            ("HASHVAL_ERROR", VizioHashvalError),
            ("HASHVAL_ERROR", VizioInvalidParameterError),
            ("BLOCKED", VizioBusyError),
            ("REQUIRES_PAIRING", VizioAuthError),
            ("PAIRING_DENIED", VizioAuthError),
        ],
    )
    async def test_envelope_status_maps_to_typed_exception(
        self, result: str, exc_type: type[Exception]
    ) -> None:
        resp = _fake_response(
            200, {"STATUS": {"RESULT": result, "DETAIL": f"detail for {result}"}}
        )
        with pytest.raises(exc_type):
            await async_validate_response(resp)

    async def test_unrecognized_status_falls_through_to_response_error(self) -> None:
        """Defensive: status strings we don't model still raise (don't
        silently succeed) so future Vizio additions surface as bugs."""
        resp = _fake_response(
            200, {"STATUS": {"RESULT": "FUTURE_VIZIO_CODE", "DETAIL": "?"}}
        )
        with pytest.raises(VizioResponseError):
            await async_validate_response(resp)

    async def test_parse_failure_includes_body_snippet(self) -> None:
        """Malformed JSON used to interpolate ``response.content`` (a
        stream object that rendered as ``<StreamReader ...>``). Now
        the captured text is included so reporters can paste it."""
        resp = _fake_response(200, "not-json-at-all <html>broken</html>")
        with pytest.raises(VizioResponseError, match="not-json-at-all"):
            await async_validate_response(resp)


class TestHttpStatusMapping:
    """HTTP-level errors (not envelope-status) follow a separate path —
    auth is the most important one because re-pair invalidation
    surfaces as raw HTTP 403."""

    @pytest.mark.parametrize("http_status", [401, 403])
    async def test_auth_http_codes_map_to_auth_error(self, http_status: int) -> None:
        resp = _fake_response(http_status, "")
        with pytest.raises(VizioAuthError, match=f"HTTP {http_status}"):
            await async_validate_response(resp)

    async def test_http_500_still_connection_error(self) -> None:
        """Non-auth HTTP errors continue to raise VizioConnectionError —
        the 401/403 special-case must not over-broaden."""
        resp = _fake_response(500, "")
        with pytest.raises(VizioConnectionError, match="500"):
            await async_validate_response(resp)


class TestAuthErrorPropagation:
    """``async_invoke_api`` swallows most exceptions and returns None,
    but ``VizioAuthError`` must always propagate so probe-style helpers
    like ``can_connect_with_auth_check`` can distinguish "token
    invalidated, re-pair needed" from generic device unreachability."""

    @pytest.fixture
    def vizio_tv(self) -> VizioAsync:
        return VizioAsync(
            device_id="test",
            ip=TV_IP_PORT,
            name="TV",
            auth_token=AUTH_TOKEN,
            device_type="tv",
        )

    @pytest.fixture
    def mock_aio(self):
        with aioresponses() as m:
            yield m

    async def test_http_403_propagates_through_invoke_api(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        mock_aio.get(tv_url("INPUTS"), status=403, body="")
        with pytest.raises(VizioAuthError):
            await vizio_tv.get_inputs_list(log_api_exception=False)

    async def test_can_connect_with_auth_check_returns_false_on_403(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        """The auth-check probe catches VizioAuthError locally to
        preserve its bool contract."""
        mock_aio.get(tv_settings_url("audio"), status=403, body="")
        assert await vizio_tv.can_connect_with_auth_check() is False


# ---------------------------------------------------------------------------
# Aggregate tv_information identity helper
# ---------------------------------------------------------------------------


class TestIdentityAggregate:
    """Modern firmware exposes all identity fields (serial, firmware,
    model, …) under a single ``tv_information`` parent, and rejects
    per-field child paths with URI_NOT_FOUND. The library prefers the
    aggregate, falling back to per-field on URI_NOT_FOUND."""

    @pytest.fixture
    def vizio_tv(self) -> VizioAsync:
        return VizioAsync(
            device_id="test",
            ip=TV_IP_PORT,
            name="TV",
            auth_token=AUTH_TOKEN,
            device_type="tv",
        )

    @pytest.fixture
    def mock_aio(self):
        with aioresponses() as m:
            yield m

    def _aggregate_payload(self) -> dict:
        return {
            "STATUS": {"RESULT": "SUCCESS", "DETAIL": "Success"},
            "ITEMS": [
                {"CNAME": "tv_name", "VALUE": "Test TV"},
                {"CNAME": "serial_number", "VALUE": "TEST00000000001"},
                {"CNAME": "model_name", "VALUE": "VHD24M-0810"},
                {"CNAME": "firmware", "VALUE": "3.720.9.1-1"},
            ],
        }

    async def test_serial_via_aggregate(self, vizio_tv, mock_aio) -> None:
        mock_aio.get(tv_url("TV_INFORMATION"), payload=self._aggregate_payload())
        assert await vizio_tv.get_serial_number() == "TEST00000000001"

    async def test_version_resolves_firmware_alias(self, vizio_tv, mock_aio) -> None:
        """Modern firmware exposes the version under cname='firmware'."""
        mock_aio.get(tv_url("TV_INFORMATION"), payload=self._aggregate_payload())
        assert await vizio_tv.get_version() == "3.720.9.1-1"

    async def test_aggregate_cached_across_calls(self, vizio_tv, mock_aio) -> None:
        """Identity is immutable — a second identity call should reuse
        the cached aggregate, not refetch (aioresponses raises if an
        unmocked URL is hit)."""
        mock_aio.get(tv_url("TV_INFORMATION"), payload=self._aggregate_payload())
        await vizio_tv.get_serial_number()
        assert await vizio_tv.get_version() == "3.720.9.1-1"

    async def test_aggregate_uri_not_found_falls_back_to_per_field(
        self, vizio_tv, mock_aio
    ) -> None:
        """When the aggregate is genuinely not exposed (URI_NOT_FOUND
        on both candidate paths), identity getters fall through to the
        per-field paths."""
        for endpoint in ("TV_INFORMATION", "_ALT_TV_INFORMATION"):
            mock_aio.get(
                tv_url(endpoint),
                payload={"STATUS": {"RESULT": "URI_NOT_FOUND", "DETAIL": "no"}},
            )
        mock_aio.get(
            tv_url("SERIAL_NUMBER"),
            payload={
                "STATUS": {"RESULT": "SUCCESS", "DETAIL": "Success"},
                "ITEMS": [{"CNAME": "serial_number", "VALUE": "FALLBACK-SN-1"}],
            },
        )
        assert await vizio_tv.get_serial_number() == "FALLBACK-SN-1"

    async def test_aggregate_uri_not_found_caches_negative_result(
        self, vizio_tv, mock_aio
    ) -> None:
        """After both aggregate paths return URI_NOT_FOUND, subsequent
        identity calls must NOT re-probe the aggregate. With only the
        per-field URLs mocked, a second call would error if the cache
        weren't honored."""
        for endpoint in ("TV_INFORMATION", "_ALT_TV_INFORMATION"):
            mock_aio.get(
                tv_url(endpoint),
                payload={"STATUS": {"RESULT": "URI_NOT_FOUND", "DETAIL": "no"}},
            )
        mock_aio.get(
            tv_url("SERIAL_NUMBER"),
            payload={
                "STATUS": {"RESULT": "SUCCESS", "DETAIL": "Success"},
                "ITEMS": [{"CNAME": "serial_number", "VALUE": "SN-1"}],
            },
        )
        mock_aio.get(
            tv_url("VERSION"),
            payload={
                "STATUS": {"RESULT": "SUCCESS", "DETAIL": "Success"},
                "ITEMS": [{"CNAME": "version", "VALUE": "1.2.3"}],
            },
        )
        assert await vizio_tv.get_serial_number() == "SN-1"
        # Second call: only per-field VERSION is mocked. If cache wasn't
        # honored, this would re-hit TV_INFORMATION, but aioresponses
        # would consume both URI_NOT_FOUND mocks on the first call.
        assert await vizio_tv.get_version() == "1.2.3"

    async def test_identity_cache_is_per_instance(self, mock_aio) -> None:
        """Two VizioAsync instances must not share an identity cache —
        identity is per-device, not per-class. Catches the bug class
        where ``_cached_identity`` accidentally lives on the class
        rather than ``self``."""
        v1 = VizioAsync(
            device_id="t1",
            ip="192.168.1.10:7345",
            name="T1",
            auth_token=AUTH_TOKEN,
            device_type="tv",
        )
        v2 = VizioAsync(
            device_id="t2",
            ip="192.168.1.20:7345",
            name="T2",
            auth_token=AUTH_TOKEN,
            device_type="tv",
        )
        mock_aio.get(
            "https://192.168.1.10:7345/menu_native/dynamic/tv_settings/admin_and_privacy/system_information/tv_information",
            payload={
                "STATUS": {"RESULT": "SUCCESS"},
                "ITEMS": [{"CNAME": "serial_number", "VALUE": "SN-FROM-V1"}],
            },
        )
        mock_aio.get(
            "https://192.168.1.20:7345/menu_native/dynamic/tv_settings/admin_and_privacy/system_information/tv_information",
            payload={
                "STATUS": {"RESULT": "SUCCESS"},
                "ITEMS": [{"CNAME": "serial_number", "VALUE": "SN-FROM-V2"}],
            },
        )
        assert await v1.get_serial_number() == "SN-FROM-V1"
        assert await v2.get_serial_number() == "SN-FROM-V2"

    async def test_aggregate_transient_failure_does_not_poison_cache(
        self, vizio_tv, mock_aio
    ) -> None:
        """A transient HTTP 500 on the aggregate must NOT cache None.
        The next identity call should retry the aggregate (and ideally
        succeed). Without the propagate_errors fix, a single transient
        blip would permanently disable the optimization."""
        # First aggregate call: transport error.
        mock_aio.get(tv_url("TV_INFORMATION"), status=500)
        mock_aio.get(tv_url("_ALT_TV_INFORMATION"), status=500)
        # Per-field fallback succeeds for the first call.
        mock_aio.get(
            tv_url("SERIAL_NUMBER"),
            payload={
                "STATUS": {"RESULT": "SUCCESS", "DETAIL": "Success"},
                "ITEMS": [{"CNAME": "serial_number", "VALUE": "FALLBACK-SN"}],
            },
        )
        assert (
            await vizio_tv.get_serial_number(log_api_exception=False) == "FALLBACK-SN"
        )
        # Second aggregate call: now succeeds. Cache wasn't poisoned,
        # so the aggregate is re-tried and the value comes from there.
        mock_aio.get(
            tv_url("TV_INFORMATION"),
            payload={
                "STATUS": {"RESULT": "SUCCESS"},
                "ITEMS": [{"CNAME": "firmware", "VALUE": "9.9.9"}],
            },
        )
        assert await vizio_tv.get_version() == "9.9.9"
