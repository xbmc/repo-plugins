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

def clean_cache_art():
    #hack to force the creation of profile directory if don't exists
    if not os.path.isdir(user_dir):
        ampache.setSetting("api-version","350001")

    #if cacheDir doesn't exist, create it
    if not os.path.isdir(user_mediaDir):
        os.mkdir(user_mediaDir)
        if not os.path.isdir(cacheDir):
            os.mkdir(cacheDir)

    #clean cache on start
    for currentFile in os.listdir(cacheDir):
        #xbmc.log("Clear Cache Art " + str(currentFile),xbmc.LOGDEBUG)
        pathDel = os.path.join( cacheDir, currentFile)
        os.remove(pathDel)


