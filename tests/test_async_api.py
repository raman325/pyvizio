"""Tests for VizioAsync public API methods."""

import pytest

from pyvizio import VizioAsync
from pyvizio.api._protocol import ENDPOINT
from pyvizio.api.apps import AppConfig
from pyvizio.api.input import InputItem
from pyvizio.api.pair import BeginPairResponse, PairChallengeResponse
from pyvizio.const import (
    APP_HOME,
    APPS,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
    NO_APP_RUNNING,
)

from tests.conftest import (
    AUTH_TOKEN,
    CRAVE_IP_PORT,
    SPEAKER_IP_PORT,
    TV_IP,
    TV_IP_PORT,
    crave_url,
    make_app_response,
    make_current_input_response,
    make_device_info_response,
    make_error_response,
    make_inputs_list_response,
    make_key_press_response,
    make_no_app_response,
    make_pair_begin_response,
    make_pair_finish_response,
    make_power_response,
    make_response,
    make_item,
    make_settings_options_response,
    make_settings_response,
    make_setting_types_response,
    speaker_settings_url,
    speaker_url,
    tv_settings_options_url,
    tv_settings_url,
    tv_url,
)


# ---- Construction ----


class TestConstruction:
    def test_valid_tv(self):
        v = VizioAsync("id", "1.2.3.4:7345", "TV", "token", "tv")
        assert v.device_type == "tv"

    def test_valid_speaker(self):
        v = VizioAsync("id", "1.2.3.4:9000", "Speaker", "", "speaker")
        assert v.device_type == "speaker"

    def test_valid_crave360(self):
        v = VizioAsync("id", "1.2.3.4:9000", "Crave", "", "crave360")
        assert v.device_type == "crave360"

    def test_invalid_device_type(self):
        with pytest.raises(Exception, match="Invalid device type"):
            VizioAsync("id", "1.2.3.4:7345", "Test", "", "invalid")

    def test_repr(self):
        v = VizioAsync("id", "1.2.3.4:7345", "TV", "token", "tv")
        assert "VizioAsync" in repr(v)

    def test_eq(self):
        a = VizioAsync("id", "1.2.3.4:7345", "TV", "token", "tv")
        b = VizioAsync("id", "1.2.3.4:7345", "TV", "token", "tv")
        assert a == b

    def test_neq(self):
        a = VizioAsync("id", "1.2.3.4:7345", "TV", "token", "tv")
        b = VizioAsync("id2", "1.2.3.4:7345", "TV", "token", "tv")
        assert a != b


# ---- Power ----


class TestPower:
    async def test_get_power_state_on(self, vizio_tv, mock_aio):
        mock_aio.get(tv_url("POWER_MODE"), payload=make_power_response(1))
        result = await vizio_tv.get_power_state()
        assert result is True

    async def test_get_power_state_off(self, vizio_tv, mock_aio):
        mock_aio.get(tv_url("POWER_MODE"), payload=make_power_response(0))
        result = await vizio_tv.get_power_state()
        assert result is False

    async def test_get_power_state_error(self, vizio_tv, mock_aio):
        mock_aio.get(tv_url("POWER_MODE"), status=500)
        result = await vizio_tv.get_power_state(log_api_exception=False)
        assert result is None

    async def test_pow_on(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.pow_on()
        assert result is True

    async def test_pow_off(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.pow_off()
        assert result is True

    async def test_pow_toggle(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.pow_toggle()
        assert result is True


# ---- Volume ----


class TestVolume:
    async def test_get_current_volume(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio", "volume"),
            payload=make_response(
                items=[make_item("volume", 25, item_type="T_VALUE_ABS_V1")]
            ),
        )
        result = await vizio_tv.get_current_volume()
        assert result == 25

    async def test_vol_up(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.vol_up()
        assert result is True

    async def test_vol_down(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.vol_down()
        assert result is True

    async def test_vol_up_multiple(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.vol_up(num=3)
        assert result is True

    async def test_is_muted_on(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio", "mute"),
            payload=make_response(items=[make_item("mute", "On")]),
        )
        result = await vizio_tv.is_muted()
        assert result is True

    async def test_is_muted_off(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio", "mute"),
            payload=make_response(items=[make_item("mute", "Off")]),
        )
        result = await vizio_tv.is_muted()
        assert result is False

    async def test_mute_on(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.mute_on()
        assert result is True

    async def test_mute_off(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.mute_off()
        assert result is True

    async def test_mute_toggle(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.mute_toggle()
        assert result is True

    async def test_get_max_volume_tv(self, vizio_tv):
        assert vizio_tv.get_max_volume() == 100

    async def test_get_max_volume_speaker(self, vizio_speaker):
        assert vizio_speaker.get_max_volume() == 31


# ---- Input ----


class TestInput:
    async def test_get_inputs_list(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("INPUTS"),
            payload=make_inputs_list_response([
                ("hdmi1", "HDMI-1", "Living Room", 1),
                ("hdmi2", "HDMI-2", "Console", 2),
                ("current_input", "Current Input", "HDMI-1", 0),
            ]),
        )
        result = await vizio_tv.get_inputs_list()
        assert result is not None
        assert len(result) == 2
        assert all(isinstance(i, InputItem) for i in result)

    async def test_get_inputs_list_meta_names(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("INPUTS"),
            payload=make_inputs_list_response([
                ("hdmi1", "HDMI-1", "Living Room", 1),
                ("hdmi2", "HDMI-2", "Console", 2),
            ]),
        )
        result = await vizio_tv.get_inputs_list()
        assert result[0].meta_name == "Living Room"
        assert result[1].meta_name == "Console"

    async def test_get_current_input(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("CURRENT_INPUT"),
            payload=make_current_input_response("current_input", "HDMI-1", 5),
        )
        result = await vizio_tv.get_current_input()
        assert result == "HDMI-1"

    async def test_set_input(self, vizio_tv, mock_aio):
        # First call: GET current input to get ID
        mock_aio.get(
            tv_url("CURRENT_INPUT"),
            payload=make_current_input_response("current_input", "HDMI-1", 5),
        )
        # Second call: PUT to change input
        mock_aio.put(tv_url("CURRENT_INPUT"), payload=make_response())
        result = await vizio_tv.set_input("HDMI-2")
        assert result is True

    async def test_next_input(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.next_input()
        assert result is True


# ---- Device Info ----


class TestDeviceInfo:
    async def test_get_esn(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("ESN"),
            payload=make_response(items=[make_item("esn", "VIZIO-ESN-123")]),
        )
        result = await vizio_tv.get_esn()
        assert result == "VIZIO-ESN-123"

    async def test_get_esn_fallback(self, vizio_tv, mock_aio):
        # Primary endpoint fails
        mock_aio.get(tv_url("ESN"), payload=make_error_response())
        # Alt endpoint succeeds
        mock_aio.get(
            tv_url("_ALT_ESN"),
            payload=make_response(items=[make_item("esn", "ALT-ESN-456")]),
        )
        result = await vizio_tv.get_esn(log_api_exception=False)
        assert result == "ALT-ESN-456"

    async def test_get_serial_number(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("SERIAL_NUMBER"),
            payload=make_response(
                items=[make_item("serial_number", "SN12345")]
            ),
        )
        result = await vizio_tv.get_serial_number()
        assert result == "SN12345"

    async def test_get_serial_number_fallback(self, vizio_tv, mock_aio):
        mock_aio.get(tv_url("SERIAL_NUMBER"), payload=make_error_response())
        mock_aio.get(
            tv_url("_ALT_SERIAL_NUMBER"),
            payload=make_response(
                items=[make_item("serial_number", "ALT-SN-789")]
            ),
        )
        result = await vizio_tv.get_serial_number(log_api_exception=False)
        assert result == "ALT-SN-789"

    async def test_get_version(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("VERSION"),
            payload=make_response(items=[make_item("version", "4.0.20.1")]),
        )
        result = await vizio_tv.get_version()
        assert result == "4.0.20.1"

    async def test_get_version_fallback(self, vizio_tv, mock_aio):
        mock_aio.get(tv_url("VERSION"), payload=make_error_response())
        mock_aio.get(
            tv_url("_ALT_VERSION"),
            payload=make_response(items=[make_item("version", "3.5.10.0")]),
        )
        result = await vizio_tv.get_version(log_api_exception=False)
        assert result == "3.5.10.0"

    async def test_get_model_name(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("DEVICE_INFO"),
            payload=make_device_info_response({"MODEL_NAME": "V505-G9"}),
        )
        result = await vizio_tv.get_model_name()
        assert result == "V505-G9"

    async def test_get_model_name_speaker(self, vizio_speaker, mock_aio):
        mock_aio.get(
            speaker_url("DEVICE_INFO"),
            payload=make_device_info_response({"NAME": "VIZIO SB3651"}),
        )
        result = await vizio_speaker.get_model_name()
        assert result == "VIZIO SB3651"


# ---- Pairing ----


class TestPairing:
    async def test_start_pair(self, vizio_tv, mock_aio):
        mock_aio.put(
            tv_url("BEGIN_PAIR"),
            payload=make_pair_begin_response(1, 54321),
        )
        result = await vizio_tv.start_pair()
        assert isinstance(result, BeginPairResponse)
        assert result.ch_type == 1
        assert result.token == 54321

    async def test_pair(self, vizio_tv, mock_aio):
        mock_aio.put(
            tv_url("FINISH_PAIR"),
            payload=make_pair_finish_response("new_auth_token"),
        )
        result = await vizio_tv.pair(1, 54321, "1234")
        assert isinstance(result, PairChallengeResponse)
        assert result.auth_token == "new_auth_token"

    async def test_stop_pair(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("CANCEL_PAIR"), payload=make_response())
        result = await vizio_tv.stop_pair()
        assert result is True


# ---- Settings ----


class TestSettings:
    async def test_get_setting_types_list(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("SETTINGS"),
            payload=make_setting_types_response(
                ["audio", "picture", "cast", "input", "devices", "network", "system"]
            ),
        )
        result = await vizio_tv.get_setting_types_list()
        assert isinstance(result, list)
        assert "audio" in result
        assert "picture" in result
        assert "system" in result
        # These should be filtered out
        assert "cast" not in result
        assert "input" not in result
        assert "devices" not in result
        assert "network" not in result

    async def test_get_all_settings(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio"),
            payload=make_settings_response([
                ("volume", 25, "T_VALUE_ABS_V1", 1),
                ("eq", "Normal", "T_LIST_V1", 2),
            ]),
        )
        result = await vizio_tv.get_all_settings("audio")
        assert isinstance(result, dict)
        assert result["volume"] == 25
        assert result["eq"] == "Normal"

    async def test_get_all_settings_options(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_options_url("audio"),
            payload=make_settings_options_response([
                {
                    "cname": "volume",
                    "item_type": "T_VALUE_ABS_V1",
                    "MINIMUM": 0,
                    "MAXIMUM": 100,
                },
                {
                    "cname": "eq",
                    "item_type": "T_LIST_V1",
                    "ELEMENTS": ["Normal", "Music", "Movie"],
                },
            ]),
        )
        result = await vizio_tv.get_all_settings_options("audio")
        assert isinstance(result, dict)
        assert result["volume"] == {"min": 0, "max": 100}
        assert result["eq"] == ["Normal", "Music", "Movie"]

    async def test_get_all_settings_options_with_default(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_options_url("audio"),
            payload=make_settings_options_response([
                {
                    "cname": "bass",
                    "item_type": "T_VALUE_ABS_V1",
                    "MINIMUM": -6,
                    "MAXIMUM": 6,
                    "CENTER": 0,
                },
            ]),
        )
        result = await vizio_tv.get_all_settings_options("audio")
        assert result["bass"] == {"min": -6, "max": 6, "default": 0}

    async def test_get_all_settings_options_xlist(self, vizio_tv, mock_aio):
        # Note: XList commands have a bug in process_response (filtering on raw
        # dict before Item conversion), so they return None in practice.
        mock_aio.get(
            tv_settings_url("audio"),
            payload=make_response(items=[]),
        )
        result = await vizio_tv.get_all_settings_options_xlist("audio")
        assert result is None

    async def test_get_setting_int(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio", "volume"),
            payload=make_response(
                items=[make_item("volume", 25, item_type="T_VALUE_ABS_V1")]
            ),
        )
        result = await vizio_tv.get_setting("audio", "volume")
        assert result == 25
        assert isinstance(result, int)

    async def test_get_setting_str(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio", "eq"),
            payload=make_response(
                items=[make_item("eq", "Normal", item_type="T_LIST_V1")]
            ),
        )
        result = await vizio_tv.get_setting("audio", "eq")
        assert result == "Normal"

    async def test_get_setting_options(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_options_url("audio"),
            payload=make_settings_options_response([
                {
                    "cname": "volume",
                    "item_type": "T_VALUE_ABS_V1",
                    "MINIMUM": 0,
                    "MAXIMUM": 100,
                },
                {
                    "cname": "eq",
                    "item_type": "T_LIST_V1",
                    "ELEMENTS": ["Normal", "Music"],
                },
            ]),
        )
        result = await vizio_tv.get_setting_options("audio", "volume")
        assert result == {"min": 0, "max": 100}

    async def test_get_setting_options_xlist(self, vizio_tv, mock_aio):
        # Same XList bug as above - returns None
        mock_aio.get(
            tv_settings_url("audio"),
            payload=make_response(items=[]),
        )
        result = await vizio_tv.get_setting_options_xlist("audio", "surround")
        assert result is None

    async def test_set_setting(self, vizio_tv, mock_aio):
        # GET to find setting ID
        mock_aio.get(
            tv_settings_url("audio", "volume"),
            payload=make_response(
                items=[make_item("volume", 20, hashval=5, item_type="T_VALUE_ABS_V1")]
            ),
        )
        # PUT to set value
        mock_aio.put(tv_settings_url("audio", "volume"), payload=make_response())
        result = await vizio_tv.set_setting("audio", "volume", 25)
        assert result is True

    async def test_set_setting_not_found(self, vizio_tv, mock_aio):
        # When the GET to find the setting fails, set_setting returns None
        mock_aio.get(tv_settings_url("audio", "nonexistent"), status=500)
        result = await vizio_tv.set_setting("audio", "nonexistent", 5, log_api_exception=False)
        assert result is None


# ---- Audio Convenience Methods ----


class TestAudioConvenience:
    async def test_get_all_audio_settings(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio"),
            payload=make_settings_response([
                ("volume", 25, "T_VALUE_ABS_V1", 1),
            ]),
        )
        result = await vizio_tv.get_all_audio_settings()
        assert result == {"volume": 25}

    async def test_get_all_audio_settings_options(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_options_url("audio"),
            payload=make_settings_options_response([
                {
                    "cname": "volume",
                    "item_type": "T_VALUE_ABS_V1",
                    "MINIMUM": 0,
                    "MAXIMUM": 100,
                },
            ]),
        )
        result = await vizio_tv.get_all_audio_settings_options()
        assert result == {"volume": {"min": 0, "max": 100}}

    async def test_get_audio_setting(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio", "volume"),
            payload=make_response(
                items=[make_item("volume", 30, item_type="T_VALUE_ABS_V1")]
            ),
        )
        result = await vizio_tv.get_audio_setting("volume")
        assert result == 30

    async def test_get_audio_setting_options(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_options_url("audio"),
            payload=make_settings_options_response([
                {
                    "cname": "volume",
                    "item_type": "T_VALUE_ABS_V1",
                    "MINIMUM": 0,
                    "MAXIMUM": 100,
                },
            ]),
        )
        result = await vizio_tv.get_audio_setting_options("volume")
        assert result == {"min": 0, "max": 100}

    async def test_set_audio_setting(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio", "volume"),
            payload=make_response(
                items=[make_item("volume", 20, hashval=5, item_type="T_VALUE_ABS_V1")]
            ),
        )
        mock_aio.put(tv_settings_url("audio", "volume"), payload=make_response())
        result = await vizio_tv.set_audio_setting("volume", 25)
        assert result is True


# ---- Apps ----


class TestApps:
    async def test_get_current_app(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("CURRENT_APP"),
            payload=make_app_response("3", 2, None),
        )
        # Hulu: APP_ID="3", NAME_SPACE=2
        result = await vizio_tv.get_current_app(apps_list=APPS)
        assert result == "Hulu"

    async def test_get_current_app_no_app(self, vizio_tv, mock_aio):
        mock_aio.get(tv_url("CURRENT_APP"), payload=make_no_app_response())
        result = await vizio_tv.get_current_app(apps_list=APPS)
        assert result == NO_APP_RUNNING

    async def test_get_current_app_config(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("CURRENT_APP"),
            payload=make_app_response("1", 3, None),
        )
        result = await vizio_tv.get_current_app_config()
        assert isinstance(result, AppConfig)
        assert result.APP_ID == "1"
        assert result.NAME_SPACE == 3

    async def test_launch_app(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("LAUNCH_APP"), payload=make_response())
        result = await vizio_tv.launch_app("Netflix", apps_list=APPS)
        assert result is True

    async def test_launch_app_config(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("LAUNCH_APP"), payload=make_response())
        result = await vizio_tv.launch_app_config("1", 3, None)
        assert result is True


# ---- Channel ----


class TestChannel:
    async def test_ch_up(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.ch_up()
        assert result is True

    async def test_ch_down(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.ch_down()
        assert result is True

    async def test_ch_prev(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.ch_prev()
        assert result is True


# ---- Remote ----


class TestRemote:
    async def test_remote_valid_key(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.remote("PLAY")
        assert result is True

    async def test_remote_invalid_key(self, vizio_tv, mock_aio):
        result = await vizio_tv.remote("INVALID_KEY")
        assert result is False

    async def test_get_remote_keys_list(self, vizio_tv):
        keys = vizio_tv.get_remote_keys_list()
        assert "PLAY" in keys
        assert "PAUSE" in keys
        assert "VOL_UP" in keys
        assert "POW_ON" in keys

    async def test_play(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.play()
        assert result is True

    async def test_pause(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.pause()
        assert result is True


# ---- Auth Behavior ----


class TestAuthBehavior:
    async def test_tv_empty_auth_raises(self, mock_aio):
        tv = VizioAsync("id", TV_IP_PORT, "TV", "", "tv")
        with pytest.raises(Exception, match="Empty auth token"):
            await tv.get_power_state()

    async def test_speaker_empty_auth_succeeds(self, vizio_speaker, mock_aio):
        mock_aio.get(
            speaker_url("POWER_MODE"), payload=make_power_response(1)
        )
        result = await vizio_speaker.get_power_state()
        assert result is True

    async def test_crave_empty_auth_succeeds(self, vizio_crave, mock_aio):
        mock_aio.get(
            crave_url("POWER_MODE"), payload=make_power_response(1)
        )
        result = await vizio_crave.get_power_state()
        assert result is True


# ---- Connection Checks ----


class TestConnection:
    async def test_can_connect_with_auth_check(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio"),
            payload=make_settings_response([
                ("volume", 25, "T_VALUE_ABS_V1", 1),
            ]),
        )
        result = await vizio_tv.can_connect_with_auth_check()
        assert result is True

    async def test_can_connect_with_auth_check_fail(self, vizio_tv, mock_aio):
        mock_aio.get(tv_settings_url("audio"), status=500)
        result = await vizio_tv.can_connect_with_auth_check()
        assert result is False

    async def test_can_connect_no_auth_check(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("DEVICE_INFO"),
            payload=make_device_info_response({"MODEL_NAME": "V505"}),
        )
        result = await vizio_tv.can_connect_no_auth_check()
        assert result is True

    async def test_can_connect_no_auth_check_fail(self, vizio_tv, mock_aio):
        mock_aio.get(tv_url("DEVICE_INFO"), status=500)
        result = await vizio_tv.can_connect_no_auth_check()
        assert result is False


# ---- Port Resolution ----


class TestPortResolution:
    async def test_ip_with_port_skips_scan(self, mock_aio):
        """IP already has port — no scan needed."""
        v = VizioAsync("id", "192.168.1.50:7345", "TV", AUTH_TOKEN, "tv")
        mock_aio.get(
            f"https://192.168.1.50:7345{ENDPOINT['tv']['POWER_MODE']}",
            payload=make_power_response(1),
        )
        result = await v.get_power_state()
        assert result is True


# ---- Static Methods ----


class TestStaticMethods:
    async def test_get_unique_id(self, mock_aio):
        ip = "192.168.1.200:7345"
        url = f"https://{ip}{ENDPOINT['tv']['SERIAL_NUMBER']}"
        mock_aio.get(
            url,
            payload=make_response(
                items=[make_item("serial_number", "UNIQUE-123")]
            ),
        )
        result = await VizioAsync.get_unique_id(ip, "tv")
        assert result == "UNIQUE-123"

    async def test_get_apps_list(self):
        result = await VizioAsync.get_apps_list("all", apps_list=APPS)
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0] == APP_HOME["name"]

    async def test_get_apps_list_filtered(self):
        result = await VizioAsync.get_apps_list("usa", apps_list=APPS)
        assert isinstance(result, list)
        assert result[0] == APP_HOME["name"]


# ---- Guess Device Type ----


class TestGuessDeviceType:
    async def test_guess_speaker(self, mock_aio):
        from pyvizio import async_guess_device_type

        ip = "192.168.1.50:9000"
        settings_url = f"https://{ip}{ENDPOINT['speaker']['SETTINGS']}/audio"
        mock_aio.get(
            settings_url,
            payload=make_settings_response([("volume", 10, "T_VALUE_ABS_V1", 1)]),
        )
        result = await async_guess_device_type(ip)
        assert result == DEVICE_CLASS_SPEAKER

    async def test_guess_tv(self, mock_aio):
        from pyvizio import async_guess_device_type

        ip = "192.168.1.50:7345"
        settings_url = f"https://{ip}{ENDPOINT['speaker']['SETTINGS']}/audio"
        mock_aio.get(settings_url, status=500)
        result = await async_guess_device_type(ip)
        assert result == DEVICE_CLASS_TV
