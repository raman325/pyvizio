"""pyvizio helper functions."""

import asyncio
from functools import wraps
from typing import Any, Dict, List, Optional

from pyvizio.const import NO_APP_RUNNING, UNKNOWN_APP


def async_to_sync(f):
    """Decorator to run async function as sync."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def dict_get_case_insensitive(
    in_dict: Dict[str, Any], key: str, default_return: Any = None
) -> Any:
    """Case insensitive dict.get."""
    out_dict = {k.lower(): v for k, v in in_dict.items()}

    return out_dict.get(key.lower(), default_return)


def get_value_from_path(
    device_info: Dict[str, Any], paths: List[List[str]]
) -> Optional[Any]:
    """Iterate through known paths to return first valid path with value from Vizio device_info."""
    for path in paths:
        temp = ""
        for step in path:
            temp = dict_get_case_insensitive(device_info, step, {})

        if temp:
            return temp

    return None


def find_app_name(config_to_check: Dict[str, Any], app_list: List[Dict[str, Any]]):
    if not config_to_check:
        return NO_APP_RUNNING

    for app_def in app_list:
        if isinstance(app_def["config"], list):
            for config in app_def["config"]:
                if (
                    config["APP_ID"] == config_to_check.APP_ID
                    and config["NAME_SPACE"] == config_to_check.NAME_SPACE
                ):
                    # Return name of app or UNKNOWN_APP if app name can't be found for given config
                    return app_def["name"]
        elif (
            isinstance(app_def["config"], dict)
            and app_def["config"]["APP_ID"] == config_to_check.APP_ID
            and app_def["config"]["NAME_SPACE"] == config_to_check.NAME_SPACE
        ):
            return app_def["name"]

    return UNKNOWN_APP


# Adapted from https://gist.github.com/betrcode/0248f0fda894013382d7#gistcomment-3161499
async def open_port(host, port):
    """Return whether or not host's port is open.

    Parameters
    ----------
    host : str
        Host IP address or hostname
    port : int
        Port number

    Returns
    -------
    awaitable bool
    """
    try:
        _reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=2
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        pass

    return False
