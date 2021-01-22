import sys
import re, os, time
import calendar, pytz
import requests, urllib
from bs4 import BeautifulSoup
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
CDN = settings.getSetting("cdn")
USERNAME = settings.getSetting("username")
PASSWORD = settings.getSetting("password")
ROGERS_SUBSCRIBER = settings.getSetting("rogers")
NO_SPOILERS = settings.getSetting("no_spoilers")
QUALITY = settings.getSetting("stream_quality")
FAV_TEAM = settings.getSetting("fav_team")
TEAM_NAMES = settings.getSetting("team_names")
TIME_FORMAT = settings.getSetting("time_format")
VIEW_MODE = settings.getSetting("view_mode")
PREVIEW_INFO = settings.getSetting("game_preview_info")

# Colors
SCORE_COLOR = 'FF00B7EB'
GAMETIME_COLOR = 'FFFFFF66'
FREE_GAME_COLOR = 'FF43CD80'

# Game Time Colors
UPCOMING = 'FFD2D2D2'
LIVE = 'FFF69E20'
CRITICAL = 'FFD10D0D'
FINAL = 'FF666666'
FREE = 'FF43CD80'

ROOTDIR = xbmcaddon.Addon().getAddonInfo('path')
ICON = os.path.join(ROOTDIR, "icon.png")
FANART = os.path.join(ROOTDIR, "fanart.jpg")
PREV_ICON = os.path.join(ROOTDIR, "icon.png")
NEXT_ICON = os.path.join(ROOTDIR, "icon.png")

API_URL = 'http://statsapi.web.nhl.com/api/v1'
API_MEDIA_URL = 'https://mf.svc.nhl.com/ws/media/mf/v2.4'
VERIFY = True
PLATFORM = "IPHONE"
PLAYBACK_SCENARIO = 'HTTP_CLOUD_TABLET_60'

# User Agents
UA_IPHONE = 'AppleCoreMedia/1.0.0.15B202 (iPhone; U; CPU OS 11_1_2 like Mac OS X; en_us)'
UA_IPAD = 'Mozilla/5.0 (iPad; CPU OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12H143 ipad nhl 5.0925'
UA_NHL = 'NHL/11479 CFNetwork/887 Darwin/17.0.0'
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36'
UA_PS4 = 'PS4Application libhttp/1.000 (PS4) libhttp/4.07 (PlayStation 4)'

# Playlists
RECAP_PLAYLIST = xbmc.PlayList(0)
EXTENDED_PLAYLIST = xbmc.PlayList(1)


def find(source, start_str, end_str):
    start = source.find(start_str)
    end = source.find(end_str, start + len(start_str))

    if start != -1:
        return source[start + len(start_str):end]
    else:
        return ''


def color_string(string, color):
    return string
    # return '[COLOR=' + color + ']' + string + '[/COLOR]'


def string_to_date(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))

    return date


def eastern_to_local(eastern_time):
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


def eastern_to_utc(eastern_time):
    utc = pytz.utc
    eastern = pytz.timezone('US/Eastern')
    eastern_time = eastern.localize(eastern_time)
    # Convert it from Eastern to UTC
    utc_time = eastern_time.astimezone(utc)
    return utc_time


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


def add_stream(name, link_url, title, game_id, icon=None, fanart=None, info=None, video_info=None, audio_info=None,
               start_time=None):
    ok = True
    u = sys.argv[0] + "?url=" + urllib.quote_plus(link_url) + "&mode=" + str(104) + "&name=" + urllib.quote_plus(name.encode('utf8')) \
        + "&game_id=" + urllib.quote_plus(game_id.encode('utf8'))

    if start_time is not None:
        u += '&start_time='+start_time

    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    
    liz.setProperty("IsPlayable", "true")

    liz.setInfo(type="Video", infoLabels={"Title": title})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)
    if video_info is not None:
        liz.addStreamInfo('video', video_info)
    if audio_info is not None:
        liz.addStreamInfo('audio', audio_info)

    liz.setProperty('dbtype', 'video')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
    xbmcplugin.setContent(addon_handle, 'videos')

    return ok


def add_fav_today(name, icon, fanart=None):
    info = {'plot': '',
            'tvshowtitle': 'NHL',
            'title': name,
            'originaltitle': name,
            'aired': '',
            'genre': 'Sports'
            }
    audio_info, video_info = getAudioVideoInfo()
    ok = True
    url = sys.argv[0] + '?url=/favteamCurrent&mode=510'
    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})

    liz.setProperty("IsPlayable", "true")
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)
    if video_info is not None:
        liz.addStreamInfo('video', video_info)
    if audio_info is not None:
        liz.addStreamInfo('audio', audio_info)

    liz.setProperty('dbtype', 'video')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=False)
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


def getFavTeamId():
    url = API_URL + '/teams/'

    headers = {'User-Agent': UA_IPHONE}

    r = requests.get(url, headers=headers, verify=False)
    json_source = r.json()

    fav_team_id = "0"
    for team in json_source['teams']:
        if FAV_TEAM in team['name']:
            fav_team_id = str(team['id'])
            break

    return fav_team_id


def getGameIcon(home, away):
    # Check if game image already exists
    image_path = os.path.join(ROOTDIR, 'resources','media', away.lower() + 'vs' + home.lower() + '.png')
    # file_name = os.path.join(image_path)
    if not os.path.isfile(image_path):
        image_path = ICON

    '''
    Hold off until PIL is fixed for Android OS
    try:
        createGameIcon(home,away,image_path)
    except:
        image_path = ICON
        pass
    '''

    return image_path


def createGameIcon(home, away, image_path):
    try:
        from PIL import Image
    except:
        try:
            from pil import Image
        except:
            xbmc.log("PIL not available")
            sys.exit()

    # Arena backgrounds
    # http://nhl.bamcontent.com/images/arena/scoreboard/52.jpg
    # http://nhl.bamcontent.com/images/arena/scoreboard/52@2x.jpg

    bg = Image.open(ROOTDIR + '/resources/bg_dark.png')
    # bg_url = urllib.urlopen('http://nhl.bamcontent.com/images/arena/scoreboard/52.jpg')
    # bg_img = StringIO(bg_url.read())
    # bg = Image.open(bg_img)

    size = 256, 256

    logo_root = 'http://nhl.bamcontent.com/images/logos/600x600/'
    img_file = urllib.urlopen(logo_root + home.lower() + '.png ')
    im = StringIO(img_file.read())
    home_image = Image.open(im)
    home_image.thumbnail(size, Image.ANTIALIAS)
    home_image = home_image.convert("RGBA")

    img_file = urllib.urlopen(logo_root + away.lower() + '.png ')
    im = StringIO(img_file.read())
    away_image = Image.open(im)
    away_image.thumbnail(size, Image.ANTIALIAS)
    away_image = away_image.convert("RGBA")

    bg.paste(away_image, (0, 0), away_image)
    bg.paste(home_image, (256, 256), home_image)
    bg.save(image_path)


def get_thumbnails():
    xbmc.log("Attempting to get thumbnails")
    try:
        from PIL import Image
    except:
        try:
            from pil import Image
        except:
            xbmc.log("PIL not available")
            sys.exit()

    url = API_URL + '/teams/'
    headers = {'User-Agent': UA_IPHONE}

    r = requests.get(url, headers=headers, verify=False)
    json_source = r.json()

    team_list = []
    for team in json_source['teams']:
        team_list.append(team['abbreviation'].lower())

    logo_url = 'http://nhl.bamcontent.com/images/logos/132x132/'
    # logo_url = 'http://nhl.bamcontent.com/images/logos/600x600/'
    # size = 256, 256
    # size = 132, 132

    # steps = number of teams * (number of teams -1)
    steps = len(team_list) * (len(team_list) - 1)
    progress = xbmcgui.DialogProgress()
    progress.create('NHL TV')
    progress.update(0, 'Generating Thumbnails...')

    i = 1
    for home_team in team_list:
        if (progress.iscanceled()): break

        for away_team in team_list:
            if (progress.iscanceled()): break

            if home_team != away_team:
                image_path = ROOTDIR + '/resources/media/' + away_team + 'vs' + home_team + '.png'
                # bg =  Image.open(ROOTDIR+'/resources/bg_dark.png')
                bg = Image.new('RGB', (400, 225), (255, 255, 255))

                # home team
                img_file = urllib.urlopen(logo_url + home_team + '.png ')
                im = StringIO(img_file.read())
                home_image = Image.open(im)
                # home_image.thumbnail(size, Image.ANTIALIAS)
                # home_image = home_image.convert("RGBA")

                # away team
                img_file = urllib.urlopen(logo_url + away_team + '.png ')
                im = StringIO(img_file.read())
                away_image = Image.open(im)
                # away_image.thumbnail(size, Image.ANTIALIAS)
                # away_image = away_image.convert("RGBA")

                # create image
                # bg.paste(away_image, (0,0), away_image.split()[3])
                # bg.paste(home_image, (256,256), home_image)
                bg.paste(away_image, (40, 46), away_image)
                bg.paste(home_image, (228, 46), home_image)
                bg.save(image_path)

                # progress bar message
                message = away_team.upper() + ' vs ' + home_team.upper()
                percent = int((float(i) / steps) * 100)
                progress.update(percent, message)
                i += 1

    progress.close()


def getFavTeamColor():
    url = 'http://nhl.bamcontent.com/data/config/nhl/teamColors.json'
    # url = 'https://statsapi.web.nhl.com/api/v1/teams?teamId=
    headers = {'User-Agent': UA_IPHONE}

    r = requests.get(url, headers=headers, verify=False)
    json_source = r.json()

    fav_team_color = ''
    fav_team_id = settings.getSetting("fav_team_id")
    for team in json_source['teams']:
        if fav_team_id == str(team['id']):
            # Pick the lightest color
            fav_team_color = str(team['colors']['foreground'])
            if fav_team_color < str(team['colors']['background']):
                fav_team_color = str(team['colors']['background'])
            if fav_team_color < str(team['colors']['highlight']):
                fav_team_color = str(team['colors']['highlight'])

            fav_team_color = fav_team_color.replace('#', 'FF')
            break

    return fav_team_color


def getFavTeamLogo():
    logo_url = ''

    url = API_URL + '/teams'
    headers = {'User-Agent': UA_IPHONE}

    r = requests.get(url, headers=headers, verify=False)
    json_source = r.json()

    fav_team_abbr = ''
    for team in json_source['teams']:
        if FAV_TEAM in team['name']:
            fav_team_abbr = str(team['abbreviation']).lower()
            break

    if fav_team_abbr != '':
        logo_url = 'http://nhl.bamcontent.com/images/logos/600x600/' + fav_team_abbr + '.png'

    return logo_url


def getAudioVideoInfo():
    # SD (800 kbps)|SD (1600 kbps)|HD (3000 kbps)|HD (5000 kbps)
    if QUALITY == 'SD (800 kbps)':
        video_info = {'codec': 'h264', 'width': 512, 'height': 288, 'aspect': 1.78}
    elif QUALITY == 'SD (1200 kbps)':
        video_info = {'codec': 'h264', 'width': 640, 'height': 360, 'aspect': 1.78}
    else:
        # elif QUALITY == 'HD (2500 kbps)' or QUALITY == 'HD (3500 kbps)' or QUALITY == 'HD (5000 kbps)':
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
            if cookie.name == "Authorization" and not cookie.is_expired():
                authorization = cookie.value
    except:
        pass

    return authorization


def getStreamQuality(stream_url):
    stream_title = []
    headers = {'User-Agent': UA_IPHONE}

    r = requests.get(stream_url, headers=headers, verify=False)
    master = r.text

    xbmc.log(stream_url)
    xbmc.log(master)

    line = re.compile("(.+?)\n").findall(master)

    for temp_url in line:
        if '.m3u8' in temp_url:
            temp_url = temp_url
            match = re.search(r'(\d.+?)K', temp_url, re.IGNORECASE)
            if match:
                bandwidth = match.group()
                if 0 < len(bandwidth) < 6:
                    bandwidth = bandwidth.replace('k', ' kbps')
                    bandwidth = bandwidth.replace('K', ' kbps')
                    stream_title.append(bandwidth)

    stream_title.sort(key=natural_sort_key, reverse=True)
    dialog = xbmcgui.Dialog()
    ret = dialog.select(LOCAL_STRING(30350), stream_title)
    if ret >= 0:
        bandwidth = find(stream_title[ret], '', ' kbps')
    else:
        sys.exit()

    return bandwidth


def natural_sort_key(s):
    _nsre = re.compile('([0-9]+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]


# Refresh Fav team info if fav team changed
if FAV_TEAM != str(settings.getSetting("fav_team_name")):
    if FAV_TEAM == 'None':
        settings.setSetting(id="fav_team_name", value='')
        settings.setSetting(id="fav_team_id", value='')
        settings.setSetting(id="fav_team_color", value='')
        settings.setSetting(id="fav_team_logo", value='')
    else:
        settings.setSetting(id="fav_team_name", value=FAV_TEAM)
        settings.setSetting(id="fav_team_id", value=getFavTeamId())
        settings.setSetting(id="fav_team_color", value=getFavTeamColor())
        settings.setSetting(id="fav_team_logo", value=getFavTeamLogo())

FAV_TEAM_ID = settings.getSetting("fav_team_id")
FAV_TEAM_COLOR = settings.getSetting("fav_team_color")
FAV_TEAM_LOGO = settings.getSetting("fav_team_logo")


def stream_to_listitem(stream_url, headers):
    if xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):
        listitem = xbmcgui.ListItem(path=stream_url)
        if KODI_VERSION >= 19:
            listitem.setProperty('inputstream', 'inputstream.adaptive')
        else:
            listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        listitem.setProperty('inputstream.adaptive.stream_headers', headers)
        listitem.setProperty('inputstream.adaptive.license_key', "|" + headers)
    else:
        listitem = xbmcgui.ListItem(path=stream_url + '|' + headers)

    listitem.setMimeType("application/x-mpegURL")
    return listitem
