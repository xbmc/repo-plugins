'''
@author: Micah Galizia <micahgalizia@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os, re, urllib, urllib2, json, cookielib, datetime, uuid
from urlparse import urlparse


class MLSLive:

    def __init__(self):
        """
        Initialize the MLSLive class.
        """

        self.BEARER = 'Bearer 94vDO2IN1y963U8NO9Jw8omaG5q94Rht1ERjD6AEnKna90x04lf5Ty6brFsbYs8V'
        self.BASIC = 'Basic bWF0Y2hkYXlfYW5kcm9pZDpKN3Q4dzhiRUJUYVVHWDJMZzJaTlZ5WXk='
        self.USER_AGENT = 'BAMSDK/1.0.4 (mlsoccer-F73A6101; 1.0.0; google; handset) google Nexus 9 (N4F26Q; Linux; 7.1.1; API 25)'
        self.TOKEN_PAGE = 'https://global-api.live-svcs.mlssoccer.com/token'
        self.LOGIN_PAGE = 'https://global-api.live-svcs.mlssoccer.com/v2/user/identity'
        self.CLUBS_PAGE = 'https://api.mlsdigital.net/www.mlssoccer.com/clubs?'
        self.MATCHES_PAGE = 'https://api.mlsdigital.net/www.mlssoccer.com/matches?'
        self.GRAPHGL_PAGE = 'https://cops-prod.live-svcs.mlssoccer.com/graphql'
        self.GRAPHGL_QUERY= '?query={{%0A%20%20Schedule(gamePks:%20%22{0}%22)%20{{%0A%20%20%20%20dates%20{{%0A%20%20%20%20%20%20games%20{{%0A%20%20%20%20%20%20%20%20media%20{{%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20videos%20{{%0A%20%20%20%20%20%20%20%20%20%20%20%20contentId%0A%20%20%20%20%20%20%20%20%20%20%20%20runTime%0A%20%20%20%20%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20%20%20%20%20...on%20Video%20{{%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20media%20{{%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20mediaId%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20mediaState%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20playbackUrls%20{{%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20href%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20}}%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20}}%0A%20%20%20%20%20%20%20%20%20%20%20%20}}%0A%20%20%20%20%20%20%20%20%20%20%20%20...on%20Airing%20{{%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20mediaId%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20eventId%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20linear%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20playbackUrls%20{{%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20href%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20}}%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20mediaConfig%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20{{%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20state%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20productType%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20type%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20}}%0A%20%20%20%20%20%20%20%20%20%20%20%20}}%0A%20%20%20%20%20%20%20%20%20%20}}%0A%20%20%20%20%20%20%20%20}}%0A%20%20%20%20%20%20}}%0A%20%20%20%20}}%0A%20%20}}%0A}}'

    def total_seconds(self, dt):
        # Keep backward compatibility with Python 2.6 which doesn't have
        # this method
        if hasattr(dt, 'total_seconds'):
            return dt.total_seconds()
        else:
            return (dt.microseconds + (dt.seconds + dt.days * 24 * 3600) * 10**6) / 10**6
 

    def getAddonFolder(self):
        try:
            import xbmc, xbmcaddon
            return xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        except:
            return os.getcwd()


    def getSettingsFile(self):
        return os.path.join(self.getAddonFolder(), 'settings.json') 

    def getCookieFile(self):
        return os.path.join(self.getAddonFolder(), 'cookies.lwp')


    def createCookieJar(self):
        cookie_file = self.getCookieFile()
        return cookielib.LWPCookieJar(cookie_file)


    def loadCookieJar(self):
        jar = cookielib.LWPCookieJar()
        cookie_file = self.getCookieFile()
        jar.load(cookie_file,ignore_discard=True)
        return jar

    def postToken(self, xff, token=None):
        """
        Get the token from MLBAM for MLS soccer.
        @param token if specified, the toke to use for token authentication
        """
        jar = self.createCookieJar()
        #urllib2.HTTPHandler(debuglevel=1),urllib2.HTTPSHandler(debuglevel=1)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('Authorization', self.BEARER),
                             ('User-Agent', urllib.quote(self.USER_AGENT))]
        if not xff == None:
            opener.addheaders.append(('X-Forwarded-For', xff))

        values = { 'platform' : 'android',
                   'latitude' : '61.172110800000000',
                   'longitude' : '149.83626080000000',
                   'grant_type' : 'client_credentials',
                   'token' : 'BAMSDK_mlsoccer-F73A6101_prod_'}

        if token == None:
            values['token'] += str(uuid.uuid4())
        else:
            values['grant_type'] = 'urn:mlbam:params:oauth:grant_type:token'
            values['token'] = token

        try:
            resp = opener.open(self.TOKEN_PAGE, urllib.urlencode(values))
        except:
            print "Unable to login"
            return None
        jar.save(filename=self.getCookieFile(), ignore_discard=True, ignore_expires=True)

        resp_json = resp.read()
        jsobj = json.loads(resp_json)

        return jsobj


    def postIdentity(self, xff, username, password, token):
        """
        Post the user credentials to the identiy service.
        @param username The username
        @param password The password
        @param token The token generated from the token service
        """
        js_obj = {'email': {'address': username},
                  'password':{'value': password},
                  'type':'email-password'}
        js_data = json.dumps(js_obj)

        jar = self.createCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        rq_headers = {'Authorization': token,
                      'User-Agent': self.USER_AGENT,
                      'Content-Type': 'application/json',
                      'Accept': 'application/vnd.identity-service+json; version=1.0',
                      'Content-Length': len(js_data)}
        if not xff == None:
            rq_headers['X-Forwarded-For'] = xff

        
        req = urllib2.Request(self.LOGIN_PAGE, data=js_data, headers=rq_headers)
        

        try:
            resp = opener.open(req)
        except:
            print "Unable to POST identify"
            return False
        jar.save(filename=self.getCookieFile(), ignore_discard=True, ignore_expires=True)

        js_obj = json.loads(resp.read())
        return js_obj['code']


    def getMatches(self, start, end, xff):
        """
        Get the matches within a time frame
        """
        jar = self.createCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('accept-version', '2.0.1'),
                             ('Authorization', self.BASIC)]
        if not xff == None:
            opener.addheaders.append(('X-Forwarded-For', xff))

        url = self.MATCHES_PAGE + urllib.urlencode({ 'startdate' : start, 'enddate' : end })
        try:
            resp = opener.open(url)
        except:
            print "Unable to get matches"
            return None
        jar.save(filename=self.getCookieFile(), ignore_discard=True, ignore_expires=True)
        js_str = resp.read()
        js_obj = json.loads(js_str)

        return js_obj


    def getClubs(self, xff = None):
        """
        Get the list of clubs
        """
        jar = self.createCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('accept-version', '2.0.1'),
                             ('Authorization', self.BASIC)]
        if not xff == None:
            opener.addheaders.append(('X-Forwarded-For', xff))

        url = self.CLUBS_PAGE + urllib.urlencode({ 'ttl' : 7200, 'pagesize' : 300 })
        try:
            resp = opener.open(url)
        except:
            print "Unable to get matches"
            return None
        jar.save(filename=self.getCookieFile(), ignore_discard=True, ignore_expires=True)
        js_str = resp.read()
        js_obj = json.loads(js_str)

        return js_obj


    def postGraphql(self, opta_id, token, xff):
        query = self.GRAPHGL_QUERY.format(opta_id)
        uri = self.GRAPHGL_PAGE + query

        jar = self.createCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('Authorization', token),
                             ('Accept', 'application/json'),
                             ('User-Agent', urllib.quote(self.USER_AGENT))]
        if not xff == None:
            opener.addheaders.append(('X-Forwarded-For', xff))

        try:
            resp = opener.open(uri)
        except:
            print "Unable to get stream metadata"
            return False
        jar.save(filename=self.getCookieFile(), ignore_discard=True, ignore_expires=True)

        js_str = resp.read()
        return json.loads(js_str)


    def getEvents(self, uri, token, xff):
        jar = self.createCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('Authorization', token),
                             ('Accept', 'application/vnd.media-service+json; version=1'),
                             ('x-mlbam-player-adapter', 'exoplayer-2.0.x'),
                             ('User-Agent', urllib.quote(self.USER_AGENT))]
        if not xff == None:
            opener.addheaders.append(('X-Forwarded-For', xff))

        try:
            resp = opener.open(uri)
        except:
            print "Unable to get stream details"
            return None
        jar.save(filename=self.getCookieFile(), ignore_discard=True, ignore_expires=True)

        js_str = resp.read()
        return json.loads(js_str)


    def login(self, username, password, xff = None):
        """
        Login to the MLS Live streaming service.
        
        @param username: the user name to log in with
        @param password: the password to log in with.
        @return: True if authentication is successful, otherwise, False.
        """

        token = self.postToken(xff)
        if token == None:
            print "No token returned"
            return None
        token = token['access_token']
        if token == None:
            print "Unable to get token."
            return None

        code = self.postIdentity(xff, username, password, token)
        if code == None:
            print "Unable to get code from identify"
            return None

        js_obj = self.postToken(xff, code)

        try:
            fp = open(self.getSettingsFile(), 'r')
            settings = json.load(fp)
            fp.close()

            # update the auth settings
            for key in js_obj.keys():
                settings[key] = js_obj[key]
            js_obj=settings
        except:
            pass

        # store of the tokens
        fp = open(self.getSettingsFile(), 'w')
        json.dump(js_obj, fp)
        fp.close()

        return True


    def getWeekRange(self, dt):
        """
        Get the epoch values of monday morning at midnight to the following
        monday at 11:59:59PM
        """
        #roll back to the first day of the week (monday)
        start = dt - datetime.timedelta(days=dt.weekday(), hours=dt.hour,
                                 minutes=dt.minute, seconds=dt.second)
        end = start + datetime.timedelta(days=8, seconds=-1)
        epoch = datetime.datetime(1970,1,1)

        return (int(self.total_seconds(start - epoch)),
                int(self.total_seconds(end - epoch)))


    def getGames(self, dt = None, xff = None):
        """
        Get the list of games.

        @return json game data
        """
        # if no datetime specified just assume now
        if dt == None:
            dt = datetime.datetime.now()

        week_range = self.getWeekRange(dt)
        return self.getMatches(week_range[0], week_range[1], xff)


    def getTitle(self, game, fmt):
        """
        Get the title string
        @param game the game json
        @param separator text to separate the teams
        """
        return fmt.format(game['home']['name']['short'],
                          game['away']['name']['short'])


    def getFullTitle(self, game, fmt):
        """
        Get the title string
        @param game the game json
        @param separator text to separate the teams
        """
        return fmt.format(game['home']['name']['full'],
                          game['away']['name']['full'])


    def getDescription(self, game, fmt, def_blackouts, def_venue):
        blackouts = def_blackouts
        if not game['blackouts'] == None:
            blackouts = ''
            for blackout in game['blackouts']:
                blackouts += blackout + ', '

        venue = def_venue
        if game['venue'] != None:
            venue = game['venue']['name']

        return fmt.format(game['home']['name']['full'],
                          game['away']['name']['full'],
                          venue, blackouts[0:-2])


    def getGameString(self, game, separator):
        """
        Get the game title string
        @param game the game data dictionary
        @param separator string containing the word to separate the home and
                         away side (eg "at")
        @return the game title
        """

        game_dt = datetime.datetime.fromtimestamp(game['date'])
        dt_str = game_dt.strftime("%m/%d %H:%M")
        title = self.getTitle(game, separator)
        game_str = '{0} [I]{1}[/I]  [B]{2}[/B]'.format(title, game['period'],
                                                       dt_str) 

        return game_str.encode('utf-8').strip()


    def getImage(self, game, fav = None):
        """
        Get the team image for the game. If the favorite is set and they are one
        of the teams in the game, their image will be used, otherwise, the home
        team's image will be used.

        @param game The game
        @param fav the [optional] favorite team
        @return the game image or None if something went wrong.
        """

        # use the home team unless the away team if the favorite
        team = game['home']
        if fav and game['away']['id'] == fav:
            team = game['away']

        if 'logo' in team:
            if 'original' in team['logo']:
                return team['logo']['original']

        return None


    def parsePlaylist(self, uri, token, xff):
        """
        Parse the playlist and split it by bitrate.
        """
        streams = {}
        jar = self.createCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('Authorization', token),
                             ('User-Agent', urllib.quote(self.USER_AGENT))]
        if not xff == None:
            opener.addheaders.append(('X-Forwarded-For', xff))

        try:
            resp = opener.open(uri)
        except:
            print "Unable to get stream metadata"
            return False
        jar.save(filename=self.getCookieFile(), ignore_discard=True, ignore_expires=True)

        m3u8 = resp.read();

        url = urlparse(uri)
        prefix = url.scheme + "://" + url.netloc + url.path[:url.path.rfind('/')+1]
        suffix = '?' + url.params + url.query + url.fragment
        lines = m3u8.split('\n')

        bandwidth = ""
        for line in lines:
            if line == "#EXTM3U":
                continue
            if line[:17] == '#EXT-X-STREAM-INF':
                bandwidth = re.search(".*,?BANDWIDTH\=(.*?),.*", line)
                if bandwidth:
                    bandwidth = bandwidth.group(1)
                else:
                    print "Unable to parse bandwidth"
            elif line[-5:] == ".m3u8":
                stream = '{0}{1}|User-Agent={2}&Authorization={3}'.format(prefix,
                            line, urllib.quote(self.USER_AGENT), token)
                if not xff == None:
                    stream += '&X-Forwarded-For={0}'.format(urllib.quote(xff))
                streams[bandwidth] = stream

        return streams


    def getStreams(self, opta_id, xff=None):
        """
        Get the stream
        @param opta_id the optaId from the games list
        @TODO check expiry on the token
        """
        try:
            fp = open(self.getSettingsFile(), 'r')
            settings = json.load(fp)
            token = settings['access_token']
            fp.close()
        except:
            print "Unable to load settings so couldn't get access_token"
            return None


        js_obj = self.postGraphql(opta_id, token, xff)
        if js_obj == None:
            return None
        dates = js_obj['data']['Schedule']['dates']
        if len(dates) == 0:
            print "Unable to load stream metadata. No dates"
            return None

        return dates[0]['games'][0]['media']


    def getStreamURIs(self, media, xff=None):
        try:
            fp = open(self.getSettingsFile(), 'r')
            settings = json.load(fp)
            token = settings['access_token']
            fp.close()
        except:
            print "Unable to load settings so couldn't get access_token"
            return None
        videos = media['videos'][0]
        if 'media' in videos:
            videos = videos['media'][0]
        print videos
        uri = videos['playbackUrls'][0]['href']
        uri = uri.replace('{scenario}', 'android')

        js_obj = self.getEvents(uri, token, xff)
        if js_obj == None:
            return None
        playlist = js_obj['stream']['complete']

        streams = self.parsePlaylist(playlist, token, xff)

        return streams

    def setFavoriteClub(self, id):
        try:
            fp = open(self.getSettingsFile(), 'r')
            settings = json.load(fp)
            fp.close()
        except:
            settings = {}

        settings['id'] = id;
        fp = open(self.getSettingsFile(), 'w')
        json.dump(settings, fp)
        fp.close()


    def getFavoriteClub(self):
        try:
            fp = open(self.getSettingsFile(), 'r')
            settings = json.load(fp)
            fp.close()
        except:
            print "Unable to load settings so couldn't get favorite club"
            return None

        # if the id was specified return it
        if 'id' in settings.keys():
            return settings['id']

        return None
