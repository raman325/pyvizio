"""Vizio SmartCast API commands for apps."""

from typing import Any, Dict, List, Union

from pyvizio.api._protocol import ENDPOINT, ResponseKey
from pyvizio.api.base import CommandBase
from pyvizio.api.input import ItemInfoCommandBase
from pyvizio.const import (
    APP_CAST,
    APP_HOME,
    EQUIVALENT_NAME_SPACES,
    NO_APP_RUNNING,
    UNKNOWN_APP,
)
from pyvizio.helpers import dict_get_case_insensitive


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

    def __bool__(self) -> bool:
        return self != AppConfig()


def find_app_name(config_to_check: AppConfig, app_list: List[Dict[str, Any]]) -> str:
    """
    Return the app name for a given AppConfig based on a list of apps.

    Returns UNKNOWN_APP if app name can't be found in APPS list for given AppConfig.
    """
    if not config_to_check:
        return NO_APP_RUNNING

    # Attempt to find an exact match from known apps list
    for app_def in app_list:
        if isinstance(app_def["config"], list):
            for config in app_def["config"]:
                if (
                    config["APP_ID"] == config_to_check.APP_ID
                    and config["NAME_SPACE"] == config_to_check.NAME_SPACE
                ):
                    return app_def["name"]
        elif (
            isinstance(app_def["config"], dict)
            and app_def["config"]["APP_ID"] == config_to_check.APP_ID
            and app_def["config"]["NAME_SPACE"] == config_to_check.NAME_SPACE
        ):
            return app_def["name"]

    # If exact match couldn't be find, swap in equivalent name spaces
    # and attempt to find a match
    if config_to_check.NAME_SPACE in EQUIVALENT_NAME_SPACES:
        for app_def in app_list:
            if isinstance(app_def["config"], list):
                for config in app_def["config"]:
                    if (
                        config["APP_ID"] == config_to_check.APP_ID
                        and config["NAME_SPACE"] in EQUIVALENT_NAME_SPACES
                    ):
                        return app_def["name"]
            elif (
                isinstance(app_def["config"], dict)
                and app_def["config"]["APP_ID"] == config_to_check.APP_ID
                and app_def["config"]["NAME_SPACE"] in EQUIVALENT_NAME_SPACES
            ):
                return app_def["name"]

    # So far only the SmartCast home screen appears to use the NAME_SPACE of 0
    if config_to_check.NAME_SPACE == 0:
        return APP_CAST

    # If no match, app is unknown
    return UNKNOWN_APP


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

    def __init__(
        self,
        device_type: str,
        app_name: str,
        apps_list: List[Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]],
    ) -> None:
        """Initialize command to launch app by name."""
        app_def = next(
            (
                app_def
                for app_def in [APP_HOME, *apps_list]
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

    def __init__(
        self,
        device_type: str,
        apps_list: List[Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]],
    ) -> None:
        """Initialize command to get currently running app's name."""
        super(GetCurrentAppNameCommand, self).__init__(device_type)
        self.apps_list = apps_list

    def process_response(self, json_obj: Dict[str, Any]) -> str:
        """
        Return response to command to get currently running app's name.

        Returns NO_APP_RUNNING if no app is currently running and UNKNOWN_APP
        if app name can't be retrieved from APPS.
        """
        current_app_config = super(GetCurrentAppNameCommand, self).process_response(
            json_obj
        )

        if current_app_config:
            return find_app_name(current_app_config, [APP_HOME, *self.apps_list])

        # Return NO_APP_RUNNING if value from response was None
        return NO_APP_RUNNING
