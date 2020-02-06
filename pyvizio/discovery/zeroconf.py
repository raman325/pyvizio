import time
from typing import Callable, List

from pyvizio.const import DEFAULT_TIMEOUT
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf

try:
    from zeroconf import IPVersion

    parse_ip_with_zc = True
except ImportError:
    from ipaddress import ip_address

    parse_ip_with_zc = False


class ZeroconfDevice:
    def __init__(self, name: str, ip: str, port: int, model: str, id: str) -> None:
        self.name = name
        self.ip = ip
        self.port = port
        self.model = model
        self.id = id

    def __repr__(self):
        return f"ZeroconfDevice(ip='{self.ip}', port='{self.port}', name='{self.name}', model='{self.model}', id='{self.id}')"


class ZeroconfListener:
    def __init__(self, func: Callable[[ServiceInfo], None]) -> None:
        self._func = func

    def add_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        self._func(zeroconf.get_service_info(type, name))


def discover(service_type: str, timeout: int = DEFAULT_TIMEOUT) -> List[ZeroconfDevice]:
    services = []

    def append_service(info: ServiceInfo) -> None:
        name = info.name[: -(len(info.type) + 1)]
        if parse_ip_with_zc:
            ip = info.parsed_addresses(IPVersion.V4Only)[0]
        else:
            ip = ip_address(info.addresses[0])
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
