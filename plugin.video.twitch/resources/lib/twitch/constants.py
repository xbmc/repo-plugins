# -*- coding: utf-8 -*-
TWITCH_API_VERSION = 3


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
    MEDIUM = 'medium'
    NAME = 'name'
    NEEDED_INFO = 'needed_info'
    PLAY = 'play'
    PLAYPATH = 'playpath'
    QUALITY = 'quality'
    RTMP = 'rtmp'
    STREAMS = 'streams'
    RTMP_URL = 'rtmpUrl'
    STATUS = 'status'
    STREAM = 'stream'
    SWF_URL = 'swfUrl'
    TEAMS = 'teams'
    TOKEN = 'token'
    TOP = 'top'
    TOTAL = '_total'
    VIDEOS = 'videos'
    VIDEO_BANNER = 'video_banner'
    PROFILE_BANNER = 'profile_banner'
    VIDEO_HEIGHT = 'video_height'
    VIEWERS = 'viewers'
    CURRENT_VIEWERS = 'current_viewers'
    PREVIEW = 'preview'
    TITLE = 'title'
    LENGTH = 'length'
    META_GAME = 'meta_game'
    URL = 'url'
    CHUNKS = 'chunks'
    SIG = 'sig'
    LIVE = 'live'
    OTHERS = 'others'
    IMAGE = 'image'
    SIZE600 = 'size600'
    VIEWS = 'views'
    MATURE = 'mature'
    PARTNER = 'partner'
    DELAY = 'delay'
    BROADCASTER_LANGUAGE = 'broadcaster_language'
    DESCRIPTION = 'description'
    CREATED_AT = 'created_at'

    QUALITY_LIST_STREAM = ['Source', 'High', 'Medium', 'Low', 'Mobile']
    QUALITY_LIST_VIDEO = ['live', '720p', '480p', '360p', '226p']

    ACCEPT = 'Accept'
    REFERER = 'Referer'
    USER_AGENT = 'User-Agent'
    USER_AGENT_STRING = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
    API_VERSION = 'application/vnd.twitchtv.v{0}+json'.format(str(TWITCH_API_VERSION))
    CLIENT_ID_HEADER = 'Client-ID'
    CLIENT_ID = 'TwitchonXBMC_{0}'
    DEFAULT_ID = 'user_{0}'


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
    VOD_PLAYLIST = 'http://usher.twitch.tv/vod/{0}?nauth={1}&nauthsig={2}&allow_source=true'

    CHANNEL_VIDEOS = 'https://api.twitch.tv/kraken/channels/{0}/videos?limit=8&offset={1}&broadcasts={2}'
    VIDEO_PLAYLIST = 'https://api.twitch.tv/api/videos/{0}'
    VIDEO_INFO = 'https://api.twitch.tv/kraken/videos/{0}'
    FOLLOWED_GAMES = 'https://api.twitch.tv/api/users/{0}/follows/games'
