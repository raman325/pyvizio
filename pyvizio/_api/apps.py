from typing import Any, Dict, Union

from pyvizio._api._protocol import ENDPOINT, ResponseKey
from pyvizio._api.base import CommandBase
from pyvizio._api.input import ItemInfoCommandBase
from pyvizio.const import NO_APP_RUNNING, UNKNOWN_APP
from pyvizio.helpers import dict_get_case_insensitive


class AppPayload(object):
    def __init__(
        self,
        APP_ID: Union[str, int] = None,
        NAME_SPACE: Union[int, str] = None,
        MESSAGE: str = None,
    ) -> None:
        self.APP_ID = APP_ID
        self.NAME_SPACE = NAME_SPACE
        self.MESSAGE = MESSAGE


class LaunchAppCommand(CommandBase):
    def __init__(self, device_type: str, app_name: str) -> None:
        super(LaunchAppCommand, self).__init__()
        LaunchAppCommand.url.fset(self, ENDPOINT[device_type]["LAUNCH_APP"])

        app_def = next(
            (
                app_def
                for app_def in (APP_HOME + APPS)
                if app_def["name"].lower() == app_name.lower()
            ),
            dict(),
        )

        self.VALUE = AppPayload(**app_def.get("payload", dict()))


class GetCurrentAppCommand(ItemInfoCommandBase):
    """Obtaining currently running app"""

    def __init__(self, device_type: str) -> None:
        super(GetCurrentAppCommand, self).__init__(device_type, "CURRENT_APP")

    def process_response(self, json_obj: Dict[str, Any]) -> str:
        item = dict_get_case_insensitive(json_obj, ResponseKey.ITEM, {})
        current_app_id = dict_get_case_insensitive(item, ResponseKey.VALUE)

        if current_app_id:
            app_def = next(
                (
                    app_def
                    for app_def in (APP_HOME + APPS)
                    if app_def["payload"]["APP_ID"] == current_app_id["APP_ID"]
                    and app_def["payload"]["NAME_SPACE"] == current_app_id["NAME_SPACE"]
                ),
                dict(),
            )

            return app_def.get("name", UNKNOWN_APP)

        return NO_APP_RUNNING


APP_HOME = [
    {
        "name": "SmartCast Home",
        "country": ["*"],
        "payload": {
            "NAME_SPACE": 4,
            "APP_ID": "1",
            "MESSAGE": "http://127.0.0.1:12345/scfs/sctv/main.html",
        },
    }
]
APPS = [
    {
        "name": "Prime Video",
        "country": ["*"],
        "id": "33",
        "payload": {"NAME_SPACE": 2, "APP_ID": "4", "MESSAGE": None},
    },
    {
        "name": "CBS All Access",
        "country": ["usa"],
        "id": "9",
        "payload": {"NAME_SPACE": 2, "APP_ID": "37", "MESSAGE": None},
    },
    {
        "name": "CBS News",
        "country": ["usa", "can"],
        "id": "56",
        "payload": {"NAME_SPACE": 2, "APP_ID": "42", "MESSAGE": None},
    },
    {
        "name": "Crackle",
        "country": ["usa"],
        "id": "8",
        "payload": {"NAME_SPACE": 2, "APP_ID": "5", "MESSAGE": None},
    },
    {
        "name": "Curiosity Stream",
        "country": ["usa", "can"],
        "id": "37",
        "payload": {"NAME_SPACE": 2, "APP_ID": "12", "MESSAGE": None},
    },
    {
        "name": "Fandango Now",
        "country": ["usa"],
        "id": "24",
        "payload": {"NAME_SPACE": 2, "APP_ID": "7", "MESSAGE": None},
    },
    {
        "name": "FilmRise",
        "country": ["usa"],
        "id": "47",
        "payload": {"NAME_SPACE": 2, "APP_ID": "24", "MESSAGE": None},
    },
    {
        "name": "Flixfling",
        "country": ["*"],
        "id": "49",
        "payload": {"NAME_SPACE": 2, "APP_ID": "36", "MESSAGE": None},
    },
    {
        "name": "Haystack TV",
        "country": ["usa", "can"],
        "id": "35",
        "payload": {
            "NAME_SPACE": 0,
            "APP_ID": "898AF734",
            "MESSAGE": '{"CAST_NAMESPACE":"urn:x-cast:com.google.cast.media","CAST_MESSAGE":{"type":"LOAD","media":{},"autoplay":true,"currentTime":0,"customData":{"platform":"sctv"}}}',
        },
    },
    {
        "name": "Hulu",
        "country": ["usa"],
        "id": "19",
        "payload": {"NAME_SPACE": 2, "APP_ID": "3", "MESSAGE": None},
    },
    {
        "name": "iHeartRadio",
        "country": ["usa"],
        "id": "11",
        "payload": {"NAME_SPACE": 2, "APP_ID": "6", "MESSAGE": None},
    },
    {
        "name": "NBC",
        "country": ["usa"],
        "id": "43",
        "payload": {"NAME_SPACE": 2, "APP_ID": "10", "MESSAGE": None},
    },
    {
        "name": "Netflix",
        "country": ["*"],
        "id": "34",
        "payload": {"NAME_SPACE": 3, "APP_ID": "1", "MESSAGE": None},
    },
    {
        "name": "Plex",
        "country": ["usa", "can"],
        "id": "40",
        "payload": {"NAME_SPACE": 2, "APP_ID": "9", "MESSAGE": None},
    },
    {
        "name": "Pluto TV",
        "country": ["usa"],
        "id": "12",
        "payload": {
            "NAME_SPACE": 0,
            "APP_ID": "E6F74C01",
            "MESSAGE": '{"CAST_NAMESPACE":"urn:x-cast:tv.pluto","CAST_MESSAGE":{"command":"initializePlayback","channel":"","episode":"","time":0}}',
        },
    },
    {
        "name": "RedBox",
        "country": ["usa"],
        "id": "55",
        "payload": {"NAME_SPACE": 2, "APP_ID": "41", "MESSAGE": None},
    },
    {
        "name": "TasteIt",
        "country": ["*"],
        "id": "52",
        "payload": {"NAME_SPACE": 2, "APP_ID": "26", "MESSAGE": None},
    },
    {
        "name": "Toon Goggles",
        "country": ["usa", "can"],
        "id": "46",
        "payload": {"NAME_SPACE": 2, "APP_ID": "21", "MESSAGE": None},
    },
    {
        "name": "Vudu",
        "country": ["usa"],
        "id": "6",
        "payload": {
            "NAME_SPACE": 2,
            "APP_ID": "21",
            "MESSAGE": "https://my.vudu.com/castReceiver/index.html?launch-source=app-icon",
        },
    },
    {
        "name": "XUMO",
        "country": ["usa"],
        "id": "27",
        "payload": {
            "NAME_SPACE": 0,
            "APP_ID": "36E1EA1F",
            "MESSAGE": '{"CAST_NAMESPACE":"urn:x-cast:com.google.cast.media","CAST_MESSAGE":{"type":"LOAD","media":{},"autoplay":true,"currentTime":0,"customData":{}}}',
        },
    },
    {
        "name": "YouTubeTV",
        "country": ["usa", "mexico"],
        "id": "45",
        "payload": {"NAME_SPACE": 5, "APP_ID": "3", "MESSAGE": None},
    },
    {
        "name": "YouTube",
        "country": ["*"],
        "id": "44",
        "payload": {"NAME_SPACE": 5, "APP_ID": "1", "MESSAGE": None},
    },
    {
        "name": "Baeble",
        "country": ["usa"],
        "id": "39",
        "payload": {"NAME_SPACE": 2, "APP_ID": "11", "MESSAGE": None},
    },
    {
        "name": "DAZN",
        "country": ["usa", "can"],
        "id": "57",
        "payload": {"NAME_SPACE": 2, "APP_ID": "34", "MESSAGE": None},
    },
    {
        "name": "FitFusion by Jillian Michaels",
        "country": ["usa", "can"],
        "id": "54",
        "payload": {"NAME_SPACE": 2, "APP_ID": "39", "MESSAGE": None},
    },
    {
        "name": "Newsy",
        "country": ["usa", "can"],
        "id": "38",
        "payload": {"NAME_SPACE": 2, "APP_ID": "15", "MESSAGE": None},
    },
    {
        "name": "Cocoro TV",
        "country": ["usa", "can"],
        "id": "63",
        "payload": {"NAME_SPACE": 2, "APP_ID": "55", "MESSAGE": None},
    },
    {
        "name": "ConTV",
        "country": ["usa", "can"],
        "id": "41",
        "payload": {"NAME_SPACE": 2, "APP_ID": "18", "MESSAGE": None},
    },
    {
        "name": "Dove Channel",
        "country": ["usa", "can"],
        "id": "42",
        "payload": {"NAME_SPACE": 2, "APP_ID": "16", "MESSAGE": None},
    },
    {
        "name": "Love Destination",
        "country": ["*"],
        "id": "64",
        "payload": {"NAME_SPACE": 2, "APP_ID": "57", "MESSAGE": None},
    },
    {
        "name": "WatchFree",
        "country": ["usa"],
        "id": "48",
        "payload": {"NAME_SPACE": 2, "APP_ID": "22", "MESSAGE": None},
    },
    {
        "name": "AsianCrush",
        "country": ["usa", "can"],
        "id": "50",
        "payload": {
            "NAME_SPACE": 2,
            "APP_ID": "27",
            "MESSAGE": "https://html5.asiancrush.com/?ua=viziosmartcast",
        },
    },
]
