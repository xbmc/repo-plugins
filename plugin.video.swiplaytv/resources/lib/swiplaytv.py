# -*- coding: utf-8 -*-

# Copyright (C) 2022 Alexander Seiler
#
#
# This file is part of plugin.video.swiplaytv.
#
# plugin.video.swiplaytv is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# plugin.video.swiplaytv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with plugin.video.swiplaytv.
# If not, see <http://www.gnu.org/licenses/>.

import sys
import traceback

from urllib.parse import unquote_plus
from urllib.parse import parse_qsl

import xbmc
import xbmcaddon
import xbmcplugin
import srgssr

ADDON_ID = 'plugin.video.swiplaytv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
DEBUG = (REAL_SETTINGS.getSetting('Enable_Debugging') == 'true')
CONTENT_TYPE = 'videos'


class SWIPlayTV(srgssr.SRGSSR):
    def __init__(self):
        super(SWIPlayTV, self).__init__(
            int(sys.argv[1]), bu='swi', addon_id=ADDON_ID)


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

    log('Mode: ' + str(mode))
    log('URL : ' + str(url))
    log('Name: ' + str(name))
    log('Page Hash: ' + str(page_hash))
    log('Page: ' + str(page))

    if mode is None:
        identifiers = [
            'Homepage',
            'Topics',
            'Search',
            'SWI_YouTube'
        ]
        SWIPlayTV().build_main_menu(identifiers)
    elif mode == 13:
        SWIPlayTV().build_topics_menu()
    elif mode == 21:
        SWIPlayTV().build_episode_menu(name)
    elif mode == 27:
        SWIPlayTV().build_search_menu()
    elif mode == 28:
        SWIPlayTV().build_search_media_menu(
            mode=mode, name=name, page=page, page_hash=page_hash)
    elif mode == 70:
        SWIPlayTV().build_recent_search_menu()
    elif mode == 30:
        SWIPlayTV().build_youtube_channel_overview_menu(33)
    elif mode == 33:
        SWIPlayTV().build_youtube_channel_menu(
            name, mode, page=page, page_token=page_hash)
    elif mode == 50:
        SWIPlayTV().play_video(name)
    elif mode == 100:
        SWIPlayTV().build_menu_by_urn(name)
    elif mode == 200:
        SWIPlayTV().build_homepage_menu()
    elif mode == 1000:
        SWIPlayTV().build_menu_apiv3(name, mode, page, page_hash)

    xbmcplugin.setContent(int(sys.argv[1]), CONTENT_TYPE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)
