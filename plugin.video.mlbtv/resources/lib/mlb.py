from resources.lib.globals import *

def categories():
    addDir(LOCAL_STRING(30360), 100, ICON, FANART)
    addDir(LOCAL_STRING(30361), 105, ICON, FANART)
    # see yesterday's scores at inning in the main menu
    addDir(LOCAL_STRING(30413), 108, ICON, FANART)
    addDir(LOCAL_STRING(30362), 200, ICON, FANART)
    # show MiLB games in the main menu
    addDir(LOCAL_STRING(30426), 109, ICON, FANART)
    # show Featured Videos in the main menu
    addDir(LOCAL_STRING(30363), 300, ICON, FANART)

def minor_league_categories():
    addDir(LOCAL_STRING(30429), 110, ICON, FANART)
    addDir(LOCAL_STRING(30430), 100, ICON, FANART, None, 'False', '11')
    addDir(LOCAL_STRING(30431), 100, ICON, FANART, None, 'False', '12')
    addDir(LOCAL_STRING(30432), 100, ICON, FANART, None, 'False', '13')
    addDir(LOCAL_STRING(30433), 100, ICON, FANART, None, 'False', '14')

def affiliate_menu():
    for affiliate in AFFILIATE_TEAM_IDS:
        addDir(affiliate, 100, ICON, FANART, None, 'False', '11,12,13,14', AFFILIATE_TEAM_IDS[affiliate])


def todays_games(game_day, start_inning='False', sport=MLB_ID, teams='None'):
    today = localToEastern()
    if game_day is None:
        game_day = today

    settings.setSetting(id='stream_date', value=game_day)

    display_day = stringToDate(game_day, "%Y-%m-%d")
    #url_game_day = display_day.strftime('year_%Y/month_%m/day_%d')
    prev_day = display_day - timedelta(days=1)

    addDir('[B]<< %s[/B]' % LOCAL_STRING(30010), 101, PREV_ICON, FANART, prev_day.strftime("%Y-%m-%d"), start_inning, sport, teams)

    # add recap note to past day titles
    recap_note = ''
    if sport == MLB_ID and game_day < today:
        recap_note = ' (watch all recaps)'
    date_display = '[B][I]' + colorString(display_day.strftime("%A, %m/%d/%Y") + recap_note, GAMETIME_COLOR) + '[/I][/B]'

    addPlaylist(date_display, str(game_day), 900, ICON, FANART)

    #url = 'http://gdx.mlb.com/components/game/mlb/' + url_game_day + '/grid_ce.json'
    url = API_URL + '/api/v1/schedule'
    # url += '?hydrate=broadcasts(all),game(content(all)),probablePitcher,linescore,team,flags'
    url += '?hydrate=broadcasts(all),game(content(media(epg))),probablePitcher,linescore,team,flags,gameInfo'
    # 51 is international (i.e. World Baseball Classic) but they aren't streamed in the normal way
    #url += '&sportId=1,51'
    url += '&sportId=' + sport
    if sport == MLB_ID and INCLUDE_FAV_AFFILIATES == 'true':
        url += ',' + MILB_IDS
    url += '&date=' + game_day
    if teams != 'None':
        url += '&teamId=' + teams
    elif sport == MLB_ID:
        url += '&teamId=' + MLB_TEAM_IDS
        if INCLUDE_FAV_AFFILIATES == 'true' and FAV_TEAM != 'None':
            url += ',' + AFFILIATE_TEAM_IDS[FAV_TEAM]

    headers = {
        'User-Agent': UA_ANDROID
    }
    xbmc.log(url)
    r = requests.get(url,headers=headers, verify=VERIFY)
    json_source = r.json()

    games = []
    if 'dates' in json_source and len(json_source['dates']) > 0 and 'games' in json_source['dates'][0]:
        games = json_source['dates'][0]['games']

    favorite_games = []
    remaining_games = []

    fav_team_id = getFavTeamId()
    game_changer_starts = []
    game_changer_start = None
    game_changer_end = None
    inprogress_exists = False
    nonentitlement_data = get_nonentitlement_data(game_day)
    blackouts = []

    # loop through games to find favorite team
    for game in games:
        if fav_team_id is not None and fav_team_id in [str(game['teams']['home']['team']['id']), str(game['teams']['away']['team']['id'])]:
            favorite_games.append(game)
        else:
            remaining_games.append(game)

        game['scheduled_innings'] = get_scheduled_innings(game)
            
        # while looping through today's games, also count in progress, non-blackout MLB games for Game Changer
        if str(game['gamePk']) in nonentitlement_data:
            blackouts.append(str(game['gamePk']))
        else:
            if game['teams']['home']['team']['sport']['id'] == 1 and 'rescheduleDate' not in game:
                game_changer_starts.append(game['gameDate'])

            if not inprogress_exists and game['status']['detailedState'] == 'In Progress':
                inprogress_exists = True

    try:
        for game in favorite_games:
            create_game_listitem(game, game_day, start_inning, today, nonentitlement_data)
    except:
        pass

    # Big Inning and game changer only available for non-free accounts (and not in minor league lists)
    if ONLY_FREE_GAMES != 'true' and sport == MLB_ID:
        # if the requested date is today,
        # then show any entitled linear channel listitems
        from .account import Account
        account = Account()
        entitlements = json.loads(account.get_entitlements())
        if today == game_day and ('MLBN' in entitlements or 'MLBALL' in entitlements or 'MLBTVMLBNADOBEPASS' in entitlements or 'EXECMLB' in entitlements):
            create_linear_channel_listitem('MLBN')
        if today == game_day and 'SNLA_119' in entitlements:
            create_linear_channel_listitem('SNLA')
        if today == game_day and 'SNY_121' in entitlements:
            create_linear_channel_listitem('SNY')
            
        # if the requested date is not in the past, we have games for this date, and it's a regular season date,
        # then show the Big Inning listitem
        if today <= game_day and len(games) > 0 and games[0]['seriesDescription'] == 'Regular Season':
            create_big_inning_listitem(game_day)

        # if it's today and there's more than one non-blackout MLB game, show the game changer listitem
        if today == game_day and len(game_changer_starts) > 1:
            # use second game and second-to-last game for game changer display times
            game_changer_starts.sort()
            game_changer_start = game_changer_starts[1]
            game_changer_end = game_changer_starts[len(game_changer_starts) - 2]
            create_game_changer_listitem(blackouts, inprogress_exists, game_changer_start, game_changer_end)
            create_stream_finder_listitem(blackouts, inprogress_exists, game_changer_start, game_changer_end)


    try:
        for game in remaining_games:
            create_game_listitem(game, game_day, start_inning, today, nonentitlement_data)
    except:
        pass

    next_day = display_day + timedelta(days=1)
    addDir('[B]%s >>[/B]' % LOCAL_STRING(30011), 101, NEXT_ICON, FANART, next_day.strftime("%Y-%m-%d"), start_inning, sport, teams)


def create_game_listitem(game, game_day, start_inning, today, nonentitlement_data):
    game_pk = game['gamePk']
    xbmc.log(str(game_pk))

    milb = None
    level_abbr = ''
    # MiLB titles and graphics
    if game['teams']['away']['team']['sport']['id'] != 1 and game['teams']['home']['team']['sport']['id'] != 1:
        # Skip MiLB games without any broadcast
        milb_broadcast = None
        if 'broadcasts' in game:
            for broadcast in game['broadcasts']:
                if broadcast['name'] == 'MiLB.TV':
                    milb_broadcast = broadcast
                    break
        if milb_broadcast is None:
            return

        milb = 'True'

        level_abbr = game['teams']['home']['team']['sport']['name']
        if level_abbr[0] == 'T':
            level_abbr = 'AAA'
        elif level_abbr[0] == 'D':
            level_abbr = 'AA'
        elif level_abbr[0] == 'H':
            level_abbr = 'A+'
        elif level_abbr[0] == 'S':
            level_abbr = 'A'
        level_abbr += ': '

        away_name = game['teams']['away']['team']['shortName']
        away_org = game['teams']['away']['team']['parentOrgName'].split()[-1]
        if (away_org == 'Sox') or (away_org == 'Jays'):
            away_org = game['teams']['away']['team']['parentOrgName'].split()[-2] + ' ' + game['teams']['away']['team']['parentOrgName'].split()[-1]

        home_name = game['teams']['home']['team']['shortName']
        home_org = game['teams']['home']['team']['parentOrgName'].split()[-1]
        if (home_org == 'Sox') or (home_org == 'Jays'):
            home_org = game['teams']['home']['team']['parentOrgName'].split()[-2] + ' ' + game['teams']['home']['team']['parentOrgName'].split()[-1]

        away_team = away_name + ' (' + away_org + ')'
        home_team = home_name + ' (' + home_org + ')'

        title = level_abbr + away_team + ' at ' + home_team

        icon_id = game['teams']['home']['team']['id']
        if away_org in FAV_TEAM:
            fav_game = True
            away_team = colorString(away_team, getFavTeamColor())
            icon_id = game['teams']['away']['team']['id']

        if home_org in FAV_TEAM:
            fav_game = True
            home_team = colorString(home_team, getFavTeamColor())

        icon = 'https://www.mlbstatic.com/team-logos/share/' + str(icon_id) + '.jpg'
        fanart = FANART

        desc = game['teams']['home']['team']['sport']['name'] + ' ' + game['teams']['home']['team']['league']['name'] + '[CR]' + game['teams']['away']['team']['name'] + ' at ' + game['teams']['home']['team']['name'] + '[CR]'

    # MLB titles and graphics
    else:

        if TEAM_NAMES == "0":
            away_team = game['teams']['away']['team']['teamName']
            home_team = game['teams']['home']['team']['teamName']
        else:
            away_team = game['teams']['away']['team']['abbreviation']
            home_team = game['teams']['home']['team']['abbreviation']

        # Use full team name for non-MLB teams
        if game['teams']['away']['team']['sport']['name'] != 'Major League Baseball':
            away_team = game['teams']['away']['team']['name']
        if game['teams']['home']['team']['sport']['name'] != 'Major League Baseball':
            home_team = game['teams']['home']['team']['name']

        title = away_team + ' at ' + home_team

        if game['teams']['away']['team']['sport']['id'] == 1 and game['teams']['home']['team']['sport']['id'] == 1:
            icon = 'https://img.mlbstatic.com/mlb-photos/image/upload/ar_167:215,c_crop/fl_relative,l_team:' + str(game['teams']['home']['team']['id']) + ':fill:spot.png,w_1.0,h_1,x_0.5,y_0,fl_no_overflow,e_distort:100p:0:200p:0:200p:100p:0:100p/fl_relative,l_team:' + str(game['teams']['away']['team']['id']) + ':logo:spot:current,w_0.38,x_-0.25,y_-0.16/fl_relative,l_team:' + str(game['teams']['home']['team']['id']) + ':logo:spot:current,w_0.38,x_0.25,y_0.16/w_750/team/' + str(game['teams']['away']['team']['id']) + '/fill/spot.png'
            fanart = 'http://cd-images.mlbstatic.com/stadium-backgrounds/color/light-theme/1920x1080/%s.png' % game['venue']['id']
        else:
            icon = ICON
            fanart = FANART

        desc = ''

    is_free = False
    if 'broadcasts' in game and len(game['broadcasts']) > 0 and 'freeGame' in game['broadcasts'][0] and game['broadcasts'][0]['freeGame'] is True:
        is_free = True

    fav_game = False
    if game['teams']['away']['team']['name'] in FAV_TEAM:
        fav_game = True
        away_team = colorString(away_team, getFavTeamColor())

    if game['teams']['home']['team']['name'] in FAV_TEAM:
        fav_game = True
        home_team = colorString(home_team, getFavTeamColor())

    game_time = ''
    suspended = 'False'
    display_time = 'TBD'
    relative_inning = None
    spoiler = 'True'
    today = localToEastern()
    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) or (NO_SPOILERS == '3' and game_day == today) or (NO_SPOILERS == '4' and game_day < today):
        spoiler = 'False'

    if 'gameDate' in game:
        display_time = get_display_time(UTCToLocal(stringToDate(game['gameDate'], "%Y-%m-%dT%H:%M:%SZ")))

    game_state = game['status']['detailedState']

    #if game['status']['abstractGameState'] == 'Preview':
    if game_state == 'Scheduled' or game_state == 'Pre-Game' or game_state == 'Warmup':
        if game['status']['startTimeTBD'] is True:
            game_time = 'TBD'
        else:
            game_time = display_time

        game_time = colorString(game_time, UPCOMING)

    else:
        #game_time = game['status']['abstractGameState']
        game_time = game_state

        if game_state != 'Postponed':
            # if we've requested to see scores at a particular inning
            if start_inning != 'False' and 'linescore' in game:
                relative_inning = (int(start_inning) - (9 - game['scheduled_innings']))
                if relative_inning > len(game['linescore']['innings']):
                    relative_inning = len(game['linescore']['innings'])
                start_inning = relative_inning
                if relative_inning > 0:
                    game_time = 'T' + str(relative_inning)
                else:
                    game_time = display_time
            elif game_state != 'Final' and game['status']['abstractGameState'] == 'Live' and 'linescore' in game:
                if game['linescore']['isTopInning']:
                    # up triangle
                    # top_bottom = u"\u25B2"
                    top_bottom = "T"
                else:
                    # down triangle
                    # top_bottom = u"\u25BC"
                    top_bottom = "B"

                if game['linescore']['currentInning'] >= game['scheduled_innings'] and spoiler == 'False':
                    game_time = str(game['scheduled_innings']) + 'th+'
                else:
                    game_time = top_bottom + ' ' + game['linescore']['currentInningOrdinal']

            try:
                if 'resumeGameDate' in game or 'resumedFromDate' in game:
                    suspended = 'archive'
                    if 'resumeGameDate' in game:
                        game_time += ' (Suspended)'
                    elif 'resumedFromDate' in game:
                        game_time += ' (Resumed)'
                        if stringToDate(game['gameDate'], "%Y-%m-%dT%H:%M:%SZ") > datetime.now():
                            game_time = display_time + ' ' + game_time
                    for epg in game['content']['media']['epg'][0]['items']:
                        if epg['mediaState'] == 'MEDIA_ON':
                            suspended = 'live'
                            break
                        elif epg['mediaState'] == 'MEDIA_OFF':
                            game_time = display_time + ' ' + game_time
                            break
            except:
                pass

        if game_state == 'Final' or game_state == 'Postponed':
            game_time = colorString(game_time, FINAL)

        elif game['status']['abstractGameState'] == 'Live':
            if 'linescore' in game and game['linescore']['currentInning'] >= game['scheduled_innings']:
                color = CRITICAL
            else:
                color = LIVE

            game_time = colorString(game_time, color)

        else:
            game_time = colorString(game_time, LIVE)

    stream_date = str(game_day)

    probables = ''
    if ('probablePitcher' in game['teams']['away'] and 'fullName' in game['teams']['away']['probablePitcher']) or ('probablePitcher' in game['teams']['home'] and 'fullName' in game['teams']['home']['probablePitcher']):
        probables = ' ('
        if 'probablePitcher' in game['teams']['away'] and 'fullName' in game['teams']['away']['probablePitcher']:
            desc += game['teams']['away']['probablePitcher']['fullName']
            probables += get_last_name(game['teams']['away']['probablePitcher']['fullName'])
        else:
            desc += 'TBD'
            probables += 'TBD'
        desc += ' vs. '
        probables += ' vs '
        if 'probablePitcher' in game['teams']['home'] and 'fullName' in game['teams']['home']['probablePitcher']:
            desc += game['teams']['home']['probablePitcher']['fullName']
            probables += get_last_name(game['teams']['home']['probablePitcher']['fullName'])
        else:
            desc += 'TBD'
            probables += 'TBD'
        probables += ')'

    if 'venue' in game and 'name' in game['venue']:
        desc += '[CR]From ' + game['venue']['name']
    if game['status']['abstractGameState'] == 'Preview' or (start_inning == 'False' and spoiler == 'False'):
        name = game_time + ' ' + level_abbr + away_team + ' at ' + home_team
    else:
        name = game_time + ' ' + level_abbr + away_team
        away_score = ''
        home_score = ''
        try:
            if 'linescore' in game and game_state != 'Postponed':
                away_score = 0
                home_score = 0
                if relative_inning is None:
                    away_score = game['linescore']['teams']['away']['runs']
                    home_score = game['linescore']['teams']['home']['runs']
                else:
                    for inning in game['linescore']['innings']:
                        if int(inning['num']) < relative_inning:
                            away_score += inning['away']['runs']
                            home_score += inning['home']['runs']
                        else:
                            break
                away_score = ' ' + colorString(str(away_score), SCORE_COLOR)
                home_score = ' ' + colorString(str(home_score), SCORE_COLOR)
        except:
            pass

        name += str(away_score) + ' at ' + home_team + str(home_score)

        # check flags
        if 'flags' in game:
            if game['flags']['perfectGame'] is True:
                name += ' ' + colorString('(Perfect Game)', CRITICAL)
            elif game['flags']['noHitter'] is True:
                name += ' ' + colorString('(No-Hitter)', CRITICAL)

    if game['doubleHeader'] != 'N':
        doubleheader_label = 'Game ' + str(game['gameNumber'])
        name += ' (' + doubleheader_label + ')'
        desc += '[CR]' + doubleheader_label

    if game['status']['abstractGameState'] == 'Final' and game_state != 'Final':
        desc += '[CR]' + game_state

    if 'description' in game and game['description'] != "":
        desc += '[CR]' + game['description']

    if game['scheduled_innings'] != 9:
        desc += '[CR]' + str(game['scheduled_innings']) + '-inning game'

    # Display TV broadcast info
    broadcast_list = []
    if 'broadcasts' in game:
        for broadcast in game['broadcasts']:
            # ignore non-TV and duplicate broadcasts
            if broadcast['type'] == 'TV' and broadcast['name'] not in broadcast_list:
                broadcast_list.append(broadcast['name'])
    if len(broadcast_list) > 0:
        desc += '[CR]' + ", ".join(broadcast_list)

    # Check entitlement/blackout status
    blackout = 'False'
    try:
        if str(game['gamePk']) in nonentitlement_data:
            blackout = 'True'
            name = blackoutString(name)
            if nonentitlement_data[str(game['gamePk'])] != '':
                blackout = nonentitlement_data[str(game['gamePk'])]
                blackout_display_time = get_display_time(UTCToLocal(blackout))
                desc += '[CR]Live video blackout until approx. 2.5 hours after the game (~' + blackout_display_time + ')'
            else:
                desc += '[CR]Your account may not be entitled to stream this game'
                
    except:
        pass

    if fav_game:
        name = '[B]' + name + '[/B]'

    if is_free:
        name = colorString(name, FREE)

    name += colorString(probables, FINAL)

    # Get audio/video info
    audio_info, video_info = getAudioVideoInfo()
    # 'duration':length
    info = {'plot': desc, 'tvshowtitle': 'MLB', 'title': title, 'originaltitle': title, 'aired': game_day, 'genre': LOCAL_STRING(700), 'mediatype': 'video'}

    # If set only show free games in the list
    if ONLY_FREE_GAMES == 'true' and not is_free:
        return
    add_stream(name, title, desc, game_pk, icon, fanart, info, video_info, audio_info, stream_date, spoiler, suspended, start_inning, blackout, milb)


# fetch a list of featured videos
def get_video_list(list_url=None):
    # use the Featured on MLB.TV list (included Big Inning) if no list is specified
    if list_url == None:
        list_url = 'https://dapi.cms.mlbinfra.com/v2/content/en-us/sel-mlbtv-featured-svod-video-list'

    headers = {
        'User-Agent': UA_PC,
        'Origin': 'https://www.mlb.com',
        'Referer': 'https://www.mlb.com',
        'Content-Type': 'application/json'
    }
    r = requests.get(list_url, headers=headers, verify=VERIFY)
    json_source = r.json()
    return json_source


# display a list of featured videos
def featured_videos(featured_video=None):
    # if no list is specified, use the master list of lists
    if featured_video == None:
        featured_video = 'https://mastapi.mobile.mlbinfra.com/api/video/v1/playlist'

    video_list = get_video_list(featured_video)
    if 'items' in video_list:
        for item in video_list['items']:
            #xbmc.log(str(item))
            if 'title' in item:
                title = item['title']
                liz=xbmcgui.ListItem(title)

                # check if a video url is provided
                if 'fields' in item:
                    description = title
                    if 'description' in item['fields']:
                        description = item['fields']['description']
                    liz.setInfo( type="Video", infoLabels={ "Title": title, "plot": description } )
                    video_url = None
                    if 'playbackScenarios' in item['fields']:
                        for playback in item['fields']['playbackScenarios']:
                            if playback['playback'] == 'hlsCloud':
                                video_url = playback['location']
                                break
                    elif 'url' in item['fields']:
                        video_url = item['fields']['url']
                    if video_url is not None:
                        xbmc.log('video url : ' + video_url)
                        if 'thumbnail' in item and 'thumbnailUrl' in item['thumbnail']:
                            thumbnail = item['thumbnail']['thumbnailUrl']
                            # modify thumnail URL for use as icon and fanart
                            icon = thumbnail.replace('w_250,h_250,c_thumb,g_auto,q_auto,f_jpg', 't_16x9/t_w1080')
                            fanart = thumbnail.replace('w_250,h_250,c_thumb,g_auto,q_auto,f_jpg', 'g_auto,c_fill,ar_16:9,q_60,w_1920/e_gradient_fade:15,x_0.6,b_black')
                        else:
                            icon = ICON
                            fanart = FANART
                        liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
                        liz.setProperty("IsPlayable", "true")
                        u=sys.argv[0]+"?mode="+str(301)+"&featured_video="+urllib.quote_plus(video_url)+"&name="+urllib.quote_plus(title)
                        isFolder=False
                # if no video url is provided, we assume it is just another list
                else:
                    liz.setInfo( type="Video", infoLabels={ "Title": title } )
                    list_url = item['url']
                    xbmc.log('list url : ' + list_url)
                    if list_url == "":
                        continue
                    u=sys.argv[0]+"?mode="+str(300)+"&featured_video="+urllib.quote_plus(list_url)
                    isFolder=True

                xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=isFolder)
                xbmcplugin.setContent(addon_handle, 'episodes')

        # if it's a long list, display a "Next" link if provided
        if 'pagination' in video_list and 'nextUrl' in video_list['pagination']:
            title = '[B]%s >>[/B]' % LOCAL_STRING(30011)
            liz=xbmcgui.ListItem(title)
            liz.setInfo( type="Video", infoLabels={ "Title": title } )
            list_url = video_list['pagination']['nextUrl']
            if list_url != "":
                u=sys.argv[0]+"?mode="+str(300)+"&featured_video="+urllib.quote_plus(list_url)
                isFolder=True
                xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=isFolder)
                xbmcplugin.setContent(addon_handle, 'episodes')


# display a linear channel item within a game list
def create_linear_channel_listitem(network):
    try:
        if network == 'MLBN':
            title = LOCAL_STRING(30367) + LOCAL_STRING(30438)
            description = LOCAL_STRING(30439)
            video_url = 'https://falcon.mlbinfra.com/api/v1/linear/mlbn'
            icon = 'https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcQRgC2JdbtFplKjfhXm5_vzpkUQ3XyDT91SEnHmuB0p5tReQ3Ez'
            fanart = 'https://img.mlbstatic.com/mlb-images/image/private/ar_16:9,g_auto,q_auto:good,w_1536,c_fill,f_jpg/mlb/i138wzlhv79dq3xvo1ti'
            mode = 301
        elif network == 'SNLA':
            title = LOCAL_STRING(30367) + LOCAL_STRING(30440)
            description = LOCAL_STRING(30441)
            video_url = 'SNLA_LIVE'
            icon = 'https://img.mlbstatic.com/mlb-images/image/upload/t_w640/mlb/fnwk2k0kgn1j8r8vvx3d.png'
            fanart = FANART
            mode = 302
        elif network == 'SNY':
            title = LOCAL_STRING(30367) + LOCAL_STRING(30442)
            description = LOCAL_STRING(30443)
            video_url = 'SNY_LIVE'
            icon = 'https://img.mlbstatic.com/mlb-images/image/upload/t_w640/mlb/le5jifzo6oylxtnuf0m1.png'
            fanart = FANART
            mode = 302
        
        liz=xbmcgui.ListItem(title)
        liz.setInfo( type="Video", infoLabels={ "Title": title, "plot": description } )
        liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
        liz.setProperty("IsPlayable", "true")
        u=sys.argv[0]+"?mode="+str(mode)+"&featured_video="+urllib.quote_plus(video_url)+"&name="+urllib.quote_plus(title)
        isFolder=False

        xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=isFolder)
        xbmcplugin.setContent(addon_handle, 'episodes')
    except Exception as e:
        xbmc.log('mlb network error : ' + str(e))
        pass


# display a Big Inning item within a game list
def create_big_inning_listitem(game_day):
    try:
        # check when we last fetched the Big Inning schedule
        today = localToEastern()
        big_inning_date = str(settings.getSetting(id="big_inning_date"))

        # if we've already fetched it today, use the cached schedule
        if big_inning_date == today:
            xbmc.log('Using cached Big Inning schedule')
            big_inning_schedule = json.loads(settings.getSetting(id="big_inning_schedule"))
        # otherwise, fetch a new big inning schedule
        else:
            xbmc.log('Fetching Big Inning schedule')
            settings.setSetting(id='big_inning_date', value=today)
            url = 'https://api.fubo.tv/gg/series/123881219/live-programs?limit=14&languages=en&countrySlugs=USA'

            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'no-cache',
                'dnt': '1',
                'pragma': 'no-cache',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'sec-gpc': '1',
                'upgrade-insecure-requests': '1',
                'user-agent': UA_PC
            }
            r = requests.get(url,headers=headers, verify=VERIFY)
            #xbmc.log(r.text)

            # parse the response
            json_source = r.json()
            
            big_inning_schedule = {}
            if 'data' in json_source:
                for entry in json_source['data']:
                    if 'airings' in entry and len(entry['airings']) > 0 and entry['airings'][0] and 'accessRightsV2' in entry['airings'][0] and 'live' in entry['airings'][0]['accessRightsV2']:
                        airing = entry['airings'][0]['accessRightsV2']['live']
                        big_inning_date = get_eastern_game_date(parse(airing['startTime']))
                        xbmc.log('Formatted date ' + big_inning_date)
                        # ignore dates in the past
                        if big_inning_date >= today:
                            big_inning_start = str(UTCToLocal(parse(airing['startTime'])))
                            big_inning_end = str(UTCToLocal(parse(airing['endTime'])))
                            big_inning_schedule[big_inning_date] = {'start': big_inning_start, 'end': big_inning_end}
            # save the scraped schedule
            settings.setSetting(id='big_inning_schedule', value=json.dumps(big_inning_schedule))

        if game_day in big_inning_schedule:
            xbmc.log(game_day + ' has a scheduled Big Inning broadcast')
            display_title = LOCAL_STRING(30368)

            big_inning_start = parse(big_inning_schedule[game_day]['start'])
            big_inning_end = parse(big_inning_schedule[game_day]['end'])

            # format the time for display

            game_time = get_display_time(big_inning_start) + ' - ' + get_display_time(big_inning_end)
            now = datetime.now()
            if now < big_inning_start:
                game_time = colorString(game_time, UPCOMING)
            elif now > big_inning_end:
                game_time = colorString(game_time, FINAL)
            elif now >= big_inning_start and now <= big_inning_end:
                display_title = LOCAL_STRING(30367) + LOCAL_STRING(30368)
                game_time = colorString(game_time, LIVE)
            name = game_time + ' ' + display_title

            desc = 'MLB Big Inning brings fans all the best action from around the league with live look-ins, breaking highlights and big moments as they happen all season long. Airing seven days a week on MLB.TV.'

            # create the list item
            liz=xbmcgui.ListItem(name)
            liz.setInfo( type="Video", infoLabels={ "Title": display_title, 'plot': desc } )
            liz.setProperty("IsPlayable", "true")
            icon = 'https://img.mlbstatic.com/mlb-images/image/private/ar_16:9,g_auto,q_auto:good,w_372,c_fill,f_jpg/mlb/uwr8vepua4t1fe8uwyki'
            fanart = 'https://img.mlbstatic.com/mlb-images/image/private/g_auto,c_fill,ar_16:9,q_60,w_1920/e_gradient_fade:15,x_0.6,b_black/mlb/uwr8vepua4t1fe8uwyki'
            liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
            u=sys.argv[0]+"?mode="+str(301)+"&featured_video="+urllib.quote_plus(LOCAL_STRING(30367) + LOCAL_STRING(30368))+"&name="+urllib.quote_plus(LOCAL_STRING(30367) + LOCAL_STRING(30368))
            xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=False)
            xbmcplugin.setContent(addon_handle, 'episodes')
        else:
            xbmc.log(game_day + ' does not have a scheduled Big Inning broadcast')
    except Exception as e:
        xbmc.log('big inning error : ' + str(e))
        pass


# display a Game Changer item within a game list
def create_game_changer_listitem(blackouts, inprogress_exists, game_changer_start, game_changer_end):
    display_title = LOCAL_STRING(30417)

    # format the time for display
    game_time = get_display_time(UTCToLocal(stringToDate(game_changer_start, "%Y-%m-%dT%H:%M:%SZ"))) + ' - ' + get_display_time(UTCToLocal(stringToDate(game_changer_end, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3) + timedelta(minutes=30)))

    if inprogress_exists:
        display_title = LOCAL_STRING(30367) + LOCAL_STRING(30417)
        game_time = colorString(game_time, LIVE)

    name = game_time + ' ' + display_title

    desc = LOCAL_STRING(30418)

    # create the list item
    liz=xbmcgui.ListItem(name)
    liz.setInfo( type="Video", infoLabels={ "Title": name, 'plot': desc } )
    liz.setProperty("IsPlayable", "true")
    liz.setArt({'icon': ICON, 'thumb': ICON, 'fanart': FANART})
    u=sys.argv[0]+"?mode="+str(500)+"&name="+urllib.quote_plus(name)+"&description="+urllib.quote_plus(desc)+"&blackout="+urllib.quote_plus(','.join(blackouts))
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, 'episodes')


# display a Stream Finder item within a game list
def create_stream_finder_listitem(blackouts, inprogress_exists, game_changer_start, game_changer_end):
    display_title = LOCAL_STRING(30444)

    # format the time for display
    game_time = get_display_time(UTCToLocal(stringToDate(game_changer_start, "%Y-%m-%dT%H:%M:%SZ"))) + ' - ' + get_display_time(UTCToLocal(stringToDate(game_changer_end, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=3) + timedelta(minutes=30)))

    if inprogress_exists:
        display_title = LOCAL_STRING(30367) + LOCAL_STRING(30444)
        game_time = colorString(game_time, LIVE)

    name = game_time + ' ' + display_title

    desc = LOCAL_STRING(30445) + 'http://' + xbmc.getIPAddress() + ':43670'

    # create the list item
    liz=xbmcgui.ListItem(name)
    liz.setInfo( type="Video", infoLabels={ "Title": name, 'plot': desc } )
    liz.setProperty("IsPlayable", "true")
    liz.setArt({'icon': STREAM_FINDER_ICON, 'thumb': STREAM_FINDER_ICON, 'fanart': FANART})
    u=sys.argv[0]+"?mode="+str(501)+"&name="+urllib.quote_plus(name)+"&description="+urllib.quote_plus(desc)+"&blackout="+urllib.quote_plus(','.join(blackouts))
    xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, 'episodes')


def stream_select(game_pk, spoiler='True', suspended='False', start_inning='False', blackout='False', description=None, name=None, icon=None, fanart=None, from_context_menu=False, autoplay=False, overlay_check='False', gamechanger='False'):
    # fetch the entitlements using the game_pk
    from .account import Account
    account = Account()
    login_token = account.login_token()
    okta_id = account.okta_id()
    
    url = 'https://mastapi.mobile.mlbinfra.com/api/epg/v3/search?exp=MLB&gamePk=' + game_pk
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://www.mlb.com', 
        'pragma': 'no-cache',
        'priority': 'u=1, i', 
        'referer': 'https://www.mlb.com/', 
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"', 
        'sec-ch-ua-mobile': '?0', 
        'sec-ch-ua-platform': '"macOS"', 
        'sec-fetch-dest': 'empty', 
        'sec-fetch-mode': 'cors', 
        'sec-fetch-site': 'same-site', 
        'user-agent': UA_PC
    }
    if login_token is not None and okta_id is not None:
        headers['authorization'] = 'Bearer ' + login_token
        headers['x-okta-id'] = okta_id
    r = requests.get(url,headers=headers, verify=VERIFY)
    json_source = r.json()
    entitled_feeds = []
    blackout_feeds = []
    if 'results' in json_source and len(json_source['results']) > 0:
        for result in json_source['results']:
            for feed in result['videoFeeds']:
                if feed['entitled'] == True:
                    entitled_feeds.append(feed['mediaId'])
                if feed['blackedOut'] == True:
                    blackout_feeds.append(feed['mediaId'])
            for feed in result['audioFeeds']:
                if feed['entitled'] == True:
                    entitled_feeds.append(feed['mediaId'])
    
    # fetch the epg content using the game_pk
    #url = f'{API_URL}/api/v1/schedule?gamePk={game_pk}&hydrate=team,linescore,xrefId,flags,review,broadcasts(all),,seriesStatus(useOverride=true),statusFlags,story&sortBy=gameDate,gameStatus,gameType'
    url = f'{API_URL}/api/v1/schedule?gamePk={game_pk}&hydrate=broadcasts(all),game(content(highlights(highlights)))'        
    headers = {
        'User-Agent': UA_PC
    }
    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()
    # start with just video content, assumed to be at index 0
    #epg = json_source['media']['epg'][0]['items']
    #epg = json_source['dates'][0]['games'][0]['broadcasts']
    epg = []
    # loop through dates/games and skip those that have been rescheduled
    if 'dates' in json_source:
        for date in json_source['dates']:
            if 'games' in date:
                for game in date['games']:
                    if 'rescheduleDate' not in game:
                        epg = game['broadcasts']
                        break

    # define some default variables
    selected_content_id = None
    selected_media_state = None
    selected_call_letters = None
    #selected_media_type = None
    stream_url = ''
    broadcast_start_offset = '1' # offset to pass to inputstream adaptive
    broadcast_start_timestamp = None # to pass to skip monitor
    stream_type = 'video'
    skip_possible = True # to determine if possible to show skip options dialog
    skip_type = 0
    is_live = False # to pass to skip monitor
    # convert start inning values to integers
    if start_inning == 'False':
        start_inning = 0
    else:
        start_inning = int(start_inning)
    start_inning_half = 'top'
    if blackout != 'False' and blackout != 'True':
        utc=pytz.UTC
        now = utc.localize(datetime.now())
        blackout = parse(blackout)
    # define a dialog that we can use as needed
    dialog = xbmcgui.Dialog()

    # auto select stream if enabled and not bypassed with context menu item and it's not an archived suspended game, or if autoplay is forced
    # and if it's not blacked out or the blackout time has passed
    if ((AUTO_SELECT_STREAM == 'true' and from_context_menu is False and suspended != 'archive') or autoplay is True) and (blackout == 'False' or (blackout != 'True' and blackout < now)):
        # loop through the streams to determine the best match
        for item in epg:        
            # ignore streams that haven't started yet, audio streams, and in-market streams
            if item['mediaState']['mediaStateCode'] != 'MEDIA_OFF' and item['type'] == 'TV': # and not item['mediaFeedType'].startswith('IN_'):
                # check if our favorite team (if defined) is associated with this stream
                # or if no favorite team match, prefer the home or national streams
                #if (FAV_TEAM != 'None' and 'mediaFeedSubType' in item and item['mediaFeedSubType'] == getFavTeamId()) or (selected_content_id is None and 'mediaFeedType' in item and (item['mediaFeedType'] == 'HOME' or item['mediaFeedType'] == 'NATIONAL' )):
                if item['mediaId'] in entitled_feeds and item['mediaId'] not in blackout_feeds and ((FAV_TEAM != 'None' and ((item['homeAway'] == 'home' and str(json_source['dates'][0]['games'][0]['teams']['home']['team']['id']) == str(getFavTeamId())) or (item['homeAway'] == 'away' and str(json_source['dates'][0]['games'][0]['teams']['away']['team']['id']) == str(getFavTeamId())))) or (item['homeAway'] == 'home' or item['isNational'] == True ) or selected_content_id is None):
                    # prefer live streams (suspended games can have both a live and archived stream available)
                    if item['mediaState']['mediaStateCode'] == 'MEDIA_ON':
                        selected_content_id = item['mediaId']
                        selected_media_state = item['mediaState']['mediaStateCode']
                        selected_call_letters = item['callSign']
                        #if 'mediaFeedType' in item:
                        #    selected_media_type = item['mediaFeedType']
                        # once we've found a fav team live stream, we don't need to search any further
                        #if FAV_TEAM != 'None' and 'mediaFeedSubType' in item and item['mediaFeedSubType'] == getFavTeamId():
                        if FAV_TEAM != 'None' and ((item['homeAway'] == 'home' and str(json_source['dates'][0]['games'][0]['teams']['home']['team']['id']) == str(getFavTeamId())) or (item['homeAway'] == 'away' and str(json_source['dates'][0]['games'][0]['teams']['away']['team']['id']) == str(getFavTeamId()))):
                            break
                    # fall back to the first available archive stream, but keep search in case there is a live stream (suspended)
                    elif item['mediaState']['mediaStateCode'] == 'MEDIA_ARCHIVE' and selected_content_id is None:
                        selected_content_id = item['mediaId']
                        selected_media_state = item['mediaState']['mediaStateCode']
                        selected_call_letters = item['callSign']
                        #if 'mediaFeedType' in item:
                        #    selected_media_type = item['mediaFeedType']

    # if coming from the game changer, just return a flag to indicate whether we need to start an overlay
    if overlay_check == 'True':
        if HIDE_SCORES_TICKER == 'true' and stream_type == 'video' and selected_call_letters is not None and selected_call_letters.startswith(SCORES_TICKER_NETWORK):
            return True
        else:
            return False

    # fallback to manual stream selection if auto selection is disabled, bypassed, or didn't find anything, and we're not looking to force autoplay
    if selected_content_id is None and autoplay is False:
        # default stream selection list starts with highlights option
        stream_title = [LOCAL_STRING(30391)]
        highlight_offset = 1
        content_id = []
        media_state = []
        call_letters = []
        #media_type = []
        # if using Kodi's default resume ability, we'll omit highlights from our stream selection prompt
        if sys.argv[3] == 'resume:true':
            stream_title = []
            highlight_offset = 0

        # define some more variables used to handle suspended games
        airings = None
        game_date = None

        # # if no video, not live, if suspended, or if live and not resuming, add audio streams to the video streams
        # if len(json_source['media']['epg']) >= 3 and 'items' in json_source['media']['epg'][2] and (len(epg) == 0 or (epg[0]['mediaState'] != "MEDIA_ON" or suspended != 'False' or (epg[0]['mediaState'] == "MEDIA_ON" and sys.argv[3] != 'resume:true'))):
        #     epg += json_source['media']['epg'][2]['items']

        for item in epg:
            #xbmc.log(str(item))

            # only display if the stream is available (either live or archive) and not in_market
            if item['mediaState']['mediaStateCode'] != 'MEDIA_OFF':
                
                # broadcast title templates:
                # Away TV (BSSUN)
                # Home Radio (WFAN)
                # Away Spanish Radio (WQBN/1300)
                title = item['homeAway'].capitalize()
                # add TV to video stream
                if item['type'] == 'TV':
                    title += LOCAL_STRING(30392)
                # add language to audio stream
                else:
                    # assume English
                    #if item['language'] == 'en':
                    #    title += LOCAL_STRING(30394)
                    #el
                    if item['language'] == 'es':
                        title += LOCAL_STRING(30395)
                    title += LOCAL_STRING(30393)
                title = title + " (" + item['callSign'] + ")"

                # modify stream title based on suspension status, if necessary
                if suspended != 'False':
                    suspended_label = 'partial'
                    try:
                        # if the game hasn't finished, we can simply tell the status from the mediaState
                        if suspended == 'live' and item['mediaState']['mediaStateCode'] == 'MEDIA_ARCHIVE':
                            suspended_label = 'Suspended'
                        elif suspended == 'live':
                            suspended_label = 'Resumed'
                        # otherwise if the game is complete, we need to check the airings data
                        else:
                            if game_date is None and 'gameDate' in item:
                                game_date = item['gameDate']
                            if airings is None and game_date is not None:
                                airings = get_airings_data(game_pk=game_pk)
                            if game_date is not None and airings is not None and 'data' in airings and 'Airings' in airings['data']:
                                for airing in airings['data']['Airings']:
                                    if airing['contentId'] == item['mediaId']:
                                        # compare the start date of the airing with the provided game_date
                                        start_date = get_eastern_game_date(parse(airing['startDate']))
                                        # same day means it is resumed
                                        if game_date == start_date:
                                            suspended_label = 'Resumed'
                                        # different day means it was suspended
                                        else:
                                            suspended_label = 'Suspended'
                                        break
                    except:
                        pass
                    title += ' (' + suspended_label + ')'

                # display non-entitlement status for a stream, if applicable
                if blackout == 'True' or item['mediaId'] not in entitled_feeds:
                    title = blackoutString(title)
                    title += ' (not entitled)'
                # display blackout status for video, if available
                elif item['type'] == 'TV' and (blackout != 'False' or item['mediaId'] in blackout_feeds):
                    title = blackoutString(title)
                    title += ' (blackout until ~'
                    if blackout == 'True' or item['mediaId'] in blackout_feeds:
                        title += '2.5 hours after'
                    else:
                        blackout_display_time = get_display_time(UTCToLocal(blackout))
                        title += blackout_display_time
                    title += ')'

                # insert home/national video streams at the top of the list
                if item['type'] == 'TV' and (item['homeAway'] == 'home' or item['isNational'] == True):
                    content_id.insert(0, item['mediaId'])
                    media_state.insert(0, item['mediaState']['mediaStateCode'])
                    call_letters.insert(0, item['callSign'])
                    #media_type.insert(0, media_feed_type)
                    stream_title.insert(highlight_offset, title)
                # otherwise append other streams to end of list
                else:
                    content_id.append(item['mediaId'])
                    media_state.append(item['mediaState']['mediaStateCode'])
                    call_letters.append(item['callSign'])
                    #media_type.append(media_feed_type)
                    stream_title.append(title)

                # add an option to directly play live YouTube streams in YouTube add-on
                if 'youtube' in item and 'videoId' in item['youtube']:
                    content_id.insert(0, item['youtube']['videoId'])
                    media_state.insert(0, item['mediaState']['mediaStateCode'])
                    call_letters.insert(0, item['callSign'])
                    #media_type.insert(0, media_feed_type)
                    stream_title.insert(highlight_offset, LOCAL_STRING(30414))

        # if we didn't find any streams, display an error and exit
        if len(stream_title) == 0:
            dialog.notification(LOCAL_STRING(30383), LOCAL_STRING(30384), ICON, 5000, False)
            xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
            sys.exit()

        # stream selection dialog
        n = dialog.select(LOCAL_STRING(30390), stream_title)
        # highlights selection will go to that function and stop processing here
        if n == 0 and highlight_offset == 1:                        
            for game in json_source['dates']:                               
                if 'highlights' in game['games'][0]['content']:                    
                    highlight_select_stream(game['games'][0]['content']['highlights']['highlights']['items'], from_context_menu=from_context_menu)
                    break
        # stream selection
        elif n > -1 and stream_title[n] != LOCAL_STRING(30391):
            # check if selected stream is a radio stream
            if LOCAL_STRING(30393) in stream_title[n]:
                stream_type = 'audio'
            # directly play live YouTube streams in YouTube add-on, if requested
            if stream_title[n] == LOCAL_STRING(30414):
                xbmc.executebuiltin('RunPlugin("plugin://plugin.video.youtube/play/?video_id=' + content_id[n-highlight_offset] + '")')
                xbmcplugin.endOfDirectory(addon_handle)
            else:
                selected_content_id = content_id[n-highlight_offset]
                selected_media_state = media_state[n-highlight_offset]
                selected_call_letters = call_letters[n-highlight_offset]
                #selected_media_type = media_type[n-highlight_offset]
        # cancel will exit
        elif n == -1:
            sys.exit()

    # only proceed with start/skip dialogs if we have a content_id, either from auto-selection or the stream selection dialog
    if selected_content_id is not None:
        # need to log in to get the stream url and headers
        from .account import Account
        account = Account()
        stream_url, headers = account.get_stream(selected_content_id)

        if selected_media_state == 'MEDIA_ON':
            is_live = True

        if stream_type == 'audio':
            skip_possible = False

        # only show the start point dialog if not using Kodi's default resume ability, the "ask to catch up" option is enabled, no start inning is specified, and we're not looking to autoplay
        if sys.argv[3] != 'resume:true' and CATCH_UP == 'true' and start_inning == 0 and autoplay is False:

            # for live video streams
            if selected_media_state == "MEDIA_ON" and stream_type == 'video':
                # begin with catch up, beginning, and live as start point options
                start_options = [LOCAL_STRING(30397), LOCAL_STRING(30398), LOCAL_STRING(30399)]
                # add inning start options
                start_options += get_inning_start_options()

                # start point selection dialog
                p = dialog.select(LOCAL_STRING(30396), start_options)
                # catch up
                if p == 0:
                    if DISABLE_CLOSED_CAPTIONS == 'true' and not stream_url.startswith('http://127.0.0.1:43670/'):
                        stream_url = 'http://127.0.0.1:43670/' + stream_url
                    # create an item for the video stream
                    listitem = stream_to_listitem(stream_url, headers, description, name, icon, fanart)
                    # pass along the highlights and the video stream item to play as a playlist and stop processing here
                    highlight_select_stream(json_source['dates'][0]['games'][0]['content']['highlights']['highlights']['items'], catchup=listitem)
                    sys.exit()
                # beginning or inning
                elif p == 1 or p > 2:
                    # inning top/bottom calculation
                    if p > 2:
                        p = p - 2
                        start_inning, start_inning_half = calculate_inning_from_index(p)
                # live
                elif p == 2:
                    broadcast_start_offset = '-1'
                    skip_possible = False
                # cancel will exit
                elif p == -1:
                    sys.exit()

            # for live audio streams
            elif selected_media_state == "MEDIA_ON" and stream_type == 'audio':
                # start point selection dialog, with only catch up and live
                # omitting the beginning and inning start options (they don't work for live audio)
                p = dialog.select(LOCAL_STRING(30396), [LOCAL_STRING(30397), LOCAL_STRING(30399)])
                # catch up
                if p == 0:
                    # create an item for the audio stream
                    listitem = stream_to_listitem(stream_url, headers, description, name, icon, fanart, stream_type='audio', music_type_unset=True)
                    # pass along the highlights and the audio stream item to play as a playlist and stop processing here
                    highlight_select_stream(json_source['highlights']['highlights']['items'], catchup=listitem)
                    sys.exit()
                # cancel will exit
                elif p == -1:
                    sys.exit()

            # for archive video streams
            elif stream_type == 'video':
                # beginning is initial start point option
                start_options = [LOCAL_STRING(30398)]
                # add inning start options
                start_options += get_inning_start_options()
                # start point selection dialog
                p = dialog.select(LOCAL_STRING(30396), start_options)
                # inning
                if p > 0:
                    start_inning, start_inning_half = calculate_inning_from_index(p)
                # cancel will exit
                elif p == -1:
                    sys.exit()
        
        # join live and hide the skip dialog if not using Kodi's resume, we didn't show the catch up / start point dialog, the game is live and is already spoiled
        elif sys.argv[3] != 'resume:true' and is_live is True and spoiler == 'True':
        	broadcast_start_offset = '-1'
        	skip_possible = False
        
        # show automatic skip dialog, if possible, enabled, and we're not looking to autoplay
        if skip_possible is True and ASK_TO_SKIP == 'true' and autoplay is False:
            # automatic skip dialog with options to skip nothing, breaks, breaks + idle time, breaks + idle time + non-action pitches
            skip_type = dialog.select(LOCAL_STRING(30403), [LOCAL_STRING(30404), LOCAL_STRING(30423), LOCAL_STRING(30408), LOCAL_STRING(30405), LOCAL_STRING(30421), LOCAL_STRING(30406)])
            # cancel will exit
            if skip_type == -1:
                sys.exit()
                            
        # get the broadcast_start_timestamp if we are starting at an inning or skipping
        if skip_type > 0 or start_inning > 0:
            broadcast_start_timestamp = account.get_broadcast_start_time(stream_url)

        # if autoplay, join live
        if autoplay is True:
            broadcast_start_offset = '-1'
        # if not live and no spoilers and not audio, generate a random number of segments to pad at end of proxy stream url
        elif DISABLE_VIDEO_PADDING == 'false' and is_live is False and spoiler == 'False' and stream_type != 'audio':
            pad = random.randint((3600 // SECONDS_PER_SEGMENT), (7200 // SECONDS_PER_SEGMENT))
            # pass padding as URL querystring parameter
            stream_url = 'http://127.0.0.1:43670/' + stream_url + '?pad=' + str(pad)

        # valid stream url
        if '.m3u8' in stream_url:
            if DISABLE_CLOSED_CAPTIONS == 'true' and not stream_url.startswith('http://127.0.0.1:43670/'):
                stream_url = 'http://127.0.0.1:43670/' + stream_url
            
            play_stream(stream_url, headers, description, title=name, icon=icon, fanart=fanart, start=broadcast_start_offset, stream_type=stream_type, music_type_unset=from_context_menu)

            # start the monitor if a skip type or start inning has been requested and we have a broadcast start timestamp
            # or if an overlay is required (overlay enabled for a Bally video stream)
            # or if we want to disable captions
            if gamechanger == 'False' and stream_type == 'video' and (((skip_type > 0 or start_inning > 0) and broadcast_start_timestamp is not None) or (HIDE_SCORES_TICKER == 'true' and selected_call_letters.startswith(SCORES_TICKER_NETWORK)) or DISABLE_CLOSED_CAPTIONS == 'true'):
                from .mlbmonitor import MLBMonitor
                mlbmonitor = MLBMonitor()

                # wait for stream start to be detected before proceeding
                if mlbmonitor.wait_for_stream(game_pk) is True:

                    if (HIDE_SCORES_TICKER == 'true' and selected_call_letters.startswith(SCORES_TICKER_NETWORK)) or DISABLE_CLOSED_CAPTIONS == 'true':
                        # wait an extra second
                        xbmc.sleep(1000)

                        if HIDE_SCORES_TICKER == 'true' and selected_call_letters.startswith(SCORES_TICKER_NETWORK):
                            mlbmonitor.start_overlay(game_pk)

                        if DISABLE_CLOSED_CAPTIONS == 'true':
                            mlbmonitor.stop_captions(game_pk)

                    # call the game monitor for skips and/or to stop the overlay
                    if ((skip_type > 0 or start_inning > 0) and broadcast_start_timestamp is not None) or (HIDE_SCORES_TICKER == 'true' and selected_call_letters.startswith(SCORES_TICKER_NETWORK)):
                        mlbmonitor.game_monitor(skip_type, game_pk, broadcast_start_timestamp, stream_url, is_live, start_inning, start_inning_half)

        # otherwise exit
        else:
            sys.exit()


# select a stream for a featured video
def featured_stream_select(featured_video, name, description, start_inning=None, game_pk=None):
    xbmc.log('video select')

    start = '-1' # offset to pass to inputstream adaptive
    broadcast_start_timestamp = None # to pass to skip monitor
    skip_possible = True # to determine if possible to show skip options dialog
    skip_type = 0
    is_live = False # to pass to skip monitor
    # convert start inning values to integers
    if start_inning == 'False':
        start_inning = 0
    else:
        start_inning = int(start_inning)
    start_inning_half = 'top'

    # define a dialog that we can use as needed
    dialog = xbmcgui.Dialog()

    video_url = None
    # check if our request video is a URL
    if featured_video.startswith('http'):
        video_url = featured_video
    # otherwise assume it is a video title (used to call Big Inning from the schedule)
    else:
        xbmc.log('must search for video url with title')
        #video_list = get_video_list('https://dapi.mlbinfra.com/v2/content/en-us/vsmcontents/mlb-tv-welcome-center-big-inning-show')
        video_list = get_video_list('https://dapi.cms.mlbinfra.com/v2/content/en-us/sel-mlbtv-featured-svod-video-list')
        eventList = None
        if 'items' in video_list:
            eventList = video_list['items']
        elif 'references' in video_list and 'video' in video_list['references']:
            eventList = video_list['references']['video']

        if eventList is not None:
            for item in eventList:
                #xbmc.log(str(item))
                # live Big Inning title should start with LIVE and contain Big Inning
                if (featured_video == (LOCAL_STRING(30367) + LOCAL_STRING(30368)) and item['title'].startswith('LIVE') and 'Big Inning' in item['title']) or featured_video == item['title']:
                    xbmc.log('found match')
                    video_url = None
                    if 'fields' in item:
                        if 'playbackScenarios' in item['fields']:
                            for playback in item['fields']['playbackScenarios']:
                                if playback['playback'] == 'hlsCloud':
                                    video_url = playback['location']
                                    break
                        elif 'url' in item['fields']:
                            video_url = item['fields']['url']
    if video_url is None:
        xbmc.log('failed to find video URL for featured video')
        sys.exit()

    xbmc.log('video url : ' + video_url)
    video_stream_url = None
    from .account import Account
    account = Account()
    # if it's not a Big Inning stream and it is HLS (M3U8) or MP4, we can simply stream the URL we already have
    if (not name.startswith('LIVE') or (name.startswith('LIVE') and 'Big Inning' not in name)) and (video_url.endswith('.m3u8') or video_url.endswith('.mp4')):
        video_stream_url = video_url
    # otherwise we need to authenticate and get the stream URL
    else:
        video_stream_url = account.get_event_stream(video_url)

    if video_stream_url is not None:
        # add start / skip menus for MiLB games
        if game_pk is not None:
            # get broadcast start timestamp from M3U
            broadcast_start_timestamp, is_live = get_broadcast_start_timestamp(video_stream_url)

            # only show the start point dialog if not using Kodi's default resume ability, the "ask to catch up" option is enabled, no start inning is specified
            if sys.argv[3] != 'resume:true' and CATCH_UP == 'true' and start_inning == 0:

                # begin with beginning as start point options
                start_options = [LOCAL_STRING(30398)]
                # add live start option, if applicable
                live_offset = 0
                if is_live is True:
                    live_offset = 1
                    start_options += [LOCAL_STRING(30399)]
                # add inning start options
                start_options += get_inning_start_options()

                # start point selection dialog
                p = dialog.select(LOCAL_STRING(30396), start_options)

                # beginning or inning
                if p == 0 or p > live_offset:
                    start = '1'
                    # inning top/bottom calculation
                    if p > live_offset:
                        p = p - live_offset
                        start_inning, start_inning_half = calculate_inning_from_index(p)
                # live
                elif p == 1:
                    broadcast_start_offset = '-1'
                    skip_possible = False
                # cancel will exit
                elif p == -1:
                    sys.exit()

            # show automatic skip dialog, if possible and enabled
            if skip_possible is True and ASK_TO_SKIP == 'true':
                # automatic skip dialog with options to skip nothing, breaks, breaks + idle time, breaks + idle time + non-action pitches
                skip_type = dialog.select(LOCAL_STRING(30403), [LOCAL_STRING(30404), LOCAL_STRING(30408), LOCAL_STRING(30405), LOCAL_STRING(30421), LOCAL_STRING(30406)])
                # cancel will exit
                if skip_type == -1:
                    sys.exit()
                elif skip_type > 1:
                    skip_type += 1


        headers = 'User-Agent=' + UA_PC
        if '.m3u8' in video_stream_url and QUALITY == 'Always Ask':
            video_stream_url = account.get_stream_quality(video_stream_url)
        # known issue warning: on Kodi 18 Leia WITHOUT inputstream adaptive, Big Inning starts at the beginning and can't seek
        # anyone with inputstream adaptive, or Kodi 19+, will not have this problem
        if name.startswith('LIVE') and 'Big Inning' in name and KODI_VERSION < 19 and not xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):
            dialog.ok(LOCAL_STRING(30370), LOCAL_STRING(30369))
        play_stream(video_stream_url, headers, description, title=name, start=start)

        # start the skip monitor if MiLB game and a skip type or start inning has been requested and we have a broadcast start timestamp
        if game_pk is not None and (skip_type > 0 or start_inning > 0) and broadcast_start_timestamp is not None:
            from .mlbmonitor import MLBMonitor
            mlbmonitor = MLBMonitor()
            mlbmonitor.game_monitor(skip_type, game_pk, broadcast_start_timestamp, video_stream_url, is_live, start_inning, start_inning_half, True)
    else:
        xbmc.log('unable to find stream for featured video')


# select a stream for a linear channel
def linear_channel_stream_select(featured_video, name, description):
    xbmc.log('linear channel select')

    start = '-1' # offset to pass to inputstream adaptive

    from .account import Account
    account = Account()
    video_stream_url = account.get_linear_stream(featured_video)
    xbmc.log('video url : ' + video_stream_url)
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'identity',
        'accept-language': 'en-US,en;q=0.5',
        'connection': 'keep-alive'
    }
    play_stream(video_stream_url, headers, description, name)


def list_highlights(game_pk, icon, fanart):
    url = API_URL + '/api/v1/game/' + game_pk + '/content'
    headers = {
        'User-Agent': UA_ANDROID
    }
    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    if 'highlights' in json_source and 'highlights' in json_source['highlights'] and 'items' in json_source['highlights']['highlights'] and len(json_source['highlights']['highlights']['items']) > 0:
        highlights = get_highlights(json_source['highlights']['highlights']['items'])
        if not highlights:
            msg = LOCAL_STRING(30383)
            dialog = xbmcgui.Dialog()
            dialog.notification(LOCAL_STRING(30391), msg, ICON, 5000, False)
            xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
            sys.exit()

        # play all
        liz=xbmcgui.ListItem(LOCAL_STRING(30411))
        liz.setInfo( type="Video", infoLabels={ "Title": LOCAL_STRING(30411), "plot": LOCAL_STRING(30411) } )
        if icon is None: icon = ICON
        if fanart is None: fanart = FANART
        liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
        liz.setProperty("IsPlayable", "true")
        u=sys.argv[0]+"?mode="+str(107)+"&game_pk="+urllib.quote_plus(str(game_pk))+"&fanart="+urllib.quote_plus(fanart)
        isFolder=False

        xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=isFolder)
        xbmcplugin.setContent(addon_handle, 'episodes')

        for clip in highlights:
            liz=xbmcgui.ListItem(clip['title'])
            liz.setInfo( type="Video", infoLabels={ "Title": clip['title'], "plot": clip['description'] } )
            liz.setArt({'icon': icon, 'thumb': clip['icon'], 'fanart': fanart})
            liz.setProperty("IsPlayable", "true")
            u=sys.argv[0]+"?mode="+str(301)+"&featured_video="+urllib.quote_plus(clip['url'])+"&name="+urllib.quote_plus(clip['title'])+"&description="+urllib.quote_plus(clip['description'])
            isFolder=False

            xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=isFolder)
            xbmcplugin.setContent(addon_handle, 'episodes')


def play_all_highlights_for_game(game_pk, fanart):
    url = API_URL + '/api/v1/game/' + game_pk + '/content'
    headers = {
        'User-Agent': UA_ANDROID
    }
    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    if 'highlights' in json_source and 'highlights' in json_source['highlights'] and 'items' in json_source['highlights']['highlights'] and len(json_source['highlights']['highlights']['items']) > 0:
        highlights = get_highlights(json_source['highlights']['highlights']['items'])
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        for clip in highlights:
            # Play All should only include game action tracking, non-analysis, non-reel highlights
            if clip['game_action_tracking'] is True and clip['analysis'] is False and clip['highlight_reel'] is False:
                listitem = xbmcgui.ListItem(clip['url'])
                listitem.setArt({'icon': clip['icon'], 'thumb': clip['icon'], 'fanart': fanart})
                listitem.setInfo(type="Video", infoLabels={"Title": clip['title'], "plot": clip['description']})
                playlist.add(clip['url'], listitem)

        xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=playlist[0])


def highlight_select_stream(json_source, catchup=None, from_context_menu=False):
    highlights = get_highlights(json_source)
    if not highlights and catchup is None:
        msg = LOCAL_STRING(30383)
        dialog = xbmcgui.Dialog()
        dialog.notification(LOCAL_STRING(30391), msg, ICON, 5000, False)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
        sys.exit()

    highlight_name = []
    highlight_url = []
    highlight_description = []
    if from_context_menu is False:
        highlight_name.append(LOCAL_STRING(30411))
        highlight_url.append('blank')
        highlight_description.append(LOCAL_STRING(30411))

    for clip in highlights:
        highlight_name.append(clip['title'])
        highlight_url.append(clip['url'])
        highlight_description.append(clip['description'])

    if catchup is None:
        dialog = xbmcgui.Dialog()
        a = dialog.select('Choose Highlight', highlight_name)
    else:
        a = 0

    if a > 0:
        headers = 'User-Agent=' + UA_PC
        play_stream(highlight_url[a], headers, highlight_description[a], highlight_name[a])
    elif a == 0:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        for clip in highlights:
            # Catch Up should only include game action tracking, non-analysis, non-reel highlights
            if clip['game_action_tracking'] is True and clip['analysis'] is False and clip['highlight_reel'] is False:
                listitem = xbmcgui.ListItem(clip['url'])
                listitem.setArt({'icon': clip['icon'], 'thumb': clip['icon'], 'fanart': FANART})
                listitem.setInfo(type="Video", infoLabels={"Title": clip['title'], "plot": clip["description"]})
                playlist.add(clip['url'], listitem)

        if catchup is not None:
            playlist.add(catchup.getPath(), catchup)

        xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=playlist[0])
    elif a == -1:
        sys.exit()


def play_stream(stream_url, headers, description, title, icon=None, fanart=None, start='1', stream_type='video', music_type_unset=False):
    listitem = stream_to_listitem(stream_url, headers, description, title, icon, fanart, start=start, stream_type=stream_type, music_type_unset=music_type_unset)
    xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=listitem)


def get_highlights(items):
    xbmc.log(str(items))
    highlights = []
    for item in sorted(items, key=lambda x: x['date']):
        # label game action tracking, analysis, and highlight reels for filtering under Play All / Catch Up
        game_action_tracking = False
        analysis = False
        highlight_reel = False
        for keyword in item['keywordsAll']:
            if keyword['displayName'] == 'game action tracking':
                game_action_tracking = True
            elif keyword['displayName'] == 'analysis':
                analysis = True
            elif keyword['displayName'].startswith('highlight reel'):
                highlight_reel = True

        for playback in item['playbacks']:
            if 'mp4Avc' in playback['name']:
                clip_url = playback['url']
                break
        headline = item['headline']
        icon = item['image']['cuts'][0]['src']
        description = item['blurb']
        highlights.append({'url': clip_url, 'title': headline, 'icon': icon, 'description': description, 'game_action_tracking': game_action_tracking, 'analysis': analysis, 'highlight_reel': highlight_reel})

    return highlights


# Play all recaps or condensed games when a date is selected
def playAllHighlights(stream_date):
    dialog = xbmcgui.Dialog()
    n = dialog.select(LOCAL_STRING(30400), [LOCAL_STRING(30401), LOCAL_STRING(30402)])
    if n == -1:
        sys.exit()

    url = API_URL + '/api/v1/schedule'
    url += '?hydrate=game(content(highlights(highlights)))'
    url += '&sportId=1,51'
    url += '&date=' + stream_date

    headers = {
        'User-Agent': UA_ANDROID
    }
    r = requests.get(url, headers, verify=VERIFY)
    json_source = r.json()

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()

    for game in json_source['dates'][0]['games']:
        try:
            fanart = 'http://cd-images.mlbstatic.com/stadium-backgrounds/color/light-theme/1920x1080/%s.png' % game['venue']['id']
            if 'highlights' in game['content']:
                for item in game['content']['highlights']['highlights']['items']:
                    try:
                        title = item['headline'].strip().lower()
                        if (n == 0 and (' vs ' in title or ' vs. ' in title or ' versus ' in title or ' at ' in title or '@' in title) and (title.endswith(' highlights') or title.endswith(' recap'))) or (n == 1 and 'condensed' in title):
                            for playback in item['playbacks']:
                                if 'hlsCloud' in playback['name']:
                                    clip_url = playback['url']
                                    break
                            listitem = xbmcgui.ListItem(item['headline'])
                            icon = item['image']['cuts'][0]['src']
                            listitem.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
                            listitem.setInfo(type="Video", infoLabels={"Title": item['headline']})
                            xbmc.log('adding recap to playlist : ' + item['headline'])
                            playlist.add(clip_url, listitem)
                            break
                    except:
                        pass
        except:
            pass

    xbmc.Player().play(playlist)


# get the airings data, which contains the start time of the broadcast(s)
def get_airings_data(content_id=None, game_pk=None):
    xbmc.log('Get airings data')
    url = 'https://search-api-mlbtv.mlb.com/svc/search/v2/graphql/persisted/query/core/Airings'
    headers = {
        'Accept': 'application/json',
        'X-BAMSDK-Version': '4.3',
        'X-BAMSDK-Platform': 'macintosh',
        'User-Agent': UA_PC,
        'Origin': 'https://www.mlb.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-type': 'application/json'
    }
    if content_id is not None:
        data = {
            'variables': '%7B%22contentId%22%3A%22' + content_id + '%22%7D'
        }
    else:
        data = {
            'variables': '{%22partnerProgramIds%22%3A[%22' + str(game_pk) + '%22]}'
        }
    r = requests.get(url, headers=headers, params=data, verify=VERIFY)
    json_source = r.json()

    return json_source


# get nonentitlement data for a date
def get_nonentitlement_data(game_date):
    nonentitlement_data = {}
    
    from .account import Account
    account = Account()
    login_token = account.login_token()
    okta_id = account.okta_id()
    
    url = 'https://mastapi.mobile.mlbinfra.com/api/epg/v3/search?exp=MLB&date=' + game_date
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://www.mlb.com', 
        'pragma': 'no-cache',
        'priority': 'u=1, i', 
        'referer': 'https://www.mlb.com/', 
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"', 
        'sec-ch-ua-mobile': '?0', 
        'sec-ch-ua-platform': '"macOS"', 
        'sec-fetch-dest': 'empty', 
        'sec-fetch-mode': 'cors', 
        'sec-fetch-site': 'same-site', 
        'user-agent': UA_PC
    }
    if login_token is not None and okta_id is not None:
        headers['authorization'] = 'Bearer ' + login_token
        headers['x-okta-id'] = okta_id
    r = requests.get(url,headers=headers, verify=VERIFY)
    json_source = r.json()

    games = []
    if 'results' in json_source and len(json_source['results']) > 0:
        for game in json_source['results']:
            if game['entitledVideo'] == False:
                nonentitlement_data[game['gamePk']] = ''
            elif game['blackedOutVideo'] == True:
                blackout_wait_minutes = 150
                innings = max(game['gameData']['scheduledInnings'], game['gameData']['currentInning'])
                # avg 9 inning game was 2:36 in 2024, or 17.33 minutes per inning
                gameDurationMinutes = 17.33 * innings
                # default to assuming the scheduled game time is the first pitch time
                firstPitch = parse(game['gameData']['gameDate'])
                gameDurationMinutes += blackout_wait_minutes
                blackout_time = firstPitch + timedelta(minutes=gameDurationMinutes)
                nonentitlement_data[game['gamePk']] = blackout_time
                            
    return nonentitlement_data


def get_scheduled_innings(game):
    scheduled_innings = 9
    if 'linescore' in game:
        if 'scheduledInnings' in game['linescore']:
            scheduled_innings = int(game['linescore']['scheduledInnings'])
        if 'currentInning' in game['linescore']:
            if game['status']['abstractGameState'] == 'Final' and int(game['linescore']['currentInning']) < 9:
                scheduled_innings = int(game['linescore']['currentInning'])
    return scheduled_innings


def get_current_inning(game):
    current_inning = 1
    if 'linescore' in game:
        if 'currentInning' in game['linescore']:
            current_inning = int(game['linescore']['currentInning'])
    return current_inning


def live_fav_game():
    game_day = localToEastern()

    auto_play_game_date = str(settings.getSetting(id='auto_play_game_date'))

    game_pk = None

    fav_team_id = getFavTeamId()

    # don't check if don't have a fav team id or if we've already flagged today's fav games as complete
    if fav_team_id is not None and auto_play_game_date != game_day:
        now = datetime.now()
        # don't check if it is before the stored next game time (if available)
        auto_play_next_game = str(settings.getSetting(id='auto_play_next_game'))
        if auto_play_next_game == '' or UTCToLocal(parse(auto_play_next_game)) <= now:
            # don't check more often than 5 minute intervals
            auto_play_game_checked = str(settings.getSetting(id='auto_play_game_checked'))
            if auto_play_game_checked == '' or (parse(auto_play_game_checked) + timedelta(minutes=5)) < now:
                settings.setSetting(id='auto_play_game_checked', value=str(now))

                url = API_URL + '/api/v1/schedule'
                url += '?hydrate=broadcasts'
                url += '&sportId=1,51'
                url += '&date=' + game_day
                url += '&teamId=' + fav_team_id

                headers = {
                    'User-Agent': UA_PC
                }
                r = requests.get(url,headers=headers, verify=VERIFY)
                json_source = r.json()

                upcoming_game = False

                if 'dates' in json_source and len(json_source['dates']) > 0 and 'games' in json_source['dates'][0]:
                    games = json_source['dates'][0]['games']
                    nonentitlement_data = get_nonentitlement_data(game_day)
                    found = False
                    for game in games:
                        try:
                            # only check games that include our fav team
                            if fav_team_id in [str(game['teams']['home']['team']['id']), str(game['teams']['away']['team']['id'])]:
                                # only check games that aren't final
                                if game['status']['abstractGameState'] != 'Final':
                                    # only check games that are entitled and not blacked out
                                    if str(game['gamePk']) not in nonentitlement_data:
                                        mediaStateCode = None
                                        for broadcast in game.get('broadcasts', []):
                                            mediaStateCode = broadcast.get('mediaState', {}).get('mediaStateCode', '')
                                            if mediaStateCode:
                                                # if media is off, assume it is still upcoming
                                                if mediaStateCode == 'MEDIA_OFF':
                                                    if game['status']['startTimeTBD'] is True:
                                                        upcoming_game = 'TBD'
                                                    else:
                                                        upcoming_game = parse(game['gameDate']) - timedelta(minutes=10)
                                                    found = True
                                                # if media is on, that means it is live
                                                elif game_pk is None and mediaStateCode == 'MEDIA_ON':
                                                    game_pk = str(game['gamePk'])
                                                    xbmc.log('Found live fav game ' + game_pk)
                                                    found = True
                                            if found:
                                                break  # broadcast loop
                            if found:
                                break  # game loop
                        except:
                            pass

                # set the date setting if there are no more upcoming fav games today
                if upcoming_game is False:
                    xbmc.log('No more upcoming fav games today')
                    settings.setSetting(id='auto_play_game_date', value=game_day)
                # otherwise store the time of the next game, and delay further checks until then
                elif game_pk is None and upcoming_game != 'TBD':
                    xbmc.log('Setting next game time')
                    settings.setSetting(id='auto_play_next_game', value=str(upcoming_game))

    return game_pk
