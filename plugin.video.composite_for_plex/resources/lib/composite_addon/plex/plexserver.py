# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import copy
import threading
import time
import uuid
import xml.etree.ElementTree as ETree

import requests
from six.moves import xrange
from six.moves.urllib_parse import parse_qsl
from six.moves.urllib_parse import quote
from six.moves.urllib_parse import quote_plus
from six.moves.urllib_parse import urlencode
from six.moves.urllib_parse import urlparse
from six.moves.urllib_parse import urlunparse

from ..addon.constants import CONFIG
from ..addon.data_cache import DATA_CACHE
from ..addon.logger import Logger
from ..addon.settings import AddonSettings
from ..addon.strings import encode_utf8
from . import plexsection
from .plexcommon import create_plex_identification
from .plexcommon import get_client_identifier
from .plexcommon import get_device_name

DEFAULT_PORT = '32400'
LOG = Logger('plexserver')

LOG.debug('Using Requests version for HTTP: %s' % requests.__version__)


class PlexMediaServer:  # pylint: disable=too-many-public-methods, too-many-instance-attributes

    def __init__(self, server_uuid=None, name=None, address=None, port=32400,  # pylint: disable=too-many-arguments
                 token=None, discovery=None, class_type='primary'):

        self.settings = None
        self.__revision = CONFIG['required_revision']
        self.protocol = 'https'
        self.uuid = server_uuid
        self.server_name = name
        self.discovery = discovery
        self.local_address = []
        self.external_address = None
        self.external_address_uri = None
        self.local_address_uri = []

        if self.discovery == 'myplex':
            self.external_address = '%s:%s' % (address, port)
            self.external_address_uri = None
        elif self.discovery == 'discovery':
            self.local_address = ['%s:%s' % (address, port)]
            self.local_address_uri = [None]

        self.access_address = '%s:%s' % (address, port)

        self.section_list = []
        self.token = token
        self.owned = 1
        self.master = 1
        self.class_type = class_type
        self.discovered = False
        self.offline = False
        self.user = None
        self.client_id = None
        self.device_name = None
        self.plex_home_enabled = False
        self.best_address = 'address'
        self.connection_test_results = []
        self.plex_identification_header = None
        self.plex_identification_string = None
        self.update_identification()

    def get_settings(self):
        if not self.settings:
            self.settings = AddonSettings()  # unable to pickle, unset before pickling
        return self.settings

    def plex_identification_headers(self):
        self.client_id = get_client_identifier(self.get_settings(), self.client_id)
        self.device_name = get_device_name(self.get_settings(), self.device_name)

        return create_plex_identification(self.get_settings(), device_name=self.device_name,
                                          client_id=self.client_id, user=self.get_user(),
                                          token=self.get_token())

    def update_identification(self):
        self.plex_identification_header = self.plex_identification_headers()
        self.plex_identification_string = self.create_plex_identification_string()

    def get_revision(self):
        return self.__revision

    def get_status(self):
        if self.offline:
            return 'Offline'

        if self.access_address == self.external_address or \
                (self.external_address_uri and (self.access_address in self.external_address_uri)):
            return 'Remote'

        if self.access_address in self.local_address:
            return 'Nearby'

        return 'Unknown'

    def get_details(self):

        return {
            'serverName': self.server_name,
            'server': self.get_address(),
            'port': self.get_port(),
            'discovery': self.discovery,
            'token': self.token,
            'uuid': self.uuid,
            'owned': self.owned,
            'master': self.master,
            'class': self.class_type
        }

    def create_plex_identification_string(self):
        header = map(lambda x: '='.join((x[0], quote(x[1]))),
                     self.plex_identification_header.items())
        return '&'.join(header)

    def get_uuid(self):
        return self.uuid

    def get_name(self):
        return self.server_name

    def get_address(self):
        return self.access_address.split(':')[0]

    def get_port(self):
        return self.access_address.split(':')[1]

    def get_location(self):
        return self.get_access_address()

    def get_access_address(self):
        return self.access_address

    def get_url_location(self):
        return '%s://%s' % (self.protocol, self.access_address)

    def get_token(self):
        return self.token

    def get_discovery(self):
        return self.discovery

    def is_secure(self):
        if self.protocol == 'https':
            return True
        return False

    def find_address_match(self, ipaddress, port):
        LOG.debug('Checking [%s:%s] against [%s]' % (ipaddress, port, self.access_address))
        if '%s:%s' % (ipaddress, port) == self.access_address:
            return True

        LOG.debug('Checking [%s:%s] against [%s]' % (ipaddress, port, self.external_address))
        if '%s:%s' % (ipaddress, port) == self.external_address:
            return True

        for test_address in self.local_address:
            LOG.debug('Checking [%s:%s] against [%s:%s]' % (ipaddress, port, ipaddress, 32400))
            if '%s:%s' % (ipaddress, port) == '%s:%s' % (test_address, 32400):
                return True

        return False

    def get_user(self):
        return self.user

    def get_owned(self):
        return self.owned

    def get_class(self):
        return self.class_type

    def get_master(self):
        return self.master

    # Set and add functions:

    def set_uuid(self, _uuid):
        self.uuid = _uuid

    def set_owned(self, value):
        self.owned = int(value)

    def set_token(self, value):
        self.token = value
        self.update_identification()

    def set_user(self, value):
        self.user = value
        self.update_identification()

    def set_class(self, value):
        self.class_type = value

    def set_master(self, value):
        self.master = value

    def set_protocol(self, value):
        self.protocol = value

    def set_plex_home_enabled(self):
        self.plex_home_enabled = True

    def set_plex_home_disabled(self):
        self.plex_home_enabled = False

    def add_external_connection(self, address, port, uri):
        self.external_address = '%s:%s' % (address, port)
        self.external_address_uri = uri

    def add_internal_connection(self, address, port, uri):
        if '%s:%s' % (address, port) not in self.local_address:
            self.local_address.append('%s:%s' % (address, port))
            self.local_address_uri.append(uri)

    def add_local_address(self, address):
        self.local_address = address.split(',')

    def connection_test(self, tag, uri):
        LOG.debug('[%s] Head request |%s|' % (self.uuid, uri))
        url_parts = urlparse(uri)
        status_code = requests.codes.not_found  # pylint: disable=no-member
        try:
            verify_cert = uri.startswith('https') and self.get_settings().verify_certificates()
            response = requests.head(uri, params=self.plex_identification_header,
                                     verify=verify_cert, timeout=(2, 60))
            status_code = response.status_code
            LOG.debug('[%s] Head status |%s| -> |%s|' % (self.uuid, uri, str(status_code)))
            if status_code in [requests.codes.ok, requests.codes.unauthorized]:  # pylint: disable=no-member
                self.connection_test_results.append((tag, url_parts.scheme, url_parts.netloc, True))
                return
        except:  # pylint: disable=bare-except
            pass
        LOG.debug('[%s] Head status |%s| -> |%s|' % (self.uuid, uri, str(status_code)))
        self.connection_test_results.append((tag, url_parts.scheme, url_parts.netloc, False))

    def _get_formatted_uris(self, address):
        external_uri = ''
        internal_address = ''
        external_address = ''

        if address:
            if ':' not in address:
                address = '%s:%s' % (address, DEFAULT_PORT)
        else:
            if self.external_address_uri:
                url_parts = urlparse(self.external_address_uri)
                external_uri = url_parts.netloc
            if self.local_address:
                internal_address = self.local_address[0]
            if self.external_address and not self.external_address.lower().startswith('none:'):
                external_address = self.external_address

            # Ensure that ipaddress comes in an ip:port format
            if external_uri and ':' not in external_uri:
                external_uri = '%s:%s' % (external_uri, DEFAULT_PORT)
            if internal_address and ':' not in internal_address:
                internal_address = '%s:%s' % (internal_address, DEFAULT_PORT)
            if external_address and ':' not in external_address:
                external_address = '%s:%s' % (external_address, DEFAULT_PORT)

        return address, external_uri, internal_address, external_address

    def _get_connection_uris_and_tags(self, address, external_uri,
                                      internal_address, external_address):
        tags = []
        uris = []

        use_https = self.get_settings().secure_connection()

        if address:
            if use_https:
                uris.append('%s://%s/' % ('https', address))
                tags.append('user')
            uris.append('%s://%s/' % ('http', address))
            tags.append('user')
        else:
            if external_uri:
                if use_https:
                    uris.append('%s://%s/' % ('https', external_uri))
                    tags.append('external_uri')
                uris.append('%s://%s/' % ('http', external_uri))
                tags.append('external_uri')
            if internal_address:
                if use_https:
                    uris.append('%s://%s/' % ('https', internal_address))
                    tags.append('internal')
                uris.append('%s://%s/' % ('http', internal_address))
                tags.append('internal')
            if external_address:
                if use_https:
                    uris.append('%s://%s/' % ('https', external_address))
                    tags.append('external')
                uris.append('%s://%s/' % ('http', external_address))
                tags.append('external')

        return uris, tags

    def _set_best_https(self):
        if any(conn[0] == 'user' and conn[1] == 'https' and conn[3]
               for conn in self.connection_test_results):
            self.access_address = next(conn[2] for conn in self.connection_test_results
                                       if conn[0] == 'user' and conn[1] == 'https' and conn[3])
            LOG.debug('[%s] Server [%s] not found in existing lists.  '
                      'selecting as default' % (self.uuid, self.access_address))
            return True

        if any(conn[0] == 'external_uri' and conn[1] == 'https' and conn[3]
               for conn in self.connection_test_results):
            self.access_address = next(conn[2] for conn in self.connection_test_results
                                       if conn[0] == 'external_uri' and
                                       conn[1] == 'https' and conn[3])
            LOG.debug('[%s] Server [%s] found in existing external list.  '
                      'selecting as default' % (self.uuid, self.access_address))
            return True

        if any(conn[0] == 'internal' and conn[1] == 'https' and conn[3]
               for conn in self.connection_test_results):
            self.access_address = next(conn[2] for conn in self.connection_test_results
                                       if conn[0] == 'internal' and conn[1] == 'https' and conn[3])
            LOG.debug('[%s] Server [%s] found on existing internal list.  '
                      'selecting as default' % (self.uuid, self.access_address))
            return True

        if any(conn[0] == 'external' and conn[1] == 'https' and conn[3]
               for conn in self.connection_test_results):
            self.access_address = next(conn[2] for conn in self.connection_test_results
                                       if conn[0] == 'external' and conn[1] == 'https' and conn[3])
            LOG.debug('[%s] Server [%s] found in existing external list.  '
                      'selecting as default' % (self.uuid, self.access_address))
            return True

        return False

    def _set_best_http(self):
        if any(conn[0] == 'user' and conn[1] == 'http' and conn[3]
               for conn in self.connection_test_results):
            self.access_address = next(conn[2] for conn in self.connection_test_results
                                       if conn[0] == 'user' and conn[1] == 'http' and conn[3])
            self.set_protocol('http')
            LOG.debug('[%s] Server [%s] not found in existing lists.  '
                      'selecting as default' % (self.uuid, self.access_address))
            return True

        if any(conn[0] == 'external_uri' and conn[1] == 'http' and conn[3]
               for conn in self.connection_test_results):
            self.access_address = next(conn[2] for conn in self.connection_test_results
                                       if conn[0] == 'external_uri' and conn[1] == 'http'
                                       and conn[3])
            self.set_protocol('http')
            LOG.debug('[%s] Server [%s] found in existing external list.  '
                      'selecting as default' % (self.uuid, self.access_address))
            return True

        if any(conn[0] == 'internal' and conn[1] == 'http' and conn[3]
               for conn in self.connection_test_results):
            self.access_address = next(conn[2] for conn in self.connection_test_results
                                       if conn[0] == 'internal' and conn[1] == 'http' and conn[3])
            self.set_protocol('http')
            LOG.debug('[%s] Server [%s] found on existing internal list.  '
                      'selecting as default' % (self.uuid, self.access_address))
            return True

        if any(conn[0] == 'external' and conn[1] == 'http' and conn[3]
               for conn in self.connection_test_results):
            self.access_address = next(conn[2] for conn in self.connection_test_results
                                       if conn[0] == 'external' and conn[1] == 'http' and conn[3])
            self.set_protocol('http')
            LOG.debug('[%s] Server [%s] found in existing external list.  '
                      'selecting as default' % (self.uuid, self.access_address))
            return True

        return False

    def set_best_address(self, address=''):
        if not address:
            self.connection_test_results = []

        self.offline = False
        self.update_identification()

        if not self.get_settings().secure_connection():
            self.set_protocol('http')

        tested = []
        append_tested = tested.append
        threads = []
        append_thread = threads.append

        address, external_uri, internal_address, external_address = \
            self._get_formatted_uris(address)

        uris, tags = self._get_connection_uris_and_tags(address, external_uri,
                                                        internal_address, external_address)
        number_of_uris = len(uris)
        thread = threading.Thread
        for idx in xrange(number_of_uris):
            uri = uris[idx]
            if uri in tested:
                continue
            append_tested(uri)
            append_thread(thread(target=self.connection_test, args=(tags[idx], uri)))

        _ = [thread.start() for thread in threads]
        _ = [thread.join() for thread in threads]

        LOG.debug('[%s] Server connection test results |%s|' %
                  (self.uuid, str(self.connection_test_results)))

        #  connection preference https
        #  (user provided, external uri, internal address, external address)
        found_connection = self._set_best_https()

        if not found_connection:
            # connection preference http
            #  (user provided, external uri, internal address, external address)
            found_connection = self._set_best_http()

        if not found_connection:
            self.offline = True
            LOG.debug('[%s] Server appears to be offline' % self.uuid)

    def _request(self, uri, params, method):
        verify_cert = self.protocol == 'https' and self.get_settings().verify_certificates()

        try:
            response = getattr(requests, method)(uri, params=params, verify=verify_cert,
                                                 timeout=(2, 60))
        except AttributeError:
            response = None

        if response:
            response.encoding = 'utf-8'

        return response

    def talk(self, url='/', refresh=False, method='get', extra_headers=None):
        if extra_headers is None:
            extra_headers = {}

        if not self.offline or refresh:
            LOG.debug('URL is: %s using %s' % (url, self.protocol))
            start_time = time.time()

            uri = '%s://%s:%s%s' % (self.protocol, self.get_address(), self.get_port(), url)
            params = copy.deepcopy(self.plex_identification_header)
            if params is not None:
                params.update(extra_headers)

            try:
                response = self._request(uri, params, method)
                self.offline = False

            except requests.exceptions.ConnectionError as error:
                LOG.error('Server: %s is offline or unreachable. error: %s' %
                          (self.get_address(), error))

                if self.protocol == 'https' and refresh:
                    LOG.debug('Server: %s - switching to http' % self.get_address())
                    self.set_protocol('http')
                    return self.talk(url, refresh, method)

                self.offline = True

            except requests.exceptions.ReadTimeout:
                LOG.debug('Server: read timeout for %s on %s ' % (self.get_address(), url))

            else:
                LOG.debug('URL was: %s using %s' % (response.url, self.protocol))

                if response.status_code == requests.codes.ok:  # pylint: disable=no-member
                    LOG.debug('Response: 200 OK - Encoding: %s' % response.encoding)
                    data = encode_utf8(response.text, py2_only=False)
                    LOG.debug('DOWNLOAD: It took %.2f seconds to retrieve data from %s' %
                              ((time.time() - start_time), self.get_address()))
                    return data
                if response.status_code == requests.codes.unauthorized:  # pylint: disable=no-member
                    LOG.debug('Response: 401 Unauthorized - '
                              'Please log into myPlex or check your myPlex password')
                    return '<?xml version="1.0" encoding="UTF-8"?>' \
                           '<message status="unauthorized">' \
                           '</message>'

                LOG.debug('Unexpected Response: %s ' % response.status_code)

        return '<?xml version="1.0" encoding="UTF-8"?>' \
               '<message status="offline">' \
               '</message>'

    def post(self, url, refresh=False, extra_headers=None):
        if extra_headers is None:
            extra_headers = {}
        return self.talk(url, refresh, method='post', extra_headers=extra_headers)

    def tell(self, url, refresh=False, extra_headers=None):
        if extra_headers is None:
            extra_headers = {}
        return self.talk(url, refresh, method='put', extra_headers=extra_headers)

    def refresh(self):
        data = self.talk(refresh=True)

        tree = ETree.fromstring(data)

        if (tree is not None and
                not (tree.get('status') == 'offline' or tree.get('status') == 'unauthorized')):
            self.server_name = encode_utf8(tree.get('friendlyName'))
            self.uuid = tree.get('machineIdentifier')
            self.owned = 1
            self.master = 1
            self.class_type = tree.get('serverClass', 'primary')
            self.plex_home_enabled = tree.get('multiuser') == '1'
            self.discovered = True
        else:
            self.discovered = False

    def is_offline(self):
        return self.offline

    def get_sections(self):
        if not self.section_list:
            self.discover_sections()
        LOG.debug('Returning sections: %s' % self.section_list)
        return self.section_list

    def discover_sections(self):
        plex_section = plexsection.PlexSection
        self.section_list = list(map(plex_section, self.processed_xml('/library/sections')))

    def get_recently_added(self, section=-1, start=0, size=0, hide_watched=True):

        if hide_watched:
            arguments = '?unwatched=1'
        else:
            arguments = '?unwatched=0'

        if section < 0:
            return self.processed_xml('/library/recentlyAdded%s' % arguments)

        if size > 0:
            arguments = '%s&X-Plex-Container-Start=%s&X-Plex-Container-Size=%s' % \
                        (arguments, start, size)

        return self.processed_xml('/library/sections/%s/recentlyAdded%s' %
                                  (section, arguments))

    def get_ondeck(self, section=-1, start=0, size=0):

        arguments = ''

        if section < 0:
            return self.processed_xml('/library/onDeck%s' % arguments)

        if size > 0:
            arguments = '%s?X-Plex-Container-Start=%s&X-Plex-Container-Size=%s' % \
                        (arguments, start, size)

        return self.processed_xml('/library/sections/%s/onDeck%s' % (section, arguments))

    def get_recently_viewed_shows(self, section=-1, start=0, size=0):

        arguments = ''

        if section < 0:
            return self.processed_xml('/library/recentlyViewedShows%s' % arguments)

        if size > 0:
            arguments = '%s?X-Plex-Container-Start=%s&X-Plex-Container-Size=%s' % \
                        (arguments, start, size)

        return self.processed_xml('/library/sections/%s/recentlyViewedShows%s' %
                                  (section, arguments))

    def get_server_recentlyadded(self):
        return self.get_recently_added(section=-1)

    def get_server_ondeck(self):
        return self.get_ondeck(section=-1)

    def get_channel_recentlyviewed(self):
        return self.processed_xml('/channels/recentlyViewed')

    def process_xml(self, data):
        start_time = time.time()
        tree = ETree.fromstring(data)
        LOG.debug('PARSE: it took %.2f seconds to parse data from %s' %
                  ((time.time() - start_time), self.get_address()))
        LOG.debugplus('TREE: %s' % ETree.tostring(tree))
        return tree

    def processed_xml(self, url):
        cache_name = DATA_CACHE.sha512_cache_name('processed_xml', self.get_uuid(), url)
        is_valid, result = DATA_CACHE.check_cache(cache_name, self.get_settings().data_cache_ttl())
        if is_valid and result is not None:
            return result

        if url.startswith('http'):
            LOG.debug('We have been passed a full URL. Parsing out path')
            url_parts = urlparse(url)
            url = url_parts.path

            if url_parts.query:
                url = '%s?%s' % (url, url_parts.query)

        data = self.talk(url)
        tree = self.process_xml(data)
        if tree is not None:
            DATA_CACHE.write_cache(cache_name, tree)
        return tree

    def raw_xml(self, url):
        if url.startswith('http'):
            LOG.debug('We have been passed a full URL. Parsing out path')
            url_parts = urlparse(url)
            url = url_parts.path

            if url_parts.query:
                url = '%s?%s' % (url, url_parts.query)

        start_time = time.time()

        data = self.talk(url)

        LOG.debug('PROCESSING: it took %.2f seconds to process data from %s' %
                  ((time.time() - start_time), self.get_address()))
        LOG.debugplus('TREE: %s' % ETree.tostring(data))
        return data

    def is_owned(self):

        if self.owned == 1 or self.owned == '1':
            return True
        return False

    def is_secondary(self):

        if self.class_type == 'secondary':
            return True
        return False

    def get_formatted_url(self, url, options=None):

        if options is None:
            options = {}

        url_options = self.plex_identification_header
        url_options.update(options)

        if url.startswith('http'):
            url_parts = urlparse(url)
            url = url_parts.path

            if url_parts.query:
                url = url + '?' + url_parts.query

        location = '%s%s' % (self.get_url_location(), url)

        url_parts = urlparse(location)

        query_args = parse_qsl(url_parts.query)
        query_args += url_options.items()

        new_query_args = urlencode(query_args, True)

        return urlunparse((url_parts.scheme, url_parts.netloc, url_parts.path,
                           url_parts.params, new_query_args, url_parts.fragment))

    def get_kodi_header_formatted_url(self, url, options=None):

        if options is None:
            options = {}

        if url.startswith('http'):
            url_parts = urlparse(url)
            url = url_parts.path

            if url_parts.query:
                url = url + '?' + url_parts.query

        location = '%s%s' % (self.get_url_location(), url)

        url_parts = urlparse(location)

        query_args = parse_qsl(url_parts.query)
        query_args += options.items()

        if self.token is not None:
            query_args += {
                'X-Plex-Token': self.token
            }.items()

        new_query_args = urlencode(query_args, True)

        return '%s|%s' % (urlunparse((url_parts.scheme, url_parts.netloc, url_parts.path,
                                      url_parts.params, new_query_args, url_parts.fragment)),
                          self.plex_identification_string)

    def get_fanart(self, section, width=1280, height=720):
        LOG.debug('Getting fanart for %s' % section.get_title())

        if self.get_settings().skip_images():
            return ''

        if section.get_art().startswith('/'):
            if self.get_settings().full_resolution_fanart():
                return self.get_formatted_url(section.get_art())

            return self.get_formatted_url('/photo/:/transcode?url=%s&width=%s&height=%s' %
                                          (quote_plus('http://localhost:32400' + section.get_art()),
                                           width, height))

        return section.get_art()

    def stop_transcode_session(self, session):
        self.talk('/video/:/transcode/segmented/stop?session=%s' % session)

    def report_playback_progress(self, media_id, watched_time, state='playing', duration=0):
        try:
            mark_watched = False
            if state == 'stopped' and int((float(watched_time) / float(duration)) * 100) >= 98:
                watched_time = duration
                mark_watched = True

            self.talk('/:/timeline?duration=%s&guid=com.plexapp.plugins.library&'
                      'key=/library/metadata/%s&ratingKey=%s&state=%s&time=%s' %
                      (duration, media_id, media_id, state, watched_time))

            if mark_watched:
                self.mark_item_watched(media_id)

        except ZeroDivisionError:
            pass

    def mark_item_watched(self, media_id):
        self.talk('/:/scrobble?key=%s&identifier=com.plexapp.plugins.library' % media_id)

    def mark_item_unwatched(self, media_id):
        self.talk('/:/unscrobble?key=%s&identifier=com.plexapp.plugins.library' % media_id)

    def refresh_section(self, key):
        return self.talk('/library/sections/%s/refresh' % key)

    def get_metadata(self, media_id):
        return self.processed_xml('/library/metadata/%s' % media_id)

    def set_audio_stream(self, part_id, stream_id):
        return self.tell('/library/parts/%s?audioStreamID=%s' % (part_id, stream_id))

    def set_subtitle_stream(self, part_id, stream_id):
        return self.tell('/library/parts/%s?subtitleStreamID=%s' % (part_id, stream_id))

    def delete_metadata(self, media_id):
        return self.talk('/library/metadata/%s' % media_id, method='delete')

    def create_playlist(self, metadata_id, playlist_title, playlist_type):
        return self.process_xml(self.post('/playlists', extra_headers={
            'uri': 'server://%s/com.plexapp.plugins.library/library/metadata/%s' %
                   (self.get_uuid(), metadata_id),
            'title': playlist_title,
            'type': playlist_type,
            'smart': 0
        }))

    def add_playlist_item(self, playlist_id, library_section_uuid, metadata_id):
        return self.process_xml(self.tell('/playlists/%s/items' % playlist_id,
                                          extra_headers={
                                              'uri': 'library://' + library_section_uuid +
                                                     '/item/%2Flibrary%2Fmetadata%2F' + metadata_id
                                          }))

    def delete_playlist_item(self, playlist_item_id, path):
        return self.process_xml(self.talk('%s/%s' % (path, playlist_item_id), method='delete'))

    def delete_playlist(self, playlist_id):
        return self.talk('/playlists/%s' % playlist_id, method='delete')

    def get_playlists(self):
        return self.processed_xml('/playlists')

    def get_children(self, media_id):
        return self.processed_xml('/library/metadata/%s/children' % media_id)

    def get_universal_transcode(self, url, transcode_profile=0):
        # Check for myplex user, which we need to alter to a master server
        LOG.debug('incoming URL is: %s' % url)

        profile = self.get_settings().transcode_profile(transcode_profile)
        resolution, bitrate = profile.get('quality').split(',')
        subtitle_size = profile.get('subtitle_size').split('.')[0]
        audio_boost = profile.get('audio_boost').split('.')[0]

        if bitrate.endswith('Mbps'):
            max_video_bitrate = float(bitrate.strip().split('Mbps')[0]) * 1000
        elif bitrate.endswith('Kbps'):
            max_video_bitrate = bitrate.strip().split('Kbps')[0]
        elif bitrate.endswith('unlimited'):
            max_video_bitrate = 20000
        else:
            max_video_bitrate = 2000  # a catch all amount for missing data

        transcode_request = '/video/:/transcode/universal/start.m3u8?'
        session = str(uuid.uuid4())
        quality = '100'
        transcode_settings = {
            'protocol': 'hls',
            'container': 'mpegts',
            'session': session,
            'offset': 0,
            'videoResolution': resolution,
            'maxVideoBitrate': max_video_bitrate,
            'videoQuality': quality,
            'directStream': '1',
            'directPlay': '0',
            'subtitleSize': subtitle_size,
            'audioBoost': audio_boost,
            'fastSeek': '1',
            'path': 'http://127.0.0.1:32400%s' % url
        }

        full_url = '%s%s' % (transcode_request, urlencode(transcode_settings))
        LOG.debug('\nURL: |%s|\nProfile: |[%s] %s@%s (%s/%s)|' %
                  (full_url, str(transcode_profile + 1), resolution, bitrate.strip(),
                   subtitle_size, audio_boost))

        return self.get_formatted_url(full_url,
                                      options={
                                          'X-Plex-Device': 'Plex Home Theater',
                                          'X-Plex-Client-Profile-Name': 'Chrome',
                                      }), session
