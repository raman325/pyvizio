from .protocol import get_json_obj, ProtoConstants, InfoCommandBase


class GetPowerStateCommand(InfoCommandBase):
    @property
    def _url(self):
        return "/state/device/power_mode"

    def process_response(self, json_obj):
        items = get_json_obj(json_obj, ProtoConstants.RESPONSE_ITEMS)
        is_awake = False
        if len(items) > 0:
            is_awake = 1 == get_json_obj(items[0], ProtoConstants.Item.VALUE)

        return is_awake
