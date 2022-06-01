# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for NWL compatibility and code cleanup

# coding=utf-8
import sys, re, os, time
import calendar, pytz
import urllib, requests
from datetime import date, datetime, timedelta
from dateutil.parser import parse
from kodi_six import xbmc, xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs

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


#Addon Info
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
KODI_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString
ROOTDIR = ADDON.getAddonInfo('path')

#Settings
settings = xbmcaddon.Addon(id='plugin.video.nwl')
FAV_TEAM = ADDON.getSettingString("fav_team")
TIME_FORMAT = ADDON.getSetting("time_format")
CATCH_UP = str(settings.getSetting(id='catch_up'))

#Colors
#SCORE_COLOR = 'FF00B7EB'
GAMETIME_COLOR = 'FFFFFF66'
FAV_TEAM_COLOR = 'FFFF0000'

#Game Time Colors
UPCOMING = 'FFD2D2D2'
LIVE = 'FFF69E20'
#CRITICAL ='FFD10D0D'
FINAL = 'FFA3A3A3'



#Images
ICON = ADDON.getAddonInfo('icon')
FANART = ADDON.getAddonInfo('fanart')


#User Agent
UA_PC = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36'

ORIGIN = 'https://ep.stretchlive.com'

REFERER = ORIGIN + '/'

#Default headers
HEADERS = {
    'User-Agent': UA_PC,
    'Origin': ORIGIN,
    'Referer': REFERER
}

VERIFY = True

TEAM_LOGOS = { 'Battle Creek Battle Jacks': '60Battle-Creek-Battle-Jacks-Icon',
               'Bismarck Larks': '50Bismarck',
               'Duluth Huskies': '51Duluth',
               'Eau Claire Express': '52EauClaire',
               'Fond du Lac Dock Spiders': '70Logo-FDL',
               'Green Bay Rockers': '61Green-Bay-Rockers-Primary',
               'Kalamazoo Growlers': '62Kalamazoo',
               'Kenosha Kingfish': '63Kenosha',
               'Kokomo Jackrabbits': '73Kokomo',
               'La Crosse Loggers': '53La-Crosse',
               'Lakeshore Chinooks': '64Lakeshore',
               'Madison Mallards': '65Madison',
               'Mankato MoonDogs': '54Mankato',
               'Minnesota Mud Puppies': '83Minnesota',
               'Rochester Honkers': '55Logo-ROC',
               'Rockford Rivets': '66Rockford',
               'St. Cloud Rox': '56StCloud',
               'Thunder Bay Border Cats': '66Rockford',
               'Traverse City Pit Spitters': 'https://neo-cdn.stretchinternet.com/geaNcs/TraverseCity.png',
               'Waterloo Bucks': '58Waterloo',
               'Wausau Woodchucks': '68Logo-WAU',
               'Willmar Stingers': '59Willmar',
               'Wisconsin Rapids Rafters': '67WisconsinRapids' }

PAGE_LENGTH = 25


def find(source,start_str,end_str):
    start = source.find(start_str)
    end = source.find(end_str,start+len(start_str))

    if start != -1:
        return source[start+len(start_str):end]
    else:
        return ''


def colorString(string, color):
    return '[COLOR='+color+']'+string+'[/COLOR]'


def stringToDate(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))

    return date


def UTCToLocal(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def localToEastern():
    return get_eastern_game_date(datetime.now(pytz.timezone('UTC')))


def get_eastern_game_date(timestamp):
    eastern = pytz.timezone('US/Eastern')
    eastern_hour = timestamp.astimezone(eastern).strftime('%H')
    eastern_date = timestamp.astimezone(eastern)
    #Don't switch to the current day until 4:00 AM est
    if int(eastern_hour) < 4:
        eastern_date = eastern_date - timedelta(days=1)
    return eastern_date.strftime('%Y-%m-%d')


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


def add_stream(name, title, id, icon, info):
    ok=True

    u=sys.argv[0]+"?mode="+str(104)+"&id="+urllib.quote_plus(str(id))

    liz=xbmcgui.ListItem(name)
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': FANART})
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setInfo( type="Video", infoLabels=info)
    liz.addStreamInfo('video', {'codec': 'h264', 'width' : 1280, 'height' : 720, 'aspect' : 1.78})
    liz.addStreamInfo('audio', {'codec': 'aac', 'language': 'en', 'channels': 2})

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, 'episodes')

    return ok


def addDir(name,mode,page_start=0):
    ok=True

    u=sys.argv[0]+"?mode="+str(mode)
    if page_start > 0:
        u += "&page_start="+str(page_start)

    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon': ICON, 'thumb': ICON, 'fanart': FANART})

    liz.setInfo( type="Video", infoLabels={ "Title": name } )

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def natural_sort_key(s):
    _nsre = re.compile('([0-9]+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]


def save_cookies(cookiejar):
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file,ignore_discard=True)
    except:
        pass
    for c in cookiejar:
        args = dict(vars(c).items())
        args['rest'] = args['_rest']
        del args['_rest']
        c = cookielib.Cookie(**args)
        cj.set_cookie(c)
    cj.save(cookie_file, ignore_discard=True)


def load_cookies():
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file, ignore_discard=True)
    except:
        pass

    return cj


def stream_to_listitem(stream_url, start='-1'):
    headers = 'User-Agent=' + UA_PC
    headers += '&Origin=' + ORIGIN
    headers += '&Referer=' + REFERER
    # check if our stream is HLS
    if '.m3u8' in stream_url:
        # check if inputstream.adaptive is present and enabled, depending on Kodi version
        if xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)') or (KODI_VERSION >= 19 and xbmc.getCondVisibility('System.AddonIsEnabled(inputstream.adaptive)')):
            listitem = xbmcgui.ListItem(path=stream_url)
            if KODI_VERSION >= 19:
                listitem.setProperty('inputstream', 'inputstream.adaptive')
            else:
                listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
            listitem.setProperty('inputstream.adaptive.stream_headers', headers)
            # if not using Kodi's resume function, set the start time
            if sys.argv[3] != 'resume:true' and start != '-1':
                listitem.setProperty('ResumeTime', start)
                listitem.setProperty('TotalTime', start)
        else:
            listitem = xbmcgui.ListItem(path=stream_url + '|' + headers)

        listitem.setMimeType("application/x-mpegURL")
    # otherwise, if not HLS, assume it is MP4
    else:
        listitem = xbmcgui.ListItem(path=stream_url + '|' + headers)
        listitem.setMimeType("video/mp4")

    return listitem
