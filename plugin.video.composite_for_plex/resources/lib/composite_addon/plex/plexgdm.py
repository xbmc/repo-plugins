# -*- coding: utf-8 -*-
"""

    This class implements the Plex GDM (G'Day Mate) protocol to discover
    local Plex Media Servers. Also allow client registration into all local
    media servers.

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import socket
import struct
import threading
import time
from contextlib import closing

from six.moves.urllib_request import urlopen

from ..addon.logger import Logger
from ..addon.strings import decode_utf8
from ..addon.strings import encode_utf8

LOG = Logger('PlexGDM')


class PlexGDM:  # pylint: disable=too-many-instance-attributes

    def __init__(self, interface=None):

        self.client_header = '* HTTP/1.0'
        self.client_data = None
        self.client_id = None

        self.interface = interface

        self._multicast_address = '239.0.0.250'
        self.discover_group = (self._multicast_address, 32414)
        self.client_register_group = (self._multicast_address, 32413)
        self.client_update_port = 32412

        self.server_list = []
        self.discovery_interval = 120

        self._discovery_is_running = False
        self._registration_is_running = False

        self.discovery_complete = False
        self.client_registered = False

        self.discover_t = None
        self.register_t = None

    def client_details(self, data):
        self.client_data = 'Content-Type: plex/media-player\nResource-Identifier: %s\nName: %s\n' \
                           'Port: %s\nProduct: %s\nVersion: %s' % \
                           (data['uuid'], data['name'], data['port'],
                            data['product']['name'], data['product']['version'])
        self.client_id = data['uuid']

    def get_client_details(self):
        if not self.client_data:
            LOG.error('Client data has not been initialised. Please use PlexGDM.client_details()')

        return self.client_data

    @staticmethod
    def _discover_message():
        return b'M-SEARCH * HTTP/1.0'

    def _hello_message(self):
        return b'HELLO %s\n%s' % (encode_utf8(self.client_header, py2_only=False),
                                  encode_utf8(self.client_data, py2_only=False))

    def _goodbye_message(self):
        return b'BYE %s\n%s' % (encode_utf8(self.client_header, py2_only=False),
                                encode_utf8(self.client_data, py2_only=False))

    def _ok_message(self):
        return b'HTTP/1.0 200 OK\n%s' % encode_utf8(self.client_data, py2_only=False)

    def client_update(self):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        with closing(_socket) as open_socket:

            # Set socket reuse, may not work on all OSs.
            try:
                open_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except:  # pylint: disable=bare-except
                pass

            # Attempt to bind to the socket to receive and send data.
            # If we can;t do this, then we cannot send registration
            try:
                open_socket.bind(('0.0.0.0', self.client_update_port))
            except:  # pylint: disable=bare-except
                LOG.error('Error: Unable to bind to port [%s] - client will not be registered' %
                          self.client_update_port)
                return

            open_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
            open_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                   socket.inet_aton(self._multicast_address) +
                                   socket.inet_aton('0.0.0.0'))
            # noinspection PyTypeChecker
            open_socket.setblocking(0)
            LOG.debugplus('Sending registration data: HELLO %s\n%s' %
                          (self.client_header, self.client_data))

            # Send initial client registration
            try:
                open_socket.sendto(self._hello_message(), self.client_register_group)
            except:  # pylint: disable=bare-except
                LOG.debug('Error: Unable to send registration message')

            # Now, listen for client discovery requests and respond.
            while self._registration_is_running:
                try:
                    data, address = open_socket.recvfrom(1024)
                    LOG.debug('Received UDP packet from [%s] containing [%s]' %
                              (address, data.strip()))
                except socket.error:
                    pass
                else:
                    if b'M-SEARCH * HTTP/1.' in data:
                        LOG.debug('Detected client discovery request from %s.  Replying' %
                                  str(address))
                        try:
                            open_socket.sendto(self._ok_message(), address)
                        except:  # pylint: disable=bare-except
                            LOG.debug('Error: Unable to send client update message')

                        LOG.debug('Sending registration data: HTTP/1.0 200 OK\n%s' %
                                  self.client_data)
                        self.client_registered = True
                time.sleep(0.5)

            LOG.debug('Client Update loop stopped')

            # When we are finished, then send a final goodbye message to de-register cleanly.
            LOG.debug('Sending registration data: BYE %s\n%s' %
                      (self.client_header, self.client_data))
            try:
                open_socket.sendto(self._goodbye_message(), self.client_register_group)
            except:  # pylint: disable=bare-except
                LOG.error('Error: Unable to send client update message')

            self.client_registered = False

    def check_client_registration(self):

        if self.client_registered and self.discovery_complete:

            if not self.server_list:
                LOG.debug('Server list is empty. Unable to check')
                return False

            try:
                media_server = self.server_list[0]['server']
                media_port = self.server_list[0]['port']

                LOG.debug('Checking server [%s] on port [%s]' % (media_server, media_port))
                with urlopen('http://%s:%s/clients' % (media_server, media_port)) as file_handle:
                    client_result = file_handle.read()

                if self.client_id in client_result:
                    LOG.debug('Client registration successful')
                    LOG.debug('Client data is: %s' % client_result)
                    return True

                LOG.debug('Client registration not found')
                LOG.debug('Client data is: %s' % client_result)

            except:  # pylint: disable=bare-except
                LOG.debug('Unable to check status')

        return False

    def get_server_list(self):
        return self.server_list

    @staticmethod
    def _get_server_from_response(response):
        server = {
            'server': response.get('from')[0]
        }

        # Check if we had a positive HTTP response
        if '200 OK' in response.get('data'):

            server['discovery'] = 'auto'
            server['owned'] = '1'
            server['master'] = 1
            server['role'] = 'master'
            server['class'] = None

            lines = response.get('data').split('\n')
            for pairs in lines:
                if ':' not in pairs:
                    continue

                key, value = pairs.split(':')
                value = value.strip()
                if key == 'Content-Type':
                    server['content-type'] = value
                elif key == 'Resource-Identifier':
                    server['uuid'] = value
                elif key == 'Name':
                    server['serverName'] = value
                elif key == 'Port':
                    server['port'] = value
                elif key == 'Updated-At':
                    server['updated'] = value
                elif key == 'Version':
                    server['version'] = value
                elif key == 'Server-Class':
                    server['class'] = value
                elif key == 'Host':
                    server['host'] = value

        return server

    def discover(self):
        received_data = []

        _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        with closing(_socket) as open_socket:
            # Set a timeout so the socket does not block indefinitely
            open_socket.settimeout(0.6)

            # Set the time-to-live for messages to 1 for local network
            ttl = struct.pack('b', 1)
            open_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

            if self.interface:
                open_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF,
                                       socket.inet_aton(self.interface))

            # Send data to the multicast group
            LOG.debug('Sending discovery messages ...')
            # noinspection PyUnusedLocal
            _ = open_socket.sendto(self._discover_message(), self.discover_group)
            # Look for responses from all recipients
            while True:
                try:
                    data, server = open_socket.recvfrom(1024)
                    LOG.debug('Received data from %s:%s' % (server[0], server[1]))
                    LOG.debug('Data received is:\n %s' % data)
                    received_data.append({
                        'from': server,
                        'data': decode_utf8(data)
                    })
                except socket.timeout:
                    break

        self.discovery_complete = True

        self.server_list = list(map(self._get_server_from_response, received_data))

        if not self.server_list:
            LOG.debug('No servers have been discovered')
        else:
            LOG.debug('Number of servers Discovered: %s' % len(self.server_list))
            for items in self.server_list:
                LOG.debug('Server Discovered: %s' % items['serverName'])

    def set_interval(self, interval):
        self.discovery_interval = interval

    def stop_all(self):
        self.stop_discovery()
        self.stop_registration()

    def stop_discovery(self):
        if self._discovery_is_running:
            LOG.debug('Discovery shutting down')
            self._discovery_is_running = False
            self.discover_t.join()
            del self.discover_t
        else:
            LOG.debug('Discovery not running')

    def stop_registration(self):
        if self._registration_is_running:
            LOG.debug('Registration shutting down')
            self._registration_is_running = False
            self.register_t.join()
            del self.register_t
        else:
            LOG.debug('Registration not running')

    def run_discovery_loop(self):
        # Run initial discovery
        self.discover()

        discovery_count = 0
        while self._discovery_is_running:
            discovery_count += 1
            if discovery_count > self.discovery_interval:
                self.discover()
                discovery_count = 0
            time.sleep(1)

    def start_discovery(self, daemon=False):
        if not self._discovery_is_running:
            LOG.debug('Discovery starting up')
            self._discovery_is_running = True
            self.discover_t = threading.Thread(target=self.run_discovery_loop)
            self.discover_t.daemon = daemon
            self.discover_t.start()
        else:
            LOG.debug('Discovery already running')

    def start_registration(self, daemon=False):
        if not self._registration_is_running:
            LOG.debug('Registration starting up')
            self._registration_is_running = True
            self.register_t = threading.Thread(target=self.client_update)
            self.register_t.daemon = daemon
            self.register_t.start()
        else:
            LOG.debug('Registration already running')

    def start_all(self, daemon=False):
        self.start_discovery(daemon)
        self.start_registration(daemon)
