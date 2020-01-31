from typing import Dict, List, Tuple

from pyvizio._api._protocol import ENDPOINT, KEY_ACTION
from pyvizio._api.base import CommandBase


class KeyPressEvent(object):
    def __init__(
        self, key_code: Tuple[int, int], action: str = KEY_ACTION["PRESS"]
    ) -> None:
        self.CODESET = key_code[0]
        self.CODE = key_code[1]
        self.ACTION = action

    def __repr__(self) -> Dict[str, str]:
        return f"KeyPressEvent(CODESET='{self.CODESET}', CODE='{self.CODE}', "
        f"ACTION='{self.ACTION}')"


class EmulateRemoteCommand(CommandBase):
    def __init__(self, key_codes: List[Tuple[int, int]], device_type: str) -> None:
        super(EmulateRemoteCommand, self).__init__()
        CommandBase.url.fset(self, ENDPOINT[device_type]["KEY_PRESS"])

        # noinspection SpellCheckingInspection
        self.KEYLIST = []

        for key_code in key_codes:
            self.KEYLIST.append(KeyPressEvent(key_code))
