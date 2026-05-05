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


class VizioNotFoundError(VizioError):
    """Requested item not found in device response.

    Also used for ``URI_NOT_FOUND`` envelope status from the device,
    which modern firmware (~3.7+) returns for paths that aren't
    exposed (HTTP 200 + this status, not HTTP 404).
    """


class VizioBusyError(VizioError):
    """Device temporarily refused — typically returned as
    ``RESULT: BLOCKED`` envelope status. Another writer holds a lock,
    or the device is mid-update."""


class VizioInvalidInputError(VizioInvalidParameterError):
    """The named input does not exist on this device, or matches
    multiple inputs ambiguously.

    Subclass of :class:`VizioInvalidParameterError` so callers that
    catch the parent still see input-specific errors.

    Note: raised by the internal input cname resolver, but the public
    :meth:`pyvizio.VizioAsync.set_input` catches it and returns
    ``None`` per the library's ``bool | None`` convention. Use
    :func:`pyvizio._resolve_input_cname` directly if you need the
    typed signal (e.g. to surface a "did you mean X?" hint to the
    user).
    """


class VizioHashvalError(VizioInvalidParameterError):
    """Stale hashval submitted in a write — the value the caller had
    when constructing the PUT no longer matches the device's current
    hashval (someone else, or the iPhone app, modified the setting).

    Catch this subclass specifically to drive a refetch-and-retry
    loop (re-GET the parent setting to obtain the fresh hashval, then
    re-issue the PUT). ``except VizioInvalidParameterError`` continues
    to catch it via the parent for callers that want to lump all
    invalid-parameter cases together.
    """


class VizioUnsupportedError(VizioError):
    """The requested operation is not supported by this device class.

    Raised before any HTTP work when the operation is gated by device
    profile capabilities (e.g., battery on a TV, apps on a soundbar).
    """
