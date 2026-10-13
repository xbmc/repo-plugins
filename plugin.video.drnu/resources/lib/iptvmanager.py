"""IPTV Manager Integration module"""

import json
import socket


class IPTVManager:
    """Interface to IPTV Manager"""

    def __init__(self, port, channels=None, epg=None):
        """Initialize IPTV Manager object"""
        self.port = port
        self.channels = channels if channels is not None else []
        self.epg = epg if epg is not None else []

    def via_socket(func):
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):
        """Return JSON-STREAMS formatted python datastructure to IPTV Manager"""
        return {'version': 1, 'streams': self.channels}

    @via_socket
    def send_epg(self):
        """Return JSON-EPG formatted python data structure to IPTV Manager"""
        return {'version': 1, 'epg': self.epg}
