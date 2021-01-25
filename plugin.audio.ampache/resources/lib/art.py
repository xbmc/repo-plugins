from future.utils import PY2
import re
import os
import cgi
import xbmc,xbmcaddon
import xbmcvfs

from resources.lib import ampache_connect

ampache = xbmcaddon.Addon("plugin.audio.ampache")

#different functions in kodi 19 (python3) and kodi 18 (python2)
if PY2:
    user_dir = xbmc.translatePath( ampache.getAddonInfo('profile'))
    user_dir = user_dir.decode('utf-8')
else:
    user_dir = xbmcvfs.translatePath( ampache.getAddonInfo('profile'))
user_mediaDir = os.path.join( user_dir , 'media' )
cacheDir = os.path.join( user_mediaDir , 'cache' )

def cacheArt(imageID,elem_type,url=None):
    #security check
    if imageID == None:
        raise NameError
   
    possible_ext = ["jpg", "png" , "bmp", "gif", "tiff"]
    for ext in possible_ext:
        imageName = str(imageID) + "." + ext
        pathImage = os.path.join( cacheDir , imageName )
        if os.path.exists( pathImage ):
            xbmc.log("AmpachePlugin::CacheArt: cached, id " + str(imageID) +  " extension " + ext ,xbmc.LOGDEBUG)
            return pathImage
    
    #no return, not found
    ampacheConnect = ampache_connect.AmpacheConnect()
    action = 'get_art'
    ampacheConnect.id = str(imageID)
    ampacheConnect.type = elem_type
    
    if url:
        #old api version
        headers,contents = ampacheConnect.handle_request(url)
    else:
        headers,contents = ampacheConnect.ampache_binary_request(action)
    #xbmc.log("AmpachePlugin::CacheArt: File needs fetching, id " + str(imageID),xbmc.LOGDEBUG)
    extension = headers['content-type']
    if extension:
        mimetype, options = cgi.parse_header(extension)
        #little hack when content-type is not standard
        if mimetype == "JPG":
            maintype = "image"
            subtype = "jpg"
        else:
            try:
                maintype, subtype = mimetype.split("/")
            except ValueError:
                xbmc.log("AmpachePlugin::CacheArt: content-type not standard " +\
                        mimetype,xbmc.LOGDEBUG)
                raise NameError
        if maintype == 'image':
            if subtype == "jpeg":
                fname = str(imageID) + ".jpg"
            else:
                fname = str(imageID) + '.' + subtype
            pathImage = os.path.join( cacheDir , fname )
            open( pathImage, 'wb').write(contents)
            #xbmc.log("AmpachePlugin::CacheArt: Cached " + str(fname), xbmc.LOGDEBUG )
            return pathImage
        else:
            xbmc.log("AmpachePlugin::CacheArt: It didnt work, id " + str(imageID) , xbmc.LOGDEBUG )
            raise NameError
    else:
        xbmc.log("AmpachePlugin::CacheArt: No file found, id " + str(imageID) , xbmc.LOGDEBUG )
        raise NameError

def get_artLabels(albumArt):
    art_labels = {
            'banner' : albumArt, 
            'thumb': albumArt, 
            'icon': albumArt,
            'fanart': albumArt
            }
    return art_labels

#get_art, url is used for legacy purposes
def get_art(object_id,elem_type,url=None):
    try:
        albumArt = cacheArt(object_id,elem_type,url)
    except NameError:
        albumArt = "DefaultFolder.png"
    #xbmc.log("AmpachePlugin::get_art: albumArt - " + str(albumArt), xbmc.LOGDEBUG )
    return albumArt


