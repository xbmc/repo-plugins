# -*- coding: utf-8 -*-
""" Kodi PVR Integration module """

from __future__ import absolute_import, division, unicode_literals

import logging
import socket
import json

_LOGGER = logging.getLogger('iptv-manager')


class IPTVManager:
    """Interface to IPTV Manager"""

    def __init__(self, port, yelo):
        """Initialize IPTV Manager object"""
        self.port = port
        self.yelo = yelo

    def via_socket(func):  # pylint: disable=no-self-argument
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            _LOGGER.debug('Sending data output to IPTV Manager using port %s', self.port)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())  # pylint: disable=not-callable
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):
        return dict(version=1, streams=self.yelo.get_channels_iptv())

    @via_socket
    def send_epg(self):
        tv_channels = self.yelo.get_channels()
        return dict(version=1, epg=self.yelo.get_epg(tv_channels))
