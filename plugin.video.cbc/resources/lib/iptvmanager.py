"""Implementation of IPTVManager class."""

from __future__ import absolute_import, division, unicode_literals

import json
import socket

from resources.lib.livechannels import LiveChannels
from resources.lib.epg import get_iptv_epg


class IPTVManager:
    """Interface to IPTV Manager."""

    def __init__(self, port):
        """Initialize IPTV Manager object."""
        self.port = port

    def via_socket(func):  # pylint: disable=no-self-argument
        """Send the output of the wrapped function to socket."""

        def send(self):
            """Decorate to send data over a socket."""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())  # pylint: disable=not-callable
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):  # pylint: disable=no-method-argument,no-self-use
        """Return JSON-STREAMS formatted information to IPTV Manager."""
        return dict(version=1, streams=LiveChannels().get_iptv_channels())

    @via_socket
    def send_epg(self):  # pylint: disable=no-method-argument,no-self-use
        """Return JSON-EPG formatted information to IPTV Manager."""
        return dict(version=1, epg=get_iptv_epg())
