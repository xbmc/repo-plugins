from future.utils import PY2
import os
import xbmc,xbmcaddon
import xbmcvfs

from datetime import datetime, timedelta
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

    #hack to force the creation of profile directory if don't exists
    if not os.path.isdir(user_dir):
        ampache.setSetting("api-version","350001")

def is_expired(cache_file_path: str) -> bool:
    """Check if the cache file has expired (older than one month)."""
    # Define the current time
    now = datetime.now()

    try:
        # Get the modification time of the cache file
        mod_time = os.path.getmtime(cache_file_path)
        last_modified = datetime.fromtimestamp(mod_time)

        # Calculate if more than a month has passed since modification
        expiration_duration = timedelta(days=30)  # One month

        return (now - last_modified) > expiration_duration
    except FileNotFoundError:
        return True  # Treat missing files as expired

def delete_expired_files():

    cacheTypes = ["album", "artist" , "song", "podcast","playlist"]

    for c_type in cacheTypes:
        cacheDirType = os.path.join( cacheDir , c_type )
        for currentFile in os.listdir(cacheDirType):
            #xbmc.log("Clear Cache Art " + str(currentFile),xbmc.LOGDEBUG)
            pathDel = os.path.join( cacheDirType, currentFile)
            if is_expired(pathDel):
                try:
                    os.remove(pathDel)
                except PermissionError as e:
                    pass

def remove_expired():
    print("Starting cache cleanup...")
    delete_expired_files()
    print("Cache cleanup completed.")

def init_cache():
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


