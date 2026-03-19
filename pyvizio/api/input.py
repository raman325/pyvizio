"""Vizio SmartCast API input data type."""

from __future__ import annotations

from typing import Any

from pyvizio.api._protocol import ResponseKey
from pyvizio.api.item import Item
from pyvizio.helpers import dict_get_case_insensitive


class InputItem(Item):
    """Input device."""

    def __init__(self, json_item: dict[str, Any], is_extended_metadata: bool) -> None:
        """Initialize input device."""
        super().__init__(json_item)
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
