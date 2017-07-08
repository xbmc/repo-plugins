
from resources.lib.nhl_tv import *

    
params=get_params()
url=None
name=None
mode=None
game_day=None
game_id=None
epg=None
teams_stream=None
stream_date=None

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
    game_day=urllib.unquote_plus(params["game_day"])
except:    
    pass
try:
    game_id=urllib.unquote_plus(params["game_id"])
except:
    pass
try:
    epg=urllib.unquote_plus(params["epg"])
except:
    pass
try:
    teams_stream=urllib.unquote_plus(params["teams_stream"])
except:
    pass
try:
    stream_date=urllib.unquote_plus(params["stream_date"])
except:
    pass


xbmc.log("Mode: "+str(mode))
#xbmc.log("URL: "+str(url))
xbmc.log("Name: "+str(name))



if mode==None or url==None:        
    categories()  

elif mode == 100:      
    #Todays Games            
    todaysGames(None)

elif mode == 101:
    #Prev and Next 
    todaysGames(game_day)    

elif mode == 104:    
    streamSelect(game_id, epg, teams_stream, stream_date)

elif mode == 105:
    #Yesterday's Games
    game_day = localToEastern()
    display_day = stringToDate(game_day, "%Y-%m-%d")            
    prev_day = display_day - timedelta(days=1)                
    todaysGames(prev_day.strftime("%Y-%m-%d"))

elif mode == 200:    
    gotoDate()

elif mode == 300:
    nhlVideos(url)

elif mode == 400:    
    logout('true')

elif mode == 500:
    myTeamsGames()

elif mode == 510:
    playTodaysFavoriteTeam()

elif mode == 515:    
    getThumbnails()

elif mode == 900:
    playAllHighlights()

elif mode == 999:
    sys.exit()

xbmc.log(str(mode))
if mode==100 or mode==101 or mode==104 or mode==105 or mode==200 or mode==300 or mode==500 or mode==510: 
    setViewMode()
elif mode==None:
    getViewMode()
    
xbmc.log("My view mode " + VIEW_MODE)

if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 101 or mode == 500 or mode == 501 or mode == 510:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)
