"""Initialize pyvizio."""

from __future__ import annotations

import asyncio
from asyncio import sleep
from collections.abc import KeysView
from datetime import datetime, timedelta
from functools import wraps
import logging
from typing import Any
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
    VizioConnectionError as VizioConnectionError,
    VizioError,
    VizioInvalidParameterError as VizioInvalidParameterError,
    VizioResponseError as VizioResponseError,
)
from pyvizio.helpers import async_to_sync, open_port
from pyvizio.util import gen_apps_list_from_url
from pyvizio.version import __version__ as __version__

_LOGGER = logging.getLogger(__name__)


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
            raise VizioError(
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
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._latest_apps = None
        self._latest_apps_last_updated = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        exclude = {"_semaphore"}
        self_d = {k: v for k, v in self.__dict__.items() if k not in exclude}
        other_d = {k: v for k, v in other.__dict__.items() if k not in exclude}
        return self_d == other_d

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
        self, cmd: CommandBase, log_api_exception: bool = True
    ) -> Any:
        """Asynchronously call SmartCast API without auth token."""
        if ":" not in self.ip:
            await self.__add_port()

        async with self._semaphore:
            return await async_invoke_api(
                self.ip,
                cmd,
                _LOGGER,
                custom_timeout=self._timeout,
                log_api_exception=log_api_exception,
                session=self._session,
            )

    async def __invoke_api_auth(
        self, cmd: CommandBase, log_api_exception: bool = True
    ) -> Any:
        """Asynchronously call SmartCast API with auth token."""
        if ":" not in self.ip:
            await self.__add_port()

        async with self._semaphore:
            return await async_invoke_api_auth(
                self.ip,
                cmd,
                _LOGGER,
                auth_token=self._auth_token,
                custom_timeout=self._timeout,
                log_api_exception=log_api_exception,
                session=self._session,
            )

    async def __invoke_api_may_need_auth(
        self, cmd: CommandBase, log_api_exception: bool = True
    ) -> Any:
        """Asynchronously call SmartCast API command with or without auth token depending on device type."""
        if not self._auth_token:
            if not self._device_config.requires_auth:
                return await self.__invoke_api(cmd, log_api_exception=log_api_exception)
            else:
                no_auth_types = [
                    k for k, v in DEVICE_CONFIGS.items() if not v.requires_auth
                ]
                raise VizioAuthError(
                    f"Empty auth token. Device types that don't require auth: "
                    f"{', '.join(repr(t) for t in no_auth_types)}"
                )
        return await self.__invoke_api_auth(cmd, log_api_exception=log_api_exception)

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

    async def __get_cached_apps_list(self) -> list[str]:
        if (
            self._latest_apps
            and datetime.now() - self._latest_apps_last_updated < timedelta(days=1)
        ):
            await sleep(0)
            return self._latest_apps
        else:
            self._latest_apps = (
                await gen_apps_list_from_url(session=self._session) or APPS
            )
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
        """Asynchronously return whether or not device API can be connected to with valid authorization."""
        return bool(
            await VizioAsync.get_all_audio_settings(self, log_api_exception=False)
        )

    async def can_connect_no_auth_check(self) -> bool:
        """Asynchronously return whether or not device API can be connected to regardless of authorization."""
        return bool(
            await self.__invoke_api(
                GetDeviceInfoCommand(self.device_type), log_api_exception=False
            )
        )

    async def get_esn(self, log_api_exception: bool = True) -> str | None:
        """Asynchronously get device's ESN (electronic serial number?)."""
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
        """Asynchronously get device's serial number."""
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
        """Asynchronously get SmartCast software version on device."""
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
        """Asynchronously switch active input to named input."""
        curr_input_item = await self.__invoke_api_may_need_auth(
            GetCurrentInputCommand(self.device_type),
            log_api_exception=log_api_exception,
        )

        if not curr_input_item:
            _LOGGER.error("Couldn't detect current input")
            return None

        return await self.__invoke_api_may_need_auth(
            ChangeInputCommand(self.device_type, curr_input_item.id, name),
            log_api_exception=log_api_exception,
        )

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
        """Asynchronously determine whether or not device is muted."""
        # If None is returned lower() will fail, if not we can do a simple boolean check
        try:
            return (
                str(
                    await VizioAsync.get_audio_setting(
                        self, "mute", log_api_exception=log_api_exception
                    )
                ).lower()
                == "on"
            )
        except AttributeError:
            return None

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
        """Asynchronously mute sound."""
        return await self.__remote("MUTE_ON", log_api_exception=log_api_exception)

    async def mute_off(self, log_api_exception: bool = True) -> bool | None:
        """Asynchronously unmute sound."""
        return await self.__remote("MUTE_OFF", log_api_exception=log_api_exception)

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
    ) -> dict[str, int | str] | None:
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
    ) -> dict[str, int | str] | None:
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
    ) -> list[str] | dict[str, int | str] | None:
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
    ) -> dict[str, int | str] | None:
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
    ) -> list[str] | dict[str, int | str] | None:
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
        apps_list: list[dict[str, str | list[str | dict[str, Any]]]] = None,
        session: ClientSession = None,
    ) -> list[str]:
        """Get list of known apps by name optionally filtered by supported country."""
        # Assumes "*" means all countries are supported
        if not apps_list:
            apps_list = await gen_apps_list_from_url(session=session) or APPS

        if country.lower() != "all":
            return [
                APP_HOME["name"],
                *sorted(
                    [
                        str(app["name"])
                        for app in apps_list
                        if "*" in app["country"] or country.lower() in app["country"]
                    ]
                ),
            ]

        return [APP_HOME["name"], *sorted([str(app["name"]) for app in apps_list])]

    async def launch_app(
        self,
        app_name: str,
        apps_list: list[dict[str, str | list[str | dict[str, Any]]]] = None,
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
        MESSAGE: str = None,
        log_api_exception: bool = True,
    ) -> bool | None:
        """Asynchronously launch app using app's config values."""
        return await self.__invoke_api_may_need_auth(
            LaunchAppConfigCommand(self.device_type, APP_ID, NAME_SPACE, MESSAGE),
            log_api_exception=log_api_exception,
        )

    async def get_current_app(
        self,
        apps_list: list[dict[str, str | list[str | dict[str, Any]]]] = None,
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
            raise VizioError(
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
    ) -> None:
        """Initialize synchronous class to interact with Vizio SmartCast devices."""
        super().__init__(
            device_id, ip, name, auth_token, device_type, session=None, timeout=timeout
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
        apps_list: list[dict[str, str | list[str | dict[str, Any]]]] = None,
        session: ClientSession = None,
    ) -> list[str]:
        """Get list of known apps by name optionally filtered by supported country."""
        return await super(Vizio, Vizio).get_apps_list(
            country=country, apps_list=apps_list, session=session
        )


def _make_sync_method(name: str):
    """Create a sync wrapper for an async VizioAsync method."""
    async_method = getattr(VizioAsync, name)

    @wraps(async_method)
    def sync_method(self, *args, **kwargs):
        return asyncio.run(async_method(self, *args, **kwargs))

    return sync_method


# Auto-wrap all public async instance methods from VizioAsync onto Vizio
for _name in list(vars(VizioAsync)):
    if _name.startswith("_"):
        continue
    _attr = getattr(VizioAsync, _name)
    if asyncio.iscoroutinefunction(_attr) and _name not in vars(Vizio):
        setattr(Vizio, _name, _make_sync_method(_name))


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
