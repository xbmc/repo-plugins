############################################################################
# NHL GAMECENTER
# XBMC ADD-ON
############################################################################
import xbmcgui
from resources.lib.userinterface import *
from resources.lib.scoring_updates import *

params = get_params()

print params
try:
    url=urllib.unquote_plus(params["url"])
except:
    url=None
try:
    mode = int(params['mode'])
except:
    mode = None


print "Mode: "+str(mode)
print "URL: "+str(url)


if mode == None or url==None or len(url)<1:        
    CATEGORIES()       
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    
elif mode == 1:
    LIVE(url)
    #xbmcplugin.endOfDirectory(int(sys.argv[1]))    
    #Do Not Cache Menu
    xbmcplugin.endOfDirectory(int(sys.argv[1]),1,0,0)
elif mode == 2:
    LIVEQUALITY(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 3:
    LIVELINKS(url)    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 4:
    ARCHIVE(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 5:
    ARCHIVEMONTH(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 6:
    ARCHIVEGAMES(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 7:
    ARCHIVEQUALITY(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 8:
    ARCHIVELINKS(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 9:
    LASTNIGHT(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 10:
    LASTNIGHTTYPE(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 11:
    LATESTGAMES(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 12:
    LATESTGQUALITY(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 13:
    LATESTGLINKS(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 14:
    LATESTGTYPE(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 100:
    ADDON.setSetting(id='score_updates', value='true')
    s = ScoreThread()
    t = threading.Thread(target = s.Scoring_Updates)
    t.start() 
elif mode == 101:
    dialog = xbmcgui.Dialog() 
    title = "Score Notifications"
    dialog.notification(title, 'Stopping...', ADDON_PATH+'/resources/images/nhl_logo.png', 5000, False)
    ADDON.setSetting(id='score_updates', value='false')