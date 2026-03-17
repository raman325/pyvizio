"""Tests for pyvizio error types and their usage."""

from __future__ import annotations

from aioresponses import aioresponses
import pytest

from pyvizio import VizioAsync
from pyvizio.api._protocol import async_validate_response
from pyvizio.errors import (
    VizioAuthError,
    VizioConnectionError,
    VizioError,
    VizioInvalidParameterError,
    VizioResponseError,
)
from tests.conftest import (
    AUTH_TOKEN,
    TV_IP_PORT,
    make_error_response,
    make_power_response,
    tv_url,
)


class TestErrorHierarchy:
    """Test that all errors inherit from VizioError."""

    def test_base_error(self):
        assert issubclass(VizioError, Exception)

    def test_connection_error_inherits(self):
        assert issubclass(VizioConnectionError, VizioError)

    def test_auth_error_inherits(self):
        assert issubclass(VizioAuthError, VizioError)

    def test_invalid_parameter_error_inherits(self):
        assert issubclass(VizioInvalidParameterError, VizioError)

    def test_response_error_inherits(self):
        assert issubclass(VizioResponseError, VizioError)

    def test_catch_all_with_base(self):
        """All typed errors should be catchable via VizioError."""
        for exc_cls in (
            VizioConnectionError,
            VizioAuthError,
            VizioInvalidParameterError,
            VizioResponseError,
        ):
            with pytest.raises(VizioError):
                raise exc_cls("test")


class TestValidateResponseErrors:
    """Test that async_validate_response raises typed exceptions."""

    async def test_non_200_raises_connection_error(self):
        with aioresponses() as m:
            m.get(tv_url("POWER_MODE"), status=500)
            from aiohttp import ClientSession

            async with ClientSession() as session:
                resp = await session.get(tv_url("POWER_MODE"), ssl=False)
                with pytest.raises(VizioConnectionError, match="Status code: 500"):
                    await async_validate_response(resp)

    async def test_invalid_json_raises_response_error(self):
        with aioresponses() as m:
            m.get(tv_url("POWER_MODE"), body="not json")
            from aiohttp import ClientSession

            async with ClientSession() as session:
                resp = await session.get(tv_url("POWER_MODE"), ssl=False)
                with pytest.raises(VizioResponseError, match="Failed to parse"):
                    await async_validate_response(resp)

    async def test_missing_status_raises_response_error(self):
        with aioresponses() as m:
            m.get(tv_url("POWER_MODE"), payload={"data": "no status"})
            from aiohttp import ClientSession

            async with ClientSession() as session:
                resp = await session.get(tv_url("POWER_MODE"), ssl=False)
                with pytest.raises(VizioResponseError, match="Unknown response"):
                    await async_validate_response(resp)

    async def test_invalid_parameter_raises_typed_error(self):
        with aioresponses() as m:
            m.get(tv_url("POWER_MODE"), payload=make_error_response())
            from aiohttp import ClientSession

            async with ClientSession() as session:
                resp = await session.get(tv_url("POWER_MODE"), ssl=False)
                with pytest.raises(VizioInvalidParameterError):
                    await async_validate_response(resp)

    async def test_unexpected_status_raises_response_error(self):
        with aioresponses() as m:
            m.get(
                tv_url("POWER_MODE"),
                payload=make_error_response(result="FAILURE", detail="Something broke"),
            )
            from aiohttp import ClientSession

            async with ClientSession() as session:
                resp = await session.get(tv_url("POWER_MODE"), ssl=False)
                with pytest.raises(VizioResponseError, match="unexpected status"):
                    await async_validate_response(resp)


class TestAuthError:
    """Test that auth errors are raised correctly."""

    async def test_tv_without_auth_raises_auth_error(self):
        vizio = VizioAsync("pyvizio", TV_IP_PORT, "TV", "", "tv")
        with pytest.raises(VizioAuthError, match="Empty auth token"):
            await vizio.get_power_state()

    async def test_speaker_without_auth_does_not_raise(self):
        """Speakers don't require auth, so no error should be raised."""
        from tests.conftest import SPEAKER_IP_PORT, speaker_url

        vizio = VizioAsync("pyvizio", SPEAKER_IP_PORT, "Speaker", "", "speaker")
        with aioresponses() as m:
            m.get(speaker_url("POWER_MODE"), payload=make_power_response(1))
            result = await vizio.get_power_state()
        assert result is True


class TestDeviceTypeError:
    """Test that invalid device types raise VizioError."""

    def test_invalid_device_type_raises(self):
        with pytest.raises(VizioError, match="Invalid device type"):
            VizioAsync("pyvizio", TV_IP_PORT, "TV", AUTH_TOKEN, "invalid")


class TestInvokeApiPreservesNoneReturn:
    """Test that typed exceptions from validate_response are caught by invoke_api,
    preserving the existing None-return behavior."""

    async def test_connection_error_returns_none(self):
        vizio = VizioAsync("pyvizio", TV_IP_PORT, "TV", AUTH_TOKEN, "tv")
        with aioresponses() as m:
            m.get(tv_url("POWER_MODE"), status=500)
            result = await vizio.get_power_state(log_api_exception=False)
        assert result is None

    async def test_invalid_param_returns_none(self):
        vizio = VizioAsync("pyvizio", TV_IP_PORT, "TV", AUTH_TOKEN, "tv")
        with aioresponses() as m:
            m.get(tv_url("POWER_MODE"), payload=make_error_response())
            result = await vizio.get_power_state(log_api_exception=False)
        assert result is None
