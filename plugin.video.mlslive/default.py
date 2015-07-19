'''
@author: Micah Galizia <micahgalizia@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, os, urllib, urlparse, datetime, mlslive

__settings__ = xbmcaddon.Addon(id='plugin.video.mlslive')
__language__ = __settings__.getLocalizedString


GAME_IMAGE_PREFIX = 'http://e2.cdnl3.neulion.com/mls/ced/images/roku/HD/'
MONTH_OFFSET = 30100


def createMainMenu():
    # add the game
    live = xbmcgui.ListItem(__language__(30010))
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=sys.argv[0] + "?" + urllib.urlencode({'id' : 'live'}),
                                listitem=live,
                                isFolder=True)

    live = xbmcgui.ListItem(__language__(30009))
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=sys.argv[0] + "?" + urllib.urlencode({'id' : 'complete'}),
                                listitem=live,
                                isFolder=True)

    # signal the end of the directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def createMonthsMenu(complete = False):

    key = 'compmonth' if complete else 'month'

    # For live games, don't show past months
    start_month = 2
    if not complete:
        start_month = datetime.datetime.now().month

    # add each month in the season
    for i in range(start_month,13):
        values = { key : str(i) }
        li = xbmcgui.ListItem(__language__(MONTH_OFFSET + i))
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + '?' + urllib.urlencode(values),
                                    listitem = li,
                                    isFolder = True)

    # signal the end of the directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def createMonthMenu(month, complete = False):

    mls = mlslive.MLSLive()

    games = mls.getGames(month)
    if games == None:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30018), __language__(30019))
        # signal the end of the directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return None

    for game in games:

        final = False
        if 'result' in game.keys():
            if game['result'] == 'F':
                final = True

        # skip any finished games if showing live or upcomming
        if final and not complete:
            continue

        # skip if showing completed and live or upcomming
        if complete and not final:
            continue

        title = mls.getGameString(game, __language__(30008))
        li = xbmcgui.ListItem(title)
        values = {'game' : game['id'],
                  'title' : title}

        # if the game has a result pass it along
        if 'result' in game.keys():
            values['result'] = game['result']

        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + '?' + urllib.urlencode(values),
                                    listitem = li,
                                    isFolder = True)

    # signal the end of the directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def createFinalMenu(game, title):

    # full game replay
    li = xbmcgui.ListItem(__language__(30011))
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=sys.argv[0] + '?' + urllib.urlencode({'game' : game,
                                                                          'title' : title}),
                                listitem = li,
                                isFolder = True)

    #condensed game replay
    li = xbmcgui.ListItem(__language__(30012))
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=sys.argv[0] + '?' + urllib.urlencode({'condensed' : game,
                                                                          'title' : title}),
                                listitem = li,
                                isFolder = True)

    # signal the end of the directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def authenticate():
    """
    Authenticate with the MLS service. This method pops up an error if
    authentication fails
    @return an MLS Live object
    """
    # get the user name
    username = __settings__.getSetting("username")
    if len(username) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30000), __language__(30001))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    # get the password
    password = __settings__.getSetting("password")
    if len(password) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30002), __language__(30003))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    # authenticate with MLS live
    my_mls = mlslive.MLSLive()

    cookie_file = my_mls.getCookieFile()
    if os.path.isfile(cookie_file):
        os.remove(cookie_file)

    if not my_mls.login(username, password):
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30004), __language__(30005))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    return my_mls


def playGame(value_string):
    values = urlparse.parse_qs(value_string)
    title = values['title'][0]
    condensed = False
    if 'condensed' in values.keys():
        game = values['condensed'][0]
        condensed = True
    else:
        game = values['game'][0]

    if 'result' in values.keys():
        if values['result'][0] == 'F':
            createFinalMenu(game, title)
            return

    mls = mlslive.MLSLive()
    stream = mls.getGameLiveStream(game, condensed)
    if stream == '':
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30015), __language__(30016))
    else:
        li = xbmcgui.ListItem(title)
        li.setInfo( type="Video", infoLabels={"Title" : title})
        p = xbmc.Player()
        p.play(stream, li)


if len(sys.argv[2]) == 0:
    if not authenticate() == None:
        createMainMenu()
elif sys.argv[2] == '?id=live':
    createMonthsMenu()
elif sys.argv[2] == '?id=complete':
    createMonthsMenu(complete = True)
elif sys.argv[2][:7] == '?month=':
    values = urlparse.parse_qs(sys.argv[2][1:])
    createMonthMenu(values['month'][0])
elif sys.argv[2][:11] == '?compmonth=':
    values = urlparse.parse_qs(sys.argv[2][1:])
    createMonthMenu(values['compmonth'][0], complete = True)
elif sys.argv[2][:10] == "?condensed":
    playGame(sys.argv[2][1:])
elif sys.argv[2][:5] == "?game":
    playGame(sys.argv[2][1:])
