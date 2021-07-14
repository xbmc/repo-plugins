# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for MiLB.TV compatibility and code cleanup

from resources.lib.milb import *

params = get_params()
mode = None
game_day = None
level = None
game_pk = None

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

if mode is None:
    categories()

elif (mode != None) and (mode >= 11) and (mode <= 14):
    todays_games(game_day, str(mode))

elif mode == 17:
    todays_games(game_day, '11,12,13,14')

elif mode == 18:
    todays_games(game_day, '11,12,13,14', teams)

elif mode == 100:
    levels(game_day)

elif mode == 101:
    # Prev and Next
    todays_games(game_day, level, teams)

elif mode == 104:
    stream_select(game_pk)

elif mode == 105:
    # Yesterday's Games
    game_day = localToEastern()
    display_day = stringToDate(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)
    game_day = prev_day.strftime("%Y-%m-%d")
    levels(game_day)

elif mode == 200:
    # Goto Date
    search_txt = ''
    dialog = xbmcgui.Dialog()
    game_day = dialog.input(LOCAL_STRING(30404), type=xbmcgui.INPUT_ALPHANUM)
    mat = re.match('(\d{4})-(\d{2})-(\d{2})$', game_day)
    if mat is not None:
        levels(game_day)
    else:
        if game_day != '':
            msg = LOCAL_STRING(30400)
            dialog = xbmcgui.Dialog()
            dialog.ok(LOCAL_STRING(30401), msg)

        sys.exit()

elif mode == 400:
    account = Account()
    account.logout()
    dialog = xbmcgui.Dialog()
    title = LOCAL_STRING(30402)
    dialog.notification(title, LOCAL_STRING(30403), ICON, 5000, False)

elif mode == 999:
    sys.exit()

if (mode != None) and (mode >= 11) and (mode <= 17):
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 101:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)
