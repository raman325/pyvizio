from typing import Any, Dict, List, Optional

from .protocol import CNames, Endpoints, InfoCommandBase, ProtoConstants, get_json_obj


class SettingsItem(object):
    def __init__(self, json_obj: Dict[str, Any]) -> None:
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
    def __init__(self, device_type: str) -> None:
        super(GetCurrentAudioCommand, self).__init__()
        InfoCommandBase.url.fset(self, Endpoints.ENDPOINTS[device_type]["VOLUME"])

    @staticmethod
    def _get_items(json_obj: Dict[str, Any]) -> List[SettingsItem]:
        items = get_json_obj(json_obj, ProtoConstants.RESPONSE_ITEMS)
        if items is None:
            return []

        results = []
        for itm in items:
            item = SettingsItem(itm)
            results.append(item)

        return results

    def process_response(self, json_obj: Dict[str, Any]) -> int:
        items = self._get_items(json_obj)
        for itm in items:
            if itm.c_name.lower() == CNames.Audio.VOLUME:
                if itm.value is not None:
                    return int(itm.value)
        return 0


class GetESNCommand(InfoCommandBase):
    def __init__(self, device_type: str) -> None:
        super(GetESNCommand, self).__init__()
        InfoCommandBase.url.fset(self, Endpoints.ENDPOINTS[device_type]["ESN"])

    @staticmethod
    def _get_items(json_obj: Dict[str, Any]) -> List[SettingsItem]:
        items = get_json_obj(json_obj, ProtoConstants.RESPONSE_ITEMS)
        if items is None:
            return []

        results = []
        for itm in items:
            item = SettingsItem(itm)
            results.append(item)

        return results

    def process_response(self, json_obj: Dict[str, Any]) -> Optional[str]:
        items = self._get_items(json_obj)
        for itm in items:
            if itm.c_name.lower() == CNames.ESN.ESN:
                if itm.value is not None:
                    return itm.value

        return None
