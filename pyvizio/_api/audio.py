from typing import Any, Dict, Union

from pyvizio._api._protocol import (
    ENDPOINT,
    TYPE_EQ_LIST,
    TYPE_EQ_SLIDER,
    ResponseKey,
)
from pyvizio._api.item import Item, ItemCommandBase, ItemInfoCommandBase
from pyvizio.helpers import dict_get_case_insensitive


class GetCurrentVolumeCommand(ItemInfoCommandBase):
    def __init__(self, device_type: str) -> None:
        super(GetCurrentVolumeCommand, self).__init__(device_type, "VOLUME", 0)


class GetAudioSettingNamesCommand(ItemInfoCommandBase):
    def __init__(self, device_type: str):
        super(GetAudioSettingNamesCommand, self).__init__(device_type, "AUDIO_SETTINGS")

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
    def __init__(self, device_type: str, setting_name: str) -> None:
        super(GetAudioSettingCommand, self).__init__(device_type, "AUDIO_SETTINGS", 0)
        self.item_name = setting_name.lower()
        ItemInfoCommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['AUDIO_SETTINGS']}/{setting_name}"
        )


class ChangeAudioSettingCommand(ItemCommandBase):
    def __init__(
        self, device_type: str, id: int, setting_name: str, value: Union[int, str]
    ) -> None:
        super(ChangeAudioSettingCommand, self).__init__(device_type, "AUDIO_SETTINGS", id, value)
        ItemCommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['AUDIO_SETTINGS']}/{setting_name}"
        )
