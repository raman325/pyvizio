import json
from typing import Any, Dict, List, Tuple

from pyvizio.util.const import (
    APK_SOURCE_PATH,
    APP_NAMES_FILE,
    APP_PAYLOADS_FILE,
    RESOURCE_PATH,
)


def gen_apps_list_from_src(
    apk_source_path: str = APK_SOURCE_PATH, resource_path: str = RESOURCE_PATH
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse JSON from VizioCast Android app source in `apk_source_path`/`resource_path` and generate app list for use in pyvizio."""
    base_path = f"{apk_source_path}/{resource_path}"
    app_names_filepath = f"{base_path}/{APP_NAMES_FILE}"
    app_payloads_filepath = f"{base_path}/{APP_PAYLOADS_FILE}"

    with open(app_names_filepath) as f:
        app_names = json.load(f)

    with open(app_payloads_filepath) as f:
        app_payloads = json.load(f)

    pyvizio_apps = []

    for app_name in app_names:
        # returns first app where condition is true
        app_payload = next(
            (
                app_payload
                for app_payload in app_payloads
                if app_payload["id"] == app_name["id"]
            )
        )

        if app_payload:
            payload_json = app_payload["chipsets"]["*"][0]["app_type_payload"]
            payload = json.loads(payload_json)
            pyvizio_apps.append(
                {
                    "name": app_name["name"],
                    "country": [country.lower() for country in app_name["country"]],
                    "id": app_name["id"],
                    "payload": payload,
                }
            )

    return pyvizio_apps
