"""Vizio SmartCast device zeroconf discovery function and classes."""

import time
from typing import Callable, List

from pyvizio.const import DEFAULT_TIMEOUT
from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, Zeroconf


class ZeroconfDevice(object):
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


class ZeroconfListener(object):
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
        self._func(zeroconf.get_service_info(type, name))


def discover(service_type: str, timeout: int = DEFAULT_TIMEOUT) -> List[ZeroconfDevice]:
    """Return all discovered zeroconf services of a given service type over given timeout period."""
    services = []

    def append_service(info: ServiceInfo) -> None:
        """Append discovered zeroconf service to service list."""
        name = info.name[: -(len(info.type) + 1)]
        ip = info.parsed_addresses(IPVersion.V4Only)[0]
        port = info.port
        model = info.properties.get(b"name", "").decode("utf-8")
        id = info.properties.get(b"id")

        # handle id decode for various discovered use cases
        if isinstance(id, bytes):
            try:
                int(id, 16)
            except Exception:
                id = id.hex()
        else:
            id = None

        service = ZeroconfDevice(name, ip, port, model, id)
        services.append(service)

    zeroconf = Zeroconf()
    ServiceBrowser(zeroconf, service_type, ZeroconfListener(append_service))
    time.sleep(timeout)
    zeroconf.close()

    return services
