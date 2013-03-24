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

import urllib, urllib2, xml.dom.minidom, json, cookielib, time, datetime, unicodedata

class MLSLive:

    def __init__(self):
        """
        Initialize the MLSLive class.
        """
        self.PUBLISH_POINT = 'http://live.mlssoccer.com/mlsmdl/servlets/publishpoint'
        self.LOGIN_PAGE = 'https://live.mlssoccer.com/mlsmdl/secure/login'
        self.GAMES_PAGE_PREFIX = 'http://mobile.cdn.mlssoccer.com/iphone/v5/prod/games_for_week_'
        self.GAMES_PAGE_SUFFIX = '.js'

        # Video channel information 
        self.CHANNELS_PAGE = 'http://mobile.cdn.mlssoccer.com/iphone/v5/prod/channels.js'
        self.CHANNEL_PREFIX = 'http://mobile.cdn.mlssoccer.com/iphone/v5/prod/channel_'
        self.CHANNEL_SUFFIX = '.js'

        # Odd, but the year is still 2011 -- I expect this will change in the future
        self.GAME_PREFIX = 'http://mls.cdnak.neulion.com/mobile/feeds/game/2011/'
        self.GAME_SUFFIX = '_ced.xml'

        self.TEAM_PAGE = 'http://mobile.cdn.mlssoccer.com/iphone/v5/prod/teams_2013.js'

        # resolution for images
        self.RES = '560x320'


    def login(self, username, password):
        """
        Login to the MLS Live streaming service.
        
        @param username: the user name to log in with
        @param password: the password to log in with.
        @return: True if authentication is successful, otherwise, False.
        """

        # setup the login values        
        values = { 'username' : username,
                   'password' : password }
        
        self.jar = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.jar))
        try:
            resp = opener.open(self.LOGIN_PAGE, urllib.urlencode(values))
        except:
            print "Unable to login"
            return False

        resp_xml = resp.read()
        dom = xml.dom.minidom.parseString(resp_xml)
        
        result_node = dom.getElementsByTagName('result')[0]
        code_node = result_node.getElementsByTagName('code')[0]
        
        if code_node.firstChild.nodeValue == 'loginsuccess':
            return True
        
        return False

    def getMonday(self, week_offset):
        today = datetime.date.today()
        monday = today + datetime.timedelta(days=-today.weekday(), weeks=week_offset)
        return monday


    def getWeeks(self):
        week_offset = 0
        week_found = True
        weeks = {}

        # work backwards through the weeks as long as there are games
        while week_found:
            games = self.getGames(week_offset)
            if len(games) > 0:
                weeks[week_offset] = self.getMonday(week_offset).strftime("%B %d, %Y")
                week_offset = week_offset - 1
            else:
                week_found = False

        # return the weeks
        return weeks


    def getGamesURI(self, week_offset): 
        monday = self.getMonday(week_offset)
        monday_str = monday.strftime("%Y-%m-%d")
        return self.GAMES_PAGE_PREFIX + monday_str + self.GAMES_PAGE_SUFFIX


    def getGames(self, week_offset):
        """
        Get the list of games.
        
        @param week_offset the number of weeks to offset from the previous
                           monday.
        @return json game data

        The list returned will contain dictionaries, each of which containing
        game details. The details are as follows:
        - homeTeamScore
        - visitorTeamScore
        - gameID
        - siteName (eg: "PPL Park", the nicest park in the league IMO)
        - television (eg: "MLS LIVE", "NBCSN", "ESPN2"
        - visitorTeamID
        - homeTeamID
        - gameDateTime (eg: "20130302T210000+0000")
        - competitionID (not sure what that does)
        - homeTeamName (pretty home team name)
        - gameStatus ("FINAL","UPCOMING", "LIVE - 50'"
        - visitorTeamName (pretty vistor team name)
        """
        games_url = self.getGamesURI(week_offset)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.jar))
        try:
            resp = opener.open(games_url)
        except:
            print "Unable to load game list."
            return None

        json_data = resp.read()

        games = json.loads(json_data)['games']

        return games


    def getTeams(self):
        """
        Get the list of teams from the web-service
        @return json team data
        """
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.jar))
        try:
            resp = opener.open(self.TEAM_PAGE)
        except:
            print "Unable to load game list."
            return None

        json_data = resp.read()

        return json.loads(json_data)['teams']


    def getTeamAbbr(self, teams, id):
        """
        Get the team abbreviation for a particular ID.
        @return the team abbreviation
        """
        for team in teams:
            if str(team['teamID']) == str(id):
                return team['abbr']
        return  None


    def getGameDateTimeStr(self, game_date_time):
        """
        Convert the date time stamp from GMT to local time
        @param game_date_time the game time (in GMT)
        @return a string containing the local game date and time.
        """

        # We know the GMT offset is 0, so just get rid of the trailing offset
        time_parts = game_date_time.split('+')
        game_t = time.strptime(time_parts[0], "%Y%m%dT%H%M%S")
        game_dt = datetime.datetime.fromtimestamp(time.mktime(game_t))

        # get the different between now and utc
        td = datetime.datetime.utcnow() - datetime.datetime.now()

        # subtract that difference from the game time (to put it into local gime)
        game_dt = game_dt - td

        # return a nice string
        return game_dt.strftime("%m/%d %H:%M")


    def isGameLive(self, game):
        """
        Determine if a game is live.
        @param game the game data dictionary
        @return true if the game is live, otherwise, false
        """
        if (game['gameStatus'][:4] == 'LIVE') or (game['gameStatus'][:4] == 'HALF'):
            return True
        return False


    def isGameUpcoming(self, game):
        """
        Determine if a game is upcoming
        @return true if the game is still upcoming, otherwise, false
        """
        if game['gameStatus'][:8] == 'UPCOMING':
            return True
        return False


    def adjustArchiveString(self, title, archive_type):
        """
        For archived games the title needs some adjustment to point out what the
        archive is (eg: highlights, condensed, full replay)
        @param title the match title
        @param archive_type the type of archive.
        @return the adjusted title
        """
        new_title = title.split('(')[0]
        return new_title + '(' + archive_type.title().replace('_', ' ') + ')';


    def getGameString(self, game, separator):
        """
        Get the game title string
        @param game the game data dictionary
        @param separator string containing the word to separate the home and
                         away side (eg "at")
        @return the game title
        """
        game_str = game['visitorTeamName'] + " " + separator + " " + \
                   game['homeTeamName']

        if game['gameStatus'] == 'FINAL' or game['gameStatus'][:4] == 'LIVE':
            game_str += ' (' + game['gameStatus'].title() + ')'
        else:
            game_str += ' (' + self.getGameDateTimeStr(game['gameDateTime']) + ')'

        return game_str


    def getGameXML(self, game_id):
        """
        Fetch the game XML configuration
        @param game_id the game id
        @return a string containing the game XML data
        """
        game_xml_url = self.GAME_PREFIX + game_id + self.GAME_SUFFIX
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.jar))
        try:
            resp = opener.open(game_xml_url)
        except:
            print "Unable to get game XML configuration"
            return ""

        game_xml = resp.read()
        return game_xml


    def getFinalStreams(self, game_id):
        """
        Get the streams for matches that have ended.
        @param game_id the game id
        @return a dictionary containing the streams with keys for the stream
                type
        """
        game_xml = self.getGameXML(game_id)
        try:
            dom = xml.dom.minidom.parseString(game_xml)
        except:
            return None

        rss_node = dom.getElementsByTagName('rss')[0]
        chan_node = rss_node.getElementsByTagName('channel')[0]
        games = {}
        for item in chan_node.getElementsByTagName('item'):
            # get the game type
            game_type = item.getElementsByTagName('nl:type')[0].firstChild.nodeValue

            # get the group list and make sure its valid
            group_list = item.getElementsByTagName('media:group')
            if group_list == None or len(group_list) == 0:
                continue

            # get the content node and then the URL
            content_node = group_list[0].getElementsByTagName('media:content')[0]
            games[game_type] = content_node.getAttribute('url')

        return games


    def getGameLiveStream(self, game_id):
        """
        Get the game streams. This method will parse the game XML for the
        HLS playlist, and then parse that playlist for the different bitrate
        streams.

        @param game_id the game id
        @return the live stream
        """
        values = { 'type' : 'game',
                   'gt' : 'live',
                   'id' : game_id }

        uri = self.PUBLISH_POINT + '?' + urllib.urlencode(values)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.jar))
        # set the user agent to get the HLS stream
        opener.addheaders = [('User-agent', 'Sony')]
        try:
            resp = opener.open(uri)
        except:
            print "Unable to get live game XML configuration"
            return ""

        game_xml = resp.read()

        try:
            dom = xml.dom.minidom.parseString(game_xml)
        except:
            print "Unable to parse game XML for game " + game_id
            return ""

        result_node = dom.getElementsByTagName('result')[0]
        path_node = result_node.getElementsByTagName('path')[0]
        stream_url = path_node.firstChild.nodeValue

        return stream_url.split('?')[0]


    def getVideoChannels(self):
        """
        Get the list of video channels
        """
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.jar))
        try:
            resp = opener.open(self.CHANNELS_PAGE)
        except:
            print "Unable to load channels list."
            return None

        json_data = resp.read()

        return json.loads(json_data)['channels']

    def getChannelImage(self, channel):
        """
        Get the channel image URL
        """
        return channel['tile'].replace('[res]', self.RES)


    def getChannelVideos(self, channel_id):
        """
        Get the list of videos for the channel
        """
        url = self.CHANNEL_PREFIX + channel_id + self.CHANNEL_SUFFIX
        print url
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.jar))
        try:
            resp = opener.open(url)
        except:
            print "Unable to load channel video list."
            return None

        json_data = resp.read()

        return json.loads(json_data)['items']
