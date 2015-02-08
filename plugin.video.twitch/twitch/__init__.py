#-*- encoding: utf-8 -*-
VERSION='0.3.8'
MAX_RETRIES=5
import sys
try:
    from urllib.request import urlopen, Request
    from urllib.parse import quote_plus
    from urllib.error import URLError
except ImportError:
    from urllib import quote_plus
    from urllib2 import Request, urlopen, URLError

try:
    import json
except:
    import simplejson as json  # @UnresolvedImport

class JSONScraper(object):
    '''
    Encapsulates execution request and parsing of response
    '''
    def __init__(self, logger):
        object.__init__(self)
        self.logger = logger
    '''
        Download Data from an url and returns it as a String
        @param url Url to download from (e.g. http://www.google.com)
        @param headers currently unused, backwards compability
        @returns String of data from URL
    '''
    def downloadWebData(self, url, headers=None):
        data = ""
        for _ in range(MAX_RETRIES):
            try:
                req = Request(url)
                req.add_header(Keys.USER_AGENT, Keys.USER_AGENT_STRING)
                response = urlopen(req)
                if sys.version_info < (3, 0):
                    data = response.read()
                else:
                    data = response.readall().decode('utf-8')
                response.close()
                break
            except Exception as err:
                if not isinstance(err, URLError):
                    self.logger.debug("Error %s during HTTP Request, abort", repr(err))
                    raise # propagate non-URLError
                self.logger.debug("Error %s during HTTP Request, retrying", repr(err))
        else:
            raise TwitchException(TwitchException.HTTP_ERROR)
        return data

    '''
        Download Data from an url and returns it as JSON
        @param url Url to download from
        @param headers currently unused, backwards compability
        @returns JSON Object with data from URL
    '''
    def getJson(self, url, headers=None):
        jsonString = self.downloadWebData(url, headers)
        try:
            jsonDict = json.loads(jsonString)
            self.logger.debug(json.dumps(jsonDict, indent=4, sort_keys=True))
            return jsonDict
        except:
            raise TwitchException(TwitchException.JSON_ERROR)

class M3UPlaylist(object):
    def __init__(self, input):
        def parseQuality(ExtXMediaLine,ExtXStreamInfLine,Url):
            namePosition = ExtXMediaLine.find('NAME')
            if(namePosition==-1):
                raise TwitchException()
            qualityName = ''
            namePosition+=6
            for char in ExtXMediaLine[namePosition:]:
                if(char=='"'):
                    break
                qualityName += char
            return qualityName, Url

        self.playlist = dict()
        lines = input.splitlines()
        linesIterator = iter(lines)
        for line in linesIterator:
            if(line.startswith('#EXT-X-MEDIA')):
                quality, url = parseQuality(line, next(linesIterator), next(linesIterator))
                self.playlist[quality] = url

    #returns selected quality or best match if not available
    def getQuality(self, QualityInt):
        def isInPlaylist(QualityInt):
            return Keys.QUALITY_LIST_STREAM[QualityInt] in self.playlist

        if(isInPlaylist(QualityInt)):
            #selected quality is available
            return self.playlist[Keys.QUALITY_LIST_STREAM[QualityInt]]
        else:
            #not available, start with worst quality and improve
            #break if better quality is not available
            bestMatch = len(Keys.QUALITY_LIST_STREAM) - 1
            for newMatch in range(bestMatch, -1, -1):
                if(isInPlaylist(newMatch)):
                    bestMatch = newMatch

            return self.playlist[Keys.QUALITY_LIST_STREAM[bestMatch]]

    def __str__(self):
        return repr(self.playlist)

class TwitchTV(object):
    '''
    Uses Twitch API to fetch json-encoded objects
    every method returns a dict containing the objects\' values
    '''
    def __init__(self, logger):
        self.logger = logger
        self.scraper = JSONScraper(logger)

    def getFeaturedStream(self):
        url = ''.join([Urls.STREAMS, Keys.FEATURED])
        return self._fetchItems(url, Keys.FEATURED)

    def getGames(self, offset=0, limit=10):
        options = Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
        url = ''.join([Urls.GAMES, Keys.TOP, options])
        return self._fetchItems(url, Keys.TOP)

    def getChannels(self, offset=0, limit=10):
        options = Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
        url = ''.join([Urls.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def getGameStreams(self, gameName, offset=0, limit=10):
        quotedName = quote_plus(gameName)
        options = Urls.OPTIONS_OFFSET_LIMIT_GAME.format(offset, limit, quotedName)
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def searchStreams(self, query, offset=0, limit=10):
        quotedQuery = quote_plus(query)
        options = Urls.OPTIONS_OFFSET_LIMIT_QUERY.format(offset, limit, quotedQuery)
        url = ''.join([Urls.SEARCH, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def getFollowingStreams(self, username):
        #Get ChannelNames
        followingChannels = self.getFollowingChannelNames(username)
        channelNames = self._filterChannelNames(followingChannels)

        #get Streams of that Channels
        options = '?channel=' + ','.join([channels[Keys.NAME] for channels in channelNames])
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        channels = {'live' : self._fetchItems(url, Keys.STREAMS)}
        channels['others'] = channelNames
        return channels

    def getFollowerVideos(self, username, offset, past):
        url = Urls.CHANNEL_VIDEOS.format(username,offset,past)
        items = self.scraper.getJson(url)
        return {Keys.TOTAL : items[Keys.TOTAL], Keys.VIDEOS : items[Keys.VIDEOS]}

    def getVideoTitle(self, id):
        url = Urls.VIDEO_INFO.format(id)
        return self._fetchItems(url, 'title')

    def __getChunkedVideo(self, id):
        # twitch site queries chunked playlists also with token
        # not necessary yet but might change (similar to vod playlists)
        url = Urls.VIDEO_PLAYLIST.format(id)
        return self.scraper.getJson(url)

    def __getVideoPlaylistChunked(self, id, maxQuality):
        vidChunks = self.__getChunkedVideo(id)
        chunks = []
        if vidChunks['chunks'].get(Keys.QUALITY_LIST_VIDEO[maxQuality]):
            # prefered quality is not None -> available
            chunks = vidChunks['chunks'][Keys.QUALITY_LIST_VIDEO[maxQuality]]
        else: #prefered quality is not available TODO best match
            chunks = vidChunks['chunks'][Keys.QUALITY_LIST_VIDEO[0]]

        title = self.getVideoTitle(id)
        itemTitle = '%s - Part {0} of %s' % (title, len(chunks))

        playlist = [('', ('', vidChunks['preview']))]
        curN = 0
        for chunk in chunks:
            curN += 1
            playlist += [(chunk['url'], (itemTitle.format(curN), vidChunks['preview']))]

        return playlist

    def __getVideoPlaylistVod(self, id, maxQuality):
        playlist = [('', ())]
        vodid = id[1:]
        url = Urls.VOD_TOKEN.format(vodid)
        access_token = self.scraper.getJson(url)

        playlistQualitiesUrl = Urls.VOD_PLAYLIST.format(
            vodid,
            access_token['token'],
            access_token['sig'])
        playlistQualitiesData = self.scraper.downloadWebData(playlistQualitiesUrl)
        playlistQualities = M3UPlaylist(playlistQualitiesData)

        vodUrl = playlistQualities.getQuality(maxQuality)
        playlist+=[(vodUrl, ())]

        return playlist

    def getVideoPlaylist(self, id, maxQuality):
        playlist = [(),()]
        if(id.startswith(('a','c'))):
            playlist = self.__getVideoPlaylistChunked(id,maxQuality)
        elif(id.startswith('v')):
            playlist = self.__getVideoPlaylistVod(id,maxQuality)
        return playlist

    def getFollowingChannelNames(self, username):
        acc = []
        limit = 100
        offset = 0
        quotedUsername = quote_plus(username)
        baseurl = Urls.FOLLOWED_CHANNELS.format(quotedUsername)
        while True:
            url = baseurl + Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
            temp = self._fetchItems(url, Keys.FOLLOWS)
            if (len(temp) == 0):
                break;
            acc = acc + temp
            offset = offset + limit
        return acc

    def getTeams(self, index):
        return self._fetchItems(Urls.TEAMS.format(str(index * 25)), Keys.TEAMS)

    def getTeamStreams(self, teamName):
        '''
        Consider this method to be unstable, because the
        requested resource is not part of the official Twitch API
        '''
        quotedTeamName = quote_plus(teamName)
        url = Urls.TEAMSTREAM.format(quotedTeamName)
        return self._fetchItems(url, Keys.CHANNELS)

    #gets playable livestream url
    def getLiveStream(self, channelName, maxQuality):
        #Get Access Token (not necessary at the moment but could come into effect at any time)
        tokenurl= Urls.CHANNEL_TOKEN.format(channelName)
        channeldata = self.scraper.getJson(tokenurl)
        channeltoken= channeldata['token']
        channelsig= channeldata['sig']
        
        #Download and Parse Multiple Quality Stream Playlist
        try:
            hls_url = Urls.HLS_PLAYLIST.format(channelName,channelsig,channeltoken)
            data = self.scraper.downloadWebData(hls_url)
            playlist = M3UPlaylist(data)
            return playlist.getQuality(maxQuality)

        except TwitchException:
                #HTTP Error in download web data -> stream is offline
                raise TwitchException(TwitchException.STREAM_OFFLINE)

    def _filterChannelNames(self, channels):
        tmp = [{Keys.DISPLAY_NAME : item[Keys.CHANNEL][Keys.DISPLAY_NAME], Keys.NAME : item[Keys.CHANNEL][Keys.NAME], Keys.LOGO : item[Keys.CHANNEL][Keys.LOGO]} for item in channels]
        return sorted(tmp, key=lambda k: k[Keys.DISPLAY_NAME]) 

    def _fetchItems(self, url, key):
        items = self.scraper.getJson(url)
        return items[key] if items else []

class Keys(object):
    '''
    Should not be instantiated, just used to categorize
    string-constants
    '''

    BITRATE = 'bitrate'
    CHANNEL = 'channel'
    CHANNELS = 'channels'
    CONNECT = 'connect'
    BACKGROUND = 'background'
    DISPLAY_NAME = 'display_name'
    FEATURED = 'featured'
    FOLLOWS = 'follows'
    GAME = 'game'
    LOGO = 'logo'
    BOX = 'box'
    LARGE = 'large'
    NAME = 'name'
    NEEDED_INFO = 'needed_info'
    PLAY = 'play'
    PLAYPATH = 'playpath'
    QUALITY = 'quality'
    RTMP = 'rtmp'
    STREAMS = 'streams'
    REFERER = 'Referer'
    RTMP_URL = 'rtmpUrl'
    STATUS = 'status'
    STREAM = 'stream'
    SWF_URL = 'swfUrl'
    TEAMS = 'teams'
    TOKEN = 'token'
    TOP = 'top'
    TOTAL = '_total'
    USER_AGENT = 'User-Agent'
    USER_AGENT_STRING = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
    VIDEOS = 'videos'
    VIDEO_BANNER = 'video_banner'
    VIDEO_HEIGHT = 'video_height'
    VIEWERS = 'viewers'
    PREVIEW = 'preview'
    TITLE = 'title'

    QUALITY_LIST_STREAM = ['Source', "High", "Medium", "Low", "Mobile"]
    QUALITY_LIST_VIDEO = ['live', "720p", "480p", "360p", "226p"]

class Urls(object):
    '''
    Should not be instantiated, just used to categorize
    string-constants
    '''
    BASE = 'https://api.twitch.tv/kraken/'
    FOLLOWED_CHANNELS = BASE + 'users/{0}/follows/channels'
    GAMES = BASE + 'games/'
    STREAMS = BASE + 'streams/'
    SEARCH = BASE + 'search/'
    TEAMS = BASE + 'teams?limit=25&offset={0}'

    TEAMSTREAM = 'http://api.twitch.tv/api/team/{0}/live_channels.json'
    CHANNEL_TOKEN = 'http://api.twitch.tv/api/channels/{0}/access_token'
    VOD_TOKEN = 'http://api.twitch.tv/api/vods/{0}/access_token'

    OPTIONS_OFFSET_LIMIT = '?offset={0}&limit={1}'
    OPTIONS_OFFSET_LIMIT_GAME = OPTIONS_OFFSET_LIMIT + '&game={2}'
    OPTIONS_OFFSET_LIMIT_QUERY = OPTIONS_OFFSET_LIMIT + '&q={2}'

    HLS_PLAYLIST = 'http://usher.twitch.tv/api/channel/hls/{0}.m3u8?sig={1}&token={2}&allow_source=true'
    VOD_PLAYLIST = 'http://usher.twitch.tv/vod/{0}?nauth={1}&nauthsig={2}'

    CHANNEL_VIDEOS = 'https://api.twitch.tv/kraken/channels/{0}/videos?limit=8&offset={1}&broadcasts={2}'
    VIDEO_PLAYLIST = 'https://api.twitch.tv/api/videos/{0}'
    VIDEO_INFO = 'https://api.twitch.tv/kraken/videos/{0}'


class TwitchException(Exception):

    NO_STREAM_URL = 0
    STREAM_OFFLINE = 1
    HTTP_ERROR = 2
    JSON_ERROR = 3

    def __init__(self, code):
        Exception.__init__(self)
        self.code = code

    def __str__(self):
        return repr(self.code)
