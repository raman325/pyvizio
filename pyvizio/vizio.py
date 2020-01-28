import asyncio
import logging
from typing import Any, List, Optional, Union

from aiohttp import ClientSession

from .cmd_input import (
    ChangeInputCommand,
    GetCurrentInputCommand,
    GetInputsListCommand,
    VizioInput,
)
from .cmd_pair import (
    BeginPairCommand,
    BeginPairResponse,
    CancelPairCommand,
    PairChallengeCommand,
    PairChallengeResponse,
)
from .cmd_power import GetPowerStateCommand
from .cmd_remote import EmulateRemoteCommand
from .cmd_settings import GetCurrentAudioCommand, GetESNCommand
from .const import (
    DEFAULT_DEVICE_CLASS,
    DEFAULT_TIMEOUT,
    DEVICE_CLASS_SOUNDBAR,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
)
from .discovery import ZeroconfDevice, discover
from .protocol import CommandBase, KeyCodes, async_invoke_api, async_invoke_api_auth

_LOGGER = logging.getLogger(__name__)

MAX_VOLUME = {DEVICE_CLASS_TV: 100, DEVICE_CLASS_SPEAKER: 31}


class DeviceDescription(object):
    def __init__(self, ip: str, name: str, model: str, id: str) -> None:
        self.ip = ip
        self.name = name
        self.model = model
        self.id = id


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
        self._device_type = device_type.lower()
        if self._device_type == DEVICE_CLASS_SOUNDBAR:
            _LOGGER.warning(
                f"The '{DEVICE_CLASS_SOUNDBAR}' device type has been deprecated and will be removed soon. Please use the '{DEVICE_CLASS_SPEAKER}' device type going forward"
            )
            self._device_type = DEVICE_CLASS_SPEAKER

        if (
            self._device_type != DEVICE_CLASS_TV
            and self._device_type != DEVICE_CLASS_SPEAKER
        ):
            raise Exception(
                f"Invalid device type specified. Use either '{DEVICE_CLASS_TV}' or '{DEVICE_CLASS_SPEAKER}'"
            )

        self._ip = ip
        self._name = name
        self._device_id = device_id
        self._auth_token = auth_token
        self._session = session
        self._timeout = timeout

    async def __invoke_api(
        self,
        cmd: CommandBase,
        log_api_exception: bool = True,
        custom_timeout: bool = True,
    ) -> Any:
        timeout = None
        if custom_timeout:
            timeout = self._timeout

        return await async_invoke_api(
            self._ip,
            cmd,
            _LOGGER,
            timeout,
            log_api_exception=log_api_exception,
            session=self._session,
        )

    async def __invoke_api_auth(
        self,
        cmd: CommandBase,
        log_api_exception: bool = True,
        custom_timeout: bool = True,
    ) -> Any:
        timeout = None
        if custom_timeout:
            timeout = self._timeout

        return await async_invoke_api_auth(
            self._ip,
            cmd,
            self._auth_token,
            _LOGGER,
            timeout,
            log_api_exception=log_api_exception,
            session=self._session,
        )

    async def __invoke_api_may_need_auth(
        self,
        cmd: CommandBase,
        log_api_exception: bool = True,
        custom_timeout: bool = True,
    ) -> Any:
        if self._auth_token is None or "" == self._auth_token:
            if self._device_type == DEVICE_CLASS_SPEAKER:
                return await self.__invoke_api(
                    cmd,
                    log_api_exception=log_api_exception,
                    custom_timeout=custom_timeout,
                )
            else:
                raise Exception(
                    f"Empty auth token. To target a speaker and bypass auth requirements, pass '{DEVICE_CLASS_SPEAKER}' as device_type"
                )
        return await self.__invoke_api_auth(
            cmd, log_api_exception=log_api_exception, custom_timeout=custom_timeout
        )

    async def __remote(
        self, key_list: Union[List[str], str], log_api_exception: bool = True
    ) -> bool:
        key_codes = []
        if isinstance(key_list, list) is False:
            key_list = [key_list]

        for key in key_list:
            if key not in KeyCodes.CODES[self._device_type]:
                _LOGGER.error(
                    "Key Code of '%s' not found for device type of '%s'",
                    key,
                    self._device_type,
                )
                return False
            else:
                key_codes.append(KeyCodes.CODES[self._device_type][key])

        result = await self.__invoke_api_may_need_auth(
            EmulateRemoteCommand(key_codes, self._device_type),
            log_api_exception=log_api_exception,
            custom_timeout=False,
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
    def discovery(timeout: int = 3) -> List[ZeroconfDevice]:
        return discover("_viziocast._tcp.local.", timeout)

    @staticmethod
    async def validate_ha_config(
        ip: str, auth_token: str, device_type: str, timeout: int = DEFAULT_TIMEOUT
    ) -> bool:
        return await VizioAsync(
            "", ip, "", auth_token, device_type, timeout=timeout
        ).can_connect()

    @staticmethod
    async def get_unique_id(
        ip: str,
        auth_token: str,
        device_type: str,
        timeout: int = DEFAULT_TIMEOUT,
        log_api_exception: bool = True,
    ) -> Optional[str]:
        return await VizioAsync(
            "", ip, "", auth_token, device_type, timeout=timeout
        ).get_esn(log_api_exception=log_api_exception)

    async def can_connect(self) -> bool:
        if (
            await self.__invoke_api_may_need_auth(
                GetPowerStateCommand(self._device_type), log_api_exception=False
            )
            is not None
        ):
            return True
        else:
            return False

    async def get_esn(self, log_api_exception: bool = True) -> Optional[str]:
        return await self.__invoke_api_may_need_auth(
            GetESNCommand(self._device_type), log_api_exception=log_api_exception
        )

    async def start_pair(
        self, log_api_exception: bool = True
    ) -> Optional[BeginPairResponse]:
        return await self.__invoke_api(
            BeginPairCommand(self._device_id, self._name, self._device_type),
            log_api_exception=log_api_exception,
        )

    async def stop_pair(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__invoke_api(
            CancelPairCommand(self._device_id, self._name, self._device_type),
            log_api_exception=log_api_exception,
        )

    async def pair(
        self, ch_type: str, token: str, pin: str, log_api_exception: bool = True
    ) -> Optional[PairChallengeResponse]:
        return await self.__invoke_api(
            PairChallengeCommand(
                self._device_id, ch_type, token, pin, self._device_type
            ),
            log_api_exception=log_api_exception,
        )

    async def get_inputs(
        self, log_api_exception: bool = True
    ) -> Optional[List[VizioInput]]:
        return await self.__invoke_api_may_need_auth(
            GetInputsListCommand(self._device_type), log_api_exception=log_api_exception
        )

    async def get_current_input(
        self, log_api_exception: bool = True
    ) -> Optional[VizioInput]:
        return await self.__invoke_api_may_need_auth(
            GetCurrentInputCommand(self._device_type),
            log_api_exception=log_api_exception,
        )

    async def get_power_state(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__invoke_api_may_need_auth(
            GetPowerStateCommand(self._device_type), log_api_exception=log_api_exception
        )

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
        return await self.__invoke_api_may_need_auth(
            GetCurrentAudioCommand(self._device_type),
            log_api_exception=log_api_exception,
        )

    def get_max_volume(self) -> int:
        return MAX_VOLUME[self._device_type]

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

    async def input_next(self, log_api_exception: bool = True) -> Optional[bool]:
        # HACK: Single call just invoking overlay menu with current input
        return await self.__remote_multiple(
            "INPUT_NEXT", 2, log_api_exception=log_api_exception
        )

    async def input_switch(
        self, name: str, log_api_exception: bool = True
    ) -> Optional[bool]:
        if isinstance(self, Vizio):
            cur_input = await super(Vizio, self).get_current_input(
                log_api_exception=log_api_exception
            )
        else:
            cur_input = await self.get_current_input(
                log_api_exception=log_api_exception
            )
        if cur_input is None:
            _LOGGER.error("Couldn't detect current input")
            return False
        return await self.__invoke_api_may_need_auth(
            ChangeInputCommand(cur_input.id, name, self._device_type),
            log_api_exception=log_api_exception,
            custom_timeout=False,
        )

    async def play(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("PLAY", log_api_exception=log_api_exception)

    async def pause(self, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote("PAUSE", log_api_exception=log_api_exception)

    async def remote(self, key: str, log_api_exception: bool = True) -> Optional[bool]:
        return await self.__remote(key, log_api_exception=log_api_exception)

    def get_device_keys(self) -> List[str]:
        return KeyCodes.CODES[self._device_type].keys()


async def async_guess_device_type(
    ip: str, port: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT
) -> str:
    """
    Attempts to guess the device type by getting power state with no auth
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
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        super(Vizio, self).__init__(
            device_id, ip, name, auth_token, device_type, session=None, timeout=timeout
        )

    def __del__(self) -> None:
        self.loop.close()

    @staticmethod
    def discovery(timeout: int = 3) -> List[ZeroconfDevice]:
        return VizioAsync.discovery(timeout)

    @staticmethod
    def validate_ha_config(
        ip: str, auth_token: str, device_type: str, timeout: int = DEFAULT_TIMEOUT
    ) -> bool:
        return Vizio("", ip, "", auth_token, device_type, timeout).can_connect()

    @staticmethod
    def get_unique_id(
        ip: str,
        auth_token: str,
        device_type: str,
        timeout: int = DEFAULT_TIMEOUT,
        log_api_exception: bool = True,
    ) -> Optional[str]:
        return Vizio("", ip, "", auth_token, device_type, timeout).get_esn(
            log_api_exception=log_api_exception
        )

    def can_connect(self) -> bool:
        return self.loop.run_until_complete(
            self.loop.create_task(super(Vizio, self).can_connect())
        )

    def get_esn(self, log_api_exception: bool = True) -> Optional[str]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).get_esn(log_api_exception=log_api_exception)
            )
        )

    def start_pair(self, log_api_exception: bool = True) -> Optional[BeginPairResponse]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).start_pair(log_api_exception=log_api_exception)
            )
        )

    def stop_pair(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).stop_pair(log_api_exception=log_api_exception)
            )
        )

    def pair(
        self, ch_type: str, token: str, pin: str, log_api_exception: bool = True
    ) -> Optional[PairChallengeResponse]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).pair(
                    ch_type, token, pin, log_api_exception=log_api_exception
                )
            )
        )

    def get_inputs(self, log_api_exception: bool = True) -> Optional[List[VizioInput]]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).get_inputs(log_api_exception=log_api_exception)
            )
        )

    def get_current_input(self, log_api_exception: bool = True) -> Optional[VizioInput]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).get_current_input(
                    log_api_exception=log_api_exception
                )
            )
        )

    def get_power_state(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).get_power_state(log_api_exception=log_api_exception)
            )
        )

    def pow_on(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).pow_on(log_api_exception=log_api_exception)
            )
        )

    def pow_off(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).pow_off(log_api_exception=log_api_exception)
            )
        )

    def pow_toggle(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).pow_toggle(log_api_exception=log_api_exception)
            )
        )

    def vol_up(self, num: int = 1, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).vol_up(num, log_api_exception=log_api_exception)
            )
        )

    def vol_down(self, num: int = 1, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).vol_down(num, log_api_exception=log_api_exception)
            )
        )

    def get_current_volume(self, log_api_exception: bool = True) -> Optional[int]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).get_current_volume(
                    log_api_exception=log_api_exception
                )
            )
        )

    def get_max_volume(self) -> int:
        return super(Vizio, self).get_max_volume()

    def ch_up(self, num: int = 1, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).ch_up(num, log_api_exception=log_api_exception)
            )
        )

    def ch_down(self, num: int = 1, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).ch_down(num, log_api_exception=log_api_exception)
            )
        )

    def ch_prev(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).ch_prev(log_api_exception=log_api_exception)
            )
        )

    def mute_on(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).mute_on(log_api_exception=log_api_exception)
            )
        )

    def mute_off(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).mute_off(log_api_exception=log_api_exception)
            )
        )

    def mute_toggle(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).mute_toggle(log_api_exception=log_api_exception)
            )
        )

    def input_next(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).input_next(log_api_exception=log_api_exception)
            )
        )

    def input_switch(self, name: str, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).input_switch(
                    name, log_api_exception=log_api_exception
                )
            )
        )

    def play(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).play(log_api_exception=log_api_exception)
            )
        )

    def pause(self, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).pause(log_api_exception=log_api_exception)
            )
        )

    def remote(self, key: str, log_api_exception: bool = True) -> Optional[bool]:
        return self.loop.run_until_complete(
            self.loop.create_task(
                super(Vizio, self).remote(key, log_api_exception=log_api_exception)
            )
        )

    def get_device_keys(self) -> List[str]:
        return super(Vizio, self).get_device_keys()


def guess_device_type(
    ip: str, port: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT
) -> str:
    """
    Attempts to guess the device type by getting power state with no auth
    token.

    NOTE:
    The `ip` and `port` values passed in have to be valid for the device in
    order for this to work. This function is being used as part of a zeroconf
    discovery workflow in HomeAssistant which is why it is safe to assume that
    `ip` and `port` are valid.
    """

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            loop.create_task(async_guess_device_type(ip, port, timeout))
        )
    finally:
        loop.close()
