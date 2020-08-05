"""pyvizio utility module."""

import json
from typing import Any, Dict, List, Union

from aiohttp import ClientError, ClientSession

from pyvizio.util.const import (
    APK_SOURCE_PATH,
    APP_NAMES_FILE,
    APP_NAMES_URL,
    APP_PAYLOADS_FILE,
    APP_PAYLOADS_URL,
    RESOURCE_PATH,
)


async def gen_apps_list_from_url(
    app_names_url: str = APP_NAMES_URL,
    app_payloads_url: str = APP_PAYLOADS_URL,
    session: ClientSession = None,
) -> Optional[List[Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]]]:
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


def gen_apps_list_from_src(
    apk_source_path: str = APK_SOURCE_PATH, resource_path: str = RESOURCE_PATH
) -> List[Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]]:
    """Parse JSON from VizioCast Android app source in `apk_source_path`/`resource_path` and return list of apps for use in pyvizio."""
    base_path = f"{apk_source_path}/{resource_path}"
    app_names_filepath = f"{base_path}/{APP_NAMES_FILE}"
    app_configs_filepath = f"{base_path}/{APP_PAYLOADS_FILE}"

    with open(app_names_filepath) as f:
        app_names = json.load(f)

    with open(app_configs_filepath) as f:
        app_configs = json.load(f)

    return gen_apps_list(app_names, app_configs)


def gen_apps_list(
    app_names: List[Dict[str, Any]], app_configs: List[Dict[str, Any]]
) -> List[Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]]:
    """Parse list of app names and app configs and return list of apps for use in pyvizio."""
    pyvizio_apps: List[Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]] = []

    for app_name in app_names:
        # returns first app where condition is true
        app_config = next(
            (
                app_config
                for app_config in app_configs
                if app_config["id"] == app_name["id"]
            )
        )

        if app_config:
            config_json = app_config["chipsets"]["*"][0]["app_type_payload"]
            config = json.loads(config_json)
            app_already_exists = False
            for pyvizio_app in pyvizio_apps:
                if pyvizio_app["name"].lower() == app_name["name"].lower():
                    pyvizio_app["id"].append(app_name["id"])
                    pyvizio_app["config"].append(config)
                    app_already_exists = True
                    break

            if not app_already_exists:
                pyvizio_apps.append(
                    {
                        "name": app_name["name"],
                        "country": [country.lower() for country in app_name["country"]],
                        "id": [app_name["id"]],
                        "config": [config],
                    }
                )

    return pyvizio_apps
