# -*- coding: utf-8 -*-
"""

    Copyright (C) 2013-2019 PleXBMC Helper (script.plexbmc.helper)
        by wickning1 (aka Nick Wing), hippojay (Dave Hawes-Johnson)
    Copyright (C) 2019-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import socket
import traceback

from six.moves import http_client

from ..addon.logger import Logger

LOG = Logger()


class RequestManager:
    def __init__(self):
        self.connections = {}
        self.uri = URIContainer

    def get_connection(self, uri):
        connection = self.connections.get(uri.protocol + uri.host + str(uri.port), False)
        if not connection:
            if uri.protocol == 'https':
                connection = http_client.HTTPSConnection(uri.host, uri.port)
            else:
                connection = http_client.HTTPConnection(uri.host, uri.port)
            self.connections[uri.protocol + uri.host + str(uri.port)] = connection
        return connection

    def close_connection(self, uri):
        connection = self.connections.get(uri.protocol + uri.host + str(uri.port), False)
        if connection and not isinstance(connection, bool):
            connection.close()
            self.connections.pop(uri.protocol + uri.host + str(uri.port), None)

    def dump_connections(self):
        connections = self.connections.values()
        for connection in connections:
            connection.close()
        self.connections = {}

    def post(self, uri, path, body, header=None):
        if header is None:
            header = {}

        connection = None
        try:
            connection = self.get_connection(uri)
            header['Connection'] = 'keep-alive'
            connection.request('POST', path, body, header)
            data = connection.getresponse()
            if int(data.status) >= 400:
                LOG.debug('HTTP response error: ' + str(data.status))
                # this should return false, but I'm hacking it since iOS returns 404 no matter what
                return data.read() or True

            return data.read() or True
        except:  # pylint: disable=bare-except
            LOG.debug('Unable to connect to %s\nReason:' % uri.host)
            LOG.debug(traceback.print_exc())
            self.connections.pop(uri.protocol + uri.host + str(uri.port), None)
            if connection:
                connection.close()
            return False

    def get_with_params(self, uri, path, params, header=None):
        if header is None:
            header = {}

        params = '&'.join(map(lambda x: '='.join([str(x), str(params[x])]), params))
        path = '?'.join([path, params])
        return self.get(uri, path, header)

    def get(self, uri, path, header=None):
        if header is None:
            header = {}

        connection = None
        try:
            connection = self.get_connection(uri)
            header['Connection'] = 'keep-alive'
            connection.request('GET', path, headers=header)
            data = connection.getresponse()
            if int(data.status) >= 400:
                LOG.debug('HTTP response error: ' + str(data.status))
                result = False
            else:
                result = data.read() or True
        except socket.error as error:
            if error.errno not in [10061, 10053]:
                LOG.debug('Unable to connect to %s\nReason: %s' % (uri.host, traceback.print_exc()))
                self.connections.pop(uri.protocol + uri.host + str(uri.port), None)
            result = False
        finally:
            if connection:
                connection.close()

        return result


class URIContainer:
    def __init__(self, host, port=32400, protocol='http'):
        self._protocol = 'http'
        self.protocol = protocol
        self._host = ''
        self.host = host
        self._port = 32400
        self.port = port

    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, value):
        _protocol = 'http'
        if value == 'https':
            _protocol = 'https'
        self._protocol = _protocol

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    @property
    def port(self):
        return int(self._port)

    @port.setter
    def port(self, value):
        self._port = int(value)

    def __str__(self):
        return '%s://%s:%d' % (self.protocol, self.host, self.port)
