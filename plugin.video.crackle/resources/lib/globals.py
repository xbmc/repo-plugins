import sys, os
import urllib, requests
import base64, hmac, hashlib
from time import gmtime, strftime
import xbmc, xbmcplugin, xbmcgui, xbmcaddon

addon_url = sys.argv[0]
addon_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon()
ROOTDIR = ADDON.getAddonInfo('path')
FANART = os.path.join(ROOTDIR,"resources","media","fanart.jpg")
ICON = os.path.join(ROOTDIR,"resources","media","icon.png")


# Addon Settings
LOCAL_STRING = ADDON.getLocalizedString
UA_CRACKLE = 'Crackle/7.60 CFNetwork/808.3 Darwin/16.3.0'
UA_WEB = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36'
UA_ANDROID = 'Android 4.1.1; E270BSA; Crackle 4.4.5.0'
#PARTNER_KEY = 'TUlSTlBTRVpZREFRQVNMWA=='
PARTNER_KEY = 'Vk5aUUdYV0ZIVFBNR1ZWVg=='
PARTNER_ID = '77'
BASE_URL = 'https://androidtv-api-us.crackle.com/Service.svc'


def main_menu():
    add_dir('Movies', 'movies', 99, ICON)
    add_dir('TV', 'shows', 99, ICON)


def list_movies(genre_id):
    url = '/browse/movies/full/%s/alpha-asc/US?format=json' % genre_id
    # url = '/browse/movies/full/all/alpha-asc/US'
    # url += '?pageSize=500'
    # url += '&pageNumber=1'
    # url += '&format=json'
    json_source = json_request(url)

    for movie in json_source['Entries']:
        title = movie['Title']
        url = str(movie['ID'])
        icon = movie['ChannelArtTileLarge']
        fanart = movie['Images']['Img_1920x1080']
        info = {'plot':movie['Description'],
                'genre':movie['Genre'],
                'year':movie['ReleaseYear'],
                'mpaa':movie['Rating'],
                'title':title,
                'originaltitle':title,
                'duration':movie['DurationInSeconds'],
                'mediatype': 'movie'
                }

        add_stream(title,url,'movies',icon,fanart,info)


def list_genre(id):
    url = '/genres/%s/all/US?format=json' % id
    json_source = json_request(url)
    for genre in json_source['Items']:
        title = genre['Name']

        add_dir(title, id, 100, ICON, genre_id=genre['ID'])
        # add_dir(name, id, mode, icon, fanart=None, info=None, genre_id=None)


def list_shows(genre_id):
    url = '/browse/shows/full/%s/alpha-asc/US/1000/1?format=json' % genre_id
    # url += '?pageSize=500'
    # url += '&pageNumber=1'
    # url += '&format=json'
    json_source = json_request(url)

    for show in json_source['Entries']:
        title = show['Title']
        url = str(show['ID'])
        icon = show['ChannelArtTileLarge']
        fanart = show['Images']['Img_1920x1080']
        info = {'plot':show['Description'],
                'genre':show['Genre'],
                'year':show['ReleaseYear'],
                'mpaa':show['Rating'],
                'title':title,
                'originaltitle':title,
                'duration':show['DurationInSeconds'],
                'mediatype': 'tvshow'
                }

        add_dir(title,url,102,icon,fanart,info,content_type='tvshows')


def get_episodes(channel):
    url = '/channel/'+channel+'/playlists/all/US?format=json'
    json_source = json_request(url)

    for episode in json_source['Playlists'][0]['Items']:
        episode = episode['MediaInfo']
        title = episode['Title']
        id = str(episode['Id'])
        icon = episode['Images']['Img_460x460']
        fanart = episode['Images']['Img_1920x1080']
        info = {'plot':episode['Description'],
                #'genre':episode['Genre'],
                'year':episode['ReleaseYear'],
                'mpaa':episode['Rating'],
                'tvshowtitle':episode['ShowName'],
                'title':title,
                'originaltitle':title,
                'duration':episode['Duration'],
                'season':episode['Season'],
                'episode':episode['Episode'],
                'mediatype': 'episode'
                }

        add_stream(title,id,'tvshows',icon,fanart,info)


def get_movie_id(channel):
    url = '/channel/'+str(channel)+'/playlists/all/US?format=json'
    json_source = json_request(url)

    return str(json_source['Playlists'][0]['Items'][0]['MediaInfo']['Id'])


def get_stream(id):
    url = '/details/media/'+id+'/US?format=json'
    json_source = json_request(url)

    for stream in json_source['MediaURLs']:
        # if 'AppleTV' in stream['Type']:
        if '480p_1mbps.mp4' in stream['Type']:
            stream_url = stream['Path']
            # stream_url = stream_url[0:stream_url.index('.m3u8')]+'.m3u8'
            break

    headers = '|User-Agent='+UA_CRACKLE
    listitem = xbmcgui.ListItem()
    # if xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):
    #     listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
    #     listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
    #     listitem.setProperty('inputstream.adaptive.stream_headers', headers)
    #     listitem.setProperty('inputstream.adaptive.license_key', headers)
    # else:
    stream_url += headers

    listitem.setPath(stream_url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem)


def json_request(url):
    url = BASE_URL + url
    xbmc.log(url)
    headers = {
        'Connection': 'keep-alive',
        'User-Agent': UA_ANDROID,
        'Authorization': get_auth(url),
        'X-Requested-With': 'com.crackle.androidtv'
    }

    r = requests.get(url, headers=headers, verify=False)

    return r.json()


def calc_hmac(src):
    # return hmac.new(base64.b64decode(PARTNER_KEY), src, hashlib.md5).hexdigest()
    return hmac.new(base64.b64decode(PARTNER_KEY), src, hashlib.sha1).hexdigest()


def get_auth(url):
    timestamp = strftime('%Y%m%d%H%M', gmtime())
    # encoded_url = str(calc_hmac(url+"|"+timestamp)).upper() + "|" + timestamp + "|" + PARTNER_ID
    encoded_url = '%s|%s|%s|1' % (calc_hmac(url + "|" + timestamp).upper(), timestamp, PARTNER_ID)

    return encoded_url


def add_stream(name, id, stream_type, icon, fanart, info=None):
    ok = True
    u=addon_url+"?id="+urllib.quote_plus(id)+"&mode="+str(103)+"&type="+urllib.quote_plus(stream_type)
    liz=xbmcgui.ListItem(name)
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'fanart': fanart})
    liz.setProperty("IsPlayable", "true")
    if info is not None:
        liz.setInfo( type="video", infoLabels=info)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, stream_type)
    return ok


def add_dir(name, id, mode, icon, fanart=None, info=None, genre_id=None, content_type='videos'):
    ok = True
    u = addon_url+"?id="+urllib.quote_plus(id)+"&mode="+str(mode)
    if genre_id is not None: u += "&genre_id=%s" % genre_id
    liz=xbmcgui.ListItem(name)
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'fanart': fanart})
    if info is not None:
        liz.setInfo( type="video", infoLabels=info)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=True)
    xbmcplugin.setContent(addon_handle, content_type)
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
