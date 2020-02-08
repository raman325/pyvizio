import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlsplit

from aiohttp import ClientSession
from pyvizio._api._protocol import KEY_CODE, async_invoke_api, async_invoke_api_auth
from pyvizio._api.apps import APP_HOME, APPS, GetCurrentAppCommand, LaunchAppCommand
from pyvizio._api.audio import (
    ChangeAudioSettingCommand,
    GetAllAudioSettingsCommand,
    GetAudioSettingCommand,
)
from pyvizio._api.base import CommandBase
from pyvizio._api.input import (
    ChangeInputCommand,
    GetCurrentInputCommand,
    GetInputsListCommand,
    InputItem,
)
from pyvizio._api.item import (
    GetCurrentPowerStateCommand,
    GetESNCommand,
    GetModelNameCommand,
    GetSerialNumberCommand,
    GetVersionCommand,
)
from pyvizio._api.pair import (
    BeginPairCommand,
    BeginPairResponse,
    CancelPairCommand,
    PairChallengeCommand,
    PairChallengeResponse,
)
from pyvizio._api.remote import EmulateRemoteCommand
from pyvizio.const import (
    DEFAULT_DEVICE_CLASS,
    DEFAULT_PORTS,
    DEFAULT_TIMEOUT,
    DEVICE_CLASS_SOUNDBAR,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
    MAX_VOLUME,
)
from pyvizio.discovery.ssdp import SSDPDevice, discover as discover_ssdp
from pyvizio.discovery.zeroconf import ZeroconfDevice, discover as discover_zc
from pyvizio.helpers import async_to_sync, open_port
import requests
import xmltodict

_LOGGER = logging.getLogger(__name__)


class VizioAsync(object):
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
        self.device_type = device_type.lower()
        if self.device_type == DEVICE_CLASS_SOUNDBAR:
            _LOGGER.warning(
                "The '%s' device type has been deprecated and will be removed"
                " soon. Please use the '%s' device type going forward",
                DEVICE_CLASS_SOUNDBAR,
                DEVICE_CLASS_SPEAKER,
            )
            self.device_type = DEVICE_CLASS_SPEAKER

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

    async def __add_port(self):
        for port in DEFAULT_PORTS:
            if await open_port(self.ip, port):
                self.ip = f"{self.ip}:{port}"

    async def __invoke_api(
        self, cmd: CommandBase, log_api_exception: bool = True
    ) -> Any:
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
        self, key_list: Union[List[str], str], log_api_exception: bool = True
    ) -> bool:
        key_codes = []
        if isinstance(key_list, list) is False:
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
        key_codes = []
        for ii in range(0, num):
            key_codes.append(key_code)

        return await self.__remote(key_codes, log_api_exception=log_api_exception)

    @staticmethod
    def discovery_zeroconf(timeout: int = DEFAULT_TIMEOUT) -> List[ZeroconfDevice]:
        results = discover_zc("_viziocast._tcp.local.", timeout=timeout)
        _LOGGER.info(results)
        return results

    @staticmethod
    def discovery_ssdp(timeout: int = DEFAULT_TIMEOUT) -> List[SSDPDevice]:
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
        return await VizioAsync(
            "", ip, "", auth_token, device_type, session=session, timeout=timeout
        ).can_connect()

    @staticmethod
    async def get_unique_id(
        ip: str,
        auth_token: str,
        device_type: str,
        timeout: int = DEFAULT_TIMEOUT,
        session: Optional[ClientSession] = None,
        log_api_exception: bool = True,
    ) -> Optional[str]:
        dev = VizioAsync(
            "", ip, "", auth_token, device_type, session=session, timeout=timeout
        )
        return (
            await dev.get_serial_number(log_api_exception=log_api_exception)
            or await dev.get_esn(log_api_exception=log_api_exception)  # noqa: W503
            or dev.ip  # noqa: W503
        )

    async def can_connect(self) -> bool:
        if (
            await self.__invoke_api_may_need_auth(
                GetCurrentPowerStateCommand(self.device_type), log_api_exception=False
            )
            is not None
        ):
            return True
        else:
            return False

    async def get_esn(self, log_api_exception: bool = True) -> Optional[str]:
        item = await self.__invoke_api_may_need_auth(
            GetESNCommand(self.device_type), log_api_exception=log_api_exception
        )

        if item:
            return item.value

        return None

    async def get_serial_number(self, log_api_exception: bool = True) -> Optional[str]:
        item = await self.__invoke_api_may_need_auth(
            GetSerialNumberCommand(self.device_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return item.value

        return None

    async def get_version(self, log_api_exception: bool = True) -> Optional[str]:
        item = await self.__invoke_api_may_need_auth(
            GetVersionCommand(self.device_type), log_api_exception=log_api_exception
        )

        if item:
            return item.value

        return None

    async def get_model(self, log_api_exception: bool = True) -> Optional[str]:
        return await self.__invoke_api(
            GetModelNameCommand(self.device_type), log_api_exception=log_api_exception
        )

    async def start_pair(
        self, log_api_exception: bool = True
    ) -> Optional[BeginPairResponse]:
        return await self.__invoke_api(
            BeginPairCommand(self.device_id, self.name, self.device_type),
            log_api_exception=log_api_exception,
        )

    async def stop_pair(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__invoke_api(
            CancelPairCommand(self.device_id, self.name, self.device_type),
            log_api_exception=log_api_exception,
        )

    async def pair(
        self, ch_type: int, token: int, pin: str = "", log_api_exception: bool = True
    ) -> Optional[PairChallengeResponse]:
        if self.device_type == DEVICE_CLASS_SPEAKER:
            pin = "0000"
        return await self.__invoke_api(
            PairChallengeCommand(self.device_id, ch_type, token, pin, self.device_type),
            log_api_exception=log_api_exception,
        )

    async def get_inputs_list(
        self, log_api_exception: bool = True
    ) -> Optional[List[InputItem]]:
        return await self.__invoke_api_may_need_auth(
            GetInputsListCommand(self.device_type), log_api_exception=log_api_exception
        )

    async def get_current_input(self, log_api_exception: bool = True) -> Optional[str]:
        item = await self.__invoke_api_may_need_auth(
            GetCurrentInputCommand(self.device_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return item.meta_name

        return None

    async def next_input(self, log_api_exception: bool = True) -> Optional[bool]:
        # HACK: Single call just invoking overlay menu with current input
        return await self.__remote_multiple(
            "INPUT_NEXT", 2, log_api_exception=log_api_exception
        )

    async def set_input(
        self, name: str, log_api_exception: bool = True
    ) -> Optional[bool]:
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
        item = await self.__invoke_api_may_need_auth(
            GetCurrentPowerStateCommand(self.device_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return bool(item.value)

        return None

    async def pow_on(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("POW_ON", log_api_exception=log_api_exception)

    async def pow_off(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("POW_OFF", log_api_exception=log_api_exception)

    async def pow_toggle(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("POW_TOGGLE", log_api_exception=log_api_exception)

    async def vol_up(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await self.__remote_multiple(
            "VOL_UP", num, log_api_exception=log_api_exception
        )

    async def vol_down(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await self.__remote_multiple(
            "VOL_DOWN", num, log_api_exception=log_api_exception
        )

    async def get_current_volume(self, log_api_exception: bool = True) -> Optional[int]:
        return await self.get_audio_setting(
            "volume", log_api_exception=log_api_exception
        )

    async def is_muted(self, log_api_exception: bool = True) -> Optional[bool]:
        # If None is returned lower() will fail, if not we can do a simple boolean check
        try:
            return (
                await self.get_audio_setting(
                    "mute", log_api_exception=log_api_exception
                ).lower()
                == "on"
            )
        except AttributeError:
            return None

    def get_max_volume(self) -> int:
        return MAX_VOLUME[self.device_type]

    async def ch_up(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await self.__remote_multiple(
            "CH_UP", num, log_api_exception=log_api_exception
        )

    async def ch_down(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await self.__remote_multiple(
            "CH_DOWN", num, log_api_exception=log_api_exception
        )

    async def ch_prev(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("CH_PREV", log_api_exception=log_api_exception)

    async def mute_on(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("MUTE_ON", log_api_exception=log_api_exception)

    async def mute_off(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("MUTE_OFF", log_api_exception=log_api_exception)

    async def mute_toggle(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("MUTE_TOGGLE", log_api_exception=log_api_exception)

    async def play(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("PLAY", log_api_exception=log_api_exception)

    async def pause(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("PAUSE", log_api_exception=log_api_exception)

    async def remote(self, key: str, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote(key, log_api_exception=log_api_exception)

    def get_remote_keys_list(self) -> List[str]:
        return KEY_CODE[self.device_type].keys()

    async def get_all_audio_settings(
        self, log_api_exception: bool = True
    ) -> Optional[Dict[str, Union[int, str]]]:
        item = await self.__invoke_api_may_need_auth(
            GetAllAudioSettingsCommand(self.device_type),
            log_api_exception=log_api_exception,
        )

        if item:
            return item

        return None

    async def get_audio_setting(
        self, setting_name: str, log_api_exception: bool = True
    ) -> Optional[Union[int, str]]:
        item = await self.__invoke_api_may_need_auth(
            GetAudioSettingCommand(self.device_type, setting_name),
            log_api_exception=log_api_exception,
        )

        # coerce to int if possible
        if item:
            try:
                return int(item.value)
            except ValueError:
                return item.value

        return None

    async def set_audio_setting(
        self,
        setting_name: str,
        new_value: Union[int, str],
        log_api_exception: bool = True,
    ) -> Optional[bool]:
        audio_setting_item = await self.__invoke_api_may_need_auth(
            GetAudioSettingCommand(self.device_type, setting_name),
            log_api_exception=log_api_exception,
        )

        if not audio_setting_item:
            _LOGGER.error("Couldn't detect setting for %s", setting_name)
            return None

        return await self.__invoke_api_may_need_auth(
            ChangeAudioSettingCommand(
                self.device_type, audio_setting_item.id, setting_name, new_value
            ),
            log_api_exception=log_api_exception,
        )

    def get_apps_list(self, country: str = "all") -> List[str]:
        # Assumes "*" means all countries are supported
        if country.lower() != "all":
            return sorted(
                [
                    app["name"]
                    for app in (APP_HOME + APPS)
                    if "*" in app["country"] or country.lower() in app["country"]
                ]
            )

        return sorted([app["name"] for app in APP_HOME + APPS])

    async def launch_app(
        self, app_name: str, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await self.__invoke_api_may_need_auth(
            LaunchAppCommand(self.device_type, app_name),
            log_api_exception=log_api_exception,
        )

    async def get_current_app(self, log_api_exception: bool = True) -> Optional[str]:
        return await self.__invoke_api_may_need_auth(
            GetCurrentAppCommand(self.device_type), log_api_exception=log_api_exception
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

    if await device.can_connect():
        return DEVICE_CLASS_SPEAKER
    else:
        return DEVICE_CLASS_TV


class Vizio(VizioAsync):
    def __init__(
        self,
        device_id: str,
        ip: str,
        name: str,
        auth_token: str = "",
        device_type: str = DEFAULT_DEVICE_CLASS,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        super(Vizio, self).__init__(
            device_id, ip, name, auth_token, device_type, session=None, timeout=timeout
        )

    @staticmethod
    def discovery_zeroconf(timeout: int = DEFAULT_TIMEOUT) -> List[ZeroconfDevice]:
        return super(Vizio, Vizio).discovery_zeroconf(timeout)

    @staticmethod
    def discovery_ssdp(timeout: int = DEFAULT_TIMEOUT) -> List[ZeroconfDevice]:
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
        return await super(Vizio, Vizio).validate_ha_config(
            ip, auth_token, device_type, session=session, timeout=timeout
        )

    @staticmethod
    @async_to_sync
    async def get_unique_id(
        ip: str,
        auth_token: str,
        device_type: str,
        session: Optional[ClientSession] = None,
        timeout: int = DEFAULT_TIMEOUT,
        log_api_exception: bool = True,
    ) -> Optional[str]:
        return await super(Vizio, Vizio).get_unique_id(
            ip,
            auth_token,
            device_type,
            timeout=timeout,
            log_api_exception=log_api_exception,
        )

    @async_to_sync
    async def can_connect(self) -> bool:
        return await super(Vizio, self).can_connect()

    @async_to_sync
    async def get_esn(self, log_api_exception: bool = True) -> Optional[str]:
        return await super(Vizio, self).get_esn(log_api_exception=log_api_exception)

    @async_to_sync
    async def get_serial_number(self, log_api_exception: bool = True) -> Optional[str]:
        return await super(Vizio, self).get_serial_number(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_version(self, log_api_exception: bool = True) -> Optional[str]:
        return await super(Vizio, self).get_version(log_api_exception=log_api_exception)

    @async_to_sync
    async def get_model(self, log_api_exception: bool = True) -> Optional[str]:
        return await super(Vizio, self).get_model(log_api_exception=log_api_exception)

    @async_to_sync
    async def start_pair(
        self, log_api_exception: bool = True
    ) -> Optional[BeginPairResponse]:
        return await super(Vizio, self).start_pair(log_api_exception=log_api_exception)

    @async_to_sync
    async def stop_pair(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).stop_pair(log_api_exception=log_api_exception)

    @async_to_sync
    async def pair(
        self, ch_type: str, token: str, pin: str, log_api_exception: bool = True
    ) -> Optional[PairChallengeResponse]:
        return await super(Vizio, self).pair(
            ch_type, token, pin, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_inputs_list(
        self, log_api_exception: bool = True
    ) -> Optional[List[InputItem]]:
        return await super(Vizio, self).get_inputs_list(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_current_input(
        self, log_api_exception: bool = True
    ) -> Optional[InputItem]:
        return await super(Vizio, self).get_current_input(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def next_input(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).next_input(log_api_exception=log_api_exception)

    @async_to_sync
    async def set_input(
        self, name: str, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await super(Vizio, self).set_input(
            name, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_power_state(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).get_power_state(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def pow_on(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).pow_on(log_api_exception=log_api_exception)

    @async_to_sync
    async def pow_off(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).pow_off(log_api_exception=log_api_exception)

    @async_to_sync
    async def pow_toggle(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).pow_toggle(log_api_exception=log_api_exception)

    @async_to_sync
    async def vol_up(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await super(Vizio, self).vol_up(num, log_api_exception=log_api_exception)

    @async_to_sync
    async def vol_down(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await super(Vizio, self).vol_down(
            num, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_current_volume(self, log_api_exception: bool = True) -> Optional[int]:
        return await super(Vizio, self).get_current_volume(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def is_muted(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).is_muted(log_api_exception=log_api_exception)

    def get_max_volume(self) -> int:
        return super(Vizio, self).get_max_volume()

    @async_to_sync
    async def ch_up(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await super(Vizio, self).ch_up(num, log_api_exception=log_api_exception)

    @async_to_sync
    async def ch_down(
        self, num: int = 1, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await super(Vizio, self).ch_down(
            num, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def ch_prev(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).ch_prev(log_api_exception=log_api_exception)

    @async_to_sync
    async def mute_on(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).mute_on(log_api_exception=log_api_exception)

    @async_to_sync
    async def mute_off(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).mute_off(log_api_exception=log_api_exception)

    @async_to_sync
    async def mute_toggle(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).mute_toggle(log_api_exception=log_api_exception)

    @async_to_sync
    async def play(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).play(log_api_exception=log_api_exception)

    @async_to_sync
    async def pause(self, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).pause(log_api_exception=log_api_exception)

    @async_to_sync
    async def remote(self, key: str, log_api_exception: bool = True) -> Optional[bool]:
        return await super(Vizio, self).remote(key, log_api_exception=log_api_exception)

    def get_remote_keys_list(self) -> List[str]:
        return super(Vizio, self).get_remote_keys_list()

    @async_to_sync
    async def get_all_audio_settings(
        self, log_api_exception: bool = True
    ) -> Optional[Dict[str, Union[int, str]]]:
        return await super(Vizio, self).get_all_audio_settings(
            log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_audio_setting(
        self, setting_name: str, log_api_exception: bool = True
    ) -> Optional[Union[int, str]]:
        return await super(Vizio, self).get_audio_setting(
            setting_name, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def set_audio_setting(
        self,
        setting_name: str,
        new_value: Union[int, str],
        log_api_exception: bool = True,
    ) -> Optional[bool]:
        return await super(Vizio, self).set_audio_setting(
            setting_name, new_value, log_api_exception=log_api_exception
        )

    def get_apps_list(self, country: str = None) -> List[str]:
        return super(Vizio, self).get_apps_list(country=country)

    @async_to_sync
    async def launch_app(
        self, app_name: str, log_api_exception: bool = True
    ) -> Optional[bool]:
        return await super(Vizio, self).launch_app(
            app_name, log_api_exception=log_api_exception
        )

    @async_to_sync
    async def get_current_app(self, log_api_exception: bool = True) -> Optional[str]:
        return await super(Vizio, self).get_current_app(
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
