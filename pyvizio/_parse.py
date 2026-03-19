"""Response parsing functions for Vizio SmartCast API responses.

Standalone functions replacing the 25+ command process_response methods
from the old api/ package. All parsing uses case-insensitive key lookups
since SmartCast responses have inconsistent casing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict

from pyvizio.errors import VizioNotFoundError

# SmartCast type constants
TYPE_SLIDER = "t_value_abs_v1"
TYPE_LIST = "t_list_v1"
TYPE_VALUE = "t_value_v1"
TYPE_MENU = "t_menu_v1"
TYPE_X_LIST = "t_list_x_v1"


class ParsedItem(TypedDict, total=False):
    """Normalized representation of a SmartCast response item."""

    cname: str
    type: str
    value: Any
    hashval: int | None
    name: str
    min: int | None
    max: int | None
    center: int | None
    choices: list[str]


@dataclass(frozen=True)
class InputInfo:
    """A device input."""

    name: str
    meta_name: str


@dataclass(frozen=True)
class SettingInfo:
    """A device setting with metadata for write-back optimization."""

    name: str
    value: int | str
    hashval: int
    setting_type: str
    min: int | None = None
    max: int | None = None
    choices: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PairStartResult:
    """Result of beginning the pairing process."""

    challenge_type: int
    token: int


def _ci_get(d: dict[str, Any], key: str, default: Any = None) -> Any:
    """Case-insensitive dict get."""
    lowered = {k.lower(): v for k, v in d.items()}
    return lowered.get(key.lower(), default)


def _parse_raw_item(raw: dict[str, Any]) -> ParsedItem:
    """Parse a single raw item dict into a ParsedItem."""
    hashval_raw = _ci_get(raw, "hashval")
    min_raw = _ci_get(raw, "minimum")
    max_raw = _ci_get(raw, "maximum")
    center_raw = _ci_get(raw, "center")

    return ParsedItem(
        cname=_ci_get(raw, "cname", ""),
        type=_ci_get(raw, "type", ""),
        value=_ci_get(raw, "value"),
        hashval=int(hashval_raw) if hashval_raw is not None else None,
        name=_ci_get(raw, "name", ""),
        min=int(min_raw) if min_raw is not None else None,
        max=int(max_raw) if max_raw is not None else None,
        center=int(center_raw) if center_raw is not None else None,
        choices=_ci_get(raw, "elements", []),
    )


# Sentinel for distinguishing "no default" from None
_SENTINEL = object()


def parse_all_items(data: dict[str, Any]) -> list[ParsedItem]:
    """Parse all ITEMS from a response into ParsedItem list."""
    raw_items = _ci_get(data, "items", [])
    return [_parse_raw_item(item) for item in raw_items]


def parse_item_by_cname(
    data: dict[str, Any],
    cname: str,
    *,
    cname_aliases: dict[str, str] | None = None,
    default_value: Any = _SENTINEL,
) -> ParsedItem:
    """Find item matching cname. Raises VizioNotFoundError if missing.

    If cname_aliases is provided, also matches against alias values.
    If default_value is provided, returns a synthetic item instead of raising.
    """
    items = parse_all_items(data)
    target = cname.lower()
    alias = (cname_aliases or {}).get(cname.upper(), "").lower()

    for item in items:
        item_cname = (item.get("cname") or "").lower()
        if item_cname in (target, alias) and (
            item.get("value") is not None
            or item.get("center") is not None
            or item.get("choices") is not None
        ):
            return item

    if default_value is not _SENTINEL:
        return ParsedItem(
            cname=cname,
            type="",
            value=default_value,
            hashval=None,
            name=cname,
            min=None,
            max=None,
            center=None,
            choices=[],
        )

    raise VizioNotFoundError(f"Item '{cname}' not found in response")


def parse_settings(data: dict[str, Any]) -> dict[str, int | str]:
    """Parse settings response into {name: value} dict.

    Only includes items of type slider, list, or value (not menus).
    """
    items = parse_all_items(data)
    result: dict[str, int | str] = {}
    for item in items:
        item_type = (item.get("type") or "").lower()
        if item_type in (TYPE_LIST, TYPE_SLIDER, TYPE_VALUE):
            result[item["cname"]] = item["value"]
    return result


def parse_settings_options(
    data: dict[str, Any],
) -> dict[str, list[str] | dict[str, int | None]]:
    """Parse settings options into {name: options} dict.

    For slider/value types: returns {"min": int, "max": int, "default": int|None}
    For list types: returns list of choice strings
    """
    items = parse_all_items(data)
    result: dict[str, list[str] | dict[str, int | None]] = {}
    for item in items:
        item_type = (item.get("type") or "").lower()
        if item_type in (TYPE_SLIDER, TYPE_VALUE):
            d: dict[str, int | None] = {"min": item.get("min"), "max": item.get("max")}
            if item.get("center") is not None:
                d["default"] = item.get("center")
            result[item["cname"]] = d
        elif item_type == TYPE_LIST:
            result[item["cname"]] = list(item.get("choices") or [])
    return result


def parse_settings_options_xlist(data: dict[str, Any]) -> dict[str, list[str]]:
    """Parse settings options for XList type settings."""
    items = parse_all_items(data)
    return {
        item["cname"]: list(item.get("choices") or [])
        for item in items
        if item.get("type") and item["type"].lower() == TYPE_X_LIST
    }


def parse_setting_types(data: dict[str, Any]) -> list[str]:
    """Extract setting type names, filtering non-setting menus."""
    items = parse_all_items(data)
    excluded = {"cast", "input", "devices", "network"}
    return [
        item["cname"]
        for item in items
        if (item.get("type") or "").lower() == TYPE_MENU
        and item["cname"] not in excluded
    ]


def parse_inputs(data: dict[str, Any]) -> list[InputInfo]:
    """Parse input list into InputInfo dataclasses."""
    raw_items = _ci_get(data, "items")
    if not raw_items:
        return []

    result = []
    for raw in raw_items:
        cname = _ci_get(raw, "cname", "")
        if cname == "current_input":
            continue

        meta = _ci_get(raw, "value")
        if isinstance(meta, dict):
            meta_name = _ci_get(meta, "name") or cname
        elif meta:
            meta_name = meta
        else:
            meta_name = cname

        result.append(InputInfo(name=cname, meta_name=meta_name))
    return result


def parse_current_input(data: dict[str, Any]) -> str | None:
    """Parse current input response, returning the meta_name."""
    raw_items = _ci_get(data, "items")
    if not raw_items:
        return None
    raw = raw_items[0]
    meta = _ci_get(raw, "value")
    if isinstance(meta, dict):
        return _ci_get(meta, "name")
    return meta


def parse_current_input_item(data: dict[str, Any]) -> ParsedItem | None:
    """Parse current input response into a full ParsedItem (for set_input hashval)."""
    raw_items = _ci_get(data, "items")
    if not raw_items:
        return None
    return _parse_raw_item(raw_items[0])


def parse_device_info(data: dict[str, Any]) -> dict[str, Any]:
    """Parse device info response."""
    items = _ci_get(data, "items", [{}])
    return items[0] if items else {}


def parse_model_name(data: dict[str, Any], paths: list[list[str]]) -> str | None:
    """Parse model name from device info response."""
    info = parse_device_info(data)
    value = _ci_get(info, "value", {})
    for path in paths:
        temp: Any = value
        for step in path:
            if isinstance(temp, dict):
                temp = _ci_get(temp, step, {})
            else:
                temp = {}
                break
        if temp and temp != {}:
            return temp
    return None


def parse_pair_start(data: dict[str, Any]) -> PairStartResult:
    """Parse begin-pair response."""
    item = _ci_get(data, "item", {})
    return PairStartResult(
        challenge_type=_ci_get(item, "challenge_type"),
        token=_ci_get(item, "pairing_req_token"),
    )


def parse_pair_finish(data: dict[str, Any]) -> str:
    """Parse pair-finish response, returning auth token."""
    item = _ci_get(data, "item", {})
    return _ci_get(item, "auth_token")


def parse_current_app_config(data: dict[str, Any]) -> dict[str, Any] | None:
    """Parse current app config from response. Returns None if no app running."""
    item = _ci_get(data, "item", {})
    return _ci_get(item, "value")
