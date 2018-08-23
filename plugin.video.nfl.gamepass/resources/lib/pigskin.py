"""
A Python library for NFL Game Pass
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
        self.episode_list = []

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
                print('[pigskin]: %s' % string)
            except UnicodeEncodeError:
                # we can't anticipate everything in unicode they might throw at
                # us, but we can handle a simple BOM
                bom = unicode(codecs.BOM_UTF8, 'utf8')
                print('[pigskin]: %s' % string.replace(bom, ''))
            except:
                pass

    def make_request(self, url, method, params=None, payload=None, headers=None):
        """Make an HTTP request. Return the response."""
        self.log('Request URL: %s' % url)
        self.log('Method: %s' % method)
        if params:
            self.log('Params: %s' % params)
        if payload:
            if 'password' in payload:
                password = payload['password']
                payload['password'] = 'xxxxxxxxxxxx'
            self.log('Payload: %s' % payload)
            if 'password' in payload:
                payload['password'] = password
        if headers:
            self.log('Headers: %s' % headers)

        # requests session implements connection pooling, after being idle for
        # some time the connection might be closed server side.
        # In case it's the servers being very slow, the timeout should fail fast
        # and retry with longer timeout.
        failed = False
        for t in [3, 22]:
            try:
                if method == 'get':
                    req = self.http_session.get(url, params=params, headers=headers, timeout=t)
                elif method == 'put':
                    req = self.http_session.put(url, params=params, data=payload, headers=headers, timeout=t)
                else:  # post
                    req = self.http_session.post(url, params=params, data=payload, headers=headers, timeout=t)
                # We made it without error, exit the loop
                break
            except requests.Timeout:
                self.log('Timeout condition occurred after %i seconds' % t)
                if failed:
                    # failed twice while sending request
                    # TODO: this should be raised so the user can be informed.
                    pass
                else:
                    failed = True
            except:
                # something else went wrong, not a timeout
                # TODO: raise this
                pass

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
                    if response[key]:  # raise all messages as GamePassError if message is not empty
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
        """Attempt to authenticate to Game Pass. Raises error_unauthorised on failure.
        Use check_for_subscription() to determine if the user has a valid subscription."""
        url = self.config['modules']['API']['LOGIN']
        post_data = {
            'username': username,
            'password': password,
            'client_id': self.client_id,
            'grant_type': 'password'
        }
        try:
            data = self.make_request(url, 'post', payload=post_data)
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']
            self.check_for_subscription()
        except TypeError:
            self.log('Login Failed.')
            self.log(data)
            raise self.GamePassError('failed_login')

        return True

    def check_for_subscription(self):
        """Return True if a subscription is detected and raise 'no_subscription' on failure."""
        url = self.config['modules']['API']['USER_ACCOUNT']
        headers = {'Authorization': 'Bearer {0}'.format(self.access_token)}
        account_data = self.make_request(url, 'get', headers=headers)

        try:
            self.log('subscription: %s' % account_data['subscriptions'])
            return True
        except TypeError:
            self.log('No active NFL Game Pass Europe subscription was found.')
            raise self.GamePassError('no_subscription')

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
                                break
                            else:
                                return None

                url = self.config['modules']['ROUTES_DATA_PROVIDERS']['team_detail'].replace(':team', team)
                games_data = self.make_request(url, 'get')
                # collect games from all keys in 'modules' for a specific season
                # At the moment, only the Current Season which is supported;
                # maybe the season category will return so this code will only
                # be commented out.
                # games = [g for x in games_data['modules'].keys() if x == 'videos'+season for g in games_data['modules'][x]['content']]
                games = [g for x in games_data['modules'].keys() if x == 'gamesCurrentSeason' for g in games_data['modules'][x]['content']]

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

    def get_streams(self, video_id, game_type=None, username=None):
        """Return a dict of available streams."""
        streams = {}
        m3u8_header = {
            'Connection': 'keep-alive',
            'User-Agent': self.user_agent
        }
        self.refresh_tokens()

        if video_id == 'nfl_network':
            diva_config_url = self.config['modules']['DIVA']['HTML5']['SETTINGS']['Live24x7']
            url = self.config['modules']['ROUTES_DATA_PROVIDERS']['network']
            response = self.make_request(url, 'get')
            video_id = response['modules']['networkLiveVideo']['content'][0]['videoId']
        elif video_id == 'redzone':
            diva_config_url = self.config['modules']['DIVA']['HTML5']['SETTINGS']['Live24x7']
            url = self.config['modules']['ROUTES_DATA_PROVIDERS']['redzone']
            response = self.make_request(url, 'get')
            video_id = response['modules']['redZoneLive']['content'][0]['videoId']
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
            try:
                vs_format = i.attrib['format'].lower()
                vs_url = i.findtext('uri')

                post_data = {
                    'Type': '1',
                    'User': '',
                    'VideoId': video_id,
                    'VideoSource': vs_url,
                    'VideoKind': 'Video',
                    'AssetState': '3',
                    'PlayerType': 'HTML5',
                    'other': '{0}|{1}|web|{1}|undefined|{2}' .format(str(uuid.uuid4()), self.access_token, self.user_agent, username)
                }
                response = self.make_request(processing_url, 'post', payload=json.dumps(post_data))

                streams[vs_format] = response['ContentUrl'] + '|' + urllib.urlencode(m3u8_header)

            except:
                pass

        return streams

    def m3u8_to_dict(self, manifest_url):
        """Return a dict of available bitrates and their respective stream. This
        is especially useful if you need to pass a URL to a player that doesn't
        support adaptive streaming."""
        streams = {}
        m3u8_header = {
            'Connection': 'keep-alive',
            'User-Agent': self.user_agent
        }

        m3u8_manifest = self.make_request(manifest_url, 'get')
        m3u8_obj = m3u8.loads(m3u8_manifest)
        for playlist in m3u8_obj.playlists:
            bitrate = int(playlist.stream_info.bandwidth) / 1000
            streams[bitrate] = manifest_url[:manifest_url.rfind('/manifest') + 1] + playlist.uri + '?' + manifest_url.split('?')[1] + '|' + urllib.urlencode(m3u8_header)

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

        # NFL Network shows
        url = self.config['modules']['API']['NETWORK_PROGRAMS']
        response = self.make_request(url, 'get')
        current_season = self.get_current_season_and_week()['season']

        for show in response['modules']['programs']:
            # Unfortunately, the 'seasons' list for each show cannot be trusted.
            # So we loop over every episode for every show to build the list.
            # TODO: this causes a lot of network traffic and slows down init
            #       quite a bit. Would be nice to have a better workaround.
            request_url = self.config['modules']['API']['NETWORK_EPISODES']
            episodes_url = request_url.replace(':seasonSlug/', '').replace(':tvShowSlug', show['slug'])
            episodes_data = self.make_request(episodes_url, 'get')['modules']['archive']['content']

            # 'season' is often left unset. It's impossible to know for sure,
            # but the year of the current Season seems like a sane best guess.
            season_list = set([episode['season'].replace('season-', '')
                               if episode['season'] else current_season
                               for episode in episodes_data])

            show_dict[show['title']] = season_list

            # Adding NFL-Network as a List of dictionary containing oher dictionaries.
            # episode_thumbnail = {videoId, thumbnail}
            # episode_id_dict = {episodename, episode_thumbnail{}}
            # episode_season_dict = {episode_season, episode_id_dict{}}
            # show_season_dict = {show_title, episode_season_dict{}}
            # The Function returns all Season and Episodes
            for episode in episodes_data:
                episode_thumbnail = {}
                episode_id_dict = {}
                episode_season_dict = {}
                show_season_dict = {}
                episode_name = episode['title']
                episode_id = episode['videoId']
                if episode['season']:
                    episode_season = episode['season'].replace('season-', '')
                else:
                    episode_season = current_season
                # Using Episode Thumbnail if not present use theire corresponding Show Thumbnail
                if episode['videoThumbnail']['templateUrl']:
                    episode_thumbnail[episode_id] = episode['videoThumbnail']['templateUrl']
                else:
                    episode_thumbnail[episode_id] = show['thumbnail']['templateUrl']
                episode_id_dict[episode_name] = episode_thumbnail
                episode_season_dict[episode_season] = episode_id_dict
                show_season_dict[show['title']] = episode_season_dict
                self.episode_list.append(show_season_dict)

        # Adding RedZone as a List of dictionary containing oher dictionaries.
        # episode_thumbnail = {videoId, thumbnail}
        # episode_id_dict = {episodename, episode_thumbnail{}}
        # episode_season_dict = {episode_season, episode_id_dict{}}
        # show_season_dict = {show_title, episode_season_dict{}}
        # The Function returns all Season and Episodes
        url = self.config['modules']['ROUTES_DATA_PROVIDERS']['redzone']
        response = self.make_request(url, 'get')

        season_list = []
        for episode in response['modules']['redZoneVod']['content']:
            season_name = episode['season'].replace('season-', '')
            season_list.append(season_name)
            episode_thumbnail = {}
            episode_id_dict = {}
            episode_season_dict = {}
            show_season_dict = {}
            episode_name = episode['title']
            episode_id = episode['videoId']
            if episode['season']:
                episode_season = episode['season'].replace('season-', '')
            else:
                episode_season = current_season
            # Using Episode Thumbnail if not present use theire corresponding Show Thumbnail
            if episode['videoThumbnail']['templateUrl']:
                episode_thumbnail[episode_id] = episode['videoThumbnail']['templateUrl']
            else:
                episode_thumbnail[episode_id] = ''
            episode_id_dict[episode_name] = episode_thumbnail
            episode_season_dict[episode_season] = episode_id_dict
            show_season_dict['RedZone'] = episode_season_dict
            self.episode_list.append(show_season_dict)

        show_dict['RedZone'] = season_list
        self.nfln_shows.update(show_dict)

    def get_shows(self, season):
        """Return a list of all shows for a season."""
        seasons_shows = []

        for show_name, years in self.nfln_shows.items():
            if season in years:
                seasons_shows.append(show_name)

        return sorted(seasons_shows)

    def get_shows_episodes(self, show_name, season=None):
        """Return a list of episodes for a show. Return empty list if none are
        found or if an error occurs."""
        # Create a List of all games related to a specific show_name and a season.
        # The returning List contains episode name, episode id and episode thumbnail
        episodes_data = []
        for episode in self.episode_list:
            for dict_show_name, episode_season_dict in episode.items():
                if dict_show_name == show_name:
                    for episode_season, episode_id_dict in episode_season_dict.items():
                        if episode_season == season:
                            episodes_data.append(episode_id_dict)

        return episodes_data

    def parse_datetime(self, date_string, localize=False):
        """Parse NFL Game Pass date string to datetime object."""
        date_time_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        datetime_obj = datetime(*(time.strptime(date_string, date_time_format)[0:6]))

        if localize:
            return self.utc_to_local(datetime_obj)

        return datetime_obj

    @staticmethod
    def utc_to_local(utc_dt):
        """Convert UTC time to local time."""
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.fromtimestamp(timestamp)
        assert utc_dt.resolution >= timedelta(microseconds=1)
        return local_dt.replace(microsecond=utc_dt.microsecond)
