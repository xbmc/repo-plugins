# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License.
# *  If not, write to the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# *  2011/05/30
# *
# *  Thanks and credit to:
# *
# *  mlbviewer  http://sourceforge.net/projects/mlbviewer/  Most of the mlb.tv code was from this project.
# *
# *  Everyone from the fourm - http://fourm.xbmc.org
# *    giftie - for the colored text code :) thanks.
# *    theophile and the others from - http://forum.xbmc.org/showthread.php?t=97251
# *    bunglebungle for game highlights patch - http://forum.xbmc.org/showthread.php?tid=104391&pid=1109006#pid1109006


import xbmcplugin
import urllib
import time
from datetime import datetime, timedelta
from resources import mlb, mlb_common, mlbtv

url=None
name=None
mode=None
live=None
event=None
content=None
session=None
cookieIp=None
cookieFp=None
scenario=None
game_type=None
podcasts=False

params=mlb_common.get_params()

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    live=eval(params["live"])
except:
    pass
try:
    podcasts=eval(params["podcasts"])
except:
    pass
try:
    event=urllib.unquote_plus(params["event"])
except:
    pass
try:
    content=urllib.unquote_plus(params["content"])
except:
    pass
try:
    session=urllib.unquote_plus(params["session"])
except:
    pass
try:
    cookieIp=urllib.unquote_plus(params["cookieIp"])
except:
    pass
try:
    cookieFp=urllib.unquote_plus(params["cookieFp"])
except:
    pass
try:
    scenario=urllib.unquote_plus(params["scenario"])
except:
    pass
try:
    game_type=urllib.unquote_plus(params["game_type"])
except:
    pass

mlb_common.addon_log("Mode: "+str(mode))
mlb_common.addon_log("URL: "+str(url))
mlb_common.addon_log("Name: "+str(name))

if mode==None:
    mlb.categories()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==1:
    mlb.getVideos(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==2:
    if podcasts:
        mlb.setVideoURL(url, True)
    else:
        mlb.setVideoURL(url)

if mode==3:
    mlb.gameCalender('mlbtv')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==4:
    mlb.getTeams(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==5:
    mlb.getTeamVideo(url)

if mode==6:
    mlb.getGames(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==7:
    mlbtv.mlbGame(event)

if mode==8:
    mlb.getRealtimeVideo(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==9:
    mlbtv.getGameURL(name,event,content,session,cookieIp,cookieFp,scenario,live)

if mode==10:
    mlb.get_podcasts(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==11:
    url = mlb.getDate(game_type)
    if game_type == 'mlbtv':
        mlb.getGames(url)
    else:
        mlb.getCondensedGames(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==12:
    mlb.playLatest(url)

if mode==13:
    mlb.gameCalender('condensed')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==14:
    mlb.getCondensedGames(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==15:
    try:
        start_date = datetime.strptime(url, "%B %d, %Y - %A")
    except TypeError:
        start_date = datetime.fromtimestamp(time.mktime(time.strptime(url, "%B %d, %Y - %A")))
    mlb.gameCalender(game_type, start_date)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==16:
    mlb.Search(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==17:
    mlb.gameHighlights()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==18:
    mlb.get_mlb_playlist(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==19:
    mlb.get_mlb_playlist(url, name)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==20:
    mlb.get_players(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==21:
    mlb.getVideos('current_playlist', int(url))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==22:
    mlb.mlb_podcasts()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==23:
    mlb.getFullCount()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==24:
    mlb.get_topic_playlist(url, eval(game_type))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==25:
    mlbtv.mlbGame(event, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==26:
    mlb.getGameHighlights(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==27:
    mlb.getRealtimeVideo(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==28:
    mlb.get_playlist_cats()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==29:
    mlb.get_playlist_cats(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode==30:
    pass