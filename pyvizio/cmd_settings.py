from .protocol import get_json_obj, ProtoConstants, CommandBase, CNames


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


class SettingsCommandBase(CommandBase):
    BASE_URL = "/menu_native/dynamic/tv_settings"

    def get_url(self):
        return self.BASE_URL + self._url

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


class GetSettingsCommandBase(SettingsCommandBase):
    @property
    def _method(self):
        return "GET"


class GetAudioSettingsCommand(GetSettingsCommandBase):
    @property
    def _url(self):
        return "/audio"

    def process_response(self, json_obj):
        return self._get_items(json_obj)


class GetCurrentAudioCommand(GetAudioSettingsCommand):
    def process_response(self, json_obj):
        items = super().process_response(json_obj)
        for itm in items:
            if itm.c_name.lower() == CNames.Audio.VOLUME:
                return int(itm.value)

        return 0
