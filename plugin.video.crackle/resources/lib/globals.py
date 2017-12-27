import sys, os
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import urllib, urllib2
import json
import base64, hmac, hashlib
from datetime import datetime

addon_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon()
ROOTDIR = ADDON.getAddonInfo('path')
FANART = ROOTDIR+"/resources/media/fanart.jpg"
ICON = os.path.join(ROOTDIR,"/resources/media/icon.png")


#Addon Settings
LOCAL_STRING = ADDON.getLocalizedString
UA_CRACKLE = 'Crackle/7.60 CFNetwork/808.3 Darwin/16.3.0'
UA_WEB = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36'
UA_ANDROID = 'Android 4.1.1; E270BSA; Crackle 4.4.5.0'
PRIVATE_KEY = 'MIRNPSEZYDAQASLX'
VENDOR_ID = '25'
BASE_URL = 'http://android-tv-api-us.crackle.com/Service.svc'


def mainMenu():
    addDir('Movies','/movies',101,ICON)
    addDir('TV','/tv',100,ICON)


def listMovies():
    url = '/browse/movies/full/all/alpha-asc/US'
    url += '?pageSize=500'
    url += '&pageNumber=1'
    url += '&format=json'
    json_source = jsonRequest(url)


    for movie in json_source['Entries']:
        title = movie['Title']
        url = str(movie['ID'])
        icon = movie['ChannelArtTileLarge']
        fanart = movie['Images']['Img_1920x1080']
        info = None
        info = {'plot':movie['Description'],
                'genre':movie['Genre'],
                'year':movie['ReleaseYear'],
                'mpaa':movie['Rating'],
                'title':title,
                'originaltitle':title,
                'duration':movie['DurationInSeconds']
                }

        addStream(title,url,'movies',icon,fanart,info)



def listShows():
    url = '/browse/shows/full/all/alpha-asc/US'
    url += '?pageSize=500'
    url += '&pageNumber=1'
    url += '&format=json'
    json_source = jsonRequest(url)

    for show in json_source['Entries']:
        title = show['Title']
        url = str(show['ID'])
        icon = show['ChannelArtTileLarge']
        fanart = show['Images']['Img_1920x1080']
        info = None
        info = {'plot':show['Description'],
                'genre':show['Genre'],
                'year':show['ReleaseYear'],
                'mpaa':show['Rating'],
                'title':title,
                'originaltitle':title,
                'duration':show['DurationInSeconds']
                }

        addDir(title,url,102,icon,fanart,info)


def getEpisodes(channel):
    url = '/channel/'+channel+'/playlists/all/US?format=json'
    json_source = jsonRequest(url)

    for episode in json_source['Playlists'][0]['Items']:
        episode = episode['MediaInfo']
        title = episode['Title']
        id = str(episode['Id'])
        icon = episode['Images']['Img_460x460']
        fanart = episode['Images']['Img_1920x1080']
        info = None
        info = {'plot':episode['Description'],
                #'genre':episode['Genre'],
                'year':episode['ReleaseYear'],
                'mpaa':episode['Rating'],
                'title':title,
                'originaltitle':title,
                'duration':episode['Duration'],
                'season':episode['Season'],
                'episode':episode['Episode']
                }

        addStream(title,id,'tvshows',icon,fanart,info)


def getMovieID(channel):
    url = '/channel/'+str(channel)+'/playlists/all/US?format=json'
    json_source = jsonRequest(url)

    return str(json_source['Playlists'][0]['Items'][0]['MediaInfo']['Id'])


def getStream(id):
    url = '/details/media/'+id+'/US?format=json'
    json_source = jsonRequest(url)


    for stream in json_source['MediaURLs']:
        if 'AppleTV' in stream['Type']:
            stream_url = stream['Path']
            stream_url = stream_url[0:stream_url.index('.m3u8')]+'.m3u8'
            break

    stream_url += '|User-Agent='+UA_CRACKLE
    listitem = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem)


def jsonRequest(url):
    url = BASE_URL + url
    req = urllib2.Request(url)
    req.add_header("Connection", "keep-alive")
    req.add_header("User-Agent", UA_ANDROID)
    req.add_header("Authorization", getAuth(url))

    response = urllib2.urlopen(req)
    json_source = json.load(response)
    response.close()

    return json_source


def calcHmac(src):
    return hmac.new(PRIVATE_KEY, src, hashlib.md5).hexdigest()


def getAuth(url):
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M')
    encoded_url = str(calcHmac(url+"|"+timestamp)).upper() + "|" + timestamp + "|" + VENDOR_ID

    return encoded_url


def addStream(name, id, stream_type, icon,fanart,info=None):
    ok=True
    u=sys.argv[0]+"?id="+urllib.quote_plus(id)+"&mode="+str(103)+"&type="+urllib.quote_plus(stream_type)
    liz=xbmcgui.ListItem(name)
    liz.setArt({'icon': ICON, 'thumb': icon, 'fanart': fanart})
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)
    ok=xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, stream_type)
    return ok


def addDir(name,id,mode,iconimage,fanart=None,info=None):
    params = get_params()
    ok=True
    u=sys.argv[0]+"?id="+urllib.quote_plus(id)+"&mode="+str(mode)
    liz=xbmcgui.ListItem(name)
    liz.setArt({'icon': ICON, 'thumb': iconimage, 'fanart': fanart})
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)
    ok=xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=True)
    xbmcplugin.setContent(addon_handle, 'tvshows')
    return ok


def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
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
