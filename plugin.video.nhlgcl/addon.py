from resources.lib.nhl_tv import *

params = get_params()
url = None
name = None
mode = None
game_day = None
game_id = None
epg = None
teams_stream = None
stream_date = None

if 'url' in params:
    url = urllib.unquote_plus(params["url"])
if 'name' in params:
    name = urllib.unquote_plus(params["name"])
if 'mode' in params:
    mode = int(params["mode"])
if 'game_day' in params:
    game_day = urllib.unquote_plus(params["game_day"])
if 'game_id' in params:
    game_id = urllib.unquote_plus(params["game_id"])
if 'epg' in params:
    epg = urllib.unquote_plus(params["epg"])
if 'teams_stream' in params:
    teams_stream = urllib.unquote_plus(params["teams_stream"])
if 'stream_date' in params:
    stream_date = urllib.unquote_plus(params["stream_date"])


if mode is None or url is None:
    categories()

elif mode == 100 or mode == 101:
    todays_games(game_day)

elif mode == 104:
    stream_select(game_id, epg, teams_stream, stream_date)

elif mode == 105:
    # Yesterday's Games
    game_day = local_to_eastern()
    display_day = string_to_date(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)
    todays_games(prev_day.strftime("%Y-%m-%d"))

elif mode == 200:
    goto_date()

elif mode == 300:
    nhl_videos(url)

elif mode == 400:
    logout('true')

elif mode == 500:
    my_teams_games()

elif mode == 510:
    play_fav_team_today()

elif mode == 515:
    get_thumbnails()

elif mode == 900:
    play_all_highlights()

elif mode == 999:
    sys.exit()

if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 101 or mode == 500 or mode == 501 or mode == 510:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)
