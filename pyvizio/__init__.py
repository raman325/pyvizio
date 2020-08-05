"""Initialize pyvizio."""
import logging
from typing import Any, Dict, List, Optional, Union
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
    GetCurrentPowerStateCommand,
    GetDeviceInfoCommand,
    GetESNCommand,
    GetModelNameCommand,
    GetSerialNumberCommand,
    GetVersionCommand,
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
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
    MAX_VOLUME,
)
from pyvizio.discovery.ssdp import SSDPDevice, discover as discover_ssdp
from pyvizio.discovery.zeroconf import ZeroconfDevice, discover as discover_zc
from pyvizio.helpers import async_to_sync, open_port
from pyvizio.util import gen_apps_list_from_url

_LOGGER = logging.getLogger(__name__)


class VizioAsync:
    """Asynchronous class to interact with Vizio SmartCast devices."""

    def __init__(
        self,
        device_id: str,
        ip: str,
        name: str,
        auth_token: str = "",
        device_type: str = DEFAULT_DEVICE_CLASS,
        session: Optional[ClientSession] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize asynchronous class to interact with Vizio SmartCast devices."""
        self.device_type = device_type.lower()
        if (
            self.device_type != DEVICE_CLASS_TV
            and self.device_type != DEVICE_CLASS_SPEAKER  # noqa: W503
        ):
            raise Exception(
                f"Invalid device type specified. Use either '{DEVICE_CLASS_TV}' or "
                f"'{DEVICE_CLASS_SPEAKER}'"
            )

        self._auth_token = auth_token
        self.ip = ip
        self.name = name
        self.device_id = device_id
        self._session = session
        self._timeout = timeout

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__

    async def __add_port(self) -> None:
        """Asynchronously add first open port from known ports list to `ip` property."""
        for port in DEFAULT_PORTS:
            if await open_port(self.ip, port):
                self.ip = f"{self.ip}:{port}"

    async def __invoke_api(
        self, cmd: CommandBase, log_api_exception: bool = True
    ) -> Any:
        """Asynchronously call SmartCast API without auth token."""
        if ":" not in self.ip:
            await self.__add_port()

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
            if self.device_type == DEVICE_CLASS_SPEAKER:
                return await self.__invoke_api(cmd, log_api_exception=log_api_exception)
            else:
                raise Exception(
                    f"Empty auth token. To target a speaker and bypass auth "
                    f"requirements, pass '{DEVICE_CLASS_SPEAKER}' as device_type"
                )
        return await self.__invoke_api_auth(cmd, log_api_exception=log_api_exception)

    async def __remote(
        self, key_list: Union[str, List[str]], log_api_exception: bool = True
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

    @staticmethod
    def discovery_zeroconf(timeout: int = DEFAULT_TIMEOUT) -> List[ZeroconfDevice]:
        """Discover Vizio devices on network using zeroconf."""
        results = discover_zc("_viziocast._tcp.local.", timeout=timeout)
        _LOGGER.info(results)
        return results

    @staticmethod
    def discovery_ssdp(timeout: int = DEFAULT_TIMEOUT) -> List[SSDPDevice]:
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
        session: Optional[ClientSession] = None,
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
        session: Optional[ClientSession] = None,
    ) -> Optional[str]:
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

    async def get_esn(self, log_api_exception: bool = True) -> Optional[str]:
        """Asynchronously get device's ESN (electronic serial number?)."""
        item = await self.__invoke_api_may_need_auth(
            GetESNCommand(self.device_type), log_api_exception=log_api_exception
        )

        if item:
            return item.value

        return None

    async def get_serial_number(self, log_api_exception: bool = True) -> Optional[str]:
        """Asynchronously get device's serial number."""
        item = await self.__invoke_api(
            GetSerialNumberCommand(self.device_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return item.value

        return None

    async def get_version(self, log_api_exception: bool = True) -> Optional[str]:
        """Asynchronously get SmartCast software version on device."""
        item = await self.__invoke_api(
            GetVersionCommand(self.device_type), log_api_exception=log_api_exception
        )

        if item:
            return item.value

        return None

    async def get_model_name(self, log_api_exception: bool = True) -> Optional[str]:
        """Asynchronously get device's model number."""
        return await self.__invoke_api(
            GetModelNameCommand(self.device_type), log_api_exception=log_api_exception
        )

    async def start_pair(
        self, log_api_exception: bool = True
    ) -> Optional[BeginPairResponse]:
        """Asynchronously begin pairing process to obtain challenge type and challenge token."""
        return await self.__invoke_api(
            BeginPairCommand(self.device_id, self.name, self.device_type),
            log_api_exception=log_api_exception,
        )

    async def stop_pair(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously cancel pairing process."""
        return await self.__invoke_api(
            CancelPairCommand(self.device_id, self.name, self.device_type),
            log_api_exception=log_api_exception,
        )

    async def pair(
        self, ch_type: int, token: int, pin: str = "", log_api_exception: bool = True
    ) -> Optional[PairChallengeResponse]:
        """Asynchronously complete pairing process to obtain auth token."""
        if self.device_type == DEVICE_CLASS_SPEAKER:
            pin = "0000"
        return await self.__invoke_api(
            PairChallengeCommand(self.device_id, ch_type, token, pin, self.device_type),
            log_api_exception=log_api_exception,
        )

    async def get_inputs_list(
        self, log_api_exception: bool = True
    ) -> Optional[List[InputItem]]:
        """Asynchronously get list of available inputs."""
        return await self.__invoke_api_may_need_auth(
            GetInputsListCommand(self.device_type), log_api_exception=log_api_exception
        )

    async def get_current_input(self, log_api_exception: bool = True) -> Optional[str]:
        """Asynchronously get device's active input."""
        item = await self.__invoke_api_may_need_auth(
            GetCurrentInputCommand(self.device_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return item.meta_name

        return None

    async def next_input(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously switch active input to next input."""
        # HACK: Single call just invoking overlay menu with current input
        return await self.__remote_multiple(
            "INPUT_NEXT", 2, log_api_exception=log_api_exception
        )

    async def set_input(
        self, name: str, log_api_exception: bool = True
    ) -> Optional[bool]:
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

    async def get_power_state(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously get device's current power state."""
        item = await self.__invoke_api_may_need_auth(
            GetCurrentPowerStateCommand(self.device_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return bool(item.value)

        return None

    async def pow_on(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously power device on."""
        return await self.__remote("POW_ON", log_api_exception=log_api_exception)

    async def pow_off(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously power device off."""
        return await self.__remote("POW_OFF", log_api_exception=log_api_exception)

    async def pow_toggle(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously toggle device power."""
        return await self.__remote("POW_TOGGLE", log_api_exception=log_api_exception)

    async def vol_up(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        """Asynchronously increase volume by number of steps."""
        return await self.__remote_multiple(
            "VOL_UP", num, log_api_exception=log_api_exception
        )

    async def vol_down(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        """Asynchronously decrease volume by number of steps."""
        return await self.__remote_multiple(
            "VOL_DOWN", num, log_api_exception=log_api_exception
        )

    async def get_current_volume(self, log_api_exception: bool = True) -> Optional[int]:
        """Asynchronously get device's current volume level."""
        return await VizioAsync.get_audio_setting(
            self, "volume", log_api_exception=log_api_exception
        )

    async def is_muted(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously determine whether or not device is muted."""
        # If None is returned lower() will fail, if not we can do a simple boolean check
        try:
            return (
                await VizioAsync.get_audio_setting(
                    self, "mute", log_api_exception=log_api_exception
                ).lower()
                == "on"
            )
        except AttributeError:
            return None

    def get_max_volume(self) -> int:
        """Get device's max volume based on device type."""
        return MAX_VOLUME[self.device_type]

    async def ch_up(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        """Asynchronously channel up by number of steps."""
        return await self.__remote_multiple(
            "CH_UP", num, log_api_exception=log_api_exception
        )

    async def ch_down(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        """Asynchronously channel down by number of steps."""
        return await self.__remote_multiple(
            "CH_DOWN", num, log_api_exception=log_api_exception
        )

    async def ch_prev(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously go to previous channel."""
        return await self.__remote("CH_PREV", log_api_exception=log_api_exception)

    async def mute_on(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously mute sound."""
        return await self.__remote("MUTE_ON", log_api_exception=log_api_exception)

    async def mute_off(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously unmute sound."""
        return await self.__remote("MUTE_OFF", log_api_exception=log_api_exception)

    async def mute_toggle(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously toggle sound mute."""
        return await self.__remote("MUTE_TOGGLE", log_api_exception=log_api_exception)

    async def play(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously emulate 'play' key press."""
        return await self.__remote("PLAY", log_api_exception=log_api_exception)

    async def pause(self, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously emulate 'pause' key press."""
        return await self.__remote("PAUSE", log_api_exception=log_api_exception)

    async def remote(self, key: str, log_api_exception: bool = True) -> Optional[bool]:
        """Asynchronously emulate key press by key name."""
        return await self.__remote(key, log_api_exception=log_api_exception)

    def get_remote_keys_list(self) -> List[str]:
        """Get list of remote key names."""
        return KEY_CODE[self.device_type].keys()

    async def get_setting_types_list(
        self, log_api_exception: bool = True
    ) -> Optional[List[str]]:
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
    ) -> Optional[Dict[str, Union[int, str]]]:
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
    ) -> Optional[Dict[str, Union[int, str]]]:
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
    ) -> Optional[Dict[str, Union[int, str]]]:
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
    ) -> Optional[Union[int, str]]:
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
    ) -> Optional[Union[int, str]]:
        """Asynchronously get options of named setting."""
        return await self.__invoke_api_may_need_auth(
            GetSettingOptionsCommand(self.device_type, setting_type, setting_name),
            log_api_exception=log_api_exception,
        )

    async def get_setting_options_xlist(
        self, setting_type: str, setting_name: str, log_api_exception: bool = True
    ) -> Optional[Union[int, str]]:
        """Asynchronously get options of named setting for settings based on a user defined list."""
        return await self.__invoke_api_may_need_auth(
            GetSettingOptionsXListCommand(self.device_type, setting_type, setting_name),
            log_api_exception=log_api_exception,
        )

    async def set_setting(
        self,
        setting_type: str,
        setting_name: str,
        new_value: Union[int, str],
        log_api_exception: bool = True,
    ) -> Optional[bool]:
        """Asynchronously set new value for setting."""
        setting_item = await self.__invoke_api_may_need_auth(
            GetSettingCommand(self.device_type, setting_type, setting_name),
            log_api_exception=log_api_exception,
        )

        if not setting_item:
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
    ) -> Optional[Dict[str, Union[int, str]]]:
        """Asynchronously get all audio setting names and corresponding values."""
        return await VizioAsync.get_all_settings(
            self, "audio", log_api_exception=log_api_exception
        )

    async def get_all_audio_settings_options(
        self, log_api_exception: bool = True
    ) -> Optional[Dict[str, Union[int, str]]]:
        """Asynchronously get all audio setting names and corresponding options."""
        return await VizioAsync.get_all_settings_options(
            self, "audio", log_api_exception=log_api_exception
        )

    async def get_audio_setting(
        self, setting_name: str, log_api_exception: bool = True
    ) -> Optional[Union[int, str]]:
        """Asynchronously get current value of named audio setting."""
        return await VizioAsync.get_setting(
            self, "audio", setting_name, log_api_exception=log_api_exception
        )

    async def get_audio_setting_options(
        self, setting_name: str, log_api_exception: bool = True
    ) -> Optional[Union[int, str]]:
        """Asynchronously get options of named audio setting."""
        return await VizioAsync.get_setting_options(
            self, "audio", setting_name, log_api_exception=log_api_exception
        )

    async def set_audio_setting(
        self,
        setting_name: str,
        new_value: Union[int, str],
        log_api_exception: bool = True,
    ) -> Optional[bool]:
        """Asynchronously set new value for named audio setting."""
        return await VizioAsync.set_setting(
            self, "audio", setting_name, new_value, log_api_exception=log_api_exception
        )

    @staticmethod
    async def get_apps_list(country: str = "all", session: ClientSession = None) -> List[str]:
        """Get list of known apps by name optionally filtered by supported country."""
        # Assumes "*" means all countries are supported
        apps_list = await gen_apps_list_from_url(session=session)
        # Fallback to local list of apps if needed
        if not apps_list:
            apps_list = APPS

        if country.lower() != "all":
            return [
                APP_HOME["name"],
                *sorted(
                    [
                        app["name"]
                        for app in apps_list
                        if "*" in app["country"] or country.lower() in app["country"]
                    ]
                ),
            ]

        return [APP_HOME["name"], *sorted([app["name"] for app in apps_list])]

    async def launch_app(
        self,
        app_name: str,
        apps_list: List[Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]],
        log_api_exception: bool = True,
    ) -> Optional[bool]:
        """Asynchronously launch known app by name."""
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
    ) -> Optional[bool]:
        """Asynchronously launch app using app's config values."""
        return await self.__invoke_api_may_need_auth(
            LaunchAppConfigCommand(self.device_type, APP_ID, NAME_SPACE, MESSAGE),
            log_api_exception=log_api_exception,
        )

    async def get_current_app(
        self,
        apps_list: List[Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]],
        log_api_exception: bool = True,
    ) -> Optional[str]:
        """Asynchronously get name of currently running app. Returns const APP_NOT_RUNNING if no app is currently running, const UNKNOWN_APP if app config isn't known by pyvizio."""
        return await self.__invoke_api_may_need_auth(
            GetCurrentAppNameCommand(self.device_type, apps_list),
            log_api_exception=log_api_exception,
        )

    async def get_current_app_config(
        self, log_api_exception: bool = True
    ) -> Optional[AppConfig]:
        """Asynchronously get config values of currently running app. Returns empty AppConfig if no app is currently running."""
        return await self.__invoke_api_may_need_auth(
            GetCurrentAppConfigCommand(self.device_type),
            log_api_exception=log_api_exception,
        )


async def async_guess_device_type(
    ip: str, port: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT
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
            raise Exception("Port can't be included in both `ip` and `port` parameters")

        device = VizioAsync(
            "test", ip + ":" + port, "test", "", DEVICE_CLASS_SPEAKER, timeout=timeout
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
    """Synchronous class to interact with Vizio SmartCast devices."""

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
        super(Vizio, self).__init__(
            device_id, ip, name, auth_token, device_type, session=None, timeout=timeout
        )

    @staticmethod
    def discovery_zeroconf(timeout: int = DEFAULT_TIMEOUT) -> List[ZeroconfDevice]:
        """Discover Vizio devices on network using zeroconf."""
        return super(Vizio, Vizio).discovery_zeroconf(timeout)

    @staticmethod
    def discovery_ssdp(timeout: int = DEFAULT_TIMEOUT) -> List[SSDPDevice]:
        """Discover Vizio devices on network using SSDP."""
        return super(Vizio, Vizio).discovery_ssdp(timeout)

    @staticmethod
    @async_to_sync
    async def validate_ha_config(
        ip: str,
        auth_token: str,
        device_type: str,
        session: Optional[ClientSession] = None,
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
    ) -> Optional[str]:
        """Get unique identifier for Vizio device."""
        return await super(Vizio, Vizio).get_unique_id(ip, device_type, timeout=timeout)

    @async_to_sync
    async def can_connect_with_auth_check(self) -> bool:
        """Return whether or not device API can be connected to with valid authorization."""
        return await super(Vizio, self).can_connect_with_auth_check()

    @async_to_sync
    async def can_connect_no_auth_check(self) -> bool:
        """Return whether or not device API can be connected to regardless of auth config."""
        return await super(Vizio, self).can_connect_no_auth_check()

    @async_to_sync
    async def get_esn(self, log_api_exception: bool = True) -> Optional[str]:
        """Get device's ESN (electronic serial number?)."""
        return await super(Vizio, self).get_esn(log_api_exception=log_api_exception)

    @async_to_sync
    async def get_serial_number(self, log_api_exception: bool = True) -> Optional[str]:
        """Get device's serial number."""
        return await super(Vizio, self).get_serial_number(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_version(self, log_api_exception: bool = True) -> Optional[str]:
        """Get SmartCast software version on device."""
        return await super(Vizio, self).get_version(log_api_exception=log_api_exception)

    @async_to_sync
    async def get_model_name(self, log_api_exception: bool = True) -> Optional[str]:
        """Get device's model number."""
        return await super(Vizio, self).get_model_name(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def start_pair(
        self, log_api_exception: bool = True
    ) -> Optional[BeginPairResponse]:
        """Begin pairing process to obtain challenge type and challenge token."""
        return await super(Vizio, self).start_pair(log_api_exception=log_api_exception)

    @async_to_sync
    async def stop_pair(self, log_api_exception: bool = True) -> Optional[bool]:
        """Cancel pairing process."""
        return await super(Vizio, self).stop_pair(log_api_exception=log_api_exception)

    @async_to_sync
    async def pair(
        self, ch_type: int, token: int, pin: str, log_api_exception: bool = True
    ) -> Optional[PairChallengeResponse]:
        """Complete pairing process to obtain auth token."""
        return await super(Vizio, self).pair(
            ch_type, token, pin, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_inputs_list(
        self, log_api_exception: bool = True
    ) -> Optional[List[InputItem]]:
        """Get list of available inputs."""
        return await super(Vizio, self).get_inputs_list(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_current_input(self, log_api_exception: bool = True) -> Optional[str]:
        """Get device's active input."""
        return await super(Vizio, self).get_current_input(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def next_input(self, log_api_exception: bool = True) -> Optional[bool]:
        """Switch active input to next input."""
        return await super(Vizio, self).next_input(log_api_exception=log_api_exception)

    @async_to_sync
    async def set_input(
        self, name: str, log_api_exception: bool = True
    ) -> Optional[bool]:
        """Switch active input to named input."""
        return await super(Vizio, self).set_input(
            name, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_power_state(self, log_api_exception: bool = True) -> Optional[bool]:
        """Get device's current power state."""
        return await super(Vizio, self).get_power_state(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def pow_on(self, log_api_exception: bool = True) -> Optional[bool]:
        """Power device off."""
        return await super(Vizio, self).pow_on(log_api_exception=log_api_exception)

    @async_to_sync
    async def pow_off(self, log_api_exception: bool = True) -> Optional[bool]:
        """Power device off."""
        return await super(Vizio, self).pow_off(log_api_exception=log_api_exception)

    @async_to_sync
    async def pow_toggle(self, log_api_exception: bool = True) -> Optional[bool]:
        """Toggle device power."""
        return await super(Vizio, self).pow_toggle(log_api_exception=log_api_exception)

    @async_to_sync
    async def vol_up(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        """Increase volume by number of steps."""
        return await super(Vizio, self).vol_up(num, log_api_exception=log_api_exception)

    @async_to_sync
    async def vol_down(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        """Decrease volume by number of steps."""
        return await super(Vizio, self).vol_down(
            num, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_current_volume(self, log_api_exception: bool = True) -> Optional[int]:
        """Get device's current volume level."""
        return await super(Vizio, self).get_current_volume(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def is_muted(self, log_api_exception: bool = True) -> Optional[bool]:
        """Return whether or not device is muted."""
        return await super(Vizio, self).is_muted(log_api_exception=log_api_exception)

    def get_max_volume(self) -> int:
        """Return device's max volume based on device type."""
        return super(Vizio, self).get_max_volume()

    @async_to_sync
    async def ch_up(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        """Channel up by number of steps."""
        return await super(Vizio, self).ch_up(num, log_api_exception=log_api_exception)

    @async_to_sync
    async def ch_down(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        """Channel down by number of steps."""
        return await super(Vizio, self).ch_down(
            num, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def ch_prev(self, log_api_exception: bool = True) -> Optional[bool]:
        """Go to previous channel."""
        return await super(Vizio, self).ch_prev(log_api_exception=log_api_exception)

    @async_to_sync
    async def mute_on(self, log_api_exception: bool = True) -> Optional[bool]:
        """Mute sound."""
        return await super(Vizio, self).mute_on(log_api_exception=log_api_exception)

    @async_to_sync
    async def mute_off(self, log_api_exception: bool = True) -> Optional[bool]:
        """Unmute sound."""
        return await super(Vizio, self).mute_off(log_api_exception=log_api_exception)

    @async_to_sync
    async def mute_toggle(self, log_api_exception: bool = True) -> Optional[bool]:
        """Toggle sound mute."""
        return await super(Vizio, self).mute_toggle(log_api_exception=log_api_exception)

    @async_to_sync
    async def play(self, log_api_exception: bool = True) -> Optional[bool]:
        """Emulate 'play' key press."""
        return await super(Vizio, self).play(log_api_exception=log_api_exception)

    @async_to_sync
    async def pause(self, log_api_exception: bool = True) -> Optional[bool]:
        """Emulate 'pause' key press."""
        return await super(Vizio, self).pause(log_api_exception=log_api_exception)

    @async_to_sync
    async def remote(self, key: str, log_api_exception: bool = True) -> Optional[bool]:
        """Emulate key press by key name."""
        return await super(Vizio, self).remote(key, log_api_exception=log_api_exception)

    def get_remote_keys_list(self) -> List[str]:
        """Get list of remote key names."""
        return super(Vizio, self).get_remote_keys_list()

    @async_to_sync
    async def get_setting_types_list(
        self, setting_type: str, log_api_exception: bool = True
    ) -> Optional[List[str]]:
        """Get list of all setting types."""
        return await super(Vizio, self).get_setting_types_list(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_all_settings(
        self, setting_type: str, log_api_exception: bool = True
    ) -> Optional[Dict[str, Union[int, str]]]:
        """Get all setting names and corresponding values."""
        return await super(Vizio, self).get_all_settings(
            setting_type, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_all_settings_options(
        self, setting_type: str, log_api_exception: bool = True
    ) -> Optional[Dict[str, Union[int, str]]]:
        """Get all setting names and corresponding options."""
        return await super(Vizio, self).get_all_settings_options(
            setting_type, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_setting(
        self, setting_type: str, setting_name: str, log_api_exception: bool = True
    ) -> Optional[Union[int, str]]:
        """Get current value of named setting."""
        return await super(Vizio, self).get_setting(
            setting_type, setting_name, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_setting_options(
        self, setting_type: str, setting_name: str, log_api_exception: bool = True
    ) -> Optional[Union[int, str]]:
        """Get options of named setting."""
        return await super(Vizio, self).get_setting_options(
            setting_type, setting_name, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def set_setting(
        self,
        setting_type: str,
        setting_name: str,
        new_value: Union[int, str],
        log_api_exception: bool = True,
    ) -> Optional[bool]:
        """Set new value for named setting."""
        return await super(Vizio, self).set_setting(
            setting_type, setting_name, new_value, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_all_audio_settings(
        self, log_api_exception: bool = True
    ) -> Optional[Dict[str, Union[int, str]]]:
        """Get all audio setting names and corresponding values."""
        return await super(Vizio, self).get_all_audio_settings(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_all_audio_settings_options(
        self, log_api_exception: bool = True
    ) -> Optional[Dict[str, Union[int, str]]]:
        """Get all audio setting names and corresponding options."""
        return await super(Vizio, self).get_all_audio_settings_options(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_audio_setting(
        self, setting_name: str, log_api_exception: bool = True
    ) -> Optional[Union[int, str]]:
        """Get current value of named audio setting."""
        return await super(Vizio, self).get_audio_setting(
            setting_name, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_audio_setting_options(
        self, setting_name: str, log_api_exception: bool = True
    ) -> Optional[Union[int, str]]:
        """Get options of named audio setting."""
        return await super(Vizio, self).get_audio_setting_options(
            setting_name, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def set_audio_setting(
        self,
        setting_name: str,
        new_value: Union[int, str],
        log_api_exception: bool = True,
    ) -> Optional[bool]:
        """Set new value for named audio setting."""
        return await super(Vizio, self).set_audio_setting(
            setting_name, new_value, log_api_exception=log_api_exception
        )

    @async_to_sync
    @staticmethod
    async def get_apps_list(country: str = "all", session: ClientSession = None) -> List[str]:
        """Get list of known apps by name optionally filtered by supported country."""
        return await super(Vizio, Vizio).get_apps_list(country=country, session=session)

    @async_to_sync
    async def launch_app(
        self,
        app_name: str,
        apps_list: List[Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]],
        log_api_exception: bool = True,
    ) -> Optional[bool]:
        """Launch known app by name."""
        return await super(Vizio, self).launch_app(
            app_name, apps_list, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def launch_app_config(
        self,
        app_name: str,
        APP_ID: str,
        NAME_SPACE: int,
        MESSAGE: str = None,
        log_api_exception: bool = True,
    ) -> Optional[bool]:
        """Launch app using app's config values."""
        return await super(Vizio, self).launch_app_config(
            APP_ID, NAME_SPACE, MESSAGE, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_current_app(
        self,
        apps_list: List[Dict[str, Union[str, List[Union[str, Dict[str, Any]]]]]],
        log_api_exception: bool = True,
    ) -> Optional[str]:
        """Get name of currently running app. Returns const APP_NOT_RUNNING if no app is currently running, const UNKNOWN_APP if app config isn't known by pyvizio."""
        return await super(Vizio, self).get_current_app(
            apps_list, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_current_app_config(
        self, log_api_exception: bool = True
    ) -> Optional[AppConfig]:
        """Get config values of currently running app. Returns empty AppConfig if no app is currently running."""
        return await super(Vizio, self).get_current_app_config(
            log_api_exception=log_api_exception
        )


@async_to_sync
async def guess_device_type(
    ip: str, port: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT
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
