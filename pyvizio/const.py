"""pyvizio constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
import json

DEVICE_CLASS_SPEAKER = "speaker"
DEVICE_CLASS_TV = "tv"
DEVICE_CLASS_CRAVE360 = "crave360"

DEFAULT_DEVICE_ID = "pyvizio"
DEFAULT_DEVICE_CLASS = DEVICE_CLASS_TV
DEFAULT_DEVICE_NAME = "Python Vizio"
DEFAULT_PORTS = [7345, 9000]
DEFAULT_TIMEOUT = 5

MAX_VOLUME = {
    DEVICE_CLASS_TV: 100,
    DEVICE_CLASS_SPEAKER: 31,
    DEVICE_CLASS_CRAVE360: 100,
}

# Current Input when app is active
INPUT_APPS = ["SMARTCAST", "CAST"]

# App name returned when it is not in app dictionary
UNKNOWN_APP = "_UNKNOWN_APP"
NO_APP_RUNNING = "_NO_APP_RUNNING"
SMARTCAST_HOME = "SmartCast Home"

APP_CAST = "Cast"

# NAME_SPACE values that appear to be equivalent
EQUIVALENT_NAME_SPACES = (2, 4)

APP_HOME = {
    "name": SMARTCAST_HOME,
    "country": ["*"],
    "config": [
        {
            "NAME_SPACE": 4,
            "APP_ID": "1",
            "MESSAGE": "http://127.0.0.1:12345/scfs/sctv/main.html",
        }
    ],
}


def _load_apps() -> list[dict]:
    """Load apps list from bundled JSON data."""
    ref = resources.files("pyvizio.data").joinpath("apps.json")
    return json.loads(ref.read_text(encoding="utf-8"))


APPS: list[dict] = _load_apps()


@dataclass(frozen=True)
class DeviceConfig:
    """Configuration for a specific Vizio device class."""

    device_class: str
    requires_auth: bool
    max_volume: int
    endpoints: dict[str, str] = field(repr=False)
    key_codes: dict[str, tuple[int, int]] = field(repr=False)


DEVICE_CONFIGS: dict[str, DeviceConfig] = {
    DEVICE_CLASS_TV: DeviceConfig(
        device_class=DEVICE_CLASS_TV,
        requires_auth=True,
        max_volume=100,
        endpoints={
            "BEGIN_PAIR": "/pairing/start",
            "FINISH_PAIR": "/pairing/pair",
            "CANCEL_PAIR": "/pairing/cancel",
            "INPUTS": "/menu_native/dynamic/tv_settings/devices/name_input",
            "CURRENT_INPUT": "/menu_native/dynamic/tv_settings/devices/current_input",
            "ESN": "/menu_native/dynamic/tv_settings/system/system_information/uli_information/esn",
            "SERIAL_NUMBER": "/menu_native/dynamic/tv_settings/system/system_information/tv_information/serial_number",
            "VERSION": "/menu_native/dynamic/tv_settings/system/system_information/tv_information/version",
            "_ALT_ESN": "/menu_native/dynamic/tv_settings/admin_and_privacy/system_information/uli_information/esn",
            "_ALT_SERIAL_NUMBER": "/menu_native/dynamic/tv_settings/admin_and_privacy/system_information/tv_information/serial_number",
            "_ALT_VERSION": "/menu_native/dynamic/tv_settings/admin_and_privacy/system_information/tv_information/version",
            "DEVICE_INFO": "/state/device/deviceinfo",
            "POWER_MODE": "/state/device/power_mode",
            "KEY_PRESS": "/key_command/",
            "SETTINGS": "/menu_native/dynamic/tv_settings",
            "SETTINGS_OPTIONS": "/menu_native/static/tv_settings",
            "CURRENT_APP": "/app/current",
            "LAUNCH_APP": "/app/launch",
        },
        key_codes={
            "SEEK_FWD": (2, 0),
            "SEEK_BACK": (2, 1),
            "PAUSE": (2, 2),
            "PLAY": (2, 3),
            "DOWN": (3, 0),
            "LEFT": (3, 1),
            "OK": (3, 2),
            "UP": (3, 8),
            "LEFT2": (3, 4),
            "RIGHT": (3, 7),
            "BACK": (4, 0),
            "SMARTCAST": (4, 3),
            "CC_TOGGLE": (4, 4),
            "INFO": (4, 6),
            "MENU": (4, 8),
            "HOME": (4, 15),
            "VOL_DOWN": (5, 0),
            "VOL_UP": (5, 1),
            "MUTE_OFF": (5, 2),
            "MUTE_ON": (5, 3),
            "MUTE_TOGGLE": (5, 4),
            "PIC_MODE": (6, 0),
            "PIC_SIZE": (6, 2),
            "INPUT_NEXT": (7, 1),
            "CH_DOWN": (8, 0),
            "CH_UP": (8, 1),
            "CH_PREV": (8, 2),
            "EXIT": (9, 0),
            "POW_OFF": (11, 0),
            "POW_ON": (11, 1),
            "POW_TOGGLE": (11, 2),
        },
    ),
    DEVICE_CLASS_SPEAKER: DeviceConfig(
        device_class=DEVICE_CLASS_SPEAKER,
        requires_auth=False,
        max_volume=31,
        endpoints={
            "BEGIN_PAIR": "/pairing/start",
            "FINISH_PAIR": "/pairing/pair",
            "CANCEL_PAIR": "/pairing/cancel",
            "INPUTS": "/menu_native/dynamic/audio_settings/input",
            "CURRENT_INPUT": "/menu_native/dynamic/audio_settings/input/current_input",
            "ESN": "/menu_native/dynamic/audio_settings/system/system_information/uli_information/esn",
            "SERIAL_NUMBER": "/menu_native/dynamic/audio_settings/system/system_information/speaker_information/serial_number",
            "VERSION": "/menu_native/dynamic/audio_settings/system/system_information/speaker_information/version",
            "_ALT_ESN": "/menu_native/dynamic/audio_settings/admin_and_privacy/system_information/uli_information/esn",
            "_ALT_SERIAL_NUMBER": "/menu_native/dynamic/audio_settings/admin_and_privacy/system_information/speaker_information/serial_number",
            "_ALT_VERSION": "/menu_native/dynamic/audio_settings/admin_and_privacy/system_information/speaker_information/version",
            "DEVICE_INFO": "/state/device/deviceinfo",
            "POWER_MODE": "/state/device/power_mode",
            "KEY_PRESS": "/key_command/",
            "SETTINGS": "/menu_native/dynamic/audio_settings",
            "SETTINGS_OPTIONS": "/menu_native/static/audio_settings",
        },
        key_codes={
            "PAUSE": (2, 2),
            "PLAY": (2, 3),
            "VOL_DOWN": (5, 0),
            "VOL_UP": (5, 1),
            "MUTE_OFF": (5, 2),
            "MUTE_ON": (5, 3),
            "MUTE_TOGGLE": (5, 4),
            "POW_OFF": (11, 0),
            "POW_ON": (11, 1),
            "POW_TOGGLE": (11, 2),
        },
    ),
    DEVICE_CLASS_CRAVE360: DeviceConfig(
        device_class=DEVICE_CLASS_CRAVE360,
        requires_auth=False,
        max_volume=100,
        endpoints={
            "BEGIN_PAIR": "/pairing/start",
            "FINISH_PAIR": "/pairing/pair",
            "CANCEL_PAIR": "/pairing/cancel",
            "INPUTS": "/menu_native/dynamic/audio_settings/input",
            "CURRENT_INPUT": "/menu_native/dynamic/audio_settings/input/current_input",
            "ESN": "/menu_native/dynamic/audio_settings/system/system_information/uli_information/esn",
            "SERIAL_NUMBER": "/menu_native/dynamic/audio_settings/system/system_information/speaker_information/serial_number",
            "VERSION": "/menu_native/dynamic/audio_settings/system/system_information/speaker_information/version",
            "_ALT_ESN": "/menu_native/dynamic/audio_settings/admin_and_privacy/system_information/uli_information/esn",
            "_ALT_SERIAL_NUMBER": "/menu_native/dynamic/audio_settings/admin_and_privacy/system_information/speaker_information/serial_number",
            "_ALT_VERSION": "/menu_native/dynamic/audio_settings/admin_and_privacy/system_information/speaker_information/version",
            "DEVICE_INFO": "/state/device/deviceinfo",
            "POWER_MODE": "/state/device/power_mode",
            "KEY_PRESS": "/key_command/",
            "SETTINGS": "/menu_native/dynamic/audio_settings",
            "SETTINGS_OPTIONS": "/menu_native/static/audio_settings",
            "CHARGING_STATUS": "/state/device/charging_status",
            "BATTERY_LEVEL": "/state/device/battery_level",
        },
        key_codes={
            "PAUSE": (2, 2),
            "PLAY": (2, 3),
            "VOL_DOWN": (5, 0),
            "VOL_UP": (5, 1),
            "MUTE_OFF": (5, 2),
            "MUTE_ON": (5, 3),
            "MUTE_TOGGLE": (5, 4),
            "POW_OFF": (11, 0),
            "POW_ON": (11, 1),
            "POW_TOGGLE": (11, 2),
        },
    ),
}
