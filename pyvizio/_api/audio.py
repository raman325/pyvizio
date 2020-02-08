"""Vizio SmartCast API commands for audio settings."""

from typing import Any, Dict, Union

from pyvizio._api._protocol import (
    ENDPOINT,
    TYPE_EQ_LIST,
    TYPE_EQ_SLIDER,
    TYPE_VALUE,
    ResponseKey,
)
from pyvizio._api.item import Item, ItemCommandBase, ItemInfoCommandBase
from pyvizio.helpers import dict_get_case_insensitive


class GetAllAudioSettingsCommand(ItemInfoCommandBase):
    """Command to get list of all audio setting names and corresponding values."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get list of all audio setting names and corresponding values."""
        super(GetAllAudioSettingsCommand, self).__init__(device_type, "AUDIO_SETTINGS")

    def process_response(self, json_obj: Dict[str, Any]) -> Dict[str, Union[int, str]]:
        """Return response to command to get list of all audio setting names and corresponding values."""
        items = [
            Item(item)
            for item in dict_get_case_insensitive(json_obj, ResponseKey.ITEMS, [])
        ]
        audio_settings = {}
        for item in items:
            if item.type.lower() in (TYPE_EQ_LIST, TYPE_EQ_SLIDER, TYPE_VALUE):
                audio_settings[item.c_name] = item.value
        return audio_settings


class GetAudioSettingCommand(ItemInfoCommandBase):
    """Command to get value of an audio setting by name."""

    def __init__(self, device_type: str, setting_name: str) -> None:
        """Initialize command to get value of an audio setting by name."""
        super(GetAudioSettingCommand, self).__init__(device_type, "AUDIO_SETTINGS", 0)
        self.item_name = setting_name.lower()
        ItemInfoCommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['AUDIO_SETTINGS']}/{setting_name}"
        )


class ChangeAudioSettingCommand(ItemCommandBase):
    """Command to set value of an audio setting by name to new value."""

    def __init__(
        self, device_type: str, id: int, setting_name: str, value: Union[int, str]
    ) -> None:
        """Initialize command to set value of an audio setting by name to new value."""
        super(ChangeAudioSettingCommand, self).__init__(
            device_type, "AUDIO_SETTINGS", id, value
        )
        ItemCommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['AUDIO_SETTINGS']}/{setting_name}"
        )
