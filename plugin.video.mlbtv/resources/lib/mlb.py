from resources.lib.globals import *
from .account import Account


def categories():
    addDir(LOCAL_STRING(30360), 100, ICON, FANART)
    addDir(LOCAL_STRING(30361), 105, ICON, FANART)
    addDir(LOCAL_STRING(30362), 200, ICON, FANART)


def todays_games(game_day):
    if game_day is None:
        game_day = localToEastern()

    settings.setSetting(id='stream_date', value=game_day)

    display_day = stringToDate(game_day, "%Y-%m-%d")
    #url_game_day = display_day.strftime('year_%Y/month_%m/day_%d')
    prev_day = display_day - timedelta(days=1)

    addDir('[B]<< %s[/B]' % LOCAL_STRING(30010), 101, PREV_ICON, FANART, prev_day.strftime("%Y-%m-%d"))

    date_display = '[B][I]' + colorString(display_day.strftime("%A, %m/%d/%Y"), GAMETIME_COLOR) + '[/I][/B]'

    addPlaylist(date_display, str(game_day), 900, ICON, FANART)

    # addPlaylist(date_display,display_day,'/playhighlights',999,ICON,FANART)

    #url = 'http://gdx.mlb.com/components/game/mlb/' + url_game_day + '/grid_ce.json'
    url = 'https://statsapi.mlb.com/api/v1/schedule'
    url += '?hydrate=broadcasts(all),game(content(all)),linescore,team'
    url += '&sportId=1,51'
    url += '&date=' + game_day

    headers = {
        'User-Agent': UA_ANDROID
    }
    xbmc.log(url)
    r = requests.get(url,headers=headers, verify=VERIFY)
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
    addDir('[B]%s >>[/B]' % LOCAL_STRING(30011), 101, NEXT_ICON, FANART, next_day.strftime("%Y-%m-%d"))


def create_game_listitem(game, game_day):
    # icon = getGameIcon(game['home_team_id'],game['away_team_id'])
    icon = ICON
    # http://mlb.mlb.com/mlb/images/devices/ballpark/1920x1080/2681.jpg
    # B&W
    # fanart = 'http://mlb.mlb.com/mlb/images/devices/ballpark/1920x1080/'+game['venue_id']+'.jpg'
    # Color
    # fanart = 'http://www.mlb.com/mlb/images/devices/ballpark/1920x1080/color/' + str(game['venue']['id']) + '.jpg'
    fanart = 'http://cd-images.mlbstatic.com/stadium-backgrounds/color/light-theme/1920x1080/' + str(game['venue']['id']) + '.png'


    xbmc.log(str(game['gamePk']))

    if TEAM_NAMES == "0":
        away_team = game['teams']['away']['team']['teamName']
        home_team = game['teams']['home']['team']['teamName']
    else:
        away_team = game['teams']['away']['team']['abbreviation']
        home_team = game['teams']['home']['team']['abbreviation']

    title = away_team + ' at ' + home_team
    title = title

    fav_game = False
    if game['teams']['away']['team']['name'] in FAV_TEAM:
        fav_game = True
        away_team = colorString(away_team, getFavTeamColor())

    if game['teams']['home']['team']['name'] in FAV_TEAM:
        fav_game = True
        home_team = colorString(home_team, getFavTeamColor())

    game_time = ''
    #if game['status']['abstractGameState'] == 'Preview':
    if game['status']['detailedState'].lower() == 'scheduled' or game['status']['detailedState'].lower() == 'pre-game':
        game_time = game['gameDate']
        game_time = stringToDate(game_time, "%Y-%m-%dT%H:%M:%SZ")
        game_time = UTCToLocal(game_time)

        if TIME_FORMAT == '0':
            game_time = game_time.strftime('%I:%M %p').lstrip('0')
        else:
            game_time = game_time.strftime('%H:%M')

        game_time = colorString(game_time, UPCOMING)

    else:
        #game_time = game['status']['abstractGameState']
        game_time = game['status']['detailedState']

        if game_time == 'Final':
            game_time = colorString(game_time, FINAL)

        elif game['status']['abstractGameState'] == 'Live':
            if game['linescore']['isTopInning']:
                # up triangle
                # top_bottom = u"\u25B2"
                top_bottom = "T"
            else:
                # down triangle
                # top_bottom = u"\u25BC"
                top_bottom = "B"

            inning = game['linescore']['currentInningOrdinal']
            game_time = top_bottom + ' ' + inning

            if game['linescore']['currentInning'] >= 9:
                color = CRITICAL
            else:
                color = LIVE

            game_time = colorString(game_time, color)

        else:
            game_time = colorString(game_time, LIVE)

    #event_id = str(game['calendar_event_id'])
    game_pk = game['gamePk']
    #gid = game['id']
    gid = 'junk'

    live_feeds = 0
    archive_feeds = 0
    stream_date = str(game_day)

    desc = ''
    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) or (NO_SPOILERS == '3' and game_day == localToEastern()) or (NO_SPOILERS == '4' and game_day < localToEastern()) or game['status']['abstractGameState'] == 'Preview':
        name = game_time + ' ' + away_team + ' at ' + home_team
    else:
        name = game_time + ' ' + away_team
        if 'linescore' in game: name += ' ' + colorString(str(game['linescore']['teams']['away']['runs']), SCORE_COLOR)
        name += ' at ' + home_team
        if 'linescore' in game: name += ' ' + colorString(str(game['linescore']['teams']['home']['runs']), SCORE_COLOR)
        try:
            desc = game['content']['editorial']['recap']['mlb']['headline']
        except:
            pass

    name = name
    if fav_game:
        name = '[B]' + name + '[/B]'

    # Label free game of the day if applicable
    try:
        if game['content']['media']['freeGame']:
            # and game_day >= localToEastern():
            name = colorString(name, FREE)
    except:
        pass


    # Set audio/video info based on stream quality setting
    audio_info, video_info = getAudioVideoInfo()
    # 'duration':length
    info = {'plot': desc, 'tvshowtitle': 'MLB', 'title': title, 'originaltitle': title, 'aired': game_day, 'genre': LOCAL_STRING(700), 'mediatype': 'video'}

    # Create Playlist for the days recaps and condensed
    """
    teams_stream = game['teams']['away']['team']['teamCode'] + game['teams']['home']['team']['teamCode']
    try:
        recap_url, condensed_url = get_highlight_links(teams_stream, stream_date)
        global RECAP_PLAYLIST
        listitem = xbmcgui.ListItem(title, thumbnailImage=icon)
        listitem.setInfo(type="Video", infoLabels={"Title": title})
        RECAP_PLAYLIST.add(recap_url, listitem)

        global EXTENDED_PLAYLIST
        listitem = xbmcgui.ListItem(title, thumbnailImage=icon)
        listitem.setInfo(type="Video", infoLabels={"Title": title})
        EXTENDED_PLAYLIST.add(condensed_url, listitem)
    except:
        pass
    """
    add_stream(name, title, game_pk, icon, fanart, info, video_info, audio_info, stream_date)


def stream_select(game_pk):
    url = 'https://statsapi.mlb.com/api/v1/game/' + game_pk + '/content'
    headers = {
        'User-Agent': UA_ANDROID
    }
    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    stream_title = ['Highlights']
    media_state = []
    content_id = []
    epg = json_source['media']['epg'][0]['items']
    for item in epg:
        xbmc.log(str(item))
        if item['mediaState'] != 'MEDIA_OFF':
            if IN_MARKET != 'Hide' or (item['mediaFeedType'] != 'IN_MARKET_HOME' and item['mediaFeedType'] != 'IN_MARKET_AWAY'):
                title = str(item['mediaFeedType']).title()
                title = title.replace('_', ' ')
                if 'HOME' in title.upper():
                    media_state.insert(0, item['mediaState'])
                    content_id.insert(0, item['contentId'])
                    stream_title.insert(1, title + " (" + item['callLetters'] + ")")
                else:
                    media_state.append(item['mediaState'])
                    content_id.append(item['contentId'])
                    stream_title.append(title + " (" + item['callLetters'] + ")")

    # All past games should have highlights
    if len(stream_title) == 0:
        # and stream_date > localToEastern():
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog()
        dialog.notification('Streams Not Found', msg, ICON, 5000, False)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
        sys.exit()

    stream_url = ''

    dialog = xbmcgui.Dialog()
    n = dialog.select('Choose Stream', stream_title)
    if n > -1 and stream_title[n] != 'Highlights':
        account = Account()
        stream_url, headers = account.get_stream(content_id[n-1])
        if epg[0]['mediaState'] == "MEDIA_ON" and CATCH_UP == 'true':
            p = dialog.select('Select a Start Point', ['Catch Up', 'Live'])
            if p == 0:
                listitem = stream_to_listitem(stream_url, headers)
                highlight_select_stream(json_source['highlights']['live']['items'], listitem)
                sys.exit()
            elif p == -1:
                sys.exit()

    if '.m3u8' in stream_url:
        play_stream(stream_url, headers)

    elif stream_title[n] == 'Highlights':
        highlight_select_stream(json_source['highlights']['highlights']['items'])

    else:
        sys.exit()


def highlight_select_stream(json_source, catchup=None):
    highlights = get_highlights(json_source)
    if not highlights and catchup is None:
        msg = "No videos found."
        dialog = xbmcgui.Dialog()
        dialog.notification('Highlights', msg, ICON, 5000, False)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
        sys.exit()

    highlight_name = ['Play All']
    highlight_url = ['junk']

    for clip in highlights:
        highlight_name.append(clip['title'])
        highlight_url.append(clip['url'])

    if catchup is None:
        dialog = xbmcgui.Dialog()
        a = dialog.select('Choose Highlight', highlight_name)
    else:
        a = 0

    if a > 0:
        play_stream(highlight_url[a], '')
    elif a == 0:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        for clip in highlights:
            listitem = xbmcgui.ListItem(clip['url'])
            listitem.setArt({'icon': clip['icon'], 'thumb': clip['icon'], 'fanart': FANART})
            listitem.setInfo(type="Video", infoLabels={"Title": clip['title']})
            playlist.add(clip['url'], listitem)

        if catchup is not None:
            playlist.add(catchup.getPath(), catchup)

        xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=playlist[0])


def play_stream(stream_url, headers):
    listitem = stream_to_listitem(stream_url, headers)
    xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=listitem)


def get_highlights(items):
    xbmc.log(str(items))
    highlights = []
    for item in items:
        for playback in item['playbacks']:
            if 'hlsCloud' in playback['name']:
                clip_url = playback['url']
                break
        headline = item['headline']
        icon = item['image']['cuts'][0]['src']
        highlights.append({'url': clip_url, 'title': headline, 'icon': icon})

    return highlights


def getGamesForDate(stream_date):
    stream_date_new = stringToDate(stream_date, "%Y-%m-%d")
    year = stream_date_new.strftime("%Y")
    month = stream_date_new.strftime("%m")
    day = stream_date_new.strftime("%d")

    url = 'http://gdx.mlb.com/components/game/mlb/year_' + year + '/month_' + month + '/day_' + day + '/'
    #req = urllib2.Request(url)
    #req.add_header('Connection', 'close')
    #req.add_header('User-Agent', UA_IPAD)

    try:
        r = requests.get(url, headers={'User-Agent': UA_IPAD})
        # response = urllib2.urlopen(req)
        html_data = r.text()
        # response.close()
    #except HTTPError as e:
    except requests.exceptions.RequestException as e:
        xbmc.log('The server couldn\'t fulfill the request.')
        xbmc.log('Error code: ', e.code)
        sys.exit()

    # <li><a href="gid_2016_03_13_arimlb_chamlb_1/"> gid_2016_03_13_arimlb_chamlb_1/</a></li>
    match = re.compile('<li><a href="gid_(.+?)/">(.+?)</a></li>', re.DOTALL).findall(html_data)
    global RECAP_PLAYLIST
    global EXTENDED_PLAYLIST
    RECAP_PLAYLIST.clear()
    EXTENDED_PLAYLIST.clear()

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(LOCAL_STRING(30380), LOCAL_STRING(30381))
    match_count = len(match)
    if match_count == 0:
        match_count = 1  # prevent division by zero when no games
    perc_increments = 100 / match_count
    first_time_thru = True
    bandwidth = find(QUALITY, '(', ' kbps)')

    for gid, junk in match:
        pDialog.update(perc_increments, message=LOCAL_STRING(30382) + gid)
        try:
            recap, condensed, highlights = get_highlight_links(None, stream_date, gid)

            if first_time_thru and QUALITY == 'Always Ask':
                bandwidth = getStreamQuality(str(recap['url']))
                first_time_thru = False

            listitem = xbmcgui.ListItem(recap['title'], thumbnailImage=recap['icon'])
            listitem.setInfo(type="Video", infoLabels={"Title": recap['title']})
            RECAP_PLAYLIST.add(createHighlightStream(recap['url'], bandwidth), listitem)

            listitem = xbmcgui.ListItem(condensed['title'], thumbnailImage=condensed['icon'])
            listitem.setInfo(type="Video", infoLabels={"Title": condensed['title']})
            EXTENDED_PLAYLIST.add(createHighlightStream(condensed['url'], bandwidth), listitem)
        except:
            pass

        perc_increments += perc_increments

    pDialog.close()


def createHighlightStream(url, bandwidth):
    if bandwidth != '' and int(bandwidth) < 4500:
        url = url.replace('master_tablet_60.m3u8', 'asset_' + bandwidth + 'K.m3u8')

    url = url + '|User-Agent=' + UA_IPAD

    return url


def get_highlight_links(teams_stream, stream_date):
    stream_date = stringToDate(stream_date, "%Y-%m-%d")
    year = stream_date.strftime("%Y")
    month = stream_date.strftime("%m")
    day = stream_date.strftime("%d")

    #if gid is None:
    away = teams_stream[:3].lower()
    home = teams_stream[3:].lower()
    #url = 'https://content.mlb.com/app/mlb/mobile/components/game/mlb/year_' + year + '/month_' + month + '/day_' + day + '/gid_' + year + '_' + month + '_' + day + '_' + away + 'mlb_' + home + 'mlb_1/media/mobile.xml'
    url = 'https://content.mlb.com/app/mlb/mobile/components/game/mlb/year_%s/month_%s/day_%s/gid_%s_%s_%s_%smlb_%smlb_1/media/mobile.xml' % (
    year, month, day, year, month, day, away, home)


    headers = {
        'User-Agent': UA_IPAD
    }

    r = requests.get(url, headers=headers, verify=VERIFY)
    xml_data = r.text
    match = re.compile('<media id="(.+?)"(.+?)<headline>(.+?)</headline>(.+?)<thumb type="22">(.+?)</thumb>(.+?)<url playback-scenario="HTTP_CLOUD_TABLET_60">(.+?)</url>', re.DOTALL).findall(xml_data)
    #bandwidth = find(QUALITY, '(', ' kbps)')

    recap = {}
    condensed = {}
    highlights = []

    for media_id, media_tag, headline, junk1, icon, junk2, clip_url in match:
        if 'media-type="T"' in media_tag:
            # if bandwidth != '' and int(bandwidth) < 4500:
            # clip_url = clip_url.replace('master_tablet_60.m3u8', 'asset_'+bandwidth+'K.m3u8')

            # clip_url = clip_url + '|User-Agent='+UA_IPAD
            highlights.append([clip_url, headline, icon])

        if 'media-type="R"' in media_tag:
            # icon = 'http://mediadownloads.mlb.com/mlbam/'+year+'/'+month+'/'+day+'/images/mlbf_'+media_id+'_th_43.jpg'
            title = headline
            recap = {'url': clip_url, 'icon': icon, 'title': headline}
        elif 'media-type="C"' in media_tag:
            # icon = 'http://mediadownloads.mlb.com/mlbam/'+year+'/'+month+'/'+day+'/images/mlbf_'+media_id+'_th_43.jpg'
            title = headline
            condensed = {'url': clip_url, 'icon': icon, 'title': headline}

    return recap, condensed, highlights





