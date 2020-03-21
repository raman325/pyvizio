"""Vizio SmartCast API command and class for emulating remote key presses."""

from typing import List, Tuple

from pyvizio.api._protocol import ENDPOINT, KEY_ACTION
from pyvizio.api.base import CommandBase


class KeyPressEvent(object):
    """Emulated remote key press."""

    def __init__(
        self, key_code: Tuple[int, int], action: str = KEY_ACTION["PRESS"]
    ) -> None:
        """Initialize emulated remote key press."""
        self.CODESET: int = key_code[0]
        self.CODE: int = key_code[1]
        self.ACTION: str = action

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__


class EmulateRemoteCommand(CommandBase):
    """Command to emulate remote key press."""

    def __init__(self, key_codes: List[Tuple[int, int]], device_type: str) -> None:
        """Initialize command to emulate remote key press."""
        super(EmulateRemoteCommand, self).__init__(ENDPOINT[device_type]["KEY_PRESS"])

        # noinspection SpellCheckingInspection
        self.KEYLIST: List[KeyPressEvent] = []

        for key_code in key_codes:
            self.KEYLIST.append(KeyPressEvent(key_code))
