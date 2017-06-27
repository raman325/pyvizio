from .protocol import get_json_obj, ProtoConstants, InfoCommandBase, CommandBase


class VizioInput(object):
    def __init__(self, json_item, is_extended_metadata):
        self.id = int(get_json_obj(json_item, ProtoConstants.Item.HASHVAL))
        self.c_name = get_json_obj(json_item, ProtoConstants.Item.CNAME)
        self.type = get_json_obj(json_item, ProtoConstants.Item.TYPE)
        self.name = get_json_obj(json_item, ProtoConstants.Item.NAME)
        self.meta_name = None
        self.meta_data = None

        meta = get_json_obj(json_item, ProtoConstants.Item.VALUE)
        if meta is not None:
            if is_extended_metadata:
                self.meta_name = get_json_obj(meta, ProtoConstants.Item.NAME)
                self.meta_data = get_json_obj(meta, ProtoConstants.Item.METADATA)
            else:
                self.meta_name = meta

        if self.meta_name is None or "" == self.meta_name:
            self.meta_name = self.c_name


class GetInputsListCommand(InfoCommandBase):
    """Obtaining list of available inputs"""

    def process_response(self, json_obj):
        items = get_json_obj(json_obj, ProtoConstants.RESPONSE_ITEMS)
        inputs = []
        if items is not None:
            for itm in items:
                v_input = VizioInput(itm, True)
                inputs.append(v_input)

        return inputs

    @property
    def _url(self):
        return "/menu_native/dynamic/tv_settings/devices/name_input"


class GetCurrentInputCommand(InfoCommandBase):
    """Obtaining current input"""

    def process_response(self, json_obj):
        items = get_json_obj(json_obj, ProtoConstants.RESPONSE_ITEMS)
        v_input = None
        if len(items) > 0:
            v_input = VizioInput(items[0], False)
        return v_input

    @property
    def _url(self):
        return "/menu_native/dynamic/tv_settings/devices/current_input"


class ChangeInputCommand(CommandBase):
    @property
    def _url(self):
        return "/menu_native/dynamic/tv_settings/devices/current_input"

    def __init__(self, id_, name):
        self.VALUE = str(name)
        # noinspection SpellCheckingInspection
        self.HASHVAL = int(id_)
        self.REQUEST = ProtoConstants.ACTION_MODIFY

    def process_response(self, json_obj):
        return True
