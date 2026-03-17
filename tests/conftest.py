"""Shared fixtures and mock response factories for pyvizio tests."""

from aioresponses import aioresponses
import pytest

from pyvizio import Vizio, VizioAsync
from pyvizio.api._protocol import ENDPOINT

# Device configuration constants
TV_IP = "192.168.1.100"
TV_PORT = 7345
TV_IP_PORT = f"{TV_IP}:{TV_PORT}"

SPEAKER_IP = "192.168.1.101"
SPEAKER_PORT = 9000
SPEAKER_IP_PORT = f"{SPEAKER_IP}:{SPEAKER_PORT}"

CRAVE_IP = "192.168.1.102"
CRAVE_PORT = 9000
CRAVE_IP_PORT = f"{CRAVE_IP}:{CRAVE_PORT}"

AUTH_TOKEN = "auth123"


# ---- Fixtures ----


@pytest.fixture
def vizio_tv():
    return VizioAsync("pyvizio", TV_IP_PORT, "TV", AUTH_TOKEN, "tv")


@pytest.fixture
def vizio_speaker():
    return VizioAsync("pyvizio", SPEAKER_IP_PORT, "Speaker", "", "speaker")


@pytest.fixture
def vizio_crave():
    return VizioAsync("pyvizio", CRAVE_IP_PORT, "Crave", "", "crave360")


@pytest.fixture
def vizio_sync():
    return Vizio("pyvizio", TV_IP_PORT, "TV", AUTH_TOKEN, "tv")


@pytest.fixture
def mock_aio():
    with aioresponses() as m:
        yield m


# ---- URL helpers ----


def device_url(device_type, ip_port, endpoint_key):
    """Build full URL for a device endpoint."""
    return f"https://{ip_port}{ENDPOINT[device_type][endpoint_key]}"


def tv_url(endpoint_key):
    return device_url("tv", TV_IP_PORT, endpoint_key)


def speaker_url(endpoint_key):
    return device_url("speaker", SPEAKER_IP_PORT, endpoint_key)


def crave_url(endpoint_key):
    return device_url("crave360", CRAVE_IP_PORT, endpoint_key)


def tv_settings_url(setting_type, setting_name=None):
    base = f"https://{TV_IP_PORT}{ENDPOINT['tv']['SETTINGS']}/{setting_type}"
    if setting_name:
        base += f"/{setting_name}"
    return base


def tv_settings_options_url(setting_type):
    return f"https://{TV_IP_PORT}{ENDPOINT['tv']['SETTINGS_OPTIONS']}/{setting_type}"


def speaker_settings_url(setting_type, setting_name=None):
    base = f"https://{SPEAKER_IP_PORT}{ENDPOINT['speaker']['SETTINGS']}/{setting_type}"
    if setting_name:
        base += f"/{setting_name}"
    return base


def settings_url(device_type, ip_port, setting_type, setting_name=None):
    """Build settings URL for any device/ip combination."""
    base = f"https://{ip_port}{ENDPOINT[device_type]['SETTINGS']}/{setting_type}"
    if setting_name:
        base += f"/{setting_name}"
    return base


# ---- Response factories ----


def make_response(items=None, item=None):
    """Create a mock success response."""
    resp = {"STATUS": {"RESULT": "SUCCESS", "DETAIL": "Success"}}
    if items is not None:
        resp["ITEMS"] = items
    if item is not None:
        resp["ITEM"] = item
    return resp


def make_item(cname, value, hashval=1, item_type="T_VALUE_V1", name=None, **kwargs):
    """Create a mock item dict."""
    result = {
        "CNAME": cname,
        "TYPE": item_type,
        "NAME": name or cname,
        "VALUE": value,
        "HASHVAL": hashval,
    }
    result.update(kwargs)
    return result


def make_power_response(value):
    """Create power state response. value=1 for on, 0 for off."""
    return make_response(items=[make_item("power_mode", value, name="Power Mode")])


def make_key_press_response():
    """Create success response for key press commands (PUT)."""
    return make_response()


def make_input_item(cname, display_name, meta_name, hashval):
    """Create an input item with extended metadata."""
    return make_item(
        cname,
        {"NAME": meta_name, "METADATA": ""},
        hashval=hashval,
        name=display_name,
    )


def make_inputs_list_response(inputs):
    """Create inputs list response. inputs: list of (cname, display_name, meta_name, hashval)."""
    items = [make_input_item(*inp) for inp in inputs]
    return make_response(items=items)


def make_current_input_response(cname, meta_name, hashval):
    """Create current input response (non-extended metadata)."""
    return make_response(
        items=[make_item(cname, meta_name, hashval=hashval, name="Current Input")]
    )


def make_pair_begin_response(ch_type, token):
    """Create begin pair response."""
    return make_response(item={"CHALLENGE_TYPE": ch_type, "PAIRING_REQ_TOKEN": token})


def make_pair_finish_response(auth_token):
    """Create pair finish response."""
    return make_response(item={"AUTH_TOKEN": auth_token})


def make_device_info_response(value_dict):
    """Create device info response."""
    return make_response(items=[{"VALUE": value_dict}])


def make_app_response(app_id, name_space, message=None):
    """Create current app response."""
    return make_response(
        item={"VALUE": {"APP_ID": app_id, "NAME_SPACE": name_space, "MESSAGE": message}}
    )


def make_no_app_response():
    """Create response when no app is running (VALUE is None)."""
    return make_response(item={"VALUE": None})


def make_setting_types_response(types):
    """Create setting types list response. types: list of cname strings."""
    items = []
    for cname in types:
        items.append(make_item(cname, "", item_type="T_MENU_V1", name=cname.title()))
    return make_response(items=items)


def make_settings_response(settings):
    """Create all settings response. settings: list of (cname, value, item_type, hashval)."""
    items = []
    for cname, value, item_type, hashval in settings:
        items.append(make_item(cname, value, hashval=hashval, item_type=item_type))
    return make_response(items=items)


def make_settings_options_response(settings):
    """Create settings options response.

    settings: list of dicts with keys: cname, item_type, and either
    min/max/center (for slider) or elements (for list).
    """
    items = []
    for s in settings:
        kwargs = {}
        if "MINIMUM" in s:
            kwargs["MINIMUM"] = s["MINIMUM"]
        if "MAXIMUM" in s:
            kwargs["MAXIMUM"] = s["MAXIMUM"]
        if "CENTER" in s:
            kwargs["CENTER"] = s["CENTER"]
        if "ELEMENTS" in s:
            kwargs["ELEMENTS"] = s["ELEMENTS"]
        items.append(
            make_item(
                s["cname"],
                s.get("value", ""),
                hashval=s.get("hashval", 1),
                item_type=s["item_type"],
                **kwargs,
            )
        )
    return make_response(items=items)


def make_error_response(result="INVALID_PARAMETER", detail="Error"):
    """Create an error response."""
    return {"STATUS": {"RESULT": result, "DETAIL": detail}}
