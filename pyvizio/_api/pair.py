from typing import Any, Dict

from pyvizio._api._protocol import ENDPOINT, PairingResponseKey, ResponseKey
from pyvizio._api.base import CommandBase
from pyvizio.helpers import dict_get_case_insensitive


class PairCommandBase(CommandBase):
    def __init__(self, device_id: str, device_type: str, endpoint: str) -> None:
        super(PairCommandBase, self).__init__()
        CommandBase.url.fset(self, ENDPOINT[device_type][endpoint])
        self.DEVICE_ID = device_id


class BeginPairResponse(object):
    def __init__(self, ch_type: str, token: str) -> None:
        self.ch_type = ch_type
        self.token = token

    def __repr__(self) -> Dict[str, str]:
        return f"BeginPairResponse(ch_type='{self.ch_type}', token='{self.token}')"


class BeginPairCommand(PairCommandBase):
    """Initiating pairing process."""

    def __init__(self, device_id: str, device_name: str, device_type: str) -> None:
        super().__init__(device_id, device_type, "BEGIN_PAIR")
        self.DEVICE_NAME = str(device_name)

    def process_response(self, json_obj: Dict[str, Any]) -> BeginPairResponse:
        item = dict_get_case_insensitive(json_obj, ResponseKey.ITEM)

        return BeginPairResponse(
            dict_get_case_insensitive(item, PairingResponseKey.CHALLENGE_TYPE),
            dict_get_case_insensitive(item, PairingResponseKey.PAIRING_REQ_TOKEN),
        )


class PairChallengeResponse(object):
    def __init__(self, auth_token: str) -> None:
        self.auth_token = auth_token

    def __repr__(self) -> Dict[str, str]:
        return f"PairChallengeResponse(auth_token='{self.auth_token}')"


class PairChallengeCommand(PairCommandBase):
    """Finish pairing."""

    def __init__(
        self,
        device_id: str,
        challenge_type: int,
        pairing_token: int,
        pin: str,
        device_type: str,
    ) -> None:
        super().__init__(device_id, device_type, "FINISH_PAIR")

        self.CHALLENGE_TYPE = int(challenge_type)
        self.PAIRING_REQ_TOKEN = int(pairing_token)
        self.RESPONSE_VALUE = str(pin)

    def process_response(self, json_obj: Dict[str, Any]) -> PairChallengeResponse:
        item = dict_get_case_insensitive(json_obj, ResponseKey.ITEM)

        return PairChallengeResponse(
            dict_get_case_insensitive(item, PairingResponseKey.AUTH_TOKEN)
        )


class CancelPairCommand(PairCommandBase):
    """Cancel pairing process."""

    def __init__(self, device_id, device_name: str, device_type: str) -> None:
        super().__init__(device_id, device_type, "CANCEL_PAIR")

        self.DEVICE_NAME = str(device_name)

    def process_response(self, json_obj: Dict[str, Any]) -> bool:
        return True
