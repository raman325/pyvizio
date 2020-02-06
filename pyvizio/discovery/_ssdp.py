#   Copyright 2014 Dan Krause
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import http.client
import io
import socket
from typing import Dict

from pyvizio.const import DEFAULT_TIMEOUT


class SSDPDevice(object):
    def __init__(self, ip, name, model, udn) -> None:
        self.ip = ip
        self.name = name
        self.model = model
        self.udn = udn

    def __repr__(self) -> Dict[str, str]:
        return f"SSDPDevice(ip='{self.ip}', name='{self.name}', model='{self.model}', udn='{self.udn}')"


class SSDPResponse(object):
    class _FakeSocket(io.BytesIO):
        def makefile(self, *args, **kw):
            return self

    def __init__(self, response):
        r = http.client.HTTPResponse(self._FakeSocket(response))
        r.begin()
        self.location = r.getheader("location")
        self.usn = r.getheader("usn")
        self.st = r.getheader("st")
        self.cache = r.getheader("cache-control").split("=")[1]

    def __repr__(self):
        return f"SSDPResponse(location='{self.location}', st='{self.st}', usn='{self.usn}')"


def discover(service, timeout=DEFAULT_TIMEOUT, retries=1, mx=3):
    group = ("239.255.255.250", 1900)
    message = "\r\n".join(
        [
            "M-SEARCH * HTTP/1.1",
            "HOST: {0}:{1}",
            'MAN: "ssdp:discover"',
            "ST: {st}",
            "MX: {mx}",
            "",
            "",
        ]
    )
    socket.setdefaulttimeout(timeout)
    responses = {}
    for _ in range(retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        message_bytes = message.format(*group, st=service, mx=mx).encode("utf-8")
        sock.sendto(message_bytes, group)

        while True:
            try:
                response = SSDPResponse(sock.recv(1024))
                responses[response.location] = response
            except socket.timeout:
                break

        return list(responses.values())
