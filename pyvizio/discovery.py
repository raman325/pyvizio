import time
from typing import Callable, List

from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, Zeroconf


class ZeroconfDevice:
    def __init__(self, name: str, ip: str, port: int, model: str, id: str) -> None:
        self.name = name
        self.ip = ip
        self.port = port
        self.model = model
        self.id = id


class ZeroconfListener:
    def __init__(self, func: Callable[[ServiceInfo], None]) -> None:
        self._func = func

    def add_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        self._func(zeroconf.get_service_info(type, name))


def discover(service_type: str, timeout: int = 3) -> List[ZeroconfDevice]:
    services = []

    def append_service(info: ServiceInfo) -> None:
        service = ZeroconfDevice(
            info.name[: -(len(info.type) + 1)],
            info.parsed_addresses(IPVersion.V4Only)[0],
            info.port,
            info.properties[b"name"].decode("utf-8"),
            info.properties[b"id"].hex(),
        )
        services.append(service)

    zeroconf = Zeroconf()
    ServiceBrowser(zeroconf, service_type, ZeroconfListener(append_service))
    time.sleep(timeout)
    zeroconf.close()
    return services
