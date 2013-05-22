#-*- encoding: utf-8 -*-
import urllib2
from urllib import quote_plus
import re
try:
    import json
except:
    import simplejson as json

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'

class JSONScraper(object):
    '''
    Encapsulates execution request and parsing of response
    '''
    def _downloadWebData(self, url, headers = None):
        req = urllib2.Request(url)
        req.add_header(Keys.USER_AGENT, USER_AGENT)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data

    def getJson(self, url, headers = None):
        try:
            jsonString = self._downloadWebData(url, headers)
        except:
            raise TwitchException(TwitchException.HTTP_ERROR)
        try:
            return json.loads(jsonString)
        except:
            raise TwitchException(TwitchException.JSON_ERROR)


class TwitchTV(object):
    '''
    Uses Twitch API to fetch json-encoded objects
    every method returns a dict containing the objects' values
    '''
    def __init__(self):
        self.scraper = JSONScraper()

    def getFeaturedStream(self):
        url = ''.join([Urls.STREAMS, Keys.FEATURED])
        return self._fetchItems(url, Keys.FEATURED)

    def getGames(self, offset = 10, limit = 10):
        options = Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
        url = ''.join([Urls.GAMES, Keys.TOP, options])
        return self._fetchItems(url, Keys.TOP)

    def getGameStreams(self, gameName, offset = 10, limit = 10):
        quotedName = quote_plus(gameName)
        options = Urls.OPTIONS_OFFSET_LIMIT_GAME.format(offset, limit, quotedName)
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def searchStreams(self, query, offset = 10, limit = 10):
        quotedQuery = quote_plus(query)
        options = Urls.OPTIONS_OFFSET_LIMIT_QUERY.format(offset, limit, quotedQuery)
        url = ''.join([Urls.SEARCH, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)
    
    def getFollowingStreams(self, username):
        #Get ChannelNames
        followingChannels = self.getFollowingChannelNames(username)
        channelNames = self._filterChannelNames(followingChannels)
        #get Streams of that Channels
        options = '?channel=' + ','.join(channelNames)
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)
        
    def getFollowingChannelNames(self, username):
        quotedUsername = quote_plus(username)
        url = Urls.FOLLOWED_CHANNELS.format(quotedUsername)
        return self._fetchItems(url, Keys.FOLLOWS)
    
    def getTeams(self):
        return self._fetchItems(Urls.TEAMS, Keys.TEAMS)
    
    def getTeamStreams(self, teamName):
        '''
        Consider this method to be unstable, because the 
        requested resource is not part of the official Twitch API
        '''
        quotedTeamName = quote_plus(teamName)
        url = Urls.TEAMSTREAM.format(quotedTeamName)
        return self._fetchItems(url, Keys.CHANNELS)
        
        
    def _filterChannelNames(self, channels):
        return [item[Keys.CHANNEL][Keys.NAME] for item in channels]
    
    def _fetchItems(self, url, key):
        items = self.scraper.getJson(url)
        return items[key] if items else []


class TwitchVideoResolver(object):
    '''
    Resolves the RTMP-Link to a given Channelname
    Uses Justin.TV API
    '''
    
    def getRTMPUrl(self, channelName, maxQuality):
        swfUrl = self._getSwfUrl(channelName)
        streamQualities = self._getStreamsForChannel(channelName)
        # check that api response isn't empty (i.e. stream is offline)
        if streamQualities: 
            items = [
                     self._parseStreamValues(stream, swfUrl)
                     for stream in streamQualities
                     if self._streamIsAccessible(stream)
                     ]
            if items:
                return self._bestMatchForChosenQuality(items, maxQuality)[Keys.RTMP_URL]
            else:
                raise TwitchException(TwitchException.NO_STREAM_URL)
        else:
            raise TwitchException(TwitchException.STREAM_OFFLINE)
    
    def _getSwfUrl(self, channelName):
        url = Urls.TWITCH_SWF + channelName
        headers = {Keys.USER_AGENT: USER_AGENT,
                   Keys.REFERER: Urls.TWITCH_TV + channelName}
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        return response.geturl()

    def _streamIsAccessible(self, stream):
        if not stream[Keys.TOKEN] and re.match(Patterns.IP, stream.get(Keys.CONNECT)): 
            return False
        return True

    def _getStreamsForChannel(self, channelName):
        scraper = JSONScraper()
        url = Urls.TWITCH_API.format(channel = channelName)
        return scraper.getJson(url)

    def _parseStreamValues(self, stream, swfUrl):
        streamVars = {Keys.SWF_URL : swfUrl}
        streamVars[Keys.RTMP] = stream[Keys.CONNECT]
        streamVars[Keys.PLAYPATH] = stream.get(Keys.PLAY)

        if stream[Keys.TOKEN]:
            token = stream[Keys.TOKEN].replace('\\', '\\5c').replace(' ', '\\20').replace('"', '\\22')
        else:
            token = ''

        streamVars[Keys.TOKEN] = (' jtv=' + token) if token else ''
        quality = int(stream.get(Keys.VIDEO_HEIGHT, 0))
        return {Keys.QUALITY: quality,
                Keys.RTMP_URL: Urls.FORMAT_FOR_RTMP.format(**streamVars)}

    def _bestMatchForChosenQuality(self, streams, maxQuality):
        streams = [stream for stream in streams 
                   if stream[Keys.QUALITY] <= maxQuality]
        streams.sort(key=lambda t: t[Keys.QUALITY], reverse=True)
        return streams[0]


class Keys(object):
    '''
    Should not be instantiated, just used to categorize 
    string-constants
    '''
    CHANNEL = 'channel'
    CHANNELS = 'channels'
    CONNECT = 'connect'
    BACKGROUND = 'background'
    DISPLAY_NAME = 'display_name'
    FEATURED = 'featured'
    FOLLOWS = 'follows'
    GAME = 'game'
    LOGO = 'logo'
    LARGE = 'large'
    NAME = 'name'
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
    USER_AGENT = 'User-Agent'
    VIDEO_BANNER  = 'video_banner'
    VIDEO_HEIGHT = 'video_height'
    VIEWERS = 'viewers'

class Patterns(object):
    '''
    Should not be instantiated, just used to categorize 
    string-constants
    '''
    VALID_FEED = "^https?:\/\/(?:[^\.]*.)?(?:twitch|justin)\.tv\/([a-zA-Z0-9_]+).*$"
    IP = '.*\d+\.\d+\.\d+\.\d+.*'
    EXPIRATION = '.*"expiration": (\d+)[^\d].*'

class Urls(object):
    '''
    Should not be instantiated, just used to categorize 
    string-constants
    '''
    TWITCH_TV = 'http://www.twitch.tv/'

    BASE = 'https://api.twitch.tv/kraken/'
    FOLLOWED_CHANNELS =  BASE + 'users/{0}/follows/channels'
    GAMES = BASE + 'games/'
    STREAMS = BASE + 'streams/'
    SEARCH = BASE + 'search/'
    TEAMS = BASE + 'teams'
    
    TEAMSTREAM = 'http://api.twitch.tv/api/team/{0}/live_channels.json'
    
    OPTIONS_OFFSET_LIMIT = '?offset={0}&limit={1}'
    OPTIONS_OFFSET_LIMIT_GAME = OPTIONS_OFFSET_LIMIT + '&game={2}'
    OPTIONS_OFFSET_LIMIT_QUERY = OPTIONS_OFFSET_LIMIT + '&q={2}'

    TWITCH_API = "http://usher.justin.tv/find/{channel}.json?type=any&group=&channel_subscription="
    TWITCH_SWF = "http://www.justin.tv/widgets/live_embed_player.swf?channel="
    FORMAT_FOR_RTMP = "{rtmp}/{playpath} swfUrl={swfUrl} swfVfy=1 {token} live=1" #Pageurl missing here
    
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
