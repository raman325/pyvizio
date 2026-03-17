"""Tests for pyvizio CLI commands."""

from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from pyvizio.api.apps import AppConfig
from pyvizio.api.input import InputItem
from pyvizio.api.pair import BeginPairResponse, PairChallengeResponse
from pyvizio.cli import cli
from pyvizio.discovery.zeroconf import ZeroconfDevice


def invoke(*args):
    """Helper to invoke CLI with common options."""
    runner = CliRunner()
    return runner.invoke(cli, ["--ip", "192.168.1.100:7345", "--auth", "token", *args])


class TestCliHelp:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.output


class TestCliDiscover:
    @patch("pyvizio.cli.VizioAsync.discovery_zeroconf")
    def test_discover(self, mock_discover):
        mock_discover.return_value = [
            ZeroconfDevice(
                name="LivingRoom",
                ip="192.168.1.100",
                port=7345,
                model="V505",
                id="uuid:test",
            ),
        ]
        result = invoke("discover")
        assert result.exit_code == 0


class TestCliPower:
    @patch("pyvizio.cli.VizioAsync.pow_on", new_callable=AsyncMock, return_value=True)
    def test_power_on(self, mock_pow):
        result = invoke("power", "on")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.pow_off", new_callable=AsyncMock, return_value=True)
    def test_power_off(self, mock_pow):
        result = invoke("power", "off")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.pow_toggle", new_callable=AsyncMock, return_value=True)
    def test_power_toggle(self, mock_pow):
        result = invoke("power", "toggle")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_power_state", new_callable=AsyncMock, return_value=True)
    def test_get_power_state(self, mock_ps):
        result = invoke("get-power-state")
        assert result.exit_code == 0


class TestCliVolume:
    @patch("pyvizio.cli.VizioAsync.vol_up", new_callable=AsyncMock, return_value=True)
    def test_volume_up(self, mock_vol):
        result = invoke("volume", "up")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.vol_down", new_callable=AsyncMock, return_value=True)
    def test_volume_down(self, mock_vol):
        result = invoke("volume", "down")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_current_volume", new_callable=AsyncMock, return_value=25)
    def test_get_volume_level(self, mock_vol):
        result = invoke("get-volume-level")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_max_volume", return_value=100)
    def test_get_volume_max(self, mock_vol):
        result = invoke("get-volume-max")
        assert result.exit_code == 0


class TestCliChannel:
    @patch("pyvizio.cli.VizioAsync.ch_up", new_callable=AsyncMock, return_value=True)
    def test_channel_up(self, mock_ch):
        result = invoke("channel", "up")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.ch_down", new_callable=AsyncMock, return_value=True)
    def test_channel_down(self, mock_ch):
        result = invoke("channel", "down")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.ch_prev", new_callable=AsyncMock, return_value=True)
    def test_channel_prev(self, mock_ch):
        result = invoke("channel", "previous")
        assert result.exit_code == 0


class TestCliMute:
    @patch("pyvizio.cli.VizioAsync.mute_on", new_callable=AsyncMock, return_value=True)
    def test_mute_on(self, mock_mute):
        result = invoke("mute", "on")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.mute_off", new_callable=AsyncMock, return_value=True)
    def test_mute_off(self, mock_mute):
        result = invoke("mute", "off")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.mute_toggle", new_callable=AsyncMock, return_value=True)
    def test_mute_toggle(self, mock_mute):
        result = invoke("mute", "toggle")
        assert result.exit_code == 0


class TestCliInput:
    @patch("pyvizio.cli.VizioAsync.get_inputs_list", new_callable=AsyncMock)
    def test_get_inputs_list(self, mock_inputs):
        item = MagicMock(spec=InputItem)
        item.name = "HDMI-1"
        item.meta_name = "Living Room"
        mock_inputs.return_value = [item]
        result = invoke("get-inputs-list")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_current_input", new_callable=AsyncMock, return_value="HDMI-1")
    def test_get_current_input(self, mock_input):
        result = invoke("get-current-input")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.set_input", new_callable=AsyncMock, return_value=True)
    def test_input_set(self, mock_input):
        result = invoke("input", "HDMI-2")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.next_input", new_callable=AsyncMock, return_value=True)
    def test_next_input(self, mock_input):
        result = invoke("next-input")
        assert result.exit_code == 0


class TestCliPlayPause:
    @patch("pyvizio.cli.VizioAsync.play", new_callable=AsyncMock, return_value=True)
    def test_play(self, mock_play):
        result = invoke("play")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.pause", new_callable=AsyncMock, return_value=True)
    def test_pause(self, mock_pause):
        result = invoke("pause")
        assert result.exit_code == 0


class TestCliRemote:
    @patch("pyvizio.cli.VizioAsync.remote", new_callable=AsyncMock, return_value=True)
    def test_key_press(self, mock_remote):
        result = invoke("key-press", "play")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_remote_keys_list", return_value=["PLAY", "PAUSE"])
    def test_get_remote_keys_list(self, mock_keys):
        result = invoke("get-remote-keys-list")
        assert result.exit_code == 0


class TestCliPairing:
    @patch("pyvizio.cli.VizioAsync.start_pair", new_callable=AsyncMock)
    def test_pair_start(self, mock_pair):
        mock_pair.return_value = BeginPairResponse(1, 12345)
        result = invoke("pair")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.pair", new_callable=AsyncMock)
    def test_pair_finish(self, mock_pair):
        mock_pair.return_value = PairChallengeResponse("new_token")
        result = invoke("pair-finish", "--ch_type", "1", "--token", "12345")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.stop_pair", new_callable=AsyncMock, return_value=True)
    def test_pair_stop(self, mock_pair):
        result = invoke("pair-stop")
        assert result.exit_code == 0


class TestCliSettings:
    @patch("pyvizio.cli.VizioAsync.get_setting_types_list", new_callable=AsyncMock)
    def test_get_setting_types_list(self, mock_types):
        mock_types.return_value = ["audio", "picture"]
        result = invoke("get-setting-types-list")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_all_settings", new_callable=AsyncMock)
    def test_get_all_settings(self, mock_settings):
        mock_settings.return_value = {"volume": 25, "eq": "Normal"}
        result = invoke("get-all-settings", "audio")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_all_settings_options", new_callable=AsyncMock)
    def test_get_all_settings_options(self, mock_options):
        mock_options.return_value = {
            "volume": {"min": 0, "max": 100},
            "eq": ["Normal", "Music"],
        }
        result = invoke("get-all-settings-options", "audio")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_setting", new_callable=AsyncMock, return_value=25)
    def test_get_setting(self, mock_setting):
        result = invoke("get-setting", "audio", "volume")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_setting_options", new_callable=AsyncMock)
    def test_get_setting_options(self, mock_options):
        mock_options.return_value = {"min": 0, "max": 100}
        result = invoke("get-setting-options", "audio", "volume")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.set_setting", new_callable=AsyncMock, return_value=True)
    def test_setting_set(self, mock_setting):
        result = invoke("setting", "audio", "volume", "25")
        assert result.exit_code == 0


class TestCliAudioSettings:
    @patch("pyvizio.cli.VizioAsync.get_all_audio_settings", new_callable=AsyncMock)
    def test_get_all_audio_settings(self, mock_settings):
        mock_settings.return_value = {"volume": 25}
        result = invoke("get-all-audio-settings")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_all_audio_settings_options", new_callable=AsyncMock)
    def test_get_all_audio_settings_options(self, mock_options):
        mock_options.return_value = {"volume": {"min": 0, "max": 100}}
        result = invoke("get-all-audio-settings-options")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_audio_setting", new_callable=AsyncMock, return_value=25)
    def test_get_audio_setting(self, mock_setting):
        result = invoke("get-audio-setting", "volume")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_audio_setting_options", new_callable=AsyncMock)
    def test_get_audio_setting_options(self, mock_options):
        mock_options.return_value = {"min": 0, "max": 100}
        result = invoke("get-audio-setting-options", "volume")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.set_audio_setting", new_callable=AsyncMock, return_value=True)
    def test_audio_setting_set(self, mock_setting):
        result = invoke("audio-setting", "volume", "25")
        assert result.exit_code == 0


class TestCliApps:
    @patch("pyvizio.cli.VizioAsync.get_apps_list", new_callable=AsyncMock)
    def test_get_apps_list(self, mock_apps):
        mock_apps.return_value = ["Netflix", "Hulu"]
        result = invoke("get-apps-list")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.launch_app", new_callable=AsyncMock, return_value=True)
    def test_launch_app(self, mock_launch):
        result = invoke("launch-app", "Netflix")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.launch_app_config", new_callable=AsyncMock, return_value=True)
    def test_launch_app_config(self, mock_launch):
        result = invoke("launch-app-config", "1", "3")
        assert result.exit_code == 0

    @patch("pyvizio.cli.gen_apps_list_from_url", new_callable=AsyncMock, return_value=None)
    @patch("pyvizio.cli.VizioAsync.get_current_app_config", new_callable=AsyncMock)
    def test_get_current_app(self, mock_config, mock_gen):
        mock_config.return_value = AppConfig("1", 3, None)
        result = invoke("get-current-app")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_current_app_config", new_callable=AsyncMock)
    def test_get_current_app_config(self, mock_config):
        mock_config.return_value = AppConfig("1", 3, None)
        result = invoke("get-current-app-config")
        assert result.exit_code == 0


class TestCliDeviceInfo:
    @patch("pyvizio.cli.VizioAsync.get_version", new_callable=AsyncMock, return_value="4.0.20")
    def test_get_version(self, mock_ver):
        result = invoke("get-version")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_esn", new_callable=AsyncMock, return_value="ESN123")
    def test_get_esn(self, mock_esn):
        result = invoke("get-esn")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_serial_number", new_callable=AsyncMock, return_value="SN123")
    def test_get_serial_number(self, mock_sn):
        result = invoke("get-serial-number")
        assert result.exit_code == 0


class TestCliCharging:
    @patch("pyvizio.cli.VizioAsync.get_charging_status", new_callable=AsyncMock, return_value=1)
    def test_get_charging_status(self, mock_charge):
        result = invoke("get-charging-status")
        assert result.exit_code == 0

    @patch("pyvizio.cli.VizioAsync.get_battery_level", new_callable=AsyncMock, return_value=75)
    def test_get_battery_level(self, mock_battery):
        result = invoke("get-battery-level")
        assert result.exit_code == 0
