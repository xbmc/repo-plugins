'''
    qobuz.service.httpd
    ~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import re
import sys

VERSION = '0.0.1'

username = password = base_path = stream_type = stream_format = None
cache_duration_long = 60 * 60 * 24 * 365
cache_duration_middle = 60 * 60 * 24 * 365
stream_format = 5
__image__ = ''


import xbmcaddon  # @UnresolvedImport
import xbmc  # @UnresolvedImport
import os
pluginId = 'plugin.audio.qobuz'
__addon__ = xbmcaddon.Addon(id=pluginId)
__addonversion__ = __addon__.getAddonInfo('version')
__addonid__ = __addon__.getAddonInfo('id')
__cwd__ = __addon__.getAddonInfo('path')
__addondir__ = __addon__.getAddonInfo('path')
__libdir__ = xbmc.translatePath(os.path.join(__addondir__, 'resources', 'lib'))
__qobuzdir__ = xbmc.translatePath(os.path.join(__libdir__, 'qobuz'))
sys.path.append(__libdir__)
sys.path.append(__qobuzdir__)

from bootstrap import QobuzBootstrap
__handle__ = -1
boot = QobuzBootstrap(__addon__, __handle__)
boot.bootstrap_directories()


def try_get_settings():
    global username, password
    username = __addon__.getSetting('username')
    password = __addon__.getSetting('password')
    if username and password:
        return True
    return False

while not (try_get_settings()):
    xbmc.sleep(5000)

import qobuz  # @UnresolvedImport
from api import api
from cache import cache
cache.base_path = qobuz.path.cache
api.login(username, password)


stream_format = 6 if __addon__.getSetting('streamtype') == 'flac' else 5
cache_durationm_middle = int(
    __addon__.getSetting('cache_duration_middle')) * 60
cache_duration_long = int(__addon__.getSetting('cache_duration_long')) * 60

if stream_format == 6:
    stream_mime = 'audio/flac'
else:
    stream_mime = 'audio/mpeg'

from debug import log
from node import getNode, Flag


class XbmcAbort(Exception):

    def __init__(self, *a, **ka):
        super(XbmcAbort, self).__init__(*a, **ka)


class BadRequest(Exception):

    def __init__(self, *a, **ka):
        self.code = 400
        self.message = 'Bad Request '
        super(BadRequest, self).__init__(*a, **ka)


class Unauthorized(Exception):

    def __init__(self, *a, **ka):
        self.code = 401
        self.message = 'Unauthorized '
        super(Unauthorized, self).__init__(*a, **ka)


class RequestFailed(Exception):

    def __init__(self, *a, **ka):
        self.code = 402
        self.message = 'Request Failed'
        super(RequestFailed, self).__init__(*a, **ka)


class ServerErrors(Exception):

    def __init__(self, *a, **ka):
        self.code = 500
        self.message = 'Server errors'
        super(ServerErrors, self).__init__(*a, **ka)


class QobuzResponse:

    def __init__(self, request):
        self.request = request
        if not self.__parse_path(request.path):
            raise RequestFailed()

    @property
    def path(self):
        return self._path

    @path.getter
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self.reset_request()
        self.__parse_path(value)
        self._path = value

    def reset_request(self):
        self.path = None
        self.request = None
        self.fileExt = None
        self.track_id = None
        self.album_id = None
        self.artist_id = None
        self.fileWanted = None

    def __parse_path(self, path):
        m = re.search('^/qobuz/(\d+)/(.*)$', path)
        if not m:
            return False
        self.artist_id = m.group(1)
        m = re.search('^(\d+)/(.*)$', m.group(2))
        if not m:
            return False
        self.album_id = m.group(1)
        m = re.search('^(\d+|cdart)\.(mp3|mpc|flac|png)', m.group(2))
        if not m:
            return False
        self.track_id = m.group(1)
        self.fileExt = m.group(2)
        self.fileWanted = 'music'
        return True


class QobuzHttpResolver_Handler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        # FIXME workaround for exceptions in logs
        # when the client broke connexion
        try:
            BaseHTTPRequestHandler.__init__(self, request, client_address,
                                            server)
        except:
            pass
        self.server_version = 'QobuzXbmcHTTP/0.0.1'

    def __GET_track(self, request):
        api.login(api.username, api.password)
        node = getNode(Flag.TRACK, {'nid': request.track_id})
        streaming_url = node.get_streaming_url()
        if not streaming_url:
            raise RequestFailed()
        self.send_response(303, "Resolved")
        self.send_header('content-type', stream_mime)
        self.send_header('location', streaming_url)
        self.end_headers()

    def do_GET(self):
        try:
            request = QobuzResponse(self)
            if request.fileWanted == 'music':
                return self.__GET_track(request)
            else:
                raise BadRequest()
        except BadRequest as e:
            pass
        except Unauthorized as e:
            self.send_error(e.code, e.message)
        except RequestFailed as e:
            self.send_error(e.code, e.message)
        except Exception as e:
            msg = 'Server errors (%s / %s)\n%s' % (
                sys.exc_type, sys.exc_value,
                repr(e))
            self.log_message(msg)
            self.send_error(500, msg)

    def do_HEAD(self):
        try:
            request = QobuzResponse(self)
            if request.fileWanted == 'music':
                self.send_response(200, "Ok ;)")
                self.send_header('content-type', stream_mime)
                self.end_headers()
                return True
            else:
                self.send_response(404, "Nops")
                self.send_header('Content-Type',
                                 'text/html; charset=iso-8859-1')
                self.end_headers()
                return True
        except Unauthorized as e:
            self.send_error(e.code, e.message)
        except RequestFailed as e:
            self.send_error(e.code, e.message)
        except Exception as e:
            msg = 'Server errors (%s / %s)\n%s' % (
                sys.exc_type, sys.exc_value,
                repr(e))
            self.log_message(msg)
            self.send_error(500, msg)

# import select
from SocketServer import ThreadingMixIn
# import threading


class QobuzHttpResolver(ThreadingMixIn, HTTPServer):

    def abortRequested(self):
        try:
            return xbmc.abortRequested
        except:
            False
        return False

    def verify_request(self, path, client_address):
        host, _port = client_address
        if host == '127.0.0.1':
            return True
        return False


class QobuzXbmcHttpResolver(QobuzHttpResolver):

    def __init__(self):
        QobuzHttpResolver.__init__(self, ('127.0.0.1', 33574),
                                   QobuzHttpResolver_Handler)


def main():
    server = None
    try:
        server = QobuzXbmcHttpResolver()
        log(server, 'Starting Qobuz Resolver')
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
    except XbmcAbort:
        log(server, 'Received xbmc abort... closing')
    finally:
        if server:
            server.socket.close()
            server = None

if __name__ == '__main__':
    main()
