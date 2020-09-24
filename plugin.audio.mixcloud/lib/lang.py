# -*- coding: utf-8 -*-

'''
@author: jackyNIX

Copyright (C) 2011-2020 jackyNIX

This file is part of KODI Mixcloud Plugin.

KODI Mixcloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

KODI Mixcloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with KODI Mixcloud Plugin.  If not, see <http://www.gnu.org/licenses/>.
'''



import xbmcaddon



__addon__ = xbmcaddon.Addon('plugin.audio.mixcloud')



class Lang:
    # main menu (301xx)
    PROFILE = __addon__.getLocalizedString(30100)
    FOLLOWINGS = __addon__.getLocalizedString(30101)
    FOLLOWERS = __addon__.getLocalizedString(30102)
    FAVORITES = __addon__.getLocalizedString(30103)
    UPLOADS = __addon__.getLocalizedString(30104)
    PLAYLISTS = __addon__.getLocalizedString(30105)
    LISTEN_LATER = __addon__.getLocalizedString(30106)
    CATEGORIES = __addon__.getLocalizedString(30107)
    HISTORY = __addon__.getLocalizedString(30108)
    SEARCH = __addon__.getLocalizedString(30109)
    MORE = __addon__.getLocalizedString(30110)

    # search menu (302xx)
    SEARCH_FOR_CLOUDCASTS = __addon__.getLocalizedString(30200)
    SEARCH_FOR_USERS = __addon__.getLocalizedString(30201)

    # context menu items (303xx)
    ADD_TO_FAVORITES = __addon__.getLocalizedString(30300)
    REMOVE_FROM_FAVORITES = __addon__.getLocalizedString(30301)
    ADD_TO_FOLLOWINGS = __addon__.getLocalizedString(30302)
    REMOVE_FROM_FOLLOWINGS = __addon__.getLocalizedString(30303)
    ADD_TO_LISTEN_LATER = __addon__.getLocalizedString(30304)
    REMOVE_FROM_LISTEN_LATER = __addon__.getLocalizedString(30305)

    # others (304xx)
    TOKEN_ERROR = __addon__.getLocalizedString(30400)
    ENTER_OATH_CODE = __addon__.getLocalizedString(30401) 
    ASK_PROFILE_LOGOUT = __addon__.getLocalizedString(30402)
    ASK_CLEAR_HISTORY = __addon__.getLocalizedString(30403)
    NO_ACTIVE_RESOLVERS = __addon__.getLocalizedString(30404)

    # settings (309xx)