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
import traceback

from kodi_six import xbmc  # pylint: disable=import-error
from six.moves.BaseHTTPServer import BaseHTTPRequestHandler
from six.moves.BaseHTTPServer import HTTPServer
from six.moves.socketserver import ThreadingMixIn
from six.moves.urllib_parse import parse_qs
from six.moves.urllib_parse import urlparse

from ..addon.common import get_platform
from ..addon.constants import CONFIG
from ..addon.logger import Logger
from .utils import get_ok_message
from .utils import get_player_ids
from .utils import get_players
from .utils import get_plex_headers
from .utils import get_xml_header
from .utils import jsonrpc
from .utils import millis_to_time

LOG = Logger()


class PlexCompanionHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, settings, *args, **kwargs):
        self.settings = settings
        self.server_list = []
        self.client_details = self.settings.companion_receiver()
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def log_message(self, format, *args):  # pylint: disable=redefined-builtin, unused-argument
        # I have my own logging, suppressing BaseHTTPRequestHandler's
        # LOG.debug(format % args)
        return True

    def do_HEAD(self):  # pylint: disable=invalid-name
        LOG.debug('Serving HEAD request...')
        self.answer_request(0)

    def do_GET(self):  # pylint: disable=invalid-name
        LOG.debug('Serving GET request...')
        self.answer_request(1)

    def do_OPTIONS(self):  # pylint: disable=invalid-name
        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.send_header('X-Plex-Client-Identifier', self.client_details['uuid'])
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Connection', 'close')
        self.send_header('Access-Control-Max-Age', '1209600')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, HEAD')
        self.send_header('Access-Control-Allow-Headers', 'x-plex-version, '
                                                         'x-plex-platform-version, '
                                                         'x-plex-username, '
                                                         'x-plex-client-identifier, '
                                                         'x-plex-target-client-identifier, '
                                                         'x-plex-device-name, '
                                                         'x-plex-platform, '
                                                         'x-plex-product, '
                                                         'accept, '
                                                         'x-plex-device')
        self.end_headers()
        self.wfile.close()

    def response(self, body, headers=None, code=200):
        if headers is None:
            headers = {}

        try:
            self.send_response(code)
            for key in headers:
                self.send_header(key, headers[key])
            self.send_header('Content-Length', len(body))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(body)
            self.wfile.close()
        except:  # pylint: disable=bare-except
            pass

    def answer_request(self, send_data):
        _ = send_data
        self.server_list = self.server.client.get_server_list()

        try:
            request_path = self.path[1:]
            request_path = re.sub(r'\?.*', '', request_path)
            url = urlparse(self.path)

            param_arrays = parse_qs(url.query)
            params = {}
            for key, value in param_arrays.items():
                params[key] = value[0]

            LOG.debug('request path is: [%s]' % (request_path,))
            LOG.debug('params are: %s' % params)

            self.server.subscription_manager.update_command_id(
                self.headers.get('X-Plex-Client-Identifier', self.client_address[0]),
                params.get('commandID', False)
            )

            responded = self._r_listener(request_path, params)
            if responded:
                return

            responded = self._r_playback(request_path, params)
            if responded:
                return

            responded = self._r_player_control(request_path, params)
            if responded:
                return

            responded = self._r_navigation(request_path)
            if responded:
                return

            LOG.debug('request went unanswered')

        except:  # pylint: disable=bare-except
            LOG.debug(traceback.print_exc())

    def _r_listener(self, path, params):
        responded = False

        if path == 'version':
            self.response('Remote Redirector: Running\r\nVersion: %s' % CONFIG['version'])
            responded = True

        elif path == 'verify':
            result = jsonrpc('ping')
            self.response('Kodi JSON connection test:\r\n' + result)
            responded = True

        elif path == 'resources':
            response = get_xml_header()
            response += '<MediaContainer>'
            response += '<Player'
            response += ' title="%s"' % self.client_details['name']
            response += ' protocol="plex"'
            response += ' protocolVersion="1"'
            response += ' protocolCapabilities="navigation,playback,timeline"'
            response += ' machineIdentifier="%s"' % self.client_details['uuid']
            response += ' product="%s"' % CONFIG['name']
            response += ' platform="%s"' % get_platform()
            response += ' platformVersion="%s"' % CONFIG['version']
            response += ' deviceClass="pc"'
            response += '/>'
            response += '</MediaContainer>'
            LOG.debug('crafted resources response: %s' % response)
            self.response(response, get_plex_headers(self.settings))
            responded = True

        elif '/subscribe' in path:
            self.response(get_ok_message(), get_plex_headers(self.settings))
            subscriber_data = {
                'protocol': params.get('protocol', False),
                'host': self.client_address[0],
                'port': params.get('port', False),
                'uuid': self.headers.get('X-Plex-Client-Identifier', ''),
                'command_id': params.get('commandID', 0),
            }
            self.server.subscription_manager.add_subscriber(subscriber_data)
            responded = True

        elif '/poll' in path:
            if params.get('wait', False) == '1':
                xbmc.sleep(950)
            command_id = params.get('commandID', 0)
            self.response(
                re.sub(r'INSERTCOMMANDID', str(command_id),
                       self.server.subscription_manager.msg(get_players())),
                {
                    'X-Plex-Client-Identifier': self.client_details['uuid'],
                    'Access-Control-Expose-Headers': 'X-Plex-Client-Identifier',
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'text/xml'
                }
            )
            responded = True

        elif '/unsubscribe' in path:
            self.response(get_ok_message(), get_plex_headers(self.settings))
            uuid = self.headers.get('X-Plex-Client-Identifier', False) or self.client_address[0]
            self.server.subscription_manager.remove_subscriber(uuid)
            responded = True

        return responded

    def _r_playback(self, path, params):
        responded = False

        if path == 'player/playback/setParameters':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            if 'volume' in params:
                volume = int(params['volume'])
                LOG.debug('adjusting the volume to %s%%' % volume)
                jsonrpc('Application.SetVolume', {
                    'volume': volume
                })
            responded = True

        elif '/playMedia' in path:
            self.response(get_ok_message(), get_plex_headers(self.settings))
            resume = params.get('viewOffset', params.get('offset', '0'))
            protocol = params.get('protocol', 'http')
            address = params.get('address', self.client_address[0])
            server = self.server.subscription_manager.get_server_by_host(address)
            port = params.get('port', server.get('port', '32400'))
            full_url = protocol + '://' + address + ':' + port + params['key']
            LOG.debug('playMedia command -> full url: %s' % full_url)
            jsonrpc('playmedia', [full_url, resume])
            self.server.subscription_manager.last_key = params['key']
            self.server.subscription_manager.server = server.get('server', 'localhost')
            self.server.subscription_manager.port = port
            self.server.subscription_manager.protocol = protocol
            self.server.subscription_manager.notify()
            responded = True

        elif path == 'player/playback/play':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            for player_id in get_player_ids():
                jsonrpc('Player.PlayPause', {
                    'playerid': player_id,
                    'play': True
                })
            responded = True

        elif path == 'player/playback/pause':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            for player_id in get_player_ids():
                jsonrpc('Player.PlayPause', {
                    'playerid': player_id,
                    'play': False
                })
            responded = True

        elif path == 'player/playback/stop':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            for player_id in get_player_ids():
                jsonrpc('Player.Stop', {
                    'playerid': player_id
                })
            responded = True

        return responded

    def _r_player_control(self, path, params):
        responded = False

        if path == 'player/playback/seekTo':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            for player_id in get_player_ids():
                jsonrpc('Player.Seek', {
                    'playerid': player_id,
                    'value': millis_to_time(params.get('offset', 0))
                })
            self.server.subscription_manager.notify()
            responded = True

        elif path == 'player/playback/stepForward':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            for player_id in get_player_ids():
                jsonrpc('Player.Seek', {
                    'playerid': player_id,
                    'value': 'smallforward'
                })
            self.server.subscription_manager.notify()
            responded = True

        elif path == 'player/playback/stepBack':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            for player_id in get_player_ids():
                jsonrpc('Player.Seek', {
                    'playerid': player_id,
                    'value': 'smallbackward'
                })
            self.server.subscription_manager.notify()
            responded = True

        elif path == 'player/playback/skipNext':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            for player_id in get_player_ids():
                jsonrpc('Player.Seek', {
                    'playerid': player_id,
                    'value': 'bigforward'
                })
            self.server.subscription_manager.notify()
            responded = True

        elif path == 'player/playback/skipPrevious':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            for player_id in get_player_ids():
                jsonrpc('Player.Seek', {
                    'playerid': player_id,
                    'value': 'bigbackward'
                })
            self.server.subscription_manager.notify()
            responded = True

        return responded

    def _r_navigation(self, path):
        responded = False

        if path == 'player/navigation/moveUp':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            jsonrpc('Input.Up')
            responded = True

        elif path == 'player/navigation/moveDown':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            jsonrpc('Input.Down')
            responded = True

        elif path == 'player/navigation/moveLeft':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            jsonrpc('Input.Left')
            responded = True

        elif path == 'player/navigation/moveRight':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            jsonrpc('Input.Right')
            responded = True

        elif path == 'player/navigation/select':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            jsonrpc('Input.Select')
            responded = True

        elif path == 'player/navigation/home':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            jsonrpc('Input.Home')
            responded = True

        elif path == 'player/navigation/back':
            self.response(get_ok_message(), get_plex_headers(self.settings))
            jsonrpc('Input.Back')
            responded = True

        return responded


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

    def __init__(self, client, subscription_manager, *args, **kwargs):
        self.client = client
        self.subscription_manager = subscription_manager
        HTTPServer.__init__(self, *args, **kwargs)
