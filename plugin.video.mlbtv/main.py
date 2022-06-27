from resources.lib.mlb import *

params = get_params()
name = None
mode = None
game_day = None
game_pk = None
gid = None
teams_stream = None
stream_date = None
spoiler = 'True'
suspended = 'False'
start_inning = 'False'
blackout = 'False'
icon = None
fanart = None
featured_video = None
description = None

if 'name' in params:
    name = urllib.unquote_plus(params["name"])

if 'mode' in params:
    mode = int(params["mode"])

if 'game_day' in params:
    game_day = urllib.unquote_plus(params["game_day"])

if 'game_pk' in params:
    game_pk = urllib.unquote_plus(params["game_pk"])

if 'teams_stream' in params:
    teams_stream = urllib.unquote_plus(params["teams_stream"])

if 'stream_date' in params:
    stream_date = urllib.unquote_plus(params["stream_date"])

if 'spoiler' in params:
    spoiler = urllib.unquote_plus(params["spoiler"])

if 'suspended' in params:
    suspended = urllib.unquote_plus(params["suspended"])

if 'icon' in params:
    icon = urllib.unquote_plus(params["icon"])

if 'fanart' in params:
    fanart = urllib.unquote_plus(params["fanart"])

if 'start_inning' in params:
    start_inning = urllib.unquote_plus(params["start_inning"])

if 'blackout' in params:
    blackout = urllib.unquote_plus(params["blackout"])

if 'featured_video' in params:
    featured_video = urllib.unquote_plus(params["featured_video"])

if 'description' in params:
    description = urllib.unquote_plus(params["description"])

# default addon home screen
if mode is None:
    # autoplay fav team, if that setting is enabled and a live broadcast is in progress
    if AUTO_PLAY_FAV == 'true' and FAV_TEAM != 'None':
        live_game = live_fav_game()
        if live_game is not None:
            xbmc.log('Auto-playing live game ' + str(live_game))
            xbmc.executebuiltin('PlayMedia("plugin://plugin.video.mlbtv/?mode=102&game_pk='+str(live_game)+'")')
            xbmcplugin.endOfDirectory(addon_handle)
    # if no autoplay, show the main options
    categories()

# Today's Games
elif mode == 100:
    todays_games(None, start_inning)

# Prev and Next
elif mode == 101:
    todays_games(game_day, start_inning)

# autoplay, use an extra parameter to force auto stream selection
elif mode == 102:
    stream_select(game_pk, spoiler, suspended, start_inning, blackout, description, name, icon, fanart, autoplay=True)

# from context menu, use an extra parameter to force manual stream selection
elif mode == 103:
    stream_select(game_pk, spoiler, suspended, start_inning, blackout, description, name, icon, fanart, from_context_menu=True)

# normal stream selection
elif mode == 104:
    stream_select(game_pk, spoiler, suspended, start_inning, blackout, description, name, icon, fanart)

# Yesterday's Games
elif mode == 105:
    todays_games(yesterdays_date(), start_inning)

# highlights from context menu
elif mode == 106:
    list_highlights(game_pk, icon, fanart)

# play all highlights for game from context menu
elif mode == 107:
    play_all_highlights_for_game(game_pk, fanart)

# see yesterday's scores at inning
elif mode == 108:
    start_inning = 'False'
    dialog = xbmcgui.Dialog()
    innings = []
    # show inning options from 1 to 12
    for x in range(1, 13):
        innings.append(LOCAL_STRING(30407) + ' ' + str(x))
    n = dialog.select(LOCAL_STRING(30413), innings)
    if n > -1:
        start_inning = (n + 1)
    game_day = yesterdays_date()
    # Refresh will erase history, so navigating back won't bring up the inning prompt again
    xbmc.executebuiltin('Container.Refresh("plugin://plugin.video.mlbtv/?mode=101&game_day='+game_day+'&start_inning='+str(start_inning)+'")')

# Goto Date
elif mode == 200:
    search_txt = ''
    dialog = xbmcgui.Dialog()
    game_day = dialog.input('Enter date (yyyy-mm-dd)', type=xbmcgui.INPUT_ALPHANUM)
    mat = re.match('(\d{4})-(\d{2})-(\d{2})$', game_day)
    if mat is not None:
        # Refresh will erase history, so navigating back won't bring up the date prompt again
        xbmc.executebuiltin('Container.Refresh("plugin://plugin.video.mlbtv/?mode=101&game_day='+game_day+'&start_inning='+str(start_inning)+'")')
    else:
        if game_day != '':
            dialog = xbmcgui.Dialog()
            dialog.ok(LOCAL_STRING(30365),LOCAL_STRING(30366))

        sys.exit()

# Featured Videos
elif mode == 300:
    featured_videos(featured_video)

# Featured stream select
elif mode == 301:
    featured_stream_select(featured_video, name, description)

# Logout
elif mode == 400:
    account = Account()
    account.logout()
    dialog = xbmcgui.Dialog()
    dialog.notification(LOCAL_STRING(30260), LOCAL_STRING(30261), ICON, 5000, False)

# play all recaps or condensed games for selected date
elif mode == 900:
    playAllHighlights(stream_date)

elif mode == 999:
    sys.exit()

# don't cache today's games or addon home screen
if mode == 100 or (mode is None and AUTO_PLAY_FAV == 'true' and FAV_TEAM != 'None'):
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
# also don't cache previous/next days
elif mode == 101:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)
