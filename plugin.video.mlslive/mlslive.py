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

import urllib, urllib2, xml.dom.minidom, cookielib, time, datetime
import _strptime


class MLSLive:

    def __init__(self):
        """
        Initialize the MLSLive class.
        """

        self.CED_CONFIG = 'http://static.mlsdigital.net/mobile/v20/config.json'
        self.PUBLISH_POINT = 'http://live.mlssoccer.com/mlsmdl/servlets/publishpoint'
        self.LOGIN_PAGE = 'https://live.mlssoccer.com/mlsmdl/secure/login'
        self.GAMES_PAGE_PREFIX = 'http://mobile.cdn.mlssoccer.com/iphone/v5/prod/games_for_week_'

        self.GAME_PREFIX = 'http://live.mlssoccer.com/mlsmdl/schedule?'

        # resolution for images
        self.RES = '560x320'
        self.timeOffset = None


    def getCookieFile(self):
        import os
        try:
            import xbmc, xbmcaddon
            base = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        except:
            base = os.getcwd()
        return os.path.join(base, 'cookies.lwp')


    def createCookieJar(self):
        cookie_file = self.getCookieFile()
        return cookielib.LWPCookieJar(cookie_file)


    def loadCookieJar(self):
        jar = cookielib.LWPCookieJar()
        cookie_file = self.getCookieFile()
        jar.load(cookie_file,ignore_discard=True)
        return jar

    
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

        jar = self.createCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))#,
        #urllib2.HTTPSHandler(debuglevel=1))
        try:
            resp = opener.open(self.LOGIN_PAGE, urllib.urlencode(values))
        except:
            print "Unable to login"
            return False
        jar.save(ignore_discard=True)

        resp_xml = resp.read()
        dom = xml.dom.minidom.parseString(resp_xml)

        result_node = dom.getElementsByTagName('result')[0]
        code_node = result_node.getElementsByTagName('code')[0]
        
        if code_node.firstChild.nodeValue == 'loginsuccess':
            return True

        return False


    def getTimeOffset(self, games_xml):

        # there are no games in the first month, but it still returns the time
        now = datetime.datetime.now()

        # parse the xml for the server time
        dom = xml.dom.minidom.parseString(games_xml)
        result_node = dom.getElementsByTagName('result')[0]
        cur_date_node = result_node.getElementsByTagName('currentDate')[0]
        cur_date = cur_date_node.firstChild.nodeValue

        try:
            t = time.strptime(cur_date, '%a %b %d %H:%M:%S EST %Y')
            server = datetime.datetime.fromtimestamp(time.mktime(t))
        except ValueError:
            print "ERROR: Unable to get server time"
            return None

        # calculate the time delta between the server and the local time zone
        # accommodating for network delay
        td = server - now
        seconds = td.seconds
        modsecs = seconds % 100
        if modsecs < 100:
            seconds += (100 - modsecs)
        self.timeOffset = datetime.timedelta(days = td.days, seconds = seconds)

        return None


    def getGamesXML(self, month, year = '2015'):

        values = {'format' : 'xml',
                  'year' : year,
                  'month' : month,
                  'checksubscription' : 'true' }

        jar = self.loadCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        try:
            resp = opener.open(self.GAME_PREFIX, urllib.urlencode(values))
        except:
            print "Unable get games xml"
            return None
        jar.save(filename=self.getCookieFile(), ignore_discard=True)

        xml_data = resp.read()

        return xml_data


    def getGames(self, month):
        """
        Get the list of games.
        
        @param games_url the url of the weeks games
        @return json game data
        """

        games_xml = self.getGamesXML(month)
        if games_xml == None:
            return None

        self.getTimeOffset(games_xml)

        dom = xml.dom.minidom.parseString(games_xml)

        result_node = dom.getElementsByTagName('result')[0]
        games_node = result_node.getElementsByTagName('games')[0]

        games = []
        for game_node in games_node.getElementsByTagName('game'):
            game = {}

            # parse each element we'll need
            for str in ['gid', 'type', 'id', 'gameTimeGMT', 'awayTeam',
                        'homeTeam', 'awayTeamName', 'homeTeamName', 'programId',
                        'gs', 'result', 'isLive']:
                nodes = game_node.getElementsByTagName(str)
                if len(nodes) > 0:
                    game[str] = nodes[0].firstChild.nodeValue

            games.append(game)

        return games

    def getGameDateTimeStr(self, game_date_time):
        """
        Convert the date time stamp from GMT to local time
        @param game_date_time the game time (in GMT)
        @return a string containing the local game date and time.
        """

        try:
            game_t = time.strptime(game_date_time, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return None

        game = datetime.datetime.fromtimestamp(time.mktime(game_t))

        # attempt to calculate the local time
        if not self.timeOffset == None:
            game -= self.timeOffset

        # return a nice string
        return game.strftime("%m/%d %H:%M")


    def getGameString(self, game, separator):
        """
        Get the game title string
        @param game the game data dictionary
        @param separator string containing the word to separate the home and
                         away side (eg "at")
        @return the game title
        """

        # create the base string
        game_str = game['awayTeamName'] + ' ' + separator + ' ' + \
                   game['homeTeamName']

        # add the result
        if 'result' in game.keys():
            if game['result'] == 'F':
                game_str += ' ([B]Final[/B])'
                return game_str.encode('utf-8').strip()

        if 'isLive' in game.keys():
            if game['isLive'] == 'true':
                game_str = '[I]' + game_str + '[/I]'

        # if we can get the date/time of the game add it
        dt = self.getGameDateTimeStr(game['gameTimeGMT'])
        if not dt == None:
            game_str += ' ([B]' + dt + '[/B])'

        return game_str.encode('utf-8').strip()


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

    def getStream(self, adaptive):

        return None


    def getGameLiveStream(self, game_id, condensed = False):
        """
        Get the game streams. This method will parse the game XML for the
        HLS playlist, and then parse that playlist for the different bitrate
        streams.

        @param game_id the game id
        @return the live stream
        """
        values = { 'type' : 'game',
                   'gt' : 'condensed' if condensed else 'live',
                   'id' : game_id,
                   'nt' : '1'}

        uri = self.PUBLISH_POINT + '?' + urllib.urlencode(values)
        jar = self.loadCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        # set the user agent to get the HLS stream
        opener.addheaders = [('User-Agent', urllib.quote('PS3Application libhttp/4.5.5-000 (CellOS)'))]

        try:
            resp = opener.open(uri)
        except urllib2.URLError as error:
            print 'ERROR: ' + error.reason + '(' + uri + ')'
            return ""

        jar.save(filename=self.getCookieFile(), ignore_discard=True)
        game_xml = resp.read()

        try:
            dom = xml.dom.minidom.parseString(game_xml)
        except:
            print "Unable to parse game XML for game " + game_id
            return ""

        result_node = dom.getElementsByTagName('result')[0]
        path_node = result_node.getElementsByTagName('path')[0]
        stream_url = path_node.firstChild.nodeValue

        return stream_url
