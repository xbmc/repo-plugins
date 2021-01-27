import time
import datetime
import xbmcaddon

#main plugin/service library
ampache = xbmcaddon.Addon("plugin.audio.ampache")

def otype_to_type(object_type):
    if object_type == 'albums':
        return 'album'
    elif object_type == 'artists':
        return 'artist'
    elif object_type == 'songs':
        return 'song'
    elif object_type == 'playlists':
        return 'playlist'
    elif object_type == 'tags':
        return 'tag'
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
            object_id=int(params["object_id"])
            xbmc.log("AmpachePlugin::object_id " + str(object_id), xbmc.LOGDEBUG)
    except:
            pass
    try:
            object_id=int(params["oid"])
            xbmc.log("AmpachePlugin::object_id " + str(object_id), xbmc.LOGDEBUG)
    except:
            pass
    return object_id
