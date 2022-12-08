import sys
import re, os, time
import calendar, pytz
import requests, urllib
from datetime import datetime, timedelta
from kodi_six import xbmc, xbmcvfs, xbmcplugin, xbmcgui, xbmcaddon

if sys.version_info[0] > 2:
    import http

    cookielib = http.cookiejar
    urllib = urllib.parse
else:
    import cookielib

try:
    xbmc.translatePath = xbmcvfs.translatePath
except AttributeError:
    pass

addon_handle = int(sys.argv[1])

# Addon Info
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
KODI_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString

# Settings
settings = ADDON
USERNAME = settings.getSetting("username")
PASSWORD = settings.getSetting("password")
TIME_FORMAT = settings.getSetting("time_format")

ROOTDIR = xbmcaddon.Addon().getAddonInfo('path')
USER_DATA_DIR = os.path.join(xbmc.translatePath("special://userdata"), 'addon_data', ADDON_ID)
ICON = os.path.join(ROOTDIR, "icon.png")
FANART = os.path.join(ROOTDIR, "fanart.jpg")
PREV_ICON = os.path.join(ROOTDIR, "icon.png")
NEXT_ICON = os.path.join(ROOTDIR, "icon.png")

API_URL = 'http://statsapi.web.nhl.com/api/v1'
API_MEDIA_URL = 'https://mf.svc.nhl.com/ws/media/mf/v2.4'
VERIFY = True
ICON_URL = "https://nhltv.nhl.com/image/400/225/"
FANART_URL = "https://nhltv.nhl.com/image/1920/1080/"
UA_PC = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'

# Playlists
RECAP_PLAYLIST = xbmc.PlayList(0)
EXTENDED_PLAYLIST = xbmc.PlayList(1)


def string_to_date(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))

    return date


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def local_to_eastern():
    eastern = pytz.timezone('US/Eastern')
    local_to_utc = datetime.now(pytz.timezone('UTC'))

    eastern_hour = local_to_utc.astimezone(eastern).strftime('%H')
    eastern_date = local_to_utc.astimezone(eastern)
    # Don't switch to the current day until 4:01 AM est
    if int(eastern_hour) < 3:
        eastern_date = eastern_date - timedelta(days=1)

    local_to_eastern = eastern_date.strftime('%Y-%m-%d')
    return local_to_eastern


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


def add_stream(name, title, icon=None, fanart=None, info=None,  **kwargs):
    ok = True
    u = sys.argv[0] + f"?url=''&mode=104&name={urllib.quote_plus(name.encode('utf8'))}"
    for key, value in kwargs.items():
        u += f"&{key}={value}"

    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setProperty("IsPlayable", "true")
    liz.setInfo(type="Video", infoLabels={"Title": title})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)

    audio_info, video_info = getAudioVideoInfo()
    liz.addStreamInfo('video', video_info)
    liz.addStreamInfo('audio', audio_info)
    liz.setProperty('dbtype', 'video')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
    xbmcplugin.setContent(addon_handle, 'videos')

    return ok


def add_link(name, url, title, icon, info=None, video_info=None, audio_info=None, fanart=None):
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo(type="Video", infoLabels={"Title": title})
    liz.setProperty('fanart_image', FANART)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})

    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)
    if video_info is not None:
        liz.addStreamInfo('video', video_info)
    if audio_info is not None:
        liz.addStreamInfo('audio', audio_info)

    liz.setProperty('dbtype', 'video')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    xbmcplugin.setContent(addon_handle, 'videos')
    return ok


def add_dir(name, url, mode, icon, fanart=None, game_day=None):
    ok = True
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) \
        + "&icon=" + urllib.quote_plus(icon)
    if game_day is not None:
        u = u + "&game_day=" + urllib.quote_plus(game_day)
    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})

    liz.setInfo(type="Video", infoLabels={"Title": name})

    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    return ok


def addPlaylist(name, game_day, url, mode, icon, fanart=None):
    ok = True
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(
        name) + "&icon=" + urllib.quote_plus(icon)
    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setInfo(type="Video", infoLabels={"Title": name})

    if fanart is not None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    info = {'plot': 'Watch all the days highlights for ' + game_day.strftime("%m/%d/%Y"), 'tvshowtitle': 'NHL',
            'title': name, 'originaltitle': name, 'aired': game_day.strftime("%Y-%m-%d"), 'genre': 'Sports'}
    audio_info, video_info = getAudioVideoInfo()

    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)
    if video_info is not None:
        liz.addStreamInfo('video', video_info)
    if audio_info is not None:
        liz.addStreamInfo('audio', audio_info)

    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
    return ok

def getAudioVideoInfo():
    video_info = {'codec': 'h264', 'width': 1280, 'height': 720, 'aspect': 1.78}
    audio_info = {'codec': 'aac', 'language': 'en', 'channels': 2}
    return audio_info, video_info


def load_cookies():
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file, ignore_discard=True)
    except:
        pass

    return cj


def save_cookies(cookiejar):
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file, ignore_discard=True)
    except:
        pass
    for c in cookiejar:
        args = dict(vars(c).items())
        args['rest'] = args['_rest']
        del args['_rest']
        c = cookielib.Cookie(**args)
        cj.set_cookie(c)
    cj.save(cookie_file, ignore_discard=True)


def getAuthCookie():
    authorization = ''
    try:
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'), ignore_discard=True)

        # If authorization cookie is missing or stale, perform login
        for cookie in cj:
            if cookie.name == "token" and not cookie.is_expired():
                authorization = cookie.value
    except:
        pass

    return authorization


def stream_to_listitem(stream_url):
    if xbmc.getCondVisibility("System.HasAddon(inputstream.adaptive)"):
        listitem = xbmcgui.ListItem(path=stream_url)
        if KODI_VERSION >= 19:
            listitem.setProperty("inputstream", "inputstream.adaptive")
        else:
            listitem.setProperty("inputstreamaddon", "inputstream.adaptive")
        listitem.setProperty("inputstream.adaptive.manifest_type", "hls")
        listitem.setProperty("inputstream.adaptive.stream_headers",  'User-Agent=%s' % UA_PC)
        listitem.setProperty("inputstream.adaptive.license_key", '|User-Agent=%s' % UA_PC)
    else:
        listitem = xbmcgui.ListItem(path=f"{stream_url}|{headers}")

    listitem.setMimeType("application/x-mpegURL")
    return listitem
