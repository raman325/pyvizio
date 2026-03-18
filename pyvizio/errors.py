"""pyvizio exception hierarchy."""

from __future__ import annotations


class VizioError(Exception):
    """Base exception for pyvizio."""


class VizioConnectionError(VizioError):
    """Device is unreachable or connection failed."""


class VizioAuthError(VizioError):
    """Authentication failed or auth token is missing/invalid."""


class VizioInvalidParameterError(VizioError):
    """Invalid parameter value was specified."""


class VizioResponseError(VizioError):
    """Unexpected or malformed response from device."""
