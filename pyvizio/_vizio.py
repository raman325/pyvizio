"""Vizio SmartCast device control — the public API.

New internals: SmartCastClient for HTTP, standalone parsing functions.
Backward-compat shims: old constructor signature, old method names,
log_api_exception support, True/None returns.
"""

from __future__ import annotations

import asyncio
from asyncio import sleep
from collections.abc import KeysView
from datetime import datetime, timedelta
import logging
from typing import Any

from aiohttp import ClientSession

from pyvizio._client import SmartCastClient
from pyvizio._parse import (
    _ci_get,
    parse_current_app_config,
    parse_current_input,
    parse_current_input_item,
    parse_item_by_cname,
    parse_model_name,
    parse_pair_finish,
    parse_pair_start,
    parse_setting_types,
    parse_settings,
    parse_settings_options,
    parse_settings_options_xlist,
)
from pyvizio.apps import AppConfig, find_app_name, gen_apps_list_from_url
from pyvizio.const import (
    APP_HOME,
    APPS,
    DEFAULT_DEVICE_CLASS,
    DEFAULT_DEVICE_ID,
    DEFAULT_DEVICE_NAME,
    DEFAULT_PORTS,
    DEFAULT_TIMEOUT,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
    DEVICE_CONFIGS,
)
from pyvizio.errors import VizioAuthError, VizioError, VizioInvalidParameterError
from pyvizio.helpers import open_port

_LOGGER = logging.getLogger(__name__)

# cname aliases used by the SmartCast API
ITEM_CNAME = {
    "CURRENT_INPUT": "current_input",
    "ESN": "esn",
    "EQ": "eq",
    "POWER_MODE": "power_mode",
    "CHARGING_STATUS": "charging_status",
    "BATTERY_LEVEL": "battery_level",
    "SERIAL_NUMBER": "serial_number",
    "VERSION": "version",
}

# Model name paths differ by device type
PATH_MODEL = {
    DEVICE_CLASS_SPEAKER: [["name"]],
    DEVICE_CLASS_TV: [["model_name"], ["system_info", "model_name"]],
}

# Key action constants
KEY_ACTION_PRESS = "KEYPRESS"

# Key codes derived from DEVICE_CONFIGS
KEY_CODE = {k: v.key_codes for k, v in DEVICE_CONFIGS.items()}


class _KeyPressEvent:
    """Single key press for remote command body."""

    def __init__(self, key_code: tuple[int, int]) -> None:
        self.CODESET: int = key_code[0]
        self.CODE: int = key_code[1]
        self.ACTION: str = KEY_ACTION_PRESS


class VizioAsync:
    """Asynchronous class to interact with Vizio SmartCast devices.

    Backward-compatible constructor accepts the old positional args:
        VizioAsync(device_id, ip, name, auth_token, device_type)
    """

    def __init__(
        self,
        device_id: str = DEFAULT_DEVICE_ID,
        ip: str = "",
        name: str = DEFAULT_DEVICE_NAME,
        auth_token: str | None = "",
        device_type: str = DEFAULT_DEVICE_CLASS,
        session: ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_concurrent_requests: int = 1,
    ) -> None:
        """Initialize asynchronous class to interact with Vizio SmartCast devices."""
        self.device_type = device_type.lower()
        if self.device_type not in DEVICE_CONFIGS:
            raise VizioInvalidParameterError(
                f"Invalid device type specified. Use one of: "
                f"{', '.join(repr(k) for k in DEVICE_CONFIGS)}"
            )
        self._device_config = DEVICE_CONFIGS[self.device_type]

        self._auth_token = auth_token
        self.ip = ip
        self.name = name
        self.device_id = device_id
        self._session = session
        self._timeout = timeout
        if max_concurrent_requests < 1:
            raise VizioInvalidParameterError("max_concurrent_requests must be >= 1")
        self._max_concurrent_requests = max_concurrent_requests
        self._semaphore: asyncio.Semaphore | None = None
        self._latest_apps: list[dict[str, Any]] | None = None
        self._latest_apps_last_updated: datetime | None = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, VizioAsync):
            return NotImplemented
        exclude = {"_semaphore", "_max_concurrent_requests"}
        self_d = {k: v for k, v in self.__dict__.items() if k not in exclude}
        other_d = {k: v for k, v in other.__dict__.items() if k not in exclude}
        return self_d == other_d

    # ---- Internal client helpers ----

    def _make_client(self, *, with_auth: bool = False) -> SmartCastClient:
        """Create a SmartCastClient configured for this device."""
        return SmartCastClient(
            host=self.ip,
            auth_token=self._auth_token if with_auth else None,
            timeout=self._timeout,
            session=self._session,
            max_concurrent=self._max_concurrent_requests,
        )

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Lazily create semaphore."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrent_requests)
        return self._semaphore

    async def _ensure_port(self) -> None:
        """Add first open port from known ports list if not already specified."""
        if ":" not in self.ip:
            for port in DEFAULT_PORTS:
                if await open_port(self.ip, port):
                    self.ip = f"{self.ip}:{port}"
                    return

    async def _get(self, path: str) -> dict[str, Any]:
        """GET with semaphore, port resolution, and appropriate auth."""
        async with self._get_semaphore():
            await self._ensure_port()
            client = self._make_client(with_auth=bool(self._auth_token))
            return await client.get(path)

    async def _put(
        self, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """PUT with semaphore, port resolution, and appropriate auth."""
        async with self._get_semaphore():
            await self._ensure_port()
            client = self._make_client(with_auth=bool(self._auth_token))
            return await client.put(path, body)

    async def _get_no_auth(self, path: str) -> dict[str, Any]:
        """GET without auth (for serial number, device info, etc.)."""
        async with self._get_semaphore():
            await self._ensure_port()
            client = self._make_client(with_auth=False)
            return await client.get(path)

    async def _put_no_auth(
        self, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """PUT without auth."""
        async with self._get_semaphore():
            await self._ensure_port()
            client = self._make_client(with_auth=False)
            return await client.put(path, body)

    def _check_auth(self) -> None:
        """Raise VizioAuthError if auth is required but missing."""
        if not self._auth_token and self._device_config.requires_auth:
            no_auth_types = [
                k for k, v in DEVICE_CONFIGS.items() if not v.requires_auth
            ]
            raise VizioAuthError(
                f"Empty auth token. Device types that don't require auth: "
                f"{', '.join(repr(t) for t in no_auth_types)}"
            )

    async def _get_may_need_auth(self, path: str) -> dict[str, Any]:
        """GET that checks auth requirement before calling."""
        self._check_auth()
        return await self._get(path)

    async def _put_may_need_auth(
        self, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """PUT that checks auth requirement before calling."""
        self._check_auth()
        return await self._put(path, body)

    def _endpoint(self, key: str) -> str:
        """Get endpoint path for this device type."""
        return self._device_config.endpoints[key]

    # ---- Compat error handling ----

    def _handle_error(self, exc: VizioError, kwargs: dict[str, Any]) -> Any:
        """Handle error for compat methods: log + return None.

        VizioAuthError always propagates (matches old behavior where auth
        check happened before the try/except in async_invoke_api).
        """
        if isinstance(exc, VizioAuthError):
            raise
        log = kwargs.get("log_api_exception", True)
        if log:
            _LOGGER.error("Failed to execute command: %s", exc)
        return None

    # ---- Key press internals ----

    def _build_key_body(self, key_codes: list[tuple[int, int]]) -> dict[str, Any]:
        """Build key press request body."""
        keylist = []
        for kc in key_codes:
            keylist.append(
                {"CODESET": kc[0], "CODE": kc[1], "ACTION": KEY_ACTION_PRESS}
            )
        return {"KEYLIST": keylist}

    async def _remote_key_internal(self, key_list: str | list[str], **kwargs) -> bool:
        """Execute remote key press. Returns True on success, False if key not found."""
        if not isinstance(key_list, list):
            key_list = [key_list]

        key_codes = []
        for key in key_list:
            if key not in KEY_CODE[self.device_type]:
                _LOGGER.error(
                    "Key Code of '%s' not found for device type of '%s'",
                    key,
                    self.device_type,
                )
                return False
            key_codes.append(KEY_CODE[self.device_type][key])

        body = self._build_key_body(key_codes)
        await self._put_may_need_auth(self._endpoint("KEY_PRESS"), body)
        return True

    async def _remote_multiple(self, key_code: str, num: int, **kwargs) -> bool:
        """Execute key press repeated multiple times."""
        key_list = [key_code for _ in range(num)]
        return await self._remote_key_internal(key_list, **kwargs)

    # ---- Cached apps list ----

    async def _get_cached_apps_list(self) -> list[dict[str, Any]]:
        if (
            self._latest_apps
            and self._latest_apps_last_updated is not None
            and datetime.now() - self._latest_apps_last_updated < timedelta(days=1)
        ):
            await sleep(0)
            return self._latest_apps
        else:
            result: list[dict[str, Any]] = (
                await gen_apps_list_from_url(session=self._session) or APPS
            )
            self._latest_apps = result
            self._latest_apps_last_updated = datetime.now()
            return self._latest_apps

    # ---- Port resolution / connect ----

    async def connect(self) -> None:
        """Eagerly resolve port if not already specified."""
        if ":" not in self.ip:
            await self._ensure_port()

    # ================================================================
    # PUBLIC API — new clean methods (exceptions, no None returns)
    # with backward-compat wrappers below
    # ================================================================

    # ---- Power ----

    async def get_power_state(self, **kwargs) -> bool | None:
        """Get device's current power state."""
        try:
            self._check_auth()
            data = await self._get(self._endpoint("POWER_MODE"))
            item = parse_item_by_cname(
                data,
                "power_mode",
                cname_aliases=ITEM_CNAME,
                default_value=0,
            )
            return bool(item["value"])
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def pow_on(self, **kwargs) -> bool | None:
        """Power device on."""
        try:
            result = await self._remote_key_internal("POW_ON", **kwargs)
            return result if result else None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def pow_off(self, **kwargs) -> bool | None:
        """Power device off."""
        try:
            result = await self._remote_key_internal("POW_OFF", **kwargs)
            return result if result else None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def pow_toggle(self, **kwargs) -> bool | None:
        """Toggle device power."""
        try:
            result = await self._remote_key_internal("POW_TOGGLE", **kwargs)
            return result if result else None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    # ---- Volume ----

    async def get_current_volume(self, **kwargs) -> int | None:
        """Get device's current volume level."""
        try:
            volume = await VizioAsync.get_audio_setting(self, "volume", **kwargs)
            return int(volume) if volume else None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def vol_up(self, num: int = 1, **kwargs) -> bool | None:
        """Increase volume by number of steps."""
        try:
            return await self._remote_multiple("VOL_UP", num, **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def vol_down(self, num: int = 1, **kwargs) -> bool | None:
        """Decrease volume by number of steps."""
        try:
            return await self._remote_multiple("VOL_DOWN", num, **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def is_muted(self, **kwargs) -> bool | None:
        """Determine whether or not device is muted."""
        try:
            mute_val = await VizioAsync.get_audio_setting(self, "mute", **kwargs)
            return str(mute_val).lower() == "on" if mute_val is not None else None
        except (VizioError, AttributeError):
            return None

    def get_max_volume(self) -> int:
        """Get device's max volume based on device type."""
        return self._device_config.max_volume

    # ---- Mute ----

    async def mute_on(self, **kwargs) -> bool | None:
        """Mute sound."""
        try:
            return await self._remote_key_internal("MUTE_ON", **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def mute_off(self, **kwargs) -> bool | None:
        """Unmute sound."""
        try:
            return await self._remote_key_internal("MUTE_OFF", **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def mute_toggle(self, **kwargs) -> bool | None:
        """Toggle sound mute."""
        try:
            return await self._remote_key_internal("MUTE_TOGGLE", **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    # ---- Channel ----

    async def ch_up(self, num: int = 1, **kwargs) -> bool | None:
        """Channel up by number of steps."""
        try:
            return await self._remote_multiple("CH_UP", num, **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def ch_down(self, num: int = 1, **kwargs) -> bool | None:
        """Channel down by number of steps."""
        try:
            return await self._remote_multiple("CH_DOWN", num, **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def ch_prev(self, **kwargs) -> bool | None:
        """Go to previous channel."""
        try:
            return await self._remote_key_internal("CH_PREV", **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    # ---- Media ----

    async def play(self, **kwargs) -> bool | None:
        """Emulate 'play' key press."""
        try:
            return await self._remote_key_internal("PLAY", **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def pause(self, **kwargs) -> bool | None:
        """Emulate 'pause' key press."""
        try:
            return await self._remote_key_internal("PAUSE", **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    # ---- Remote ----

    async def remote(self, key: str, **kwargs) -> bool | None:
        """Emulate key press by key name. Returns False for invalid keys."""
        try:
            return await self._remote_key_internal(key, **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    def get_remote_keys_list(self) -> KeysView[str]:
        """Get list of remote key names."""
        return KEY_CODE[self.device_type].keys()

    # ---- Input ----

    async def get_inputs_list(self, **kwargs) -> list | None:
        """Get list of available inputs."""
        try:
            self._check_auth()
            data = await self._get(self._endpoint("INPUTS"))
            # Return InputItem-compatible objects for backward compat
            raw_items = _ci_get(data, "items")
            if not raw_items:
                return None

            from pyvizio.api.input import InputItem

            result = []
            for raw in raw_items:
                cname = _ci_get(raw, "cname", "")
                if cname == "current_input":
                    continue
                result.append(InputItem(raw, True))
            return result if result else None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_current_input(self, **kwargs) -> str | None:
        """Get device's active input."""
        try:
            self._check_auth()
            data = await self._get(self._endpoint("CURRENT_INPUT"))
            return parse_current_input(data)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def next_input(self, **kwargs) -> bool | None:
        """Switch active input to next input."""
        try:
            return await self._remote_multiple("INPUT_NEXT", 2, **kwargs)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def set_input(self, name: str, **kwargs) -> bool | None:
        """Switch active input to named input."""
        try:
            self._check_auth()
            data = await self._get(self._endpoint("CURRENT_INPUT"))
            item = parse_current_input_item(data)

            if not item:
                _LOGGER.error("Couldn't detect current input")
                return None

            hashval = item.get("hashval", 0)
            body = {
                "VALUE": name,
                "HASHVAL": int(hashval) if hashval is not None else 0,
                "REQUEST": "MODIFY",
            }
            await self._put_may_need_auth(self._endpoint("CURRENT_INPUT"), body)
            return True
        except VizioError as e:
            return self._handle_error(e, kwargs)

    # ---- Device Info ----

    async def get_esn(self, **kwargs) -> str | None:
        """Get device's ESN (electronic serial number)."""
        try:
            self._check_auth()
            try:
                data = await self._get(self._endpoint("ESN"))
                item = parse_item_by_cname(data, "esn", cname_aliases=ITEM_CNAME)
                if item and item.get("value"):
                    return item["value"]
            except VizioError:
                if kwargs.get("log_api_exception", True):
                    pass  # Fall through to alt endpoint
                pass

            data = await self._get(self._endpoint("_ALT_ESN"))
            item = parse_item_by_cname(data, "esn", cname_aliases=ITEM_CNAME)
            if item and item.get("value"):
                return item["value"]
            return None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_serial_number(self, **kwargs) -> str | None:
        """Get device's serial number."""
        try:
            try:
                data = await self._get_no_auth(self._endpoint("SERIAL_NUMBER"))
                item = parse_item_by_cname(
                    data, "serial_number", cname_aliases=ITEM_CNAME
                )
                if item and item.get("value"):
                    return item["value"]
            except VizioError:
                pass

            data = await self._get_no_auth(self._endpoint("_ALT_SERIAL_NUMBER"))
            item = parse_item_by_cname(data, "serial_number", cname_aliases=ITEM_CNAME)
            if item and item.get("value"):
                return item["value"]
            return None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_version(self, **kwargs) -> str | None:
        """Get SmartCast software version on device."""
        try:
            try:
                data = await self._get_no_auth(self._endpoint("VERSION"))
                item = parse_item_by_cname(data, "version", cname_aliases=ITEM_CNAME)
                if item and item.get("value"):
                    return item["value"]
            except VizioError:
                pass

            data = await self._get_no_auth(self._endpoint("_ALT_VERSION"))
            item = parse_item_by_cname(data, "version", cname_aliases=ITEM_CNAME)
            if item and item.get("value"):
                return item["value"]
            return None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_model_name(self, **kwargs) -> str | None:
        """Get device's model number."""
        try:
            data = await self._get_no_auth(self._endpoint("DEVICE_INFO"))
            return parse_model_name(
                data, PATH_MODEL.get(self.device_type, [["model_name"]])
            )
        except VizioError as e:
            return self._handle_error(e, kwargs)

    # ---- Charging / Battery (Crave360) ----

    async def get_charging_status(self, **kwargs) -> int | None:
        """Get device's current charging state."""
        try:
            self._check_auth()
            data = await self._get(self._endpoint("CHARGING_STATUS"))
            item = parse_item_by_cname(
                data,
                "charging_status",
                cname_aliases=ITEM_CNAME,
                default_value=0,
            )
            return int(item["value"])
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_battery_level(self, **kwargs) -> int | None:
        """Get device's current battery level (will be 0 if charging)."""
        try:
            self._check_auth()
            data = await self._get(self._endpoint("BATTERY_LEVEL"))
            item = parse_item_by_cname(
                data,
                "battery_level",
                cname_aliases=ITEM_CNAME,
                default_value=0,
            )
            return int(item["value"])
        except VizioError as e:
            return self._handle_error(e, kwargs)

    # ---- Pairing ----

    async def start_pair(self, **kwargs) -> Any:
        """Begin pairing process to obtain challenge type and challenge token."""
        try:
            body = {
                "DEVICE_ID": self.device_id,
                "DEVICE_NAME": str(self.name),
            }
            data = await self._put_no_auth(self._endpoint("BEGIN_PAIR"), body)
            result = parse_pair_start(data)

            # Return as BeginPairResponse for backward compat
            from pyvizio.api.pair import BeginPairResponse

            return BeginPairResponse(result.challenge_type, result.token)  # type: ignore[arg-type]
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def stop_pair(self, **kwargs) -> bool | None:
        """Cancel pairing process."""
        try:
            body = {
                "DEVICE_ID": self.device_id,
                "DEVICE_NAME": str(self.name),
            }
            await self._put_no_auth(self._endpoint("CANCEL_PAIR"), body)
            return True
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def pair(
        self,
        ch_type: int | str,
        token: int | str,
        pin: str = "",
        **kwargs,
    ) -> Any:
        """Complete pairing process to obtain auth token."""
        try:
            if self.device_type == DEVICE_CLASS_SPEAKER:
                pin = "0000"
            body = {
                "DEVICE_ID": self.device_id,
                "CHALLENGE_TYPE": int(ch_type),
                "PAIRING_REQ_TOKEN": int(token),
                "RESPONSE_VALUE": str(pin),
            }
            data = await self._put_no_auth(self._endpoint("FINISH_PAIR"), body)
            auth_token = parse_pair_finish(data)

            # Return as PairChallengeResponse for backward compat
            from pyvizio.api.pair import PairChallengeResponse

            return PairChallengeResponse(auth_token)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    # ---- Settings ----

    async def get_setting_types_list(self, **kwargs) -> list[str] | None:
        """Get list of all setting types."""
        try:
            self._check_auth()
            data = await self._get(self._endpoint("SETTINGS"))
            result = parse_setting_types(data)
            return result if result else None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_all_settings(
        self, setting_type: str, **kwargs
    ) -> dict[str, int | str] | None:
        """Get all setting names and corresponding values."""
        try:
            self._check_auth()
            path = f"{self._endpoint('SETTINGS')}/{setting_type}"
            data = await self._get(path)
            result = parse_settings(data)
            return result if result else None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_all_settings_options(
        self, setting_type: str, **kwargs
    ) -> dict[str, list[str] | dict[str, int | None]] | None:
        """Get all setting names and corresponding options."""
        try:
            self._check_auth()
            path = f"{self._endpoint('SETTINGS_OPTIONS')}/{setting_type}"
            data = await self._get(path)
            result = parse_settings_options(data)
            return result if result else None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_all_settings_options_xlist(
        self, setting_type: str, **kwargs
    ) -> dict[str, list[str]] | None:
        """Get all setting names and corresponding options for XList settings."""
        try:
            self._check_auth()
            path = f"{self._endpoint('SETTINGS')}/{setting_type}"
            data = await self._get(path)
            result = parse_settings_options_xlist(data)
            return result if result else None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_setting(
        self, setting_type: str, setting_name: str, **kwargs
    ) -> int | str | None:
        """Get current value of named setting."""
        try:
            self._check_auth()
            path = f"{self._endpoint('SETTINGS')}/{setting_type}/{setting_name}"
            data = await self._get(path)
            item = parse_item_by_cname(
                data,
                setting_name.lower(),
                cname_aliases=ITEM_CNAME,
                default_value=0,
            )
            if item:
                try:
                    return int(item["value"])
                except (ValueError, TypeError):
                    return item["value"]
            return None
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_setting_options(
        self, setting_type: str, setting_name: str, **kwargs
    ) -> list[str] | dict[str, int | None] | None:
        """Get options of named setting."""
        try:
            self._check_auth()
            path = f"{self._endpoint('SETTINGS_OPTIONS')}/{setting_type}"
            data = await self._get(path)
            result = parse_settings_options(data)
            return result.get(setting_name)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_setting_options_xlist(
        self, setting_type: str, setting_name: str, **kwargs
    ) -> list[str] | None:
        """Get options of named setting for XList type settings."""
        try:
            self._check_auth()
            path = f"{self._endpoint('SETTINGS')}/{setting_type}"
            data = await self._get(path)
            result = parse_settings_options_xlist(data)
            return result.get(setting_name)
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def set_setting(
        self,
        setting_type: str,
        setting_name: str,
        new_value: int | str,
        **kwargs,
    ) -> bool | None:
        """Set new value for setting. Does GET+PUT (2 round trips) for hashval."""
        try:
            self._check_auth()
            get_path = f"{self._endpoint('SETTINGS')}/{setting_type}/{setting_name}"
            data = await self._get(get_path)
            item = parse_item_by_cname(
                data,
                setting_name.lower(),
                cname_aliases=ITEM_CNAME,
                default_value=0,
            )

            if not item or item.get("hashval") is None:
                _LOGGER.error(
                    "Couldn't detect setting for %s of setting type %s",
                    setting_name,
                    setting_type,
                )
                return None

            put_path = f"{self._endpoint('SETTINGS')}/{setting_type}/{setting_name}"
            body = {
                "VALUE": new_value,
                "HASHVAL": item.get("hashval", 0),
                "REQUEST": "MODIFY",
            }
            await self._put_may_need_auth(put_path, body)
            return True
        except VizioError as e:
            return self._handle_error(e, kwargs)

    # ---- Audio convenience methods (delegate to settings) ----

    async def get_all_audio_settings(self, **kwargs) -> dict[str, int | str] | None:
        """Get all audio setting names and corresponding values."""
        return await VizioAsync.get_all_settings(self, "audio", **kwargs)

    async def get_all_audio_settings_options(
        self, **kwargs
    ) -> dict[str, list[str] | dict[str, int | None]] | None:
        """Get all audio setting names and corresponding options."""
        return await VizioAsync.get_all_settings_options(self, "audio", **kwargs)

    async def get_audio_setting(self, setting_name: str, **kwargs) -> int | str | None:
        """Get current value of named audio setting."""
        return await VizioAsync.get_setting(self, "audio", setting_name, **kwargs)

    async def get_audio_setting_options(
        self, setting_name: str, **kwargs
    ) -> list[str] | dict[str, int | None] | None:
        """Get options of named audio setting."""
        return await VizioAsync.get_setting_options(
            self, "audio", setting_name, **kwargs
        )

    async def set_audio_setting(
        self,
        setting_name: str,
        new_value: int | str,
        **kwargs,
    ) -> bool | None:
        """Set new value for named audio setting."""
        return await VizioAsync.set_setting(
            self, "audio", setting_name, new_value, **kwargs
        )

    # ---- Apps ----

    @staticmethod
    async def get_apps_list(
        country: str = "all",
        apps_list: list[dict[str, Any]] | None = None,
        session: ClientSession | None = None,
    ) -> list[str]:
        """Get list of known apps by name optionally filtered by supported country."""
        if not apps_list:
            fetched: list[dict[str, Any]] = (
                await gen_apps_list_from_url(session=session) or APPS
            )
            apps_list = fetched

        home_name = str(APP_HOME["name"])
        if country.lower() != "all":
            return [
                home_name,
                *sorted(
                    [
                        str(app["name"])
                        for app in apps_list
                        if "*" in app["country"] or country.lower() in app["country"]
                    ]
                ),
            ]

        return [home_name, *sorted([str(app["name"]) for app in apps_list])]

    async def launch_app(
        self,
        app_name: str,
        apps_list: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> bool | None:
        """Launch known app by name."""
        try:
            if not apps_list:
                apps_list = await self._get_cached_apps_list()

            # Find app config
            app_def: dict[str, Any] = next(
                (
                    ad
                    for ad in [APP_HOME, *apps_list]
                    if ad["name"].lower() == app_name.lower()
                ),
                {},
            )
            config_list: list[dict[str, Any]] = app_def.get("config", [{}])
            config = config_list[0] if config_list else {}

            app_config = AppConfig(
                config.get("APP_ID"),
                config.get("NAME_SPACE"),
                config.get("MESSAGE"),
            )
            body = {
                "VALUE": {
                    "APP_ID": app_config.APP_ID,
                    "NAME_SPACE": app_config.NAME_SPACE,
                    "MESSAGE": app_config.MESSAGE,
                }
            }
            await self._put_may_need_auth(self._endpoint("LAUNCH_APP"), body)
            return True
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def launch_app_config(
        self,
        APP_ID: str,
        NAME_SPACE: int,
        MESSAGE: str | None = None,
        **kwargs,
    ) -> bool | None:
        """Launch app using app's config values."""
        try:
            body = {
                "VALUE": {
                    "APP_ID": APP_ID,
                    "NAME_SPACE": NAME_SPACE,
                    "MESSAGE": MESSAGE,
                }
            }
            await self._put_may_need_auth(self._endpoint("LAUNCH_APP"), body)
            return True
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_current_app(
        self,
        apps_list: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> str | None:
        """Get name of currently running app."""
        try:
            if not apps_list:
                apps_list = await self._get_cached_apps_list()

            self._check_auth()
            data = await self._get(self._endpoint("CURRENT_APP"))
            config_dict = parse_current_app_config(data)

            if config_dict:
                app_config = AppConfig(**config_dict)
                return find_app_name(app_config, [APP_HOME, *apps_list])

            from pyvizio.const import NO_APP_RUNNING

            return NO_APP_RUNNING
        except VizioError as e:
            return self._handle_error(e, kwargs)

    async def get_current_app_config(self, **kwargs) -> AppConfig | None:
        """Get config values of currently running app."""
        try:
            self._check_auth()
            data = await self._get(self._endpoint("CURRENT_APP"))
            config_dict = parse_current_app_config(data)
            if config_dict:
                return AppConfig(**config_dict)
            return AppConfig()
        except VizioError as e:
            return self._handle_error(e, kwargs)

    # ---- Connection checks ----

    async def can_connect_with_auth_check(self) -> bool:
        """Return whether or not device API can be connected to with valid authorization."""
        return bool(
            await VizioAsync.get_all_audio_settings(self, log_api_exception=False)
        )

    async def can_connect_no_auth_check(self) -> bool:
        """Return whether or not device API can be connected to regardless of authorization."""
        try:
            await self._get_no_auth(self._endpoint("DEVICE_INFO"))
            return True
        except VizioError:
            return False

    # ---- Discovery (static, kept for backward compat) ----

    @staticmethod
    def discovery_zeroconf(timeout: int = DEFAULT_TIMEOUT):
        """Discover Vizio devices on network using zeroconf."""
        from pyvizio.discovery.zeroconf import discover as discover_zc

        results = discover_zc("_viziocast._tcp.local.", timeout=timeout)
        _LOGGER.info(results)
        return results

    @staticmethod
    def discovery_ssdp(timeout: int = DEFAULT_TIMEOUT):
        """Discover Vizio devices on network using SSDP."""
        from urllib.parse import urlsplit

        import requests
        import xmltodict

        from pyvizio.discovery.ssdp import SSDPDevice, discover as discover_ssdp

        results = []
        devices = discover_ssdp(
            "urn:dial-multiscreen-org:device:dial:1", timeout=timeout
        )
        for dev in devices:
            data = xmltodict.parse(
                requests.get(dev.location, verify=False, timeout=timeout).text
            )
            if "root" not in data or "device" not in data["root"]:
                continue
            root = data["root"]["device"]
            manufacturer = root["manufacturer"]
            if manufacturer is None or "VIZIO" != manufacturer:
                continue
            split_url = urlsplit(dev.location)
            device = SSDPDevice(
                split_url.hostname,
                root["friendlyName"],
                root["modelName"],
                root["UDN"],
            )
            results.append(device)
        _LOGGER.info(results)
        return results

    @staticmethod
    async def validate_ha_config(
        ip: str,
        auth_token: str,
        device_type: str,
        session: ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """Return whether or not HomeAssistant config is valid."""
        return await VizioAsync(
            "", ip, "", auth_token, device_type, session=session, timeout=timeout
        ).can_connect_with_auth_check()

    @staticmethod
    async def get_unique_id(
        ip: str,
        device_type: str,
        timeout: int = DEFAULT_TIMEOUT,
        session: ClientSession | None = None,
    ) -> str | None:
        """Get unique identifier for Vizio device."""
        return await VizioAsync(
            "", ip, "", "", device_type, session=session, timeout=timeout
        ).get_serial_number(log_api_exception=False)
