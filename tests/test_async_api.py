"""Tests for VizioAsync public API methods."""

import pytest

from pyvizio import VizioAsync
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
    TV_IP_PORT,
    crave_url,
    device_url,
    make_app_response,
    make_current_input_response,
    make_device_info_response,
    make_error_response,
    make_inputs_list_response,
    make_item,
    make_key_press_response,
    make_no_app_response,
    make_pair_begin_response,
    make_pair_finish_response,
    make_power_response,
    make_response,
    make_setting_types_response,
    make_settings_options_response,
    make_settings_response,
    settings_url,
    speaker_url,
    tv_settings_options_url,
    tv_settings_url,
    tv_url,
)

# ---- Construction ----


class TestConstruction:
    @pytest.mark.parametrize(
        "ip,name,auth,device_type",
        [
            ("1.2.3.4:7345", "TV", "token", "tv"),
            ("1.2.3.4:9000", "Speaker", "", "speaker"),
            ("1.2.3.4:9000", "Crave", "", "crave360"),
        ],
    )
    def test_valid_device_types(self, ip, name, auth, device_type):
        v = VizioAsync("id", ip, name, auth, device_type)
        assert v.device_type == device_type

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
    @pytest.mark.parametrize("value,expected", [(1, True), (0, False)])
    async def test_get_power_state(self, vizio_tv, mock_aio, value, expected):
        mock_aio.get(tv_url("POWER_MODE"), payload=make_power_response(value))
        result = await vizio_tv.get_power_state()
        assert result is expected

    async def test_get_power_state_error(self, vizio_tv, mock_aio):
        mock_aio.get(tv_url("POWER_MODE"), status=500)
        result = await vizio_tv.get_power_state(log_api_exception=False)
        assert result is None

    @pytest.mark.parametrize("method", ["pow_on", "pow_off", "pow_toggle"])
    async def test_power_commands(self, vizio_tv, mock_aio, method):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await getattr(vizio_tv, method)()
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

    @pytest.mark.parametrize("method", ["vol_up", "vol_down"])
    async def test_vol_commands(self, vizio_tv, mock_aio, method):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await getattr(vizio_tv, method)()
        assert result is True

    async def test_vol_up_multiple(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.vol_up(num=3)
        assert result is True

    @pytest.mark.parametrize("value,expected", [("On", True), ("Off", False)])
    async def test_is_muted(self, vizio_tv, mock_aio, value, expected):
        mock_aio.get(
            tv_settings_url("audio", "mute"),
            payload=make_response(items=[make_item("mute", value)]),
        )
        result = await vizio_tv.is_muted()
        assert result is expected

    @pytest.mark.parametrize("method", ["mute_on", "mute_off", "mute_toggle"])
    async def test_mute_commands(self, vizio_tv, mock_aio, method):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await getattr(vizio_tv, method)()
        assert result is True

    @pytest.mark.parametrize(
        "fixture,expected",
        [
            ("vizio_tv", 100),
            ("vizio_speaker", 31),
        ],
    )
    async def test_get_max_volume(self, fixture, expected, request):
        device = request.getfixturevalue(fixture)
        assert device.get_max_volume() == expected


# ---- Input ----


class TestInput:
    async def test_get_inputs_list(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("INPUTS"),
            payload=make_inputs_list_response(
                [
                    ("hdmi1", "HDMI-1", "Living Room", 1),
                    ("hdmi2", "HDMI-2", "Console", 2),
                    ("current_input", "Current Input", "HDMI-1", 0),
                ]
            ),
        )
        result = await vizio_tv.get_inputs_list()
        assert result is not None
        assert len(result) == 2
        assert all(isinstance(i, InputItem) for i in result)

    async def test_get_inputs_list_meta_names(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_url("INPUTS"),
            payload=make_inputs_list_response(
                [
                    ("hdmi1", "HDMI-1", "Living Room", 1),
                    ("hdmi2", "HDMI-2", "Console", 2),
                ]
            ),
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
        mock_aio.get(
            tv_url("CURRENT_INPUT"),
            payload=make_current_input_response("current_input", "HDMI-1", 5),
        )
        mock_aio.put(tv_url("CURRENT_INPUT"), payload=make_response())
        result = await vizio_tv.set_input("HDMI-2")
        assert result is True

    async def test_next_input(self, vizio_tv, mock_aio):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await vizio_tv.next_input()
        assert result is True


# ---- Device Info ----


class TestDeviceInfo:
    @pytest.mark.parametrize(
        "method,endpoint,cname,value",
        [
            ("get_esn", "ESN", "esn", "VIZIO-ESN-123"),
            ("get_serial_number", "SERIAL_NUMBER", "serial_number", "SN12345"),
            ("get_version", "VERSION", "version", "4.0.20.1"),
        ],
    )
    async def test_device_info_primary(
        self, vizio_tv, mock_aio, method, endpoint, cname, value
    ):
        mock_aio.get(
            tv_url(endpoint),
            payload=make_response(items=[make_item(cname, value)]),
        )
        result = await getattr(vizio_tv, method)()
        assert result == value

    @pytest.mark.parametrize(
        "method,endpoint,alt_endpoint,cname,value",
        [
            ("get_esn", "ESN", "_ALT_ESN", "esn", "ALT-ESN-456"),
            (
                "get_serial_number",
                "SERIAL_NUMBER",
                "_ALT_SERIAL_NUMBER",
                "serial_number",
                "ALT-SN-789",
            ),
            ("get_version", "VERSION", "_ALT_VERSION", "version", "3.5.10.0"),
        ],
    )
    async def test_device_info_fallback(
        self, vizio_tv, mock_aio, method, endpoint, alt_endpoint, cname, value
    ):
        mock_aio.get(tv_url(endpoint), payload=make_error_response())
        mock_aio.get(
            tv_url(alt_endpoint),
            payload=make_response(items=[make_item(cname, value)]),
        )
        result = await getattr(vizio_tv, method)(log_api_exception=False)
        assert result == value

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
        for excluded in ("cast", "input", "devices", "network"):
            assert excluded not in result

    async def test_get_all_settings(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio"),
            payload=make_settings_response(
                [
                    ("volume", 25, "T_VALUE_ABS_V1", 1),
                    ("eq", "Normal", "T_LIST_V1", 2),
                ]
            ),
        )
        result = await vizio_tv.get_all_settings("audio")
        assert isinstance(result, dict)
        assert result["volume"] == 25
        assert result["eq"] == "Normal"

    async def test_get_all_settings_options(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_options_url("audio"),
            payload=make_settings_options_response(
                [
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
                ]
            ),
        )
        result = await vizio_tv.get_all_settings_options("audio")
        assert isinstance(result, dict)
        assert result["volume"] == {"min": 0, "max": 100}
        assert result["eq"] == ["Normal", "Music", "Movie"]

    async def test_get_all_settings_options_with_default(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_options_url("audio"),
            payload=make_settings_options_response(
                [
                    {
                        "cname": "bass",
                        "item_type": "T_VALUE_ABS_V1",
                        "MINIMUM": -6,
                        "MAXIMUM": 6,
                        "CENTER": 0,
                    },
                ]
            ),
        )
        result = await vizio_tv.get_all_settings_options("audio")
        assert result["bass"] == {"min": -6, "max": 6, "default": 0}

    async def test_get_all_settings_options_xlist(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio"),
            payload=make_response(
                items=[
                    make_item(
                        "surround",
                        "Music",
                        item_type="T_LIST_X_V1",
                        ELEMENTS=["Normal", "Music", "Movie"],
                    ),
                ]
            ),
        )
        result = await vizio_tv.get_all_settings_options_xlist("audio")
        assert result == {"surround": ["Normal", "Music", "Movie"]}

    @pytest.mark.parametrize(
        "cname,value,item_type,expected_type",
        [
            ("volume", 25, "T_VALUE_ABS_V1", int),
            ("eq", "Normal", "T_LIST_V1", str),
        ],
    )
    async def test_get_setting(
        self, vizio_tv, mock_aio, cname, value, item_type, expected_type
    ):
        mock_aio.get(
            tv_settings_url("audio", cname),
            payload=make_response(items=[make_item(cname, value, item_type=item_type)]),
        )
        result = await vizio_tv.get_setting("audio", cname)
        assert result == value
        assert isinstance(result, expected_type)

    async def test_get_setting_options(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_options_url("audio"),
            payload=make_settings_options_response(
                [
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
                ]
            ),
        )
        result = await vizio_tv.get_setting_options("audio", "volume")
        assert result == {"min": 0, "max": 100}

    async def test_get_setting_options_xlist(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio"),
            payload=make_response(
                items=[
                    make_item(
                        "surround",
                        "Music",
                        item_type="T_LIST_X_V1",
                        ELEMENTS=["Normal", "Music", "Movie"],
                    ),
                ]
            ),
        )
        result = await vizio_tv.get_setting_options_xlist("audio", "surround")
        assert result == ["Normal", "Music", "Movie"]

    async def test_set_setting(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio", "volume"),
            payload=make_response(
                items=[make_item("volume", 20, hashval=5, item_type="T_VALUE_ABS_V1")]
            ),
        )
        mock_aio.put(tv_settings_url("audio", "volume"), payload=make_response())
        result = await vizio_tv.set_setting("audio", "volume", 25)
        assert result is True

    async def test_set_setting_not_found(self, vizio_tv, mock_aio):
        mock_aio.get(tv_settings_url("audio", "nonexistent"), status=500)
        result = await vizio_tv.set_setting(
            "audio", "nonexistent", 5, log_api_exception=False
        )
        assert result is None


# ---- Audio Convenience Methods ----


class TestAudioConvenience:
    async def test_get_all_audio_settings(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_url("audio"),
            payload=make_settings_response(
                [
                    ("volume", 25, "T_VALUE_ABS_V1", 1),
                ]
            ),
        )
        result = await vizio_tv.get_all_audio_settings()
        assert result == {"volume": 25}

    async def test_get_all_audio_settings_options(self, vizio_tv, mock_aio):
        mock_aio.get(
            tv_settings_options_url("audio"),
            payload=make_settings_options_response(
                [
                    {
                        "cname": "volume",
                        "item_type": "T_VALUE_ABS_V1",
                        "MINIMUM": 0,
                        "MAXIMUM": 100,
                    },
                ]
            ),
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
            payload=make_settings_options_response(
                [
                    {
                        "cname": "volume",
                        "item_type": "T_VALUE_ABS_V1",
                        "MINIMUM": 0,
                        "MAXIMUM": 100,
                    },
                ]
            ),
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
    @pytest.mark.parametrize("method", ["ch_up", "ch_down", "ch_prev"])
    async def test_channel_commands(self, vizio_tv, mock_aio, method):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await getattr(vizio_tv, method)()
        assert result is True


# ---- Remote ----


class TestRemote:
    @pytest.mark.parametrize("method", ["play", "pause"])
    async def test_media_commands(self, vizio_tv, mock_aio, method):
        mock_aio.put(tv_url("KEY_PRESS"), payload=make_key_press_response())
        result = await getattr(vizio_tv, method)()
        assert result is True

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


# ---- Auth Behavior ----


class TestAuthBehavior:
    async def test_tv_empty_auth_raises(self, mock_aio):
        tv = VizioAsync("id", TV_IP_PORT, "TV", "", "tv")
        with pytest.raises(Exception, match="Empty auth token"):
            await tv.get_power_state()

    @pytest.mark.parametrize(
        "fixture,url_fn",
        [
            ("vizio_speaker", speaker_url),
            ("vizio_crave", crave_url),
        ],
    )
    async def test_no_auth_device_succeeds(self, fixture, url_fn, mock_aio, request):
        device = request.getfixturevalue(fixture)
        mock_aio.get(url_fn("POWER_MODE"), payload=make_power_response(1))
        result = await device.get_power_state()
        assert result is True


# ---- Connection Checks ----


class TestConnection:
    @pytest.mark.parametrize(
        "status,expected",
        [
            (200, True),
            (500, False),
        ],
    )
    async def test_can_connect_with_auth_check(
        self, vizio_tv, mock_aio, status, expected
    ):
        if status == 200:
            mock_aio.get(
                tv_settings_url("audio"),
                payload=make_settings_response([("volume", 25, "T_VALUE_ABS_V1", 1)]),
            )
        else:
            mock_aio.get(tv_settings_url("audio"), status=status)
        result = await vizio_tv.can_connect_with_auth_check()
        assert result is expected

    @pytest.mark.parametrize(
        "status,expected",
        [
            (200, True),
            (500, False),
        ],
    )
    async def test_can_connect_no_auth_check(
        self, vizio_tv, mock_aio, status, expected
    ):
        if status == 200:
            mock_aio.get(
                tv_url("DEVICE_INFO"),
                payload=make_device_info_response({"MODEL_NAME": "V505"}),
            )
        else:
            mock_aio.get(tv_url("DEVICE_INFO"), status=status)
        result = await vizio_tv.can_connect_no_auth_check()
        assert result is expected


# ---- Port Resolution ----


class TestPortResolution:
    async def test_ip_with_port_skips_scan(self, mock_aio):
        """IP already has port — no scan needed."""
        ip_port = "192.168.1.50:7345"
        v = VizioAsync("id", ip_port, "TV", AUTH_TOKEN, "tv")
        mock_aio.get(
            device_url("tv", ip_port, "POWER_MODE"),
            payload=make_power_response(1),
        )
        result = await v.get_power_state()
        assert result is True


# ---- Static Methods ----


class TestStaticMethods:
    async def test_get_unique_id(self, mock_aio):
        ip = "192.168.1.200:7345"
        mock_aio.get(
            device_url("tv", ip, "SERIAL_NUMBER"),
            payload=make_response(items=[make_item("serial_number", "UNIQUE-123")]),
        )
        result = await VizioAsync.get_unique_id(ip, "tv")
        assert result == "UNIQUE-123"

    @pytest.mark.parametrize("country", ["all", "usa"])
    async def test_get_apps_list(self, country):
        result = await VizioAsync.get_apps_list(country, apps_list=APPS)
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0] == APP_HOME["name"]


# ---- Guess Device Type ----


class TestGuessDeviceType:
    @pytest.mark.parametrize(
        "status,expected",
        [
            (200, DEVICE_CLASS_SPEAKER),
            (500, DEVICE_CLASS_TV),
        ],
    )
    async def test_guess_device_type(self, mock_aio, status, expected):
        from pyvizio import async_guess_device_type

        ip = "192.168.1.50:9000"
        url = settings_url("speaker", ip, "audio")
        if status == 200:
            mock_aio.get(
                url,
                payload=make_settings_response([("volume", 10, "T_VALUE_ABS_V1", 1)]),
            )
        else:
            mock_aio.get(url, status=status)
        result = await async_guess_device_type(ip)
        assert result == expected
