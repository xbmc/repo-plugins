#-*- encoding: utf-8 -*-
import xbmcgui, xbmc
import sys
try:
    from urllib.request import urlopen, Request
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus
    from urllib2 import Request, urlopen

try:
    import json
except:
    import simplejson as json  # @UnresolvedImport

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'


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
        try:
            req = Request(url)
            req.add_header(Keys.USER_AGENT, USER_AGENT)
            response = urlopen(req)
            
            if sys.version_info < (3, 0):
                data = response.read()
            else:
                data = response.readall().decode('utf-8')
            response.close()
        except:
            raise TwitchException(TwitchException.HTTP_ERROR)
        return data
        
    '''
        Download Data from an url and returns it as JSON
        @param url Url to download from
        @param headers currently unused, backwards compability
        @returns JSON Object with data from URL
    '''
    def getJson(self, url, headers=None):
        try:
            jsonString = self.downloadWebData(url, headers)
        except:
            raise TwitchException(TwitchException.HTTP_ERROR)
        try:
            jsonDict = json.loads(jsonString)
            self.logger.debug(json.dumps(jsonDict, indent=4, sort_keys=True))
            return jsonDict
        except:
            raise TwitchException(TwitchException.JSON_ERROR)


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

    def getGames(self, offset=10, limit=10):
        options = Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
        url = ''.join([Urls.GAMES, Keys.TOP, options])
        return self._fetchItems(url, Keys.TOP)

    def getChannels(self, offset=10, limit=10):
        options = Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
        url = ''.join([Urls.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def getGameStreams(self, gameName, offset=10, limit=10):
        quotedName = quote_plus(gameName)
        options = Urls.OPTIONS_OFFSET_LIMIT_GAME.format(offset, limit, quotedName)
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def searchStreams(self, query, offset=10, limit=10):
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
        
    def getVideoChunks(self, id):
        url = Urls.VIDEO_CHUNKS.format(id)
        return self.scraper.getJson(url)
        
    def getVideoTitle(self, id):
        url = Urls.VIDEO_INFO.format(id)
        return self._fetchItems(url, 'title')
        
    
    def getVideoChunksPlaylist(self, id, maxQuality):
        vidChunks = self.getVideoChunks(id)
        
        chunks = []
        if vidChunks['chunks'].get(Keys.QUALITY_LIST_VIDEO[maxQuality]):
            # prefered quality is not None -> available
            chunks = vidChunks['chunks'][Keys.QUALITY_LIST_VIDEO[maxQuality]]
        else: #prefered quality is not available TODO best match
            chunks = vidChunks['chunks'][Keys.QUALITY_LIST_VIDEO[0]]
        
        title = self.getVideoTitle(id)
        itemTitle = '%s - Part {0} of %s' % (title, len(chunks))
        
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        
        # For some reason first item is skipped, so added a dummy first item to fix
        # theres probably a better way
        playlist.add('', xbmcgui.ListItem('', thumbnailImage=vidChunks['preview']))
        curN = 0
        for chunk in chunks:
            curN += 1
            playlist.add(chunk['url'], xbmcgui.ListItem(itemTitle.format(curN), thumbnailImage=vidChunks['preview']))
            
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

    def _filterChannelNames(self, channels):
        tmp = [{Keys.DISPLAY_NAME : item[Keys.CHANNEL][Keys.DISPLAY_NAME], Keys.NAME : item[Keys.CHANNEL][Keys.NAME], Keys.LOGO : item[Keys.CHANNEL][Keys.LOGO]} for item in channels]
        return sorted(tmp, key=lambda k: k[Keys.DISPLAY_NAME].lower()) 

    def _fetchItems(self, url, key):
        items = self.scraper.getJson(url)
        return items[key] if items else []
        

class TwitchVideoResolver(object):
    '''
    Resolves the RTMP-Link to a given Channelname
    Uses Justin.TV API
    '''
    
    def __init__(self, logger):
        object.__init__(self)
        self.logger = logger
        self.scraper = JSONScraper(logger)

    def getRTMPUrl(self, channelName, maxQuality):
        swfUrl = self._getSwfUrl(channelName)
        streamQualities = self._getStreamsForChannel(channelName)
        
        self.logger.debug("=== URL and available Streams ===")
        self.logger.debug(json.dumps(swfUrl, sort_keys=True, indent=4))
        
        # check that api response isn't empty (i.e. stream is offline)
        if streamQualities:
            items = [self._parseStreamValues(stream, swfUrl)
                     for stream in streamQualities
                     if self._streamIsAccessible(stream)]
            if items:
                self.logger.debug("=== Accessible Streams ===")
                self.logger.debug(json.dumps(items, sort_keys=True, indent=4))
                return self._bestMatchForChosenQuality(items, maxQuality)[Keys.RTMP_URL]
            else:
                raise TwitchException(TwitchException.NO_STREAM_URL)
        else:
            raise TwitchException(TwitchException.STREAM_OFFLINE)

    #downloads Playlist from twitch and passes it to subfunction for custom playlist generation
    def saveHLSToPlaylist(self, channelName, maxQuality, fileName):
        #Get Access Token (not necessary at the moment but could come into effect at any time)
        tokenurl= Urls.CHANNEL_TOKEN.format(channelName)
        channeldata = self.scraper.getJson(tokenurl)
        channeltoken= channeldata['token']
        channelsig= channeldata['sig']
        
        #Download Multiple Quality Stream Playlist
        try:
            hls_url = Urls.HLS_PLAYLIST.format(channelName,channelsig,channeltoken)
            data = self.scraper.downloadWebData(hls_url)
            playlist = self._saveHLSToPlaylist(data,maxQuality)

            #Write Custom Playlist
            with open(fileName, "w") as text_file:
                text_file.write(str(playlist))
        except TwitchException:
                #HTTP Error in download web data -> stream is offline
                raise TwitchException(TwitchException.STREAM_OFFLINE)
        return

    #split off from main function so we can feed custom data for test cases + speedtest
    def _saveHLSToPlaylist(self, data, maxQuality):
        if(maxQuality>=len(Keys.QUALITY_LIST_STREAM)): #check if maxQuality is supported
            raise TwitchException()
        
        lines = data.split('\n') # split into lines
        
        playlist = lines[:2] # take first two lines into playlist
        qualities = [None] * len(Keys.QUALITY_LIST_STREAM) # create quality based None array
        
        lines_iterator = iter(lines[2:]) #start iterator after the first two lines
        for line in lines_iterator: # start after second line
            # if line contains 'EXT-X-TWITCH-RESTRICTED' drop the line
            if 'EXT-X-TWITCH-RESTRICTED' in line:
                continue
            
            def concat_next_3_lines(): # helper function for concatination
                return '\n'.join([line,next(lines_iterator),next(lines_iterator)])
                
            #if a line with quality is detected, put it into qualities array
            if Keys.QUALITY_LIST_STREAM[0] in line:
                qualities[0] = concat_next_3_lines()
            elif Keys.QUALITY_LIST_STREAM[1] in line:
                qualities[1] = concat_next_3_lines()
            elif Keys.QUALITY_LIST_STREAM[2] in line:
                qualities[2] = concat_next_3_lines()
            elif Keys.QUALITY_LIST_STREAM[3] in line:
                qualities[3] = concat_next_3_lines()
            elif Keys.QUALITY_LIST_STREAM[4] in line:
                qualities[4] = concat_next_3_lines()
            else:
                pass # drop other lines
        
        bestmatch = len(Keys.QUALITY_LIST_STREAM) - 1 #start with worst quality and improve
        if qualities[maxQuality]: # prefered quality is not None -> available
            bestmatch = maxQuality
        else: #prefered quality is not available, choose best fit, TODO refactor all quality queries
            for i,q in enumerate(qualities):
                if q is not None and i>maxQuality:
                    bestmatch = i
                    break
        playlist.append(qualities[bestmatch])
        
        playlist = '\n'.join(playlist) + '\n'
        return playlist


    def _getSwfUrl(self, channelName):
        url = Urls.TWITCH_SWF + channelName
        headers = {Keys.USER_AGENT: USER_AGENT,
                   Keys.REFERER: Urls.TWITCH_TV + channelName}
        req = Request(url, None, headers)
        response = urlopen(req)
        return response.geturl()

    def _streamIsAccessible(self, stream):
        stream_is_public = (stream.get(Keys.NEEDED_INFO) != "channel_subscription")
        stream_has_token = stream.get(Keys.TOKEN)

        if stream.get(Keys.CONNECT) is None:
            return False

        return stream_is_public and stream_has_token

    def _getStreamsForChannel(self, channelName):
        scraper = JSONScraper(self.logger)
        url = Urls.TWITCH_API.format(channel=channelName)
        return scraper.getJson(url)

    def _parseStreamValues(self, stream, swfUrl):
        streamVars = {Keys.SWF_URL: swfUrl}
        streamVars[Keys.RTMP] = stream[Keys.CONNECT]
        streamVars[Keys.PLAYPATH] = stream.get(Keys.PLAY)

        if stream[Keys.TOKEN]:
            token = stream[Keys.TOKEN].replace('\\', '\\5c').replace(' ', '\\20').replace('"', '\\22')
        else:
            token = ''

        streamVars[Keys.TOKEN] = (' jtv=' + token) if token else ''
        quality = int(stream.get(Keys.VIDEO_HEIGHT, 0))
        bitrate = int(stream.get(Keys.BITRATE, 0))
        return {Keys.QUALITY: quality,
                Keys.BITRATE: bitrate,
                Keys.RTMP_URL: Urls.FORMAT_FOR_RTMP.format(**streamVars)}
    
    def _bestMatchForChosenQuality(self, streams, maxQuality):
        # sorting on resolution, then bitrate, both ascending 
        streams.sort(key=lambda t: (t[Keys.QUALITY], t[Keys.BITRATE]))
        self.logger.debug("Available streams sorted: %s" % streams)
        for stream in streams:
            if stream[Keys.QUALITY] <= maxQuality:
                bestMatch = stream
        self.logger.debug("Chosen Stream is: %s" % bestMatch)
        return bestMatch


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
    VIDEOS = "videos"
    VIDEO_BANNER = 'video_banner'
    VIDEO_HEIGHT = 'video_height'
    VIEWERS = 'viewers'
    PREVIEW = 'preview'
    TITLE = 'title'
    QUALITY_LIST_STREAM = ['Source', "High", "Medium", "Low", "Mobile"]
    QUALITY_LIST_VIDEO = ['live', "720p", "480p", "360p", "226p"]



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
    FOLLOWED_CHANNELS = BASE + 'users/{0}/follows/channels'
    GAMES = BASE + 'games/'
    STREAMS = BASE + 'streams/'
    SEARCH = BASE + 'search/'
    TEAMS = BASE + 'teams?limit=25&offset={0}'

    TEAMSTREAM = 'http://api.twitch.tv/api/team/{0}/live_channels.json'
    CHANNEL_TOKEN = 'http://api.twitch.tv/api/channels/{0}/access_token'

    OPTIONS_OFFSET_LIMIT = '?offset={0}&limit={1}'
    OPTIONS_OFFSET_LIMIT_GAME = OPTIONS_OFFSET_LIMIT + '&game={2}'
    OPTIONS_OFFSET_LIMIT_QUERY = OPTIONS_OFFSET_LIMIT + '&q={2}'

    TWITCH_API = "http://usher.justin.tv/find/{channel}.json?type=any&group=&channel_subscription="
    TWITCH_SWF = "http://www.justin.tv/widgets/live_embed_player.swf?channel="
    FORMAT_FOR_RTMP = "{rtmp}/{playpath} swfUrl={swfUrl} swfVfy=1 {token} live=1"  # Pageurl missing here
    HLS_PLAYLIST = 'http://usher.twitch.tv/api/channel/hls/{0}.m3u8?sig={1}&token={2}&allow_source=true'
    
    CHANNEL_VIDEOS = 'https://api.twitch.tv/kraken/channels/{0}/videos?limit=8&offset={1}&broadcasts={2}'
    VIDEO_CHUNKS = 'https://api.twitch.tv/api/videos/{0}'
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
