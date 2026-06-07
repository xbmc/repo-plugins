# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for MiLB.TV compatibility and code cleanup

from resources.lib.milb import *

params = get_params()
mode = None
game_day = None
level = None
teams = None
game_pk = None
spoiler = 'True'
suspended = 'False'
start_inning = 'False'
status = 'Preview'

if 'mode' in params:
    mode = int(params["mode"])

if 'game_day' in params:
    game_day = urllib.unquote_plus(params["game_day"])

if 'level' in params:
    level = urllib.unquote_plus(params["level"])

if 'teams' in params:
    teams = urllib.unquote_plus(params["teams"])

if 'game_pk' in params:
    game_pk = urllib.unquote_plus(params["game_pk"])

if 'spoiler' in params:
    spoiler = urllib.unquote_plus(params["spoiler"])

if 'suspended' in params:
    suspended = urllib.unquote_plus(params["suspended"])

if 'start_inning' in params:
    start_inning = urllib.unquote_plus(params["start_inning"])

if 'status' in params:
    status = urllib.unquote_plus(params["status"])

# default addon home screen
if mode is None:
    categories()

# by level
elif mode >= 11 and mode <= 14:
    todays_games(game_day, start_inning, str(mode))

# all levels
elif mode == 17:
    todays_games(game_day, start_inning, ALL_LEVELS)

# by affiliate
elif mode == 18:
    todays_games(game_day, start_inning, ALL_LEVELS, teams)

# level select
elif mode == 100:
    levels(game_day, start_inning)

# Prev and Next
elif mode == 101:
    todays_games(game_day, start_inning, level, teams)

# stream selection
elif mode == 104:
    stream_select(game_pk, spoiler, suspended, start_inning, status)

# Yesterday's Games
elif mode == 105:
    levels(yesterdays_date(), start_inning)

# see yesterday's scores at inning
elif mode == 108:
    start_inning = 'False'
    dialog = xbmcgui.Dialog()
    innings = []
    # show inning options from 1 to 12
    for x in range(1, 13):
        innings.append(LOCAL_STRING(30421) + ' ' + str(x))
    n = dialog.select(LOCAL_STRING(30424), innings)
    if n > -1:
        start_inning = (n + 1)
    game_day = yesterdays_date()
    # Refresh will erase history, so navigating back won't bring up the inning prompt again
    xbmc.executebuiltin('Container.Refresh("plugin://plugin.video.milbtv/?mode=100&game_day='+game_day+'&start_inning='+str(start_inning)+'")')

# Goto Date
elif mode == 200:
    search_txt = ''
    dialog = xbmcgui.Dialog()
    game_day = dialog.input(LOCAL_STRING(30404), type=xbmcgui.INPUT_ALPHANUM)
    mat = re.match('(\d{4})-(\d{2})-(\d{2})$', game_day)
    if mat is not None:
        # Refresh will erase history, so navigating back won't bring up the date prompt again
        xbmc.executebuiltin('Container.Refresh("plugin://plugin.video.milbtv/?mode=100&game_day='+game_day+'&start_inning='+str(start_inning)+'")')
    else:
        if game_day != '':
            dialog = xbmcgui.Dialog()
            dialog.ok(LOCAL_STRING(30401), LOCAL_STRING(30400))

        sys.exit()

# Logout
elif mode == 400:
    account = Account()
    account.logout()
    dialog = xbmcgui.Dialog()
    dialog.notification(LOCAL_STRING(30402), LOCAL_STRING(30403), ICON, 5000, False)

elif mode == 999:
    sys.exit()

# don't cache today's games
if mode is not None and mode >= 11 and mode <= 18:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 101:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)
