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
import xbmcplugin, xbmcgui, xbmcaddon, urllib, urlparse, mlslive

__settings__ = xbmcaddon.Addon(id='plugin.video.mlslive')
__language__ = __settings__.getLocalizedString


GAME_IMAGE_PREFIX = 'http://e2.cdnl3.neulion.com/mls/ced/images/roku/HD/'


def createFinalMenu(my_mls, values_string):
    """
    Create a menu for games that have already finished
    @param my_mls the MLS live object
    @param values_string the string containing the game id and title
    """
    values = dict(urlparse.parse_qsl(values_string))
    streams = my_mls.getFinalStreams(values['id'])
    
    if (streams == None):
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return
    
    for key in streams.keys():
        title = my_mls.adjustArchiveString(values['title'], key)
        li = xbmcgui.ListItem(title, iconImage=values['image'])
        li.setInfo( type="Video", infoLabels={"Title" : title})
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=streams[key],
                                    listitem=li,
                                    isFolder=False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def createMainMenu(my_mls, values_string):
    """
    Create the main menu consisting of the days games
    @param my_mls the MLS live object
    @param values_string the string containing the week offset from the present
    """
    # get the values -- should just be the week offset
    values = dict(urlparse.parse_qsl(values_string))

    # get the teams
    teams = my_mls.getTeams()
    offset = int(values['week'])

    # add next week
    nli = xbmcgui.ListItem(__language__(30009))
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=sys.argv[0] + "?" + urllib.urlencode({'week' : offset + 1}),
                                listitem=nli,
                                isFolder=True)

    # add previous week
    pli = xbmcgui.ListItem(__language__(30010))
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=sys.argv[0] + "?" + urllib.urlencode({'week' : offset - 1}),
                                listitem=pli,
                                isFolder=True)

    for game in my_mls.getGames(offset):

        # get the pretty title        
        game_str = my_mls.getGameString(game, __language__(30008))

        # get the home/away images
        home = my_mls.getTeamAbbr(teams, game['homeTeamID'])
        vist = my_mls.getTeamAbbr(teams, game['visitorTeamID'])
        game_img = GAME_IMAGE_PREFIX + vist + "_at_" + home + ".jpg";

        li = xbmcgui.ListItem(game_str, iconImage=game_img)

        if my_mls.isGameLive(game):
            stream = my_mls.getGameLiveStream(game['gameID'])

            li.setInfo( type="Video", infoLabels={"Title" : game_str})
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                        url=stream,
                                        listitem=li,
                                        isFolder=False)
        elif my_mls.isGameUpcoming(game):
            li.setInfo( type="Video", infoLabels={"Title" : game_str})
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                        url="",
                                        listitem=li,
                                        isFolder=False)
        else:
            values = { 'image' : game_img,
                       'title' : game_str,
                       'id' : game['gameID'] }
            url = sys.argv[0] + "?" + urllib.urlencode(values);

            li.setInfo( type="Video", infoLabels={"Title" : game_str})
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                        url=url,
                                        listitem=li,
                                        isFolder=True)

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
    if not my_mls.login(username, password):
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30004), __language__(30005))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    return my_mls

my_mls = authenticate()

if my_mls == None:
    print "ERROR: Unable to authenticate"
elif (len(sys.argv[2]) == 0):
    createMainMenu(my_mls, 'week=0')
elif sys.argv[2][:3] == '?id':
    createFinalMenu(my_mls, sys.argv[2][1:])
elif sys.argv[2][:5] == '?week':
    createMainMenu(my_mls, sys.argv[2][1:])
