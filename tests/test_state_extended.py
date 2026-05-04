"""Tests for ``pyvizio.api.state_extended`` and ``Vizio.get_state_extended``.

The ``/state_extended`` endpoint is non-standard — it returns flat
top-level keys (``POWER_MODE``, ``APP_CURRENT``, …) without the usual
``STATUS`` / ``ITEMS`` envelope. ``parse_state_extended`` consumes the
raw payload directly, and ``Vizio.get_state_extended`` uses the new
``SmartCastClient.get_raw_json`` helper that bypasses envelope
validation.

Captured live from a Vizio VHD24M-0810 (firmware 3.720.9.1-1) during
the hardware-probe pass that motivated this addition.
"""

from __future__ import annotations

from aioresponses import aioresponses
import pytest

from pyvizio import VizioAsync
from pyvizio.api.state_extended import StateExtended, parse_state_extended
from tests.conftest import AUTH_TOKEN, TV_IP_PORT, tv_url

# ---------------------------------------------------------------------------
# parse_state_extended (unit, no HTTP)
# ---------------------------------------------------------------------------


class TestParseStateExtended:
    """Captured payload shapes from real firmware. Parser must produce
    the expected typed fields and degrade gracefully when fields are
    missing or have unexpected shapes."""

    def test_full_captured_payload(self) -> None:
        """Full payload as captured live from VHD24M-0810 fw 3.720.9.1-1
        on the SmartCast Home screen."""
        payload = {
            "ERRORS": [],
            "URI": "/state_extended",
            "DEVICE_NAME": "Test TV",
            "POWER_STATUS": {"VALUE": 1},
            "POWER_MODE": {"VALUE": "Quick Start", "HASHVAL": 3026334404},
            "APP_CURRENT": {
                "APP_ID": "1",
                "MESSAGE": '{"app":"home","bundle":"bundles/home"}',
                "NAME_SPACE": 4,
            },
            "CURRENT_INPUT": {"NAME": "SMARTCAST", "HASHVAL": 3009117460},
            "SCREEN_MODE": "Full screen",
            "MEDIA_STATE": "MediaState::Stopped",
        }
        s = parse_state_extended(payload)

        assert isinstance(s, StateExtended)
        assert s.power_on is True
        assert s.power_mode == "Quick Start"
        assert s.current_input == "SMARTCAST"
        assert s.current_input_hashval == 3009117460
        assert s.current_app == {
            "app_id": "1",
            "name_space": 4,
            "message": '{"app":"home","bundle":"bundles/home"}',
        }
        assert s.screen_mode == "Full screen"
        assert s.media_state == "MediaState::Stopped"
        assert s.device_name == "Test TV"
        assert s.errors == ()
        assert s.raw == payload

    def test_powered_off(self) -> None:
        """POWER_STATUS.VALUE = 0 → power_on = False."""
        payload = {
            "POWER_STATUS": {"VALUE": 0},
            "POWER_MODE": {"VALUE": "Active Off"},
        }
        s = parse_state_extended(payload)
        assert s.power_on is False
        assert s.power_mode == "Active Off"

    def test_minimal_payload_degrades_gracefully(self) -> None:
        """Older or partial firmware may omit fields — every getter
        degrades to empty / None / () instead of raising."""
        s = parse_state_extended({"URI": "/state_extended"})
        assert s.power_on is False
        assert s.power_mode == ""
        assert s.current_input == ""
        assert s.current_input_hashval is None
        assert s.current_app is None
        assert s.screen_mode == ""
        assert s.media_state == ""
        assert s.device_name == ""
        assert s.errors == ()

    def test_missing_app_current_returns_none(self) -> None:
        """No app running → APP_CURRENT may be missing or empty."""
        s = parse_state_extended({"POWER_STATUS": {"VALUE": 1}})
        assert s.current_app is None

    def test_partial_app_current_returns_none(self) -> None:
        """APP_CURRENT missing app_id or name_space → None (not partial)."""
        s = parse_state_extended(
            {"APP_CURRENT": {"APP_ID": "5"}}  # no NAME_SPACE
        )
        assert s.current_app is None

    def test_app_current_with_invalid_namespace(self) -> None:
        """Non-integer name_space → None rather than raising."""
        s = parse_state_extended(
            {"APP_CURRENT": {"APP_ID": "5", "NAME_SPACE": "not-a-number"}}
        )
        assert s.current_app is None

    def test_current_input_invalid_hashval(self) -> None:
        """Non-integer hashval degrades to None."""
        s = parse_state_extended(
            {"CURRENT_INPUT": {"NAME": "HDMI-1", "HASHVAL": "not-a-number"}}
        )
        assert s.current_input == "HDMI-1"
        assert s.current_input_hashval is None

    def test_errors_array(self) -> None:
        s = parse_state_extended({"ERRORS": ["disk full", 42, None]})
        assert s.errors == ("disk full", "42", "None")

    def test_errors_non_list_ignored(self) -> None:
        """Defensive: ERRORS as a non-list shape doesn't crash."""
        s = parse_state_extended({"ERRORS": "oops"})
        assert s.errors == ()

    def test_lowercase_keys(self) -> None:
        """Parser is case-insensitive (devices normalize keys variably)."""
        s = parse_state_extended(
            {
                "power_status": {"value": 1},
                "current_input": {"name": "HDMI-1", "hashval": 7},
                "screen_mode": "Full screen",
            }
        )
        assert s.power_on is True
        assert s.current_input == "HDMI-1"
        assert s.current_input_hashval == 7
        assert s.screen_mode == "Full screen"


# ---------------------------------------------------------------------------
# Vizio.get_state_extended (integration, HTTP-mocked)
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


class TestVizioGetStateExtended:
    """End-to-end via HTTP mocking — exercises the non-standard envelope
    bypass (``SmartCastClient.get_raw_json``) and the parser together."""

    async def test_round_trip(self, vizio_tv: VizioAsync, mock_aio) -> None:
        mock_aio.get(
            tv_url("STATE_EXTENDED"),
            payload={
                "POWER_STATUS": {"VALUE": 1},
                "POWER_MODE": {"VALUE": "On"},
                "CURRENT_INPUT": {"NAME": "HDMI-1", "HASHVAL": 42},
                "SCREEN_MODE": "Full screen",
                "MEDIA_STATE": "MediaState::Stopped",
                "DEVICE_NAME": "Test TV",
            },
        )
        s = await vizio_tv.get_state_extended()
        assert s is not None
        assert s.power_on is True
        assert s.current_input == "HDMI-1"
        assert s.device_name == "Test TV"

    async def test_uri_not_found_envelope_raises_not_found(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        """Older firmware that doesn't expose ``/state_extended`` returns
        the standard SCPL envelope ``{"STATUS": {"RESULT":
        "URI_NOT_FOUND", ...}}`` rather than the flat-keyed shape we
        want. ``get_raw_json`` deliberately skips envelope validation
        (the success-case payload doesn't have ``STATUS``/``ITEMS``),
        so ``get_state_extended`` detects an envelope-shaped error
        manually and raises ``VizioNotFoundError``. Without this
        check, the parser would happily produce a default-filled
        ``StateExtended`` and callers couldn't distinguish "endpoint
        unsupported" from "real all-default state".

        ``_handle_error`` swallows ``VizioNotFoundError`` when
        ``log_api_exception=False``, so the result is ``None`` (which
        is the documented "not available" signal for compat callers).
        """
        mock_aio.get(
            tv_url("STATE_EXTENDED"),
            payload={"STATUS": {"RESULT": "URI_NOT_FOUND", "DETAIL": "URI not found"}},
        )
        s = await vizio_tv.get_state_extended(log_api_exception=False)
        assert s is None

    async def test_unsupported_device_class(self) -> None:
        """Speakers and Crave don't define STATE_EXTENDED; library must
        gate before any HTTP work rather than crashing with a KeyError
        from the missing endpoint lookup. The compat-helper
        ``_handle_error`` then suppresses the ``VizioUnsupportedError``
        and returns ``None``, which is the documented signal for
        "not available on this device class"."""
        speaker = VizioAsync(
            device_id="probe",
            ip="192.168.1.50:9000",
            name="Speaker",
            auth_token="",
            device_type="speaker",
        )
        # No HTTP mock needed — the endpoint-presence gate
        # short-circuits before any request would fire.
        assert await speaker.get_state_extended(log_api_exception=False) is None
        assert await speaker.get_state_extended() is None

    async def test_http_error_returns_none(
        self, vizio_tv: VizioAsync, mock_aio
    ) -> None:
        """Connection failure with log_api_exception=False returns None."""
        mock_aio.get(tv_url("STATE_EXTENDED"), status=500)
        s = await vizio_tv.get_state_extended(log_api_exception=False)
        assert s is None
