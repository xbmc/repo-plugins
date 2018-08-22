# -*- coding: utf-8 -*-
"""
A Kodi-agnostic library for ESPN Player
"""
import json
import codecs
import cookielib
import calendar
from datetime import datetime, timedelta
import time
from urllib import urlencode

import requests
import m3u8
import xmltodict


class espnlib(object):
    def __init__(self, cookie_file, debug=False, verify_ssl=True):
        self.debug = debug
        self.verify_ssl = verify_ssl
        self.base_url = 'https://www.espnplayer.com'
        self.http_session = requests.Session()
        self.cookie_jar = cookielib.LWPCookieJar(cookie_file)
        try:
            self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
        except IOError:
            pass
        self.http_session.cookies = self.cookie_jar
        self.secure_token = []

    class LoginFailure(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)

    def log(self, string):
        if self.debug:
            try:
                print '[espnlib]: %s' % string
            except UnicodeEncodeError:
                # we can't anticipate everything in unicode they might throw at
                # us, but we can handle a simple BOM
                bom = unicode(codecs.BOM_UTF8, 'utf8')
                print '[espnlib]: %s' % string.replace(bom, '')
            except:
                pass

    def make_request(self, url, method, payload=None, headers=None, return_req=False):
        """Make an HTTP request. Return the response."""
        self.log('Request URL: %s' % url)
        try:
            if method == 'get':
                req = self.http_session.get(url, params=payload, headers=headers, allow_redirects=False,
                                            verify=self.verify_ssl)
            else:  # post
                req = self.http_session.post(url, data=payload, headers=headers, allow_redirects=False,
                                             verify=self.verify_ssl)
            req.raise_for_status()
            self.log('Response code: %s' % req.status_code)
            self.log('Response: %s' % req.content)
            self.cookie_jar.save(ignore_discard=True, ignore_expires=False)
            if return_req:
                return req
            else:
                return req.content
        except requests.exceptions.HTTPError as error:
            self.log('An HTTP error occurred: %s' % error)
            raise
        except requests.exceptions.ConnectionError as error:
            self.log('Connection Error: - %s' % error.message)
            raise
        except requests.exceptions.RequestException as error:
            self.log('Error: - %s' % error.value)
            raise

    def login(self, username=None, password=None):
        """Complete login process for ESPN Player. Errors (auth issues, blackout,
        etc) are raised as LoginFailure.
        """
        if self.check_for_subscription():
            self.log('Already logged into ESPN Player.')
        else:
            if username and password:
                self.log('Not (yet) logged into ESPN Player.')
                self.login_to_account(username, password)
                if not self.check_for_subscription():
                    raise self.LoginFailure('Login failed')

            else:
                self.log('No username and password supplied.')
                raise self.LoginFailure('No username and password supplied.')

    def login_to_account(self, username, password):
        """authenticate to ESPN Player.
        """
        url = 'https://www.espnplayer.com/secure/authenticate'
        post_data = {
            'username': username,
            'password': password,
            'format': 'xml'
        }
        sc_data = self.make_request(url=url, method='post', payload=post_data)
        if 'loginsuccess' not in sc_data:
             raise self.LoginFailure('Login failed')

    def check_for_subscription(self):
        """Return whether a subscription is detected.
        """
        url = "https://www.espnplayer.com/account/subscriptions"
        post_data = {'isFlex': 'true','format': 'xml'}
        sc_data = self.make_request(url=url, method='post', payload=post_data)
        sc_dict = xmltodict.parse(sc_data)
#        self.log(sc_dict)
#        if sc_dict['isBlocked'] == 'true':
#            self.log('ESPN Player is geo blocked.')
#            return False
        if 'sku' not in sc_data:
            self.log('No subscription detected in ESPN Player response.')
            return False
        else:
            self.log('Subscription detected in ESPN Player response.')
            return True

    def get_services(self):
        """Return a dict of the services the user is subscribed to."""
        services = {}
        subscribed_services = []
        url = 'https://www.espnplayer.com/account/subscriptions'
        post_data = {'format': 'xml','isFlex': 'true'}
        sc_data = self.make_request(url=url, method='post', payload=post_data)
        sc_dict = xmltodict.parse(sc_data)['subscriptions']
        if 'NCAA' in sc_data:
            services.update({'NCAA College Pass': 'ncaa'})
        
        if 'INDY' in sc_data:
            services.update({'IndyCar Series': 'indycar'})
  
        if 'SELECT' in sc_data:
            services.update({'ESPN Select': 'select'})

#        for service in sc_dict['subs'].values():
#            subscribed_services.append(service)

#        for service in sc_dict['leagues']['league']:
#            if service['type'] in subscribed_services:
#                services[service['name']] = service['type']
        
        return services

    def get_games(self, service, filter_date=False, filter_games=False, category='all'):
        """Return games in a list. Ability to sort games by date/game status."""
        url = 'https://www.espnplayer.com/schedule'
        filter_mask = { 0: 'upcoming',
                        1: 'inplay',
                        3: 'archive' 
        }
        games = []
        now = datetime.now()
        for month in range(-1,1):
            payload = {
                # 'product': service,
                # 'category': category,
                'lid': service,
                'format': 'json',
                'ps': 300,
                'monthly': "%d-%02d" % (now.year,(now.month+month))
            }
            games_data=self.make_request(url=url, method='get', payload=payload)
            games+=json.loads(games_data)['games']

        if filter_date:
            dgames = []
            for game in games:
                gamedate = self.parse_datetime(game['dateTimeGMT'], localize=True).date()
                if str(filter_date) == str(gamedate):
                    dgames.append(game)
            games = dgames

        if filter_games:
            fgames = []
            for game in games:
                game_status = game['gameState']
                if filter_games == filter_mask[game_status]:
                    fgames.append(game)
            games = fgames

        return games
    def get_token(self, airingId):
        """Return a token needed to request a pkan"""
        url = 'https://www.espnplayer.com/secure/espntoken'
        payload = {
            'airingId': airingId,
            'format': 'json',
            'isFlex': 'true'
        }
        sc_data = self.make_request(url=url, method='post', payload=payload)
        return json.loads(sc_data)['data']


    def get_pkan(self, token):
        """Return a 'pkan' token needed to request a stream URL.
           Requires a secure token
        """
        url = 'https://neulion.go.com/espngeo/dgetpkan'
        payload = {
            'airingId': token['airingId'],
            'auth_airingid': token['airingId'],
            'auth_timestamp': token['timestamp'],
            'auth_token': token['token'],
            'auth_usertrackname': token['userTrackName'],
            'isFlex': 'true'
        }
        pkan = self.make_request(url=url, method='post', payload=payload)
        return pkan

    def get_stream_url(self, airingId, channel='espn3'):
        """Return the URL for a stream. _mediaAuth cookie is needed for decryption."""
        stream_url = {}
        auth_cookie = None
        token = self.get_token(airingId)
        url = 'https://neulion.go.com/espngeo/startSession'
        payload = {
            'channel': channel,
            'playbackScenario': 'HTTP_CLOUD_WIRED',
            'playerId': 'neulion',
            'pkan': self.get_pkan(token),
            'pkanType': 'TOKEN',
            'tokenType': 'GATEKEEPER',
            'ttl': '480',
            'airingId': airingId,
            'auth_airingid': token['airingId'],
            'auth_timestamp': token['timestamp'],
            'auth_token': token['token'],
            'auth_usertrackname': token['userTrackName'],
            'simulcastAiringId': airingId if channel=='espn3' else 0
        }
        req = self.make_request(url=url, method='post', payload=payload, return_req=True)
        stream_data = req.content
        try:
            stream_dict = xmltodict.parse(stream_data)['user-verified-media-response']['user-verified-event']['user-verified-content']['user-verified-media-item']
        except KeyError:
            self.log('Unable to get stream dict.')
            stream_dict = False

        if req.cookies:
            self.log('Cookies: %s' % req.cookies)
            for cookie in req.cookies:
                if cookie.name == '_mediaAuth':
                    auth_cookie = '%s=%s; path=%s; domain=%s;' % (cookie.name, cookie.value, cookie.path, cookie.domain)

        if stream_dict:
            if stream_dict['url']:
                stream_url['manifest'] = stream_dict['url']
                self.log('HLS manifest found (primary).')
            elif stream_dict['hls-backup-url']:
                stream_url['manifest'] = stream_dict['hls-backup-url']
                self.log('HLS manifest found (backup).')
            elif stream_dict['alt-url']:
                stream_url['manifest'] = stream_dict['alt-url']
                self.log('HLS manifest found (alternative).')
            else:
                stream_url['manifest'] = None
                self.log('No HLS manifest found.')

        if stream_url['manifest']:
            if stream_url['manifest'].startswith('http'):
                stream_url['bitrates'] = self.parse_m3u8_manifest(stream_url['manifest'], auth_cookie=auth_cookie)
            else:
                stream_url['bitrates'] = []
                self.log('Invalid manifest URL found: %s' % stream_url['manifest'])

        return stream_url

    def parse_m3u8_manifest(self, manifest_url, auth_cookie=None):
        """Return the stream URL along with its bitrate."""
        streams = {}
        req = requests.get(manifest_url)
        m3u8_manifest = req.content
        self.log('HLS manifest: \n %s' % m3u8_manifest)

        m3u8_header = {'Cookie': auth_cookie}
        m3u8_obj = m3u8.loads(m3u8_manifest)

        for playlist in m3u8_obj.playlists:
            bitrate = int(playlist.stream_info.bandwidth) / 1000
            if playlist.uri.startswith('http'):
                stream_url = playlist.uri
            else:
                stream_url = manifest_url[:manifest_url.rfind('/') + 1] + playlist.uri
            streams[str(bitrate)] = stream_url + '|' + urlencode(m3u8_header)

        return streams

    def get_channels(self, service):
        """Return a dict with available channels for NCAA College Pass."""
        channels = {}
        url = 'https://www.espnplayer.com/channels'
        payload = {
        #     'product': service
            'lid': service,
            'format': 'xml'
        }

        channel_data = self.make_request(url=url, method='get', payload=payload)
        channel_dict = xmltodict.parse(channel_data)['result']['channels']['channel']

        for channel in channel_dict:
            channel_name = channel['name']
            channel_id = channel['seoName']
            channels[channel_name] = channel_id
        return channels

    def get_gamedates(self, service, filter=False):
        """Return a list with dates containing at least one game."""
        dates = []
        now = datetime.now()
        games = self.get_games(service)

        for game in games:
            gamedate = self.parse_datetime(game['dateTimeGMT'], localize=True).date()
            if gamedate not in dates:
                if filter == 'upcoming':
                    if gamedate > now.date():
                        dates.append(gamedate)
                elif filter == 'archive':
                    if gamedate < now.date():
                        dates.append(gamedate)
                else:
                    dates.append(gamedate)

        return dates

    def utc_to_local(self, utc_dt):
        """Convert UTC time to local time."""
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.fromtimestamp(timestamp)
        assert utc_dt.resolution >= timedelta(microseconds=1)
        return local_dt.replace(microsecond=utc_dt.microsecond)

    def parse_datetime(self, game_date, localize=False):
        """Parse ESPN Player date string to datetime object."""
        date_time_format = '%Y-%m-%dT%H:%M:%S.000'
        datetime_obj = datetime(*(time.strptime(game_date, date_time_format)[0:6]))
        if localize:
            datetime_obj = self.utc_to_local(datetime_obj)
        return datetime_obj
