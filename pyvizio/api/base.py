"""Vizio SmartCast API base commands."""

from abc import abstractmethod
from typing import Any, Dict


class CommandBase(object):
    """Base command to send data to Vizio device."""

    def __init__(self, url: str = "") -> None:
        """Initialize base command to send data to Vizio device."""
        self._url = url

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__

    @property
    def _method(self) -> str:
        """Get command method."""
        return "put"

    @property
    def url(self) -> str:
        """Get endpoint for command."""
        return self._url

    @url.setter
    def url(self, new_url: str) -> None:
        """Set endpoint for command."""
        self._url = new_url

    def get_url(self) -> str:
        """Get endpoint for command."""
        return self._url

    def get_method(self) -> str:
        return self._method

    @abstractmethod
    def process_response(self, json_obj: Dict[str, Any]) -> None:
        """Always return True when there is no custom process_response method for subclass."""
        return True


class InfoCommandBase(CommandBase):
    """Base command to get data from Vizio device."""

    def __init__(self, url: str = "") -> None:
        """Initialize base command to get data from Vizio device."""
        super(InfoCommandBase, self).__init__(url)

    @property
    def _method(self) -> str:
        """Get command method."""
        return "get"

    @property
    def url(self) -> str:
        """Get endpoint for command."""
        return CommandBase.url.fget(self)

    @url.setter
    def url(self, new_url: str) -> None:
        """Set endpoint for command."""
        CommandBase.url.fset(self, new_url)

    def process_response(self, json_obj: Dict[str, Any]) -> None:
        """Always return None when there is no custom process_response method for subclass."""
        return None
