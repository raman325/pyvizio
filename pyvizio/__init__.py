"""Initialize pyvizio.

Re-exports from new v2 internals with full backward compatibility.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from aiohttp import ClientSession

# New v2 internals
from pyvizio._vizio import VizioAsync

# Backward-compat re-exports: old import paths still work
from pyvizio.api._protocol import KEY_CODE  # noqa: F401
from pyvizio.api.apps import AppConfig  # noqa: F401
from pyvizio.api.input import InputItem  # noqa: F401
from pyvizio.api.pair import (  # noqa: F401
    BeginPairResponse,
    PairChallengeResponse,
)
from pyvizio.apps import gen_apps_list_from_url  # noqa: F401
from pyvizio.const import (  # noqa: F401
    APP_HOME,
    APPS,
    DEFAULT_DEVICE_CLASS,
    DEFAULT_PORTS,
    DEFAULT_TIMEOUT,
    DEVICE_CLASS_CRAVE360 as DEVICE_CLASS_CRAVE360,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
    DEVICE_CONFIGS,
    MAX_VOLUME as MAX_VOLUME,
)
from pyvizio.discovery.ssdp import SSDPDevice, discover as discover_ssdp  # noqa: F401
from pyvizio.discovery.zeroconf import (  # noqa: F401
    ZeroconfDevice,
    discover as discover_zc,
)
from pyvizio.errors import (  # noqa: F401
    VizioAuthError as VizioAuthError,
    VizioBusyError as VizioBusyError,
    VizioConnectionError as VizioConnectionError,
    VizioError as VizioError,
    VizioInvalidInputError as VizioInvalidInputError,
    VizioInvalidParameterError as VizioInvalidParameterError,
    VizioNotFoundError as VizioNotFoundError,
    VizioResponseError as VizioResponseError,
    VizioUnsupportedError as VizioUnsupportedError,
)
from pyvizio.helpers import async_to_sync, open_port  # noqa: F401
from pyvizio.version import __version__ as __version__

# ---- Sync wrapper class ----


class Vizio(VizioAsync):
    """Synchronous class to interact with Vizio SmartCast devices.

    All async methods from VizioAsync are automatically available as synchronous
    methods via auto-wrapping with asyncio.run().
    """

    def __init__(
        self,
        device_id: str,
        ip: str,
        name: str,
        auth_token: str = "",
        device_type: str = DEFAULT_DEVICE_CLASS,
        timeout: int = DEFAULT_TIMEOUT,
        max_concurrent_requests: int = 1,
    ) -> None:
        """Initialize synchronous class to interact with Vizio SmartCast devices."""
        super().__init__(
            device_id,
            ip,
            name,
            auth_token,
            device_type,
            session=None,
            timeout=timeout,
            max_concurrent_requests=max_concurrent_requests,
        )

    @staticmethod
    def discovery_zeroconf(timeout: int = DEFAULT_TIMEOUT) -> list[ZeroconfDevice]:
        """Discover Vizio devices on network using zeroconf."""
        return super(Vizio, Vizio).discovery_zeroconf(timeout)

    @staticmethod
    def discovery_ssdp(timeout: int = DEFAULT_TIMEOUT) -> list[SSDPDevice]:
        """Discover Vizio devices on network using SSDP."""
        return super(Vizio, Vizio).discovery_ssdp(timeout)

    @staticmethod
    @async_to_sync
    async def validate_ha_config(
        ip: str,
        auth_token: str,
        device_type: str,
        session: ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """Return whether or not HomeAssistant config is valid."""
        return await super(Vizio, Vizio).validate_ha_config(
            ip, auth_token, device_type, session=session, timeout=timeout
        )

    @staticmethod
    @async_to_sync
    async def get_unique_id(
        ip: str, device_type: str, timeout: int = DEFAULT_TIMEOUT
    ) -> str | None:
        """Get unique identifier for Vizio device."""
        return await super(Vizio, Vizio).get_unique_id(ip, device_type, timeout=timeout)

    @staticmethod
    @async_to_sync
    async def get_apps_list(
        country: str = "all",
        apps_list: list[dict[str, Any]] | None = None,
        session: ClientSession | None = None,
    ) -> list[str]:
        """Get list of known apps by name optionally filtered by supported country."""
        return await super(Vizio, Vizio).get_apps_list(
            country=country, apps_list=apps_list, session=session
        )


# Auto-wrap all public async instance methods from VizioAsync onto Vizio
def _generate_sync_wrappers() -> None:
    vizio_vars = vars(Vizio)
    for name, raw in vars(VizioAsync).items():
        if name.startswith("_"):
            continue
        if isinstance(raw, staticmethod | classmethod):
            continue
        attr = getattr(VizioAsync, name)
        if asyncio.iscoroutinefunction(attr) and name not in vizio_vars:
            wrapper = async_to_sync(attr)
            wrapper.__qualname__ = f"Vizio.{name}"
            doc = (wrapper.__doc__ or "").removeprefix("Asynchronously ")
            if doc:
                doc = doc[0].upper() + doc[1:]
            wrapper.__doc__ = doc
            setattr(Vizio, name, wrapper)


_generate_sync_wrappers()
del _generate_sync_wrappers


# ---- Module-level functions ----


async def async_guess_device_type(
    ip: str, port: str | None = None, timeout: int = DEFAULT_TIMEOUT
) -> str:
    """Attempt to guess the device type by getting audio settings with no auth token."""
    if port:
        if ":" in ip:
            raise VizioInvalidParameterError(
                "Port can't be included in both `ip` and `port` parameters"
            )
        device = VizioAsync(
            "test", f"{ip}:{port}", "test", "", DEVICE_CLASS_SPEAKER, timeout=timeout
        )
    else:
        device = VizioAsync(
            "test", ip, "test", "", DEVICE_CLASS_SPEAKER, timeout=timeout
        )

    if await device.can_connect_with_auth_check():
        return DEVICE_CLASS_SPEAKER
    else:
        return DEVICE_CLASS_TV


@async_to_sync
async def guess_device_type(
    ip: str, port: str | None = None, timeout: int = DEFAULT_TIMEOUT
) -> str:
    """Attempt to guess the device type (sync wrapper)."""
    return await async_guess_device_type(ip, port, timeout)


if TYPE_CHECKING:
    # fmt: off
    # Stubs so type checkers/IDEs see the sync signatures on Vizio.
    class Vizio(VizioAsync):  # type: ignore[no-redef]
        def __init__(self, device_id: str, ip: str, name: str, auth_token: str = "", device_type: str = DEFAULT_DEVICE_CLASS, timeout: int = DEFAULT_TIMEOUT, max_concurrent_requests: int = 1) -> None: ...
        def connect(self) -> None: ...  # type: ignore[override]
        @staticmethod
        def validate_ha_config(ip: str, auth_token: str, device_type: str, session: ClientSession | None = None, timeout: int = DEFAULT_TIMEOUT) -> bool: ...  # type: ignore[override]
        @staticmethod
        def get_unique_id(ip: str, device_type: str, timeout: int = DEFAULT_TIMEOUT) -> str | None: ...  # type: ignore[override]
        @staticmethod
        def get_apps_list(country: str = "all", apps_list: list[dict[str, Any]] | None = None, session: ClientSession | None = None) -> list[str]: ...  # type: ignore[override]
        def can_connect_no_auth_check(self) -> bool: ...  # type: ignore[override]
        def can_connect_with_auth_check(self) -> bool: ...  # type: ignore[override]
        def ch_down(self, num: int = 1, **kwargs) -> bool | None: ...  # type: ignore[override]
        def ch_prev(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def ch_up(self, num: int = 1, **kwargs) -> bool | None: ...  # type: ignore[override]
        def get_all_audio_settings(self, **kwargs) -> dict[str, int | str] | None: ...  # type: ignore[override]
        def get_all_audio_settings_options(self, **kwargs) -> dict[str, list[str] | dict[str, int | None]] | None: ...  # type: ignore[override]
        def get_all_settings(self, setting_type: str, **kwargs) -> dict[str, int | str] | None: ...  # type: ignore[override]
        def get_all_settings_options(self, setting_type: str, **kwargs) -> dict[str, list[str] | dict[str, int | None]] | None: ...  # type: ignore[override]
        def get_all_settings_options_xlist(self, setting_type: str, **kwargs) -> dict[str, list[str]] | None: ...  # type: ignore[override]
        def get_audio_setting(self, setting_name: str, **kwargs) -> int | str | None: ...  # type: ignore[override]
        def get_audio_setting_options(self, setting_name: str, **kwargs) -> list[str] | dict[str, int | None] | None: ...  # type: ignore[override]
        def get_battery_level(self, **kwargs) -> int | None: ...  # type: ignore[override]
        def get_charging_status(self, **kwargs) -> int | None: ...  # type: ignore[override]
        def get_current_app(self, apps_list: list[dict[str, Any]] | None = None, **kwargs) -> str | None: ...  # type: ignore[override]
        def get_current_app_config(self, **kwargs) -> AppConfig | None: ...  # type: ignore[override]
        def get_current_input(self, **kwargs) -> str | None: ...  # type: ignore[override]
        def get_current_volume(self, **kwargs) -> int | None: ...  # type: ignore[override]
        def get_esn(self, **kwargs) -> str | None: ...  # type: ignore[override]
        def get_inputs_list(self, **kwargs) -> list[InputItem] | None: ...  # type: ignore[override]
        def get_model_name(self, **kwargs) -> str | None: ...  # type: ignore[override]
        def get_power_state(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def get_serial_number(self, **kwargs) -> str | None: ...  # type: ignore[override]
        def get_setting(self, setting_type: str, setting_name: str, **kwargs) -> int | str | None: ...  # type: ignore[override]
        def get_setting_options(self, setting_type: str, setting_name: str, **kwargs) -> list[str] | dict[str, int | None] | None: ...  # type: ignore[override]
        def get_setting_options_xlist(self, setting_type: str, setting_name: str, **kwargs) -> list[str] | None: ...  # type: ignore[override]
        def get_setting_types_list(self, **kwargs) -> list[str] | None: ...  # type: ignore[override]
        def get_version(self, **kwargs) -> str | None: ...  # type: ignore[override]
        def is_muted(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def launch_app(self, app_name: str, apps_list: list[dict[str, Any]] | None = None, **kwargs) -> bool | None: ...  # type: ignore[override]
        def launch_app_config(self, APP_ID: str, NAME_SPACE: int, MESSAGE: str | None = None, **kwargs) -> bool | None: ...  # type: ignore[override]
        def mute_off(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def mute_on(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def mute_toggle(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def next_input(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def pair(self, ch_type: int | str, token: int | str, pin: str = "", **kwargs) -> PairChallengeResponse | None: ...  # type: ignore[override]
        def pause(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def play(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def pow_off(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def pow_on(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def pow_toggle(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def remote(self, key: str, **kwargs) -> bool | None: ...  # type: ignore[override]
        def set_audio_setting(self, setting_name: str, new_value: int | str, **kwargs) -> bool | None: ...  # type: ignore[override]
        def set_input(self, name: str, **kwargs) -> bool | None: ...  # type: ignore[override]
        def set_setting(self, setting_type: str, setting_name: str, new_value: int | str, **kwargs) -> bool | None: ...  # type: ignore[override]
        def start_pair(self, **kwargs) -> BeginPairResponse | None: ...  # type: ignore[override]
        def stop_pair(self, **kwargs) -> bool | None: ...  # type: ignore[override]
        def vol_down(self, num: int = 1, **kwargs) -> bool | None: ...  # type: ignore[override]
        def vol_up(self, num: int = 1, **kwargs) -> bool | None: ...  # type: ignore[override]
    # fmt: on
