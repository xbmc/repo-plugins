import sys, os
import urllib, requests
import inputstreamhelper
from urllib.parse import urlparse
from urllib.parse import urlencode
from time import gmtime, strftime
from kodi_six import xbmc, xbmcplugin, xbmcgui, xbmcaddon

if sys.version_info[0] > 2:
    urllib = urllib.parse

addon_url = sys.argv[0]
addon_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon()
ROOTDIR = ADDON.getAddonInfo('path')
FANART = os.path.join(ROOTDIR,"resources","media","fanart.jpg")
ICON = os.path.join(ROOTDIR,"resources","media","icon.png")

# Addon Settings
LOCAL_STRING = ADDON.getLocalizedString
UA_CRACKLE = 'Crackle/7.60 CFNetwork/808.3 Darwin/16.3.0'
UA_WEB = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
UA_ANDROID = 'Android 4.1.1; E270BSA; Crackle 4.4.5.0'
BASE_URL = 'https://prod-api.crackle.com'
# found in https://prod-api.crackle.com/appconfig (platformId)
WEB_KEY = '5FE67CCA-069A-42C6-A20F-4B47A8054D46'
PAGE_SIZE = ADDON.getSetting(id="page_size")
SORT = int(ADDON.getSetting(id="sort"))
SORT_ORDER = [
    "latest",
    "alpha-asc",
    "alpha-desc"
]

GENRES = {
    "All",
    "Action",
    "Adventure",
    "Anime",
    "Biography",
    "Black Entertainment",
    "British",
    "Classics",
    "Comedy",
    "Crackle Original",
    "Crime",
    "Documentary",
    "Drama",
    "Faith-Based",
    "Family",
    "Fantasy",
    "Foreign Language",
    "Holiday",
    "Horror",
    "Lifestyle",
    "Music / Musicals",
    "Mystery",
    "Reality Show",
    "Romance",
    "Sci-Fi",
    "Sports",
    "Stand-Up",
    "Thriller",
    "Unidentified / Unexplained",
    "Variety / Talk / Games",
    "Ware / Military",
    "Western"
    }


def main_menu():
    add_dir(LOCAL_STRING(30001), 'movies', 99, ICON)
    add_dir(LOCAL_STRING(30002), 'shows', 99, ICON)
    add_dir(LOCAL_STRING(30003), 'search', 104, ICON)

def list_genre(id):
    for genre in GENRES:
        add_dir(genre, id, 100, ICON, genre_id=genre)

    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

def list_movies_shows(type, genre, page_num):    
    url = f'/browse/{type}?enforcemediaRights=true&sortOrder={SORT_ORDER[SORT]}&pageNumber={page_num}&pageSize={PAGE_SIZE}'
    if genre != "All":
        url += f'&genreType={genre}'
    
    if page_num > 1:
        add_dir("<< Prev", type, 98, ICON, None, None, None, page_num-1)
        #add_dir("Home", 'home', 1, ICON)

    add_dir("Next >>", type, 98, ICON, None, None, None, page_num+1)

    json_source = json_request(url)  
    list_results(json_source['data']['items'])


def search(search_phrase):
    url = f"/contentdiscovery/search/{search_phrase}" \
          "?useFuzzyMatching=false" \
          "&enforcemediaRights=true" \
          f"&pageNumber=1&pageSize={PAGE_SIZE}" \
          "&contentType=Channels" \
          "&searchFields=Title%2CCast"
    
    json_source = json_request(url)
    list_results(json_source['data']['items'])


def list_results(list):           
    for item in list:
        metadata = item['metadata'][0]
        title = metadata['title']        
        content_id = item['id']        
        icon = get_image(item['assets']['images'], 220, 330)
        fanart = get_image(item['assets']['images'], 1920, 1080)
        info = {'plot': metadata['longDescription'],
                'title':title,
                'originaltitle':title,
                }
        
        if 'type' in item and 'movie' in item['type'].lower():
            add_stream(title, content_id,'movies',icon,fanart,info)            
        else:
            add_dir(title, content_id, 102, icon, fanart, info, content_type='tvshows', icon_url=icon)

def get_children(content_id, icon_url):
    url = f"/content/{content_id}/children"
    json_source = json_request(url)
    print(str(json_source))
    for item in json_source['data']:      
        if item['type'].lower() == "season":
            title = item['title']
            id = str(item['id'])           
            xbmc.log(f'icon URL: {icon_url}')
            add_dir(title,id,102,icon_url,FANART,content_type='tvshows')        
        else:
            title = item['title']
            id = str(item['id'])
            icon = get_image(item['images'], 400, 224)
            fanart = get_image(item['images'], 1920, 1080)
            info = {'plot':item['shortDescription'],                                
                    'title':title,
                    'originaltitle':title,
                    'duration':item['duration'],
                    'season':item['seasonNumber'],
                    'episode':item['episodeNumber'],
                    'mediatype': 'episode'
                    }

            add_stream(title,id,'tvshows',icon,fanart,info)

    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_EPISODE)


def get_movie_id(content_id):
    url = f"/content/{content_id}/children"
    json_source = json_request(url)
    print(str(json_source))
    for item in json_source['data']:                      
        id = str(item['id']) 
        break
    return id

def get_image(images, width, height):
    img = ICON
    for image in images:
        if image['width'] == width and image['height'] == height:
            img = image['url']
            break

    return img


def json_request(url):
    url = f'{BASE_URL}{url}'
    xbmc.log(url)
    headers = {
        'User-Agent': UA_WEB,
        'X-Crackle-Platform': WEB_KEY,
    }

    r = requests.get(url, headers=headers)
    if not r.ok:
        dialog = xbmcgui.Dialog()
        msg = r.json()['error']['message']        
        dialog.notification(LOCAL_STRING(30270), msg, ICON, 5000, False)
        sys.exit()

    return r.json()

def get_stream(id):    
    url = f'/playback/vod/{id}'
    json_source = json_request(url)
    stream_url = ''    
    for stream in json_source['data']['streams']:
        if 'widevine' in stream['type']:            
            stream_url = stream['url']
            lic_url = stream['drm']['keyUrl']
        
    
    listitem = xbmcgui.ListItem()
    if 'mpd' in stream_url:
        stream_url = get_stream_session(stream_url)
        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
        if not is_helper.check_inputstream():
            sys.exit()
    
        listitem.setPath(stream_url)
        listitem.setMimeType('application/dash+xml')
        listitem.setContentLookup(False)

        listitem.setProperty('inputstream', 'inputstream.adaptive')
        #listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd') # Deprecated on Kodi 21
        listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')

        license_headers = {
            'User-Agent': UA_WEB,            
            'Content-Type': 'application/octet-stream',            
            'origin': 'https://www.crackle.com',
            'referer': 'https://www.crackle.com/'
        }
        
        license_config = { # for Python < v3.7 you should use OrderedDict to keep order
            'license_server_url': lic_url,
            'headers': urlencode(license_headers),
            'post_data': 'R{SSM}',
            'response_data': 'R'
        }
        xbmc.log('|'.join(license_config.values()))
        listitem.setProperty('inputstream.adaptive.license_key', '|'.join(license_config.values()))
        listitem.setProperty('inputstream.adaptive.manifest_headers', urlencode(license_headers))
    else:
        # Return Error message
        sys.exit()

    xbmcplugin.setResolvedUrl(addon_handle, True, listitem)

def get_stream_session(url):            
    headers = {
        'User-Agent': UA_WEB,
    }

    r = requests.post(url, headers=headers, json={}, verify=False)
    if r.ok:
        stream_url = r.json()['manifestUrl']
        if 'https:' not in stream_url:
            # Get domain from url
            parsed_url = urlparse(url)
            scheme = parsed_url.scheme
            netloc = parsed_url.netloc
            full_domain = f"{scheme}://{netloc}"
            stream_url = f"{full_domain}{stream_url}"
    
    return stream_url


def add_stream(name, id, stream_type, icon, fanart, info=None):
    ok = True
    u=addon_url+"?id="+urllib.quote_plus(id)+"&mode="+str(103)+"&type="+urllib.quote_plus(stream_type)
    listitem=xbmcgui.ListItem(name)
    if fanart is None: fanart = FANART
    listitem.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'fanart': fanart})
    listitem.setProperty("IsPlayable", "true")
    if info is not None:
        listitem.setInfo( type="video", infoLabels=info)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=listitem,isFolder=False)
    xbmcplugin.setContent(addon_handle, stream_type)
    return ok


def add_dir(name, id, mode, icon, fanart=None, info=None, genre_id=None, page_num=None, icon_url=None, content_type='videos'):
    ok = True
    u = addon_url+"?id="+urllib.quote_plus(id)+"&mode="+str(mode)
    if genre_id is not None: u += f"&genre_id={genre_id}"
    if page_num is not None: u += f"&page_num={page_num}"
    if icon_url is not None: u += f"&icon_url={icon_url}"
    listitem=xbmcgui.ListItem(name)
    if fanart is None: fanart = FANART
    listitem.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'fanart': fanart})
    if info is not None:
        listitem.setInfo( type="video", infoLabels=info)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=listitem,isFolder=True)
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
