"""Vizio SmartCast API commands for audio settings."""

from typing import Any, Dict, List, Optional, Union

from pyvizio.api._protocol import (
    ENDPOINT,
    TYPE_LIST,
    TYPE_MENU,
    TYPE_SLIDER,
    TYPE_VALUE,
    TYPE_X_LIST,
    ResponseKey,
)
from pyvizio.api.item import Item, ItemCommandBase, ItemInfoCommandBase
from pyvizio.helpers import dict_get_case_insensitive


class GetAllSettingTypesCommand(ItemInfoCommandBase):
    """Command to get list of all setting types."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get list of all setting types."""
        super(GetAllSettingTypesCommand, self).__init__(device_type, "SETTINGS")
        ItemInfoCommandBase.url.fset(self, f"{ENDPOINT[device_type]['SETTINGS']}")

    def process_response(self, json_obj: Dict[str, Any]) -> List[str]:
        """Return response to command to get list of all setting types."""
        items = [
            Item(item)
            for item in dict_get_case_insensitive(json_obj, ResponseKey.ITEMS, [])
        ]
        return [
            item.c_name
            for item in items
            if item.type.lower() == TYPE_MENU
            and item.c_name not in ("cast", "input", "devices", "network")
        ]


class GetAllSettingsCommand(ItemInfoCommandBase):
    """Command to get list of all setting names and corresponding values."""

    def __init__(self, device_type: str, setting_type: str) -> None:
        """Initialize command to get list of all setting names and corresponding values."""
        super(GetAllSettingsCommand, self).__init__(device_type, "SETTINGS")
        self.setting_type = setting_type.lower()
        ItemInfoCommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['SETTINGS']}/{setting_type}"
        )

    def process_response(self, json_obj: Dict[str, Any]) -> Dict[str, Union[int, str]]:
        """Return response to command to get list of all setting names and corresponding values."""
        items = [
            Item(item)
            for item in dict_get_case_insensitive(json_obj, ResponseKey.ITEMS, [])
        ]
        return {
            item.c_name: item.value
            for item in items
            if item.type.lower() in (TYPE_LIST, TYPE_SLIDER, TYPE_VALUE)
        }


class GetSettingCommand(ItemInfoCommandBase):
    """Command to get value of a setting by name."""

    def __init__(self, device_type: str, setting_type: str, setting_name: str) -> None:
        """Initialize command to get value of a setting by name."""
        super(GetSettingCommand, self).__init__(device_type, "SETTINGS", 0)
        self.item_name = setting_name.lower()
        self.setting_type = setting_type.lower()
        ItemInfoCommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['SETTINGS']}/{setting_type}/{setting_name}"
        )


class GetAllSettingsOptionsCommand(ItemInfoCommandBase):
    """Command to get list of all setting names and corresponding options."""

    def __init__(self, device_type: str, setting_type: str) -> None:
        """Initialize command to get list of all setting names and corresponding options."""
        super(GetAllSettingsOptionsCommand, self).__init__(
            device_type, "SETTINGS_OPTIONS"
        )
        self.setting_type = setting_type.lower()
        ItemInfoCommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['SETTINGS_OPTIONS']}/{setting_type}"
        )

    def process_response(
        self, json_obj: Dict[str, Any]
    ) -> Dict[str, Union[List[str], Dict[str, Union[int, str]]]]:
        """Return response to command to get list of all setting names and corresponding options."""
        items = [
            Item(item)
            for item in dict_get_case_insensitive(json_obj, ResponseKey.ITEMS, [])
        ]

        settings_options = {}
        for item in items:
            if item.type.lower() in (TYPE_SLIDER, TYPE_VALUE):
                settings_options[item.c_name] = {"min": item.min, "max": item.max}
                if item.center is not None:
                    settings_options[item.c_name].update({"default": item.center})
            elif item.type.lower() == TYPE_LIST:
                settings_options[item.c_name] = item.choices.copy()

        return settings_options


class GetSettingOptionsCommand(GetAllSettingsOptionsCommand):
    """Command to get options of a setting by name."""

    def __init__(self, device_type: str, setting_type: str, setting_name: str) -> None:
        """Initialize command to get options of a setting by name."""
        self.setting_name = setting_name
        self.setting_type = setting_type.lower()
        super(GetSettingOptionsCommand, self).__init__(device_type, self.setting_type)

    def process_response(
        self, json_obj: Dict[str, Any]
    ) -> Optional[Union[List[str], Dict[str, Union[int, str]]]]:
        """Return response to command to get options of a setting by name."""
        return (
            super(GetSettingOptionsCommand, self)
            .process_response(json_obj)
            .get(self.setting_name)
        )


class GetAllSettingsOptionsXListCommand(ItemInfoCommandBase):
    """Command to get list of all setting names and corresponding options for settings of type XList."""

    def __init__(self, device_type: str, setting_type: str) -> None:
        """Initialize command to get list of all setting names and corresponding options for settings of type XList."""
        super(GetAllSettingsOptionsXListCommand, self).__init__(device_type, "SETTINGS")
        self.setting_type = setting_type.lower()
        ItemInfoCommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['SETTINGS']}/{setting_type}"
        )

    def process_response(self, json_obj: Dict[str, Any]) -> Dict[str, List[str]]:
        """Return response to command to get list of all setting names and corresponding options for settings of type XList."""
        items = [
            Item(item)
            for item in dict_get_case_insensitive(json_obj, ResponseKey.ITEMS, [])
            if item.type.lower() == TYPE_X_LIST
        ]

        return {item.c_name: item.choices for item in items}


class GetSettingOptionsXListCommand(GetAllSettingsOptionsXListCommand):
    """Command to get options of an audio setting by name (used for setting of type XList)."""

    def __init__(self, device_type: str, setting_type: str, setting_name: str) -> None:
        """Initialize command to get options of an audio setting by name (used for setting of type XList)."""
        self.setting_name = setting_name
        self.setting_type = setting_type.lower()
        super(GetSettingOptionsXListCommand, self).__init__(
            device_type, self.setting_type
        )

    def process_response(self, json_obj: Dict[str, Any]) -> List[str]:
        """Return response to command to get options of an audio setting by name (used for setting of type XList)."""
        return (
            super(GetSettingOptionsXListCommand, self)
            .process_response(json_obj)
            .get(self.setting_name)
        )


class ChangeSettingCommand(ItemCommandBase):
    """Command to set value of a setting by name to new value."""

    def __init__(
        self,
        device_type: str,
        id: int,
        setting_type: str,
        setting_name: str,
        value: Union[int, str],
    ) -> None:
        """Initialize command to set value of a setting by name to new value."""
        super(ChangeSettingCommand, self).__init__(device_type, "SETTINGS", id, value)
        ItemCommandBase.url.fset(
            self, f"{ENDPOINT[device_type]['SETTINGS']}/{setting_type}/{setting_name}"
        )
