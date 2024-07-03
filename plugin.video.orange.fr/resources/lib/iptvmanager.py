"""IPTV Manager Integration module."""

import json
import socket
from typing import Any, Callable

from lib.providers import get_provider


class IPTVManager:
    """Interface to IPTV Manager."""

    def __init__(self, port: int):
        """Initialize IPTV Manager object."""
        self.port = port
        self.provider = get_provider()

    def via_socket(func: Callable[[Any], Any]):
        """Send the output of the wrapped function to socket."""

        def send(self) -> None:
            """Decorate to send over a socket."""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("127.0.0.1", self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):
        """Return JSON-STREAMS formatted python datastructure to IPTV Manager."""
        return dict(version=1, streams=self.provider.get_streams())

    @via_socket
    def send_epg(self):
        """Return JSON-EPG formatted python data structure to IPTV Manager."""
        return dict(version=1, epg=self.provider.get_epg())
