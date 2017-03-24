'''
@author: Micah Galizia <micahgalizia@gmail.com>
@todo Don't login every time. Add a login/logout configuration and login
      automatically when there is no token or the token has expired.

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
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import sys, os, urllib, urlparse, time, datetime, mlslive

__settings__ = xbmcaddon.Addon(id='plugin.video.mlslive')
__language__ = __settings__.getLocalizedString

xff = __settings__.getSetting("xff")
if len(xff) == 0:
    xff = None


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


def createGamesMenu(complete = False, offset = None):
    """
    Create the list of game.
    @param complete flag to indicate if we're showing completed games
    @param offset from the current date for which completed games will be shown
    """
    mls = mlslive.MLSLive()
    fav = mls.getFavoriteClub()

    dt = datetime.datetime.now();
    if not offset == None:
        dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(offset, "%c")))

    games = mls.getGames(dt, xff)
    if games == None:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30018), __language__(30019))
        # signal the end of the directory
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return None

    for game in games:

        # Skip completed games in the live menu
        if complete == False and game['period'] == 'FullTime':
            continue
        elif complete and game['period'] != 'FullTime':
            continue

        plot = mls.getDescription(game, __language__(30021),
                                  __language__(30023), __language__(30024))
        infos = { 'genre' : game['competition']['name'],
                  'title' : mls.getFullTitle(game, __language__(30008)),
                  'tvshowtitle' : game['competition']['name'],
                  'plot' : plot,
                  'plotoutline' : plot }
        title = mls.getGameString(game, __language__(30008))
        li = xbmcgui.ListItem(title)
        li.setInfo('video', infos)

        # if an image is available, use it
        img = mls.getImage(game, fav)
        if not img == None:
            li.setIconImage(img)

        values = {'game' : game['optaId'],
                  'title' : title}

        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + '?' + urllib.urlencode(values),
                                    listitem = li,
                                    isFolder = True)
    
    if complete:
        delta = datetime.timedelta(days=7);
        values = {'id' : 'complete',
                  'offset' : (dt - delta).strftime('%c')}
        li = xbmcgui.ListItem(__language__(30020))
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + '?' + urllib.urlencode(values),
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

    if not my_mls.login(username, password, xff):
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30004), __language__(30005))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    return my_mls


def playGame(values):
    """
    @TODO add new language keys
    """
    title = values['title'][0]
    game = values['game'][0]

    mls = mlslive.MLSLive()
    medias = mls.getStreams(game, xff)

    if medias == None:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30015), __language__(30016))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    names = []
    for media in medias:
        names.append(media['name'])

    if len(names) > 1:
        index = xbmcgui.Dialog().select("Select Stream", names)
        if index < 0:
            xbmcplugin.endOfDirectory(int(sys.argv[1]))
            return
        media = medias[index]
    else:
        media = medias[0]
    
    streams = mls.getStreamURIs(media, xff)

    bitrates = [int(x) for x in streams.keys()]
    bitrates = [str(x) for x in reversed(sorted(bitrates)) ]

    index = xbmcgui.Dialog().select("Select Bitrate", bitrates)

    stream = streams[bitrates[index]]

    li = xbmcgui.ListItem(title)
    li.setInfo( type="Video", infoLabels={"Title" : title})
    p = xbmc.Player()
    p.play(stream, li)


def favoriteTeam():
    mls = mlslive.MLSLive()
    clubs = mls.getClubs(xff)

    mls_clubs = {}
    for club in clubs:
        if club['isMLS']:
            mls_clubs[club['name']['full']] = club['id']

    names = sorted(mls_clubs.keys())
    index = xbmcgui.Dialog().select("Select Favorite Team", names)
    if index < 0:
        return

    mls.setFavoriteClub(mls_clubs[names[index]])
    return

# handle favorite teams from the configuration
if sys.argv[1] == 'favorite':
    favoriteTeam()
    sys.exit(0)

# handle normal plugin operations
values = urlparse.parse_qs(sys.argv[2][1:])
if 'game' in values.keys():
    playGame(values)
elif 'id' in values.keys():
    id = values['id'][0]
    if id == 'live':
        createGamesMenu()
    elif id == 'complete':
        dt = None
        if 'offset' in values.keys():
            dt = values['offset'][0]
        createGamesMenu(complete=True, offset=dt)
else:
    if not authenticate() == None:
        createMainMenu()