import sys, os
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import urllib
import base64
import requests
import random
from adobepass.adobe import ADOBE

addon_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon()
ROOTDIR = ADDON.getAddonInfo('path')

FANART = os.path.join(ROOTDIR, "resources", "media", "fanart.jpg")
ICON = os.path.join(ROOTDIR, "resources", "media", "icon.png")
VERIFY = False

# Addon Settings
RATIO = str(ADDON.getSetting(id="ratio"))
COMMENTARY = str(ADDON.getSetting(id="commentary"))
LOCAL_STRING = ADDON.getLocalizedString
INPUTSTREAM_ENABLED = str(ADDON.getSetting(id="inputstream_adaptive"))

RESOURCE_ID = "<rss version='2.0'><channel><title>fx</title></channel></rss>"
UA_FX = 'FXNOW/562 CFNetwork/711.4.6 Darwin/14.0.0'

# Add-on specific Adobepass variables
SERVICE_VARS = {'app_version': 'Fire TV',
                'device_type': 'firetv',
                'private_key': 'B081JNlGKn1ZqpQH',
                'public_key': 'Dy1OhW3HrWk03QJrMMIULAmUdPQqk2Ds',
                'registration_url': 'fxnetworks.com/activate',
                'requestor_id': 'fx',
                'resource_id': urllib.quote(RESOURCE_ID)
                }

art_root = 'http://thetvdb.com/banners/seasons/'
season_art = {'1': '71663-1-16.jpg',
              '2': '71663-2-15.jpg',
              '3': '71663-3-15.jpg',
              '4': '71663-4-16.jpg',
              '5': '71663-5-16.jpg',
              '6': '71663-6-15.jpg',
              '7': '71663-7-14.jpg',
              '8': '71663-8-14.jpg',
              '9': '71663-9-15.jpg',
              '10': '71663-10-15.jpg',
              '11': '71663-11-14.jpg',
              '12': '71663-12-10.jpg',
              '13': '71663-13-13.jpg',
              '14': '71663-14-13.jpg',
              '15': '71663-15-10.jpg',
              '16': '71663-16-11.jpg',
              '17': '71663-17-11.jpg',
              '18': '71663-18-10.jpg',
              '19': '71663-19-8.jpg',
              '20': '71663-20-11.jpg',
              '21': '71663-21-11.jpg',
              '22': '71663-22-9.jpg',
              '23': '71663-23-9.jpg',
              '24': '71663-24-4.jpg',
              '25': '71663-25-3.jpg',
              '26': '71663-26.jpg',
              '27': '71663-27-2.jpg',
              '28': '5bb0705e47a0a.jpg',
              '29': '5bb06fe5bf4af.jpg',
              '30': '5bb070d688a18.jpg'
              }

min_season = 1
max_season = 31


def list_seasons():
    properties = {'totaltime': '1380', 'resumetime': '0'}
    add_episode("Random[CR]Episode", str(0), "Random[CR]Episode",
                'https://www.thetvdb.com/banners/posters/71663-32.jpg', FANART, None, 103, properties)

    for x in range(min_season, max_season):
        title = "Season " + str(x)
        url = str(x)
        icon = art_root + season_art[str(x)]
        add_season(title, url, 101, icon, FANART)


def random_episode():
    # Get a random season
    season = random.randint(min_season, max_season)
    url = "http://fapi2.fxnetworks.com/androidtv/videos?filter%5Bfapi_show_id%5D=9aad7da1-093f-40f5-b371-fec4122f0d86" \
          "&filter%5Bseason%5D=" + str(season) + "&limit=500&filter%5Btype%5D=episode"

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "deflate",
        "Accept-Language": "en-us",
        "Connection": "keep-alive",
        "Authentication": "androidtv:a4y4o0e01jh27dsyrrgpvo6d1wvpravc2c4szpp4",
        "User-Agent": UA_FX,
    }

    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    episode_list = sorted(json_source['videos'], key=lambda k: k['episode'])
    # Get a random episode from that season
    elen = len(episode_list)
    elen -= 1
    enum = random.randint(1, elen)

    # Default video type is 16x9
    url = episode_list[enum]['video_urls']['16x9']['en_US']['video_url']
    try:
        url = episode_list[enum]['video_urls'][RATIO]['en_US']['video_url']
    except:
        pass
    if COMMENTARY == 'true':
        try:
            url = episode_list[enum]['video_urls'][RATIO]['en_US']['video_url_commentary']
        except:
            pass

    info = {'plot': episode_list[enum]['description'], 'tvshowtitle': LOCAL_STRING(30000), 'season': season,
            'episode': str(episode_list[enum]['episode']).zfill(2), 'title': episode_list[enum]['name'],
            'originaltitle': episode_list[enum]['name'], 'duration': episode_list[enum]['duration'],
            'aired': episode_list[enum]['airDate'], 'genre': LOCAL_STRING(30002)}

    get_stream(url, info)


def list_episode(season):
    url = "http://fapi2.fxnetworks.com/androidtv/videos?filter%5Bfapi_show_id%5D=9aad7da1-093f-40f5-b371-fec4122f0d86" \
          "&filter%5Bseason%5D=" + season + "&limit=500&filter%5Btype%5D=episode"

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "deflate",
        "Accept-Language": "en-us",
        "Connection": "keep-alive",
        "Authentication": "androidtv:a4y4o0e01jh27dsyrrgpvo6d1wvpravc2c4szpp4",
        "User-Agent": UA_FX,
    }

    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    # for episode in reversed(json_source['videos']):
    for episode in sorted(json_source['videos'], key=lambda k: k['episode']):
        title = episode['name']
        # Default video type is 16x9
        url = episode['video_urls']['16x9']['en_US']['video_url']
        try:
            url = episode['video_urls'][RATIO]['en_US']['video_url']
        except:
            pass
        if COMMENTARY == 'true':
            try:
                url = episode['video_urls'][RATIO]['en_US']['video_url_commentary']
            except:
               pass

        icon = episode['img_url']
        desc = episode['description']
        duration = episode['duration']
        aired = episode['airDate']
        season = str(episode['season']).zfill(2)
        episode = str(episode['episode']).zfill(2)

        info = {'plot': desc, 'tvshowtitle': LOCAL_STRING(30000), 'season': season, 'episode': episode, 'title': title,
                'originaltitle': title, 'duration': duration, 'aired': aired, 'genre': LOCAL_STRING(30002)}

        add_episode(title, url, title, icon, FANART, info)


def get_stream(url, INFO=None):
    adobe = ADOBE(SERVICE_VARS)
    if adobe.check_authn():
        if adobe.authorize():
            media_token = adobe.media_token()
            url = url + "&auth=" + urllib.quote(base64.b64decode(media_token))

            headers = {
                "Accept": "*/*",
                "Accept-Encoding": "deflate",
                "Accept-Language": "en-us",
                "Connection": "keep-alive",
                "User-Agent": UA_FX,
            }

            r = requests.get(url, headers=headers, verify=VERIFY)

            stream_url = r.url
            stream_url = stream_url + '|User-Agent=okhttp/3.4.1'

            if xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)') and INPUTSTREAM_ENABLED == 'true':
                listitem = xbmcgui.ListItem(path=stream_url.split("|")[0])
                listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
                listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
                listitem.setProperty('inputstream.adaptive.stream_headers', stream_url.split("|")[1])
                listitem.setProperty('inputstream.adaptive.license_key', "|" + stream_url.split("|")[1])
            else:
                listitem = xbmcgui.ListItem(path=stream_url)
                listitem.setMimeType("application/x-mpegURL")

            if INFO is not None:
                listitem.setInfo(type='Video', infoLabels=INFO)

            xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
        else:
            sys.exit()
    else:
        dialog = xbmcgui.Dialog()
        answer = dialog.yesno(LOCAL_STRING(30911), LOCAL_STRING(30910))
        if answer:
            adobe.register_device()
            get_stream(url, INFO)
        else:
            sys.exit()


def deauthorize():
    adobe = ADOBE(SERVICE_VARS)
    adobe.logout()
    dialog = xbmcgui.Dialog()
    dialog.notification(LOCAL_STRING(30900), LOCAL_STRING(30901), '', 5000, False)


def add_episode(name, link_url, title, iconimage, fanart, info=None, mode=102, properties=None):
    ok = True
    u = sys.argv[0] + "?url=" + urllib.quote_plus(link_url) + "&mode=" + str(mode)
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon': ICON, 'thumb': iconimage, 'fanart': fanart})
    liz.setProperty("IsPlayable", "true")
    liz.setInfo(type="Video", infoLabels={"Title": title, 'mediatype': 'episode'})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)
    if properties is not None:
        for key, value in properties.iteritems():
            liz.setProperty(key, value)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
    xbmcplugin.setContent(addon_handle, 'tvshows')
    return ok


def add_season(name, url, mode, iconimage, fanart=None, info=None):
    ok = True
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon': ICON, 'thumb': iconimage, 'fanart': fanart})
    liz.setInfo(type="Video", infoLabels={'Title': name, 'tvdb_id': '71663', 'mediatype': 'season'})
    if info != None:
        liz.setInfo(type="Video", infoLabels=info)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    xbmcplugin.setContent(addon_handle, 'tvshows')
    return ok


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param
