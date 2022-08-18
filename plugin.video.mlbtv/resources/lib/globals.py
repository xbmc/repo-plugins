# coding=utf-8
import sys, re, os, time
import calendar, pytz
import urllib, requests
from datetime import date, datetime, timedelta
from dateutil.parser import parse
import json
from kodi_six import xbmc, xbmcvfs, xbmcplugin, xbmcgui, xbmcaddon
import random
from collections import namedtuple, deque

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
NO_SPOILERS = settings.getSetting(id="no_spoilers")
DISABLE_VIDEO_PADDING = str(settings.getSetting(id='disable_video_padding'))
FAV_TEAM = str(settings.getSetting(id="fav_team"))
TEAM_NAMES = settings.getSetting(id="team_names")
TIME_FORMAT = settings.getSetting(id="time_format")
SINGLE_TEAM = str(settings.getSetting(id='single_team'))
AUTO_SELECT_STREAM = str(settings.getSetting(id='auto_select_stream'))
CATCH_UP = str(settings.getSetting(id='catch_up'))
ASK_TO_SKIP = str(settings.getSetting(id='ask_to_skip'))
AUTO_PLAY_FAV = str(settings.getSetting(id='auto_play_fav'))
ONLY_FREE_GAMES = str(settings.getSetting(id="only_free_games"))
GAME_CHANGER_DELAY = int(settings.getSetting(id="game_changer_delay"))

#Monitor setting
MLB_MONITOR_STARTED = settings.getSetting(id='mlb_monitor_started')
now = datetime.now()
if MLB_MONITOR_STARTED != '' and not xbmc.getCondVisibility("Player.HasMedia") and (parse(MLB_MONITOR_STARTED) + timedelta(seconds=5)) < now:
    xbmc.log("MLB Monitor detection resetting due to no stream playing")
    settings.setSetting(id='mlb_monitor_started', value='')

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

API_URL = 'https://statsapi.mlb.com'
#User Agents
UA_IPAD = 'AppleCoreMedia/1.0 ( iPad; compatible; 3ivx HLS Engine/2.0.0.382; Win8; x64; 264P AACP AC3P AESD CLCP HTPC HTPI HTSI MP3P MTKA)'
UA_PC = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
UA_ANDROID = 'okhttp/3.12.1'

VERIFY = True

SECONDS_PER_SEGMENT = 5

def find(source,start_str,end_str):    
    start = source.find(start_str)
    end = source.find(end_str,start+len(start_str))

    if start != -1:        
        return source[start+len(start_str):end]
    else:
        return ''


def colorString(string, color):
    return '[COLOR='+color+']'+string+'[/COLOR]'


def blackoutString(string):
    return '* ' + string + ' *'


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
    #Don't switch to the current day until 4:01 AM est
    if int(eastern_hour) < 3:
        eastern_date = eastern_date - timedelta(days=1)
    return eastern_date.strftime('%Y-%m-%d')


def yesterdays_date():
    game_day = localToEastern()
    display_day = stringToDate(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)
    return prev_day.strftime("%Y-%m-%d")


def get_display_time(timestamp):
    if TIME_FORMAT == '0':
        display_time = timestamp.strftime('%I:%M %p').lstrip('0')
    else:
        display_time = timestamp.strftime('%H:%M')
    return display_time


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


def add_stream(name, title, desc, game_pk, icon=None, fanart=None, info=None, video_info=None, audio_info=None, stream_date=None, spoiler='True', suspended=None, start_inning='False', blackout='False'):
    ok=True
    u_params = "&name="+urllib.quote_plus(title)+"&game_pk="+urllib.quote_plus(str(game_pk))+"&stream_date="+urllib.quote_plus(str(stream_date))+"&spoiler="+urllib.quote_plus(str(spoiler))+"&suspended="+urllib.quote_plus(str(suspended))+"&start_inning="+urllib.quote_plus(str(start_inning))+"&description="+urllib.quote_plus(desc)+"&blackout="+urllib.quote_plus(str(blackout))
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    art_params = "&icon="+urllib.quote_plus(icon)+"&fanart="+urllib.quote_plus(fanart)
    u=sys.argv[0]+"?mode="+str(104)+u_params+art_params

    liz=xbmcgui.ListItem(name)
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if info is not None:
        liz.setInfo( type="Video", infoLabels=info)
    if video_info is not None:
        liz.addStreamInfo('video', video_info)
    if audio_info is not None:
        liz.addStreamInfo('audio', audio_info)

    # add Choose Stream and Highlights as context menu items
    liz.addContextMenuItems([(LOCAL_STRING(30390), 'PlayMedia(plugin://plugin.video.mlbtv/?mode='+str(103)+u_params+art_params+')'), (LOCAL_STRING(30391), 'Container.Update(plugin://plugin.video.mlbtv/?mode='+str(106)+'&name='+urllib.quote_plus(title)+'&game_pk='+urllib.quote_plus(str(game_pk))+art_params+')')])

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


def addDir(name,mode,icon,fanart=None,game_day=None,start_inning='False'):
    ok=True

    u_params="&name="+urllib.quote_plus(name)+"&icon="+urllib.quote_plus(icon)+'&start_inning='+urllib.quote_plus(str(start_inning))
    if game_day is not None:
        u_params = u_params+"&game_day="+urllib.quote_plus(game_day)
    u=sys.argv[0]+"?mode="+str(mode)+u_params

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
    game_day_display = parse(game_day).strftime('%A, %B %d, %Y').replace(' 0', ' ')
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

    fav_team_id = None
    if FAV_TEAM in team_ids:
        fav_team_id = team_ids[FAV_TEAM]

    return fav_team_id


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


def stream_to_listitem(stream_url, headers, description, title, icon, fanart, start='1', stream_type='video', music_type_unset=False):
    # check if our stream is HLS
    if '.m3u8' in stream_url:
        # if not audio only, check if inputstream.adaptive is present and enabled, depending on Kodi version
        if stream_type != 'audio' and (xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)') or (KODI_VERSION >= 19 and xbmc.getCondVisibility('System.AddonIsEnabled(inputstream.adaptive)'))):
            listitem = xbmcgui.ListItem(title, path=stream_url)
            if KODI_VERSION >= 19:
                listitem.setProperty('inputstream', 'inputstream.adaptive')
            else:
                listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
            listitem.setProperty('inputstream.adaptive.stream_headers', headers)
            listitem.setProperty('inputstream.adaptive.license_key', "|" + headers)
            # if not using Kodi's resume function, set the start time
            if sys.argv[3] != 'resume:true' and start != '-1':
                listitem.setProperty('ResumeTime', start)
                listitem.setProperty('TotalTime', start)
        else:
            listitem = xbmcgui.ListItem(title, path=stream_url + '|' + headers)

        listitem.setMimeType("application/x-mpegURL")
    # otherwise, if not HLS, assume it is MP4
    else:
        listitem = xbmcgui.ListItem(title, path=stream_url + '|' + headers)
        listitem.setMimeType("video/mp4")

    if title is not None and description is not None:
        # don't set Music type for audio selection through Catch Up or context menu, otherwise playback will fail
        if stream_type == 'audio' and music_type_unset is False:
            listitem.setInfo( type="Music", infoLabels={ "Title": title, "Album": description } )
        else:
            listitem.setInfo( type="Video", infoLabels={ "Title": title, "Plot": description } )

    if icon is not None and fanart is not None:
        listitem.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})

    return listitem


def get_inning_start_options():
    start_options = []
    # add start options for each inning 1-12
    for x in range(1, 13):
        start_options.append(LOCAL_STRING(30409) + ' ' + LOCAL_STRING(30407) + ' ' + str(x)) # top
        start_options.append(LOCAL_STRING(30410) + ' ' + LOCAL_STRING(30407) + ' ' + str(x)) # bottom
    return start_options


def calculate_inning_from_index(index):
    inning_half = 'top'
    inning = int(round(((index+0.5) / 2), 0))
    if (index % 2) == 0 and ((index+1) % 2) == 1:
        inning_half = 'bottom'
    return inning, inning_half


def get_last_name(full_name):
    last_name = ''
    try:
        name_split = full_name.split()
        last_name = name_split[len(name_split)-1]
        if last_name.endswith('.'):
            last_name = name_split[len(name_split)-2] + ' ' + last_name
    except:
        pass
    return last_name


# get the teams blacked out based on zip code
def get_blackout_teams(zip_code):
    xbmc.log('Resetting blackout teams')
    blackout_teams = []
    try:
        if re.match('^[0-9]{5}$', zip_code):
            xbmc.log('Fetching new blackout teams')
            url = 'https://content.mlb.com/data/blackouts/' + zip_code + '.json'
            headers = {
                'User-Agent': UA_PC,
                'Origin': 'https://www.mlb.com',
                'Referer': 'https://www.mlb.com/'
            }
            r = requests.get(url, headers=headers, verify=VERIFY)
            json_source = r.json()
            if 'teams' in json_source:
                blackout_teams = json_source['teams']
    except:
        pass

    return blackout_teams


ZIP_CODE = str(settings.getSetting(id='zip_code'))
OLD_ZIP_CODE = str(settings.getSetting(id='old_zip_code'))
if ZIP_CODE != OLD_ZIP_CODE:
    settings.setSetting(id='old_zip_code', value=ZIP_CODE)
    BLACKOUT_TEAMS = get_blackout_teams(ZIP_CODE)
    settings.setSetting(id='blackout_teams', value=json.dumps(BLACKOUT_TEAMS))
else:
    BLACKOUT_TEAMS = json.loads(str(settings.getSetting(id='blackout_teams')))
