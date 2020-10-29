# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
""" Implementation of IPTVManager class """

from __future__ import absolute_import, division, unicode_literals


class IPTVManager:
    """ Interface to IPTV Manager """

    def __init__(self, port):
        """ Initialize IPTV Manager object. """
        self.port = port

    def via_socket(func):  # pylint: disable=no-self-argument
        """ Send the output of the wrapped function to socket. """

        def send(self):
            """ Decorator to send data over a socket. """
            import json
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())  # pylint: disable=not-callable
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):  # pylint: disable=no-method-argument,no-self-use
        """ Return JSON-STREAMS formatted information to IPTV Manager. """
        from kodiutils import addon_icon

        streams = []

        streams.append(dict(
            name="Red Bull TV",
            stream="plugin://plugin.video.redbulltv/iptv/play",
            id="redbulltv",
            logo=addon_icon(),
            preset=88,
        ))

        return dict(version=1, streams=streams)

    @via_socket
    def send_epg(self):  # pylint: disable=no-method-argument,no-self-use
        """ Return JSON-EPG formatted information to IPTV Manager. """
        from collections import defaultdict
        from datetime import datetime
        from dateutil.tz import UTC
        from kodiutils import url_for
        from redbull import RedBullTV

        redbull = RedBullTV()

        epg = defaultdict(list)
        for item in redbull.get_epg().get('items'):
            epg['redbulltv'].append(dict(
                start=datetime.strptime(item.get('start_time'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC).isoformat(),
                stop=datetime.strptime(item.get('end_time'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC).isoformat(),
                title=item.get('title'),
                description=item.get('long_description'),
                subtitle=item.get('subheading'),
                genre='Sport',
                image=redbull.get_image_url(item.get('id'), item.get('resources'), 'landscape'),
                stream=url_for('play_uid', uid=item.get('id'))
            ))

        return dict(version=1, epg=epg)
