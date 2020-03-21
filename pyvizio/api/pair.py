"""Vizio SmartCast API commands and class for pairing."""

from typing import Any, Dict

from pyvizio.api._protocol import ENDPOINT, PairingResponseKey, ResponseKey
from pyvizio.api.base import CommandBase
from pyvizio.helpers import dict_get_case_insensitive


class PairCommandBase(CommandBase):
    """Base pairing command."""

    def __init__(self, device_id: str, device_type: str, endpoint: str) -> None:
        """Initialize base pairing command."""
        super(PairCommandBase, self).__init__(ENDPOINT[device_type][endpoint])
        self.DEVICE_ID: str = device_id


class BeginPairResponse(object):
    """Response from command to begin pairing process."""

    def __init__(self, ch_type: str, token: str) -> None:
        """Initialize response from command to begin pairing process."""
        self.ch_type: str = ch_type
        self.token: str = token

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__


class BeginPairCommand(PairCommandBase):
    """Command to begin pairing process."""

    def __init__(self, device_id: str, device_name: str, device_type: str) -> None:
        """Initialize command to begin pairing process."""
        super().__init__(device_id, device_type, "BEGIN_PAIR")
        self.DEVICE_NAME: str = str(device_name)

    def process_response(self, json_obj: Dict[str, Any]) -> BeginPairResponse:
        """Return response to command to begin pairing process."""
        item = dict_get_case_insensitive(json_obj, ResponseKey.ITEM)

        return BeginPairResponse(
            dict_get_case_insensitive(item, PairingResponseKey.CHALLENGE_TYPE),
            dict_get_case_insensitive(item, PairingResponseKey.PAIRING_REQ_TOKEN),
        )


class PairChallengeResponse(object):
    """Response from command to complete pairing process."""

    def __init__(self, auth_token: str) -> None:
        """Initialize response from command to complete pairing process."""
        self.auth_token = auth_token

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__


class PairChallengeCommand(PairCommandBase):
    """Command to complete pairing process."""

    def __init__(
        self,
        device_id: str,
        challenge_type: int,
        pairing_token: int,
        pin: str,
        device_type: str,
    ) -> None:
        """Initialize command to complete pairing process."""
        super().__init__(device_id, device_type, "FINISH_PAIR")

        self.CHALLENGE_TYPE = int(challenge_type)
        self.PAIRING_REQ_TOKEN = int(pairing_token)
        self.RESPONSE_VALUE = str(pin)

    def process_response(self, json_obj: Dict[str, Any]) -> PairChallengeResponse:
        """Return response to command to complete pairing process."""
        item = dict_get_case_insensitive(json_obj, ResponseKey.ITEM)

        return PairChallengeResponse(
            dict_get_case_insensitive(item, PairingResponseKey.AUTH_TOKEN)
        )


class CancelPairCommand(PairCommandBase):
    """Command to cancel pairing process."""

    def __init__(self, device_id, device_name: str, device_type: str) -> None:
        """Initialize command to cancel pairing process."""
        super().__init__(device_id, device_type, "CANCEL_PAIR")

        self.DEVICE_NAME = str(device_name)
