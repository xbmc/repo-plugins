# -*- coding: utf-8 -*-
"""
A Kodi-agnostic library for C More
"""
import os
import json
import codecs
import time
from datetime import datetime, timedelta

import requests


class CMore(object):
    def __init__(self, settings_folder, locale, debug=False):
        self.debug = debug
        self.locale = locale
        self.locale_suffix = self.locale.split('_')[1].lower()
        self.http_session = requests.Session()
        self.settings_folder = settings_folder
        self.credentials_file = os.path.join(settings_folder, 'credentials')
        self.base_url = 'https://cmore-mobile-bff.b17g.services'
        self.config_path = os.path.join(self.settings_folder, 'configuration.json')
        self.config_version = '3.6.1'
        self.config = self.get_config()
        self.client = 'cmore-android'
        # hopefully, this can be acquired dynamically in the future
        self.root_pages = {
            'sv_SE': ['start', 'movies', 'series', 'sports', 'tv', 'programs', 'kids'],
            'da_DK': ['start', 'movies', 'series', 'sports', 'tv', 'kids'],
            'nb_NO': ['start', 'movies', 'series', 'tv', 'kids']
        }

    class CMoreError(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)

    def log(self, string):
        """C More class log method."""
        if self.debug:
            try:
                print('[C More]: %s') % string
            except UnicodeEncodeError:
                # we can't anticipate everything in unicode they might throw at
                # us, but we can handle a simple BOM
                bom = unicode(codecs.BOM_UTF8, 'utf8')
                print('[C More]: %s' % string.replace(bom, ''))
            except:
                pass

    def make_request(self, url, method, params=None, payload=None, headers=None):
        """Make an HTTP request. Return the response."""
        self.log('Request URL: %s' % url)
        self.log('Method: %s' % method)
        if params:
            self.log('Params: %s' % params)
        if payload:
            self.log('Payload: %s' % payload)
        if headers:
            self.log('Headers: %s' % headers)

        if method == 'get':
            req = self.http_session.get(url, params=params, headers=headers)
        elif method == 'put':
            req = self.http_session.put(url, params=params, data=payload, headers=headers)
        else:  # post
            req = self.http_session.post(url, params=params, data=payload, headers=headers)
        self.log('Response code: %s' % req.status_code)
        self.log('Response: %s' % req.content)

        return self.parse_response(req.content)

    def parse_response(self, response):
        """Try to load JSON data into dict and raise potential API errors."""
        try:
            response = json.loads(response)
            if 'error' in response:
                if 'message' in response['error']:
                    raise self.CMoreError(response['error']['message'])
                elif 'description' in response['error']:
                    raise self.CMoreError(response['error']['description'])
                elif 'code' in response['error']:
                    raise self.CMoreError(response['error']['error'])

        except ValueError:  # when response is not in json
            pass

        return response

    def get_config(self):
        """Return the config in a dict. Re-download if the config version doesn't match self.config_version."""
        try:
            config = json.load(open(self.config_path))['data']
        except IOError:
            self.download_config()
            config = json.load(open(self.config_path))['data']

        config_version = int(str(config['settings']['currentAppVersion']).replace('.', ''))
        version_to_use = int(str(self.config_version).replace('.', ''))
        config_lang = config['bootstrap']['suggested_site']['locale']
        if version_to_use > config_version or config_lang != self.locale:
            self.download_config()
            config = json.load(open(self.config_path))['data']

        return config

    def download_config(self):
        """Download the C More app configuration."""
        url = self.base_url + '/configuration'
        params = {
            'device': 'android_tab',
            'locale': self.locale
        }
        config_data = self.make_request(url, 'get', params=params)
        with open(self.config_path, 'w') as fh_config:
            fh_config.write(json.dumps(config_data))

    def save_credentials(self, credentials):
        """Save credentials in JSON format."""
        credentials_dict = json.loads(credentials)['data']
        if self.get_credentials().get('remember_me'):
            credentials_dict['remember_me'] = {}
            credentials_dict['remember_me']['token'] = self.get_credentials()['remember_me']['token']  # resave token
        with open(self.credentials_file, 'w') as fh_credentials:
            fh_credentials.write(json.dumps(credentials_dict))

    def reset_credentials(self):
        """Overwrite credentials with empty JSON data."""
        credentials = {}
        with open(self.credentials_file, 'w') as fh_credentials:
            fh_credentials.write(json.dumps(credentials))

    def get_credentials(self):
        """Get JSON credentials file from disk and load it into a dictionary."""
        try:
            with open(self.credentials_file, 'r') as fh_credentials:
                credentials_dict = json.loads(fh_credentials.read())
                return credentials_dict
        except IOError:
            self.reset_credentials()
            with open(self.credentials_file, 'r') as fh_credentials:
                return json.loads(fh_credentials.read())

    def get_operators(self):
        """Return a list of TV operators supported by the C More login system."""
        url = self.config['links']['accountAPI'] + 'operators'
        params = {
            'client': self.client,
            'country_code': self.locale_suffix
        }
        data = self.make_request(url, 'get', params=params)

        return data['data']['operators']

    def login(self, username=None, password=None, operator=None):
        """Complete login process for C More."""
        url = self.config['links']['accountAPI'] + 'session'
        params = {
            'client': self.client,
            'legacy': 'true'
        }

        if self.get_credentials().get('remember_me'):
            method = 'put'
            payload = {
                'locale': self.locale,
                'remember_me': self.get_credentials()['remember_me']['token']
            }
        else:
            method = 'post'
            payload = {
                'username': username,
                'password': password
            }
            if operator:
                payload['country_code'] = self.locale_suffix
                payload['operator'] = operator

        credentials = self.make_request(url, method, params=params, payload=payload)
        self.save_credentials(json.dumps(credentials))

    def get_page(self, page_id, namespace='page'):
        url = self.config['links']['pageAPI'] + page_id
        params = {
            'locale': self.locale,
            'namespace': namespace
        }
        headers = {'Authorization': 'Bearer {0}'.format(self.get_credentials().get('jwt_token'))}
        data = self.make_request(url, 'get', params=params, headers=headers)

        return data['data']

    def get_content_details(self, page_type, page_id, season=None, size='999', page='1'):
        url = self.config['links']['contentDetailsAPI'] + '{0}/{1}'.format(page_type, page_id)
        params = {'locale': self.locale}
        if season:
            params['season'] = season
            params['size'] = size
            params['page'] = page

        headers = {'Authorization': 'Bearer {0}'.format(self.get_credentials().get('jwt_token'))}
        data = self.make_request(url, 'get', params=params, headers=headers)

        return data['data']

    def parse_page(self, page_id, namespace='page', root_page=False):
        page = self.get_page(page_id, namespace)
        if 'targets' in page:
            return page['targets']  # movie/series items on theme-pages
        if 'nowPlaying' in page:
            return page['nowPlaying']  # tv channels/program info
        if 'scheduledEvents' in page:
            return page['scheduledEvents']  # sports events
        if page.get('containers'):
            if page['containers'].get('page_link_container'):
                if page['containers']['page_link_container']['pageLinks'] and root_page:
                    # no parsing needed as it's already in the 'correct' format
                    return page['containers']['page_link_container']['pageLinks']
            if 'genre_containers' in page['containers']:
                return self.parse_containers(page['containers']['genre_containers'])
            if 'section_containers' in page['containers']:
                return self.parse_containers(page['containers']['section_containers'])

        # if nothing matches
        self.log('Failed to parse page.')
        return False

    def parse_containers(self, containers):
        """Parse containers in a sane format. See addon.py for implementation examples."""
        parsed_containers = []
        for i in containers:
            if i['pageLink']['id']:
                parsed_containers.append(i['pageLink'])
            else:
                container = {
                    'id': i['id'],
                    'attributes': i['attributes'],
                    'page_data': i['targets']

                }
                parsed_containers.append(container)

        return parsed_containers

    def get_stream(self, video_id):
        """Return a dict with stream URL and Widevine license URL."""
        stream = {}
        allowed_formats = ['ism', 'mpd']
        url = self.config['links']['vimondRestAPI'] + 'api/tve_web/asset/{0}/play.json'.format(video_id)
        params = {'protocol': 'VUDASH'}
        headers = {'Authorization': 'Bearer {0}'.format(self.get_credentials().get('vimond_token'))}
        data_dict = self.make_request(url, 'get', params=params, headers=headers)['playback']
        stream['drm_protected'] = data_dict['drmProtected']

        if isinstance(data_dict['items']['item'], list):
            for i in data_dict['items']['item']:
                if i['mediaFormat'] in allowed_formats:
                    stream['mpd_url'] = i['url']
                    if stream['drm_protected']:
                        stream['license_url'] = i['license']['@uri']
                        stream['drm_type'] = i['license']['@name']
                    break
        else:
            stream['mpd_url'] = data_dict['items']['item']['url']
            if stream['drm_protected']:
                stream['license_url'] = data_dict['items']['item']['license']['@uri']
                stream['drm_type'] = data_dict['items']['item']['license']['@name']

        live_stream_offset = self.parse_stream_offset(video_id)
        if live_stream_offset:
            stream['mpd_url'] = '{0}?t={1}'.format(stream['mpd_url'], live_stream_offset)

        return stream

    def parse_stream_offset(self, video_id):
        """Calculate offset parameter needed for on-demand sports content."""
        url = self.config['links']['vimondRestAPI'] + 'api/tve_web/asset/{0}.json'.format(video_id)
        params = {'expand': 'metadata'}
        headers = {'Authorization': 'Bearer {0}'.format(self.get_credentials().get('jwt_token'))}
        data = self.make_request(url, 'get', params=params, headers=headers)['asset']

        if 'live-event-end' in data['metadata']:
            utc_time_difference = int(data['liveBroadcastTime'].split('+')[1][1])
            start_time_local = self.parse_datetime(data['liveBroadcastTime'])
            end_time_local = self.parse_datetime(data['metadata']['live-event-end']['$'])

            start_time_utc = start_time_local - timedelta(hours=utc_time_difference)
            end_time_utc = end_time_local - timedelta(hours=utc_time_difference)
            offset = '{0}-{1}'.format(start_time_utc.isoformat(), end_time_utc.isoformat())
            return offset
        else:
            return None

    def get_image_url(self, image_url):
        """Request the image from their image proxy. Can be extended to resize/add image effects automatically.
        See https://imageproxy.b17g.services/docs for more information."""
        if image_url:
            return '{0}?source={1}'.format(self.config['links']['imageProxy'], image_url)
        else:
            return None

    def get_search_data(self, query, page='0', page_size='300'):
        url = self.config['links']['searchAPI']
        params = {
            'query': query,
            'page': page,
            'pageSize': page_size,
            'locale': self.locale
        }
        headers = {'Authorization': 'Bearer {0}'.format(self.get_credentials().get('jwt_token'))}
        data = self.make_request(url, 'get', params=params, headers=headers)

        return data['data']['hits']

    @staticmethod
    def parse_datetime(event_date):
        """Parse date string to datetime object."""
        date_time_format = '%Y-%m-%dT%H:%M:%S+' + event_date.split('+')[1]  # summer/winter time changes format
        datetime_obj = datetime(*(time.strptime(event_date, date_time_format)[0:6]))
        return datetime_obj

    @staticmethod
    def get_current_time():
        """Return the current local time."""
        return datetime.now()
