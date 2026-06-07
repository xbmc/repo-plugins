# -*- coding: utf-8 -*-
"""

    Copyright (C) 2013-2019 PleXBMC Helper (script.plexbmc.helper)
        by wickning1 (aka Nick Wing), hippojay (Dave Hawes-Johnson)
    Copyright (C) 2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import re

from kodi_six import xbmcgui  # pylint: disable=import-error

from ..addon.logger import Logger
from .utils import get_audio_player_id
from .utils import get_photo_player_id
from .utils import get_players
from .utils import get_plex_headers
from .utils import get_video_player_id
from .utils import get_volume
from .utils import get_xml_header
from .utils import jsonrpc
from .utils import kodi_photo
from .utils import kodi_video
from .utils import plex_audio
from .utils import plex_photo
from .utils import plex_video
from .utils import time_to_millis

LOG = Logger()
WINDOW = xbmcgui.Window(10000)


class SubscriptionManager:  # pylint: disable=too-many-instance-attributes,
    def __init__(self, settings, request_manager):
        self.request_manager = request_manager
        self.subscribers = {}
        self.settings = settings
        self.info = {}
        self.last_key = ''
        self.last_rating_key = ''
        self.volume = 0
        self.guid = ''
        self.server = ''
        self.server_list = []
        self.protocol = 'http'
        self.port = ''
        self.main_location = ''
        self.player_props = {}
        self.sent_stopped = True

    def get_server_by_host(self, host):
        if len(self.server_list) == 1:
            return self.server_list[0]

        return next((server for server in self.server_list
                     if server.get('serverName') in host or server.get('server') in host), {})

    def get_volume(self):
        self.volume = get_volume()

    def msg(self, players):
        msg = get_xml_header()
        msg += '<MediaContainer commandID="INSERTCOMMANDID"'
        if players:
            self.get_volume()
            maintype = plex_audio()
            _players = players.values()
            for player in _players:
                if player.get('type') == kodi_video():
                    maintype = plex_video()
                elif player.get('type') == kodi_photo():
                    maintype = plex_photo()
            self.main_location = 'fullScreen' + maintype[0:1].upper() + maintype[1:].lower()
        else:
            self.main_location = 'navigation'
        msg += ' location="%s">' % self.main_location

        msg += self.get_timeline_xml(get_audio_player_id(players), plex_audio())
        msg += self.get_timeline_xml(get_photo_player_id(players), plex_photo())
        msg += self.get_timeline_xml(get_video_player_id(players), plex_video())
        msg += '\r\n</MediaContainer>'
        return msg

    def get_server(self):
        server = str(WINDOW.getProperty('plugin.video.composite-nowplaying.server'))
        if server:
            self.server, self.port = server.split(':')

    @staticmethod
    def get_key_id():
        return str(WINDOW.getProperty('plugin.video.composite-nowplaying.id'))

    def get_timeline_xml(self, player_id, ptype):
        if player_id is not None:
            info = self.get_player_properties(player_id)
            # save this info off so the server update can use it too
            self.player_props[player_id] = info
            state = info['state']
            time = info['time']
        else:
            info = {}
            state = 'stopped'
            time = 0
        ret = '\r\n' + '<Timeline location="%s" state="%s" time="%s" type="%s"' % \
              (self.main_location, state, time, ptype)
        if player_id is not None:
            self.get_server()
            key_id = self.get_key_id()
            if key_id:
                self.last_key = '/library/metadata/%s' % key_id
                self.last_rating_key = key_id
            server = self.get_server_by_host(self.server)
            ret += ' duration="%s"' % info['duration']
            ret += ' seekRange="0-%s"' % info['duration']
            ret += ' controllable="%s"' % self.controllable()
            ret += ' machineIdentifier="%s"' % server.get('uuid', '')
            ret += ' protocol="%s"' % server.get('protocol', 'http')
            ret += ' address="%s"' % server.get('server', self.server)
            ret += ' port="%s"' % server.get('port', self.port)
            ret += ' guid="%s"' % info['guid']
            ret += ' containerKey="%s"' % (self.last_key or '/library/metadata/900000')
            ret += ' key="%s"' % (self.last_key or '/library/metadata/900000')
            ret += ' ratingKey="%s"' % (self.last_rating_key or '900000')
            ret += ' volume="%s"' % info['volume']
            ret += ' shuffle="%s"' % info['shuffle']

        ret += '/>'
        return ret

    def update_command_id(self, uuid, command_id):
        if command_id and self.subscribers.get(uuid, False):
            self.subscribers[uuid].command_id = int(command_id)

    def notify(self, event=False):
        _ = event
        self.cleanup()
        players = get_players()
        # fetch the message, subscribers or not, since the server
        # will need the info anyway
        msg = self.msg(players)
        if self.subscribers:
            is_nav = len(players) == 0
            subs = self.subscribers.values()
            for sub in subs:
                sub.send_update(msg, is_nav)

        self.notify_server(players)

        return True

    def notify_server(self, players):
        if not players and self.sent_stopped:
            return

        params = {
            'state': 'stopped'
        }
        _players = players.values()
        for player in _players:
            info = self.player_props[player.get('player_id')]
            params = {
                'containerKey': (self.last_key or '/library/metadata/900000'),
                'key': (self.last_key or '/library/metadata/900000'),
                'ratingKey': (self.last_rating_key or '900000'),
                'state': info['state'],
                'time': info['time'],
                'duration': info['duration'],
            }
        self.get_server()
        server = self.get_server_by_host(self.server)

        self.request_manager.get_with_params(
            self.request_manager.uri(
                server.get('server', 'localhost'),
                server.get('port', 32400),
                server.get('protocol', 'http')
            ),
            '/:/timeline', params, get_plex_headers(self.settings)
        )

        LOG.debug('sent server notification with state = %s' % params['state'])
        if players:
            self.sent_stopped = False
        else:
            self.sent_stopped = True

    @staticmethod
    def controllable():
        return 'playPause,play,stop,skipPrevious,skipNext,volume,stepBack,stepForward,seekTo'

    def add_subscriber(self, data):
        sub = Subscriber(data, self.request_manager, self)
        self.subscribers[sub.uuid] = sub
        return sub

    def remove_subscriber(self, uuid):
        subs = self.subscribers.values()
        for sub in subs:
            if uuid in [sub.uuid, sub.host]:
                sub.cleanup()
                del self.subscribers[sub.uuid]

    def cleanup(self):
        subs = self.subscribers.values()
        for sub in subs:
            if sub.age > 30:
                sub.cleanup()
                del self.subscribers[sub.uuid]

    def get_player_properties(self, player_id):
        info = {}
        try:
            # get info from the player
            props = jsonrpc('Player.GetProperties', {
                'playerid': player_id,
                'properties': ['time', 'totaltime', 'speed', 'shuffled']
            })
            LOG.debug(jsonrpc('Player.GetItem', {
                'playerid': player_id,
                'properties': ['file', 'showlink', 'episode', 'season']
            }))
            info['time'] = time_to_millis(props['time'])
            info['duration'] = time_to_millis(props['totaltime'])
            info['state'] = ('paused', 'playing')[int(props['speed'])]
            info['shuffle'] = ('0', '1')[props.get('shuffled', False)]
        except:  # pylint: disable=bare-except
            info['time'] = 0
            info['duration'] = 0
            info['state'] = 'stopped'
            info['shuffle'] = False
        # get the volume from the application
        info['volume'] = self.volume
        info['guid'] = self.guid

        return info


class Subscriber:
    def __init__(self, data, request_manager, subscription_manager):
        self.data = data
        self.request_manager = request_manager
        self.subscription_manager = subscription_manager

        self.nav_location_sent = False
        self.age = 0

    @property
    def protocol(self):
        return self.data.get('protocol') or 'http'

    @property
    def host(self):
        return self.data.get('host')

    @property
    def port(self):
        return self.data.get('port') or 32400

    @property
    def uuid(self):
        return self.data.get('uuid') or self.data.get('host')

    @property
    def command_id(self):
        return int(self.data.get('command_id')) or 0

    def __eq__(self, other):
        return self.uuid == other.uuid

    def tostr(self):
        return 'uuid=%s,commandID=%i' % (self.uuid, self.command_id)

    def cleanup(self):
        self.request_manager.close_connection(
            self.request_manager.uri(self.host, self.port, self.protocol)
        )

    def send_update(self, msg, is_nav):
        self.age += 1
        if not is_nav:
            self.nav_location_sent = False
        elif self.nav_location_sent:
            return
        else:
            self.nav_location_sent = True
        msg = re.sub(r'INSERTCOMMANDID', str(self.command_id), msg)
        LOG.debug('sending xml to subscriber %s: %s' % (self.tostr(), msg))

        if not self.request_manager.post(
                self.request_manager.uri(self.host, self.port, self.protocol), '/:/timeline',
                msg, get_plex_headers(self.subscription_manager.settings)
        ):
            self.subscription_manager.remove_subscriber(self.uuid)
