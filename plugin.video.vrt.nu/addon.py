# -*- coding: utf-8 -*-

# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

''' This is the actual VRT Nu video plugin entry point '''

from __future__ import absolute_import, division, unicode_literals

import sys

import xbmcaddon
from resources.lib.kodiwrappers import kodiwrapper
from resources.lib.vrtplayer import vrtplayer, streamservice, tokenresolver, actions, vrtapihelper

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
    if params:
        if params['action'] == actions.LISTING_AZ_TVSHOWS:
            vrt_player.show_tvshow_menu_items('az')
        elif params['action'] == actions.LISTING_CATEGORIES:
            vrt_player.show_category_menu_items()
        elif params['action'] == actions.LISTING_LIVE:
            vrt_player.show_livestream_items()
        elif params['action'] == actions.LISTING_EPISODES:
            vrt_player.show_episodes(params['video_url'])
        elif params['action'] == actions.LISTING_CATEGORY_TVSHOWS:
            vrt_player.show_tvshow_menu_items(params['video_url'])
        elif params['action'] == actions.PLAY:
            video_id = params['video_id'] if 'video_id' in params else None
            publication_id = params['publication_id'] if  'publication_id' in params else None
            video = {'video_url' : params['video_url'], 'video_id' : video_id,
                     'publication_id' : publication_id}
            vrt_player.play(video)
    else:
        vrt_player.show_main_menu_items()


if __name__ == '__main__':
    router(sys.argv[2][1:])
