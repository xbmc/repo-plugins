import sys
import xbmcaddon
from resources.lib.kodiwrapper import kodiwrapper
from resources.lib.yelo import yelo

if sys.version_info[0] == 3:
    from urllib.parse import parse_qsl
else:
    from urlparse import parse_qsl

from resources.lib.enums.enums import protocols

# Get the plugin url in plugin:// notation.
__url__ = sys.argv[0]
# Get the plugin handle as an integer number.
__handle__ = int(sys.argv[1])

# Get the plugin addon.
__addon__ = xbmcaddon.Addon()

def router(paramstring):
    kodi_wrapper = kodiwrapper.KodiWrapper(__handle__, __url__, __addon__)
    yelo_player = yelo.YeloPlay(kodi_wrapper, protocols.DASH)

    params = dict(parse_qsl(paramstring[1:]))

    if params:
        if params['action'] == 'listing' and params['category'] == 'livestreams':
            data = yelo_player.fetch_channel_list()
            if data:
                yelo_player.list_channels(data)

        elif params['action'] == 'play':
            stream_url = yelo_player.select_manifest_url(params['livestream'])
            if stream_url:
                yelo_player.play_live_stream(stream_url)
    else:
        if yelo_player.login():
            yelo_player.display_main_menu()



if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    router(sys.argv[2])
