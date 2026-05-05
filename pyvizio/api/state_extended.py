"""Aggregate state snapshot from ``GET /state_extended``.

Bulk poll alternative to issuing five individual GETs against power
mode, current input, current app, screen mode, and media state.
Returns a single response with all of the above in a flat-keyed
envelope (no ``STATUS``/``ITEMS`` wrapper, unlike every other SCPL
endpoint).

Capability is advertised by the device under
``deviceinfo.scpl_capabilities.state_extended``. Older firmware that
doesn't expose it returns ``URI_NOT_FOUND`` from
:meth:`pyvizio.VizioAsync.get_state_extended`, which surfaces as
:class:`pyvizio.errors.VizioNotFoundError`.

Verified live on VHD24M-0810 firmware 3.720.9.1-1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pyvizio.api.base import InfoCommandBase
from pyvizio.const import DEVICE_CONFIGS
from pyvizio.helpers import dict_get_case_insensitive


@dataclass
class StateExtended:
    """Typed view of the ``/state_extended`` payload.

    All fields are best-effort: missing values from older or partial
    firmware degrade to empty string / ``None`` / empty tuple rather
    than raising. This lets a polling integration consume one snapshot
    per loop iteration regardless of which fields the device chose
    to populate.
    """

    power_on: bool = False
    """Derived from ``POWER_STATUS.VALUE`` (``1 = on, 0 = off``)."""

    power_mode: str = ""
    """Human-readable mode such as ``"On"``, ``"Active Off"``,
    ``"Quick Start"``."""

    current_input: str = ""
    """Meta-name of the active input. For consistency with
    :meth:`pyvizio.VizioAsync.get_current_input`, this is the same
    value the device returns for ``current_input`` — which can be
    the cname-derived display name OR the meta_name depending on
    input type (verified live: cast inputs return the meta_name
    ``"SMARTCAST"`` while HDMI inputs return the display name
    ``"HDMI-2"`` even when user-renamed)."""

    current_input_hashval: int | None = None
    """Hashval of the current_input setting — useful for callers that
    want to write back without an additional GET."""

    current_app: dict[str, Any] | None = None
    """Active SmartCast app config as ``{"app_id", "name_space",
    "message"}``, or ``None`` when no app is running. For the
    SmartCast Home screen this is populated with
    ``{"app_id": "1", "name_space": 4, ...}``."""

    screen_mode: str = ""
    """e.g. ``"Full screen"``, ``"PIP"``."""

    media_state: str = ""
    """e.g. ``"MediaState::Stopped"``, ``"MediaState::Playing"``.
    Vizio uses C++-style namespace prefixes — caller usually wants
    ``.split("::", 1)[1]``."""

    device_name: str = ""
    """User-set TV name (e.g. ``"Living Room TV"``)."""

    errors: tuple[str, ...] = ()
    """Per-field errors reported alongside the snapshot. Empty in the
    common case."""

    raw: dict[str, Any] = field(default_factory=dict)
    """Original parsed JSON payload. Escape hatch for fields we don't
    model (firmware-specific extensions)."""


def parse_state_extended(payload: dict[str, Any]) -> StateExtended:
    """Parse the ``/state_extended`` envelope into a :class:`StateExtended`.

    The on-the-wire payload uses flat top-level keys
    (``POWER_MODE``, ``APP_CURRENT``, ``CURRENT_INPUT``, ...) with no
    ``STATUS``/``ITEMS`` wrapper. We're tolerant of missing fields:
    older or partial firmware degrades each field gracefully rather
    than raising.
    """
    power_status = dict_get_case_insensitive(payload, "power_status")
    power_on = False
    if isinstance(power_status, dict):
        power_on = bool(dict_get_case_insensitive(power_status, "value", 0))

    power_mode_raw = dict_get_case_insensitive(payload, "power_mode")
    power_mode = ""
    if isinstance(power_mode_raw, dict):
        power_mode = str(dict_get_case_insensitive(power_mode_raw, "value", ""))

    current_input_raw = dict_get_case_insensitive(payload, "current_input")
    current_input = ""
    current_input_hashval: int | None = None
    if isinstance(current_input_raw, dict):
        current_input = str(dict_get_case_insensitive(current_input_raw, "name", ""))
        hv = dict_get_case_insensitive(current_input_raw, "hashval")
        try:
            current_input_hashval = int(hv) if hv is not None else None
        except (TypeError, ValueError):
            current_input_hashval = None

    app_current_raw = dict_get_case_insensitive(payload, "app_current")
    current_app: dict[str, Any] | None = None
    if isinstance(app_current_raw, dict):
        app_id = dict_get_case_insensitive(app_current_raw, "app_id")
        name_space = dict_get_case_insensitive(app_current_raw, "name_space")
        if app_id is not None and name_space is not None:
            try:
                current_app = {
                    "app_id": str(app_id),
                    "name_space": int(name_space),
                    "message": (
                        str(dict_get_case_insensitive(app_current_raw, "message"))
                        if dict_get_case_insensitive(app_current_raw, "message")
                        is not None
                        else None
                    ),
                }
            except (TypeError, ValueError):
                current_app = None

    errors_raw = dict_get_case_insensitive(payload, "errors")
    errors: tuple[str, ...] = ()
    if isinstance(errors_raw, list):
        errors = tuple(str(e) for e in errors_raw)

    return StateExtended(
        power_on=power_on,
        power_mode=power_mode,
        current_input=current_input,
        current_input_hashval=current_input_hashval,
        current_app=current_app,
        screen_mode=str(dict_get_case_insensitive(payload, "screen_mode", "")),
        media_state=str(dict_get_case_insensitive(payload, "media_state", "")),
        device_name=str(dict_get_case_insensitive(payload, "device_name", "")),
        errors=errors,
        raw=dict(payload),
    )


class GetStateExtendedCommand(InfoCommandBase):
    """Command to GET ``/state_extended`` and parse into :class:`StateExtended`.

    Note: the response has a non-standard envelope (no STATUS/ITEMS),
    so callers must invoke this command with ``skip_envelope=True``
    against :func:`pyvizio.api._protocol.async_invoke_api_auth`.
    """

    def __init__(self, device_type: str) -> None:
        """Initialize state_extended GET command."""
        super().__init__(DEVICE_CONFIGS[device_type].endpoints["STATE_EXTENDED"])

    def process_response(self, json_obj: dict[str, Any]) -> StateExtended:
        """Parse the raw payload into a typed snapshot."""
        return parse_state_extended(json_obj)
