"""
A Kodi-agnostic library for NFL Game Pass and Game Rewind support.
"""
import codecs
import cookielib
import hashlib
import random
import m3u8
import urllib
from traceback import format_exc
from uuid import getnode as get_mac
from urlparse import urlsplit

import requests
import xmltodict


class pigskin(object):
    def __init__(self, subscription, proxy_config, cookie_file, debug=False):
        self.subscription = subscription
        self.debug = debug
        self.non_seasonal_shows = {'Super Bowl Archives': '117'}
        self.seasonal_shows = {
            'NFL Gameday': {'2015': '252', '2014': '212', '2013': '179', '2012': '146'},
            'Top 100 Players': {'2015': '257', '2014': '217', '2013': '185', '2012': '153'}
        }
        self.boxscore_url = 'http://neulionms-a.akamaihd.net/fs/nfl/nfl/edl/nflgr'

        if subscription == 'gamepass':
            self.base_url = 'https://gamepass.nfl.com/nflgp'
            self.servlets_url = 'http://gamepass.nfl.com/nflgp/servlets'
            self.seasonal_shows.update({
                'Playbook': {'2015': '255', '2014': '213', '2013': '180', '2012': '147'},
                'NFL Total Access': {'2015': '254', '2014': '214', '2013': '181', '2012': '148'},
                'NFL RedZone Archives': {'2015': '248', '2014': '221', '2013': '182', '2012': '149'},
                'Sound FX': {'2015': '256', '2014': '215', '2013': '183', '2012': '150'},
                'Coaches Show': {'2014': '216', '2013': '184', '2012': '151'},
                'A Football Life': {'2015': '249', '2014': '218', '2013': '186', '2012': '154'},
                'NFL Films Presents': {'2014': '219', '2013': '187'},
                'Hard Knocks': {'2015': '251', '2014': '220', '2013': '223'},
                'Hall of Fame': {'2015': '253', '2014': '222'}
            })
        elif subscription == 'gamerewind':
            self.base_url = 'https://gamerewind.nfl.com/nflgr'
            self.servlets_url = 'http://gamerewind.nfl.com/nflgr/servlets'

        else:
            raise ValueError('"%s" is not a supported subscription.' % subscription)

        self.http_session = requests.Session()
        if proxy_config is not None:
            proxy_url = self.build_proxy_url(proxy_config)
            if proxy_url != '':
                self.http_session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url,
                }
        self.cookie_jar = cookielib.LWPCookieJar(cookie_file)
        try:
            self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
        except IOError:
            pass
        self.http_session.cookies = self.cookie_jar

    class LoginFailure(Exception):
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

    def check_for_coachestape(self, game_id, season):
        """Return whether coaches tape is available for a given game."""
        url = self.boxscore_url + '/' + season + '/' + game_id + '.xml'
        boxscore = self.make_request(url=url, method='get')

        try:
            boxscore_dict = xmltodict.parse(boxscore, encoding='cp1252')
        except xmltodict.expat.ExpatError:
            try:
                boxscore_dict = xmltodict.parse(boxscore)
            except xmltodict.expat.ExpatError:
                return False

        try:
            if boxscore_dict['dataset']['@coach'] == 'true':
                return True
            else:
                return False
        except KeyError:
            return False

    def check_for_subscription(self):
        """Return whether a subscription and user name are detected. Determines
        whether a login was successful."""
        url = self.servlets_url + '/simpleconsole'
        post_data = {'isFlex': 'true'}
        sc_data = self.make_request(url=url, method='post', payload=post_data)

        if '</userName>' not in sc_data:
            self.log('No user name detected.')
            return False
        elif '</subscription>' not in sc_data:
            self.log('No subscription detected.')
            return False
        else:
            self.log('Subscription and user name detected.')
            return True

    def gen_plid(self):
        """Return a "unique" MD5 hash. Getting the video path requires a plid,
        which looks like an and always changes. Reusing a plid does not work,
        so our guess is that it's a id for each instance of the player.
        """
        rand = random.getrandbits(10)
        mac_address = str(get_mac())
        md5 = hashlib.md5(str(rand) + mac_address)
        return md5.hexdigest()

    def get_coaches_playIDs(self, game_id, season):
        """Return a dict of play IDs with associated play descriptions."""
        playIDs = {}
        url = self.boxscore_url + '/' + season + '/' + game_id + '.xml'
        boxscore = self.make_request(url=url, method='get')

        try:
            boxscore_dict = xmltodict.parse(boxscore, encoding='cp1252')
        except xmltodict.expat.ExpatError:
            try:
                boxscore_dict = xmltodict.parse(boxscore)
            except xmltodict.expat.ExpatError:
                return False

        for row in boxscore_dict['dataset']['table']['row']:
            playIDs[row['@PlayID']] = row['@PlayDescription']

        return playIDs

    def get_coaches_url(self, game_id, game_date, event_id):
        """Return the URL for a coaches-film play."""
        self.get_current_season_and_week()  # set cookies
        url = self.servlets_url + '/publishpoint'

        post_data = {'id': game_id, 'type': 'game', 'nt': '1', 'gt': 'coach',
                     'event': event_id, 'bitrate': '1600', 'gdate': game_date}
        headers = {'User-Agent': 'iPad'}
        coach_data = self.make_request(url=url, method='post', payload=post_data, headers=headers)
        coach_dict = xmltodict.parse(coach_data)['result']

        return coach_dict['path']

    def get_current_season_and_week(self):
        """Return the current season and week_code (e.g. 210) in a dict."""
        url = self.servlets_url + '/simpleconsole'
        post_data = {'isFlex': 'true'}
        sc_data = self.make_request(url=url, method='post', payload=post_data)

        sc_dict = xmltodict.parse(sc_data)['result']
        current_s_w = {sc_dict['currentSeason']: sc_dict['currentWeek']}
        return current_s_w

    def get_publishpoint_streams(self, video_id, stream_type=None, game_type=None):
        """Return the URL for a stream."""
        streams = {}
        self.get_current_season_and_week()  # set cookies
        url = self.servlets_url + '/publishpoint'

        if video_id == 'nfl_network':
            post_data = {'id': '1', 'type': 'channel', 'nt': '1'}
        elif video_id == 'redzone':
            post_data = {'id': '2', 'type': 'channel', 'nt': '1'}
        elif stream_type == 'game':
            post_data = {'id': video_id, 'type': stream_type, 'nt': '1', 'gt': game_type}
        else:
            post_data = {'id': video_id, 'type': stream_type, 'nt': '1'}

        # I hate lying with User-Agent. Points to anyone who can get all the
        # streams we need without lying.
        headers = {'User-Agent': 'iPad'}
        m3u8_data = self.make_request(url=url, method='post', payload=post_data, headers=headers)
        m3u8_dict = xmltodict.parse(m3u8_data)['result']
        self.log('NFL Dict %s' % m3u8_dict)

        m3u8_url = m3u8_dict['path'].replace('_ipad', '')
        m3u8_param = m3u8_url.split('?', 1)[-1]
        # Please don't add User-Agent here unless you are /sure/ it is needed
        m3u8_header = {'Cookie': 'nlqptid=' + m3u8_param, 'Accept-encoding': 'identity', 'Connection': 'keep-alive'}

        m3u8_obj = m3u8.load(m3u8_url)
        if m3u8_obj.is_variant:  # if this m3u8 contains links to other m3u8s
            for playlist in m3u8_obj.playlists:
                bitrate = str(int(playlist.stream_info.bandwidth[:playlist.stream_info.bandwidth.find(' ')])/100)
                streams[bitrate] = m3u8_url[:m3u8_url.rfind('/') + 1] + playlist.uri + '?' + m3u8_url.split('?')[1] + '|' + urllib.urlencode(m3u8_header)
        else:
            streams['only available'] = m3u8_url

        return streams

    def get_shows(self, season):
        """Return a list of all shows for a season."""
        seasons_shows = self.non_seasonal_shows.keys()
        for show_name, show_codes in self.seasonal_shows.items():
            if season in show_codes:
                seasons_shows.append(show_name)

        return sorted(seasons_shows)

    def get_shows_episodes(self, show_name, season=None):
        """Return a list of episodes for a show. Return empty list if none are
        found or if an error occurs.
        """
        url = self.servlets_url + '/browse'
        try:
            cid = self.seasonal_shows[show_name][season]
        except KeyError:
            try:
                cid = self.non_seasonal_shows[show_name]
            except KeyError:
                return []

        if show_name == 'NFL RedZone Archives':
            ps = 17
        else:
            ps = 50

        post_data = {
            'isFlex': 'true',
            'cid': cid,
            'pm': 0,
            'ps': ps,
            'pn': 1
        }

        archive_data = self.make_request(url=url, method='post', payload=post_data)
        archive_dict = xmltodict.parse(archive_data)['result']

        try:
            items = archive_dict['programs']['program']
            # if only one episode is returned, we explicitly put it into a list
            if isinstance(items, dict):
                items = [items]
            return items
        except TypeError:
            return []

    def get_seasons_and_weeks(self):
        """Return a multidimensional array of all seasons and weeks."""
        seasons_and_weeks = {}

        try:
            url = 'http://smb.cdnak.neulion.com/fs/nfl/nfl/mobile/weeks_v2.xml'
            s_w_data = self.make_request(url=url, method='get')
            s_w_data_dict = xmltodict.parse(s_w_data)
        except:
            self.log('Acquiring season and week data failed.')
            raise

        try:
            for season in s_w_data_dict['seasons']['season']:
                year = season['@season']
                season_dict = {}

                for week in season['week']:
                    if week['@section'] == "pre":  # preseason
                        week_code = '1' + week['@value'].zfill(2)
                        season_dict[week_code] = week
                    else:  # regular season and post season
                        week_code = '2' + week['@value'].zfill(2)
                        season_dict[week_code] = week

                seasons_and_weeks[year] = season_dict
        except KeyError:
            self.log('Parsing season and week data failed.')
            raise

        return seasons_and_weeks

    def get_weeks_games(self, season, week_code):
        """Return a list of games for a week."""
        url = self.servlets_url + '/games'
        post_data = {
            'isFlex': 'true',
            'season': season,
            'week': week_code
        }

        game_data = self.make_request(url=url, method='post', payload=post_data)
        game_data_dict = xmltodict.parse(game_data)['result']
        games = game_data_dict['games']['game']
        # if only one game is returned, we explicitly put it into a list
        if isinstance(games, dict):
            games = [games]

        return games

    # Handles necessary steps and checks to login to Game Pass/Rewind
    def login(self, username=None, password=None):
        """Complete login process for Game Pass/Rewind. Errors (auth issues,
        blackout, etc) are raised as LoginFailure.
        """
        if self.check_for_subscription():
            self.log('Already logged into %s' % self.subscription)
        else:
            if username and password:
                self.log('Not (yet) logged into %s' % self.subscription)
                self.login_to_account(username, password)
                if not self.check_for_subscription():
                    raise self.LoginFailure('%s login failed' % self.subscription)
                elif self.subscription == 'gamerewind' and self.service_blackout():
                    raise self.LoginFailure('Game Rewind Blackout')
            else:
                # might need sans-login check here for Game Pass, though as of
                # 2014, there /may/ no longer be any sans-login regions.
                self.log('No username and password supplied.')
                raise self.LoginFailure('No username and password supplied.')

    def login_to_account(self, username, password):
        """Blindly authenticate to Game Pass/Rewind. Use
        check_for_subscription() to determine success.
        """
        url = self.base_url + '/secure/nfllogin'
        post_data = {
            'username': username,
            'password': password
        }
        self.make_request(url=url, method='post', payload=post_data)

    def make_request(self, url, method, payload=None, headers=None):
        """Make an http request. Return the response."""
        self.log('Request URL: %s' % url)
        self.log('Headers: %s' % headers)

        try:
            if method == 'get':
                req = self.http_session.get(url, params=payload, headers=headers, allow_redirects=False)
            else:  # post
                req = self.http_session.post(url, data=payload, headers=headers, allow_redirects=False)
            self.log('Response code: %s' % req.status_code)
            self.log('Response: %s' % req.content)
            self.cookie_jar.save(ignore_discard=True, ignore_expires=False)
            return req.content
        except requests.exceptions.RequestException as error:
            self.log('Error: - %s' % error.value)

    def parse_manifest(self, manifest):
        """Return a dict of the supplied XML manifest. Builds and adds
        "full_url" for convenience.
        """
        streams = {}
        manifest_dict = xmltodict.parse(manifest)

        for stream in manifest_dict['channel']['streamDatas']['streamData']:
            try:
                url_path = stream['@url']
                bitrate = url_path[(url_path.rindex('_') + 1):url_path.rindex('.')]
                try:
                    stream['full_url'] = 'http://%s%s.m3u8' % (stream['httpservers']['httpserver']['@name'], url_path)
                except TypeError:  # if multiple servers are returned, use the first in the list
                    stream['full_url'] = 'http://%s%s.m3u8' % (stream['httpservers']['httpserver'][0]['@name'], url_path)

                streams[bitrate] = stream
            except KeyError:
                self.log(format_exc())

        return streams

    def redzone_on_air(self):
        """Return whether RedZone Live is currently broadcasting."""
        url = self.servlets_url + '/simpleconsole'
        post_data = {'isFlex': 'true'}
        sc_data = self.make_request(url=url, method='post', payload=post_data)

        sc_dict = xmltodict.parse(sc_data)['result']
        if sc_dict['rzPhase'] == 'in':
            self.log('RedZone is on air.')
            return True
        else:
            self.log('RedZone is not on air.')
            return False

    def service_blackout(self):
        """Return whether Game Rewind is blacked out."""
        url = self.base_url + '/secure/schedule'
        blackout_message = ('Due to broadcast restrictions, the NFL Game Rewind service is currently unavailable.'
                            ' Please check back later.')
        service_data = self.make_request(url=url, method='get')

        if blackout_message in service_data:
            return True
        else:
            return False
