# -*- coding: utf-8 -*-

# Copyright (C) 2018 Alexander Seiler
#
#
# This file is part of plugin.video.rsiplaytv.
#
# plugin.video.rsiplaytv is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# plugin.video.rsiplaytv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with plugin.video.rsiplaytv.
# If not, see <http://www.gnu.org/licenses/>.

import sys
import traceback

from urllib.parse import unquote_plus
from urllib.parse import parse_qsl

import xbmc
import xbmcaddon
import xbmcplugin
import srgssr

ADDON_ID = 'plugin.video.rsiplaytv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
DEBUG = REAL_SETTINGS.getSettingBool('Enable_Debugging')
CONTENT_TYPE = 'videos'

YOUTUBE_CHANNELS_FILENAME = 'youtube_channels.json'


class RSIPlayTV(srgssr.SRGSSR):
    def __init__(self):
        super(RSIPlayTV, self).__init__(
            int(sys.argv[1]), bu='rsi', addon_id=ADDON_ID)


def log(msg, level=xbmc.LOGDEBUG):
    """
    Logs a message using Kodi's logging interface.

    Keyword arguments:
    msg   -- the message to log
    level -- the logging level
    """
    if DEBUG:
        if level == xbmc.LOGERROR:
            msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)


def get_params():
    return dict(parse_qsl(sys.argv[2][1:]))


def run():
    """
    Run the plugin.
    """
    params = get_params()
    try:
        url = unquote_plus(params["url"])
    except Exception:
        url = None
    try:
        name = unquote_plus(params["name"])
    except Exception:
        name = None
    try:
        mode = int(params["mode"])
    except Exception:
        mode = None
    try:
        page_hash = unquote_plus(params['page_hash'])
    except Exception:
        page_hash = None
    try:
        page = unquote_plus(params['page'])
    except Exception:
        page = None

    log('Mode: %s, URL: %s, Name: %s, Page Hash: %s, Page: %s' % (
        str(mode), str(url), str(name), str(page_hash), str(page)))

    if mode is None:
        identifiers = [
            'All_Shows',
            'Favourite_Shows',
            'Newest_Favourite_Shows',
            # 'Topics',
            'Most_Searched_TV_Shows',
            'Shows_By_Date',
            'Search',
            # 'Live_TV',
            'RSI_YouTube',
        ]
        RSIPlayTV().build_main_menu(identifiers)
    elif mode == 10:
        RSIPlayTV().build_all_shows_menu()
    elif mode == 11:
        RSIPlayTV().build_favourite_shows_menu()
    elif mode == 12:
        RSIPlayTV().build_newest_favourite_menu(page=page)
    elif mode == 13:
        RSIPlayTV().build_topics_menu()
    elif mode == 14:
        RSIPlayTV().build_most_searched_shows_menu()
    elif mode == 17:
        RSIPlayTV().build_dates_overview_menu()
    # elif mode == 18:
    #     RSIPlayTV().build_live_menu()
    elif mode == 19:
        RSIPlayTV().manage_favourite_shows()
    elif mode == 20:
        RSIPlayTV().build_show_menu(name, page_hash=page_hash)
    elif mode == 21:
        RSIPlayTV().build_episode_menu(name)
    elif mode == 24:
        RSIPlayTV().build_date_menu(name)
    elif mode == 25:
        RSIPlayTV().pick_date()
    # elif mode == 26:
    #     RSIPlayTV().build_tv_menu()
    elif mode == 27:
        RSIPlayTV().build_search_menu()
    elif mode == 28:
        RSIPlayTV().build_search_media_menu(
            mode=mode, name=name, page=page, page_hash=page_hash)
    elif mode == 70:
        RSIPlayTV().build_recent_search_menu()
    elif mode == 30:
        RSIPlayTV().build_youtube_channel_overview_menu(33)
    elif mode == 33:
        RSIPlayTV().build_youtube_channel_menu(
            name, mode, page=page, page_token=page_hash)
    elif mode == 50:
        RSIPlayTV().play_video(name)
    elif mode == 51:
        RSIPlayTV().play_livestream(name)
    elif mode == 100:
        RSIPlayTV().build_menu_by_urn(name)
    elif mode == 1000:
        RSIPlayTV().build_menu_apiv3(name, mode, page, page_hash)

    xbmcplugin.setContent(int(sys.argv[1]), CONTENT_TYPE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)
