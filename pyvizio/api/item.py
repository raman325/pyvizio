"""Vizio SmartCast API item data type."""

from __future__ import annotations

from typing import Any

from pyvizio.api._protocol import ResponseKey
from pyvizio.helpers import dict_get_case_insensitive


class Item:
    """Individual item setting."""

    def __init__(self, json_obj: dict[str, Any]) -> None:
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
