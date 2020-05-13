# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import json
import os

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcaddon  # pylint: disable=import-error

__ID = 'plugin.video.composite_for_plex'
__ADDON = xbmcaddon.Addon(id=__ID)


def __enum(**enums):
    return type('Enum', (), enums)


COMMANDS = __enum(
    UNSET=None,
    ADDTOPLAYLIST='add_playlist_item',
    AUDIO='audio',
    DELETE='delete',
    DELETEPLAYLIST='delete_playlist',
    DELETEFROMPLAYLIST='delete_playlist_item',
    DELETEREFRESH='delete_refresh',
    DISPLAYSERVER='displayservers',
    MANAGEMYPLEX='managemyplex',
    MASTER='master',
    REFRESH='refresh',
    SIGNIN='signin',
    SIGNOUT='signout',
    SUBS='subs',
    SWITCHUSER='switchuser',
    UPDATE='update',
    WATCH='watch',
)

MODES = __enum(
    UNSET=-1,
    GETCONTENT=0,
    TVSHOWS=1,
    MOVIES=2,
    ARTISTS=3,
    TVSEASONS=4,
    PLAYLIBRARY=5,
    TVEPISODES=6,
    PLEXPLUGINS=7,
    PROCESSXML=8,
    CHANNELSEARCH=9,
    CHANNELPREFS=10,
    PLAYSHELF=11,
    BASICPLAY=12,
    SHARED_MOVIES=13,
    ALBUMS=14,
    TRACKS=15,
    PHOTOS=16,
    MUSIC=17,
    VIDEOPLUGINPLAY=18,
    PLEXONLINE=19,
    CHANNELINSTALL=20,
    CHANNELVIEW=21,
    PLAYLIBRARY_TRANSCODE=23,
    DISPLAYSERVERS=22,
    MYPLEXQUEUE=24,
    SHARED_SHOWS=25,
    SHARED_MUSIC=26,
    SHARED_PHOTOS=27,
    SHARED_ALL=29,
    PLAYLISTS=30,
    WIDGETS=31,
    SEARCHALL=32,
    TXT_MOVIES='movies',
    TXT_MOVIES_ON_DECK='movies_on_deck',
    TXT_MOVIES_RECENT_ADDED='movies_recent_added',
    TXT_MOVIES_RECENT_RELEASE='movies_recent_release',
    TXT_TVSHOWS='tvshows',
    TXT_TVSHOWS_ON_DECK='tvshows_on_deck',
    TXT_TVSHOWS_RECENT_ADDED='tvshows_recent_added',
    TXT_TVSHOWS_RECENT_AIRED='tvshows_recent_aired',
    TXT_OPEN='open',
    TXT_PLAY='play',
    TXT_MOVIES_LIBRARY='library/movies',
    TXT_TVSHOWS_LIBRARY='library/tvshows',
)

CONFIG = {
    'addon': __ADDON,
    'id': __ID,
    'name': __ADDON.getAddonInfo('name'),
    'icon': __ADDON.getAddonInfo('icon'),
    'cache_path': os.path.join(__ADDON.getAddonInfo('profile'), 'cache'),
    'version': __ADDON.getAddonInfo('version'),
    'media_path': 'special://home/addons/%s/resources/media/' % __ADDON.getAddonInfo('id'),
    'temp_path': xbmc.translatePath('special://temp/%s/' % __ADDON.getAddonInfo('id')),
    'required_revision': '1.0.7'
}

try:
    CONFIG['kodi_version'] = int(xbmc.getInfoLabel('System.BuildVersion').split()[0].split('.')[0])
except:  # pylint: disable=bare-except
    CONFIG['kodi_version'] = 0

try:
    _ = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "Application.GetProperties",
        "params": {
            "properties": ["language"]
        }
    }
    CONFIG['language'] = json.loads(xbmc.executeJSONRPC(json.dumps(_))) \
        .get('result').get('language').split('_')[0]
except:  # pylint: disable=bare-except
    CONFIG['language'] = 'en'

StreamControl = __enum(
    KODI='0',
    PLEX='1',
    NEVER='2'
)
