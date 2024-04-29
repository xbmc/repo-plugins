from resources.lib.nhl_tv import *

params = get_params()
url = None
name = None
mode = None
game_day = None
stream_ids = None
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
if "stream_ids" in params:
    stream_ids = ast.literal_eval(params["stream_ids"])
if "highlight_id" in params:
    highlight_id = urllib.unquote_plus(params["highlight_id"])


if mode is None or url is None:
    categories()

elif mode == 100 or mode == 101:
    todays_games(game_day)

elif mode == 104:
    stream_select(stream_ids, highlight_id)

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
