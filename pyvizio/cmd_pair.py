from typing import Any, Dict

from .protocol import CommandBase, Endpoints, ProtoConstants, get_json_obj


class PairCommandBase(CommandBase):
    def __init__(self, device_id: str, device_type: str, endpoint: str) -> None:
        super(PairCommandBase, self).__init__()
        CommandBase.url.fset(self, Endpoints.ENDPOINTS[device_type][endpoint])
        self.DEVICE_ID = device_id


class BeginPairResponse(object):
    def __init__(self, ch_type: str, token: str) -> None:
        self.ch_type = ch_type
        self.token = token


class BeginPairCommand(PairCommandBase):
    """Initiating pairing process."""

    def __init__(self, device_id: str, device_name: str, device_type: str) -> None:
        super().__init__(device_id, device_type, "BEGIN_PAIR")
        self.DEVICE_NAME = str(device_name)

    def process_response(self, json_obj: Dict[str, Any]) -> BeginPairResponse:
        item = get_json_obj(json_obj, ProtoConstants.RESPONSE_ITEM)
        response = BeginPairResponse(
            get_json_obj(item, ProtoConstants.CHALLENGE_TYPE),
            get_json_obj(item, ProtoConstants.PAIRING_REQ_TOKEN),
        )
        return response


class PairChallengeResponse(object):
    def __init__(self, auth_token: str) -> None:
        self.auth_token = auth_token


class PairChallengeCommand(PairCommandBase):
    """Finish pairing."""

    def __init__(
        self,
        device_id: str,
        challenge_type: str,
        pairing_token: str,
        pin: str,
        device_type: str,
    ) -> None:
        super().__init__(device_id, device_type, "FINISH_PAIR")
        self.CHALLENGE_TYPE = int(challenge_type)
        self.RESPONSE_VALUE = str(pin)
        self.PAIRING_REQ_TOKEN = int(pairing_token)

    def process_response(self, json_obj: Dict[str, Any]) -> PairChallengeResponse:
        item = get_json_obj(json_obj, ProtoConstants.RESPONSE_ITEM)
        response = PairChallengeResponse(get_json_obj(item, ProtoConstants.AUTH_TOKEN))
        return response


class CancelPairCommand(PairCommandBase):
    """Cancel pairing process."""

    def __init__(self, device_id, device_name: str, device_type: str) -> None:
        super().__init__(device_id, device_type, "CANCEL_PAIR")
        self.DEVICE_NAME = str(device_name)

    def process_response(self, json_obj: Dict[str, Any]) -> bool:
        return True
