"""Initialize pyvizio."""

from __future__ import annotations

import asyncio
from asyncio import sleep
from collections.abc import KeysView
from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from aiohttp import ClientSession
import requests
import xmltodict

from pyvizio.api._protocol import KEY_CODE, async_invoke_api, async_invoke_api_auth
from pyvizio.api.apps import (
    AppConfig,
    GetCurrentAppConfigCommand,
    GetCurrentAppNameCommand,
    LaunchAppConfigCommand,
    LaunchAppNameCommand,
)
from pyvizio.api.base import CommandBase
from pyvizio.api.input import (
    ChangeInputCommand,
    GetCurrentInputCommand,
    GetInputsListCommand,
    InputItem,
)
from pyvizio.api.item import (
    AltItemInfoCommandBase,
    GetDeviceInfoCommand,
    GetModelNameCommand,
    GetTvInformationCommand,
    ItemInfoCommandBase,
)
from pyvizio.api.pair import (
    BeginPairCommand,
    BeginPairResponse,
    CancelPairCommand,
    PairChallengeCommand,
    PairChallengeResponse,
)
from pyvizio.api.remote import EmulateRemoteCommand
from pyvizio.api.settings import (
    ChangeSettingCommand,
    GetAllSettingsCommand,
    GetAllSettingsOptionsCommand,
    GetAllSettingsOptionsXListCommand,
    GetAllSettingTypesCommand,
    GetSettingCommand,
    GetSettingOptionsCommand,
    GetSettingOptionsXListCommand,
)
from pyvizio.api.state_extended import GetStateExtendedCommand, StateExtended
from pyvizio.const import (
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
from pyvizio.discovery.ssdp import SSDPDevice, discover as discover_ssdp
from pyvizio.discovery.zeroconf import ZeroconfDevice, discover as discover_zc
from pyvizio.errors import (
    VizioAuthError,
    VizioBusyError as VizioBusyError,
    VizioConnectionError as VizioConnectionError,
    VizioError as VizioError,
    VizioHashvalError as VizioHashvalError,
    VizioInvalidInputError,
    VizioInvalidParameterError as VizioInvalidParameterError,
    VizioNotFoundError as VizioNotFoundError,
    VizioResponseError as VizioResponseError,
    VizioUnsupportedError as VizioUnsupportedError,
)
from pyvizio.helpers import async_to_sync, dict_get_case_insensitive, open_port
from pyvizio.util import gen_apps_list_from_url
from pyvizio.version import __version__ as __version__

_LOGGER = logging.getLogger(__name__)


def _resolve_input_cname(name: str, inputs: list[InputItem]) -> str:
    """Resolve a user-supplied input identifier to its canonical cname.

    The device's PUT body for ``current_input`` carries the lowercase
    **cname** (e.g. ``"hdmi2"``), not the display name (``"HDMI-2"``)
    or the meta_name (``"Mac"``). Verified live on VHD24M-0810 fw
    3.720.9.1-1: PUT VALUE=``HDMI-2`` → FAILURE; PUT VALUE=``Mac`` →
    HASHVAL_ERROR; PUT VALUE=``hdmi2`` → SUCCESS.

    Resolution order, all case-insensitive:

    1. Exact ``cname`` match (most specific).
    2. Exact ``meta_name`` match (handles CAST/SMARTCAST and user
       renames).
    3. Exact display ``name`` match (label fallback).

    Raises :class:`VizioInvalidInputError` when no input matches, or
    when a label is ambiguous within the same resolution tier (user
    renamed two HDMIs to the same label).
    """
    target = name.lower()
    candidates_by_tier = {
        "cname": [i for i in inputs if (i.c_name or "").lower() == target],
        "meta_name": [i for i in inputs if (i.meta_name or "").lower() == target],
        "name": [i for i in inputs if (i.name or "").lower() == target],
    }
    for tier, hits in candidates_by_tier.items():
        if len(hits) == 1:
            return (hits[0].c_name or "").lower()
        if len(hits) > 1:
            raise VizioInvalidInputError(
                f"input {name!r} matches multiple inputs by {tier} "
                f"({[h.c_name for h in hits]}); rename one to disambiguate"
            )

    # Build a deduplicated list of valid identifiers, normalized to
    # lowercase and stripped of empties so the user-facing error
    # message is clean.
    valid = sorted(
        v.lower()
        for v in (
            {i.c_name or "" for i in inputs}
            | {i.name or "" for i in inputs}
            | {i.meta_name or "" for i in inputs if i.meta_name}
        )
        if v
    )
    raise VizioInvalidInputError(f"input {name!r} not found. Valid: {valid}")


class VizioAsync:
    """Asynchronous class to interact with Vizio SmartCast devices."""

    def __init__(
        self,
        device_id: str,
        ip: str,
        name: str,
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
        # Identity (esn / serial_number / firmware / version) is
        # immutable for a device's lifetime, so the aggregate fetch is
        # cached on the instance after the first attempt. ``_loaded``
        # captures both success (mapping) and failure (None) — without
        # it, three identity calls on a device that doesn't expose the
        # aggregate would each pay the round-trip + URI_NOT_FOUND.
        self._cached_identity: dict[str, str] | None = None
        self._cached_identity_loaded: bool = False
        # Capability cache for /state_extended. Once a device has
        # answered URI_NOT_FOUND we don't re-probe — capabilities are
        # immutable for the session, and HA-style polling otherwise
        # pays the round trip on every poll cycle.
        self._state_extended_unavailable: bool = False

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

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Lazily create semaphore (Python 3.9 requires a running event loop)."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrent_requests)
        return self._semaphore

    async def __add_port(self) -> None:
        """Asynchronously add first open port from known ports list to `ip` property."""
        for port in DEFAULT_PORTS:
            if await open_port(self.ip, port):
                self.ip = f"{self.ip}:{port}"

    async def connect(self) -> None:
        """Eagerly resolve port if not already specified.

        This is optional — lazy resolution still works if connect() is not called.
        """
        if ":" not in self.ip:
            await self.__add_port()

    async def __invoke_api(
        self,
        cmd: CommandBase,
        log_api_exception: bool = True,
        propagate_errors: bool = False,
    ) -> Any:
        """Asynchronously call SmartCast API without auth token."""
        async with self._get_semaphore():
            if ":" not in self.ip:
                await self.__add_port()

            return await async_invoke_api(
                self.ip,
                cmd,
                _LOGGER,
                custom_timeout=self._timeout,
                log_api_exception=log_api_exception,
                session=self._session,
                propagate_errors=propagate_errors,
            )

    async def __invoke_api_auth(
        self,
        cmd: CommandBase,
        log_api_exception: bool = True,
        skip_envelope: bool = False,
        propagate_errors: bool = False,
    ) -> Any:
        """Asynchronously call SmartCast API with auth token.

        ``skip_envelope=True`` is for endpoints with non-standard
        response shapes (currently only ``/state_extended``).
        ``propagate_errors=True`` re-raises typed VizioError instead of
        returning ``None`` — used by multi-path-fallback callers.
        """
        async with self._get_semaphore():
            if ":" not in self.ip:
                await self.__add_port()

            return await async_invoke_api_auth(
                self.ip,
                cmd,
                _LOGGER,
                auth_token=self._auth_token,
                custom_timeout=self._timeout,
                log_api_exception=log_api_exception,
                session=self._session,
                skip_envelope=skip_envelope,
                propagate_errors=propagate_errors,
            )

    async def __invoke_api_may_need_auth(
        self,
        cmd: CommandBase,
        log_api_exception: bool = True,
        propagate_errors: bool = False,
        skip_envelope: bool = False,
    ) -> Any:
        """Asynchronously call SmartCast API command with or without auth token depending on device type."""
        if not self._auth_token:
            if not self._device_config.requires_auth:
                return await self.__invoke_api(
                    cmd,
                    log_api_exception=log_api_exception,
                    propagate_errors=propagate_errors,
                )
            else:
                no_auth_types = [
                    k for k, v in DEVICE_CONFIGS.items() if not v.requires_auth
                ]
                raise VizioAuthError(
                    f"Empty auth token. Device types that don't require auth: "
                    f"{', '.join(repr(t) for t in no_auth_types)}"
                )
        return await self.__invoke_api_auth(
            cmd,
            log_api_exception=log_api_exception,
            propagate_errors=propagate_errors,
            skip_envelope=skip_envelope,
        )

    async def __remote(
        self, key_list: str | list[str], log_api_exception: bool = True
    ) -> bool:
        """Asynchronously call key press API with list of keys."""
        key_codes = []
        if not isinstance(key_list, list):
            key_list = [key_list]

        for key in key_list:
            if key not in KEY_CODE[self.device_type]:
                _LOGGER.error(
                    "Key Code of '%s' not found for device type of '%s'",
                    key,
                    self.device_type,
                )
                return False
            else:
                key_codes.append(KEY_CODE[self.device_type][key])

        result = await self.__invoke_api_may_need_auth(
            EmulateRemoteCommand(key_codes, self.device_type),
            log_api_exception=log_api_exception,
        )
        return result is not None

    async def __remote_multiple(
        self, key_code: str, num: int, log_api_exception: bool = True
    ) -> bool:
        """Asynchronously call key press API with list of same key repeated multiple times."""
        key_codes = [key_code for _ in range(num)]
        return await self.__remote(key_codes, log_api_exception=log_api_exception)

    async def __get_identity_aggregate(
        self,
        log_api_exception: bool = True,
        require_auth: bool = True,
    ) -> dict[str, str] | None:
        """Asynchronously fetch the aggregate ``tv_information`` envelope.

        Result is cached on the instance — identity is immutable for a
        device's lifetime. When the aggregate is exposed, three identity
        calls (esn + serial_number + version) make one HTTP round trip
        instead of three.

        Cache write rules:
          * Mapping returned: cache the mapping.
          * Every candidate path returned ``URI_NOT_FOUND``: cache
            ``None`` (this firmware definitively doesn't expose the
            aggregate, so identity getters can stop trying).
          * Transient failure (transport, auth, busy, malformed): do
            **not** cache; the next call will re-attempt.

        ``VizioAuthError`` always propagates — callers like
        ``can_connect_with_auth_check`` rely on the typed exception to
        distinguish "token invalidated" from generic failure.
        """
        if self._cached_identity_loaded:
            return self._cached_identity
        for endpoint_key in ("TV_INFORMATION", "_ALT_TV_INFORMATION"):
            if endpoint_key not in self._device_config.endpoints:
                continue
            try:
                # Probe-style identity calls (e.g. get_unique_id, which
                # uses an empty auth_token) need the no-auth invoker.
                # ESN-bearing callers want the auth-aware invoker so the
                # device returns the auth-gated fields.
                if require_auth:
                    mapping = await self.__invoke_api_may_need_auth(
                        GetTvInformationCommand(self.device_type, endpoint_key),
                        log_api_exception=log_api_exception,
                        # Propagate typed errors so we can distinguish
                        # "not exposed at this path" (URI_NOT_FOUND →
                        # try next candidate) from transient/auth
                        # failures (don't cache; retry next call).
                        propagate_errors=True,
                    )
                else:
                    mapping = await self.__invoke_api(
                        GetTvInformationCommand(self.device_type, endpoint_key),
                        log_api_exception=log_api_exception,
                        propagate_errors=True,
                    )
            except VizioNotFoundError:
                continue
            if mapping:
                self._cached_identity = mapping
                self._cached_identity_loaded = True
                return mapping
        # Every candidate either returned URI_NOT_FOUND or returned an
        # empty mapping. Cache the negative result so identity getters
        # stop probing the aggregate on every call.
        self._cached_identity = None
        self._cached_identity_loaded = True
        return None

    async def __get_cached_apps_list(self) -> list[dict[str, Any]]:
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

    @staticmethod
    def discovery_zeroconf(timeout: int = DEFAULT_TIMEOUT) -> list[ZeroconfDevice]:
        """Discover Vizio devices on network using zeroconf."""
        results = discover_zc("_viziocast._tcp.local.", timeout=timeout)
        _LOGGER.info(results)
        return results

    @staticmethod
    def discovery_ssdp(timeout: int = DEFAULT_TIMEOUT) -> list[SSDPDevice]:
        """Discover Vizio devices on network using SSDP."""
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
                split_url.hostname, root["friendlyName"], root["modelName"], root["UDN"]
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
        """Asynchronously return whether or not HomeAssistant config will allow HomeAssistant to make successful calls to Vizio SmartCast API."""
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
        """Asynchronously get unique identifier for Vizio device."""
        return await VizioAsync(
            "", ip, "", "", device_type, session=session, timeout=timeout
        ).get_serial_number(log_api_exception=False)

    async def can_connect_with_auth_check(self) -> bool:
        """Asynchronously return whether or not device API can be connected to with valid authorization.

        Probe-style helper — must always return a bool, never propagate.
        HTTP 401/403 raises :class:`VizioAuthError` from the transport;
        non-probe callers rely on that propagation to detect re-pair
        invalidation, so this probe catches it locally and surfaces it
        as a ``False`` result.
        """
        try:
            return bool(
                await VizioAsync.get_all_audio_settings(self, log_api_exception=False)
            )
        except VizioAuthError:
            return False

    async def can_connect_no_auth_check(self) -> bool:
        """Asynchronously return whether or not device API can be connected to regardless of authorization."""
        return bool(
            await self.__invoke_api(
                GetDeviceInfoCommand(self.device_type), log_api_exception=False
            )
        )

    async def get_esn(self, log_api_exception: bool = True) -> str | None:
        """Asynchronously get device's ESN (electronic serial number?).

        Prefers the aggregate ``TV_INFORMATION`` endpoint; falls back
        to per-field ``ESN`` / ``_ALT_ESN`` paths for older firmware
        or after a transient aggregate failure. ``VizioAuthError``
        always propagates.
        """
        try:
            agg = await self.__get_identity_aggregate(
                log_api_exception=log_api_exception
            )
        except VizioAuthError:
            raise
        except VizioError:
            agg = None
        if agg and agg.get("esn"):
            return agg["esn"]

        item = await self.__invoke_api_may_need_auth(
            ItemInfoCommandBase(self.device_type, "ESN"),
            log_api_exception=log_api_exception,
        ) or await self.__invoke_api_may_need_auth(
            AltItemInfoCommandBase(self.device_type, "_ALT_ESN", "ESN"),
            log_api_exception=log_api_exception,
        )

        if item and item.value:
            return item.value

        return None

    async def get_serial_number(self, log_api_exception: bool = True) -> str | None:
        """Asynchronously get device's serial number.

        Prefers the aggregate ``TV_INFORMATION`` endpoint; falls back
        to per-field paths for older firmware or after a transient
        aggregate failure. ``VizioAuthError`` always propagates.
        """
        try:
            agg = await self.__get_identity_aggregate(
                log_api_exception=log_api_exception, require_auth=False
            )
        except VizioAuthError:
            raise
        except VizioError:
            agg = None
        if agg and agg.get("serial_number"):
            return agg["serial_number"]

        item = await self.__invoke_api(
            ItemInfoCommandBase(self.device_type, "SERIAL_NUMBER"),
            log_api_exception=log_api_exception,
        ) or await self.__invoke_api(
            AltItemInfoCommandBase(
                self.device_type, "_ALT_SERIAL_NUMBER", "SERIAL_NUMBER"
            ),
            log_api_exception=log_api_exception,
        )

        if item and item.value:
            return item.value

        return None

    async def get_version(self, log_api_exception: bool = True) -> str | None:
        """Asynchronously get SmartCast software version on device.

        Prefers the aggregate ``TV_INFORMATION`` endpoint, where the
        version is exposed under cname ``"firmware"`` (modern firmware)
        or ``"version"`` (older). Falls back to per-field paths for
        older firmware or after a transient aggregate failure.
        ``VizioAuthError`` always propagates.
        """
        try:
            agg = await self.__get_identity_aggregate(
                log_api_exception=log_api_exception, require_auth=False
            )
        except VizioAuthError:
            raise
        except VizioError:
            agg = None
        if agg:
            for cname in ("version", "firmware"):
                if agg.get(cname):
                    return agg[cname]

        item = await self.__invoke_api(
            ItemInfoCommandBase(self.device_type, "VERSION"),
            log_api_exception=log_api_exception,
        ) or await self.__invoke_api(
            AltItemInfoCommandBase(self.device_type, "_ALT_VERSION", "VERSION"),
            log_api_exception=log_api_exception,
        )

        if item and item.value:
            return item.value

        return None

    async def get_model_name(self, log_api_exception: bool = True) -> str | None:
        """Asynchronously get device's model number."""
        return await self.__invoke_api(
            GetModelNameCommand(self.device_type), log_api_exception=log_api_exception
        )

    async def start_pair(
        self, log_api_exception: bool = True
    ) -> BeginPairResponse | None:
        """Asynchronously begin pairing process to obtain challenge type and challenge token."""
        return await self.__invoke_api(
            BeginPairCommand(self.device_id, self.name, self.device_type),
            log_api_exception=log_api_exception,
        )

    async def stop_pair(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously cancel pairing process."""
        return await self.__invoke_api(
            CancelPairCommand(self.device_id, self.name, self.device_type),
            log_api_exception=log_api_exception,
        )

    async def pair(
        self,
        ch_type: int | str,
        token: int | str,
        pin: str = "",
        log_api_exception: bool = True,
    ) -> PairChallengeResponse | None:
        """Asynchronously complete pairing process to obtain auth token."""
        if self.device_type == DEVICE_CLASS_SPEAKER:
            pin = "0000"
        return await self.__invoke_api(
            PairChallengeCommand(self.device_id, ch_type, token, pin, self.device_type),
            log_api_exception=log_api_exception,
        )

    async def get_inputs_list(
        self, log_api_exception: bool = True
    ) -> list[InputItem] | None:
        """Asynchronously get list of available inputs."""
        return await self.__invoke_api_may_need_auth(
            GetInputsListCommand(self.device_type), log_api_exception=log_api_exception
        )

    async def get_current_input(self, log_api_exception: bool = True) -> str | None:
        """Asynchronously get device's active input."""
        item = await self.__invoke_api_may_need_auth(
            GetCurrentInputCommand(self.device_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return item.meta_name

        return None

    async def next_input(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously switch active input to next input."""
        # HACK: Single call just invoking overlay menu with current input
        return await self.__remote_multiple(
            "INPUT_NEXT", 2, log_api_exception=log_api_exception
        )

    async def set_input(self, name: str, log_api_exception: bool = True) -> bool | None:
        """Asynchronously switch active input to named input.

        ``name`` accepts any of the input's three identifier forms,
        case-insensitively: cname (``"hdmi2"``), display name
        (``"HDMI-2"``), or meta_name (``"Mac"`` / ``"SMARTCAST"``).
        Verified live on VHD24M-0810 fw 3.720.9.1-1: only the
        lowercase cname succeeds in the PUT body — display name
        returns FAILURE, meta_name returns HASHVAL_ERROR. This method
        translates any of the three forms before sending.

        Short-circuits when already on the target input — the device
        explicitly rejects "switch to current input" with FAILURE.

        This issues two GETs (current input + inputs list) before the
        PUT to perform the name → cname resolution.
        """
        curr_input_item = await self.__invoke_api_may_need_auth(
            GetCurrentInputCommand(self.device_type),
            log_api_exception=log_api_exception,
        )
        if not curr_input_item:
            _LOGGER.error("Couldn't detect current input")
            return None

        inputs = await self.__invoke_api_may_need_auth(
            GetInputsListCommand(self.device_type),
            log_api_exception=log_api_exception,
        )
        if not inputs:
            _LOGGER.error("Couldn't fetch inputs list")
            return None

        try:
            target_cname = _resolve_input_cname(name, inputs)
        except VizioInvalidInputError as err:
            if log_api_exception:
                _LOGGER.error("%s", err)
            return None

        # Short-circuit when already on target. ``current_input.value``
        # is inconsistent across input types (display name for HDMI,
        # meta_name for CAST) so check against any of the three forms.
        target_input = next(
            (i for i in inputs if (i.c_name or "").lower() == target_cname),
            None,
        )
        if target_input and isinstance(curr_input_item.value, str):
            # Drop empty strings so a missing meta_name doesn't make the
            # short-circuit match an empty-string current_value.
            candidates = {
                c
                for c in (
                    target_cname,
                    (target_input.name or "").lower(),
                    (target_input.meta_name or "").lower(),
                )
                if c
            }
            if curr_input_item.value.lower() in candidates:
                return True

        return await self.__invoke_api_may_need_auth(
            ChangeInputCommand(self.device_type, curr_input_item.id, target_cname),
            log_api_exception=log_api_exception,
        )

    async def get_state_extended(
        self, log_api_exception: bool = True
    ) -> StateExtended | None:
        """Asynchronously fetch aggregate device state in one HTTP round trip.

        Returns power, current input, current app, screen mode, and
        media state — meaningfully cheaper than five individual GETs
        for HA-style polling integrations. Capability is advertised
        under ``deviceinfo.scpl_capabilities.state_extended``.

        The on-the-wire success payload is **distinct** from the
        regular SCPL response shape — flat top-level keys, no
        ``STATUS``/``ITEMS`` — so this method invokes with
        ``skip_envelope=True``. When the device instead returns a
        normal SCPL envelope (older firmware that doesn't expose the
        endpoint, or transient errors like ``BLOCKED`` /
        ``REQUIRES_PAIRING``), the bypassed validator would let the
        parser silently produce a default-filled ``StateExtended``;
        this method detects any ``STATUS.RESULT`` envelope on the raw
        payload and returns ``None`` (URI_NOT_FOUND, BLOCKED) or
        raises (auth-class envelopes) accordingly.

        Raises :class:`VizioUnsupportedError` for device types that
        don't expose the endpoint (speakers, Crave). The standard
        ``log_api_exception=False`` swallow turns it back into ``None``
        for compat callers.
        """
        if "STATE_EXTENDED" not in self._device_config.endpoints:
            # Device-class capability is a programming-level invariant
            # (set by the constructor), not a runtime device condition,
            # so this always raises — the swallow-and-return-None path
            # is reserved for transport / device failures.
            raise VizioUnsupportedError(
                f"{self.device_type!r} doesn't expose /state_extended"
            )
        if self._state_extended_unavailable:
            # Earlier call definitively confirmed the firmware doesn't
            # expose this endpoint; don't re-probe.
            return None

        try:
            result = await self.__invoke_api_may_need_auth(
                GetStateExtendedCommand(self.device_type),
                log_api_exception=log_api_exception,
                skip_envelope=True,
            )
        except VizioAuthError:
            raise
        except VizioError as err:
            if log_api_exception:
                _LOGGER.error("Failed to fetch /state_extended: %s", err)
            return None

        if result is None:
            return None

        # ``skip_envelope`` bypassed standard validation. Detect any
        # SCPL-envelope-shaped error here so callers can't be confused
        # by a default-filled StateExtended:
        #   * URI_NOT_FOUND  → endpoint not exposed → return None
        #   * BLOCKED        → device busy           → return None
        #   * REQUIRES_PAIRING / PAIRING_DENIED → re-raise VizioAuthError
        #   * other unrecognized → return None (defensive)
        raw = result.raw if isinstance(result, StateExtended) else {}
        status_obj = dict_get_case_insensitive(raw, "status")
        if isinstance(status_obj, dict):
            res = dict_get_case_insensitive(status_obj, "result")
            res_lower = res.lower() if isinstance(res, str) else ""
            if res_lower in ("requires_pairing", "pairing_denied"):
                raise VizioAuthError(
                    dict_get_case_insensitive(status_obj, "detail") or res_lower
                )
            if res_lower == "uri_not_found":
                # Definitive: this firmware doesn't expose the endpoint.
                # Cache so the next poll doesn't re-probe.
                self._state_extended_unavailable = True
                if log_api_exception:
                    _LOGGER.debug("/state_extended not exposed by this firmware")
                return None
            if res_lower:
                # Other envelope statuses (BLOCKED, etc.) are transient
                # — don't poison the capability cache.
                if log_api_exception:
                    _LOGGER.debug(
                        "/state_extended returned envelope status %r — "
                        "treating as unavailable",
                        res,
                    )
                return None
        return result

    async def get_power_state(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously get device's current power state."""
        item = await self.__invoke_api_may_need_auth(
            ItemInfoCommandBase(self.device_type, "POWER_MODE", 0),
            log_api_exception=log_api_exception,
        )

        if item:
            return bool(item.value)

        return None

    async def get_charging_status(self, log_api_exception: bool = True) -> int | None:
        """Asynchronously get device's current charging state."""
        item = await self.__invoke_api_may_need_auth(
            ItemInfoCommandBase(self.device_type, "CHARGING_STATUS", 0),
            log_api_exception=log_api_exception,
        )

        if item:
            return int(item.value)

        return None

    async def get_battery_level(self, log_api_exception: bool = True) -> int | None:
        """Asynchronously get device's current battery level (will be 0 if charging)."""
        item = await self.__invoke_api_may_need_auth(
            ItemInfoCommandBase(self.device_type, "BATTERY_LEVEL", 0),
            log_api_exception=log_api_exception,
        )
        if item:
            return int(item.value)

        return None

    async def pow_on(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously power device on."""
        return await self.__remote("POW_ON", log_api_exception=log_api_exception)

    async def pow_off(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously power device off."""
        return await self.__remote("POW_OFF", log_api_exception=log_api_exception)

    async def pow_toggle(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously toggle device power."""
        return await self.__remote("POW_TOGGLE", log_api_exception=log_api_exception)

    async def vol_up(self, num: int = 1, log_api_exception: bool = True) -> bool | None:
        """Asynchronously increase volume by number of steps."""
        return await self.__remote_multiple(
            "VOL_UP", num, log_api_exception=log_api_exception
        )

    async def vol_down(
        self, num: int = 1, log_api_exception: bool = True
    ) -> bool | None:
        """Asynchronously decrease volume by number of steps."""
        return await self.__remote_multiple(
            "VOL_DOWN", num, log_api_exception=log_api_exception
        )

    async def get_current_volume(self, log_api_exception: bool = True) -> int | None:
        """Asynchronously get device's current volume level."""
        volume = await VizioAsync.get_audio_setting(
            self, "volume", log_api_exception=log_api_exception
        )
        return int(volume) if volume else None

    async def is_muted(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously determine whether or not device is muted.

        Returns ``None`` when the underlying mute setting can't be
        read (transport / device error). The state-aware
        :meth:`mute_on` / :meth:`mute_off` rely on the ``None`` signal
        to avoid blindly toggling on an unknown state.

        Note: every :class:`VizioError` (including :class:`VizioAuthError`
        and :class:`VizioBusyError`) is swallowed as ``None`` here. If
        a caller needs to distinguish auth invalidation from a transport
        blip, call ``get_audio_setting('mute')`` directly.
        """
        try:
            mute_val = await VizioAsync.get_audio_setting(
                self, "mute", log_api_exception=log_api_exception
            )
        except VizioError:
            return None
        if mute_val is None:
            return None
        return str(mute_val).lower() == "on"

    def get_max_volume(self) -> int:
        """Get device's max volume based on device type."""
        return self._device_config.max_volume

    async def ch_up(self, num: int = 1, log_api_exception: bool = True) -> bool | None:
        """Asynchronously channel up by number of steps."""
        return await self.__remote_multiple(
            "CH_UP", num, log_api_exception=log_api_exception
        )

    async def ch_down(
        self, num: int = 1, log_api_exception: bool = True
    ) -> bool | None:
        """Asynchronously channel down by number of steps."""
        return await self.__remote_multiple(
            "CH_DOWN", num, log_api_exception=log_api_exception
        )

    async def ch_prev(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously go to previous channel."""
        return await self.__remote("CH_PREV", log_api_exception=log_api_exception)

    async def mute_on(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously mute sound (idempotent — no-op if already muted).

        Verified live on VHD24M-0810 fw 3.720.9.1-1: discrete
        ``MUTE_ON`` / ``MUTE_OFF`` codes don't actually exist as
        discrete actions on TVs — codeset 5 codes 2/3/4 all behave
        as toggles. ``MUTE_TOGGLE`` is the only universally reliable
        behavior, so this method reads current mute state and sends
        the toggle only on mismatch.

        Returns ``None`` when the state probe fails (transport / auth
        error during ``is_muted``) — falling through to a blind
        toggle would risk inverting an already-muted device. Power
        users wanting raw codes can still call ``remote("MUTE_ON")``.
        """
        current = await self.is_muted(log_api_exception=log_api_exception)
        if current is True:
            return True
        if current is None:
            return None
        return await self.__remote("MUTE_TOGGLE", log_api_exception=log_api_exception)

    async def mute_off(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously unmute sound (idempotent — no-op if already unmuted).

        See :meth:`mute_on` for the rationale on the read-then-toggle
        pattern, including the ``is_muted() == None`` guard against
        inverting an already-correct state when the probe fails.
        """
        current = await self.is_muted(log_api_exception=log_api_exception)
        if current is False:
            return True
        if current is None:
            return None
        return await self.__remote("MUTE_TOGGLE", log_api_exception=log_api_exception)

    async def mute_toggle(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously toggle sound mute."""
        return await self.__remote("MUTE_TOGGLE", log_api_exception=log_api_exception)

    async def play(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously emulate 'play' key press."""
        return await self.__remote("PLAY", log_api_exception=log_api_exception)

    async def pause(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously emulate 'pause' key press."""
        return await self.__remote("PAUSE", log_api_exception=log_api_exception)

    async def remote(self, key: str, log_api_exception: bool = True) -> bool | None:
        """Asynchronously emulate key press by key name."""
        return await self.__remote(key, log_api_exception=log_api_exception)

    def get_remote_keys_list(self) -> KeysView[str]:
        """Get list of remote key names."""
        return KEY_CODE[self.device_type].keys()

    async def get_setting_types_list(
        self, log_api_exception: bool = True
    ) -> list[str] | None:
        """Asynchronously get list of all setting types."""
        items = await self.__invoke_api_may_need_auth(
            GetAllSettingTypesCommand(self.device_type),
            log_api_exception=log_api_exception,
        )

        if items:
            return items

        return None

    async def get_all_settings(
        self, setting_type: str, log_api_exception: bool = True
    ) -> dict[str, int | str] | None:
        """Asynchronously get all setting names and corresponding values."""
        item = await self.__invoke_api_may_need_auth(
            GetAllSettingsCommand(self.device_type, setting_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return item

        return None

    async def get_all_settings_options(
        self, setting_type: str, log_api_exception: bool = True
    ) -> dict[str, list[str] | dict[str, int | None]] | None:
        """Asynchronously get all setting names and corresponding options."""
        item = await self.__invoke_api_may_need_auth(
            GetAllSettingsOptionsCommand(self.device_type, setting_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return item

        return None

    async def get_all_settings_options_xlist(
        self, setting_type: str, log_api_exception: bool = True
    ) -> dict[str, list[str]] | None:
        """Asynchronously get all setting names and corresponding options for settings that are based on a user defined list."""
        item = await self.__invoke_api_may_need_auth(
            GetAllSettingsOptionsXListCommand(self.device_type, setting_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return item

        return None

    async def get_setting(
        self, setting_type: str, setting_name: str, log_api_exception: bool = True
    ) -> int | str | None:
        """Asynchronously get current value of named setting."""
        item = await self.__invoke_api_may_need_auth(
            GetSettingCommand(self.device_type, setting_type, setting_name),
            log_api_exception=log_api_exception,
        )

        # coerce to int if possible
        if item:
            try:
                return int(item.value)
            except ValueError:
                return item.value

        return None

    async def get_setting_options(
        self, setting_type: str, setting_name: str, log_api_exception: bool = True
    ) -> list[str] | dict[str, int | None] | None:
        """Asynchronously get options of named setting."""
        return await self.__invoke_api_may_need_auth(
            GetSettingOptionsCommand(self.device_type, setting_type, setting_name),
            log_api_exception=log_api_exception,
        )

    async def get_setting_options_xlist(
        self, setting_type: str, setting_name: str, log_api_exception: bool = True
    ) -> list[str] | None:
        """Asynchronously get options of named setting for settings based on a user defined list."""
        return await self.__invoke_api_may_need_auth(
            GetSettingOptionsXListCommand(self.device_type, setting_type, setting_name),
            log_api_exception=log_api_exception,
        )

    async def set_setting(
        self,
        setting_type: str,
        setting_name: str,
        new_value: int | str,
        log_api_exception: bool = True,
    ) -> bool | None:
        """Asynchronously set new value for setting."""
        setting_item = await self.__invoke_api_may_need_auth(
            GetSettingCommand(self.device_type, setting_type, setting_name),
            log_api_exception=log_api_exception,
        )

        if not setting_item or not hasattr(setting_item, "id"):
            _LOGGER.error(
                "Couldn't detect setting for %s of setting type %s",
                setting_name,
                setting_type,
            )
            return None

        return await self.__invoke_api_may_need_auth(
            ChangeSettingCommand(
                self.device_type, setting_item.id, setting_type, setting_name, new_value
            ),
            log_api_exception=log_api_exception,
        )

    async def get_all_audio_settings(
        self, log_api_exception: bool = True
    ) -> dict[str, int | str] | None:
        """Asynchronously get all audio setting names and corresponding values."""
        return await VizioAsync.get_all_settings(
            self, "audio", log_api_exception=log_api_exception
        )

    async def get_all_audio_settings_options(
        self, log_api_exception: bool = True
    ) -> dict[str, list[str] | dict[str, int | None]] | None:
        """Asynchronously get all audio setting names and corresponding options."""
        return await VizioAsync.get_all_settings_options(
            self, "audio", log_api_exception=log_api_exception
        )

    async def get_audio_setting(
        self, setting_name: str, log_api_exception: bool = True
    ) -> int | str | None:
        """Asynchronously get current value of named audio setting."""
        return await VizioAsync.get_setting(
            self, "audio", setting_name, log_api_exception=log_api_exception
        )

    async def get_audio_setting_options(
        self, setting_name: str, log_api_exception: bool = True
    ) -> list[str] | dict[str, int | None] | None:
        """Asynchronously get options of named audio setting."""
        return await VizioAsync.get_setting_options(
            self, "audio", setting_name, log_api_exception=log_api_exception
        )

    async def set_audio_setting(
        self,
        setting_name: str,
        new_value: int | str,
        log_api_exception: bool = True,
    ) -> bool | None:
        """Asynchronously set new value for named audio setting."""
        return await VizioAsync.set_setting(
            self, "audio", setting_name, new_value, log_api_exception=log_api_exception
        )

    @staticmethod
    async def get_apps_list(
        country: str = "all",
        apps_list: list[dict[str, Any]] | None = None,
        session: ClientSession | None = None,
    ) -> list[str]:
        """Get list of known apps by name optionally filtered by supported country."""
        # Assumes "*" means all countries are supported
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
        log_api_exception: bool = True,
    ) -> bool | None:
        """Asynchronously launch known app by name."""
        if not apps_list:
            apps_list = await self.__get_cached_apps_list()

        return await self.__invoke_api_may_need_auth(
            LaunchAppNameCommand(self.device_type, app_name, apps_list),
            log_api_exception=log_api_exception,
        )

    async def launch_app_config(
        self,
        APP_ID: str,
        NAME_SPACE: int,
        MESSAGE: str | None = None,
        log_api_exception: bool = True,
    ) -> bool | None:
        """Asynchronously launch app using app's config values."""
        return await self.__invoke_api_may_need_auth(
            LaunchAppConfigCommand(self.device_type, APP_ID, NAME_SPACE, MESSAGE),
            log_api_exception=log_api_exception,
        )

    async def get_current_app(
        self,
        apps_list: list[dict[str, Any]] | None = None,
        log_api_exception: bool = True,
    ) -> str | None:
        """Asynchronously get name of currently running app. Returns const APP_NOT_RUNNING if no app is currently running, const UNKNOWN_APP if app config isn't known by pyvizio."""
        if not apps_list:
            apps_list = await self.__get_cached_apps_list()

        return await self.__invoke_api_may_need_auth(
            GetCurrentAppNameCommand(self.device_type, apps_list),
            log_api_exception=log_api_exception,
        )

    async def get_current_app_config(
        self, log_api_exception: bool = True
    ) -> AppConfig | None:
        """Asynchronously get config values of currently running app. Returns empty AppConfig if no app is currently running."""
        return await self.__invoke_api_may_need_auth(
            GetCurrentAppConfigCommand(self.device_type),
            log_api_exception=log_api_exception,
        )


async def async_guess_device_type(
    ip: str, port: str | None = None, timeout: int = DEFAULT_TIMEOUT
) -> str:
    """
    Attempt to guess the device type by getting power state with no auth
    token.

    NOTE:
    The `ip` and `port` values passed in have to be valid for the device in
    order for this to work. This function is being used as part of a zeroconf
    discovery workflow in HomeAssistant which is why it is safe to assume that
    `ip` and `port` are valid.
    """

    if port:
        if ":" in ip:
            raise VizioInvalidParameterError(
                "Port can't be included in both `ip` and `port` parameters"
            )

        device = VizioAsync(
            "test", f"{ip}:{port}", "test", "", DEVICE_CLASS_SPEAKER, timeout=timeout
        )
    else:
        if ":" not in ip:
            _LOGGER.warning(
                "May not return correct device type since a port was not specified."
            )
        device = VizioAsync(
            "test", ip, "test", "", DEVICE_CLASS_SPEAKER, timeout=timeout
        )

    if await device.can_connect_with_auth_check():
        return DEVICE_CLASS_SPEAKER
    else:
        return DEVICE_CLASS_TV


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
        """Return whether or not HomeAssistant config will allow HomeAssistant to make successful calls to Vizio SmartCast API."""
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
        if isinstance(raw, (staticmethod, classmethod)):
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
        def ch_down(self, num: int = 1, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def ch_prev(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def ch_up(self, num: int = 1, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def get_all_audio_settings(self, log_api_exception: bool = True) -> dict[str, int | str] | None: ...  # type: ignore[override]
        def get_all_audio_settings_options(self, log_api_exception: bool = True) -> dict[str, list[str] | dict[str, int | None]] | None: ...  # type: ignore[override]
        def get_all_settings(self, setting_type: str, log_api_exception: bool = True) -> dict[str, int | str] | None: ...  # type: ignore[override]
        def get_all_settings_options(self, setting_type: str, log_api_exception: bool = True) -> dict[str, list[str] | dict[str, int | None]] | None: ...  # type: ignore[override]
        def get_all_settings_options_xlist(self, setting_type: str, log_api_exception: bool = True) -> dict[str, list[str]] | None: ...  # type: ignore[override]
        def get_audio_setting(self, setting_name: str, log_api_exception: bool = True) -> int | str | None: ...  # type: ignore[override]
        def get_audio_setting_options(self, setting_name: str, log_api_exception: bool = True) -> list[str] | dict[str, int | None] | None: ...  # type: ignore[override]
        def get_battery_level(self, log_api_exception: bool = True) -> int | None: ...  # type: ignore[override]
        def get_charging_status(self, log_api_exception: bool = True) -> int | None: ...  # type: ignore[override]
        def get_current_app(self, apps_list: list[dict[str, Any]] | None = None, log_api_exception: bool = True) -> str | None: ...  # type: ignore[override]
        def get_current_app_config(self, log_api_exception: bool = True) -> AppConfig | None: ...  # type: ignore[override]
        def get_current_input(self, log_api_exception: bool = True) -> str | None: ...  # type: ignore[override]
        def get_current_volume(self, log_api_exception: bool = True) -> int | None: ...  # type: ignore[override]
        def get_esn(self, log_api_exception: bool = True) -> str | None: ...  # type: ignore[override]
        def get_inputs_list(self, log_api_exception: bool = True) -> list[InputItem] | None: ...  # type: ignore[override]
        def get_model_name(self, log_api_exception: bool = True) -> str | None: ...  # type: ignore[override]
        def get_power_state(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def get_serial_number(self, log_api_exception: bool = True) -> str | None: ...  # type: ignore[override]
        def get_setting(self, setting_type: str, setting_name: str, log_api_exception: bool = True) -> int | str | None: ...  # type: ignore[override]
        def get_setting_options(self, setting_type: str, setting_name: str, log_api_exception: bool = True) -> list[str] | dict[str, int | None] | None: ...  # type: ignore[override]
        def get_setting_options_xlist(self, setting_type: str, setting_name: str, log_api_exception: bool = True) -> list[str] | None: ...  # type: ignore[override]
        def get_setting_types_list(self, log_api_exception: bool = True) -> list[str] | None: ...  # type: ignore[override]
        def get_state_extended(self, log_api_exception: bool = True) -> StateExtended | None: ...  # type: ignore[override]
        def get_version(self, log_api_exception: bool = True) -> str | None: ...  # type: ignore[override]
        def is_muted(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def launch_app(self, app_name: str, apps_list: list[dict[str, Any]] | None = None, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def launch_app_config(self, APP_ID: str, NAME_SPACE: int, MESSAGE: str | None = None, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def mute_off(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def mute_on(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def mute_toggle(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def next_input(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def pair(self, ch_type: int | str, token: int | str, pin: str = "", log_api_exception: bool = True) -> PairChallengeResponse | None: ...  # type: ignore[override]
        def pause(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def play(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def pow_off(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def pow_on(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def pow_toggle(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def remote(self, key: str, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def set_audio_setting(self, setting_name: str, new_value: int | str, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def set_input(self, name: str, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def set_setting(self, setting_type: str, setting_name: str, new_value: int | str, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def start_pair(self, log_api_exception: bool = True) -> BeginPairResponse | None: ...  # type: ignore[override]
        def stop_pair(self, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def vol_down(self, num: int = 1, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
        def vol_up(self, num: int = 1, log_api_exception: bool = True) -> bool | None: ...  # type: ignore[override]
    # fmt: on


@async_to_sync
async def guess_device_type(
    ip: str, port: str | None = None, timeout: int = DEFAULT_TIMEOUT
) -> str:
    """
    Attempt to guess the device type by getting power state with no auth
    token.

    NOTE:
    The `ip` and `port` values passed in have to be valid for the device in
    order for this to work. This function is being used as part of a zeroconf
    discovery workflow in HomeAssistant which is why it is safe to assume that
    `ip` and `port` are valid.
    """

    return await async_guess_device_type(ip, port, timeout)
