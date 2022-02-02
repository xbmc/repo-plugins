# -*- coding: utf-8 -*-
"""Implementation of IPTVManager class"""

from __future__ import absolute_import, division, unicode_literals

import logging
from datetime import datetime, timedelta

from resources.lib import kodiutils
from resources.lib.viervijfzes import CHANNELS
from resources.lib.viervijfzes.epg import EpgApi

_LOGGER = logging.getLogger(__name__)


class IPTVManager:
    """Interface to IPTV Manager"""

    def __init__(self, port):
        """Initialize IPTV Manager object"""
        self.port = port

    def via_socket(func):  # pylint: disable=no-self-argument
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            import json
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func()).encode())  # pylint: disable=not-callable
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels():  # pylint: disable=no-method-argument
        """Return JSON-STREAMS formatted information to IPTV Manager"""
        streams = []
        for key, channel in CHANNELS.items():
            if channel.get('iptv_id'):
                streams.append(dict(
                    id=channel.get('iptv_id'),
                    name=channel.get('name'),
                    logo='special://home/addons/{addon}/resources/logos/{logo}'.format(addon=kodiutils.addon_id(),
                                                                                       logo=channel.get('logo')),
                    preset=channel.get('iptv_preset'),
                    stream='plugin://plugin.video.viervijfzes/play/live/{channel}'.format(channel=key),
                    vod='plugin://plugin.video.viervijfzes/play/epg/{channel}/{{date}}'.format(channel=key)
                ))

        return dict(version=1, streams=streams)

    @via_socket
    def send_epg():  # pylint: disable=no-method-argument
        """Return JSON-EPG formatted information to IPTV Manager"""
        epg_api = EpgApi()

        try:  # Python 3
            from urllib.parse import quote
        except ImportError:  # Python 2
            from urllib import quote

        today = datetime.today()

        results = {}
        for key, channel in CHANNELS.items():
            iptv_id = channel.get('iptv_id')

            if channel.get('iptv_id'):
                results[iptv_id] = []

                for i in range(-3, 7):
                    date = today + timedelta(days=i)
                    epg = epg_api.get_epg(key, date.strftime('%Y-%m-%d'))

                    results[iptv_id].extend([
                        dict(
                            start=program.start.isoformat(),
                            stop=(program.start + timedelta(seconds=program.duration)).isoformat(),
                            title=program.program_title,
                            subtitle=program.episode_title,
                            description=program.description,
                            episode='S%sE%s' % (program.season, program.number) if program.season and program.number else None,
                            genre=program.genre,
                            genre_id=program.genre_id,
                            image=program.thumb,
                            stream=kodiutils.url_for('play_from_page',
                                                     channel=key,
                                                     page=quote(program.video_url, safe='')) if program.video_url else None)
                        for program in epg if program.duration
                    ])

        return dict(version=1, epg=results)
