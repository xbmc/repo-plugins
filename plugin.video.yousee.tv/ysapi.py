"""
https://docs.google.com/document/d/1_rs5BXklnLqGS6g6eAjevVHsPafv4PXDCi_dAM2b7G0/edit?pli=1
"""

import cookielib
import urllib2
import simplejson

API_URL = 'http://api.yousee.tv/rest'
API_KEY = 'HCN2BMuByjWnrBF4rUncEfFBMXDumku7nfT3CMnn'

AREA_LIVETV = 'livetv'
AREA_MOVIE = 'movie'
AREA_PLAY = 'play'
AREA_USERS = 'users'
AREA_TVGUIDE = 'tvguide'

class YouSeeApi(object):
    COOKIE_JAR = cookielib.LWPCookieJar()

    def __init__(self):
        print 'YouSeeApi.__init__'
        print self.COOKIE_JAR
        urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(self.COOKIE_JAR)))

    def _invoke(self, area, function, params = None):
        url = API_URL + '/' + area + '/' + function
        if params:
            for key, value in params.items():
                url += '/' + key + '/' + str(value)
        url += '/format/json'

        print 'Invoking URL: %s' % url

        try:
            r = urllib2.Request(url, headers = {'X-API-KEY' : API_KEY})
            u = urllib2.urlopen(r)
            json = u.read()
            u.close()
        except urllib2.HTTPError, error:
            json = error.read()

        try:
            return simplejson.loads(json)
        except simplejson.JSONDecodeError, error:
            return None

class YouSeeLiveTVApi(YouSeeApi):
    def popularChannels(self):
        """
        Returns list of channels sorted by popularity.
        Based on live viewing data from yousee.tv
        """
        return self._invoke(AREA_LIVETV, 'popularchannels')

    def allowedChannels(self):
        """
        Returns list of channels the requesting IP is allowed to stream.
        """
        return self._invoke(AREA_LIVETV, 'allowed_channels')

    def suggestedChannels(self):
        """
        Returns list of channels that should be presented to the user. NOTE: this is not the list of allowed channels.
        A non-yousee bredbaand user will get a list of channels from "Grundpakken".
        """
        return self._invoke(AREA_LIVETV, 'suggested_channels')


    def streamUrl(self, channelId, client = 'xbmc'):
        """
        Returns absolute streaming URL for channel.
        Channel rights are based on client ip address.

        @param channelId: Unique ID of channel (e.g. 1 for DR1)
        @type channelId: int
        @param client: client identifier. Handset or platform. Used to determine best stream.
        @type client: str
        """
        json = self._invoke(AREA_LIVETV, 'streamurl', {
            'channel_id' : channelId,
            'client' : client
        })

        return json

class YouSeeMovieApi(YouSeeApi):
    def themes(self):
        """
        Returns all active themes (themes with one or more movies attached)
        """
        return self._invoke(AREA_MOVIE, 'themes')

    def genres(self):
        """
        Returns all active genres (genres with one or more movies attached)
        """
        return self._invoke(AREA_MOVIE, 'genres')

    def search(self, query):
        """
        Returns movies matching search query.
        Searches are done on title, cast and director.
        If query is less than 4 chars a LIKE search will be made, and results returned ordered by title. If query is 4 chars or more a MATCH AGAINST search will be made, and results returned ordered by score.
        @param query:
        @type query: string
        @return:
        """
        return self._invoke(AREA_MOVIE, 'search', {
            'query' : query
        })

    def moviesInGenre(self, genre):
        """
        Returns movies in genre.
        @param genre: Genre
        """
        return self._invoke(AREA_MOVIE, 'movies_in_genre', {
            'genre' : genre
        })

    def moviesInTheme(self, theme):
        """
        Returns movies in theme.
        @param theme: Theme
        """
        return self._invoke(AREA_MOVIE, 'movies_in_theme', {
            'theme' : theme
        })

class YouSeeTVGuideApi(YouSeeApi):
    def channels(self):
        """
        Returns complete channel list ordered in channel packages.

        Note: the channel package "Mine Kanaler" contains the default channels a user should have in her favorites, until overwritten by the user herself.
        """
        return self._invoke(AREA_TVGUIDE, 'channels')

    def categories(self):
        """
        Returns complete list of categories
        """
        return self._invoke(AREA_TVGUIDE, 'categories')

    def programs(self, channelId, offset = 0):
         """
         Returns program list
         """
         return self._invoke(AREA_TVGUIDE, 'programs', {
             'channel_id' : channelId,
             'offset' : offset
         })

class YouSeePlayApi(YouSeeApi):
    def album(self, id):
        return self._invoke(AREA_PLAY, 'album', {
            'id' : id
        })

class YouSeeUsersApi(YouSeeApi):
    def login(self, username, password):
        return self._invoke(AREA_USERS, 'login', {
            'username' : username,
            'password' : password
        })

    def transactions(self):
        return self._invoke(AREA_USERS, 'transactions')

if __name__ == '__main__':
    api = YouSeeLiveTVApi()
#    json = api.allowedChannels()
    json = api.streamUrl(1)

#    api = YouSeeTVGuideApi()
#    json = api.programs(1)

#    api = YouSeeMovieApi()
#    json= api.moviesInGenre('action')['movies'][1]

    s = simplejson.dumps(json, sort_keys=True, indent='    ')
    print '\n'.join([l.rstrip() for l in  s.splitlines()])

