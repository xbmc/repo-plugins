
# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2024 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------
import json
import socket
import xbmc

from codequick.script import Script
from codequick.support import build_path


# Logo URLs from now/next.
CHANNELS = {
    'ITV': {'id': 'viwx.itv',
            'name': 'ITV',
            'logo': 'https://images.ctfassets.net/bd5zurrrnk1g/54OefyIkbiHPMJUYApbuUX/7dfe2176762fd8ec10f77cd61a318b07/itv1.png?w=512',
            'preset': 1},
    'ITV2': {'id': 'viwx.itv2',
             'name': 'ITV2',
             'logo': 'https://images.ctfassets.net/bd5zurrrnk1g/aV9MOsYOMEXHx3iw0p4tk/57b35173231c4290ff199ef8573367ad/itv2.png?w=512',
             'preset': 2},
    'ITVBe': {'id': 'viwx.itvbe',
              'name': 'ITVBe',
              'logo': 'https://images.ctfassets.net/bd5zurrrnk1g/6Mul5JVrb06pRu8bNDgIAe/b5309fa32322cc3db398d25e523e2b2e/itvBe.png?w=512',
              'preset': 3},
    'ITV3': {'id': 'viwx.itv3',
             'name': 'ITV3',
             'logo': 'https://images.ctfassets.net/bd5zurrrnk1g/39fJAu9LbUJptatyAs8HkL/80ac6eb141104854b209da946ae7a02f/itv3.png?w=512',
             'preset': 4},
    'ITV4': {'id': 'viwx.itv4',
             'name': 'ITV4',
             'logo': 'https://images.ctfassets.net/bd5zurrrnk1g/6Dv76O9mtWd6m7DzIavtsf/b3d491289679b8030eae7b4a7db58f2d/itv4.png?w=512',
             'preset': 5}
}


# IPTVManager class from https://github.com/add-ons/service.iptv.manager/wiki/Integration
class IPTVManager:
    """Interface to IPTV Manager"""

    def __init__(self, port):
        """Initialize IPTV Manager object"""
        self.port = port

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
        from resources.lib.main import play_stream_live
        chan_list = [
            {
                'id': chan_data.get('id'),
                'name': chan_data.get('name'),
                'logo': chan_data.get('logo'),
                'stream': build_path(play_stream_live, query={'channel': name, 'url': None})
            } for name, chan_data in CHANNELS.items()
        ]
        return {'version': 1, 'streams': chan_list}

    @via_socket
    def send_epg(self):
        """Return JSON-EPG formatted python data structure to IPTV Manager"""
        from resources.lib.itvx import get_full_schedule

        schedules = get_full_schedule()
        epg = {CHANNELS[k]['id']: v for k, v in schedules.items()}
        return dict(version=1, epg=epg)


@Script.register
def channels(_, port):
    try:
        IPTVManager(int(port)).send_channels()
    except Exception as err:
        # Catch all errors to prevent codequick showing an error message
        xbmc.log("[viwX] Error in iptvmanager.channels: {!r}.".format(err))


@Script.register
def epg(_, port):
    try:
         IPTVManager(int(port)).send_epg()
    except Exception as err:
        # Catch all errors to prevent codequick showing an error message
        xbmc.log("[viwX] Error in iptvmanager.epg: {!r}.".format(err))
