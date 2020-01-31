import time
from typing import Callable, List

from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, Zeroconf

from .const import DEFAULT_TIMEOUT


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


def discover(service_type: str, timeout: int = DEFAULT_TIMEOUT) -> List[ZeroconfDevice]:
    services = []

    def append_service(info: ServiceInfo) -> None:
        name = info.name[: -(len(info.type) + 1)]
        ip = info.parsed_addresses(IPVersion.V4Only)[0]
        port = info.port
        model = info.properties[b"name"].decode("utf-8")
        # id = info.properties[b"id"]
        # # handle id decode for various discovered use cases
        # if isinstance(id, bytes):
        #     try:
        #         int(id, 16)
        #     except Exception:
        #         id = id.hex()
        # else:
        #     id = None

        service = ZeroconfDevice(name, ip, port, model, None)
        services.append(service)

    zeroconf = Zeroconf()
    ServiceBrowser(zeroconf, service_type, ZeroconfListener(append_service))
    time.sleep(timeout)
    zeroconf.close()
    return services
