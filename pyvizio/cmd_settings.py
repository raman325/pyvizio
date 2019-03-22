from .protocol import get_json_obj, ProtoConstants, CommandBase, CNames, InfoCommandBase, Endpoints


class SettingsItem(object):
    def __init__(self, json_obj):
        self.id = int(get_json_obj(json_obj, ProtoConstants.Item.HASHVAL))
        self.c_name = get_json_obj(json_obj, ProtoConstants.Item.CNAME)
        self.type = get_json_obj(json_obj, ProtoConstants.Item.TYPE)
        self.name = get_json_obj(json_obj, ProtoConstants.Item.NAME)
        self.value = get_json_obj(json_obj, ProtoConstants.Item.VALUE)
        self.options = []
        options = get_json_obj(json_obj, ProtoConstants.Item.ELEMENTS)
        if options is not None:
            for opt in options:
                self.options.append(opt)

class GetCurrentAudioCommand(InfoCommandBase):

    def __init__(self, device_type):
        super(GetCurrentAudioCommand, self).__init__()
        InfoCommandBase.url.fset(self, Endpoints.ENDPOINTS[device_type]["VOLUME"])

    @staticmethod
    def _get_items(json_obj):
        items = get_json_obj(json_obj, ProtoConstants.RESPONSE_ITEMS)
        if items is None:
            return []

        results = []
        for itm in items:
            item = SettingsItem(itm)
            results.append(item)

        return results

    def process_response(self, json_obj):
        items = self._get_items(json_obj)
        for itm in items:
            if itm.c_name.lower() == CNames.Audio.VOLUME:
                if itm.value is not None:
                    return int(itm.value)
                return None

        return 0
