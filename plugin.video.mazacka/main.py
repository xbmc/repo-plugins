# -*- coding: utf-8 -*-
# Module: default
# Author: Radek Homola
# Created on: 13.1.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmcgui
import xbmcaddon
import xbmcplugin

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
PLUGIN_ID = 'plugin.video.mazacka'
MEDIA_URL = 'special://home/addons/{0}/resources/media/'.format(PLUGIN_ID)
_lang = xbmcaddon.Addon(PLUGIN_ID).getLocalizedString

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def play_video(path):
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'play':
            play_video(params['video'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        fanart = 'special://home/addons/{0}/fanart.jpg'.format(PLUGIN_ID)
        xbmcplugin.setContent(_handle, 'movies')
        list_item = xbmcgui.ListItem(label='720p')
        list_item.setInfo('video', {'title': 'Mazačka 720p', 'mediatype': 'video', 'plot': _lang(30000)})
        list_item.setArt({'thumb': MEDIA_URL + 'icon720.png', 'fanart': fanart, 'icon': MEDIA_URL + 'icon720.png'})
        list_item.setProperty('IsPlayable', 'true')
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, get_url(action='play', video='http://live.idnes.cz/slow/slowtv7_720p/playlist.m3u8'), list_item, is_folder)
        list_item = xbmcgui.ListItem(label='360p')
        list_item.setInfo('video', {'title': 'Mazačka 360p', 'mediatype': 'video', 'plot': _lang(30001)})
        list_item.setArt({'thumb': MEDIA_URL + 'icon360.png', 'fanart': fanart, 'icon': MEDIA_URL + 'icon360.png'})
        list_item.setProperty('IsPlayable', 'true')
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, get_url(action='play', video='http://live.idnes.cz/slow/slowtv7_360p/playlist.m3u8'), list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)


if __name__ == '__main__':
    router(sys.argv[2][1:])
