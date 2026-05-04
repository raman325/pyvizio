"""Tests for the new code paths added in the real-device-fixes commit.

Covers status-code mappings, HTTP-status mappings, the input cname
resolver, and the aggregate identity endpoint helper. These are the
new behaviors introduced alongside the bug-fix work; the existing
test suite continues to cover the unchanged surface.
"""

from __future__ import annotations

from aioresponses import aioresponses
import pytest

from pyvizio import VizioAsync
from pyvizio._vizio import _resolve_input_cname
from pyvizio.errors import (
    VizioAuthError,
    VizioBusyError,
    VizioInvalidInputError,
    VizioInvalidParameterError,
    VizioNotFoundError,
    VizioResponseError,
)
from tests.conftest import (
    AUTH_TOKEN,
    TV_IP_PORT,
    make_inputs_list_response,
    tv_url,
)

# ---------------------------------------------------------------------------
# _resolve_input_cname — pure unit, no HTTP
# ---------------------------------------------------------------------------


class TestResolveInputCname:
    """The user's input identifier is resolved to the lowercase cname
    (the only form the device accepts in PUT bodies — verified live).
    Acceptance order: cname → meta_name → display name."""

    def _inputs(self) -> dict:
        return make_inputs_list_response(
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
        inputs = make_inputs_list_response(
            [
                ("hdmi1", "HDMI-1", "Living Room", 1),
                ("hdmi2", "HDMI-2", "Living Room", 2),
            ]
        )
        with pytest.raises(VizioInvalidInputError, match="multiple"):
            _resolve_input_cname("Living Room", inputs)

    def test_skips_synthetic_current_input(self) -> None:
        """Older firmware includes a synthetic ``current_input`` item
        in the inputs list — must be excluded from resolution targets."""
        inputs = {
            "STATUS": {"RESULT": "SUCCESS", "DETAIL": "Success"},
            "ITEMS": [
                {"CNAME": "current_input", "NAME": "Current Input", "VALUE": "HDMI-1"},
                {
                    "CNAME": "hdmi1",
                    "NAME": "HDMI-1",
                    "VALUE": {"NAME": "HDMI-1", "METADATA": ""},
                    "HASHVAL": 5,
                },
            ],
        }
        assert _resolve_input_cname("HDMI-1", inputs) == "hdmi1"


# ---------------------------------------------------------------------------
# Status-code mappings via SmartCastClient._validate_response
# ---------------------------------------------------------------------------


@pytest.fixture
def vizio_tv() -> VizioAsync:
    return VizioAsync(
        device_id="test",
        ip=TV_IP_PORT,
        name="TV",
        auth_token=AUTH_TOKEN,
        device_type="tv",
    )


@pytest.fixture
def mock_aio() -> aioresponses:
    with aioresponses() as m:
        yield m


class TestEnvelopeStatusMapping:
    """Each new envelope status maps to the correct typed exception.
    Tests use a known auth-required endpoint that surfaces the raw
    exception class via a method that doesn't swallow it."""

    async def _provoke(
        self, vizio_tv: VizioAsync, mock_aio, status: str
    ) -> Exception | None:
        """GET an arbitrary endpoint with the given STATUS.RESULT and
        return the exception raised (or None on success)."""
        from pyvizio.errors import VizioError

        mock_aio.get(
            tv_url("POWER_MODE"),
            payload={"STATUS": {"RESULT": status, "DETAIL": f"detail for {status}"}},
        )
        try:
            await vizio_tv._get(vizio_tv._endpoint("POWER_MODE"))
        except VizioError as e:
            return e
        return None

    async def test_uri_not_found_maps_to_not_found_error(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        e = await self._provoke(vizio_tv, mock_aio, "URI_NOT_FOUND")
        assert isinstance(e, VizioNotFoundError)
        assert "detail for URI_NOT_FOUND" in str(e)

    async def test_hashval_error_maps_to_invalid_parameter(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        e = await self._provoke(vizio_tv, mock_aio, "HASHVAL_ERROR")
        assert isinstance(e, VizioInvalidParameterError)

    async def test_blocked_maps_to_busy(self, vizio_tv: VizioAsync, mock_aio) -> None:
        e = await self._provoke(vizio_tv, mock_aio, "BLOCKED")
        assert isinstance(e, VizioBusyError)

    async def test_requires_pairing_maps_to_auth_error(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        e = await self._provoke(vizio_tv, mock_aio, "REQUIRES_PAIRING")
        assert isinstance(e, VizioAuthError)

    async def test_pairing_denied_maps_to_auth_error(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        e = await self._provoke(vizio_tv, mock_aio, "PAIRING_DENIED")
        assert isinstance(e, VizioAuthError)

    async def test_unrecognized_status_falls_through_to_response_error(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        """Defensive: status strings we don't model still raise (don't
        silently succeed) so future Vizio additions surface as bugs."""
        e = await self._provoke(vizio_tv, mock_aio, "FUTURE_VIZIO_CODE")
        assert isinstance(e, VizioResponseError)


class TestHttpStatusMapping:
    """HTTP-level errors (not envelope-status) follow a separate path —
    auth is the most important one because re-pair invalidation
    surfaces as raw HTTP 403."""

    async def test_http_403_maps_to_auth_error(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        mock_aio.get(tv_url("POWER_MODE"), status=403, body="")
        with pytest.raises(VizioAuthError, match="HTTP 403"):
            await vizio_tv._get(vizio_tv._endpoint("POWER_MODE"))

    async def test_http_401_maps_to_auth_error(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        mock_aio.get(tv_url("POWER_MODE"), status=401, body="")
        with pytest.raises(VizioAuthError, match="HTTP 401"):
            await vizio_tv._get(vizio_tv._endpoint("POWER_MODE"))

    async def test_http_500_still_connection_error(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        """Non-auth HTTP errors continue to raise VizioConnectionError —
        the 401/403 special-case must not over-broaden."""
        from pyvizio.errors import VizioConnectionError

        mock_aio.get(tv_url("POWER_MODE"), status=500, body="")
        with pytest.raises(VizioConnectionError, match="500"):
            await vizio_tv._get(vizio_tv._endpoint("POWER_MODE"))


# ---------------------------------------------------------------------------
# Aggregate tv_information identity helper
# ---------------------------------------------------------------------------


class TestMuteStateAware:
    """``mute_on`` / ``mute_off`` probe state via ``is_muted`` first.
    Critical edge case: ``is_muted`` returns ``None`` on transport or
    auth failures (it swallows the exception). We must NOT fall through
    to MUTE_TOGGLE in that case — toggling on an unknown state could
    invert an already-correct state."""

    async def test_mute_on_no_op_when_probe_returns_none(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        from tests.conftest import tv_settings_url

        # is_muted under the hood does GET on audio.mute. Make it 500
        # so is_muted swallows the exception and returns None.
        mock_aio.get(tv_settings_url("audio", "mute"), status=500)
        # No KEY_PRESS mock — if mute_on incorrectly fell through to
        # MUTE_TOGGLE, this test would error with "no mock matched".
        result = await vizio_tv.mute_on(log_api_exception=False)
        assert result is None

    async def test_mute_off_no_op_when_probe_returns_none(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        from tests.conftest import tv_settings_url

        mock_aio.get(tv_settings_url("audio", "mute"), status=500)
        result = await vizio_tv.mute_off(log_api_exception=False)
        assert result is None


class TestIdentityAggregate:
    """Modern firmware exposes all identity fields (serial, firmware,
    model, …) under a single ``tv_information`` parent, and rejects
    per-field child paths with URI_NOT_FOUND. The library prefers the
    aggregate, falling back to per-field on URI_NOT_FOUND."""

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

    async def test_serial_via_aggregate(self, vizio_tv: VizioAsync, mock_aio) -> None:
        mock_aio.get(tv_url("TV_INFORMATION"), payload=self._aggregate_payload())
        result = await vizio_tv.get_serial_number()
        assert result == "TEST00000000001"

    async def test_version_resolves_firmware_alias(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        """Modern firmware exposes the version under cname='firmware'."""
        mock_aio.get(tv_url("TV_INFORMATION"), payload=self._aggregate_payload())
        result = await vizio_tv.get_version()
        assert result == "3.720.9.1-1"

    async def test_aggregate_cached_across_calls(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        """Identity is immutable — a second identity call should reuse
        the cached aggregate, not refetch."""
        mock_aio.get(tv_url("TV_INFORMATION"), payload=self._aggregate_payload())
        # First call hits the network
        await vizio_tv.get_serial_number()
        # Second call should also succeed without a second mock — if
        # the cache works, no further HTTP request fires.
        # (aioresponses raises if an unmocked URL is hit.)
        v = await vizio_tv.get_version()
        assert v == "3.720.9.1-1"
