from future.utils import PY2
import os
import cgi
import xbmc,xbmcaddon
import xbmcvfs

#main plugin library

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
    if not imageID and not url:
        raise NameError

    cacheDirType = os.path.join( cacheDir , elem_type )
   
    possible_ext = ["jpg", "png" , "bmp", "gif", "tiff"]
    for ext in possible_ext:
        imageName = imageID + "." + ext
        pathImage = os.path.join( cacheDirType , imageName )
        if os.path.exists( pathImage ):
            xbmc.log("AmpachePlugin::CacheArt: cached, id " + imageID +  " extension " + ext ,xbmc.LOGDEBUG)
            return pathImage
    
    #no return, not found
    ampacheConnect = ampache_connect.AmpacheConnect()
    action = 'get_art'
    ampacheConnect.id = imageID
    ampacheConnect.type = elem_type
    
    try:
        if(int(ampache.getSetting("api-version"))) < 400001:
            #old api version
            headers,contents = ampacheConnect.handle_request(url)
        else:
            headers,contents = ampacheConnect.ampache_binary_request(action)
    except AmpacheConnect.ConnectionError:
        raise NameError
    #xbmc.log("AmpachePlugin::CacheArt: File needs fetching, id " + imageID,xbmc.LOGDEBUG)
    extension = headers['content-type']
    if extension:
        mimetype, options = cgi.parse_header(extension)
        #little hack when content-type is not standard
        if mimetype == "JPG" or mimetype == "jpeg":
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
                fname = imageID + ".jpg"
            else:
                fname = imageID + '.' + subtype

            pathImage = os.path.join( cacheDirType , fname )
            with open( pathImage, 'wb') as f:
                f.write(contents)
                f.close()
            #xbmc.log("AmpachePlugin::CacheArt: Cached " + fname, xbmc.LOGDEBUG )
            return pathImage
        else:
            xbmc.log("AmpachePlugin::CacheArt: It didnt work, id " + imageID , xbmc.LOGDEBUG )
            raise NameError
    else:
        xbmc.log("AmpachePlugin::CacheArt: No file found, id " + imageID , xbmc.LOGDEBUG )
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

    albumArt = "DefaultFolder.png"
    #no url, no art, so no need to activate a connection
    if not object_id and not url:
        return albumArt
    try:
        albumArt = cacheArt(object_id,elem_type,url)
    except NameError:
        albumArt = "DefaultFolder.png"

    #xbmc.log("AmpachePlugin::get_art: id - " + object_id + " - albumArt - " + str(albumArt), xbmc.LOGDEBUG )
    return albumArt


