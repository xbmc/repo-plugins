from resources.lib.ahl_tv import *

params = get_params()
mode = None
game_day = None
game_id = None

if 'mode' in params:
    mode = int(params["mode"])
if 'game_day' in params:
    game_day = quote(params["game_day"])
if 'game_id' in params:
    game_id = quote(params["game_id"])

if mode is None: # or url is None:
    main_menu()

elif mode == 100 or mode == 101:
    daily_games(game_day)

elif mode == 102:
    # Yesterday's Games
    game_day = local_to_eastern()
    display_day = string_to_date(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)
    daily_games(prev_day.strftime("%Y-%m-%d"))

elif mode == 103:
    select_date()

elif mode == 104:
    select_game(game_id)

elif mode == 401:
    logout()

elif mode == 999:
    sys.exit()

#else:
xbmcplugin.endOfDirectory(addon_handle)
