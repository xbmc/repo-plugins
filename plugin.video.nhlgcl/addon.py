from resources.lib.nhl_tv import *

params = get_params()
url = None
name = None
mode = None
game_day = None
stream1_id = None
stream2_id = None
stream3_id = None
stream1_name = None
stream2_name = None
stream3_name = None
highlight_id = None
teams_stream = None
stream_date = None

if "url" in params:
    url = urllib.unquote_plus(params["url"])
if "name" in params:
    name = urllib.unquote_plus(params["name"])
if "mode" in params:
    mode = int(params["mode"])
if "game_day" in params:
    game_day = urllib.unquote_plus(params["game_day"])
if "stream1_id" in params:
    stream1_id = urllib.unquote_plus(params["stream1_id"])
if "stream2_id" in params:
    stream2_id = urllib.unquote_plus(params["stream2_id"])
if "stream3_id" in params:
    stream3_id = urllib.unquote_plus(params["stream3_id"])
if "stream1_name" in params:
    stream1_name = urllib.unquote_plus(params["stream1_name"])
if "stream2_name" in params:
    stream2_name = urllib.unquote_plus(params["stream2_name"])
if "stream3_name" in params:
    stream3_name = urllib.unquote_plus(params["stream3_name"])
if "highlight_id" in params:
    highlight_id = urllib.unquote_plus(params["highlight_id"])


if mode is None or url is None:
    categories()

elif mode == 100 or mode == 101:
    todays_games(game_day)

elif mode == 104:
    stream_select(stream1_id, stream2_id, stream3_id, stream1_name, stream2_name, stream3_name, highlight_id)

elif mode == 105:
    # Yesterday"s Games
    game_day = local_to_eastern()
    display_day = string_to_date(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)
    todays_games(prev_day.strftime("%Y-%m-%d"))

elif mode == 200:
    goto_date()

elif mode == 400:
    logout("true")

elif mode == 999:
    sys.exit()

if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 101 or mode == 500 or mode == 501 or mode == 510:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)
