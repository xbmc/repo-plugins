import sys
import xbmcaddon
from urlparse import parse_qsl
from resources.lib.vrtplayer import vrtplayer
from resources.lib.kodiwrappers import kodiwrapper
from resources.lib.vrtplayer import actions
from resources.lib.kodiwrappers import sortmethod
from resources.lib.vrtplayer import urltostreamservice

_url = sys.argv[0]
_handle = int(sys.argv[1])


def router(params_string):
    addon = xbmcaddon.Addon()
    kodi_wrapper = kodiwrapper.KodiWrapper(_handle, _url, addon)
    stream_service = urltostreamservice.UrlToStreamService(vrtplayer.VRTPlayer._VRT_BASE,
                                                           vrtplayer.VRTPlayer._VRTNU_BASE_URL,
                                                           kodi_wrapper)
    vrt_player = vrtplayer.VRTPlayer(addon.getAddonInfo("path"), kodi_wrapper, stream_service)
    params = dict(parse_qsl(params_string))
    if params:
        if params['action'] == actions.LISTING_AZ:
            vrt_player.show_az_menu_items()
        elif params['action'] == actions.LISTING_CATEGORIES:
            vrt_player.show_category_menu_items()
        elif params['action'] == actions.LISTING_LIVE:
            vrt_player.show_livestream_items()
        elif params['action'] == actions.LISTING_VIDEOS:
            vrt_player.show_videos(params['video'])
        elif params['action'] == actions.LISTING_CATEGORY_VIDEOS:
            vrt_player.show_video_category_episodes(params['video'])
        elif params['action'] == actions.PLAY:
            vrt_player.play_vrtnu_video(params['video'])
        elif params['action'] == actions.PLAY_LIVE:
            vrt_player.play_livestream(params['video'])
    else:
        vrt_player.show_main_menu_items()

if __name__ == '__main__':
    router(sys.argv[2][1:])

