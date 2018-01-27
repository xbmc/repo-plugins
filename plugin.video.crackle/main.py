from resources.lib.globals import *

params = get_params()
media_id = None
name = None
mode = None
stream_type = None

try:
    media_id=urllib.unquote_plus(params["id"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    stream_type=urllib.unquote_plus(params["type"])
except:
    pass

if mode is None:
    main_menu()

elif mode == 100:
    list_shows()

elif mode == 101:
    list_movies()

elif mode == 102:
    get_episodes(media_id)

elif mode == 103:
    if stream_type == "movies": media_id = get_movie_id(media_id)
    get_stream(media_id)


xbmcplugin.endOfDirectory(addon_handle)