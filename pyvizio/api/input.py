"""Vizio SmartCast API commands and class for device inputs."""

from typing import Any, Dict, List, Optional

from pyvizio.api._protocol import ResponseKey
from pyvizio.api.item import Item, ItemCommandBase, ItemInfoCommandBase
from pyvizio.helpers import dict_get_case_insensitive


class InputItem(Item):
    """Input device."""

    def __init__(self, json_item: Dict[str, Any], is_extended_metadata: bool) -> None:
        """Initialize input device."""
        super(InputItem, self).__init__(json_item)
        self.meta_name = None
        self.meta_data = None

        meta = dict_get_case_insensitive(json_item, ResponseKey.VALUE)

        if meta:
            if is_extended_metadata:
                self.meta_name = dict_get_case_insensitive(meta, ResponseKey.NAME)
                self.meta_data = dict_get_case_insensitive(meta, ResponseKey.METADATA)
            else:
                self.meta_name = meta

        if not self.meta_name:
            self.meta_name = self.c_name


class GetInputsListCommand(ItemInfoCommandBase):
    """Command to get list of available inputs."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get list of available inputs."""
        super(GetInputsListCommand, self).__init__(device_type, "INPUTS")

    def process_response(self, json_obj: Dict[str, Any]) -> Optional[List[InputItem]]:
        """Return response to command to get list of available inputs."""
        items = dict_get_case_insensitive(json_obj, ResponseKey.ITEMS)

        if items:
            return [
                InputItem(itm, True)
                for itm in items
                if dict_get_case_insensitive(itm, ResponseKey.CNAME) != "current_input"
            ]

        return None


class GetCurrentInputCommand(ItemInfoCommandBase):
    """Command to get currently active input."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get currently active input."""
        super(GetCurrentInputCommand, self).__init__(device_type, "CURRENT_INPUT")

    def process_response(self, json_obj: Dict[str, Any]) -> Optional[InputItem]:
        """Return response to command to get currently active input."""
        items = dict_get_case_insensitive(json_obj, ResponseKey.ITEMS)

        v_input = None

        if items:
            v_input = InputItem(items[0], False)

        return v_input


class ChangeInputCommand(ItemCommandBase):
    """Command to change active input by name."""

    def __init__(self, device_type: str, id: int, name: str) -> None:
        """Initialize command to change active input by name."""
        super(ChangeInputCommand, self).__init__(device_type, "CURRENT_INPUT", id, name)
