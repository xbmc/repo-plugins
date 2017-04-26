# -*- coding: utf-8 -*-
"""
     
    Copyright (C) 2016 Twitch-on-Kodi
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from common import kodi
from twitch import scopes


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
    CLEARLIVEPREVIEWS='clear_live_previews',
    INSTALLIRCCHAT='install_ircchat',
    PLAY='play',
    TOKENURL='get_token_url',
    COMMUNITIES='communities',
    COMMUNITYSTREAMS='community_streams',
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
    EDITLANGUAGES='edit_languages'
)

LINE_LENGTH = 60
MAX_REQUESTS = 5
REQUEST_LIMIT = 100
CURSOR_LIMIT = 10

ICON = kodi.get_icon()
FANART = kodi.get_fanart()

CLIENT_ID = 'NjdlYnBmaHlvaWNhYjVrcjB5N3B6b2NzZm9oczd0eQ=='
REDIRECT_URI = 'https://mrsprigster.github.io/Twitch-on-Kodi/token/'

LIVE_PREVIEW_TEMPLATE = '%://static-cdn.jtvnw.net/previews-ttv/live_user_%-%___x%___.jpg'  # sqlite LIKE pattern


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
    BROADCASTER = 'broadcaster'
    BROADCASTER_LANGUAGE = 'broadcaster_language'
    CHANNEL = 'channel'
    CHANNELS = 'channels'
    CHUNKS = 'chunks'
    CLIPS = 'clips'
    COLLECTIONS = 'collections'
    COMMUNITIES = 'communities'
    CONNECT = 'connect'
    CREATED_AT = 'created_at'
    CURATOR = 'curator'
    CURRENT_VIEWERS = 'current_viewers'
    CURSOR = '_cursor'
    DELAY = 'delay'
    DESCRIPTION = 'description'
    DISPLAY_NAME = 'display_name'
    DURATION = 'duration'
    FEATURED = 'featured'
    FOLLOWERS = 'followers'
    FOLLOWS = 'follows'
    GAME = 'game'
    GAMES = 'games'
    ID = 'id'
    IMAGE = 'image'
    ITEMS = 'items'
    ITEMS_COUNT = 'items_count'
    ITEM_ID = 'item_id'
    ITEM_TYPE = 'item_type'
    LANGUAGE = 'language'
    LARGE = 'large'
    LENGTH = 'length'
    LIVE = 'live'
    LOGO = 'logo'
    MATURE = 'mature'
    MEDIUM = 'medium'
    META_GAME = 'meta_game'
    NAME = 'name'
    NEEDED_INFO = 'needed_info'
    OTHERS = 'others'
    OWNER = 'owner'
    PARTNER = 'partner'
    PLAY = 'play'
    PLAYPATH = 'playpath'
    PREVIEW = 'preview'
    PROFILE_BANNER = 'profile_banner'
    PUBLISHED_AT = 'published_at'
    QUALITY = 'quality'
    RTMP = 'rtmp'
    RTMP_URL = 'rtmpUrl'
    SIG = 'sig'
    SIZE600 = 'size600'
    SLUG = 'slug'
    STATUS = 'status'
    STREAM = 'stream'
    STREAMS = 'streams'
    SWF_URL = 'swfUrl'
    TEAMS = 'teams'
    THUMBNAILS = 'thumbnails'
    TITLE = 'title'
    TOKEN = 'token'
    TOP = 'top'
    TOTAL = '_total'
    TOTAL_DURATION = 'total_duration'
    TRACKING_ID = 'tracking_id'
    URL = 'url'
    USER = 'user'
    VIDEOS = 'videos'
    VIDEO_BANNER = 'video_banner'
    VIDEO_HEIGHT = 'video_height'
    VIEWERS = 'viewers'
    VIEWS = 'views'
    VOD = 'vod'
    VODS = 'vods'


SCOPES = [scopes.user_read, scopes.user_follows_edit, scopes.user_subscriptions, scopes.chat_login]
