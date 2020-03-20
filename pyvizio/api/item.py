"""Vizio SmartCast API commands and class for individual item settings."""

from typing import Any, Dict, Union

from pyvizio.api._protocol import (
    ACTION_MODIFY,
    ENDPOINT,
    ITEM_CNAME,
    PATH_MODEL,
    ResponseKey,
)
from pyvizio.api.base import CommandBase, InfoCommandBase
from pyvizio.helpers import dict_get_case_insensitive, get_value_from_path


class GetDeviceInfoCommand(InfoCommandBase):
    """Command to get device info."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get device info."""
        super(GetDeviceInfoCommand, self).__init__(ENDPOINT[device_type]["DEVICE_INFO"])
        self.paths = PATH_MODEL[device_type]

    def process_response(self, json_obj: Dict[str, Any]) -> bool:
        """Return response to command to get device info."""
        return dict_get_case_insensitive(json_obj, ResponseKey.ITEMS, [{}])[0]


class GetModelNameCommand(GetDeviceInfoCommand):
    """Command to get device model name."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get device model name."""
        super(GetModelNameCommand, self).__init__(device_type)

    def process_response(self, json_obj: Dict[str, Any]) -> bool:
        """Return response to command to get device model name."""
        return get_value_from_path(
            dict_get_case_insensitive(
                super(GetModelNameCommand, self).process_response(json_obj),
                ResponseKey.VALUE,
                {},
            ),
            self.paths,
        )


class Item(object):
    """Individual item setting."""

    def __init__(self, json_obj: Dict[str, Any]) -> None:
        """Initialize individual item setting."""
        self.id = None
        id = dict_get_case_insensitive(json_obj, ResponseKey.HASHVAL)
        if id is not None:
            self.id = int(id)

        self.c_name = dict_get_case_insensitive(json_obj, ResponseKey.CNAME)
        self.type = dict_get_case_insensitive(json_obj, ResponseKey.TYPE)
        self.name = dict_get_case_insensitive(json_obj, ResponseKey.NAME)
        self.value = dict_get_case_insensitive(json_obj, ResponseKey.VALUE)

        self.min = None
        min = dict_get_case_insensitive(json_obj, ResponseKey.MINIMUM)
        if min is not None:
            self.min = int(min)

        self.max = None
        max = dict_get_case_insensitive(json_obj, ResponseKey.MAXIMUM)
        if max is not None:
            self.max = int(max)

        self.center = None
        center = dict_get_case_insensitive(json_obj, ResponseKey.CENTER)
        if center is not None:
            self.center = int(center)

        self.choices = dict_get_case_insensitive(json_obj, ResponseKey.ELEMENTS, [])

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or (
            self.c_name == other.c_name
            and self.type == other.type
            and self.name == other.name
            and self.value == other.value
        )


class DefaultReturnItem(object):
    """Mock individual item setting response when item is not found."""

    def __init__(self, value: Any) -> None:
        """Initialize mock individual item setting response when item is not found."""
        self.value = value

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__


class ItemInfoCommandBase(InfoCommandBase):
    """Command to get individual item setting."""

    def __init__(
        self, device_type: str, item_name: str, default_return: Union[int, str] = None
    ) -> None:
        """Initialize command to get individual item setting."""
        super(ItemInfoCommandBase, self).__init__(ENDPOINT[device_type][item_name])
        self.item_name = item_name.upper()
        self.default_return = default_return

    def process_response(self, json_obj: Dict[str, Any]) -> Any:
        """Return response to command to get individual item setting."""
        items = [
            Item(item)
            for item in dict_get_case_insensitive(json_obj, ResponseKey.ITEMS, [])
        ]

        for itm in items:
            if itm.c_name.lower() in (
                ITEM_CNAME.get(self.item_name, ""),
                self.item_name,
            ) and (
                itm.value is not None
                or itm.center is not None
                or itm.choices is not None
            ):
                return itm

        if self.default_return is not None:
            return DefaultReturnItem(self.default_return)

        return None


class ItemCommandBase(CommandBase):
    """Command to set value of individual item setting."""

    def __init__(
        self, device_type: str, item_name: str, id: int, value: Union[int, str]
    ) -> None:
        """Initialize command to set value of individual item setting."""
        super(ItemCommandBase, self).__init__(ENDPOINT[device_type][item_name])
        self.item_name = item_name

        self.VALUE = value
        # noinspection SpellCheckingInspection
        self.HASHVAL = int(id)
        self.REQUEST = ACTION_MODIFY.upper()


class GetCurrentPowerStateCommand(ItemInfoCommandBase):
    """Command to get current power state of device."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get current power state of device."""
        super(GetCurrentPowerStateCommand, self).__init__(device_type, "POWER_MODE", 0)


class GetESNCommand(ItemInfoCommandBase):
    """Command to get device ESN (electronic serial number?)."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get device ESN (electronic serial number?)."""
        super(GetESNCommand, self).__init__(device_type, "ESN")


class GetSerialNumberCommand(ItemInfoCommandBase):
    """Command to get device serial number."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get device serial number."""
        super(GetSerialNumberCommand, self).__init__(device_type, "SERIAL_NUMBER")


class GetVersionCommand(ItemInfoCommandBase):
    """Command to get SmartCast software version."""

    def __init__(self, device_type: str) -> None:
        """Initialize command to get SmartCast software version."""
        super(GetVersionCommand, self).__init__(device_type, "VERSION")
