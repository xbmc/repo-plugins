# coding=utf-8
import sys, re, os, time
import calendar, pytz
import urllib, requests
from datetime import date, datetime, timedelta
from dateutil.parser import parse
import json
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


#Addon Info
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
KODI_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString
ROOTDIR = ADDON.getAddonInfo('path')

#Settings
settings = xbmcaddon.Addon(id='plugin.video.mlbtv')
USERNAME = str(settings.getSetting(id="username"))
PASSWORD = str(settings.getSetting(id="password"))
OLD_USERNAME = str(settings.getSetting(id="old_username"))
OLD_PASSWORD = str(settings.getSetting(id="old_password"))
QUALITY = str(settings.getSetting(id="quality"))
CDN = str(settings.getSetting(id="cdn"))
IN_MARKET = str(settings.getSetting(id="in_market"))
NO_SPOILERS = settings.getSetting(id="no_spoilers")
FAV_TEAM = str(settings.getSetting(id="fav_team"))
TEAM_NAMES = settings.getSetting(id="team_names")
TIME_FORMAT = settings.getSetting(id="time_format")
SINGLE_TEAM = str(settings.getSetting(id='single_team'))
CATCH_UP = str(settings.getSetting(id='catch_up'))
ONLY_FREE_GAMES = str(settings.getSetting(id="only_free_games"))

#Proxy Settings
PROXY_ENABLED = str(settings.getSetting(id='use_proxy'))
PROXY_SERVER = str(settings.getSetting(id='proxy_server'))
PROXY_PORT = str(settings.getSetting(id='proxy_port'))
PROXY_USER = str(settings.getSetting(id='proxy_user'))
PROXY_PWD = str(settings.getSetting(id='proxy_pwd'))

#Colors
SCORE_COLOR = 'FF00B7EB'
GAMETIME_COLOR = 'FFFFFF66'
#FAV_TEAM_COLOR = 'FFFF0000'
FREE_GAME_COLOR = 'FF43CD80'

#Game Time Colors
UPCOMING = 'FFD2D2D2'
LIVE = 'FFF69E20'
CRITICAL ='FFD10D0D'
FINAL = 'FF666666'
FREE = 'FF43CD80'



#Images
ICON = os.path.join(ROOTDIR,"icon.png")
FANART = os.path.join(ROOTDIR,"fanart.jpg")
PREV_ICON = os.path.join(ROOTDIR,"icon.png")
NEXT_ICON = os.path.join(ROOTDIR,"icon.png")

if SINGLE_TEAM == 'true':
    MASTER_FILE_TYPE = 'master_wired.m3u8'
    PLAYBACK_SCENARIO = 'HTTP_CLOUD_WIRED'
else:
    MASTER_FILE_TYPE = 'master_wired60.m3u8'
    PLAYBACK_SCENARIO = 'HTTP_CLOUD_WIRED_60'


#User Agents
UA_IPAD = 'AppleCoreMedia/1.0 ( iPad; compatible; 3ivx HLS Engine/2.0.0.382; Win8; x64; 264P AACP AC3P AESD CLCP HTPC HTPI HTSI MP3P MTKA)'
UA_PC = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
UA_ANDROID = 'okhttp/3.12.1'

VERIFY = True

#Big Inning
BIG_INNING_LIVE_NAME = 'LIVE NOW: MLB Big Inning'


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


def add_stream(name, title, game_pk, icon=None, fanart=None, info=None, video_info=None, audio_info=None, stream_date=None, spoiler='True'):
    ok=True
    u=sys.argv[0]+"?mode="+str(104)+"&name="+urllib.quote_plus(name)+"&game_pk="+urllib.quote_plus(str(game_pk))+"&stream_date="+urllib.quote_plus(str(stream_date))+"&spoiler="+urllib.quote_plus(str(spoiler))

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


def addLink(name,url,title,icon,info=None,video_info=None,audio_info=None,fanart=None):
    ok=True
    liz=xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setProperty('fanart_image', FANART)

    if info is not None:
        liz.setInfo( type="Video", infoLabels=info)
    if video_info is not None:
        liz.addStreamInfo('video', video_info)
    if audio_info is not None:
        liz.addStreamInfo('audio', audio_info)

    if fanart is not None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    xbmcplugin.setContent(addon_handle, 'episodes')
    return ok


def addDir(name,mode,icon,fanart=None,game_day=None):
    ok=True

    u=sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&icon="+urllib.quote_plus(icon)
    if game_day is not None:
        u = u+"&game_day="+urllib.quote_plus(game_day)

    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})

    liz.setInfo( type="Video", infoLabels={ "Title": name } )

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def addPlaylist(name,game_day,mode,icon,fanart=None):
    ok=True    
    u=sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&icon="+urllib.quote_plus(icon)+"&stream_date="+urllib.quote_plus(str(game_day))

    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    game_day_display = parse(game_day).strftime('%A, %B %d, %Y')
    info = {'plot': LOCAL_STRING(30375)+game_day_display,'tvshowtitle':'MLB','title':name,'originaltitle':name,'aired':game_day,'genre':LOCAL_STRING(700),'mediatype':'video'}
    # Get audio/video info
    audio_info, video_info = getAudioVideoInfo()

    liz.setInfo( type="Video", infoLabels=info)
    liz.addStreamInfo('video', video_info)
    liz.addStreamInfo('audio', audio_info)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)    
    #xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def getFavTeamColor():
    #Hex code taken from http://jim-nielsen.com/teamcolors/    
    team_colors = {'Arizona Diamondbacks': 'FFA71930',
                   'Atlanta Braves': 'FFCE1141',
                   'Baltimore Orioles': 'FFDF4601',
                   'Boston Red Sox': 'FFBD3039',
                   'Chicago Cubs': 'FFCC3433',
                   'Chicago White Sox': 'FFC4CED4',
                   'Cincinnati Reds': 'FFC6011F',
                   'Cleveland Guardians': 'FFE31937',
                   'Colorado Rockies': 'FFC4CED4',
                   'Detroit Tigers': 'FF0C2C56',
                   'Houston Astros': 'FFEB6E1F',
                   'Kansas City Royals': 'FFC09A5B',
                   'Los Angeles Angels': 'FFBA0021',
                   'Los Angeles Dodgers': 'FFEF3E42',
                   'Miami Marlins': 'FFFF6600',
                   'Milwaukee Brewers': 'FFB6922E',
                   'Minnesota Twins': 'FFD31145',
                   'New York Mets': 'FFFF5910',
                   'New York Yankees': 'FFE4002B',
                   'Oakland Athletics': 'FFEFB21E',
                   'Philadelphia Phillies': 'FFE81828',
                   'Pittsburgh Pirates': 'FFFDB827',
                   'St. Louis Cardinals': 'FFC41E3A',
                   'San Diego Padres': 'FF05143F',
                   'San Francisco Giants': 'FFFD5A1E',
                   'Seattle Mariners': 'FFC4CED4',
                   'Tampa Bay Rays': 'FF8FBCE6',
                   'Texas Rangers': 'FFC0111F',
                   'Toronto Blue Jays': 'FFE8291C',
                   'Washington Nationals': 'FFAB0003'}

    fav_team_color = team_colors[FAV_TEAM]
    
    return fav_team_color


def getFavTeamId():
    #possibly use the xml file in the future
    #http://mlb.mlb.com/shared/properties/mlb_properties.xml  
    team_ids = {'Arizona Diamondbacks': '109',
                'Atlanta Braves': '144',
                'Baltimore Orioles': '110',
                'Boston Red Sox': '111',
                'Chicago Cubs': '112',
                'Chicago White Sox': '145',
                'Cincinnati Reds': '113',
                'Cleveland Guardians': '114',
                'Colorado Rockies': '115',
                'Detroit Tigers': '116',
                'Houston Astros': '117',
                'Kansas City Royals': '118',
                'Los Angeles Angels': '108',
                'Los Angeles Dodgers': '119',
                'Miami Marlins': '146',
                'Milwaukee Brewers': '158',
                'Minnesota Twins': '142',
                'New York Mets': '121',
                'New York Yankees': '147',
                'Oakland Athletics': '133',
                'Philadelphia Phillies': '143',
                'Pittsburgh Pirates': '134',
                'St. Louis Cardinals': '138',
                'San Diego Padres': '135',
                'San Francisco Giants': '137',
                'Seattle Mariners': '136',
                'Tampa Bay Rays': '139',
                'Texas Rangers': '140',
                'Toronto Blue Jays': '141',
                'Washington Nationals': '120'}
    
    fav_team_id = team_ids[FAV_TEAM]

    return  fav_team_id


def getAudioVideoInfo():
    video_info = { 'codec': 'h264', 'width' : 1280, 'height' : 720, 'aspect' : 1.78 }
    audio_info = { 'codec': 'aac', 'language': 'en', 'channels': 2 }
    return audio_info, video_info


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


def stream_to_listitem(stream_url, headers, spoiler='True', start='1', stream_type='video'):
    # check if our stream is HLS
    if '.m3u8' in stream_url:
        # if not audio only, check if inputstream.adaptive is present and enabled, depending on Kodi version
        if stream_type != 'audio' and (xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)') or (KODI_VERSION >= 19 and xbmc.getCondVisibility('System.AddonIsEnabled(inputstream.adaptive)'))):
            listitem = xbmcgui.ListItem(path=stream_url)
            if KODI_VERSION >= 19:
                listitem.setProperty('inputstream', 'inputstream.adaptive')
            else:
                listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
            listitem.setProperty('inputstream.adaptive.stream_headers', headers)
            listitem.setProperty('inputstream.adaptive.license_key', "|" + headers)
            # start stream at beginning if no spoilers
            if spoiler == "False":
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
