from .protocol import CommandBase, KeyCodes


class KeyPressEvent(object):
    def __init__(self, key_code, action=KeyCodes.KeyPressActions.KEY_PRESS):
        self.CODESET = key_code[0]
        self.CODE = key_code[1]
        self.ACTION = action


class EmulateRemoteCommand(CommandBase):
    @property
    def _url(self):
        return "/key_command/"

    def __init__(self, key_codes):
        # noinspection SpellCheckingInspection
        self.KEYLIST = []
        for key_code in key_codes:
            event = KeyPressEvent(key_code)
            self.KEYLIST.append(event)

    def process_response(self, json_obj):
        return True
