import sys, os
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import random
import cookielib, urllib, urlparse
import json
import requests
import time, calendar
from datetime import date, datetime, timedelta


def main_menu():
    addDir(LOCAL_STRING(30100), 50, ICON)
    addDir(LOCAL_STRING(30101), 100, ICON)
    addDir(LOCAL_STRING(30102), 200, ICON)
    addDir(LOCAL_STRING(30103), 300, ICON)
    addDir(LOCAL_STRING(30104), 400, ICON)
    addDir(LOCAL_STRING(30105), 500, ICON)
    addDir(LOCAL_STRING(30106), 600, ICON)
    addDir(LOCAL_STRING(30107), 700, ICON)


def timeline():
    list_timeline()


def my_shows():
    json_source = get_json(EPG_URL + '/browse/items/favorites/filter/shows/sort/title/offset/0/size/100')
    list_shows(json_source['body']['items'])


def favorite_channels():
    json_source = get_json(EPG_URL + '/browse/items/favorites/filter/channels/sort/name/offset/0/size/100')
    list_channels(json_source['body']['items'])


def live_tv():
    json_source = get_json(EPG_URL + '/browse/items/now_playing/filter/all/sort/channel/offset/0/size/100')
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


def list_timeline():
    url = 'https://sentv-user-ext.totsuko.tv/sentv_user_ext/ws/v2/profile/ids'
    airing_id = get_json(url)['body']['launch_program']['airing_id']

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
        show_id = str(show['id'])

        genre = ''
        for item in show['genres']:
            if genre != '': genre += ', '
            genre += item['genre']

        plot = ''
        if 'synopsis' in show: plot = show['synopsis']

        # if watched = true look in airing for last time code
        # "last_timecode": "00:10:54",

        # channel_url = CHANNEL_URL+'/'+show_id
        # show_url = 'https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/airing/'+airing_id

        info = {'plot': plot, 'tvshowtitle': title, 'title': title, 'originaltitle': title, 'genre': genre}
        # addStream(title,show_url,title,icon,fanart,info)
        addDir(title, 150, icon, fanart, info, show_id)


def list_episodes(show_id):
    url = EPG_URL + '/details/items/program/' + show_id + '/episodes/offset/0/size/20'

    json_source = get_json(url)

    # Sort by airing_date
    json_source = json_source['body']['items']
    json_source = sorted(json_source, key=lambda k: k['airing_date'], reverse=False)

    for show in json_source:
        list_episode(show)


def list_episode(show):
    # if str(show['playable']).upper() == 'FALSE': return
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
    airing_date = show['airing_date']
    airing_date = stringToDate(airing_date, "%Y-%m-%dT%H:%M:%S.000Z")
    airing_date = UTCToLocal(airing_date)
    broadcast_date = show['broadcast_date']
    broadcast_date = stringToDate(broadcast_date, "%Y-%m-%dT%H:%M:%S.000Z")
    broadcast_date = UTCToLocal(broadcast_date)

    genre = ''
    for item in show['genres']:
        if genre != '': genre += ', '
        genre += item['genre']

    plot = ''
    if 'synopsis' in show: plot = show['synopsis']

    if str(show['playable']).upper() == 'FALSE':
        # Add airing date/time to title
        # airing = airing.strftime('%H:%M')
        title = title + ' ' +  airing_date.strftime('%m/%d/%y') + ' ' + airing_date.strftime('%I:%M %p').lstrip('0')



    # if watched = true look in airing for last time code
    # "last_timecode": "00:10:54",

    # channel_url = CHANNEL_URL+'/'+show_id
    show_url = 'https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/airing/' + airing_id

    info = {'plot': plot, 'tvshowtitle': show_title, 'title': title, 'originaltitle': title, 'genre': genre,
            'aired': airing_date.strftime('%Y-%m-%d'), 'premiered': broadcast_date.strftime('%Y-%m-%d')}
    addStream(title, show_url, title, icon, fanart, info)


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

        plot = ''
        if 'synopsis' in channel: plot = channel['synopsis']
        # try: plot = channel['synopsis']
        # except: pass

        channel_url = CHANNEL_URL + '/' + channel_id

        info = {'plot': plot, 'tvshowtitle': title, 'title': title, 'originaltitle': title, 'genre': genre}
        addStream(title, channel_url, title, icon, fanart, info)


def get_stream(url):
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
    # save_cookies(r.cookies)

    stream_url = json_source['body']['video']
    stream_url = stream_url + '|User-Agent=Dalvik/2.1.0 (Linux; U; Android 6.0.1 Build/MOB31H)&Cookie=reqPayload=' + urllib.quote('"' + ADDON.getSetting(id='reqPayload') + '"')

    listitem = xbmcgui.ListItem(path=stream_url)
    # listitem.setProperty('ResumeTime', '600')
    # listitem.setProperty('setResumePoint', '600')

    xbmcplugin.setResolvedUrl(addon_handle, True, listitem)

    # Seek to time
    '''
    monitor = xbmc.Monitor()
    monitor.waitForAbort(3000)
    if xbmc.Player().isPlayingVideo():
        xbmc.Player().seekTime(600)
    '''


def put_resume_time():
    """
    PUT https://sentv-user-action.totsuko.tv/sentv_user_action/ws/v2/watch_history HTTP/1.1
    Host: sentv-user-action.totsuko.tv
    Connection: keep-alive
    Content-Length: 247
    Accept: */*
    reqPayload: redacted
    User-Agent: Mozilla/5.0 (Linux; Android 6.0.1; Build/MOB31H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/44.0.2403.119 Safari/537.36
    Origin: https://themis.dl.playstation.net
    Content-Type: application/json
    Referer: https://themis.dl.playstation.net/themis/zartan/2.2.2b/
    Accept-Encoding: gzip, deflate
    Accept-Language: en-US
    X-Requested-With: com.snei.vue.android

    {"series_id":21188,"program_id":1320750,"channel_id":25039,"tms_id":"EP005544655496","airing_id":14626670,"last_watch_date":"2017-04-28T00:40:43Z","last_timecode":"01:46:29","start_timecode":"00:00:00:00","fully_watched":false,"stream_type":"dvr"}    
    """
    url = 'https://sentv-user-action.totsuko.tv/sentv_user_action/ws/v2/watch_history'
    headers = {"Accept": "*/*",
               "Content-type": "application/json",
               "Origin": "https://themis.dl.playstation.net",
               "Accept-Language": "en-US",
               "Referer": "https://themis.dl.playstation.net/themis/zartan/2.2.2b/",
               "Accept-Encoding": "gzip, deflate",
               "User-Agent": UA_ANDROID,
               "Connection": "Keep-Alive",
               'reqPayload': ADDON.getSetting(id='reqPayload'),
               'X-Requested-With': 'com.snei.vue.android'
               }

    payload = '{"series_id":21188,'
    payload += '"program_id":1320750,'
    payload += '"channel_id":25039,'
    payload += '"tms_id":"EP005544655496",'
    payload += '"airing_id":14626670,'
    payload += '"last_watch_date":"2017-04-28T00:40:43Z",'
    payload += '"last_timecode":"01:46:29",'
    payload += '"start_timecode":"00:00:00:00",'
    payload += '"fully_watched":false,'
    payload += '"stream_type":"dvr"}'

    r = requests.put(url, headers=headers, data=payload, verify=VERIFY)


def login():
    global USERNAME
    if USERNAME == '':
        dialog = xbmcgui.Dialog()
        USERNAME = dialog.input('Please enter your username', type=xbmcgui.INPUT_ALPHANUM)
        if USERNAME != '':
            ADDON.setSetting(id='username', value=USERNAME)
            USERNAME = json.dumps(USERNAME)
        else:
            sys.exit()

    global PASSWORD
    if PASSWORD == '':
        dialog = xbmcgui.Dialog()
        PASSWORD = dialog.input('Please enter your password', type=xbmcgui.INPUT_ALPHANUM,
                                option=xbmcgui.ALPHANUM_HIDE_INPUT)
        if PASSWORD != '':
            ADDON.setSetting(id='password', value=PASSWORD)
            PASSWORD = json.dumps(PASSWORD)
        else:
            sys.exit()

    if USERNAME != '' and PASSWORD != '':
        url = 'https://auth.api.sonyentertainmentnetwork.com/2.0/ssocookie'
        headers = {"Accept": "*/*",
                   "Content-type": "application/x-www-form-urlencoded",
                   "Origin": "https://id.sonyentertainmentnetwork.com",
                   "Accept-Language": "en-US,en;q=0.8",
                   "Accept-Encoding": "deflate",
                   "User-Agent": UA_ANDROID,
                   "Connection": "Keep-Alive"
                   }

        payload = 'authentication_type=password&username=' + USERNAME + '&password=' + PASSWORD + '&client_id=' + LOGIN_CLIENT_ID
        r = requests.post(url, headers=headers, cookies=load_cookies(), data=payload, verify=VERIFY)
        json_source = r.json()
        save_cookies(r.cookies)

        if 'npsso' in json_source:
            npsso = json_source['npsso']
            ADDON.setSetting(id='npsso', value=npsso)
        elif 'authentication_type' in json_source:
            if json_source['authentication_type'] == 'two_step':
                ticket_uuid = json_source['ticket_uuid']
                two_step_verification(ticket_uuid)
        elif 'error_description' in json_source:
            msg = json_source['error_description']
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(LOCAL_STRING(30200), msg)
            sys.exit()
        else:
            # Something went wrong during login
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(LOCAL_STRING(30200), LOCAL_STRING(30201))
            sys.exit()


def two_step_verification(ticket_uuid):
    dialog = xbmcgui.Dialog()
    code = dialog.input('Please enter your verification code', type=xbmcgui.INPUT_ALPHANUM)
    if code == '': sys.exit()

    url = 'https://auth.api.sonyentertainmentnetwork.com/2.0/ssocookie'
    headers = {
        "Accept": "*/*",
        "Content-type": "application/x-www-form-urlencoded",
        "Origin": "https://id.sonyentertainmentnetwork.com",
        "Accept-Language": "en-US,en;q=0.8",
        "Accept-Encoding": "deflate",
        "User-Agent": UA_ANDROID,
        "Connection": "Keep-Alive",
        "Referer": "https://id.sonyentertainmentnetwork.com/signin/?service_entity=urn:service-entity:psn&ui=pr&service_logo=ps&response_type=code&scope=psn:s2s&client_id="+REQ_CLIENT_ID+"&request_locale=en_US&redirect_uri=https://io.playstation.com/playstation/psn/acceptLogin&error=login_required&error_code=4165&error_description=User+is+not+authenticated"
    }

    payload = 'authentication_type=two_step&ticket_uuid='+ticket_uuid+'&code='+code+'&client_id='+LOGIN_CLIENT_ID
    r = requests.post(url, headers=headers, cookies=load_cookies(), data=payload, verify=VERIFY)
    json_source = r.json()
    save_cookies(r.cookies)

    if 'npsso' in json_source:
        npsso = json_source['npsso']
        ADDON.setSetting(id='npsso', value=npsso)
    elif 'error_description' in json_source:
        msg = json_source['error_description']
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(LOCAL_STRING(30200), msg)
        sys.exit()
    else:
        # Something went wrong during login
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(LOCAL_STRING(30200), LOCAL_STRING(30201))
        sys.exit()


def logout():
    url = 'https://auth.api.sonyentertainmentnetwork.com/2.0/ssocookie'
    headers = {
        "User-Agent": "com.sony.snei.np.android.sso.share.oauth.versa.USER_AGENT",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }

    r = requests.delete(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
    # Clear addon settings
    ADDON.setSetting(id='reqPayload', value='')
    ADDON.setSetting(id='npsso', value='')
    ADDON.setSetting(id='default_profile', value='')


def get_reqpayload():
    url = 'https://auth.api.sonyentertainmentnetwork.com/2.0/oauth/authorize'
    url += '?state=209189737'
    url += '&duid=' + DEVICE_ID
    url += '&ui=pr'
    url += '&animation=enable'
    url += '&client_id=' + REQ_CLIENT_ID
    url += '&device_base_font_size=10'
    url += '&device_profile=tablet'
    url += '&hidePageElements=noAccountSection'
    url += '&redirect_uri=https%3A%2F%2Fthemis.dl.playstation.net%2Fthemis%2Fzartan%2Fredirect.html'
    url += '&response_type=code'
    url += '&scope=psn%3As2s'
    url += '&service_entity=urn%3Aservice-entity%3Anp'
    url += '&service_logo=ps'
    url += '&smcid=android%3Apsvue'
    url += '&support_scheme=sneiprls'

    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
               "X-Requested-With": "com.snei.vue.android",
               "Accept-Language": "en-US",
               "Accept-Encoding": "deflate",
               "User-Agent": UA_ANDROID,
               "Connection": "Keep-Alive",
               "Upgrade-Insecure-Requests": "1",
               "Referer": "https://id.sonyentertainmentnetwork.com/signin/?hidePageElements=noAccountSection&smcid=android%3Apsvue&client_id=" + REQ_CLIENT_ID + "&response_type=code&scope=psn%3As2s&redirect_uri=https%3A%2F%2Fthemis.dl.playstation.net%2Fthemis%2Fzartan%2Fredirect.html&state=209189737&service_entity=urn%3Aservice-entity%3Anp&duid=" + DEVICE_ID + "&ui=pr&support_scheme=sneiprls&device_profile=tablet&device_base_font_size=10&animation=enable&service_logo=ps&error=login_required&error_code=4165&error_description=User+is+not+authenticated"
               }

    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
    last_url = r.url
    parsed = urlparse.urlparse(last_url)
    code = urlparse.parse_qs(parsed.query)['code'][0]

    # Get reqPayload
    url = 'https://sentv-user-auth.totsuko.tv/sentv_user_auth/ws/oauth2/token'
    url += '?device_type_id=android_tablet'
    url += '&device_id=' + DEVICE_ID
    url += '&code=' + code
    url += '&redirect_uri=https%3A%2F%2Fthemis.dl.playstation.net%2Fthemis%2Fzartan%2Fredirect.html'

    headers = {"Accept": "*/*",
               "Origin": "https://themis.dl.playstation.net",
               "Connection": "Keep-Alive",
               "Accept-Encoding": "gzip"
               }

    r = requests.get(url, headers=headers, verify=VERIFY)
    req_payload = str(r.headers['reqPayload'])
    ADDON.setSetting(id='reqPayload', value=req_payload)


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
        dialog.notification('Error '+str(r.status_code), 'The request could not be completed.', xbmcgui.NOTIFICATION_INFO, 5000)
        sys.exit()

    return r.json()


def check_reqpayload():
    check_login()

    if ADDON.getSetting(id='reqPayload') == '':
        get_reqpayload()


def check_login():
    expired_cookies = True

    try:
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'), ignore_discard=True)
        if ADDON.getSetting(id='npsso') != '':
            for cookie in cj:
                if cookie.name == 'npsso':
                    xbmc.log(str(cookie.name))
                    xbmc.log(str(cookie.expires))
                    xbmc.log(str(cookie.is_expired()))
                    expired_cookies = cookie.is_expired()
    except:
        pass

    if expired_cookies:
        login()


def get_profiles():
    url = 'https://sentv-user-ext.totsuko.tv/sentv_user_ext/ws/v2/profile/ids'
    headers = {
        'User-Agent': UA_ANDROID,
        'reqPayload': ADDON.getSetting(id='reqPayload'),
        'Accept': '*/*',
        'Origin': 'https://themis.dl.playstation.net',
        'Host': 'sentv-user-ext.totsuko.tv',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }

    r = requests.get(url, headers=headers, verify=VERIFY)
    profiles = r.json()['body']['profiles']
    prof_dict = {}
    prof_list = []
    for profile in profiles:
        xbmc.log(str(profile['profile_id']) + ' ' + str(profile['profile_name']))
        prof_dict[str(profile['profile_name'])] = str(profile['profile_id'])
        prof_list.append(str(profile['profile_name']))

    dialog = xbmcgui.Dialog()
    ret = dialog.select('Choose Profile', prof_list)
    if ret >= 0:
        set_profile(prof_dict[prof_list[ret]])
    else:
        sys.exit()


def set_profile(profile_id):
    url = 'https://sentv-user-ext.totsuko.tv/sentv_user_ext/ws/v2/profile/' + profile_id
    headers = {
        'User-Agent': UA_ANDROID,
        'reqPayload': ADDON.getSetting(id='reqPayload'),
        'Accept': '*/*',
        'Origin': 'https://themis.dl.playstation.net',
        'Host': 'sentv-user-ext.totsuko.tv',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }

    r = requests.get(url, headers=headers, verify=VERIFY)
    req_payload = str(r.headers['reqPayload'])
    ADDON.setSetting(id='reqPayload', value=req_payload)
    ADDON.setSetting(id='default_profile', value=profile_id)


def save_cookies(cookiejar):
    filename = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    lwp_cookiejar = cookielib.LWPCookieJar()
    for c in cookiejar:
        args = dict(vars(c).items())
        args['rest'] = args['_rest']
        del args['_rest']
        c = cookielib.Cookie(**args)
        lwp_cookiejar.set_cookie(c)
    lwp_cookiejar.save(filename, ignore_discard=True)


def load_cookies():
    filename = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    lwp_cookiejar = cookielib.LWPCookieJar()
    try:
        lwp_cookiejar.load(filename, ignore_discard=True)
    except:
        pass

    return lwp_cookiejar


def stringToDate(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))

    return date


def create_device_id():
    android_id = ''.join(random.choice('0123456789abcdef') for i in range(16))
    android_id = android_id.rjust(30, '0')
    manufacturer = 'Amazon'
    model = 'AFTS'  # fire tv gen 2
    manf_model = ":%s:%s" % (manufacturer.rjust(10, ' '), model.rjust(10, ' '))
    manf_model = manf_model.encode("hex")
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


def addDir(name, mode, icon, fanart=None, info=None, show_id=None):
    u = sys.argv[0] + "?mode=" + str(mode)
    if show_id != None: u += '&show_id=' + show_id

    liz = xbmcgui.ListItem(name)
    if fanart == None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    if info != None:
        liz.setInfo(type="Video", infoLabels=info)

    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=True)
    xbmcplugin.setContent(addon_handle, 'tvshows')
    return ok


def addStream(name, link_url, title, icon, fanart, info=None):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(link_url) + "&mode=" + str(900)
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setProperty("IsPlayable", "true")
    # liz.setProperty('setResumePoint', '1200')
    liz.setInfo(type="Video", infoLabels={"Title": title, 'mediatype': 'episode'})
    if info != None:
        liz.setInfo(type="Video", infoLabels=info)
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


addon_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon()
ROOTDIR = ADDON.getAddonInfo('path')
LOCAL_STRING = ADDON.getLocalizedString
FANART = os.path.join(ROOTDIR, "resources", "fanart.jpg")
ICON = os.path.join(ROOTDIR, "resources", "icon.png")

ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
USERNAME = ADDON.getSetting(id='username')
PASSWORD = ADDON.getSetting(id='password')
DEVICE_ID = ADDON.getSetting(id='deviceId')
if DEVICE_ID == '':
    create_device_id()
    DEVICE_ID = ADDON.getSetting(id='deviceId')

UA_ANDROID = 'Mozilla/5.0 (Linux; Android 6.0.1; Build/MOB31H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/44.0.2403.119 Safari/537.36'
LOGIN_CLIENT_ID = '71a7beb8-f21a-47d9-a604-2e71bee24fe0'
REQ_CLIENT_ID = 'dee6a88d-c3be-4e17-aec5-1018514cee40'
CHANNEL_URL = 'https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/channel'
EPG_URL = 'https://epg-service.totsuko.tv/epg_service_sony/service/v2'
VERIFY = False
