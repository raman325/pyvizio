"""Tests for Vizio synchronous wrapper class."""

import asyncio

from aioresponses import aioresponses

import pyvizio
from pyvizio import Vizio, VizioAsync
from pyvizio.const import APPS
from tests.conftest import (
    AUTH_TOKEN,
    TV_IP_PORT,
    make_app_response,
    make_current_input_response,
    make_item,
    make_key_press_response,
    make_power_response,
    make_response,
    tv_settings_url,
    tv_url,
)


class TestSyncInit:
    def test_sync_init(self):
        v = Vizio("pyvizio", TV_IP_PORT, "TV", AUTH_TOKEN, "tv")
        assert v.device_type == "tv"
        assert v.ip == TV_IP_PORT

    def test_sync_repr(self):
        v = Vizio("pyvizio", TV_IP_PORT, "TV", AUTH_TOKEN, "tv")
        assert "Vizio" in repr(v)

    def test_sync_eq(self):
        a = Vizio("pyvizio", TV_IP_PORT, "TV", AUTH_TOKEN, "tv")
        b = Vizio("pyvizio", TV_IP_PORT, "TV", AUTH_TOKEN, "tv")
        assert a == b


class TestSyncPower:
    def test_sync_get_power_state(self, vizio_sync):
        with aioresponses() as m:
            m.get(tv_url("POWER_MODE"), payload=make_power_response(1))
            result = vizio_sync.get_power_state()
        assert result is True

    def test_sync_pow_on(self, vizio_sync):
        with aioresponses() as m:
            m.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
            result = vizio_sync.pow_on()
        assert result is True


class TestSyncVolume:
    def test_sync_vol_up(self, vizio_sync):
        with aioresponses() as m:
            m.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
            result = vizio_sync.vol_up()
        assert result is True

    def test_sync_get_current_volume(self, vizio_sync):
        with aioresponses() as m:
            m.get(
                tv_settings_url("audio", "volume"),
                payload=make_response(
                    items=[make_item("volume", 15, item_type="T_VALUE_ABS_V1")]
                ),
            )
            result = vizio_sync.get_current_volume()
        assert result == 15

    def test_sync_get_max_volume(self, vizio_sync):
        assert vizio_sync.get_max_volume() == 100


class TestSyncInput:
    def test_sync_get_current_input(self, vizio_sync):
        with aioresponses() as m:
            m.get(
                tv_url("CURRENT_INPUT"),
                payload=make_current_input_response("current_input", "HDMI-1", 5),
            )
            result = vizio_sync.get_current_input()
        assert result == "HDMI-1"

    def test_sync_set_input(self, vizio_sync):
        with aioresponses() as m:
            m.get(
                tv_url("CURRENT_INPUT"),
                payload=make_current_input_response("current_input", "HDMI-1", 5),
            )
            m.put(tv_url("CURRENT_INPUT"), payload=make_response())
            result = vizio_sync.set_input("HDMI-2")
        assert result is True


class TestSyncDeviceInfo:
    def test_sync_get_esn(self, vizio_sync):
        with aioresponses() as m:
            m.get(
                tv_url("ESN"),
                payload=make_response(items=[make_item("esn", "ESN-123")]),
            )
            result = vizio_sync.get_esn()
        assert result == "ESN-123"


class TestSyncSettings:
    def test_sync_get_setting(self, vizio_sync):
        with aioresponses() as m:
            m.get(
                tv_settings_url("audio", "volume"),
                payload=make_response(
                    items=[make_item("volume", 20, item_type="T_VALUE_ABS_V1")]
                ),
            )
            result = vizio_sync.get_setting("audio", "volume")
        assert result == 20

    def test_sync_set_setting(self, vizio_sync):
        with aioresponses() as m:
            m.get(
                tv_settings_url("audio", "volume"),
                payload=make_response(
                    items=[
                        make_item("volume", 20, hashval=5, item_type="T_VALUE_ABS_V1")
                    ]
                ),
            )
            m.put(tv_settings_url("audio", "volume"), payload=make_response())
            result = vizio_sync.set_setting("audio", "volume", 25)
        assert result is True


class TestSyncApps:
    def test_sync_get_current_app(self, vizio_sync):
        with aioresponses() as m:
            m.get(tv_url("CURRENT_APP"), payload=make_app_response("3", 2, None))
            result = vizio_sync.get_current_app(apps_list=APPS)
        assert result == "Hulu"


class TestSyncRemote:
    def test_sync_get_remote_keys_list(self, vizio_sync):
        keys = vizio_sync.get_remote_keys_list()
        assert "PLAY" in keys
        assert "VOL_UP" in keys


class TestSyncWrapperGeneration:
    """Tests for the auto-generated sync wrappers."""

    # Build expected set from VizioAsync: public async instance methods that
    # should be auto-wrapped (excludes staticmethod/classmethod).
    _expected_wrapped = [
        name
        for name, raw in vars(VizioAsync).items()
        if not name.startswith("_")
        and not isinstance(raw, (staticmethod, classmethod))
        and asyncio.iscoroutinefunction(getattr(VizioAsync, name))
    ]

    def test_all_async_methods_are_wrapped(self):
        """Every public async instance method on VizioAsync has a sync counterpart on Vizio."""
        assert len(self._expected_wrapped) > 0, "No methods found to wrap"
        for name in self._expected_wrapped:
            attr = getattr(Vizio, name)
            assert callable(attr), f"Vizio.{name} is not callable"
            assert not asyncio.iscoroutinefunction(attr), (
                f"Vizio.{name} should be sync, not async"
            )

    def test_sync_methods_have_sync_docstrings(self):
        """Auto-wrapped methods should not have 'Asynchronously' in docstrings."""
        for name in self._expected_wrapped:
            attr = getattr(Vizio, name)
            doc = getattr(attr, "__doc__", "") or ""
            assert not doc.startswith("Asynchronously"), (
                f"Vizio.{name} docstring should not start with 'Asynchronously': {doc[:60]}"
            )

    def test_sync_docstrings_are_capitalized(self):
        """After stripping 'Asynchronously ', the docstring should start with a capital letter."""
        for name in self._expected_wrapped:
            attr = getattr(Vizio, name)
            doc = getattr(attr, "__doc__", "") or ""
            if doc:
                assert doc[0].isupper(), (
                    f"Vizio.{name} docstring should start capitalized: {doc[:60]}"
                )

    def test_sync_methods_have_correct_qualname(self):
        """Auto-wrapped methods should report Vizio.* as their __qualname__."""
        for name in self._expected_wrapped:
            attr = getattr(Vizio, name)
            assert attr.__qualname__ == f"Vizio.{name}", (
                f"Vizio.{name} has unexpected qualname: {attr.__qualname__}"
            )

    def test_staticmethods_are_not_auto_wrapped(self):
        """@staticmethod async methods should keep their explicit Vizio definitions, not be auto-wrapped."""
        for name, raw in vars(VizioAsync).items():
            if isinstance(raw, staticmethod) and asyncio.iscoroutinefunction(
                getattr(VizioAsync, name)
            ):
                # The Vizio version should remain a staticmethod descriptor
                vizio_raw = vars(Vizio).get(name)
                assert isinstance(vizio_raw, staticmethod), (
                    f"Vizio.{name} should be a staticmethod, got {type(vizio_raw)}"
                )
                vizio_attr = getattr(Vizio, name)
                assert not asyncio.iscoroutinefunction(vizio_attr), (
                    f"Vizio.{name} should be sync, not async"
                )

    def test_no_wrapper_temporaries_in_module(self):
        """The wrapper generation should not leak temporary variables into the module namespace."""
        for leaked in ("_name", "_raw", "_attr", "_generate_sync_wrappers"):
            assert not hasattr(pyvizio, leaked), (
                f"'{leaked}' leaked into pyvizio module namespace"
            )

    def test_wrapper_preserves_method_name(self):
        """Auto-wrapped methods should preserve __name__ from the original async method."""
        for name in self._expected_wrapped:
            attr = getattr(Vizio, name)
            assert attr.__name__ == name, (
                f"Vizio.{name} has unexpected __name__: {attr.__name__}"
            )
