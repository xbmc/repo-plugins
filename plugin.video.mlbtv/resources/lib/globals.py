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
HIDE_SCORES_TICKER = str(settings.getSetting(id='hide_scores_ticker'))
DISABLE_VIDEO_PADDING = str(settings.getSetting(id='disable_video_padding'))
DISABLE_CLOSED_CAPTIONS = str(settings.getSetting(id='disable_closed_captions'))
FAV_TEAM = str(settings.getSetting(id="fav_team"))
INCLUDE_FAV_AFFILIATES = str(settings.getSetting(id='include_fav_affiliates'))
TEAM_NAMES = settings.getSetting(id="team_names")
TIME_FORMAT = settings.getSetting(id="time_format")
SINGLE_TEAM = str(settings.getSetting(id='single_team'))
AUTO_SELECT_STREAM = str(settings.getSetting(id='auto_select_stream'))
CATCH_UP = str(settings.getSetting(id='catch_up'))
ASK_TO_SKIP = str(settings.getSetting(id='ask_to_skip'))
AUTO_PLAY_FAV = str(settings.getSetting(id='auto_play_fav'))
ONLY_FREE_GAMES = str(settings.getSetting(id="only_free_games"))
GAME_CHANGER_DELAY = int(settings.getSetting(id="game_changer_delay"))

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
BLACK_IMAGE = os.path.join(ROOTDIR, "resources", "img", "black.png")

API_URL = 'https://statsapi.mlb.com'
#User Agents
UA_IPAD = 'AppleCoreMedia/1.0 ( iPad; compatible; 3ivx HLS Engine/2.0.0.382; Win8; x64; 264P AACP AC3P AESD CLCP HTPC HTPI HTSI MP3P MTKA)'
UA_PC = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
UA_ANDROID = 'okhttp/3.12.1'

VERIFY = True

SECONDS_PER_SEGMENT = 5

MLB_ID = '1'
MILB_IDS = '11,12,13,14'
MLB_TEAM_IDS = '108,109,110,111,112,113,114,115,116,117,118,119,120,121,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,158,159,160'

AFFILIATE_TEAM_IDS = {"Arizona Diamondbacks": "419,516,2310,5368", "Atlanta Braves": "430,431,432,478", "Baltimore Orioles": "418,488,548,568", "Boston Red Sox": "414,428,533,546", "Chicago Cubs": "451,521,550,553", "Chicago White Sox": "247,487,494,580", "Cincinnati Reds": "416,450,459,498", "Cleveland Guardians": "402,437,445,481", "Colorado Rockies": "259,342,486,538", "Detroit Tigers": "106,512,570,582", "Houston Astros": "482,573,3712,5434", "Kansas City Royals": "541,565,1350,3705", "Los Angeles Angels": "401,460,559,561", "Los Angeles Dodgers": "238,260,456,526", "Miami Marlins": "479,554,564,4124", "Milwaukee Brewers": "249,556,572,5015", "Minnesota Twins": "492,509,1960,3898", "New York Mets": "453,505,507,552", "New York Yankees": "531,537,587,1956", "Oakland Athletics": "237,400,499,524", "Philadelphia Phillies": "427,522,566,1410", "Pittsburgh Pirates": "452,477,484,3390", "San Diego Padres": "103,510,584,4904", "San Francisco Giants": "105,461,476,3410", "Seattle Mariners": "403,515,529,574", "St. Louis Cardinals": "235,279,440,443", "Tampa Bay Rays": "233,234,421,2498", "Texas Rangers": "102,448,485,540", "Toronto Blue Jays": "422,424,435,463", "Washington Nationals": "426,436,534,547"}

ESPN_SUNDAY_NIGHT_BLACKOUT_COUNTRIES = ["Angola", "Anguilla", "Antigua and Barbuda", "Argentina", "Aruba", "Australia", "Bahamas", "Barbados", "Belize", "Belize", "Benin", "Bermuda", "Bolivia", "Bonaire", "Botswana", "Brazil", "British Virgin Islands", "Burkina Faso", "Burundi", "Cameroon", "Cape Verde", "Cayman Islands", "Central African Republic", "Chad", "Chile", "Colombia", "Comoros", "Cook Islands", "Costa Rica", "Cote d'Ivoire", "Curacao", "Democratic Republic of the Congo", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "El Salvador", "England", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Falkland Islands", "Falkland Islands", "Fiji", "French Guiana", "French Guiana", "French Polynesia", "Gabon", "Ghana", "Grenada", "Guadeloupe", "Guatemala", "Guinea", "Guinea Bissau", "Guyana", "Guyana", "Haiti", "Honduras", "Ireland", "Jamaica", "Kenya", "Kiribati", "Lesotho", "Liberia", "Madagascar", "Malawi", "Mali", "Marshall Islands", "Martinique", "Mayotte", "Mexico", "Micronesia", "Montserrat", "Mozambique", "Namibia", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Niue", "Northern Ireland", "Palau Islands", "Panama", "Paraguay", "Peru", "Republic of Ireland", "Reunion", "Rwanda", "Saba", "Saint Maarten", "Samoa", "Sao Tome & Principe", "Scotland", "Senegal", "Seychelles", "Sierra Leone", "Solomon Islands", "Somalia", "South Africa", "St. Barthelemy", "St. Eustatius", "St. Kitts and Nevis", "St. Lucia", "St. Martin", "St. Vincent and the Grenadines", "Sudan", "Surinam", "Suriname", "Tahiti", "Tanzania & Zanzibar", "The Gambia", "The Republic of Congo", "Togo", "Tokelau", "Tonga", "Trinidad and Tobago", "Turks and Caicos Islands", "Tuvalu", "Uganda", "Uruguay", "Venezuela", "Wales", "Zambia", "Zimbabwe"]

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


def add_stream(name, title, desc, game_pk, icon=None, fanart=None, info=None, video_info=None, audio_info=None, stream_date=None, spoiler='True', suspended=None, start_inning='False', blackout='False', milb=None):
    ok=True

    if milb is not None:
        u_params = "&featured_video="+urllib.quote_plus("https://dai.tv.milb.com/api/v2/playback-info/games/"+str(game_pk)+"/contents/14862/products/milb-carousel")+"&name="+urllib.quote_plus(title)+"&description="+urllib.quote_plus(desc)+"&game_pk="+urllib.quote_plus(str(game_pk))+"&start_inning="+urllib.quote_plus(str(start_inning))
        u=sys.argv[0]+"?mode="+str(301)+u_params
    else:
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
    if milb is None:
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


def addDir(name,mode,icon,fanart=None,game_day=None,start_inning='False',sport=MLB_ID,teams='None'):
    ok=True

    u_params="&name="+urllib.quote_plus(name)+"&icon="+urllib.quote_plus(icon)+'&start_inning='+urllib.quote_plus(str(start_inning))+'&sport='+urllib.quote_plus(str(sport))+'&teams='+urllib.quote_plus(str(teams))
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
    xbmc.log(f'URL: {stream_url} Headers: {headers} start: {start}')
    headers = 'User-Agent=' + UA_PC
    if '.m3u8' in stream_url:
        # if not audio only, check if inputstream.adaptive is present and enabled, depending on Kodi version
        if stream_type != 'audio' and (xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)') or (KODI_VERSION >= 19 and xbmc.getCondVisibility('System.AddonIsEnabled(inputstream.adaptive)'))):
            listitem = xbmcgui.ListItem(title, path=stream_url)
            if KODI_VERSION >= 19:
                listitem.setProperty('inputstream', 'inputstream.adaptive')
            else:
                listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            # IA manifest_type deprecated in Kodi 20, may eventually need to remove this
            # but will need to ensure manifest type can be auto-detected from streams and proxied streams
            listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
            listitem.setProperty('inputstream.adaptive.stream_headers', headers)
            # IA stream_headers deprecated for manifests in Kodi 20, manifest_headers required in Kodi 21+
            if KODI_VERSION >= 20:
                listitem.setProperty('inputstream.adaptive.manifest_headers', headers)
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


def get_broadcast_start_timestamp(stream_url):
    broadcast_start_timestamp = None
    is_live = True
    try:
        url = stream_url[:len(stream_url)-5] + '_1280x720_59_5472K.m3u8'
        headers = {
            'User-Agent': UA_PC,
             'Origin': 'https://www.mlb.com',
             'Referer': 'https://www.mlb.com/'
        }
        r = requests.get(url, headers=headers, verify=VERIFY)
        content = r.text
        line_array = content.splitlines()
        for line in line_array:
            if line.startswith('#EXT-X-PLAYLIST-TYPE:VOD'):
                is_live = False
            elif line.startswith('#EXT-X-PROGRAM-DATE-TIME:'):
                broadcast_start_timestamp = parse(line[25:])
                xbmc.log('Found broadcast start timestamp ' + str(broadcast_start_timestamp))
                break
    except:
        xbmc.log('Failed to find broadcast start timestamp')
        pass
    return broadcast_start_timestamp, is_live


# get the teams blacked out based on zip code
def get_blackout_teams(zip_code):
    xbmc.log('Resetting blackout teams')
    found_blackout_teams = []
    try:
        if re.match('^[0-9]{5}$', zip_code):
            xbmc.log('Fetching new blackout teams')
            url = 'https://content.mlb.com/data/blackouts/' + zip_code + '.json'
            headers = {
                'User-Agent': UA_PC,
                'Origin': 'https://www.mlb.com',
                'Referer': 'https://www.mlb.com/'
            }
            # set verify to False here to avoid a Python request error "unable to get local issuer certificate"
            r = requests.get(url, headers=headers, verify=False)
            json_source = r.json()
            if 'teams' in json_source:
                found_blackout_teams = json_source['teams']
    except:
        pass

    return found_blackout_teams

COUNTRY = str(settings.getSetting(id='country'))
OLD_COUNTRY = str(settings.getSetting(id='old_country'))
ZIP_CODE = str(settings.getSetting(id='zip_code'))
OLD_ZIP_CODE = str(settings.getSetting(id='old_zip_code'))
BLACKOUT_TEAMS = json.loads(str(settings.getSetting(id='blackout_teams')))
if COUNTRY == 'Canada':
    BLACKOUT_TEAMS = ['TOR']
elif COUNTRY == 'USA':
    if ZIP_CODE != OLD_ZIP_CODE or COUNTRY != OLD_COUNTRY:
        BLACKOUT_TEAMS = get_blackout_teams(ZIP_CODE)
else:
    BLACKOUT_TEAMS = []

settings.setSetting(id='blackout_teams', value=json.dumps(BLACKOUT_TEAMS))
settings.setSetting(id='old_zip_code', value=ZIP_CODE)
settings.setSetting(id='old_country', value=COUNTRY)

