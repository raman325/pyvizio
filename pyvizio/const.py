"""pyvizio constants."""

DEVICE_CLASS_SOUNDBAR = "soundbar"  # Deprecated
DEVICE_CLASS_SPEAKER = "speaker"
DEVICE_CLASS_TV = "tv"

DEFAULT_DEVICE_ID = "pyvizio"
DEFAULT_DEVICE_CLASS = DEVICE_CLASS_TV
DEFAULT_DEVICE_NAME = "Python Vizio"
DEFAULT_PORTS = [7345, 9000]
DEFAULT_TIMEOUT = 5

MAX_VOLUME = {DEVICE_CLASS_TV: 100, DEVICE_CLASS_SPEAKER: 31}

# Current Input when app is active
INPUT_APPS = ["SMARTCAST", "CAST"]

# App name returned when it is not in app dictionary
UNKNOWN_APP = "_UNKNOWN_APP"
NO_APP_RUNNING = "_NO_APP_RUNNING"
SMARTCAST_HOME = "SmartCast Home"
