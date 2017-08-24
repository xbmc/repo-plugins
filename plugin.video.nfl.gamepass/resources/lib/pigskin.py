"""
A Kodi-agnostic library for NFL Game Pass
"""
import codecs
import uuid
import sys
import json
import calendar
import time
import urllib
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import requests
import m3u8

class pigskin(object):
    def __init__(self, proxy_config, debug=False):
        self.debug = debug
        self.base_url = 'https://www.nflgamepass.com'
        self.user_agent = 'Firefox'
        self.http_session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.config = self.make_request(self.base_url + '/api/en/content/v1/web/config', 'get')
        self.client_id = self.config['modules']['API']['CLIENT_ID']
        self.nfln_shows = {}
        self.nfln_seasons = []
        self.parse_shows()

        if proxy_config is not None:
            proxy_url = self.build_proxy_url(proxy_config)
            if proxy_url != '':
                self.http_session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url,
                }

        self.log('Debugging enabled.')
        self.log('Python Version: %s' % sys.version)

    class GamePassError(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)

    def log(self, string):
        if self.debug:
            try:
                print '[pigskin]: %s' % string
            except UnicodeEncodeError:
                # we can't anticipate everything in unicode they might throw at
                # us, but we can handle a simple BOM
                bom = unicode(codecs.BOM_UTF8, 'utf8')
                print '[pigskin]: %s' % string.replace(bom, '')
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

        return self.parse_response(req)

    def parse_response(self, req):
        """Try to load JSON data into dict and raise potential errors."""
        try:
            response = json.loads(req.content)
        except ValueError:  # if response is not json
            response = req.content

        if isinstance(response, dict):
            for key in response.keys():
                if key.lower() == 'message':
                    if response[key]: # raise all messages as GamePassError if message is not empty
                        raise self.GamePassError(response[key])

        return response

    def build_proxy_url(self, config):
        proxy_url = ''

        if 'scheme' in config:
            scheme = config['scheme'].lower().strip()
            if scheme != 'http' and scheme != 'https':
                return ''
            proxy_url += scheme + '://'

        if 'auth' in config and config['auth'] is not None:
            try:
                username = config['auth']['username']
                password = config['auth']['password']
                if username == '' or password == '':
                    return ''
                proxy_url += '%s:%s@' % (urllib.quote(username), urllib.quote(password))
            except KeyError:
                return ''

        if 'host' not in config or config['host'].strip() == '':
            return ''
        proxy_url += config['host'].strip()

        if 'port' in config:
            try:
                port = int(config['port'])
                if port <= 0 or port > 65535:
                    return ''
                proxy_url += ':' + str(port)
            except ValueError:
                return ''

        return proxy_url

    def login(self, username, password):
        """Blindly authenticate to Game Pass. Use has_subscription() to
        determine success.
        """
        url = self.config['modules']['API']['LOGIN']
        post_data = {
            'username': username,
            'password': password,
            'client_id': self.client_id,
            'grant_type': 'password'
        }
        data = self.make_request(url, 'post', payload=post_data)
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.check_for_subscription()

        return True

    def check_for_subscription(self):
        """Returns True if a subscription is detected. Raises error_unauthorised on failure."""
        url = self.config['modules']['API']['USER_PROFILE']
        headers = {'Authorization': 'Bearer {0}'.format(self.access_token)}
        self.make_request(url, 'get', headers=headers)

        return True

    def refresh_tokens(self):
        """Refreshes authorization tokens."""
        url = self.config['modules']['API']['LOGIN']
        post_data = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'grant_type': 'refresh_token'
        }
        data = self.make_request(url, 'post', payload=post_data)
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']

        return True

    def get_seasons_and_weeks(self):
        """Return a multidimensional array of all seasons and weeks."""
        seasons_and_weeks = {}

        try:
            url = self.config['modules']['ROUTES_DATA_PROVIDERS']['games']
            seasons = self.make_request(url, 'get')
        except:
            self.log('Acquiring season and week data failed.')
            raise

        try:
            for season in seasons['modules']['mainMenu']['seasonStructureList']:
                weeks = []
                year = str(season['season'])
                for season_type in season['seasonTypes']:
                    for week in season_type['weeks']:
                        week_dict = {
                            'week_number': str(week['number']),
                            'week_name': week['weekNameAbbr'],
                            'season_type': season_type['seasonType']
                        }
                        weeks.append(week_dict)

                seasons_and_weeks[year] = weeks
        except KeyError:
            self.log('Parsing season and week data failed.')
            raise

        return seasons_and_weeks

    def get_current_season_and_week(self):
        """Return the current season, season type, and week in a dict."""
        try:
            url = self.config['modules']['ROUTES_DATA_PROVIDERS']['games']
            seasons = self.make_request(url, 'get')
        except:
            self.log('Acquiring season and week data failed.')
            raise

        current_s_w = {
            'season': seasons['modules']['meta']['currentContext']['currentSeason'],
            'season_type': seasons['modules']['meta']['currentContext']['currentSeasonType'],
            'week': str(seasons['modules']['meta']['currentContext']['currentWeek'])
        }

        return current_s_w

    def get_weeks_games(self, season, season_type, week):
        try:
            url = self.config['modules']['ROUTES_DATA_PROVIDERS']['games_detail'].replace(':seasonType', season_type).replace(':season', season).replace(':week', week)
            games_data = self.make_request(url, 'get')
            # collect the games from all keys in 'modules' that has 'content' as a key
            games = [g for x in games_data['modules'].keys() if 'content' in games_data['modules'][x] for g in games_data['modules'][x]['content']]
        except:
            self.log('Acquiring games data failed.')
            raise

        return sorted(games, key=lambda x: x['gameDateTimeUtc'])

    def get_team_games(self, season, team=None):
        try:
            url = self.config['modules']['ROUTES_DATA_PROVIDERS']['teams']
            teams = self.make_request(url, 'get')
            if team is None:
                return teams
            else:
                # look for the team name
                for conference in teams['modules']:
                    if 'content' in teams['modules'][conference]:
                        for teamname in teams['modules'][conference]['content']:
                            if team == teamname['fullName']:
                                team = teamname['seoname']
                                break;
                            else:
                                return None

                url = self.config['modules']['ROUTES_DATA_PROVIDERS']['team_detail'].replace(':team', team)
                games_data = self.make_request(url, 'get')
                # collect games from all keys in 'modules' for a specific season
                games = [g for x in games_data['modules'].keys() if x == 'videos'+season for g in games_data['modules'][x]['content']]

        except:
            self.log('Acquiring Team games data failed.')
            raise

        return sorted(games, key=lambda x: x['gameDateTimeUtc'])

    def get_game_versions(self, game_id, season):
        """Return a dict of available game versions for a single game."""
        game_versions = {}
        url = self.config['modules']['ROUTES_DATA_PROVIDERS']['game_page'].replace(':season', season).replace(':gameslug', game_id)
        data = self.make_request(url, 'get')['modules']['singlegame']['content'][0]
        for key in data.keys():
            if isinstance(data[key], dict) and 'videoId' in data[key]:
                game_versions[data[key]['kind']] = data[key]['videoId']

        self.log('Game versions found for {0}: {1}'.format(game_id, ', '.join(game_versions.keys())))
        return game_versions

    def get_stream(self, video_id, game_type=None, username=None):
        """Return the URL for a stream."""
        self.refresh_tokens()

        if video_id == 'nfl_network':
            diva_config_url = self.config['modules']['DIVA']['HTML5']['SETTINGS']['Live24x7']
            url = self.config['modules']['ROUTES_DATA_PROVIDERS']['network']
            response = self.make_request(url, 'get')
            video_id = response['modules']['networkLiveVideo']['content'][0]['videoId']
        else:
            if game_type == 'live':
                diva_config_url = self.config['modules']['DIVA']['HTML5']['SETTINGS']['LiveNoData']
            else:
                diva_config_url = self.config['modules']['DIVA']['HTML5']['SETTINGS']['VodNoData']

        diva_config_data = self.make_request(diva_config_url.replace('device', 'html5'), 'get')
        diva_config_root = ET.fromstring(diva_config_data)
        for i in diva_config_root.iter('parameter'):
            if i.attrib['name'] == 'processingUrlCallPath':
                processing_url = i.attrib['value']
            elif i.attrib['name'] == 'videoDataPath':
                stream_request_url = i.attrib['value'].replace('{V.ID}', video_id)
        akamai_xml_data = self.make_request(stream_request_url, 'get')
        akamai_xml_root = ET.fromstring(akamai_xml_data)
        for i in akamai_xml_root.iter('videoSource'):
            if i.attrib['format'] == 'ChromeCast':
                for text in i.itertext():
                    if 'http' in text:
                        m3u8_url = text
                        break

        post_data = {
            'Type': '1',
            'User': '',
            'VideoId': video_id,
            'VideoSource': m3u8_url,
            'VideoKind': 'Video',
            'AssetState': '3',
            'PlayerType': 'HTML5',
            'other': '{0}|{1}|web|{1}|undefined|{2}' .format(str(uuid.uuid4()), self.access_token, self.user_agent, username)
        }

        response = self.make_request(processing_url, 'post', payload=json.dumps(post_data))

        return self.parse_m3u8_manifest(response['ContentUrl'])

    def parse_m3u8_manifest(self, manifest_url):
        """Return the manifest URL along with its bitrate."""
        streams = {}
        m3u8_header = {
            'Connection': 'keep-alive',
            'User-Agent': self.user_agent
        }
        streams['manifest_url'] = manifest_url + '|' + urllib.urlencode(m3u8_header)
        streams['bitrates'] = {}
        m3u8_manifest = self.make_request(manifest_url, 'get')
        m3u8_obj = m3u8.loads(m3u8_manifest)
        for playlist in m3u8_obj.playlists:
            bitrate = int(playlist.stream_info.bandwidth) / 1000
            streams['bitrates'][bitrate] = manifest_url[:manifest_url.rfind('/manifest') + 1] + playlist.uri + '?' + manifest_url.split('?')[1] + '|' + urllib.urlencode(m3u8_header)

        return streams

    def redzone_on_air(self):
        """Return whether RedZone Live is currently broadcasting."""
        url = self.config['modules']['ROUTES_DATA_PROVIDERS']['redzone']
        response = self.make_request(url, 'get')
        if not response['modules']['redZoneLive']['content']:
            return False
        else:
            return True

    def parse_shows(self):
        """Dynamically parse the NFL Network shows into a dict."""
        show_dict = {}
        url = self.config['modules']['API']['NETWORK_PROGRAMS']
        response = self.make_request(url, 'get')

        for show in response['modules']['programs']:
            season_dict = {}
            for season in show['seasons']:
                season_name = season['value']
                season_id = season['slug']
                season_dict[season_name] = season_id
                if season_name not in self.nfln_seasons:
                    self.nfln_seasons.append(season_name)
            show_dict[show['title']] = season_dict
        self.nfln_shows.update(show_dict)

    def get_shows(self, season):
        """Return a list of all shows for a season."""
        seasons_shows = []

        for show_name, show_codes in self.nfln_shows.items():
            if season in show_codes:
                seasons_shows.append(show_name)

        return sorted(seasons_shows)

    def get_shows_episodes(self, show_name, season=None):
        """Return a list of episodes for a show. Return empty list if none are
        found or if an error occurs."""
        url = self.config['modules']['API']['NETWORK_PROGRAMS']
        programs = self.make_request(url, 'get')['modules']['programs']
        for show in programs:
            if show_name == show['title']:
                selected_show = show
                break
        season_slug = [x['slug'] for x in selected_show['seasons'] if season == x['value']][0]
        request_url = self.config['modules']['API']['NETWORK_EPISODES']
        episodes_url = request_url.replace(':seasonSlug', season_slug).replace(':tvShowSlug', selected_show['slug'])
        episodes_data = self.make_request(episodes_url, 'get')['modules']['archive']['content']
        for episode in episodes_data:
            if not episode['videoThumbnail']['templateUrl']:  # set programs thumbnail as episode thumbnail
                episode['videoThumbnail']['templateUrl'] = [x['thumbnail']['templateUrl'] for x in programs if x['slug'] == episode['nflprogram']][0]

        return episodes_data

    def parse_datetime(self, date_string, localize=False):
        """Parse NFL Game Pass date string to datetime object."""
        date_time_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        datetime_obj = datetime(*(time.strptime(date_string, date_time_format)[0:6]))
        if localize:
            return self.utc_to_local(datetime_obj)
        else:
            return datetime_obj

    @staticmethod
    def utc_to_local(utc_dt):
        """Convert UTC time to local time."""
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.fromtimestamp(timestamp)
        assert utc_dt.resolution >= timedelta(microseconds=1)
        return local_dt.replace(microsecond=utc_dt.microsecond)
