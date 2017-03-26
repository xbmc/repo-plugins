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


def authenticate(mls):
    """
    Authenticate with the MLS service. This method pops up an error if
    authentication fails
    @return an MLS Live object
    """
    progress = xbmcgui.DialogProgress()
    progress.create(__language__(30026), __language__(30027))
    
    # get the user name
    username = __settings__.getSetting("username")
    if len(username) == 0:
        progress.close()
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30000), __language__(30001))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return False

    # get the password
    password = __settings__.getSetting("password")
    if len(password) == 0:
        progress.close()
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30002), __language__(30003))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return False

    cookie_file = mls.getCookieFile()
    if os.path.isfile(cookie_file):
        os.remove(cookie_file)

    progress.update(50)
    auth_res = mls.login(username, password, xff)
    progress.close()
 
    if not auth_res:
        progress.close()
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30004), __language__(30005))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return False

    return True


def playGame(values, selected_media = None):
    """
    Play a game.
    @param values the dictionary containing game details
    @param selected_media used to recursively call playGame on reauthentication.
           prevents user from having to reselect condensed or full match.
    """
    title = values['title'][0]
    game = values['game'][0]

    mls = mlslive.MLSLive()
    medias = mls.getStreams(game, xff)

    if medias == None:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30015), __language__(30016))
        return False

    names = []
    for media in medias:
        names.append(media['name'])

    if not selected_media == None:
        media = selected_media 
    elif len(names) > 1:
        index = xbmcgui.Dialog().select("Select Stream", names)
        if index < 0:
            return False
        media = medias[index]
    else:
        media = medias[0]

    try:
        streams = mls.getStreamURIs(media, xff)
    except RuntimeError as ex:
        err = str(ex)
        print "Error getting stream URIs: '{0}'".format(err)
        if err == 'blackout':
            xbmcgui.Dialog().ok(__language__(30016), __language__(30025))
            return False
        elif err[:12] == 'access-token':
            if authenticate(mls):
                return playGame(values, media)
            else:
                return False

    if streams == None:
        xbmcgui.Dialog().ok(__language__(30016), __language__(30006))
        return False

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
    if clubs == None:
        xbmcgui.Dialog().ok(__language__(30028),__language__(30028))
        return

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

def logout():
    mls = mlslive.MLSLive()
    mls.deleteAccesstoken()
    xbmcgui.Dialog().notification(__language__(30029),__language__(30030),
                                  xbmcgui.NOTIFICATION_INFO)
# handle favorite teams from the configuration
if sys.argv[1] == 'favorite':
    favoriteTeam()
    sys.exit(0)
if sys.argv[1] == 'logout':
    logout()
    sys.exit(0)

# handle normal plugin operations
values = urlparse.parse_qs(sys.argv[2][1:])
if 'game' in values.keys():
    if not playGame(values):
        sys.exit(0)
elif 'id' in values.keys():
    game_id = values['id'][0]
    if game_id == 'live':
        createGamesMenu()
    elif game_id == 'complete':
        dt = None
        if 'offset' in values.keys():
            dt = values['offset'][0]
        createGamesMenu(complete=True, offset=dt)
else:
    mls = mlslive.MLSLive()
    token = mls.getAccessToken()
    if token == None:
        if not authenticate(mls):
            sys.exit(0)

    createMainMenu()