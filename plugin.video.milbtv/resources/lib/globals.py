# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for MiLB.TV compatibility and code cleanup

# coding=utf-8
import sys, re, os, time
import calendar, pytz
import urllib, requests
from datetime import date, datetime, timedelta
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
USERNAME = ADDON.getSettingString("username")
PASSWORD = ADDON.getSettingString("password")
QUALITY = ADDON.getSettingString("quality")
NO_SPOILERS = ADDON.getSetting("no_spoilers")
FAV_TEAM = ADDON.getSettingString("fav_team")
TIME_FORMAT = ADDON.getSetting("time_format")

#Colors
SCORE_COLOR = 'FF00B7EB'
GAMETIME_COLOR = 'FFFFFF66'
FAV_TEAM_COLOR = 'FFFF0000'

#Game Time Colors
UPCOMING = 'FFD2D2D2'
LIVE = 'FFF69E20'
CRITICAL ='FFD10D0D'
FINAL = 'FF666666'



#Images
ICON = ADDON.getAddonInfo('icon')
FANART = ADDON.getAddonInfo('fanart')
PREV_ICON = ICON
NEXT_ICON = ICON


#User Agents
UA_PC = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'

VERIFY = True

AFFILIATES = {'Athletics':'237,400,524,499','Pirates':'452,484,3390,477','Padres':'510,4904,103,584','Mariners':'574,403,515,529','Giants':'3410,105,461,476','Cardinals':'235,279,443,440','Rays':'234,421,233,2498','Rangers':'102,540,448,485','Blue Jays':'422,463,424,435','Twins':'3898,1960,492,509','Phillies':'1410,427,522,566','Braves':'430,431,432,478','White Sox':'247,580,487,494','Marlins':'4124,564,554,479','Yankees':'531,1956,537,587','Brewers':'556,5015,249,572','Angels':'559,561,401,460','D-backs':'2310,419,516,5368','Orioles':'418,568,548,488','Red Sox':'533,546,414,428','Cubs':'553,451,521,550','Reds':'416,498,450,459','Indians':'402,445,437,481','Rockies':'538,259,342,486','Tigers':'106,512,570,582','Astros':'482,3712,573,5434','Royals':'541,3705,1350,565','Dodgers':'238,260,526,456','Nationals':'534,547,426,436','Mets':'552,505,453,507'}


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


def easternToLocal(eastern_time):
    utc = pytz.utc
    eastern = pytz.timezone('US/Eastern')
    eastern_time = eastern.localize(eastern_time)
    # Convert it from Eastern to UTC
    utc_time = eastern_time.astimezone(utc)
    timestamp = calendar.timegm(utc_time.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    # Convert it from UTC to local time
    assert utc_time.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_time.microsecond)


def UTCToLocal(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def localToEastern():
    eastern = pytz.timezone('US/Eastern')
    local_to_utc = datetime.now(pytz.timezone('UTC'))

    eastern_hour = local_to_utc.astimezone(eastern).strftime('%H')
    eastern_date = local_to_utc.astimezone(eastern)
    #Don't switch to the current day until 4:01 AM est
    if int(eastern_hour) < 3:
        eastern_date = eastern_date - timedelta(days=1)

    local_to_eastern = eastern_date.strftime('%Y-%m-%d')
    return local_to_eastern

def easternToUTC(eastern_time):
    utc = pytz.utc
    eastern = pytz.timezone('US/Eastern')
    eastern_time = eastern.localize(eastern_time)
    # Convert it from Eastern to UTC
    utc_time = eastern_time.astimezone(utc)
    return utc_time


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


def add_stream(name, title, game_pk, icon=None, fanart=None, info=None, video_info=None, audio_info=None, stream_date=None):
    ok=True

    u=sys.argv[0]+"?mode="+str(104)+"&name="+urllib.quote_plus(name)+"&game_pk="+urllib.quote_plus(str(game_pk))+"&stream_date="+urllib.quote_plus(str(stream_date))

    liz=xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if info is not None:
        liz.setInfo( type="Video", infoLabels=info)
    if video_info is not None:
        liz.addStreamInfo('video', video_info)
    if audio_info is not None:
        liz.addStreamInfo('audio', audio_info)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, 'episodes')

    return ok


def addDir(name,mode,icon=None,fanart=None,game_day=None,level=None,teams=None):
    ok=True

    u=sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(name)
    if game_day is not None:
        u = u+"&game_day="+urllib.quote_plus(game_day)
    if level is not None:
        u = u+"&level="+urllib.quote_plus(level)
    if teams is not None:
        u = u+"&teams="+urllib.quote_plus(teams)

    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})

    liz.setInfo( type="Video", infoLabels={ "Title": name } )

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def getAudioVideoInfo(resolution):
    if resolution == 'SD':
        video_info = { 'codec': 'h264', 'width' : 640, 'height' : 360, 'aspect' : 1.78 }
    else:
        video_info = { 'codec': 'h264', 'width' : 1280, 'height' : 720, 'aspect' : 1.78 }

    audio_info = { 'codec': 'aac', 'language': 'en', 'channels': 2 }
    return audio_info, video_info


def getStreamQuality(stream_url):
    stream_title = []
    r = reguests.get(stream_url, headers={'User-Agent': UA_PC})
    master = r.text()

    line = re.compile("(.+?)\n").findall(master)

    for temp_url in line:
        if '.m3u8' in temp_url:
            temp_url = temp_url
            match = re.search(r'(\d.+?)K', temp_url)
            if match:
                bandwidth = match.group()
                if 0 < len(bandwidth) < 6:
                    bandwidth = bandwidth.replace('K',' ' + LOCAL_STRING(30413))
                    stream_title.append(bandwidth)


    stream_title.sort(key=natural_sort_key,reverse=True)
    dialog = xbmcgui.Dialog()
    ret = dialog.select(LOCAL_STRING(30372), stream_title)
    if ret >=0:
        bandwidth = find(stream_title[ret],'',' ' + LOCAL_STRING(30413))
    else:
        sys.exit()

    return bandwidth

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


def stream_to_listitem(stream_url, headers):
    if xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):
        listitem = xbmcgui.ListItem(path=stream_url)
        if KODI_VERSION >= 19:
            listitem.setProperty('inputstream', 'inputstream.adaptive')
        else:
            listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        listitem.setProperty('inputstream.adaptive.stream_headers', headers)
    else:
        listitem = xbmcgui.ListItem(path=stream_url + '|' + headers)

    listitem.setMimeType("application/x-mpegURL")
    return listitem
