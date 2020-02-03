from abc import abstractmethod
from typing import Any, Dict


class CommandBase(object):
    def __init__(self) -> None:
        self._url = ""

    @property
    def _method(self) -> str:
        return "put"

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, new_url: str) -> None:
        self._url = new_url

    def get_url(self) -> str:
        return self._url

    def get_method(self) -> str:
        return self._method

    @abstractmethod
    def process_response(self, json_obj: Dict[str, Any]) -> None:
        return True


class InfoCommandBase(CommandBase):
    def __init__(self) -> None:
        super(InfoCommandBase, self).__init__()

    @property
    def _method(self) -> str:
        return "get"

    @property
    def url(self) -> str:
        return CommandBase.url.fget(self)

    @url.setter
    def url(self, new_url: str) -> None:
        CommandBase.url.fset(self, new_url)

    def process_response(self, json_obj: Dict[str, Any]) -> bool:
        return None
