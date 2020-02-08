from typing import Any, Dict, List, Optional

from pyvizio._api._protocol import ResponseKey
from pyvizio._api.item import Item, ItemCommandBase, ItemInfoCommandBase
from pyvizio.helpers import dict_get_case_insensitive


class InputItem(Item):
    def __init__(self, json_item: Dict[str, Any], is_extended_metadata: bool) -> None:
        self.id = int(dict_get_case_insensitive(json_item, ResponseKey.HASHVAL))
        self.c_name = dict_get_case_insensitive(json_item, ResponseKey.CNAME)
        self.type = dict_get_case_insensitive(json_item, ResponseKey.TYPE)
        self.name = dict_get_case_insensitive(json_item, ResponseKey.NAME)
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

    def __repr__(self) -> Dict[str, str]:
        return (
            f"InputItem(id='{self.id}', c_name='{self.c_name}', type='{self.type}', "
            f"name='{self.name}, meta_name='{self.meta_name}, "
            f"meta_data='{self.meta_data}')"
        )


class GetInputsListCommand(ItemInfoCommandBase):
    """Obtaining list of available inputs"""

    def __init__(self, device_type: str) -> None:
        super(GetInputsListCommand, self).__init__(device_type, "INPUTS")

    def process_response(self, json_obj: Dict[str, Any]) -> Optional[List[InputItem]]:
        items = dict_get_case_insensitive(json_obj, ResponseKey.ITEMS)

        if items:
            return [
                InputItem(itm, True)
                for itm in items
                if dict_get_case_insensitive(itm, ResponseKey.CNAME) != "current_input"
            ]

        return None


class GetCurrentInputCommand(ItemInfoCommandBase):
    """Obtaining current input"""

    def __init__(self, device_type: str) -> None:
        super(GetCurrentInputCommand, self).__init__(device_type, "CURRENT_INPUT")

    def process_response(self, json_obj: Dict[str, Any]) -> Optional[InputItem]:
        items = dict_get_case_insensitive(json_obj, ResponseKey.ITEMS)

        v_input = None

        if items:
            v_input = InputItem(items[0], False)

        return v_input


class ChangeInputCommand(ItemCommandBase):
    def __init__(self, device_type: str, id: int, name: str) -> None:
        super(ChangeInputCommand, self).__init__(device_type, "CURRENT_INPUT", id, name)
