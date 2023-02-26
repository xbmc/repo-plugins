# -*- coding: utf-8 -*-
"""
     
    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from .common import kodi

from twitch.oauth.helix import scopes


def __enum(**enums):
    return type('Enum', (), enums)


ADDON_DATA_DIR = kodi.translate_path(kodi.get_profile())

MODES = __enum(
    MAIN='main',
    FEATUREDSTREAMS='featured_streams',
    GAMES='games',
    CHANNELS='channels',
    FOLLOWING='following',
    SEARCH='search',
    NEWSEARCH='new_search',
    SEARCHRESULTS='search_results',
    SETTINGS='settings',
    FOLLOWED='followed',
    CHANNELVIDEOS='channel_videos',
    CHANNELVIDEOLIST='channel_video_list',
    GAMESTREAMS='game_streams',
    RESETCACHE='reset_cache',
    INSTALLIRCCHAT='install_ircchat',
    PLAY='play',
    TOKENURL='get_token_url',
    EDITFOLLOW='edit_user_follows',
    EDITBLOCK='edit_user_blocks',
    EDITBLACKLIST='edit_blacklist',
    EDITQUALITIES='edit_qualities',
    CLEARLIST='clear_list',
    COLLECTIONS='collections',
    COLLECTIONVIDEOLIST='collection_video_list',
    BROWSE='browse',
    STREAMLIST='stream_list',
    CLIPSLIST='clips_list',
    GAMELISTS='game_lists',
    EDITSORTING='edit_sorting',
    EDITLANGUAGES='edit_languages',
    CONFIGUREIA='configure_ia',
    REVOKETOKEN='revoke_token',
    UPDATETOKEN='update_token',
    REFRESH='refresh',
    LISTSEARCH='list_search',
    CLEARSEARCHHISTORY='clear_search_history',
    REMOVESEARCHHISTORY='remove_search_history',
    MAINTAIN='maintain'
)

LINE_LENGTH = 60
MAX_REQUESTS = 5
REQUEST_LIMIT = 100
CURSOR_LIMIT = 10

COLORS = 'aliceblue|antiquewhite|aqua|aquamarine|azure|beige|bisque|black|blanchedalmond|blue|blueviolet|brown|burlywood|cadetblue|chartreuse|chocolate|coral|cornflowerblue|cornsilk|crimson|cyan|darkblue|darkcyan|darkgoldenrod|darkgray|darkgreen|darkkhaki|darkmagenta|darkolivegreen|darkorange|darkorchid|darkred|darksalmon|darkseagreen|darkslateblue|darkslategray|darkturquoise|darkviolet|deeppink|deepskyblue|dimgray|dodgerblue|firebrick|floralwhite|forestgreen|fuchsia|gainsboro|ghostwhite|gold|goldenrod|gray|green|greenyellow|honeydew|hotpink|indianred|indigo|ivory|khaki|lavender|lavenderblush|lawngreen|lemonchiffon|lightblue|lightcoral|lightcyan|lightgoldenrodyellow|lightgrey|lightgreen|lightpink|lightsalmon|lightseagreen|lightskyblue|lightslategray|lightsteelblue|lightyellow|lime|limegreen|linen|magenta|maroon|mediumaquamarine|mediumblue|mediumorchid|mediumpurple|mediumseagreen|mediumslateblue|mediumspringgreen|mediumturquoise|mediumvioletred|midnightblue|mintcream|mistyrose|moccasin|navajowhite|navy|none|oldlace|olive|olivedrab|orange|orangered|orchid|palegoldenrod|palegreen|paleturquoise|palevioletred|papayawhip|peachpuff|peru|pink|plum|powderblue|purple|red|rosybrown|royalblue|saddlebrown|salmon|sandybrown|seagreen|seashell|sienna|silver|skyblue|slateblue|slategray|snow|springgreen|steelblue|tan|teal|thistle|tomato|turquoise|violet|wheat|white|whitesmoke|yellow|yellowgreen'

ICON = kodi.get_icon()
FANART = kodi.get_fanart()

ADAPTIVE_SOURCE_TEMPLATE = {'id': 'hls', 'name': 'Adaptive', 'bandwidth': -1, 'url': ''}

CLIENT_ID = 'cHMyZWQ5emxqOHp5cXp0c2R6MnRsNHV5czg0Yjhr'
REDIRECT_URI = 'https://anxdpanic.github.io/plugin.video.twitch/token/'

LIVE_PREVIEW_TEMPLATE = '%://static-cdn.jtvnw.net/previews-ttv/live_user_%-%x%.jpg'  # sqlite LIKE pattern


class Images:
    ICON = ICON
    THUMB = ICON
    POSTER = ICON
    FANART = FANART
    BANNER = ''
    CLEARART = ''
    CLEARLOGO = ''
    LANDSCAPE = ''
    #
    VIDEOTHUMB = 'http://static-cdn.jtvnw.net/ttv-static/404_preview-320x180.jpg'
    BOXART = 'http://static-cdn.jtvnw.net/ttv-static/404_boxart.jpg'


class Keys:
    _ID = '_id'
    AVATAR_IMAGE = 'avatar_image_url'
    BACKGROUND = 'background'
    BITRATE = 'bitrate'
    BLOCKS = 'blocks'
    BOX = 'box'
    BOX_ART_URL = 'box_art_url'
    BROADCASTER = 'broadcaster'
    BROADCASTER_ID = 'broadcaster_id'
    BROADCASTER_LANGUAGE = 'broadcaster_language'
    BROADCASTER_LOGIN = 'broadcaster_login'
    BROADCASTER_NAME = 'broadcaster_name'
    BROADCASTER_TYPE = 'broadcaster_type'
    CHANNEL = 'channel'
    CHANNELS = 'channels'
    CHUNKS = 'chunks'
    CLIPS = 'clips'
    COLLECTIONS = 'collections'
    CONNECT = 'connect'
    CREATED_AT = 'created_at'
    CREATOR_NAME = 'creator_name'
    CURATOR = 'curator'
    CURRENT_VIEWERS = 'current_viewers'
    CURSOR = '_cursor'
    DATA = 'data'
    DELAY = 'delay'
    DESCRIPTION = 'description'
    DISPLAY_NAME = 'display_name'
    DURATION = 'duration'
    FEATURED = 'featured'
    FOLLOWERS = 'followers'
    FOLLOWS = 'follows'
    GAME = 'game'
    GAME_ID = 'game_id'
    GAME_NAME = 'game_name'
    GAMES = 'games'
    ID = 'id'
    IMAGE = 'image'
    IS_LIVE = 'is_live'
    IS_MATURE = 'is_mature'
    ITEMS = 'items'
    ITEMS_COUNT = 'items_count'
    ITEM_ID = 'item_id'
    ITEM_TYPE = 'item_type'
    LANGUAGE = 'language'
    LARGE = 'large'
    LENGTH = 'length'
    LIVE = 'live'
    LOGO = 'logo'
    LOGIN = 'login'
    MATURE = 'mature'
    MEDIUM = 'medium'
    META_GAME = 'meta_game'
    NAME = 'name'
    NEEDED_INFO = 'needed_info'
    OFFLINE_IMAGE_URL = 'offline_image_url'
    OTHERS = 'others'
    OWNER = 'owner'
    PARTNER = 'partner'
    PLAY = 'play'
    PLAYPATH = 'playpath'
    PREVIEW = 'preview'
    PROFILE_BANNER = 'profile_banner'
    PROFILE_IMAGE_URL = 'profile_image_url'
    PUBLISHED_AT = 'published_at'
    QUALITY = 'quality'
    RESOLUTIONS = 'resolutions'
    RTMP = 'rtmp'
    RTMP_URL = 'rtmpUrl'
    SIG = 'sig'
    SIZE600 = 'size600'
    SLUG = 'slug'
    SMALL = 'small'
    SOURCE = 'source'
    STATUS = 'status'
    STREAM = 'stream'
    STREAMS = 'streams'
    STREAM_TYPE = 'stream_type'
    SWF_URL = 'swfUrl'
    TEAMS = 'teams'
    THUMBNAILS = 'thumbnails'
    THUMBNAIL_URL = 'thumbnail_url'
    TITLE = 'title'
    TO_ID = 'to_id'
    TOKEN = 'token'
    TOP = 'top'
    TOTAL = '_total'
    TOTAL_DURATION = 'total_duration'
    TRACKING_ID = 'tracking_id'
    TYPE = 'type'
    URL = 'url'
    USER = 'user'
    USER_ID = 'user_id'
    USER_LOGIN = 'user_login'
    USER_NAME = 'user_name'
    USERS = 'users'
    VIDEOS = 'videos'
    VIDEO_BANNER = 'video_banner'
    VIDEO_HEIGHT = 'video_height'
    VIEW_COUNT = 'view_count'
    VIEWER_COUNT = 'viewer_count'
    VIEWERS = 'viewers'
    VIEWS = 'views'
    VOD = 'vod'
    VODS = 'vods'


class Scripts:
    REFRESH = 'special://home/addons/plugin.video.twitch/resources/lib/twitch_addon/refresh.py'


SCOPES = [scopes.user_read_follows, scopes.user_edit_follows, scopes.user_read_subscriptions,
          scopes.chat_read, scopes.chat_edit]
