# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for MiLB.TV compatibility and code cleanup

# coding=utf-8
import sys, re, os, time
import calendar, pytz
import urllib, requests
from datetime import date, datetime, timedelta
from dateutil.parser import parse
import json
from kodi_six import xbmc, xbmcvfs, xbmcplugin, xbmcgui, xbmcaddon
import random

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
settings = xbmcaddon.Addon(id='plugin.video.milbtv')
USERNAME = str(settings.getSetting(id='username'))
PASSWORD = str(settings.getSetting(id='password'))
QUALITY = str(settings.getSetting(id='quality'))
NO_SPOILERS = str(settings.getSetting(id='no_spoilers'))
DISABLE_VIDEO_PADDING = str(settings.getSetting(id='disable_video_padding'))
FAV_TEAM = str(settings.getSetting(id='fav_team'))
TIME_FORMAT = str(settings.getSetting(id='time_format'))
CATCH_UP = str(settings.getSetting(id='catch_up'))
ASK_TO_SKIP = str(settings.getSetting(id='ask_to_skip'))

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


API_URL = 'https://statsapi.mlb.com'
#User Agents
UA_PC = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'

VERIFY = True

ALL_LEVELS = '11,12,13,14'

AFFILIATES = { 'Angels': '401,559,561,460', 'Astros': '3712,573,482,5434', 'Athletics': '237,400,524,499', 'Blue Jays': '422,424,435,463', 'Braves': '430,431,432,478', 'Brewers': '249,556,572,5015', 'Cardinals': '235,279,440,443', 'Cubs': '521,553,451,550', 'D-backs': '2310,419,516,5368', 'Dodgers': '238,260,526,456', 'Giants': '3410,105,461,476', 'Guardians': '402,437,445,481', 'Mariners': '403,515,529,574', 'Marlins': '4124,564,554,479', 'Mets': '552,453,505,507', 'Nationals': '436,426,534,547', 'Orioles': '418,568,488,548', 'Padres': '103,584,510,4904', 'Phillies': '1410,427,522,566', 'Pirates': '3390,452,477,484', 'Rangers': '102,540,448,485', 'Rays': '233,234,421,2498', 'Red Sox': '414,428,533,546', 'Reds': '416,450,459,498', 'Rockies': '259,342,538,486', 'Royals': '3705,1350,541,565', 'Tigers': '106,570,582,512', 'Twins': '3898,492,509,1960', 'White Sox': '247,580,487,494', 'Yankees': '531,587,1956,537' }

#Skip monitor
#These are the break events to skip
BREAK_TYPES = ['Game Advisory', 'Pitching Substitution', 'Offensive Substitution', 'Defensive Sub', 'Defensive Switch', 'Runner Placed On Base', 'Injury']
#These are the action events to keep, in addition to the last event of each at-bat, if we're skipping non-decision pitches
ACTION_TYPES = ['Wild Pitch', 'Passed Ball', 'Stolen Base', 'Caught Stealing', 'Pickoff', 'Error', 'Out', 'Balk', 'Defensive Indiff']
#Pad events at both start (-) and end (+)
EVENT_START_PADDING = 4
EVENT_END_PADDING = 17
MINIMUM_BREAK_DURATION = 10

SECONDS_PER_SEGMENT = 4


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
    return get_eastern_game_date(datetime.now(pytz.timezone('UTC')))


def easternToUTC(eastern_time):
    utc = pytz.utc
    eastern = pytz.timezone('US/Eastern')
    eastern_time = eastern.localize(eastern_time)
    # Convert it from Eastern to UTC
    utc_time = eastern_time.astimezone(utc)
    return utc_time


def get_eastern_game_date(timestamp):
    eastern = pytz.timezone('US/Eastern')
    eastern_hour = timestamp.astimezone(eastern).strftime('%H')
    eastern_date = timestamp.astimezone(eastern)
    #Don't switch to the current day until 4:00 AM est
    if int(eastern_hour) < 4:
        eastern_date = eastern_date - timedelta(days=1)
    return eastern_date.strftime('%Y-%m-%d')


def yesterdays_date():
    game_day = localToEastern()
    display_day = stringToDate(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)
    return prev_day.strftime("%Y-%m-%d")


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


def add_stream(name, title, game_pk, icon=None, fanart=None, info=None, video_info=None, audio_info=None, spoiler='True', suspended='False', start_inning='False', status='Preview'):
    ok=True

    u=sys.argv[0]+"?mode="+str(104)+"&name="+urllib.quote_plus(name)+"&game_pk="+urllib.quote_plus(str(game_pk))+"&spoiler="+urllib.quote_plus(str(spoiler))+"&suspended="+urllib.quote_plus(str(suspended))+"&start_inning="+urllib.quote_plus(str(start_inning))+"&status="+urllib.quote_plus(str(status))

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


def addDir(name,mode,game_day=None,start_inning='False',level=None,teams=None):
    ok=True

    u=sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(name)
    if game_day is not None:
        u = u+"&game_day="+urllib.quote_plus(game_day)
    if start_inning != 'False':
        u = u+"&start_inning="+urllib.quote_plus(start_inning)
    if level is not None:
        u = u+"&level="+urllib.quote_plus(level)
    if teams is not None:
        u = u+"&teams="+urllib.quote_plus(teams)

    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon': ICON, 'thumb': ICON, 'fanart': FANART})

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


def stream_to_listitem(stream_url, headers, start='1'):
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
    return listitem


def get_inning_start_options():
    start_options = []
    # add start options for each inning 1-12
    for x in range(1, 13):
        start_options.append(LOCAL_STRING(30422) + ' ' + LOCAL_STRING(30421) + ' ' + str(x)) # top
        start_options.append(LOCAL_STRING(30423) + ' ' + LOCAL_STRING(30421) + ' ' + str(x)) # bottom
    return start_options


def calculate_inning_from_index(index):
    inning_half = 'top'
    inning = int(round(((index+0.5) / 2), 0))
    if (index % 2) == 0 and ((index+1) % 2) == 1:
        inning_half = 'bottom'
    return inning, inning_half


def get_last_name(full_name):
    try:
        return full_name.split(' ', 1)[1]
    except:
        pass
    return full_name


def get_broadcast_start_timestamp(stream_url):
    broadcast_start_timestamp = None
    try:
        url = stream_url[:len(stream_url)-5] + '_5472K.m3u8'
        headers = {
            'User-Agent': UA_PC,
             'Origin': 'https://www.milb.com',
             'Referer': 'https://www.milb.com/'
        }
        r = requests.get(url, headers=headers, verify=VERIFY)
        content = r.text
        line_array = content.splitlines()
        for line in line_array:
            if line.startswith('#EXT-X-PROGRAM-DATE-TIME:'):
                broadcast_start_timestamp = parse(line[25:])
                xbmc.log('Found broadcast start timestamp ' + str(broadcast_start_timestamp))
                break
    except:
        xbmc.log('Failed to find broadcast start timestamp')
        pass
    return broadcast_start_timestamp
