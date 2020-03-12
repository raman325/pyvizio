"""Vizio SmartCast API commands for apps."""

from typing import Any, Dict

from pyvizio._api._protocol import ENDPOINT, ResponseKey
from pyvizio._api.base import CommandBase
from pyvizio._api.input import ItemInfoCommandBase
from pyvizio.const import APPS, APP_HOME, NO_APP_RUNNING
from pyvizio.helpers import dict_get_case_insensitive, find_app_name


class AppConfig(object):
    """Vizio SmartCast app config."""

    def __init__(
        self, APP_ID: str = None, NAME_SPACE: int = None, MESSAGE: str = None
    ) -> None:
        self.APP_ID = APP_ID
        self.NAME_SPACE = NAME_SPACE
        self.MESSAGE = MESSAGE

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__


class LaunchAppConfigCommand(CommandBase):
    """Command to launch app by config."""

    def __init__(
        self, device_type: str, APP_ID: str, NAME_SPACE: int, MESSAGE: str = None
    ) -> None:
        """Initialize command to launch app by config."""
        super(LaunchAppConfigCommand, self).__init__(
            ENDPOINT[device_type]["LAUNCH_APP"]
        )

        self.VALUE = AppConfig(APP_ID, NAME_SPACE, MESSAGE)


class LaunchAppNameCommand(LaunchAppConfigCommand):
    """Command to launch app by name."""

    def __init__(self, device_type: str, app_name: str) -> None:
        """Initialize command to launch app by name."""
        app_def = next(
            (
                app_def
                for app_def in (APP_HOME + APPS)
                if app_def["name"].lower() == app_name.lower()
            ),
            dict(),
        )

        # Unpack config dict into expected key/value argument pairs
        super(LaunchAppNameCommand, self).__init__(
            device_type, **app_def.get("config", [{}])[0]
        )


class GetCurrentAppConfigCommand(ItemInfoCommandBase):
    """Command to get currently running app's config."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get currently running app's config."""
        super(GetCurrentAppConfigCommand, self).__init__(device_type, "CURRENT_APP")

    def process_response(self, json_obj: Dict[str, Any]) -> AppConfig:
        """Return response to command to get currently running app's config."""
        item = dict_get_case_insensitive(json_obj, ResponseKey.ITEM, {})
        current_app_id = dict_get_case_insensitive(item, ResponseKey.VALUE)

        if current_app_id:
            return AppConfig(**current_app_id)

        return AppConfig()


class GetCurrentAppNameCommand(GetCurrentAppConfigCommand):
    """Command to get currently running app's name."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get currently running app's name."""
        super(GetCurrentAppNameCommand, self).__init__(device_type)

    def process_response(self, json_obj: Dict[str, Any]) -> str:
        """Return response to command to get currently running app's name. Returns NO_APP_RUNNING if no app is currently running and UNKNOWN_APP if app name can't be retrieved from APPS."""
        current_app_config = super(GetCurrentAppNameCommand, self).process_response(
            json_obj
        )

        if current_app_config != AppConfig():
            return find_app_name(current_app_config, APP_HOME + APPS)

        # Return NO_APP_RUNNING if value from response was "null"
        return NO_APP_RUNNING
