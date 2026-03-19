"""Vizio SmartCast API pairing response types."""

from __future__ import annotations


class BeginPairResponse:
    """Response from command to begin pairing process."""

    def __init__(self, ch_type: str, token: str) -> None:
        """Initialize response from command to begin pairing process."""
        self.ch_type: str = ch_type
        self.token: str = token

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__


class PairChallengeResponse:
    """Response from command to complete pairing process."""

    def __init__(self, auth_token: str) -> None:
        """Initialize response from command to complete pairing process."""
        self.auth_token = auth_token

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__
