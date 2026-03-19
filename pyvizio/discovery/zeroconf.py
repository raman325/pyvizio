"""Vizio SmartCast device zeroconf discovery function and classes."""

from __future__ import annotations

from collections.abc import Callable
import time

from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

from pyvizio.const import DEFAULT_TIMEOUT


class ZeroconfDevice:
    def __init__(self, name: str, ip: str, port: int, model: str, id: str) -> None:
        self.name = name
        self.ip = ip
        self.port = port
        self.model = model
        self.id = id

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__


class ZeroconfListener(ServiceListener):
    """Basic zeroconf listener."""

    def __init__(self, func: Callable[[ServiceInfo], None]) -> None:
        """Initialize zeroconf listener with function callback."""
        self._func = func

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"

    def __eq__(self, other) -> bool:
        return self is other or self.__dict__ == other.__dict__

    def add_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        """Callback function when zeroconf service is discovered."""
        info = zeroconf.get_service_info(type, name)
        if info is not None:
            self._func(info)

    def remove_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        """Callback function when zeroconf service is removed."""

    def update_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        """Callback function when zeroconf service is updated."""


def discover(service_type: str, timeout: int = DEFAULT_TIMEOUT) -> list[ZeroconfDevice]:
    """Return all discovered zeroconf services of a given service type over given timeout period."""
    services = []

    def append_service(info: ServiceInfo) -> None:
        """Append discovered zeroconf service to service list."""
        name = info.name[: -(len(info.type) + 1)]
        ip = info.parsed_addresses(IPVersion.V4Only)[0]
        port = info.port or 0
        model_raw = info.properties.get(b"name", b"")
        model = (
            model_raw.decode("utf-8")
            if isinstance(model_raw, bytes)
            else str(model_raw)
        )
        id_raw = info.properties.get(b"id")

        # handle id decode for various discovered use cases
        id_str: str | None = None
        if isinstance(id_raw, bytes):
            try:
                int(id_raw, 16)
                id_str = id_raw.decode("utf-8")
            except Exception:
                id_str = id_raw.hex()

        service = ZeroconfDevice(name, ip, port, model, id_str or "")
        services.append(service)

    zeroconf = Zeroconf()
    ServiceBrowser(zeroconf, service_type, ZeroconfListener(append_service))
    time.sleep(timeout)
    zeroconf.close()

    return services
