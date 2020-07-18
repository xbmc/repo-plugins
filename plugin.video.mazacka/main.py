# -*- coding: utf-8 -*-
# Module: default
# Author: Radek Homola
# Created on: 13.1.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib import urlencode
from urlparse import parse_qsl
import urllib2
import zlib
import re
import xbmcgui
import xbmcaddon
import xbmcplugin

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
PLUGIN_ID = 'plugin.video.mazacka'
MEDIA_URL = 'special://home/addons/{0}/resources/media/'.format(PLUGIN_ID)
STREAM_URL = 'https://www.mall.tv/embed/vlaky-a-tramvaje/mazacka-jizda-prahou?autoplay=true'
_lang = xbmcaddon.Addon(PLUGIN_ID).getLocalizedString

UTF8 = 'utf-8'
USERAGENT = """Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36"""
httpHeaders = {'User-Agent': USERAGENT,
               'Accept': "application/json, text/javascript, text/html,*/*",
               'Accept-Encoding': 'gzip,deflate,sdch',
               'Accept-Language': 'en-US,en;q=0.8'
}

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def play_video(path):
    if not checkStream(getRequest(STREAM_URL)):
        return
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
        html = getRequest(STREAM_URL)
        if not checkStream(html):
            return
        try:
            out = re.findall(r'<source src=(.+?)\s', html)[0]
        except Exception:
            raise ValueError('Stream URL not found!')
            return
        res = ['1080', '720', '360']
        fanart = 'special://home/addons/{0}/fanart.jpg'.format(PLUGIN_ID)
        xbmcplugin.setContent(_handle, 'movies')
        for r in res:
          list_item = xbmcgui.ListItem(label=r + 'p')
          list_item.setInfo('video', {'title': 'Mazačka ' + r + 'p', 'mediatype': 'video', 'plot': _lang(30000 + int(r))})
          list_item.setArt({'thumb': MEDIA_URL + 'icon' + r + '.png', 'fanart': fanart, 'icon': MEDIA_URL + 'icon' + r + '.png'})
          list_item.setProperty('IsPlayable', 'true')
          is_folder = False
          xbmcplugin.addDirectoryItem(_handle, get_url(action='play', video=out + r + '/index.m3u8'), list_item, is_folder)
        xbmcplugin.endOfDirectory(_handle)

def getRequest(url, udata=None, headers=httpHeaders):
    req = urllib2.Request(url.encode(UTF8), udata, headers)
    try:
        response = urllib2.urlopen(req)
        page = response.read()
        if response.info().getheader('Content-Encoding') == 'gzip':
            page = zlib.decompress(page, zlib.MAX_WBITS + 16)
        response.close()
    except Exception:
        page = ""
    return(page)
    
def checkStream(html):
    if html == '':
        xbmcgui.Dialog().ok(PLUGIN_ID, _lang(30003))
        return(False)
    if html.find('bude brzy') != -1:
        xbmcgui.Dialog().ok(PLUGIN_ID, _lang(30002))
        return(False)
    return(True)


if __name__ == '__main__':
    router(sys.argv[2][1:])
