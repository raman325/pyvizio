"""Tests for Vizio synchronous wrapper class."""

from aioresponses import aioresponses

from pyvizio import Vizio

from tests.conftest import (
    AUTH_TOKEN,
    TV_IP_PORT,
    make_app_response,
    make_current_input_response,
    make_key_press_response,
    make_power_response,
    make_response,
    make_item,
    tv_settings_url,
    tv_url,
)
from pyvizio.const import APPS


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
                    items=[make_item("volume", 20, hashval=5, item_type="T_VALUE_ABS_V1")]
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
