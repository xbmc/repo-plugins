# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import base64
import hashlib
import socket
import traceback
import xml.etree.ElementTree as ETree

import requests
from kodi_six import xbmcgui  # pylint: disable=import-error
from six import PY3
from six import iteritems
from six import string_types
from six.moves.urllib_parse import urlparse

from ..addon import cache_control
from ..addon.common import get_platform_ip
from ..addon.common import is_ip
from ..addon.constants import CONFIG
from ..addon.dialogs.progress_dialog import ProgressDialog
from ..addon.logger import Logger
from ..addon.server_config import ServerConfigStore
from ..addon.strings import encode_utf8
from ..addon.strings import i18n
from .plexcommon import create_plex_identification
from .plexcommon import get_client_identifier
from .plexgdm import PlexGDM
from .plexsection import PlexSection
from .plexserver import PlexMediaServer

DEFAULT_PORT = '32400'
LOG = Logger('plex')

WINDOW = xbmcgui.Window(10000)


class Plex:  # pylint: disable=too-many-public-methods, too-many-instance-attributes

    def __init__(self, settings, load=False):
        self.settings = settings
        # Provide an interface into Plex
        self.cache = cache_control.CacheControl('servers', self.settings.cache())
        self.myplex_server = 'https://plex.tv'
        self.myplex_user = None
        self.myplex_token = None
        self.effective_user = None
        self.effective_token = None
        self.server_list = {}
        self.discovered = False
        self.server_list_cache = 'discovered_plex_servers.cache'
        self.plexhome_cache = 'plexhome_user.pcache'
        self.client_id = None
        self.user_list = {}
        self.plexhome_settings = {
            'myplex_signedin': False,
            'plexhome_enabled': False,
            'myplex_user_cache': '',
            'plexhome_user_cache': '',
            'plexhome_user_avatar': ''
        }

        self.server_configs = ServerConfigStore()

        self.setup_user_token()
        if load:
            self.load()

    def plex_identification_header(self):
        self.client_id = get_client_identifier(self.settings, self.client_id)
        return create_plex_identification(self.settings, client_id=self.client_id,
                                          token=self.effective_token)

    def is_plexhome_enabled(self):
        return self.plexhome_settings['plexhome_enabled']

    def is_myplex_signedin(self):
        return self.plexhome_settings['myplex_signedin']

    def get_myplex_user(self):
        return self.effective_user

    def get_myplex_avatar(self):
        return self.plexhome_settings['plexhome_user_avatar']

    def signout(self):
        self.plexhome_settings = {
            'myplex_signedin': False,
            'plexhome_enabled': False,
            'myplex_user_cache': '',
            'plexhome_user_cache': '',
            'plexhome_user_avatar': ''
        }

        self.delete_cache(True)
        LOG.debug('Signed out from myPlex')

    def get_signin_pin(self):
        data = self.talk_to_myplex('/pins.xml', method='post')
        try:
            xml = ETree.fromstring(data)
            code = xml.find('code').text
            identifier = xml.find('id').text
        except:  # pylint: disable=bare-except
            code = None
            identifier = None

        if code is None:
            LOG.debug('Error, no code provided')
            code = '----'
            identifier = 'error'

        LOG.debug('code is: %s' % code)
        LOG.debug('id   is: %s' % identifier)

        return {
            'id': identifier,
            'code': list(code)
        }

    def check_signin_status(self, identifier):
        data = self.talk_to_myplex('/pins/%s.xml' % identifier, method='get2')
        xml = ETree.fromstring(data)
        temp_token = xml.find('auth_token').text

        LOG.debugplus('Temp token is: %s' % temp_token)

        if temp_token:
            response = requests.get('%s/users/account?X-Plex-Token=%s' %
                                    (self.myplex_server, temp_token),
                                    headers=self.plex_identification_header(),
                                    timeout=120)
            response.encoding = 'utf-8'

            LOG.debug('Status Code: %s' % response.status_code)

            if response.status_code == 200:
                try:
                    LOG.debugplus(encode_utf8(response.text, py2_only=False))
                    LOG.debug('Received new plex token')
                    xml = ETree.fromstring(encode_utf8(response.text))

                    home = xml.get('home', '0')
                    username = xml.get('username', '')
                    avatar = xml.get('thumb')

                    if avatar.startswith('https://plex.tv') or avatar.startswith('http://plex.tv'):
                        avatar = avatar.replace('//', '//i2.wp.com/', 1)
                    self.plexhome_settings['plexhome_user_avatar'] = avatar

                    if home == '1':
                        self.plexhome_settings['plexhome_enabled'] = True
                        LOG.debug('Setting Plex Home enabled.')
                    else:
                        self.plexhome_settings['plexhome_enabled'] = False
                        LOG.debug('Setting Plex Home disabled.')

                    token = xml.findtext('authentication-token')
                    self.plexhome_settings['myplex_user_cache'] = '%s|%s' % (username, token)
                    self.plexhome_settings['myplex_signedin'] = True
                    self.save_tokencache()
                    return True
                except:  # pylint: disable=bare-except
                    LOG.debug('No authentication token found')

        return False

    def load(self):
        LOG.debug('Loading cached server list')

        data_ok = False
        self.server_list = None

        if WINDOW.getProperty('plugin.video.composite-refresh.servers') != 'true':
            data_ok, self.server_list = self.cache.read_cache(self.server_list_cache)

        WINDOW.clearProperty('plugin.video.composite-refresh.servers')

        if data_ok:
            if not self.check_server_version():
                LOG.debug('Refreshing for new versions')
                data_ok = False

            if not self.check_user():
                LOG.debug('User Switch, refreshing for new authorization settings')
                data_ok = False

        if not data_ok or not self.server_list:
            LOG.debug('unsuccessful')
            self.server_list = {}
            if not self.discover():
                self.server_list = {}

        LOG.debug('Server list is now: %s' % self.server_list)

    def setup_user_token(self):

        self.load_tokencache()

        if self.plexhome_settings['myplex_signedin']:
            LOG.debug('myPlex is logged in')
        else:
            return

        self.myplex_user, self.myplex_token = self.plexhome_settings['myplex_user_cache'].split('|')

        if self.plexhome_settings['plexhome_enabled']:
            LOG.debug('Plexhome is enabled')

        try:
            self.effective_user, self.effective_token = \
                self.plexhome_settings['plexhome_user_cache'].split('|')
        except:  # pylint: disable=bare-except
            LOG.debug('No user set.  Will default to admin user')
            self.effective_user = self.myplex_user
            self.effective_token = self.myplex_token
            self.save_tokencache()

        myplex_user = self.myplex_user
        effective_user = self.effective_user
        if self.settings.privacy():
            myplex_user = hashlib.md5()
            myplex_user.update(self.myplex_user.encode('utf-8'))
            myplex_user = myplex_user.hexdigest()

            effective_user = hashlib.md5()
            effective_user.update(self.effective_user.encode('utf-8'))
            effective_user = effective_user.hexdigest()

        LOG.debug('myPlex user id: %s' % myplex_user)
        LOG.debug('Effective user id: %s' % effective_user)

    def load_tokencache(self):

        data_ok, token_cache = self.cache.read_cache(self.plexhome_cache)

        if data_ok:
            try:
                if not isinstance(token_cache['myplex_signedin'], int):
                    raise TypeError
                if not isinstance(token_cache['plexhome_enabled'], int):
                    raise TypeError
                if not isinstance(token_cache['myplex_user_cache'], string_types):
                    raise TypeError
                if not isinstance(token_cache['plexhome_user_cache'], string_types):
                    raise TypeError
                if not isinstance(token_cache['plexhome_user_avatar'], string_types):
                    raise TypeError

                self.plexhome_settings = token_cache
                LOG.debug('plexhome_cache data loaded successfully')
            except:  # pylint: disable=bare-except
                LOG.debug('plexhome_cache data is corrupt. Will not use.')
        else:
            LOG.debug('plexhome cache data not loaded')

    def save_tokencache(self):
        self.cache.write_cache(self.plexhome_cache, self.plexhome_settings)

    def check_server_version(self):
        for _uuid, servers in iteritems(self.server_list):
            try:
                if not servers.get_revision() == CONFIG['required_revision']:
                    LOG.debug('Old object revision found')
                    return False
            except:  # pylint: disable=bare-except
                LOG.debug('No revision found')
                return False
        return True

    def check_user(self):

        if self.effective_user is None:
            return True

        for _uuid, servers in iteritems(self.server_list):
            if not servers.get_user() == self.effective_user:
                LOG.debug('authorized user mismatch')
                return False
        return True

    def discover(self):
        self.discover_all_servers()

        if self.server_list:
            self.discovered = True

        return self.discovered

    def get_server_list(self):
        return self.server_list.values()

    def talk_direct_to_server(self, ip_address='localhost', port=DEFAULT_PORT, url=None):
        response = requests.get('http://%s:%s%s' % (ip_address, port, url),
                                params=self.plex_identification_header(), timeout=2)
        response.encoding = 'utf-8'

        LOG.debug('URL was: %s' % response.url)

        if response.status_code == requests.codes.ok:  # pylint: disable=no-member
            LOG.debugplus('XML: \n%s' % encode_utf8(response.text, py2_only=False))
            return response.text

        return ''

    def get_processed_myplex_xml(self, url):
        data = self.talk_to_myplex(url)
        return ETree.fromstring(data)

    def gdm_discovery(self):
        try:
            interface_address = get_platform_ip()
            LOG.debug('Using interface: %s for GDM discovery' % interface_address)
        except:  # pylint: disable=bare-except
            interface_address = None
            LOG.debug('Using systems default interface for GDM discovery')

        try:
            gdm_client = PlexGDM(interface=interface_address)
            gdm_client.discover()
            gdm_server_name = gdm_client.get_server_list()
        except Exception as error:  # pylint: disable=broad-except
            LOG.error('GDM Issue [%s]' % error)
            traceback.print_exc()
        else:
            if gdm_client.discovery_complete and gdm_server_name:
                LOG.debug('GDM discovery completed')

                for device in gdm_server_name:
                    server = PlexMediaServer(name=device['serverName'],
                                             address=device['server'],
                                             port=device['port'],
                                             discovery='discovery',
                                             server_uuid=device['uuid'])
                    server.set_user(self.effective_user)
                    server.set_token(self.effective_token)

                    self.merge_server(server)
            else:
                LOG.debug('GDM was not able to discover any servers')

    def user_provided_discovery(self):
        port = self.settings.port()
        if not port:
            LOG.debug('No port defined.  Using default of ' + DEFAULT_PORT)
            port = DEFAULT_PORT

        ip_address = self.settings.ip_address()
        LOG.debug('Settings hostname and port: %s : %s' %
                  (ip_address, port))

        server = PlexMediaServer(address=ip_address, port=port, discovery='local')
        server.set_user(self.effective_user)
        server.set_token(self.effective_token)
        server.set_protocol('https' if self.settings.https() else 'http')
        server.ssl_certificate_verification = self.settings.certificate_verification()
        server.refresh()

        if server.discovered:
            self.merge_server(server)
        else:
            LOG.error('Error: Unable to discover server %s' %
                      self.settings.ip_address())

    def _discovery_notification(self, servers):
        if self.settings.servers_detected_notification():
            if servers:
                msg = i18n('Found servers:') + ' ' + servers
            else:
                msg = i18n('No servers found')

            xbmcgui.Dialog().notification(heading=CONFIG['name'],
                                          message=msg,
                                          icon=CONFIG['icon'],
                                          sound=False)

    def discover_all_servers(self):
        with ProgressDialog(heading=CONFIG['name'] + ' ' + i18n('Server Discovery'),
                            line1=i18n('Please wait...'), background=True) as progress_dialog:
            try:
                percent = 0
                self.server_list = {}
                # First discover the servers we should know about from myplex
                if self.is_myplex_signedin():
                    LOG.debug('Adding myPlex as a server location')
                    progress_dialog.update(percent=percent, line1=i18n('myPlex discovery...'))

                    self.server_list = self.get_myplex_servers()

                    if self.server_list:
                        LOG.debug('MyPlex discovery completed successfully')
                    else:
                        LOG.debug('MyPlex discovery found no servers')

                # Now grab any local devices we can find
                if self.settings.discovery() == '1':
                    LOG.debug('local GDM discovery setting enabled.')
                    LOG.debug('Attempting GDM lookup on multicast')
                    percent += 40
                    progress_dialog.update(percent=percent, line1=i18n('GDM discovery...'))
                    self.gdm_discovery()

                # Get any manually configured servers
                elif self.settings.ip_address():
                    percent += 40
                    progress_dialog.update(percent=percent, line1=i18n('User provided...'))
                    self.user_provided_discovery()

                percent += 40
                progress_dialog.update(percent=percent, line1=i18n('Caching results...'))

                for server_uuid in list(self.server_list.keys()):
                    self.server_list[server_uuid].settings = None  # can't pickle xbmcaddon.Addon()

                self.cache.write_cache(self.server_list_cache, self.server_list)

                servers = list(map(lambda x: (self.server_list[x].get_name(), x),
                                   self.server_list.keys()))

                server_names = ', '.join(map(lambda x: x[0], servers))

                LOG.debug('serverList is: %s ' % servers)
            finally:
                progress_dialog.update(percent=100, line1=i18n('Finished'))

        self._discovery_notification(server_names)

    def get_myplex_queue(self):
        return self.get_processed_myplex_xml('/pms/playlists/queue/all')

    def get_myplex_sections(self):
        xml = self.talk_to_myplex('/pms/system/library/sections')
        if xml is False:
            return {}
        return xml

    def get_myplex_servers(self):
        temp_servers = {}
        xml = self.talk_to_myplex('/api/resources?includeHttps=1')

        if xml is False:
            return {}

        server_list = ETree.fromstring(xml)
        if PY3:
            devices = server_list.iter('Device')
        else:
            devices = server_list.getiterator('Device')

        for device in devices:

            LOG.debug('[%s] Found device' % device.get('name'))

            if 'server' not in device.get('provides'):
                LOG.debug('[%s] Skipping as not a server [%s]' %
                          (device.get('name'), device.get('provides')))
                continue

            discovered_server = PlexMediaServer(name=encode_utf8(device.get('name')),
                                                discovery='myplex')
            discovered_server.set_uuid(device.get('clientIdentifier'))
            discovered_server.set_owned(device.get('owned'))
            discovered_server.set_token(device.get('accessToken'))
            discovered_server.set_user(self.effective_user)
            if PY3:
                connections = device.iter('Connection')
            else:
                connections = device.getiterator('Connection')
            for connection in connections:
                LOG.debug('[%s] Found server connection' % device.get('name'))

                if connection.get('local') == '0':
                    discovered_server.add_external_connection(connection.get('address'),
                                                              connection.get('port'),
                                                              connection.get('uri'))
                else:
                    discovered_server.add_internal_connection(connection.get('address'),
                                                              connection.get('port'),
                                                              connection.get('uri'))

                if connection.get('protocol') == 'http':
                    LOG.debug('[%s] Dropping back to http' % device.get('name'))
                    discovered_server.set_protocol('http')

            discovered_server.add_custom_access_urls(
                self.server_configs.access_urls(device.get('clientIdentifier'))
            )

            discovered_server.ssl_certificate_verification = \
                self.server_configs.ssl_certificate_verification(device.get('clientIdentifier'))

            discovered_server.set_best_address()  # Default to external address

            temp_servers[discovered_server.get_uuid()] = discovered_server
            LOG.debug('[%s] Discovered server via myPlex: %s' %
                      (discovered_server.get_name(), discovered_server.get_uuid()))

        return temp_servers

    def merge_server(self, server):
        LOG.debug('merging server with uuid %s' % server.get_uuid())

        try:
            existing = self.get_server_from_uuid(server.get_uuid())
        except:  # pylint: disable=bare-except
            LOG.debug('Adding new server %s %s' %
                      (server.get_name(), server.get_uuid()))
            server.refresh()
            if server.discovered:
                self.server_list[server.get_uuid()] = server
        else:
            LOG.debug('Found existing server %s %s' %
                      (existing.get_name(), existing.get_uuid()))

            existing.set_best_address(server.get_access_address())
            existing.refresh()
            self.server_list[existing.get_uuid()] = existing

    def _request(self, path, method, use_params):
        try:
            if use_params:
                response = getattr(requests, method)('%s%s' % (self.myplex_server, path),
                                                     params=self.plex_identification_header(),
                                                     verify=True, timeout=(3, 10))
            else:
                response = getattr(requests, method)('%s%s' % (self.myplex_server, path),
                                                     headers=self.plex_identification_header(),
                                                     verify=True, timeout=(3, 10))
        except AttributeError:
            LOG.error('Unknown HTTP method requested: %s' % method)
            response = None

        if response:
            response.encoding = 'utf-8'

        return response

    def talk_to_myplex(self, path, renew=False, method='get'):
        LOG.debug('url = %s%s' % (self.myplex_server, path))

        use_params = method == 'get'
        method = method.replace('get2', 'get')

        try:
            response = self._request(path, method, use_params=use_params)

        except requests.exceptions.ConnectionError as error:
            LOG.error('myPlex: %s is offline or unreachable. error: %s' %
                      (self.myplex_server, error))
            return '<?xml version="1.0" encoding="UTF-8"?><message status="error"></message>'

        except requests.exceptions.ReadTimeout:
            LOG.debug('myPlex: read timeout for %s on %s ' % (self.myplex_server, path))
            return '<?xml version="1.0" encoding="UTF-8"?><message status="error"></message>'

        else:
            LOG.debugplus('Full URL was: %s' % response.url)
            LOG.debugplus('Full header sent was: %s' % response.request.headers)
            LOG.debugplus('Full header received was: %s' % response.headers)

            if response.status_code == 401 and not renew:
                return self.talk_to_myplex(path, True)

            if response.status_code >= 400:
                error = 'HTTP response error: %s' % response.status_code
                LOG.error(error)
                if response.status_code == 404:
                    return '<?xml version="1.0" encoding="UTF-8"?>' \
                           '<message status="unauthorized">' \
                           '</message>'

                return '<?xml version="1.0" encoding="UTF-8"?>' \
                       '<message status="error">' \
                       '</message>'

            link = encode_utf8(response.text, py2_only=False)
            LOG.debugplus('XML: \n%s' % link)

        return link

    def get_myplex_token(self):

        if self.plexhome_settings['myplex_signedin']:
            return {
                'X-Plex-Token': self.effective_token
            }

        LOG.debug('Myplex not in use')
        return {}

    def sign_into_myplex(self, username=None, password=None):
        LOG.debug('Getting New token')

        if username is None:
            LOG.debug('No myPlex details in provided..')
            return None

        credentials = '%s:%s' % (username, password)
        if PY3:
            credentials = credentials.encode('utf-8')
            base64bytes = base64.encodebytes(credentials)
            base64string = base64bytes.decode('utf-8').replace('\n', '')
        else:
            base64string = base64.encodestring(credentials).replace('\n', '')  # pylint: disable=no-member

        token = False
        myplex_headers = {
            'Authorization': 'Basic %s' % base64string
        }

        response = requests.post('%s/users/sign_in.xml' % self.myplex_server,
                                 headers=dict(self.plex_identification_header(), **myplex_headers),
                                 timeout=120)
        response.encoding = 'utf-8'

        if response.status_code == 201:
            try:
                LOG.debugplus(encode_utf8(response.text, py2_only=False))
                LOG.debug('Received new plex token')
                xml = ETree.fromstring(encode_utf8(response.text))
                home = xml.get('home', '0')

                avatar = xml.get('thumb')
                # Required because plex.tv doesn't return content-length and
                # KODI requires it for cache
                # fixed in KODI 15 (isengard)
                if avatar.startswith('https://plex.tv') or avatar.startswith('http://plex.tv'):
                    avatar = avatar.replace('//', '//i2.wp.com/', 1)
                self.plexhome_settings['plexhome_user_avatar'] = avatar

                if home == '1':
                    self.plexhome_settings['plexhome_enabled'] = True
                    LOG.debug('Setting Plex Home enabled.')
                else:
                    self.plexhome_settings['plexhome_enabled'] = False
                    LOG.debug('Setting Plex Home disabled.')

                token = xml.findtext('authentication-token')
                self.plexhome_settings['myplex_user_cache'] = '%s|%s' % (username, token)
                self.plexhome_settings['myplex_signedin'] = True
                self.save_tokencache()
            except:  # pylint: disable=bare-except
                LOG.debug('No authentication token found')
        else:
            error = 'HTTP response error: %s %s' % (response.status_code, response.reason)
            LOG.error(error)
            return None

        return token

    def get_server_from_parts(self, scheme, uri):
        LOG.debug('IP to lookup: %s' % uri)

        port = None
        if ':' in uri.split('@')[-1]:
            # We probably have an address:port being passed
            uri, port = uri.split(':')

        if is_ip(uri):
            LOG.debug('IP address detected - passing through')
        elif 'plex.direct' in uri:
            LOG.debug('Plex.direct name detected - attempting look up')

            address = uri.split('.')[0]
            clean_address = address.replace('-', '.')

            if is_ip(clean_address):
                uri = clean_address
            else:
                LOG.debug('Unable to clean plex.direct name')
        else:
            try:
                socket.gethostbyname(uri)
            except:  # pylint: disable=bare-except
                LOG.debug('Unable to lookup hostname: %s' % uri)
                return PlexMediaServer(name='dummy', address='127.0.0.1',
                                       port=32400, discovery='local')

        server_list = self.server_list.values()
        for server in server_list:

            LOG.debug('[%s] - checking ip:%s against server ip %s' %
                      (server.get_name(), uri, server.get_address()))

            if server.find_address_match(scheme, uri, port):
                return server

        LOG.debug('Unable to translate - Returning new plex server set to %s' % uri)

        return PlexMediaServer(name=i18n('Unknown'), address=uri, port=port, discovery='local')

    def get_server_from_url(self, url):
        url_parts = urlparse(url)
        return self.get_server_from_parts(url_parts.scheme, url_parts.netloc)

    def get_server_from_uuid(self, _uuid):
        return self.server_list[_uuid]

    def get_processed_xml(self, url):
        url_parts = urlparse(url)
        server = self.get_server_from_parts(url_parts.scheme, url_parts.netloc)

        if server:
            return server.processed_xml(url)
        return ''

    def talk_to_server(self, url):
        url_parts = urlparse(url)
        server = self.get_server_from_parts(url_parts.scheme, url_parts.netloc)

        if server:
            return server.raw_xml(url)
        return ''

    def delete_cache(self, force=False):
        return self.cache.delete_cache(force)

    def set_plex_home_users(self):
        data = ETree.fromstring(self.talk_to_myplex('/api/home/users'))
        self.user_list = {}
        for users in data:
            add = {
                'id': users.get('id'),
                'admin': users.get('admin'),
                'restricted': users.get('restricted'),
                'protected': users.get('protected'),
                'title': users.get('title'),
                'username': users.get('username'),
                'email': users.get('email'),
                'thumb': users.get('thumb')
            }
            self.user_list[users.get('id')] = add

    def get_plex_home_users(self):
        data = ETree.fromstring(self.talk_to_myplex('/api/home/users'))
        self.user_list = {}
        for users in data:
            add = {
                'id': users.get('id'),
                'admin': users.get('admin'),
                'restricted': users.get('restricted'),
                'protected': users.get('protected'),
                'title': users.get('title'),
                'username': users.get('username'),
                'email': users.get('email'),
                'thumb': users.get('thumb')
            }
            self.user_list[users.get('title')] = add

        return self.user_list

    def switch_plex_home_user(self, uid, pin):
        if pin is None:
            pin_arg = '?X-Plex-Token=%s' % self.effective_token
        else:
            pin_arg = '?pin=%s&X-Plex-Token=%s' % (pin, self.effective_token)

        data = self.talk_to_myplex('/api/home/users/%s/switch%s' % (uid, pin_arg), method='post')
        tree = ETree.fromstring(data)

        if tree.get('status') == 'unauthorized':
            return False, 'Unauthorised'

        if tree.get('status') == 'error':
            return False, 'Unknown error'

        username = None
        user_list = self.user_list.values()
        for users in user_list:
            if uid == users['id']:
                username = users['title']
                break

        avatar = tree.get('thumb')
        # Required because plex.tv doesn't return content-length and KODI requires it for cache
        # fixed in KODI 15 (isengard)
        if avatar.startswith('https://plex.tv') or avatar.startswith('http://plex.tv'):
            avatar = avatar.replace('//', '//i2.wp.com/', 1)
        self.plexhome_settings['plexhome_user_avatar'] = avatar

        token = tree.findtext('authentication-token')
        self.plexhome_settings['plexhome_user_cache'] = '%s|%s' % (username, token)
        self.effective_user = username
        self.save_tokencache()
        return True, None

    def is_admin(self):
        if self.effective_user == self.myplex_user:
            return True
        return False

    def get_myplex_information(self):
        data = self.talk_to_myplex('/users/account')
        xml = ETree.fromstring(data)

        result = {
            'username': xml.get('username', 'unknown'),
            'email': xml.get('email', 'unknown'),
            'thumb': xml.get('thumb')
        }

        subscription = xml.find('subscription')
        if subscription is not None:
            result['plexpass'] = subscription.get('plan')
        else:
            result['plexpass'] = 'No Subscription'

        try:
            date = xml.find('joined-at').text
            result['membersince'] = date.split(' ')[0]
        except:  # pylint: disable=bare-except
            result['membersince'] = i18n('Unknown')

        LOG.debug('Gathered information: %s' % result)

        return result

    def all_sections(self):
        tree = ETree.fromstring(self.get_myplex_sections())
        return list(map(PlexSection, tree))

    @staticmethod
    def _tree_tostring(tree):
        return ETree.tostring(tree)
