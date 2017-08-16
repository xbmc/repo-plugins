import sys, os
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import random
import cookielib, urllib
import json
import requests
import time, calendar
from datetime import date, datetime, timedelta
from sony import SONY


def main_menu():
    if ADDON.getSetting(id='all_chan_visible') == 'true': addDir(LOCAL_STRING(30224), 30, ICON)
    if ADDON.getSetting(id='timeline_visible') == 'true': addDir(LOCAL_STRING(30100), 50, ICON)
    if ADDON.getSetting(id='myshows_visible') == 'true': addDir(LOCAL_STRING(30101), 100, ICON)
    if ADDON.getSetting(id='fav_visible') == 'true': addDir(LOCAL_STRING(30102), 200, ICON)
    if ADDON.getSetting(id='live_visible') == 'true': addDir(LOCAL_STRING(30103), 300, ICON)
    if ADDON.getSetting(id='sports_visible') == 'true': addDir(LOCAL_STRING(30104), 400, ICON)
    if ADDON.getSetting(id='kids_visible') == 'true': addDir(LOCAL_STRING(30105), 500, ICON)
    if ADDON.getSetting(id='recent_visible') == 'true': addDir(LOCAL_STRING(30106), 600, ICON)
    if ADDON.getSetting(id='featured_visible') == 'true': addDir(LOCAL_STRING(30107), 700, ICON)
    if ADDON.getSetting(id='search_visible') == 'true': addDir(LOCAL_STRING(30211), 750, ICON)


def all_channels():
    json_source = get_json(EPG_URL + '/browse/items/channels/filter/all/sort/channeltype/offset/0/size/500')
    list_channels(json_source['body']['items'])


def timeline():
    list_timeline()


def my_shows():
    json_source = get_json(EPG_URL + '/browse/items/favorites/filter/shows/sort/title/offset/0/size/500')
    list_shows(json_source['body']['items'])


def favorite_channels():
    json_source = get_json(EPG_URL + '/browse/items/favorites/filter/channels/sort/name/offset/0/size/500')
    list_channels(json_source['body']['items'])


def live_tv():
    json_source = get_json(EPG_URL + '/browse/items/now_playing/filter/all/sort/channel/offset/0/size/500')
    list_channels(json_source['body']['items'])


def sports():
    json_source = get_json(EPG_URL + '/programs?size=10&offset=0&filter=ds-sports')
    list_shows(json_source['body']['items'])


def kids():
    json_source = get_json(EPG_URL + '/programs?size=10&offset=0&filter=ds-kids')
    list_shows(json_source['body']['items'])


def recently_watched():
    json_source = get_json(EPG_URL + '/browse/items/recently_watched/filter/shows/sort/watched_date/offset/0/size/35')
    list_shows(json_source['body']['items'])


def featured():
    json_source = get_json(EPG_URL + '/browse/items/featured/filter/shows/sort/featured/offset/0/size/100')
    list_shows(json_source['body']['items'])


def search():
    dialog = xbmcgui.Dialog()
    search_txt = dialog.input('Enter search text', type=xbmcgui.INPUT_ALPHANUM)
    if search_txt == '': sys.exit()
    json_source = get_json(EPG_URL + '/search/'+search_txt+'/offset/0/size/100')
    list_shows(json_source['body']['programs'])


def list_timeline():
    url = 'https://sentv-user-ext.totsuko.tv/sentv_user_ext/ws/v2/profile/ids'
    json_source = get_json(url)
    try:
        airing_id = json_source['body']['launch_program']['airing_id']
    except:
        sys.exit()

    json_source = get_json(EPG_URL + '/timeline/' + str(airing_id))

    for strand in json_source['body']['strands']:
       if strand['id'] == 'now_playing':
           addDir('[B][I][COLOR=FFFFFF66]Now Playing[/COLOR][/B][/I]', 998, ICON)
           for program in strand['programs']:
               #list_channel(program)
                list_episode(program)
       elif strand['id'] == 'watched_episodes':
           addDir('[B][I][COLOR=FFFFFF66]Watched Episodes[/COLOR][/B][/I]', 998, ICON)
           for program in reversed(strand['programs']):
               list_episode(program)
       elif strand['id'] == 'coming_up':
           addDir('[B][I][COLOR=FFFFFF66]Coming Up[/COLOR][/B][/I]', 998, ICON)
           for program in strand['programs']:
               list_episode(program)


def list_shows(json_source):
    for show in json_source:
        list_show(show)


def list_show(show):
        fanart = FANART
        icon = ICON
        for image in show['urls']:
            if 'width' in image:
                if image['width'] == 600: icon = image['src']
                if image['width'] >= 1080: fanart = image['src']
                if icon != ICON and fanart != FANART: break
        title = show['title']

        airing_id = 'null'
        if 'airing_id' in show: airing_id = str(show['airing_id'])
        channel_id = 'null'
        if 'channel_id' in show: channel_id = str(show['channel_id'])
        program_id = str(show['id'])
        series_id = 'null'
        if 'series_id' in show: series_id = str(show['series_id'])
        tms_id = str(show['tms_id'])

        genre = ''
        for item in show['genres']:
            if genre != '': genre += ', '
            genre += item['genre']

        plot = get_dict_item('series_synopsis', show)
        if plot == '': plot = get_dict_item('synopsis', show)

        info = {
            'plot': plot,
            'tvshowtitle': title,
            'title': title,
            'originaltitle': title,
            'genre': genre
        }

        show_info = {
            'airing_id': airing_id,
            'channel_id': channel_id,
            'program_id': program_id,
            'series_id': series_id,
            'tms_id': tms_id
        }

        addShow(title, 150, icon, fanart, info, show_info)


def list_episodes(program_id):
    url = EPG_URL + '/details/items/program/' + program_id + '/episodes/offset/0/size/20'

    json_source = get_json(url)

    # Sort by airing_date newest to oldest
    json_source = json_source['body']['items']
    json_source = sorted(json_source, key=lambda k: k['airing_date'], reverse=True)

    for show in json_source:
        list_episode(show)


def list_episode(show):
    fanart = FANART
    icon = ICON
    for image in show['urls']:
        if 'width' in image:
            if image['width'] == 600: icon = image['src']
            if image['width'] >= 1080: fanart = image['src']
            if icon != ICON and fanart != FANART: break

    # Set variables from json
    show_title = show['title']
    title = show['display_episode_title']
    airing_id = str(show['airings'][0]['airing_id'])

    #airing_id = 'null'
    #if 'airing_id' in show: airing_id = str(show['airings'][0]['airing_id'])
    channel_id = 'null'
    if 'channel_id' in show['channel']: channel_id = str(show['channel']['channel_id'])
    program_id = str(show['id'])
    series_id = 'null'
    if 'series_id' in show: series_id = str(show['series_id'])
    tms_id = str(show['tms_id'])

    airing_date = show['airing_date']
    airing_date = stringToDate(airing_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    airing_enddate = str(show['airings'][0]['airing_enddate'])
    airing_enddate = stringToDate(airing_enddate, "%Y-%m-%dT%H:%M:%S.%fZ")

    duration = airing_enddate - airing_date
    #xbmc.log("DURATION = "+ str(duration.total_seconds()))

    airing_date = UTCToLocal(airing_date)
    broadcast_date = ''
    if 'broadcast_date' in show:
        broadcast_date = show['broadcast_date']
        broadcast_date = stringToDate(broadcast_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        broadcast_date = UTCToLocal(broadcast_date)

    genre = ''
    for item in show['genres']:
        if genre != '': genre += ', '
        genre += item['genre']

    plot = get_dict_item('synopsis', show)

    if str(show['playable']).upper() == 'FALSE':
        # Add airing date/time to title
        title = title + ' ' +  airing_date.strftime('%m/%d/%y') + ' ' + airing_date.strftime('%I:%M %p').lstrip('0')

    # Add resumetime if applicable
    resumetime=''
    try:
        resumetime = str(show['airings'][0]['last_timecode'])
        xbmc.log("RESUME TIME = "+resumetime)
        h,m,s = resumetime.split(':')
        resumetime = str(int(h) * 3600 + int(m) * 60 + int(s))
    except: pass
    #xbmc.log("RESUME TIME IN Seconds = "+resumetime)
    #xbmc.log("TOTAL TIME IN Seconds = "+str(int(duration.total_seconds())))

    show_url = 'https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/airing/' + airing_id

    info = {
        'plot': plot,
        'tvshowtitle': show_title,
        'title': title,
        'originaltitle': title,
        'mediatype': 'episode',
        'genre': genre,
        'aired': airing_date.strftime('%Y-%m-%d'),
        'duration': str(int(duration.total_seconds()))
    }
    if broadcast_date != '': info['premiered'] = broadcast_date.strftime('%Y-%m-%d')

    properties = {

        'totaltime': str(int(duration.total_seconds())),
        'resumetime': resumetime,
        'IsPlayable': str(show['playable']).lower()
    }

    show_info = {
        'airing_id': airing_id,
        'channel_id': channel_id,
        'program_id': program_id,
        'series_id': series_id,
        'tms_id': tms_id
    }

    addStream(title, show_url, title, icon, fanart, info, properties, show_info)


def list_channels(json_source):
    for channel in json_source:
        list_channel(channel)


def list_channel(channel):
        fanart = FANART
        icon = ICON
        for image in channel['urls']:
            if 'width' in image:
                if image['width'] == 600 or image['width'] == 440: icon = image['src']
                if image['width'] == 1920: fanart = image['src']
                if icon != ICON and fanart != FANART: break

        if 'channel' in channel:
            title = channel['channel']['name']
            channel_id = str(channel['channel']['channel_id'])
        else:
            title = channel['title']
            channel_id = str(channel['id'])

        genre = ''
        for item in channel['genres']:
            if genre != '': genre += ', '
            genre += item['genre']

        plot = get_dict_item('synopsis', channel)
        season = get_dict_item('season_num', channel)
        episode = get_dict_item('episode_num', channel)

        channel_url = CHANNEL_URL + '/' + channel_id

        info = {
            'season':season,
            'episode':episode,
            'plot': plot,
            'tvshowtitle': title,
            'title': title,
            'originaltitle': title,
            'genre': genre
        }

        properties = {
            'IsPlayable': 'true'
        }

        show_info = {
            'channel_id': channel_id
        }

        addStream(title, channel_url, title, icon, fanart, info, properties, show_info)


def get_dict_item(key, dictionary):
    if key in dictionary:
        return dictionary[key]
    else:
        return ''


def get_stream(url, airing_id, channel_id, program_id, series_id, tms_id):
    headers = {"Accept": "*/*",
               "Content-type": "application/x-www-form-urlencoded",
               "Origin": "https://vue.playstation.com",
               "Accept-Language": "en-US,en;q=0.8",
               "Referer": "https://vue.playstation.com/watch/live",
               "Accept-Encoding": "deflate",
               "User-Agent": UA_ANDROID,
               "Connection": "Keep-Alive",
               'reqPayload': ADDON.getSetting(id='reqPayload')
               }

    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
    json_source = r.json()
    stream_url = json_source['body']['video']
    stream_url += '|User-Agent='
    stream_url += 'Adobe Primetime/1.4 Dalvik/2.1.0 (Linux; U; Android 6.0.1 Build/MOB31H)'
    stream_url += '&Cookie=reqPayload=' + urllib.quote('"' + ADDON.getSetting(id='reqPayload') + '"')

    listitem = xbmcgui.ListItem(path=stream_url)
    # listitem.setProperty('ResumeTime', '600')
    # listitem.setProperty('setResumePoint', '600')

    xbmcplugin.setResolvedUrl(addon_handle, True, listitem)

    # Seek to time

    #Give the stream sometime to start before checking
    '''
    monitor = xbmc.Monitor()
    monitor.waitForAbort(10)
    xbmc.log("Is playing video? " + str(xbmc.Player().isPlayingVideo()))
    while xbmc.Player().isPlayingVideo() and not monitor.abortRequested():
        xbmc.log("Still playing...")
        monitor.waitForAbort(3)

    xbmc.log("We're done, write info back to ps servers!!!")
    sony = SONY()
    sony.put_resume_time(airing_id, channel_id, program_id, series_id, tms_id)
    '''



def get_json(url):
    headers = {'Accept': '*/*',
               'reqPayload': ADDON.getSetting(id='reqPayload'),
               'User-Agent': UA_ANDROID,
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'en-US',
               'X-Requested-With': 'com.snei.vue.android'
               }

    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)

    if r.status_code != 200:
        dialog = xbmcgui.Dialog()
        msg = 'The request could not be completed.'
        try:
            json_source = r.json()
            msg = json_source['header']['error']['message']
        except:
            pass
        dialog.notification('Error '+str(r.status_code), msg, xbmcgui.NOTIFICATION_INFO, 5000)
        sys.exit()

    return r.json()


def load_cookies():
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file, ignore_discard=True)
    except:
        pass

    return cj


def stringToDate(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))

    return date


def create_device_id():
    android_id = ''.join(random.choice('0123456789abcdef') for i in range(16))
    android_id = android_id.rjust(30, '0')
    manufacturer = 'Asus'
    model = 'Nexus 7'
    manf_model = ":%s:%s" % (manufacturer.rjust(10, ' '), model.rjust(10, ' '))
    manf_model = manf_model.encode("hex").upper()
    zero = '0'
    device_id = "0000%s%s01a8%s%s" % ("0007", "0002", android_id, manf_model + zero.ljust(32, '0'))

    ADDON.setSetting(id='deviceId', value=device_id)


def findString(source, start_str, end_str):
    start = source.find(start_str)
    end = source.find(end_str, start + len(start_str))

    if start != -1:
        return source[start + len(start_str):end]
    else:
        return ''


def UTCToLocal(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def addDir(name, mode, icon, fanart=None, info=None):
    u = sys.argv[0] + "?mode=" + str(mode)
    liz = xbmcgui.ListItem(name)
    if fanart == None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    if info != None:
        liz.setInfo(type="Video", infoLabels=info)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=True)
    xbmcplugin.setContent(addon_handle, 'tvshows')
    return ok

def addShow(name, mode, icon, fanart, info, show_info):
    u = sys.argv[0] + "?mode=" + str(mode)
    u += '&program_id=' + show_info['program_id']

    liz = xbmcgui.ListItem(name)
    if fanart == None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setInfo(type="Video", infoLabels=info)
    show_values =''
    for key, value in show_info.iteritems():
        show_values += '&' + key + '=' + value

    context_items = [('Add To My Shows', 'RunPlugin(plugin://plugin.video.psvue/?mode=1001'+show_values+')'),
                    ('Remove From My Shows', 'RunPlugin(plugin://plugin.video.psvue/?mode=1002'+show_values+')')]
    liz.addContextMenuItems(context_items)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=True)
    xbmcplugin.setContent(addon_handle, 'tvshows')


def addStream(name, link_url, title, icon, fanart, info=None, properties=None, show_info=None):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(link_url) + "&mode=" + str(900)
    #xbmc.log(str(info))
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    if info != None: liz.setInfo(type="Video", infoLabels=info)
    if properties != None:
        for key, value in properties.iteritems():
            liz.setProperty(key,value)
    xbmc.log(str(show_info))
    if show_info != None:
        show_values =''
        for key, value in show_info.iteritems():
            show_values += '&' + key + '=' + value
        u += show_values
        if len(show_info) == 1:
            #Only add this option for channels not episodes
            context_items = [('Add To Favorites', 'RunPlugin(plugin://plugin.video.psvue/?mode=1001'+show_values+')'),
                            ('Remove From Favorites', 'RunPlugin(plugin://plugin.video.psvue/?mode=1002'+show_values+')')]
            liz.addContextMenuItems(context_items)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
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

def check_device_id():
    DEVICE_ID = ADDON.getSetting(id='deviceId')
    amazon_device = 'Amazon'
    amazon_device = amazon_device.encode("hex")
    old_asus = 'ASUS'
    old_asus = old_asus.encode("hex")
    if amazon_device in DEVICE_ID or old_asus in DEVICE_ID:
        sony = SONY()
        sony.logout()
        DEVICE_ID = ''

    if DEVICE_ID == '':
        create_device_id()
        DEVICE_ID = ADDON.getSetting(id='deviceId')



addon_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon()
ROOTDIR = ADDON.getAddonInfo('path')
LOCAL_STRING = ADDON.getLocalizedString
FANART = os.path.join(ROOTDIR, "resources", "fanart.jpg")
ICON = os.path.join(ROOTDIR, "resources", "icon.png")

ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
UA_ANDROID = 'Mozilla/5.0 (Linux; Android 6.0.1; Build/MOB31H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/44.0.2403.119 Safari/537.36'
CHANNEL_URL = 'https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/channel'
EPG_URL = 'https://epg-service.totsuko.tv/epg_service_sony/service/v2'
VERIFY = False
