from typing import Any, Dict, Union

from pyvizio._api._protocol import (
    ACTION_MODIFY,
    ENDPOINT,
    ITEM_CNAME,
    PATH_MODEL,
    ResponseKey,
)
from pyvizio._api.base import CommandBase, InfoCommandBase
from pyvizio.helpers import dict_get_case_insensitive, get_value_from_path


class GetModelNameCommand(InfoCommandBase):
    def __init__(self, device_type: str) -> None:
        super(GetModelNameCommand, self).__init__()
        InfoCommandBase.url.fset(self, ENDPOINT[device_type]["MODEL_NAME"])
        self.paths = PATH_MODEL[device_type]

    def process_response(self, json_obj: Dict[str, Any]) -> bool:
        items = dict_get_case_insensitive(json_obj, ResponseKey.ITEMS)
        return get_value_from_path(
            dict_get_case_insensitive(items[0], ResponseKey.VALUE, {}), self.paths
        )


class Item(object):
    def __init__(self, json_obj: Dict[str, Any]) -> None:
        self.id = None
        id = dict_get_case_insensitive(json_obj, ResponseKey.HASHVAL)
        if id:
            self.id = int(id)

        self.c_name = dict_get_case_insensitive(json_obj, ResponseKey.CNAME)
        self.type = dict_get_case_insensitive(json_obj, ResponseKey.TYPE)
        self.name = dict_get_case_insensitive(json_obj, ResponseKey.NAME)
        self.value = dict_get_case_insensitive(json_obj, ResponseKey.VALUE)

    def __repr__(self) -> Dict[str, str]:
        return (
            f"Item(id='{self.id}', c_name='{self.c_name}', "
            f"type='{self.type}', name='{self.name}', value='{self.value}')"
        )


class DefaultReturnItem(object):
    def __init__(self, value: Any) -> None:
        self.value = value


class ItemInfoCommandBase(InfoCommandBase):
    def __init__(
        self, device_type: str, item_name: str, default_return: Union[int, str] = None
    ) -> None:
        super(ItemInfoCommandBase, self).__init__()
        self.item_name = item_name.upper()
        self.default_return = default_return
        InfoCommandBase.url.fset(self, ENDPOINT[device_type][item_name])

    def process_response(self, json_obj: Dict[str, Any]) -> Any:
        items = [
            Item(item)
            for item in dict_get_case_insensitive(json_obj, ResponseKey.ITEMS, [])
        ]

        for itm in items:
            if itm.c_name.lower() in (
                ITEM_CNAME.get(self.item_name, ""),
                self.item_name,
            ):
                if itm.value is not None:
                    return itm

        if self.default_return is not None:
            return DefaultReturnItem(self.default_return)

        return None


class ItemCommandBase(CommandBase):
    def __init__(
        self, device_type: str, item_name: str, id: int, value: Union[int, str]
    ) -> None:
        super(ItemCommandBase, self).__init__()
        self.item_name = item_name
        CommandBase.url.fset(self, ENDPOINT[device_type][item_name])

        self.VALUE = value
        # noinspection SpellCheckingInspection
        self.HASHVAL = int(id)
        self.REQUEST = ACTION_MODIFY.upper()


class GetCurrentPowerStateCommand(ItemInfoCommandBase):
    def __init__(self, device_type: str) -> None:
        super(GetCurrentPowerStateCommand, self).__init__(device_type, "POWER_MODE", 0)


class GetESNCommand(ItemInfoCommandBase):
    def __init__(self, device_type: str) -> None:
        super(GetESNCommand, self).__init__(device_type, "ESN")


class GetSerialNumberCommand(ItemInfoCommandBase):
    def __init__(self, device_type: str) -> None:
        super(GetSerialNumberCommand, self).__init__(device_type, "SERIAL_NUMBER")


class GetVersionCommand(ItemInfoCommandBase):
    def __init__(self, device_type: str) -> None:
        super(GetVersionCommand, self).__init__(device_type, "VERSION")
