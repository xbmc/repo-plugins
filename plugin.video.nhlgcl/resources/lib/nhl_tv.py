from resources.lib.globals import *


def categories():
    add_dir(LOCAL_STRING(30360), '/live', 100, ICON, FANART)
    add_dir(LOCAL_STRING(30361), '/live', 105, ICON, FANART)
    if FAV_TEAM != 'None' and FAV_TEAM != '':
        add_fav_today(FAV_TEAM + LOCAL_STRING(30362).encode('utf8'), FAV_TEAM_LOGO, FANART)
        add_dir(FAV_TEAM + LOCAL_STRING(30363).encode('utf8'), 'favteam', 500, FAV_TEAM_LOGO, FANART)
    add_dir(LOCAL_STRING(30364), '/date', 200, ICON, FANART)
    add_dir(LOCAL_STRING(30365), '/qp', 300, ICON, FANART)


def todays_games(game_day):
    if game_day is None:
        game_day = local_to_eastern()

    xbmc.log("GAME DAY = " + str(game_day))
    settings.setSetting(id='stream_date', value=game_day)
    display_day = string_to_date(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)
    add_dir('[B]<< %s[/B]' % LOCAL_STRING(30010), '/live', 101, PREV_ICON, FANART, prev_day.strftime("%Y-%m-%d"))
    date_display = '[B][I]%s[/I][/B]' % display_day.strftime("%A, %m/%d/%Y")
    addPlaylist(date_display, display_day, '/playhighlights', 900, ICON, FANART)

    url = '%s/schedule?date=%s&expand=schedule.teams,schedule.linescore,schedule.game.content.media.epg' \
          '&site=en_nhl&platform=%s' \
          % (API_URL, game_day, PLATFORM)
    headers = {'User-Agent': UA_IPHONE}
    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
    json_source = r.json()

    global RECAP_PLAYLIST
    global EXTENDED_PLAYLIST
    RECAP_PLAYLIST.clear()
    EXTENDED_PLAYLIST.clear()
    try:
        for game in json_source['dates'][0]['games']:
            create_game_listitem(game, game_day)
    except:
        pass

    next_day = display_day + timedelta(days=1)
    add_dir('[B]%s >>[/B]' % LOCAL_STRING(30011), '/live', 101, NEXT_ICON, FANART, next_day.strftime("%Y-%m-%d"))


def create_game_listitem(game, game_day, show_date=False):
    away = game['teams']['away']['team']
    away_record = game['teams']['away']['leagueRecord']
    home = game['teams']['home']['team']
    home_record = game['teams']['home']['leagueRecord']
    icon = getGameIcon(home['abbreviation'], away['abbreviation'])

    if TEAM_NAMES == "1":
        away_team = away['teamName']
        home_team = home['teamName']
    elif TEAM_NAMES == "2":
        away_team = away['name']
        home_team = home['name']
    elif TEAM_NAMES == "3":
        away_team = away['abbreviation']
        home_team = home['abbreviation']
    else:
        away_team = away['locationName']
        home_team = home['locationName']

    if away_team == "New York":
        away_team = away['name']
    if home_team == "New York":
        home_team = home['name']

    fav_game = False
    if FAV_TEAM_ID == str(away['id']) or FAV_TEAM_ID == str(home['id']):
        fav_game = True

    game_line_header = ''
    detailed_state = game['status']['detailedState'].lower().strip()
    if detailed_state == 'scheduled' or detailed_state == 'pre-game':
        game_time = utc_to_local(string_to_date(game['gameDate'], "%Y-%m-%dT%H:%M:%SZ"))
        if TIME_FORMAT == '0':
            game_time = game_time.strftime('%I:%M %p').lstrip('0')
        else:
            game_time = game_time.strftime('%H:%M')
        game_line_header = game_time

    elif detailed_state == 'in progress':
        game_line_header = '%s %s' % \
                           (game['linescore']['currentPeriodTimeRemaining'], game['linescore']['currentPeriodOrdinal'])

    elif detailed_state == 'final' and show_date:
        game_line_header = utc_to_local(string_to_date(game['gameDate'], "%Y-%m-%dT%H:%M:%SZ")).strftime("%Y-%m-%d")

    else:
        game_line_header = game['status']['detailedState']

    game_id = str(game['gamePk'])

    desc = ''
    hide_spoilers = 0
    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) \
            or (NO_SPOILERS == '3' and game_day == local_to_eastern()) \
            or (NO_SPOILERS == '4' and game_day < local_to_eastern()) \
            or game['status']['abstractGameState'].lower().strip() == 'preview':

        name = '%s %s at %s' % (game_line_header, away_team, home_team)
        hide_spoilers = 1
    else:
        name = '%s %s - %s at %s - %s' % \
               (game_line_header, away_team, game['teams']['away']['score'], home_team, game['teams']['home']['score'])
        away_wins = away_record['wins'] if 'wins' in away_record else '0'
        away_losses = away_record['losses'] if 'losses' in away_record else '0'
        away_ot = away_record['ot'] if 'ot' in away_record else '0'
        home_wins = home_record['wins'] if 'wins' in home_record else '0'
        home_losses = home_record['losses'] if 'losses' in home_record else '0'
        home_ot = home_record['ot'] if 'ot' in home_record else '0'
        desc = '%s %s-%s-%s\n%s %s-%s-%s' % (away_team, away_wins, away_losses, away_ot,
                                             home_team, home_wins, home_losses, home_ot)

    fanart = 'http://nhl.bamcontent.com/images/arena/default/%s@2x.jpg' % home['id']
    try:
        if game_day < local_to_eastern():
            if hide_spoilers == 0:
                desc = str(game['content']['media']['epg'][3]['items'][0]['description'])
        else:
            if PREVIEW_INFO == 'true':
                url = API_URL + '/game/' + str(game['gamePk']) + '/content?site=en_nhl'
                headers = {'User-Agent': UA_IPHONE,
                           'Connection': 'close'
                           }

                r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
                json_source = r.json()
                fanart = str(
                    json_source['editorial']['preview']['items'][0]['media']['image']['cuts']['1284x722']['src'])
                soup = BeautifulSoup(str(json_source['editorial']['preview']['items'][0]['preview']))
                desc = soup.get_text()
            elif hide_spoilers == 0 and 'scoringPlays' in game:
                for play in game['scoringPlays']:
                    scorer = play['result']['description']
                    scorer = scorer[0:scorer.find(",")]
                    when = play['about']['periodTime'] + ' ' + play['about']['ordinalNum']
                    game_score = '(' + str(play['about']['goals']['away']) + ' - ' + str(
                        play['about']['goals']['home']) + ')'
                    desc += color_string(when, LIVE) + ' ' + scorer + ' ' + game_score + '\n'
    except:
        pass

    name = name
    if fav_game:
        name = '[B]%s[/B]' % name

    title = '%s at %s' % (away_team, home_team)

    # Label free game of the day
    try:
        if bool(game['content']['media']['epg'][0]['items'][0]['freeGame']):
            name = color_string(name, FREE)
    except:
        pass

    # Set audio/video info based on stream quality setting
    audio_info, video_info = getAudioVideoInfo()
    # 'duration':length
    info = {'plot': desc,
            'tvshowtitle': 'NHL',
            'title': title,
            'originaltitle': title,
            'aired': game_day,
            'genre': 'Sports'}

    start_time = None
    try:
        start_time = game['linescore']['periods'][0]['startTime']
    except:
        pass

    # Create playlists for all highlights
    global RECAP_PLAYLIST
    recap = get_epg_item(game['content']['media']['epg'], "recap")
    if 'items' in recap and len(recap['items']) > 0:
        recap_url = get_highlight_url(recap['items'][0]['playbacks'])
        recap_url = create_highlight_stream(recap_url)
        listitem = xbmcgui.ListItem(title)
        listitem.setArt({'thumb' : icon})
        listitem.setInfo(type="Video", infoLabels={"Title": title})
        RECAP_PLAYLIST.add(recap_url, listitem)

    global EXTENDED_PLAYLIST
    extend = get_epg_item(game['content']['media']['epg'], "extended highlights")
    if 'items' in extend and len(extend['items']) > 0:
        extend_url = get_highlight_url(extend['items'][0]['playbacks'])
        extend_url = create_highlight_stream(extend_url)
        listitem = xbmcgui.ListItem(title)
        listitem.setArt({'thumb' : icon})
        listitem.setInfo(type="Video", infoLabels={"Title": title})
        EXTENDED_PLAYLIST.add(extend_url, listitem)

    add_stream(name, '', title, game_id, icon, fanart, info, video_info, audio_info, start_time)


def stream_select(game_id, start_time):
    url = '%s/game/%s/content' % (API_URL, game_id)
    headers = {'User-Agent': UA_PC}
    r = requests.get(url, headers=headers, verify=VERIFY)

    if not r.ok or 'media' not in r.json() or 'epg' not in r.json()['media']:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(LOCAL_STRING(30366), LOCAL_STRING(30367))
        sys.exit()

    epg = r.json()['media']['epg']
    full_game = get_epg_item(epg, "nhltv")
    # audio_items = get_epg_item(epg, "audio")['items']
    stream_title = []
    content_id = []
    event_id = []
    free_game = []
    media_state = []

    multi_angle = 0
    multi_cam = 0
    if 'items' in full_game and len(full_game['items']) > 0:
        for item in full_game['items']:
            media_state.append(item['mediaState'])
            feed_type = item['mediaFeedType']
            if feed_type == "COMPOSITE":
                multi_cam += 1
                stream_title.append("Multi-Cam " + str(multi_cam))
            elif feed_type == "ISO":
                multi_angle += 1
                stream_title.append("Multi-Angle " + str(multi_angle))
            else:
                temp_item = feed_type.title()
                if item['callLetters'] != '':
                    temp_item = '%s (%s)' % (temp_item, item['callLetters'])
                stream_title.append(temp_item)

            content_id.append(item['mediaPlaybackId'])
            event_id.append(item['eventId'])
            free_game.append(item['freeGame'])
    else:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(LOCAL_STRING(30366), LOCAL_STRING(30367))
        sys.exit()

    if 'archive' in media_state[0].lower().strip():
        stream_url, headers = media_archive(stream_title, content_id, event_id, epg)
    else:
        stream_url, headers = media_live(stream_title, content_id, event_id)

    if stream_url == '':
        sys.exit()
    else:
        start_from_beginning = -1
        if start_time is not None and 'archive' not in media_state[0].lower().strip():
            dialog = xbmcgui.Dialog()
            start_from_beginning = dialog.select("Choose Start", ['Watch Live', 'Start from Beginning'])

        listitem = stream_to_listitem(stream_url, headers)
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem)

        if start_from_beginning == 1:
            while not xbmc.Player().isPlayingVideo() and not xbmc.Monitor().abortRequested():
                xbmc.Monitor().waitForAbort(0.25)

            if xbmc.Player().isPlayingVideo() and not xbmc.Monitor().abortRequested():
                xbmc.Monitor().waitForAbort(0.25)
                start_time = string_to_date(start_time, '%Y-%m-%dT%H:%M:%SZ')
                seek_secs = int((start_time - datetime.utcnow()).total_seconds())
                xbmc.log("seconds seek = " + str(seek_secs))
                xbmc.executebuiltin('Seek(' + str(seek_secs) + ')')


def media_live(stream_title, content_id, event_id):
    stream_url = ''
    headers = 'User-Agent=' + UA_IPHONE
    dialog = xbmcgui.Dialog()
    n = dialog.select('Choose Stream', stream_title)
    if n > -1:
        stream_url, media_auth = fetch_stream(content_id[n], event_id[n])
        if stream_url != '':
            stream_url, headers = create_full_game_stream(stream_url, media_auth)

    return stream_url, headers


def media_archive(stream_title, content_id, event_id, epg):
    stream_url = ''
    headers = 'User-Agent=' + UA_IPHONE
    highlight = get_epg_item(epg, "extended highlights")
    recap = get_epg_item(epg, "recap")

    archive_type = [LOCAL_STRING(30022), LOCAL_STRING(30021), LOCAL_STRING(30020)]
    dialog = xbmcgui.Dialog()
    a = dialog.select('Choose Archive', archive_type)

    # Full Game
    if archive_type[a] == LOCAL_STRING(30020) and a != -1:
        n = dialog.select('Choose Stream', stream_title)
        if n > -1:
            stream_url, media_auth = fetch_stream(content_id[n], event_id[n])
            if stream_url != '':
                stream_url, headers = create_full_game_stream(stream_url, media_auth)

    # Extended Highlights
    elif archive_type[a] == LOCAL_STRING(30021):
        stream_url = get_highlight_url(highlight['items'][0]['playbacks'])
        stream_url = create_highlight_stream(stream_url)

    # Recap
    elif archive_type[a] == LOCAL_STRING(30022):
        stream_url = get_highlight_url(recap['items'][0]['playbacks'])
        stream_url = create_highlight_stream(stream_url)

    return stream_url, headers


def get_epg_item(epg, title):
    for item in epg:
        if item['title'].lower().strip() == title.lower().strip():
            break

    return item


def get_highlight_url(playbacks):
    for item in playbacks:
        url = item['url']
        if item['name'] == PLAYBACK_SCENARIO:
            break

    return url


def play_all_highlights():
    stream_title = ['Recap', 'Extended Highlights']
    dialog = xbmcgui.Dialog()
    n = dialog.select('View All', stream_title)

    if n == 0:
        xbmc.Player().play(RECAP_PLAYLIST)
    elif n == 1:
        xbmc.Player().play(EXTENDED_PLAYLIST)


def create_highlight_stream(stream_url):
    bandwidth = find(QUALITY, '(', ' kbps)')
    if bandwidth != '':
        stream_url = stream_url.replace(stream_url.rsplit('/', 1)[-1], 'asset_' + bandwidth + 'k.m3u8')

    stream_url = stream_url + '|User-Agent=' + UA_IPHONE
    xbmc.log(stream_url)
    return stream_url


def create_full_game_stream(stream_url, media_auth):
    if not xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):
        bandwidth = ''
        bandwidth = find(QUALITY, '(', ' kbps)')

        # Only set bandwidth if it's explicitly set in add-on settings
        if QUALITY.upper() == 'ALWAYS ASK':
            bandwidth = getStreamQuality(stream_url)

        if bandwidth != '':
            # Reduce convert bandwidth if composite video selected
            if 'COMPOSITE' in stream_url or 'ISO' in stream_url:
                if int(bandwidth) >= 3500:
                    bandwidth = '3500'
                elif int(bandwidth) == 1200:
                    bandwidth = '1500'

            playlist = get_playlist(stream_url, media_auth)
            for line in playlist:
                if bandwidth in line and '#EXT' not in line:
                    if 'http' in line:
                        stream_url = line
                    else:
                        stream_url = stream_url.replace(stream_url.rsplit('/', 1)[-1], line)

    cj = load_cookies()

    cookies = ''
    for cookie in cj:
        if cookie.name == "Authorization":
            cookies = cookies + cookie.name + "=" + cookie.value + "; "

    headers = 'User-Agent=' + UA_IPHONE + '&Cookie=' + cookies + media_auth
    xbmc.log("STREAM URL: " + stream_url)
    return stream_url, headers


def get_playlist(stream_url, media_auth):
    headers = {
        "User-Agent": UA_NHL,
        "Cookie": media_auth
    }

    r = requests.get(stream_url, headers=headers, cookies=load_cookies(), verify=VERIFY)
    playlist = r.text

    return playlist.splitlines()


def fetch_stream(content_id, event_id):
    stream_url = ''
    media_auth = ''

    authorization = getAuthCookie()
    if authorization == '':
        login()
        authorization = getAuthCookie()
        if authorization == '':
            return stream_url, media_auth

    session_key = get_session_key(event_id, authorization)

    url = '%s/stream?contentId=%s&playbackScenario=%s&platform=%s&sessionKey=%s' % \
          (API_MEDIA_URL, content_id, PLAYBACK_SCENARIO, PLATFORM, urllib.quote_plus(session_key))
    if settings.getSetting('debug') != "":
        url += settings.getSetting('debug')

    # Get user set CDN
    if CDN == 'Akamai':
        url += '&cdnName=MED2_AKAMAI_SECURE'
    elif CDN == 'Level 3':
        url += '&cdnName=MED2_LEVEL3_SECURE'

    headers = {
        "Authorization": authorization,
        "User-Agent": UA_NHL
    }
    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)

    if r.ok and 'session_key' in r.json():
        settings.setSetting(id='session_key', value=r.json()['session_key'])

    if not r.ok or 'status_code' not in r.json() or r.json()['status_code'] != 1:
        msg = LOCAL_STRING(30368)
        if 'status_message' in r.json():
            msg = r.json()['status_message']
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(LOCAL_STRING(30368), msg)
        sys.exit()
    else:
        if r.json()['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['blackout_status']['status'] == 'BlackedOutStatus':
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(LOCAL_STRING(30370), LOCAL_STRING(30371))
            sys.exit()
        elif r.json()['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['auth_status'] == 'NotAuthorizedStatus':
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(LOCAL_STRING(30372), LOCAL_STRING(30373))
            sys.exit()
        else:
            stream_url = r.json()['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['url']
            media_auth = str(r.json()['session_info']['sessionAttributes'][0]['attributeName'])
            media_auth += "=" + str(r.json()['session_info']['sessionAttributes'][0]['attributeValue'])

            settings.setSetting(id='media_auth', value=media_auth)

    return stream_url, media_auth


def get_session_key(event_id, authorization):
    # session_key = ''
    session_key = str(settings.getSetting(id="session_key"))

    if session_key == '':
        epoch_time_now = str(int(round(time.time() * 1000)))

        url = '%s/stream?eventId=%s&format=json&platform=%s&subject=NHLTV&_=%s' % \
              (API_MEDIA_URL, event_id, PLATFORM, epoch_time_now)
        if settings.getSetting('debug') != "":
            url += settings.getSetting('debug')
        headers = {
            "Accept": "application/json",
            "Authorization": authorization,
            "User-Agent": UA_PC
        }

        r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
        if r.ok and 'session_key' in r.json():
            settings.setSetting(id='session_key', value=r.json()['session_key'])

        if not r.ok or 'status_code' not in r.json() or r.json()['status_code'] != 1:
            msg = LOCAL_STRING(30368)
            if 'status_message' in r.json():
                msg = r.json()['status_message']
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(LOCAL_STRING(30368), msg)
            sys.exit()
        else:
            if r.json()['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['blackout_status']['status'] == 'BlackedOutStatus':
                dialog = xbmcgui.Dialog()
                ok = dialog.ok(LOCAL_STRING(30370), LOCAL_STRING(30371))
                sys.exit()

    return session_key


def login():
    # Check if username and password are provided
    global USERNAME
    if USERNAME == '':
        dialog = xbmcgui.Dialog()
        USERNAME = dialog.input(LOCAL_STRING(30380), type=xbmcgui.INPUT_ALPHANUM)
        settings.setSetting(id='username', value=USERNAME)
    global PASSWORD
    if PASSWORD == '':
        dialog = xbmcgui.Dialog()
        PASSWORD = dialog.input(LOCAL_STRING(30381), type=xbmcgui.INPUT_ALPHANUM,
                                option=xbmcgui.ALPHANUM_HIDE_INPUT)
        settings.setSetting(id='password', value=PASSWORD)

    if USERNAME != '' and PASSWORD != '':
        url = 'https://user.svc.nhl.com/oauth/token?grant_type=client_credentials'
        headers = {
            "Accept": "application/json",
            "User-Agent": UA_PC,
            "Origin": "https://www.nhl.com",
            "Authorization": "Basic d2ViX25obC12MS4wLjA6MmQxZDg0NmVhM2IxOTRhMThlZjQwYWM5ZmJjZTk3ZTM=",
        }

        r = requests.post(url, headers=headers, data='', cookies=load_cookies(), verify=VERIFY)
        if not r.ok:            
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(LOCAL_STRING(30382), LOCAL_STRING(30383))
            sys.exit()

        json_source = r.json()

        authorization = getAuthCookie()
        if authorization == '':
            authorization = json_source['access_token']

        if ROGERS_SUBSCRIBER == 'true':
            url = 'https://activation-rogers.svc.nhl.com/ws/subscription/flow/rogers.login'
            login_data = {"rogerCredentials": {"email": USERNAME, "password": PASSWORD}}
        else:
            url = 'https://user.svc.nhl.com/v2/user/identity'
            login_data = {"email":{"address": USERNAME},"type":"email-password","password":{"value": PASSWORD}}

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": authorization,
            "User-Agent": UA_PC
        }

        r = requests.post(url, headers=headers, json=login_data, cookies=load_cookies(), verify=VERIFY)

        if not r.ok:
            if 'message' in r.json():
                msg = r.json()['message']
            else:
                msg = LOCAL_STRING(30385)

            dialog = xbmcgui.Dialog()
            ok = dialog.ok(LOCAL_STRING(30384), msg)
            sys.exit()

        save_cookies(r.cookies)


def logout(display_msg=None):
    # Delete cookie file
    if os.path.exists(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')):
        os.remove(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))

    if display_msg == 'true':
        settings.setSetting(id='session_key', value='')
        dialog = xbmcgui.Dialog()        
        dialog.notification(LOCAL_STRING(30386), LOCAL_STRING(30387), ICON, 5000, False)


def my_teams_games():
    if FAV_TEAM == 'None':
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(LOCAL_STRING(30390), LOCAL_STRING(30391))
    else:
        end_day = local_to_eastern()
        end_date = string_to_date(end_day, "%Y-%m-%d")
        start_date = end_date - timedelta(days=30)
        start_day = start_date.strftime("%Y-%m-%d")

        url = '%s/schedule?teamId=%s&startDate=%s&endDate=%s&expand=schedule.linescore,schedule.game.content.media.epg,schedule.teams' % \
              (API_URL, FAV_TEAM_ID, start_day, end_day)
        headers = {'User-Agent': UA_IPHONE}
        r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)

        for date in reversed(r.json()['dates']):
            for game in date['games']:
                create_game_listitem(game, date['date'], True)


def play_fav_team_today():
    if FAV_TEAM == 'None':
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(LOCAL_STRING(30390), LOCAL_STRING(30391))
    else:
        end_day = local_to_eastern()
        start_day = end_day

        url = '%s/schedule?teamId=%s&startDate=%s&endDate=%s&expand=schedule.game.content.media.epg,schedule.teams' % \
              (API_URL, FAV_TEAM_ID, start_day, end_day)
        headers = {'User-Agent': UA_IPHONE}

        r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
        stream_url = ''
        if r.ok and r.json()['dates']:
            todays_game = r.json()['dates'][0]['games'][0]
            # Determine if favorite team is home or away
            fav_team_homeaway = ''
            away = todays_game['teams']['away']['team']
            home = todays_game['teams']['home']['team']

            if FAV_TEAM_ID == str(away['id']):
                fav_team_homeaway = 'AWAY'
            elif FAV_TEAM_ID == str(home['id']):
                fav_team_homeaway = 'HOME'

            # Grab the correct feed (home/away/national)
            epg = todays_game['content']['media']['epg']
            streams = epg[0]['items']
            local_stream = {}
            natl_stream = {}
            for stream in streams:
                feedType = stream['mediaFeedType']
                if feedType == fav_team_homeaway:
                    local_stream = stream
                    break
                elif feedType == 'NATIONAL':
                    natl_stream = stream
            if not local_stream:
                local_stream = natl_stream

            # Create the stream url
            stream_url, media_auth = fetch_stream(local_stream['mediaPlaybackId'], local_stream['eventId'])
            if stream_url != '':
                stream_url, headers = create_full_game_stream(stream_url, media_auth)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(LOCAL_STRING(30374), FAV_TEAM + LOCAL_STRING(30375).encode('utf8'))
            sys.exit()

        if stream_url != '':
            listitem = stream_to_listitem(stream_url, headers)
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
        else:
            xbmcplugin.setResolvedUrl(addon_handle, False, listitem)


def goto_date():
    # Goto Date
    search_txt = ''
    dialog = xbmcgui.Dialog()
    # game_day = dialog.input('Enter date (yyyy-mm-dd)', type=xbmcgui.INPUT_ALPHANUM)
    game_day = ''

    # Year
    year_list = []
    # year_item = datetime.now().year
    year_item = 2015
    while year_item <= datetime.now().year:
        year_list.insert(0, str(year_item))
        year_item = year_item + 1

    ret = dialog.select('Choose Year', year_list)

    if ret > -1:
        year = year_list[ret]
        mnth_name = ['January', 'February', 'March', 'April', 'May', 'June', 'September', 'October', 'November',
                     'December']
        mnth_num = ['1', '2', '3', '4', '5', '6', '9', '10', '11', '12']

        ret = dialog.select('Choose Month', mnth_name)

        if ret > -1:
            mnth = mnth_num[ret]

            # Day
            day_list = []
            day_item = 1
            last_day = calendar.monthrange(int(year), int(mnth))[1]
            while day_item <= last_day:
                day_list.append(str(day_item))
                day_item = day_item + 1

            ret = dialog.select('Choose Day', day_list)

            if ret > -1:
                day = day_list[ret]
                game_day = year + '-' + mnth.zfill(2) + '-' + day.zfill(2)

    if game_day != '':
        todays_games(game_day)
    else:
        sys.exit()


def nhl_videos(selected_topic=None):
    url = 'http://nhl.bamcontent.com/nhl/en/nav/v1/video/connectedDevices/nhl/playstation-v1.json'
    headers = {'User-Agent': UA_PS4}
    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
    json_source = r.json()

    if selected_topic is None or 'topic=' not in selected_topic:
        for topic in json_source['topics']:
            add_dir(topic['title'], '/topic=' + topic['title'] + '&', 300, ICON, FANART)
    else:
        topic = find(selected_topic, 'topic=', '&')
        for main_topic in json_source['topics']:
            if topic == main_topic['title']:
                for video in main_topic['list']:
                    title = video['title']
                    name = title
                    try:
                        icon = video['image']['cuts']['1136x640']['src']
                    except:
                        icon = ICON
                    url = video['playbacks'][4]['url']
                    desc = video['description']
                    release_date = video['date'][0:10]
                    duration = video['duration']

                    bandwidth = find(QUALITY, '(', ' kbps)')
                    if bandwidth != '':
                        url = url.replace('master_wired60.m3u8', 'asset_' + bandwidth + 'k.m3u8')
                    url = url + '|User-Agent=' + UA_PS4

                    audio_info, video_info = getAudioVideoInfo()
                    info = {'plot': desc,
                            'tvshowtitle': 'NHL',
                            'title': name,
                            'originaltitle': name,
                            'duration': duration,
                            'aired': release_date
                            }
                    add_link(name, url, title, icon, info, video_info, audio_info, icon)
