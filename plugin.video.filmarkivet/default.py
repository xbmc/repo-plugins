# -*- coding: utf-8 -*-

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os, sys
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
from lib.filmarkivet import Filmarkivet
import requests

try:
    # Python 3
    from urllib.parse import parse_qs
except ImportError:
    # Python 2
    from urlparse import parse_qs

addon = xbmcaddon.Addon()
ADDON_PATH = addon.getAddonInfo('path')
__translation = addon.getLocalizedString


def view_menu(menu):
    for item in menu:
        title = u'{} | {}'.format(item.title, item.description) if item.description else item.title
        li = xbmcgui.ListItem(title)
        li.setArt({'thumb': item.icon})
        li.setInfo('video', {'title': item.title, 'year': item.year, 'duration': item.duration})
        if item.playable:
            li.setProperty('isplayable', 'true')
            li.setInfo('video', {'plot': item.description})
        xbmcplugin.addDirectoryItem(info.handle, item.url, li, not item.playable)
    xbmcplugin.endOfDirectory(info.handle)


def keyboard_get_string(default, message):
    keyboard = xbmc.Keyboard(default, message)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return keyboard.getText()
    else:
        return None


def show_error():
    error_title = __translation(30002)
    error_message1 = __translation(30003)
    error_message2 = __translation(30004)
    xbmcgui.Dialog().ok(error_title, error_message1, error_message2)


class AddonInfo(object):
    def __init__(self):
        self.name = addon.getAddonInfo('name')
        self.id = addon.getAddonInfo('id')
        self.handle = int(sys.argv[1])
        self.path = sys.argv[0]
        self.icon = os.path.join(addon.getAddonInfo('path'), 'icon.png')
        self.fanart = os.path.join(addon.getAddonInfo('path'), 'fanart.jpg')
        self.trans = addon.getLocalizedString
        self.profile_dir = xbmc.translatePath(addon.getAddonInfo("Profile"))
        self.cache_file = xbmc.translatePath(os.path.join(self.profile_dir, 'requests_cache'))


if (__name__ == "__main__"):
    info = AddonInfo()
    params = parse_qs(sys.argv[2][1:])

    if 'content_type' in params:
        content_type = params['content_type'][0]

    fa = Filmarkivet(info)
    if 'mode' in params:
        try:
            mode = params['mode'][0]
            page = int(params['page'][0]) if 'page' in params else 1
            url = params['url'][0] if 'url' in params else None

            if mode == 'categories':
                view_menu(fa.get_categories())
            if mode == 'category' and url:
                movies = fa.get_url_movies(url, mode='category', page=page, limit=True)
                view_menu(movies)

            if mode == 'letters':
                view_menu(fa.get_letters())
            if mode == 'letter':
                if 'l' in params:
                    view_menu(fa.get_letter_movies(params['l'][0]))

            if mode == 'themes':
                view_menu(fa.get_themes())
            if mode == 'theme' and url:
                movies = fa.get_url_movies(url, mode='theme', page=page, limit=True)
                view_menu(movies)

            if mode == 'watch':
                media_url = fa.get_media_url(requests.utils.unquote(url))
                xbmcplugin.setResolvedUrl(info.handle, True, xbmcgui.ListItem(path=media_url))

            if mode == 'search':
                key = params['key'][0] if 'key' in params else keyboard_get_string('', info.trans(30023))
                movies = fa.get_url_movies('/sokresultat/?q={}'.format(key), mode='search&key={}'.format(key),
                                           page=page, limit=True)
                view_menu(movies)
        except:
            show_error()
    else:
        view_menu(fa.get_mainmenu())
