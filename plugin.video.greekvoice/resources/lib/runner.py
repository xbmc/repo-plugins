#  Greek Voice Add-on
#  Author: threshold84
#  SPDX-License-Identifier: GPL-3.0
#  See LICENSES/GPL-3.0 for more information.

import os
import sys

import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
from .url_dispatcher import urldispatcher
from .scrapetube import wrapper
from urllib.parse import quote_plus

__addon__ = xbmcaddon.Addon()
__lang__ = __addon__.getLocalizedString
__handle__ = int(sys.argv[1])


ADDON_ID = __addon__.getAddonInfo('id')
HOME = xbmcvfs.translatePath(__addon__.getAddonInfo('path'))
ART_FOLDER = os.path.join(HOME, "resources", "art")
ICON = os.path.join(ART_FOLDER, 'icon.png')
FANART = os.path.join(ART_FOLDER, 'fanart.jpg')

GREEK_VOICE_URL_1 = 'http://65.108.62.57:8080/live/greektv1.m3u8'
GREEK_VOICE_URL_2 = 'http://wpso.com:1936/hls/wzra.m3u8'
TILEMOUSIKI_URL_1 = 'http://65.108.62.57:8080/live/greekmusic.m3u8'
TILEMOUSIKI_URL_2 = 'http://wpso.com:1936/hls/music.m3u8'
CARTOONS_URL_1 = 'http://65.108.62.57:8080/live/kidshd.m3u8'
CARTOONS_URL_2 = 'http://wpso.com:1936/hls/kidshd.m3u8'
WPSO_GREEK_VOICE_RADIO_URL = 'http://wpso.com:8000/'
WXYB_RADIO_GR_IT_ES = 'http://wpso.com:7071/'
XAMOS_URL = 'http://xamosam.com:9050'
YT_CHANNEL_URL = 'https://www.youtube.com/@GreekVoiceTV/'


@urldispatcher.register('root')
def root():

    menu = [
        {
            'title': __lang__(30001),
            'icon': os.path.join(ART_FOLDER, 'video_streams.jpg'),
            'fanart': os.path.join(ART_FOLDER, 'video_streams.jpg'),
            'kind': 'video'
        }
        ,
        {
            'title': __lang__(30002),
            'icon': os.path.join(ART_FOLDER, 'radio_streams.jpg'),
            'fanart': os.path.join(ART_FOLDER, 'radio_fanart.jpg'),
            'kind': 'audio'
        }
        ,
        {
            'title': __lang__(30003),
            'icon': os.path.join(ART_FOLDER, 'youtube.jpg'),
            'fanart': FANART,
            'kind': 'youtube'
        }
    ]

    for m in menu:
        list_item = xbmcgui.ListItem(m['title'])
        list_item.setArt({'icon': m['icon'], 'thumb': m['icon'], 'fanart': m['fanart']})
        url = 'plugin://{0}/?action={1}&kind={2}'.format(ADDON_ID, 'directory', m['kind'])
        xbmcplugin.addDirectoryItem(__handle__, url, list_item, True)

    xbmcplugin.endOfDirectory(__handle__, True)


@urldispatcher.register('directory', ['kind'])
def directory(kind=None):

    if kind == 'video':

        menu = [
            {
                'title': ' '.join(['Greek Voice', __lang__(30005).format('1')]),
                'icon': ICON,
                'fanart': os.path.join(ART_FOLDER, 'greek_voice_fanart_1.jpg'),
                'url': GREEK_VOICE_URL_1
            }
            ,
            {
                'title': ' '.join(['Greek Voice', __lang__(30005).format('2')]),
                'icon': ICON,
                'fanart': os.path.join(ART_FOLDER, 'greek_voice_fanart_2.jpg'),
                'url': GREEK_VOICE_URL_2
            }
            ,
            {
                'title': ' '.join([__lang__(30004), __lang__(30005).format('1')]),
                'icon': os.path.join(ART_FOLDER, 'tilemousiki.jpg'),
                'fanart': os.path.join(ART_FOLDER, 'tilemousiki_fanart.jpg'),
                'url': TILEMOUSIKI_URL_1
            }
            ,
            {
                'title': ' '.join([__lang__(30004), __lang__(30005).format('2')]),
                'icon': os.path.join(ART_FOLDER, 'tilemousiki.jpg'),
                'fanart': os.path.join(ART_FOLDER, 'tilemousiki_fanart.jpg'),
                'url': TILEMOUSIKI_URL_2
            }
            ,
            {
                'title': ' '.join(['Greek Kids', __lang__(30005).format('1')]),
                'icon': os.path.join(ART_FOLDER, 'greek_kids.jpg'),
                'fanart': FANART,
                'url': CARTOONS_URL_1
            }
            ,
            {
                'title': ' '.join(['Greek Kids', __lang__(30005).format('2')]),
                'icon': os.path.join(ART_FOLDER, 'greek_kids.jpg'),
                'fanart': FANART,
                'url': CARTOONS_URL_2
            }
        ]

    elif kind == 'audio':

        menu = [
            {
                'title': 'WPSO Greek Voice Radio',
                'icon': os.path.join(ART_FOLDER, 'wpso.jpg'),
                'fanart': os.path.join(ART_FOLDER, 'radio_fanart.jpg'),
                'url': WPSO_GREEK_VOICE_RADIO_URL
            }
            ,
            {
                'title': 'WXYB Radio GR IT ES',
                'icon': os.path.join(ART_FOLDER, 'wxyb.jpg'),
                'fanart': os.path.join(ART_FOLDER, 'radio_fanart.jpg'),
                'url': WXYB_RADIO_GR_IT_ES
            }
            ,
            {
                'title': 'XAMOS Youth Radio',
                'icon': os.path.join(ART_FOLDER, 'xamos.jpg'),
                'fanart': os.path.join(ART_FOLDER, 'xamos_fanart.jpg'),
                'url': XAMOS_URL
            }
        ]

    elif kind == 'youtube':

        menu = wrapper.list_channel_videos(channel_url=YT_CHANNEL_URL, limit=50)

    else:

        return

    # noinspection PyUnboundLocalVariable
    for m in menu:
        list_item = xbmcgui.ListItem(m['title'])
        if kind == 'youtube':
            thumb = m['image']
            fanart = FANART
        else:
            thumb = m['icon']
            fanart = m['fanart']
        list_item.setArt({'icon': thumb, 'thumb': thumb, 'fanart': fanart})
        if kind == 'audio':
            list_item.setInfo(type="music", infoLabels={"title": m['title']})
        else:
            list_item.setInfo(type="video", infoLabels={"title": m['title']})
        list_item.setProperty('IsPlayable', 'true')
        url = 'plugin://{0}/?action={1}&url={2}&icon={3}'.format(
            ADDON_ID, 'play', quote_plus(m['url']), quote_plus(thumb)
        )
        xbmcplugin.addDirectoryItem(__handle__, url, list_item, False)

    xbmcplugin.endOfDirectory(__handle__, True)


@urldispatcher.register('play', ['url', 'icon'])
def play(url, icon):

    list_item = xbmcgui.ListItem(offscreen=True)
    list_item.setArt({'thumb': icon})
    list_item.setPath(url)
    xbmcplugin.setResolvedUrl(__handle__, True, list_item)
