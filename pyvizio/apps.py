"""Vizio SmartCast app configuration and name resolution.

Canonical location for AppConfig, find_app_name, and app list utilities.
"""

from __future__ import annotations

import json
from typing import Any

from aiohttp import ClientError, ClientSession

from pyvizio.const import (
    APP_CAST,
    EQUIVALENT_NAME_SPACES,
    NO_APP_RUNNING,
    UNKNOWN_APP,
)

# URLs for fetching app data from Vizio servers
APP_NAMES_URL = "http://scfs.vizio.com/appservice/vizio_apps_prod.json"
APP_PAYLOADS_URL = "http://scfs.vizio.com/appservice/app_availability_prod.json"


class AppConfig:
    """Vizio SmartCast app config."""

    def __init__(
        self,
        APP_ID: str | None = None,
        NAME_SPACE: int | None = None,
        MESSAGE: str | None = None,
    ) -> None:
        self.APP_ID = APP_ID
        self.NAME_SPACE = NAME_SPACE
        self.MESSAGE = MESSAGE

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other: object) -> bool:
        # Guard against non-AppConfig comparisons. Without this,
        # ``AppConfig() == None`` raised ``AttributeError`` because
        # ``None.__dict__`` doesn't exist. Returning ``NotImplemented``
        # lets Python fall back to the right-hand operand's __eq__ and
        # ultimately resolves to ``False`` for non-AppConfig types.
        if self is other:
            return True
        if not isinstance(other, AppConfig):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __bool__(self) -> bool:
        return self != AppConfig()


def find_app_name(
    config_to_check: AppConfig | None, app_list: list[dict[str, Any]]
) -> str:
    """Return the app name for a given AppConfig based on a list of apps.

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


async def gen_apps_list_from_url(
    app_names_url: str = APP_NAMES_URL,
    app_payloads_url: str = APP_PAYLOADS_URL,
    session: ClientSession | None = None,
) -> list[dict[str, Any]] | None:
    """Get app JSON files from external URLs and return list of apps for use in pyvizio."""
    headers = {"Content-Type": "application/json"}
    try:
        if session:
            response = await session.get(
                app_names_url, headers=headers, raise_for_status=True
            )
            app_names = await response.json(content_type=None)
            response = await session.get(
                app_payloads_url, headers=headers, raise_for_status=True
            )
            app_configs = await response.json(content_type=None)
        else:
            async with ClientSession() as local_session:
                response = await local_session.get(
                    app_names_url, headers=headers, raise_for_status=True
                )
                app_names = await response.json(content_type=None)
                response = await local_session.get(
                    app_payloads_url, headers=headers, raise_for_status=True
                )
                app_configs = await response.json(content_type=None)

        return gen_apps_list(app_names, app_configs)
    except ClientError:
        return None


def gen_apps_list(
    app_names: list[dict[str, Any]], app_configs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Parse list of app names and app configs and return list of apps for use in pyvizio."""
    apps_list: list[dict[str, Any]] = []

    for app_name in app_names:
        try:
            app_config = next(
                app_config
                for app_config in app_configs
                if app_config["id"] == app_name["id"]
            )
        except StopIteration:
            pass
        else:
            config_jsons = {
                item["app_type_payload"]
                for val in app_config["chipsets"].values()
                for item in val
            }
            configs = [json.loads(config_json) for config_json in config_jsons]
            try:
                app = next(
                    app
                    for app in apps_list
                    if app["name"].lower() == app_name["name"].lower()
                )
            except StopIteration:
                apps_list.append(
                    {
                        "name": app_name["name"],
                        "country": [country.lower() for country in app_name["country"]],
                        "id": [app_name["id"]],
                        "config": configs,
                    }
                )
            else:
                app["id"].append(app_name["id"])
                app["config"].extend(configs)

    return sorted(apps_list, key=lambda app: app["name"])
