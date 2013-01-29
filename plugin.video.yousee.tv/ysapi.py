#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
# https://docs.google.com/document/d/1_rs5BXklnLqGS6g6eAjevVHsPafv4PXDCi_dAM2b7G0/edit?pli=1
#
import cookielib
import urllib
import urllib2
import simplejson
import os
import re

import xbmc

API_URL = 'http://api.yousee.tv/rest'
API_KEY = 'HCN2BMuByjWnrBF4rUncEfFBMXDumku7nfT3CMnn'

AREA_LIVETV = 'livetv'
AREA_MOVIE = 'movie'
AREA_PLAY = 'play'
AREA_USERS = 'users'
AREA_TVGUIDE = 'tvguide'
AREA_SYSTEM = 'system'
AREA_CONTENT = 'content'
AREA_ARCHIVE = 'archive'
AREA_PLAY = 'play'

METHOD_GET = 'get'
METHOD_POST = 'post'


class YouSeeApiException(Exception):
    pass


class YouSeeApi(object):
    COOKIE_JAR = cookielib.LWPCookieJar()
    COOKIES_LWP = 'cookies.lwp'

    def __init__(self, dataPath):
        xbmc.log('YouSeeApi.__init__(dataPath = %s)' % dataPath, xbmc.LOGDEBUG)
        self.cookieFile = os.path.join(dataPath, self.COOKIES_LWP)
        if os.path.isfile(self.cookieFile):
            try:
                self.COOKIE_JAR.load(self.cookieFile, ignore_discard=True, ignore_expires=True)
            except cookielib.LoadError:
                pass  # ignore

        urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(self.COOKIE_JAR)))

    def _invoke(self, area, function, params=None, method=METHOD_GET):
        url = API_URL + '/' + area + '/' + function
        if method == METHOD_GET and params:
            for key, value in params.items():
                url += '/' + key + '/' + str(value)
        url += '/format/json'

        xbmc.log('Invoking URL: %s' % re.sub('/password/([^/]+)/', '/password/****/', url), xbmc.LOGDEBUG)

        try:
            r = urllib2.Request(url, headers={'X-API-KEY': API_KEY})
            if method == METHOD_POST and params:
                xbmc.log("POST data: %s" % urllib.urlencode(params), xbmc.LOGDEBUG)
                r.add_data(urllib.urlencode(params))
            u = urllib2.urlopen(r)
            json = u.read()
            u.close()

            self.COOKIE_JAR.save(self.cookieFile, ignore_discard=True, ignore_expires=True)
        except urllib2.HTTPError, error:
            json = error.read()
        except Exception, ex:
            raise YouSeeApiException(ex)

        try:
            return simplejson.loads(json)
        except:
            return None


class YouSeeLiveTVApi(YouSeeApi):
    def channel(self, id):
        """
        Returns metadata for channel based on channel id.

        @param id: channel id
        @return:
        """
        return self._invoke(AREA_LIVETV, 'channel', {
            'id': id
        })

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

    def streamUrl(self, channelId, client='xbmc'):
        """
        Returns absolute streaming URL for channel.
        Channel rights are based on client ip address.

        @param channelId: Unique ID of channel (e.g. 1 for DR1)
        @type channelId: int
        @param client: client identifier. Handset or platform. Used to determine best stream.
        @type client: str
        """
        json = self._invoke(AREA_LIVETV, 'streamurl', {
            'channel_id': channelId,
            'client': client
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
            'query': query
        })

    def moviesInGenre(self, genre):
        """
        Returns movies in genre.
        @param genre: Genre
        """
        return self._invoke(AREA_MOVIE, 'movies_in_genre', {
            'genre': genre
        })

    def moviesInTheme(self, theme):
        """
        Returns movies in theme.
        @param theme: Theme
        """
        return self._invoke(AREA_MOVIE, 'movies_in_theme', {
            'theme': theme
        })

    def related(self, movie_id):
        """

        @param movie_id: can be both VODKa id and url-id
        @return: List of movies (see moviedata method for description of movie object)
        """
        return self._invoke(AREA_MOVIE, 'related', {
            'movie_id': movie_id
        })

    def supported_payment_methods(self, amount):
        """
        @param amount:
        @return: List of cards
        """
        return self._invoke(AREA_MOVIE, 'supported_payment_methods', {
            'amount': amount
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

    def programs(self, channelId, offset=0):
        """
         Returns program list
         """
        return self._invoke(AREA_TVGUIDE, 'programs', {
            'channel_id': channelId,
            'offset': offset
        })


class YouSeePlayApi(YouSeeApi):
    def album(self, id):
        return self._invoke(AREA_PLAY, 'album', {
            'id': id
        })


class YouSeeUsersApi(YouSeeApi):
    def login(self, username, password):
        return self._invoke(AREA_USERS, 'login', {
            'username': username,
            'password': password
        })

    def user(self, session_id):
        return self._invoke(AREA_USERS, 'user', {
            'yspro': session_id
        })

    def transactions(self):
        return self._invoke(AREA_USERS, 'transactions')

    def isYouSeeIP(self):
        return self._invoke(AREA_USERS, 'isyouseeip')


class YouSeeSystemApi(YouSeeApi):
    def supportmessage(self):
        return self._invoke(AREA_SYSTEM, 'supportmessage')


class YouSeeContentApi(YouSeeApi):
    def teasers(self, area):
        """
        Returns editorial teasers from YouSee. (see yousee.tv/film for reference)

        @param area: Teaser area (allowed area: movie)
        @return:
        """
        return self._invoke(AREA_CONTENT, 'teasers', {
            'area': area
        })


class YouSeeArchiveApi(YouSeeApi):
    def genres(self):
        return self._invoke(AREA_ARCHIVE, 'genres')

    def programs(self, channel_id=None, genre_id=None, tvdate=None):
        """
        Returns program list
        @param channel_id: (optional)
        @param genre_id: Genre ID (optional)
        @param tvdate: yyyy-mm-dd format (optional)
        @return:
        """
        params = dict()
        if channel_id:
            params['channel_id'] = channel_id
        if genre_id:
            params['genre_id'] = genre_id
        if tvdate:
            params['tvdate'] = tvdate

        return self._invoke(AREA_ARCHIVE, 'programs', params)

    def allowed_channels(self):
        return self._invoke(AREA_ARCHIVE, 'allowed_channels')

    def search(self, query, offset=None, limit=None):
        params = dict()
        params['query'] = query
        if offset:
            params['offset'] = offset
        if limit:
            params['limit'] = limit
        return self._invoke(AREA_ARCHIVE, 'search', params)

    def streamurl(self, epg_id, client='xbmc'):
        """

        @param epg_id: program_id
        @param client:
        @return:
        """
        return self._invoke(AREA_ARCHIVE, 'streamurl', {
            'epg_id': epg_id,
            'client': client
        })


class YouSeePlayApi(YouSeeApi):
    def search(self, query, limit=None, offset=None, startLetter=None):
        return self._invoke(AREA_PLAY, 'search', {
            'query': query.replace(' ', '+')
        })

    def usersession(self, externalPersonId, email):
        return self._invoke(AREA_PLAY, 'usersession', {
            'external_person_id': externalPersonId,
            'email': email
        })

    def streamUrl(self, trackId, userSession):
        return self._invoke(AREA_PLAY, 'streamurl', {
            'track_id': trackId,
            'usersession': userSession
        })


if __name__ == '__main__':
    api = YouSeeLiveTVApi('/tmp')
    json = api.allowedChannels()

    #    api = YouSeeTVGuideApi()
    #    json = api.programs(1)

    #    api = YouSeeMovieApi()
    #    json= api.moviesInGenre('action')['movies'][1]

    s = simplejson.dumps(json, sort_keys=True, indent='    ')
    print '\n'.join([l.rstrip() for l in s.splitlines()])

