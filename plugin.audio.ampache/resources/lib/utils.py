import time
import datetime
import xbmcaddon,xbmcplugin
import sys

#main plugin/service library
ampache = xbmcaddon.Addon("plugin.audio.ampache")

def setContent(handle,object_type):
    if object_type == 'artists' or object_type == 'albums' or object_type == 'songs' or object_type == 'videos':
        xbmcplugin.setContent(handle, object_type)

def otype_to_mode(object_type, object_subtype=None):
    mode = None
    if object_type == 'artists':
        mode = 1
    elif object_type == 'albums':
        mode = 2
    elif object_type == 'songs':
        mode = 3
    elif object_type == 'playlists':
        mode = 4
    elif object_type == 'podcasts':
        mode = 5
    elif object_type == 'live_streams':
        mode = 6
    elif object_type == 'videos':
        mode = 8
    elif object_type == 'tags' or object_type == 'genres':
        if object_subtype == 'tag_artists' or object_subtype == 'genre_artists':
            mode = 19
        elif object_subtype == 'tag_albums' or object_subtype == 'genre_albums':
            mode = 20
        elif object_subtype == 'tag_songs' or object_subtype == 'genre_songs':
            mode = 21

    return mode

def mode_to_tags(mode):
    if(int(ampache.getSetting("api-version"))) < 500000:
        if mode == 19:
            return "tags","tag_artists"
        if mode == 20:
            return "tags","tag_albums"
        if mode == 21:
            return "tags","tag_songs"
    else:
        if mode == 19:
            return "genres","genre_artists"
        if mode == 20:
            return "genres","genre_albums"
        if mode == 21:
            return "genres","genre_songs"

def otype_to_type(object_type,object_subtype=None):
    if object_type == 'albums':
        return 'album'
    elif object_type == 'artists':
        return 'artist'
    elif object_type == 'playlists':
        return 'playlist'
    elif object_type == 'tags':
        return 'tag'
    elif object_type == 'genres':
        return 'genre'
    elif object_type == 'podcasts':
        return 'podcast'
    elif object_type == 'videos':
        return 'video'
    elif object_type == 'songs':
        if object_subtype == 'podcast_episodes':
            return 'podcast_episode'
        elif object_subtype == 'live_streams':
            return 'live_stream'
        return 'song'
    return None

def int_to_strBool(s):
    if s == 1:
        return 'true'
    elif s == 0:
        return 'false'
    else:
        raise ValueError

#   string to bool function : from string 'true' or 'false' to boolean True or
#   False, raise ValueError
def strBool_to_bool(s):
    if s == 'true':
        return True
    elif s == 'false':
        return False
    else:
        raise ValueError

def check_tokenexp():
    session_time = ampache.getSetting("session_expire")
    if session_time is None or session_time == "":
        return True

    #from python 3.7 we can easly compare the dates, otherwise we use the old
    #method

    if sys.version_info >= (3, 7):
        try:
            s_time = datetime.datetime.fromisoformat(session_time)
            if datetime.datetime.now(datetime.timezone.utc) > s_time:
                return True
            return False
        except:
            return False
    else:
        try:
            tokenexp = int(ampache.getSetting("token-exp"))
            if int(time.time()) > tokenexp:
                return True
            return False
        except:
            return True

def get_time(time_offset):
    d = datetime.date.today()
    dt = datetime.timedelta(days=time_offset)
    nd = d + dt
    return nd.isoformat()

#return the translated String
def tString(code):
    return ampache.getLocalizedString(code)

def get_params(plugin_url):
    param=[]
    paramstring=plugin_url
    if len(paramstring)>=2:
            params=plugin_url
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]

    return param

def get_objectId_from_fileURL( file_url ):
    params = get_params(file_url)
    object_id = None
    #i use two kind of object_id, i don't know, but sometime i have different
    #url, btw, no problem, i handle both and i solve the problem in this way
    try:
            object_id=params["object_id"]
            xbmc.log("AmpachePlugin::object_id " + object_id, xbmc.LOGDEBUG)
    except:
            pass
    try:
            object_id=params["oid"]
            xbmc.log("AmpachePlugin::object_id " + object_id, xbmc.LOGDEBUG)
    except:
            pass
    return object_id

def getRating(rating):
    if rating:
        #converts from five stats ampache rating to ten stars kodi rating
        rating = int(float(rating)*2)
    else:
        #zero equals no rating
        rating = 0
    return rating
