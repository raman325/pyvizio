"""Vizio SmartCast API commands for apps.

AppConfig and find_app_name are now canonical in pyvizio.apps;
re-exported here for backward compatibility.
"""

from __future__ import annotations

from typing import Any

from pyvizio.api._protocol import ENDPOINT, ResponseKey
from pyvizio.api.base import CommandBase
from pyvizio.api.input import ItemInfoCommandBase
from pyvizio.apps import AppConfig, find_app_name  # noqa: F401
from pyvizio.const import APP_HOME, NO_APP_RUNNING
from pyvizio.helpers import dict_get_case_insensitive


class LaunchAppConfigCommand(CommandBase):
    """Command to launch app by config."""

    def __init__(
        self, device_type: str, APP_ID: str, NAME_SPACE: int, MESSAGE: str | None = None
    ) -> None:
        """Initialize command to launch app by config."""
        super().__init__(ENDPOINT[device_type]["LAUNCH_APP"])

        self.VALUE = AppConfig(APP_ID, NAME_SPACE, MESSAGE)

    def process_response(self, json_obj: dict[str, Any]) -> bool:
        """Return True on successful app launch."""
        return True


class LaunchAppNameCommand(LaunchAppConfigCommand):
    """Command to launch app by name."""

    def __init__(
        self,
        device_type: str,
        app_name: str,
        apps_list: list[dict[str, Any]],
    ) -> None:
        """Initialize command to launch app by name."""
        app_def: dict[str, Any] = next(
            (
                app_def
                for app_def in [APP_HOME, *apps_list]
                if app_def["name"].lower() == app_name.lower()
            ),
            {},
        )

        # Unpack config dict into expected key/value argument pairs
        config_list: list[dict[str, Any]] = app_def.get("config", [{}])
        super().__init__(device_type, **config_list[0] if config_list else {})


class GetCurrentAppConfigCommand(ItemInfoCommandBase):
    """Command to get currently running app's config."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get currently running app's config."""
        super().__init__(device_type, "CURRENT_APP")

    def process_response(self, json_obj: dict[str, Any]) -> AppConfig:
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
        apps_list: list[dict[str, Any]],
    ) -> None:
        """Initialize command to get currently running app's name."""
        super().__init__(device_type)
        self.apps_list = apps_list

    def process_response(self, json_obj: dict[str, Any]) -> str:  # type: ignore[override]
        """
        Return response to command to get currently running app's name.

        Returns NO_APP_RUNNING if no app is currently running and UNKNOWN_APP
        if app name can't be retrieved from APPS.
        """
        current_app_config = super().process_response(json_obj)

        if current_app_config:
            return find_app_name(current_app_config, [APP_HOME, *self.apps_list])

        # Return NO_APP_RUNNING if value from response was None
        return NO_APP_RUNNING
