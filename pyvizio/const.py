"""pyvizio constants."""

from __future__ import annotations

from importlib import resources
import json
from typing import Any

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


def _load_apps() -> list[dict[str, Any]]:
    """Load apps list from bundled JSON data."""
    ref = resources.files("pyvizio.data").joinpath("apps.json")
    return json.loads(ref.read_text(encoding="utf-8"))


APPS: list[dict[str, Any]] = _load_apps()
