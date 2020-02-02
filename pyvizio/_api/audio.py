from typing import Any, Dict

from pyvizio._api._protocol import (
    ACTION_MODIFY,
    ENDPOINT,
    TYPE_EQ_LIST,
    TYPE_EQ_SLIDER,
    ResponseKey,
)
from pyvizio._api.base import CommandBase, InfoCommandBase
from pyvizio._api.item import Item, ItemInfoCommandBase
from pyvizio.helpers import dict_get_case_insensitive


class GetCurrentVolumeCommand(ItemInfoCommandBase):
    def __init__(self, device_type: str) -> None:
        super(GetCurrentVolumeCommand, self).__init__(device_type, "VOLUME", 0)


class GetAudioSettingNamesCommand(InfoCommandBase):
    def __init__(self, device_type: str):
        super(GetAudioSettingNamesCommand, self).__init__()
        CommandBase.url.fset(self, ENDPOINT[device_type]["AUDIO_SETTINGS"])

    def process_response(self, json_obj: Dict[str, Any]) -> Any:
        items = [
            Item(item)
            for item in dict_get_case_insensitive(json_obj, ResponseKey.ITEMS, [])
        ]
        return [
            item.c_name
            for item in items
            if item.type.lower() in (TYPE_EQ_LIST, TYPE_EQ_SLIDER)
        ]


class GetAudioSettingCommand(ItemInfoCommandBase):
    def __init__(self, device_type: str, item_name: str) -> None:
        super(GetAudioSettingCommand, self).__init__(device_type, "AUDIO_SETTINGS", 0)
        self.item_name = item_name.lower()
        InfoCommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['AUDIO_SETTINGS']}/{self.item_name}"
        )


class ChangeAudioSettingCommand(CommandBase):
    def __init__(self, device_type: str, id: int, item_name: str, value: int) -> None:
        super(ChangeAudioSettingCommand, self).__init__()
        self.item_name = item_name.lower()
        CommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['AUDIO_SETTINGS']}/{self.item_name}"
        )

        self.VALUE = value
        # noinspection SpellCheckingInspection
        self.HASHVAL = int(id)
        self.REQUEST = ACTION_MODIFY.upper()
