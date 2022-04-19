from future.utils import PY2
import os
import xbmc,xbmcaddon
import xbmcvfs

#split the art library to not have import problems, as the function is used by
#service and the main plugin
#library used both by service and main plugin, DO NOT INCLUDE OTHER LOCAL
#LIBRARIES

ampache = xbmcaddon.Addon("plugin.audio.ampache")

#different functions in kodi 19 (python3) and kodi 18 (python2)
if PY2:
    user_dir = xbmc.translatePath( ampache.getAddonInfo('profile'))
    user_dir = user_dir.decode('utf-8')
else:
    user_dir = xbmcvfs.translatePath( ampache.getAddonInfo('profile'))
user_mediaDir = os.path.join( user_dir , 'media' )
cacheDir = os.path.join( user_mediaDir , 'cache' )

def clean_settings():
    ampache.setSetting("session_expire", "")
    ampache.setSetting("add", "")
    ampache.setSetting("token", "")
    ampache.setSetting("token-exp", "")
    ampache.setSetting("artists", "")
    ampache.setSetting("albums", "")
    ampache.setSetting("songs", "")
    ampache.setSetting("playlists", "")
    ampache.setSetting("videos", "")
    ampache.setSetting("podcasts", "")
    ampache.setSetting("live_streams", "")

def clean_cache_art():
    #hack to force the creation of profile directory if don't exists
    if not os.path.isdir(user_dir):
        ampache.setSetting("api-version","350001")

    cacheTypes = ["album", "artist" , "song", "podcast","playlist"]
    #if cacheDir doesn't exist, create it
    if not os.path.isdir(user_mediaDir):
        os.mkdir(user_mediaDir)
    if not os.path.isdir(cacheDir):
        os.mkdir(cacheDir)
    for c_type in cacheTypes:
        cacheDirType = os.path.join( cacheDir , c_type )
        if not os.path.isdir(cacheDirType):
            os.mkdir( cacheDirType )

    #clean cache on start
    for c_type in cacheTypes:
        cacheDirType = os.path.join( cacheDir , c_type )
        for currentFile in os.listdir(cacheDirType):
            #xbmc.log("Clear Cache Art " + str(currentFile),xbmc.LOGDEBUG)
            pathDel = os.path.join( cacheDirType, currentFile)
            os.remove(pathDel)


