"""Tests for pyvizio CLI commands."""

from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner
import pytest

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
        mock_discover.assert_called_once()


class TestCliKeyPressCommands:
    """Tests for CLI commands that map to simple key-press API calls."""

    @pytest.mark.parametrize(
        "method,cli_args",
        [
            ("pow_on", ["power", "on"]),
            ("pow_off", ["power", "off"]),
            ("pow_toggle", ["power", "toggle"]),
            ("vol_up", ["volume", "up"]),
            ("vol_down", ["volume", "down"]),
            ("ch_up", ["channel", "up"]),
            ("ch_down", ["channel", "down"]),
            ("ch_prev", ["channel", "previous"]),
            ("mute_on", ["mute", "on"]),
            ("mute_off", ["mute", "off"]),
            ("mute_toggle", ["mute", "toggle"]),
            ("play", ["play"]),
            ("pause", ["pause"]),
            ("next_input", ["next-input"]),
        ],
    )
    def test_key_press_command(self, method, cli_args):
        with patch(
            f"pyvizio.cli.VizioAsync.{method}",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_method:
            result = invoke(*cli_args)
            assert result.exit_code == 0
            mock_method.assert_awaited_once()


class TestCliGetters:
    """Tests for CLI commands that retrieve a value."""

    @pytest.mark.parametrize(
        "method,return_value,cli_args",
        [
            ("get_power_state", True, ["get-power-state"]),
            ("get_current_volume", 25, ["get-volume-level"]),
            ("get_current_input", "HDMI-1", ["get-current-input"]),
            ("get_version", "4.0.20", ["get-version"]),
            ("get_esn", "ESN123", ["get-esn"]),
            ("get_serial_number", "SN123", ["get-serial-number"]),
            ("get_charging_status", 1, ["get-charging-status"]),
            ("get_battery_level", 75, ["get-battery-level"]),
            ("get_setting", 25, ["get-setting", "audio", "volume"]),
            ("get_audio_setting", 25, ["get-audio-setting", "volume"]),
        ],
    )
    def test_getter_command(self, method, return_value, cli_args):
        with patch(
            f"pyvizio.cli.VizioAsync.{method}",
            new_callable=AsyncMock,
            return_value=return_value,
        ) as mock_method:
            result = invoke(*cli_args)
            assert result.exit_code == 0
            mock_method.assert_awaited_once()

    @patch("pyvizio.cli.VizioAsync.get_max_volume", return_value=100)
    def test_get_volume_max(self, mock_vol):
        result = invoke("get-volume-max")
        assert result.exit_code == 0
        mock_vol.assert_called_once()

    @patch(
        "pyvizio.cli.VizioAsync.get_remote_keys_list", return_value=["PLAY", "PAUSE"]
    )
    def test_get_remote_keys_list(self, mock_keys):
        result = invoke("get-remote-keys-list")
        assert result.exit_code == 0
        mock_keys.assert_called_once()


class TestCliInput:
    @patch("pyvizio.cli.VizioAsync.get_inputs_list", new_callable=AsyncMock)
    def test_get_inputs_list(self, mock_inputs):
        item = MagicMock(spec=InputItem)
        item.name = "HDMI-1"
        item.meta_name = "Living Room"
        mock_inputs.return_value = [item]
        result = invoke("get-inputs-list")
        assert result.exit_code == 0
        mock_inputs.assert_awaited_once()

    @patch(
        "pyvizio.cli.VizioAsync.set_input", new_callable=AsyncMock, return_value=True
    )
    def test_input_set(self, mock_input):
        result = invoke("input", "HDMI-2")
        assert result.exit_code == 0
        mock_input.assert_awaited_once()


class TestCliRemote:
    @patch("pyvizio.cli.VizioAsync.remote", new_callable=AsyncMock, return_value=True)
    def test_key_press(self, mock_remote):
        result = invoke("key-press", "play")
        assert result.exit_code == 0
        mock_remote.assert_awaited_once()


class TestCliPairing:
    @patch("pyvizio.cli.VizioAsync.start_pair", new_callable=AsyncMock)
    def test_pair_start(self, mock_pair):
        mock_pair.return_value = BeginPairResponse(1, 12345)
        result = invoke("pair")
        assert result.exit_code == 0
        mock_pair.assert_awaited_once()

    @patch("pyvizio.cli.VizioAsync.pair", new_callable=AsyncMock)
    def test_pair_finish(self, mock_pair):
        mock_pair.return_value = PairChallengeResponse("new_token")
        result = invoke("pair-finish", "--ch_type", "1", "--token", "12345")
        assert result.exit_code == 0
        mock_pair.assert_awaited_once()

    @patch(
        "pyvizio.cli.VizioAsync.stop_pair", new_callable=AsyncMock, return_value=True
    )
    def test_pair_stop(self, mock_pair):
        result = invoke("pair-stop")
        assert result.exit_code == 0
        mock_pair.assert_awaited_once()


class TestCliSettings:
    @patch("pyvizio.cli.VizioAsync.get_setting_types_list", new_callable=AsyncMock)
    def test_get_setting_types_list(self, mock_types):
        mock_types.return_value = ["audio", "picture"]
        result = invoke("get-setting-types-list")
        assert result.exit_code == 0
        mock_types.assert_awaited_once()

    @pytest.mark.parametrize(
        "method,return_value,cli_args",
        [
            (
                "get_all_settings",
                {"volume": 25, "eq": "Normal"},
                ["get-all-settings", "audio"],
            ),
            (
                "get_all_settings_options",
                {"volume": {"min": 0, "max": 100}},
                ["get-all-settings-options", "audio"],
            ),
            (
                "get_setting_options",
                {"min": 0, "max": 100},
                ["get-setting-options", "audio", "volume"],
            ),
            ("get_all_audio_settings", {"volume": 25}, ["get-all-audio-settings"]),
            (
                "get_all_audio_settings_options",
                {"volume": {"min": 0, "max": 100}},
                ["get-all-audio-settings-options"],
            ),
            (
                "get_audio_setting_options",
                {"min": 0, "max": 100},
                ["get-audio-setting-options", "volume"],
            ),
        ],
    )
    def test_settings_getters(self, method, return_value, cli_args):
        with patch(
            f"pyvizio.cli.VizioAsync.{method}",
            new_callable=AsyncMock,
            return_value=return_value,
        ) as mock_method:
            result = invoke(*cli_args)
            assert result.exit_code == 0
            mock_method.assert_awaited_once()

    @pytest.mark.parametrize(
        "method,cli_args",
        [
            ("set_setting", ["setting", "audio", "volume", "25"]),
            ("set_audio_setting", ["audio-setting", "volume", "25"]),
        ],
    )
    def test_settings_setters(self, method, cli_args):
        with patch(
            f"pyvizio.cli.VizioAsync.{method}",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_method:
            result = invoke(*cli_args)
            assert result.exit_code == 0
            mock_method.assert_awaited_once()


class TestCliApps:
    @patch("pyvizio.cli.VizioAsync.get_apps_list", new_callable=AsyncMock)
    def test_get_apps_list(self, mock_apps):
        mock_apps.return_value = ["Netflix", "Hulu"]
        result = invoke("get-apps-list")
        assert result.exit_code == 0
        mock_apps.assert_awaited_once()

    @pytest.mark.parametrize(
        "method,cli_args",
        [
            ("launch_app", ["launch-app", "Netflix"]),
            ("launch_app_config", ["launch-app-config", "1", "3"]),
        ],
    )
    def test_launch_commands(self, method, cli_args):
        with patch(
            f"pyvizio.cli.VizioAsync.{method}",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_method:
            result = invoke(*cli_args)
            assert result.exit_code == 0
            mock_method.assert_awaited_once()

    @patch(
        "pyvizio.cli.gen_apps_list_from_url", new_callable=AsyncMock, return_value=None
    )
    @patch("pyvizio.cli.VizioAsync.get_current_app_config", new_callable=AsyncMock)
    def test_get_current_app(self, mock_config, mock_gen):
        mock_config.return_value = AppConfig("1", 3, None)
        result = invoke("get-current-app")
        assert result.exit_code == 0
        mock_config.assert_awaited_once()

    @patch("pyvizio.cli.VizioAsync.get_current_app_config", new_callable=AsyncMock)
    def test_get_current_app_config(self, mock_config):
        mock_config.return_value = AppConfig("1", 3, None)
        result = invoke("get-current-app-config")
        assert result.exit_code == 0
        mock_config.assert_awaited_once()
