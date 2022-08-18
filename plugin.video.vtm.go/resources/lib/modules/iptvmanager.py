# -*- coding: utf-8 -*-
""" Kodi PVR Integration module """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import socket
from datetime import timedelta

from resources.lib import kodiutils
from resources.lib.modules import CHANNELS
from resources.lib.vtmgo.vtmgo import VtmGo
from resources.lib.vtmgo.vtmgoepg import VtmGoEpg

_LOGGER = logging.getLogger(__name__)


class IPTVManager:
    """ Code related to the Kodi PVR integration """

    def __init__(self, port):
        """ Initialise object
        :type port: int
        """
        self._vtm_go = VtmGo(None)
        self._vtm_go_epg = VtmGoEpg()
        self.port = port

    def via_socket(func):  # pylint: disable=no-self-argument
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())  # pylint: disable=not-callable
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):
        """ Report channel data """
        # Fetch EPG from API
        channels = self._vtm_go.get_live_channels()

        results = []
        for channel in channels:
            channel_data = CHANNELS.get(channel.key)

            if not channel_data:
                _LOGGER.warning('Skipping %s since we don\'t know this channel', channel.key)
                continue

            results.append(dict(
                name=channel_data.get('label') if channel_data else channel.name,
                id=channel_data.get('iptv_id'),
                preset=channel_data.get('iptv_preset'),
                logo='special://home/addons/{addon}/resources/logos/{logo}.png'.format(addon=kodiutils.addon_id(), logo=channel.key)
                if channel_data else channel.logo,
                stream=kodiutils.url_for('play', category='channels', item=channel.channel_id),
                vod=kodiutils.url_for('play_epg_datetime', channel=channel.key, timestamp='{date}'),
            ))

        return dict(version=1, streams=results)

    @via_socket
    def send_epg(self):
        """ Report EPG data """
        results = {}

        # Fetch EPG data
        for date in ['yesterday', 'today', 'tomorrow']:

            channels = self._vtm_go_epg.get_epgs(date)
            for channel in channels:
                # Lookup channel data in our own CHANNELS dict
                channel_data = next((c for c in list(CHANNELS.values()) if c.get('epg') == channel.key), None)
                if not channel_data:
                    _LOGGER.warning('Skipping EPG for %s since we don\'t know this channel', channel.key)
                    continue

                key = channel_data.get('iptv_id')

                # Create channel in dict if it doesn't exists
                if key not in list(results.keys()):
                    results[key] = []

                results[key].extend([
                    dict(
                        start=broadcast.time.isoformat(),
                        stop=(broadcast.time + timedelta(seconds=broadcast.duration)).isoformat(),
                        title=broadcast.title,
                        description=broadcast.description,
                        # subtitle=None,  # Not available in the API
                        # season=None,  # Not available in the API
                        # epsiode=None,  # Not available in the API
                        genre=broadcast.genre,
                        image=broadcast.thumb,
                        stream=kodiutils.url_for('play',
                                                 category=broadcast.playable_type,
                                                 item=broadcast.playable_uuid) if broadcast.playable_uuid else None)
                    for broadcast in channel.broadcasts
                ])

        return dict(version=1, epg=results)
