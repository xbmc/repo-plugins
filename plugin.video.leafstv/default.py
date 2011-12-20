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

import xbmcplugin, xbmcgui, xbmcaddon
import urllib, re, time
from LeafsTV import LeafsTV, LeafsTVError
from time import strftime
from xbmc import Player

__settings__ = xbmcaddon.Addon(id='plugin.video.leafstv')
__language__ = __settings__.getLocalizedString

team_images = {"ANA" : "http://1.cdn.nhle.com/ducks/images/logos/extralarge.png",
               "BOS" : "http://1.cdn.nhle.com/bruins/images/logos/extralarge.png",
               "BUF" : "http://1.cdn.nhle.com/sabres/images/logos/extralarge.png",
               "CAL" : "http://1.cdn.nhle.com/flames/images/logos/extralarge.png",
               "CAR" : "http://1.cdn.nhle.com/hurricanes/images/logos/extralarge.png",
               "CHI" : "http://1.cdn.nhle.com/blackhawks/images/logos/extralarge.png",
               "CMB" : "http://1.cdn.nhle.com/bluejackets/images/logos/extralarge.png",
               "COL" : "http://1.cdn.nhle.com/avalanche/images/logos/extralarge.png",
               "DAL" : "http://1.cdn.nhle.com/stars/images/logos/extralarge.png",
               "DET" : "http://1.cdn.nhle.com/redwings/images/logos/extralarge.png",
               "EDM" : "http://1.cdn.nhle.com/oilers/images/logos/extralarge.png",
               "FLA" : "http://1.cdn.nhle.com/panthers/images/logos/extralarge.png",
               "LOS" : "http://1.cdn.nhle.com/kings/images/logos/extralarge.png",
               "MIN" : "http://1.cdn.nhle.com/wild/images/logos/extralarge.png",
               "MTL" : "http://1.cdn.nhle.com/canadiens/images/logos/extralarge.png",
               "NJD" : "http://1.cdn.nhle.com/devils/images/logos/extralarge.png",
               "NSH" : "http://1.cdn.nhle.com/predators/images/logos/extralarge.png",
               "NYI" : "http://1.cdn.nhle.com/islanders/images/logos/extralarge.png",
               "NYR" : "http://1.cdn.nhle.com/rangers/images/logos/extralarge.png",
               "OTT" : "http://1.cdn.nhle.com/senators/images/logos/extralarge.png",               
               "PHI" : "http://1.cdn.nhle.com/flyers/images/logos/extralarge.png",
               "PHX" : "http://1.cdn.nhle.com/coyotes/images/logos/extralarge.png",
               "PIT" : "http://1.cdn.nhle.com/penguins/images/logos/extralarge.png",
               "SJS" : "http://1.cdn.nhle.com/sharks/images/logos/extralarge.png",
               "STL" : "http://1.cdn.nhle.com/blues/images/logos/extralarge.png",
               "TAM" : "http://1.cdn.nhle.com/lightning/images/logos/extralarge.png",
               "TOR" : "http://1.cdn.nhle.com/mapleleafs/images/logos/extralarge.png",
               "VAN" : "http://1.cdn.nhle.com/canucks/images/logos/extralarge.png",
               "WSH" : "http://1.cdn.nhle.com/capitals/images/logos/extralarge.png",
               "WPG" : "http://1.cdn.nhle.com/jets/images/logos/extralarge.png"}

team_strings = {"ANA" : 30970,
                "BOS" : 30971,
                "BUF" : 30972,
                "CAL" : 30973,
                "CAR" : 30974,
                "CHI" : 30975,
                "CMB" : 30976,
                "COL" : 30977,
                "DAL" : 30978,
                "DET" : 30979,
                "EDM" : 30980,
                "FLA" : 30981,
                "LOS" : 30982,
                "MIN" : 30983,
                "MTL" : 30984,
                "NJD" : 30985, 
                "NSH" : 30986,
                "NYI" : 30987,
                "NYR" : 30988,
                "OTT" : 30989,
                "PHI" : 30990,
                "PHX" : 30991,
                "PIT" : 30992,
                "SJS" : 30993,
                "STL" : 30994,
                "TAM" : 30995,
                "TOR" : 30996,
                "VAN" : 30997,
                "WPG" : 30998,
                "WSH" : 30999}

ARCHIVED_GAMES = 'Archived Games'
LIVE_GAME = 'Live Game'

def createMainMenu():
    """
    Create the main menu, offering live and archived games
    """

    # add the live list
    li = xbmcgui.ListItem(LIVE_GAME, iconImage=team_images['TOR'])
    li.setInfo( type="Video", infoLabels={"Title" : LIVE_GAME})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=sys.argv[0]+"?url="+urllib.quote_plus("live"),
                                listitem=li,
                                isFolder=True)
    
    
    # add the archived list
    li=xbmcgui.ListItem(ARCHIVED_GAMES, iconImage=team_images['TOR'])
    li.setInfo( type="Video", infoLabels={"Title": ARCHIVED_GAMES})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=sys.argv[0]+"?url="+urllib.quote_plus("archived"),
                                listitem=li,
                                isFolder=True)

    # signal the end of the directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def authenticate():
    """
    Try to authenticate with leafs tv
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

    # attempt to authenticate
    ltv = LeafsTV(username, password)
    if not ltv.authenticate():
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30004),__language__(30005))
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]),
                                  succeeded=False)
        return None
    
    return ltv


def getGamesList(ltv):
    """
    Get the games list from leafs tv interactive using a LeafsTV object that is
    already authenticated
    """
    try:
        games_list = ltv.getGames()
    except LeafsTVError, ltvErr:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30007), __language__(30006))
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=False)
        return None

    return games_list


def createLiveMenu():
    """
    Create the menu containing the live game
    """    

    # authenticate and get the leafs tv object
    ltv = authenticate()
    if ltv == None:
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=False)
        return

    # get the games list
    games_list = getGamesList(ltv)
    if games_list == None:
        return

    # find any live games (there will only be one) and add them to the menu
    for game in games_list:
        if game['progress'] == "LIVE":
            addLiveGame(game, ltv)

    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    return


def createArchivedMenu():
    """
    Create the menu containing the archived games
    """

    # authenticate with leafs tv
    ltv = authenticate()
    if ltv == None:
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
        return

    # get the list of games
    games_list = getGamesList(ltv)
    if games_list == None:
        return

    # add any game that has already happened or is not live
    local_time = time.localtime(None)
    for game in games_list:
        if game['time'] < local_time  and game['progress'] != "LIVE":
            addArchivedGame(game, ltv)
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    return


def addArchivedGame(game, ltv):
    
    game_time=game['time']
    time_str = strftime("%d %b %Y", game_time)
    
    # get the away team string
    away_team = __language__(team_strings[game['away_team']])
    home_team = __language__(team_strings[game['home_team']])
    
    
    game_name = time_str + " " + away_team + " " + __language__(30013) + " " + home_team
    
    # figure out the opposition
    opposition = game['home_team']
    if opposition == "TOR":
        opposition = game['away_team']
        
    # get the opposing teams picture
    oplogo = team_images['TOR']
    if opposition in team_images:
        oplogo = team_images[opposition]  

    # add the live list
    li = xbmcgui.ListItem(game_name, iconImage=oplogo)
    li.setInfo( type="Video", infoLabels={"Title" : game_name})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=sys.argv[0] + "?archive=" + urllib.quote_plus(game['id']),
                                listitem=li)
    
    return


def addLiveGame(game, ltv):
    """
    Add the live game to the menu
    """

    # get the away team string
    away_team = __language__(team_strings[game['away_team']])
    home_team = __language__(team_strings[game['home_team']])
    game_name = away_team + " " + __language__(30013) + " " + home_team
        
    try:
        game_url = ltv.getLiveGame()
    except LeafsTVError, ltvErr:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30009), __language__(30006))
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=False)
        return
    
    # figure out the opposition
    opposition = game['home_team']
    if opposition == "TOR":
        opposition = game['away_team']
        
    # get the opposing teams picture
    oplogo = team_images['TOR']
    if opposition in team_images:
        oplogo = team_images[opposition]  

    # add the live list
    li = xbmcgui.ListItem(game_name, iconImage=oplogo)
    li.setInfo( type="Video", infoLabels={"Title" : game_name})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=game_url + " live=true",
                                listitem=li,
                                isFolder=False)
    
    return


def playArchive(game_id):
    """
    Play an archived game
    """
    
    # authenticate with leafs TV
    ltv = authenticate()
    if ltv == None:
        return
    
    # get the archived game URL
    try:
        url = ltv.getArchivedGame(game_id)
    except LeafsTVError, ltvErr:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30008),__language__(30010))
        return

    # play the archived game
    player = Player(xbmc.PLAYER_CORE_AUTO)
    player.play(url)
    
    return


# if the second argument is empty this is the main menu
if (len(sys.argv[2]) == 0):
    createMainMenu()
elif sys.argv[2] == "?url=archived":
    createArchivedMenu()
elif sys.argv[2] == '?url=live':
    createLiveMenu()
else:
    match = re.match('\?archive\=(.*)', sys.argv[2])
    if match != None:
        print str(match)
        try:
            game_id = match.group(1)
            playArchive(game_id)
        except:
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30008), __language__(30011))
    else:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30008), __language__(30012))
    
