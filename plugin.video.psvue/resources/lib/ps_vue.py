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
    if ADDON.getSetting(id='all_chan_visible') == 'true': add_dir(LOCAL_STRING(30224), 30, ICON)
    if ADDON.getSetting(id='next_airings_visible') == 'true': add_dir(LOCAL_STRING(30100), 50, ICON)
    if ADDON.getSetting(id='myshows_visible') == 'true': add_dir(LOCAL_STRING(30101), 100, ICON)
    if ADDON.getSetting(id='fav_visible') == 'true': add_dir(LOCAL_STRING(30102), 200, ICON)
    if ADDON.getSetting(id='live_visible') == 'true': add_dir(LOCAL_STRING(30103), 300, ICON)
    if ADDON.getSetting(id='sports_visible') == 'true': add_dir(LOCAL_STRING(30104), 400, ICON)
    if ADDON.getSetting(id='kids_visible') == 'true': add_dir(LOCAL_STRING(30105), 500, ICON)
    if ADDON.getSetting(id='recent_visible') == 'true': add_dir(LOCAL_STRING(30106), 600, ICON)
    if ADDON.getSetting(id='featured_visible') == 'true': add_dir(LOCAL_STRING(30107), 700, ICON)
    if ADDON.getSetting(id='search_visible') == 'true': add_dir(LOCAL_STRING(30211), 750, ICON)


def all_channels():
    json_source = get_json(EPG_URL + '/browse/items/channels/filter/all/sort/channeltype/offset/0/size/500')
    list_channels(json_source['body']['items'])


def next_airings():
    list_next_airings()


def my_shows():
    json_source = get_json(EPG_URL + '/browse/items/favorites/filter/shows/sort/title/offset/0/size/500')
    list_shows(json_source['body']['items'])


def favorite_channels():
    json_source = get_json(EPG_URL + '/browse/items/favorites/filter/channels/sort/name/offset/0/size/500')
    list_channels(json_source['body']['items'])


def live_tv():
    json_source = get_json(EPG_URL + '/browse/items/now_playing/filter/all/sort/channel/offset/0/size/500')
    list_shows(json_source['body']['items'])


def on_demand(channel_id):
    json_source = get_json(EPG_URL + '/details/channel/'+channel_id+'/popular/offset/0/size/500')
    list_shows(json_source['body']['popular'])


def sports():
    json_source = get_json(EPG_URL + '/programs?size=100&offset=0&filter=ds-sports')
    list_shows(json_source['body']['items'])


def kids():
    json_source = get_json(EPG_URL + '/programs?size=100&offset=0&filter=ds-kids')
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


def list_next_airings():
    channel_source = get_json(EPG_URL + '/browse/items/channels/filter/all/sort/channeltype/offset/0/size/300')
    # Get channel id for to tv guide selection
    channel_dict ={}
    channel_list = []
    for channel in channel_source['body']['items']:
        uni_channel = channel['title'].encode("utf-8")
        xbmc.log(str(channel['id']) + ' ' + uni_channel)
        channel_dict[uni_channel] = str(channel['id'])
        channel_list.append(uni_channel)
    
    dialog = xbmcgui.Dialog()
    ret = dialog.select(LOCAL_STRING(30214), channel_list)
    if ret < 0:
        sys.exit()

    channel_id = channel_dict[channel_list[ret]]
    # Json information from live and upcoming timeline for specified channel
    # Max upcoming shows display is 10
    json_source = get_json(EPG_URL + '/timeline/live/' + channel_id + '/watch_history_size/0/coming_up_size/20')

    # Sort live and upcoming episodes on selected channel
    # Some channels (not many) do not load any live or upcoming info. This is a Sony server issue.
    for strand in json_source['body']['strands']:
        if strand['id'] == 'now_playing':
            icon = ICON
            for image in strand['programs'][0]['channel']['urls']: #Display Channel icon
                if 'width' in image:
                    if image['width'] == 600 or image['width'] == 440: icon = image['src']
                    if icon != ICON: break
            add_dir('[B][I][COLOR=FFE4287C]NOW PLAYING[/COLOR][/B][/I]', 998, icon)
            for program in strand['programs']:
                list_episode(program)
        elif strand['id'] == 'coming_up':
            icon = ICON
            for image in strand['programs'][0]['channel']['urls']:
                if 'width' in image:
                    if image['width'] == 600 or image['width'] == 440: icon = image['src']
                    if icon != ICON: break
            uni_name = strand['programs'][0]['channel']['name'].encode("utf-8")
            add_dir('[B][I][COLOR=FFE4287C]COMING UP ON:[/COLOR][/B][/I]'+'      '+uni_name, 998, icon)
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
    title = show['display_title']
        
    airing_id = 'null'
    if 'airings' in show: airing_id = str(show['airings'][0]['airing_id'])
    channel_id = 'null'
    if 'channel' in show: channel_id = str(show['channel']['channel_id'])
    program_id = 'null'
    program_id = str(show['id'])
    series_id = 'null'
    if 'series_id' in show: series_id = str(show['series_id'])
    tms_id = str(show['tms_id'])
    name = title
    genre = ''
    for item in show['genres']:
        if genre != '': genre += ', '
        genre += item['genre']

    plot = get_dict_item('series_synopsis', show)
    if plot == '': plot = get_dict_item('synopsis', show)

    info = {
        'plot': plot,
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

    properties = {
        'IsPlayable': 'true'
     }

    channel_url = CHANNEL_URL + '/' + channel_id

    if str(show['airings'][0]['badge']) == 'live':
        add_stream(name, channel_url, icon, fanart, info, properties, show_info)
    else:
        add_show(title, 150, icon, fanart, info, show_info)
        
    add_sort_methods(addon_handle)


def list_episodes(program_id):
    url = EPG_URL + '/details/items/program/' + program_id + '/episodes/offset/0/size/500'
    
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
    show_title = show['display_title']
    title = show['display_episode_title']
    airing_id = str(show['airings'][0]['airing_id'])

    channel_name = 'null'
    if 'airings' in show:
        channel_name = str(show['airings'][0]['channel_name'])
    else:
        channel_name = str(show['channel']['name'])

    channel_id = 'null'
    if 'airings' in show:
        channel_id = str(show['airings'][0]['channel_id'])
    else:
        channel_id = str(show['channel']['channel_id'])

    program_id = str(show['id'])
    
    series_id = 'null'
    if 'series_id' in show: series_id = str(show['series_id'])
    
    tms_id = str(show['tms_id'])
    
    airing_date = show['airing_date']
    airing_date = string_to_date(airing_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    airing_enddate = str(show['airings'][0]['airing_enddate'])
    airing_enddate = string_to_date(airing_enddate, "%Y-%m-%dT%H:%M:%S.%fZ")
    age_rating = get_dict_item('age_rating',show['airings'][0])
    duration = airing_enddate - airing_date
    
    airing_date = utc_to_local(airing_date)

    broadcast_date = airing_date
    if 'broadcast_date' in show:
        broadcast_date = show['broadcast_date']
        xbmc.log(str(broadcast_date))
        broadcast_date = string_to_date(broadcast_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        broadcast_date = utc_to_local(broadcast_date)

    media_type = 'tvshow'
    if 'movie' in get_dict_item('sentv_type',show).lower():
        media_type = 'movie'

    genre = ''
    for item in show['genres']:
        if genre != '': genre += ', '
        genre += item['genre']

    plot = get_dict_item('synopsis', show)

    if str(show['airings'][0]['badge']) != 'live' and str(show['playable']).upper() == 'TRUE':
        name = '[B][COLOR=FFB048B5]Aired On[/COLOR][/B]' + '  ' + broadcast_date.strftime('%m/%d/%y') + '   ' + title
        channel_name = show['title']
        show_title = show['display_episode_title']

    elif str(show['playable']).upper() == 'FALSE':
        # Add airing date/time to title for upcoming shows
        name = '[B][I][COLOR=FFFFFF66]AIRING ON[/COLOR][/I][/B]' + '  ' + airing_date.strftime('%m/%d/%y') + '  @' + airing_date.strftime('%I:%M %p').lstrip('0') + '    ' + show_title
    
    # Sort Live shows and episodes no longer available to watch
    elif str(show['airings'][0]['badge']) == 'live':
        name = title
        channel_name = channel_name + '    ' + '[B][I][COLOR=FFFFFF66]Live[/COLOR][/I][/B]'

    # Add resumetime if applicable
    resumetime=''
    if 'last_timecode' in show['airings'][0]:
        resumetime = str(show['airings'][0]['last_timecode'])
        xbmc.log("RESUME TIME = "+resumetime)
        try:
            h,m,s = resumetime.split(':')
        except ValueError:
            h,m,s,ms = resumetime.split(':')
        resumetime = str(int(h) * 3600 + int(m) * 60 + int(s))

    # xbmc.log("RESUME TIME IN Seconds = "+resumetime)
    # xbmc.log("TOTAL TIME IN Seconds = "+str(int(duration.total_seconds())))
    
    show_url = SHOW_URL + '/' + airing_id
    
    info = {
        'plot': plot,
        'tvshowtitle': show_title,
        'title': channel_name,
        'originaltitle': title,
        'mediatype': media_type,
        'genre': genre,
        'aired': broadcast_date.strftime('%Y-%m-%d'),
        'duration': str(int(duration.total_seconds())),
        'season': get_dict_item('season_num',show),
        'episode': get_dict_item('episode_num',show),
        'mpaa': age_rating
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
        'tms_id': tms_id,
        'title': title,
        'plot': plot
    }
    
    add_stream(name, show_url, icon, fanart, info, properties, show_info)


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

    airing_id = ''
    program_id = ''
    series_id = ''
    tms_id = ''

    if 'id' in channel and 'sub_item' in channel:
        if 'airings' in channel['sub_item'] and channel['sub_item']['airings']:
            air_dict = {}
            air_list = []
            for airing in channel['sub_item']['airings']:
                xbmc.log(str(airing['airing_id']) + ' ' + str(airing['type']))
                air_dict[str(airing['type'])] = str(airing['airing_id'])
                air_list.append(str(airing['type']))

            airing_id = air_dict[air_list[0]]

        if 'id' in channel['sub_item']: program_id = str(channel['sub_item']['id'])
        if 'series_id' in channel['sub_item']: series_id = str(channel['sub_item']['series_id'])
        tms_id = str(channel['sub_item']['tms_id'])

    if 'channel' in channel:
        title = channel['channel']['name']
        channel_id = str(channel['channel']['channel_id'])
    else:
        title = channel['title']
        channel_id = str(channel['id'])

    plot = get_dict_item('synopsis', channel['sub_item'])
    season = get_dict_item('season_num', channel['sub_item'])
    episode = get_dict_item('episode_num', channel['sub_item'])

    genre = ''
    for item in (channel['sub_item']['genres']):
        if genre != '': genre += ', '
        genre += item['genre']

    channel_url = CHANNEL_URL + '/' + channel_id
    
    info = {
        'season':season,
        'episode':episode,
        'plot': plot,
        'title': title,
        'originaltitle': title,
        'genre': genre
    }
        
    properties = {
        'IsPlayable': 'true'
    }
        
    show_info = {
        'airing_id': airing_id,
        'channel_id': channel_id,
        'program_id': program_id,
        'series_id': series_id,
        'tms_id': tms_id,
        'title': title,
        'icon': icon
    }

    if get_dict_item('channel_type',channel) == 'vod':
        add_dir(title, 350, icon, fanart, channel_id)
    else:
        add_stream(title, channel_url, icon, fanart, info, properties, show_info)


def get_dict_item(key, dictionary):
    if key in dictionary:
        return dictionary[key]
    else:
        return ''


def get_stream(url, airing_id, channel_id, program_id, series_id, tms_id, title, plot, icon):
    headers = {
        'Accept': '*/*',
        'Content-type': 'application/x-www-form-urlencoded',
        'Origin': 'https://vue.playstation.com',
        'Accept-Language': 'en-US,en;q=0.8',
        'Referer': 'https://vue.playstation.com/watch/live',
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': UA_ANDROID_TV,
        'Connection': 'Keep-Alive',
        'Host': 'media-framework.totsuko.tv',
        'reqPayload': ADDON.getSetting(id='EPGreqPayload'),
        'X-Requested-With': 'com.snei.vue.android'
    }

    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
    json_source = r.json()
    stream_url = json_source['body']['video']
    headers = '|User-Agent='
    headers += 'Adobe Primetime/1.4 Dalvik/2.1.0 (Linux; U; Android 6.0.1 Build/MOB31H)'
    headers += '&Cookie=reqPayload=' + urllib.quote('"' + ADDON.getSetting(id='EPGreqPayload') + '"')
    listitem = xbmcgui.ListItem()

    # Checks to see if VideoPlayer info is already saved. If not then info is loaded from stream link
    if xbmc.getCondVisibility('String.IsEmpty(ListItem.Title)'):
        listitem = xbmcgui.ListItem(title, plot, thumbnailImage=icon)
        listitem.setInfo(type="Video", infoLabels={'title': title, 'plot': plot})
        listitem.setMimeType("application/x-mpegURL")

    else:
        listitem = xbmcgui.ListItem()
        listitem.setMimeType("application/x-mpegURL")

    '''inputstreamCOND = str(json_source['body']['dai_method']) # Checks whether stream method is "mlbam" or "freewheel" or "none"

    if  inputstreamCOND == 'mlbam' and xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):#Inputstream 2.1.15.0 update does not work with PSVue
        stream_url = json_source['body']['video_alt'] # Uses alternate Sony stream to prevent Inputstream adaptive from crashing
        listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        listitem.setProperty('inputstream.adaptive.stream_headers', headers)
        listitem.setProperty('inputstream.adaptive.license_key', headers)
    '''
        
    stream_url += headers

    listitem.setPath(stream_url)

    xbmcplugin.setResolvedUrl(addon_handle, True, listitem)

    # Seek to time

    # Give the stream sometime to start before checking
    monitor = xbmc.Monitor()
    monitor.waitForAbort(10)
    watched = 'false'
    play_time = 0
    mark_watched = -1
    xbmc.log("Is playing video? " + str(xbmc.Player().isPlayingVideo()))
    while xbmc.Player().isPlayingVideo() and not monitor.abortRequested():
        xbmc.log("Still playing...")
        play_time = str(xbmc.Player().getTime())  # Get timestamp of video from VideoPlayer to save as resume time
        mark_watched = xbmc.Player().getTotalTime()  # Get the total time of video playing
        monitor.waitForAbort(3)
    xbmc.log("We're done, write info back to ps servers!!!")
    int_time = int(float(play_time))  # Convert VideoPlayer seconds from float to int
    res_time = time.strftime("%H:%M:%S", time.gmtime(int_time))  # Convert seconds to 00:00:00 resume time
    cur_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S:%SZ")

    if 0 < (mark_watched - int_time) <= 120:  # Mark video as watched if less than 2 minutes are left
        watched = 'true'

    sony = SONY()
    sony.put_resume_time(airing_id, channel_id, program_id, series_id, tms_id, res_time, cur_time, watched)


def get_json(url):
    headers = {
        'Accept': '*/*',
        'reqPayload': ADDON.getSetting(id='EPGreqPayload'),
        'User-Agent': UA_ANDROID_TV,
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.5',
        'X-Requested-With': 'com.snei.vue.android',
        'Connection': 'keep-alive'
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
        dialog.notification('Error '+str(r.status_code), msg, xbmcgui.NOTIFICATION_INFO, 9000)
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


def string_to_date(string, date_format):
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


def utc_to_local(utc_dt):
    offset = datetime.now() - datetime.utcnow()
    local_dt = utc_dt + offset + timedelta(seconds=1)
    return local_dt


def add_dir(name, mode, icon, fanart=None, channel_id=None):
    u = sys.argv[0] + "?mode=" + str(mode)
    if channel_id is not None: u += "&channel_id=" + channel_id
    liz = xbmcgui.ListItem(name)
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=True)
    xbmcplugin.setContent(addon_handle, 'tvshows')
    return ok


def add_sort_methods(handle):
    xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)


def add_show(name, mode, icon, fanart, info, show_info):
    u = sys.argv[0] + "?mode=" + str(mode)
    u += '&program_id=' + show_info['program_id']
    
    liz = xbmcgui.ListItem(name)
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setInfo(type="Video", infoLabels=info)
    show_values = ''
    for key, value in show_info.iteritems():
        show_values += '&' + key + '=' + value

    context_items = [
        ('Add To Favorites Channels', 'RunPlugin(plugin://plugin.video.psvue/?mode=1001&fav_type=channel' + show_values + ')'),
        ('Remove From Favorites Channels', 'RunPlugin(plugin://plugin.video.psvue/?mode=1002&fav_type=channel' + show_values + ')'),
        ('Add To My Shows', 'RunPlugin(plugin://plugin.video.psvue/?mode=1001&fav_type=show' + show_values + ')'),
        ('Remove From My Shows', 'RunPlugin(plugin://plugin.video.psvue/?mode=1002&fav_type=show' + show_values + ')')
    ]
    liz.addContextMenuItems(context_items)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=True)
    xbmcplugin.setContent(addon_handle, 'tvshows')


def add_stream(name, link_url, icon, fanart, info=None, properties=None, show_info=None):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(link_url)
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    if info is not None: liz.setInfo(type="Video", infoLabels=info)
    if properties is not None:
        for key, value in properties.iteritems():
            liz.setProperty(key,value)
        if 'IsPlayable' in properties and properties['IsPlayable'] == 'false':
            u += "&mode=" + str(998)
        else:
            u += "&mode=" + str(900)

    if show_info is not None:
        show_values = ''
        for key, value in show_info.iteritems():
            show_values += '&' + key + '=' + value
        u += show_values
        context_items = [
            ('Add To Favorites Channels', 'RunPlugin(plugin://plugin.video.psvue/?mode=1001&fav_type=channel'+show_values+')'),
            ('Remove From Favorites Channels', 'RunPlugin(plugin://plugin.video.psvue/?mode=1002&fav_type=channel'+show_values+')'),
            ('Add To My Shows', 'RunPlugin(plugin://plugin.video.psvue/?mode=1001&fav_type=show' + show_values + ')'),
            ('Remove From My Shows', 'RunPlugin(plugin://plugin.video.psvue/?mode=1002&fav_type=show' + show_values + ')')
        ]
        liz.addContextMenuItems(context_items)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=False)
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
    device_id = ADDON.getSetting(id='deviceId')
    amazon_device = 'Amazon'
    amazon_device = amazon_device.encode("hex")
    old_asus = 'ASUS'
    old_asus = old_asus.encode("hex")
    if amazon_device in device_id or old_asus in device_id:
        sony = SONY()
        sony.logout()
        device_id = ''
    
    if device_id == '':
        create_device_id()


addon_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon()
ROOTDIR = ADDON.getAddonInfo('path')
LOCAL_STRING = ADDON.getLocalizedString
FANART = os.path.join(ROOTDIR, "resources", "fanart.jpg")
ICON = os.path.join(ROOTDIR, "resources", "icon.png")
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
UA_ANDROID = 'Mozilla/5.0 (Linux; Android 6.0.1; Build/MOB31H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/44.0.2403.119 Safari/537.36'
UA_ANDROID_TV = 'Mozilla/5.0 (Linux; Android 6.0.1; Hub Build/MHC19J; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.3163.98 Safari/537.36'
CHANNEL_URL = 'https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/channel'
EPG_URL = 'https://epg-service.totsuko.tv/epg_service_sony/service/v2'
SHOW_URL = 'https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/airing/'
PROF_ID = ADDON.getSetting(id='default_profile')
VERIFY = False
