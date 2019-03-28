# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' This is the actual VRT Nu video plugin entry point '''

from __future__ import absolute_import, division, unicode_literals

import sys

import xbmcaddon
from resources.lib.kodiwrappers import kodiwrapper
from resources.lib.vrtplayer import actions, streamservice, tokenresolver, vrtapihelper, vrtplayer

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

_ADDON_URL = sys.argv[0]
_ADDON_HANDLE = int(sys.argv[1])


def router(params_string):
    ''' This is the main router for the video plugin menu '''
    addon = xbmcaddon.Addon()
    kodi_wrapper = kodiwrapper.KodiWrapper(_ADDON_HANDLE, _ADDON_URL, addon)
    token_resolver = tokenresolver.TokenResolver(kodi_wrapper)
    stream_service = streamservice.StreamService(vrtplayer.VRTPlayer.VRT_BASE,
                                                 vrtplayer.VRTPlayer.VRTNU_BASE_URL,
                                                 kodi_wrapper, token_resolver)
    api_helper = vrtapihelper.VRTApiHelper(kodi_wrapper)
    vrt_player = vrtplayer.VRTPlayer(addon.getAddonInfo('path'), kodi_wrapper, stream_service, api_helper)
    params = dict(parse_qsl(params_string))
    action = params.get('action')
    if action == actions.LISTING_AZ_TVSHOWS:
        vrt_player.show_tvshow_menu_items('az')
    elif action == actions.LISTING_CATEGORIES:
        vrt_player.show_category_menu_items()
    elif action == actions.LISTING_LIVE:
        vrt_player.show_livestream_items()
    elif action == actions.LISTING_EPISODES:
        vrt_player.show_episodes(params.get('video_url'))
    elif action == actions.LISTING_CATEGORY_TVSHOWS:
        vrt_player.show_tvshow_menu_items(params.get('video_url'))
    elif action == actions.PLAY:
        video = dict(
            video_url=params.get('video_url'),
            video_id=params.get('video_id'),
            publication_id=params.get('publication_id'),
        )
        vrt_player.play(video)
    else:
        vrt_player.show_main_menu_items()


if __name__ == '__main__':
    router(sys.argv[2][1:])
