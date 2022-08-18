# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for MiLB.TV compatibility and code cleanup

from resources.lib.globals import *
from .account import Account
from .milbmonitor import MILBMonitor


def categories():
    addDir(LOCAL_STRING(30360), 100)
    addDir(LOCAL_STRING(30361), 105)
    # see yesterday's scores at inning in the main menu
    addDir(LOCAL_STRING(30424), 108)
    addDir(LOCAL_STRING(30362), 200)


def levels(game_day, start_inning):
    if FAV_TEAM != 'None':
        addDir(FAV_TEAM + LOCAL_STRING(30368), 18, game_day, start_inning, ALL_LEVELS, AFFILIATES[FAV_TEAM])
    addDir(LOCAL_STRING(30363), 11, game_day, start_inning)
    addDir(LOCAL_STRING(30364), 12, game_day, start_inning)
    addDir(LOCAL_STRING(30365), 13, game_day, start_inning)
    addDir(LOCAL_STRING(30366), 14, game_day, start_inning)
    addDir(LOCAL_STRING(30367), 17, game_day, start_inning)


def todays_games(game_day, start_inning, level, teams=None):
    if game_day is None:
        game_day = localToEastern()

    display_day = stringToDate(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)

    addDir('[B]<< %s[/B]' % LOCAL_STRING(30010), 101, prev_day.strftime("%Y-%m-%d"), start_inning, level, teams)

    date_display = '[B][I]' + colorString(display_day.strftime("%A, %m/%d/%Y"), GAMETIME_COLOR) + '[/I][/B]'

    addDir(date_display, 100, game_day, start_inning, level, teams)

    url = API_URL + '/api/v1/schedule'
    url += '?hydrate=broadcasts(all),probablePitcher,linescore,team,flags'
    url += '&sportId=' + str(level)
    url += '&date=' + game_day
    if teams is not None:
        url += '&teamId=' + teams
    #xbmc.log('Schedule URL ' + url)

    headers = {
        'User-Agent': UA_PC
    }
    r = requests.get(url,headers=headers, verify=VERIFY)
    json_source = r.json()

    try:
        if 'dates' in json_source and len(json_source['dates']) > 0 and 'games' in json_source['dates'][0]:
            for game in json_source['dates'][0]['games']:
                milb_broadcast = None
                if 'broadcasts' in game:
                    for broadcast in game['broadcasts']:
                        if broadcast['name'] == 'MiLB.TV':
                            milb_broadcast = broadcast
                            break
                if milb_broadcast is not None:
                    create_game_listitem(game, game_day, start_inning, milb_broadcast)
    except:
       pass


    next_day = display_day + timedelta(days=1)
    addDir('[B]%s >>[/B]' % LOCAL_STRING(30011), 101, next_day.strftime("%Y-%m-%d"), start_inning, level, teams)


def create_game_listitem(game, game_day, start_inning, broadcast):
    level_abbr = game['teams']['home']['team']['sport']['name']
    if level_abbr[0] == 'T':
        level_abbr = 'AAA'
    elif level_abbr[0] == 'D':
        level_abbr = 'AA'
    elif level_abbr[0] == 'H':
        level_abbr = 'A+'
    elif level_abbr[0] == 'S':
        level_abbr = 'A'

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

    title = level_abbr + ': ' + away_team + ' at ' + home_team

    fav_game = False
    icon_id = game['teams']['home']['team']['id']
    if away_org in FAV_TEAM:
        fav_game = True
        away_team = colorString(away_team, FAV_TEAM_COLOR)
        icon_id = game['teams']['away']['team']['id']

    if home_org in FAV_TEAM:
        fav_game = True
        home_team = colorString(home_team, FAV_TEAM_COLOR)

    icon = 'https://www.mlbstatic.com/team-logos/share/' + str(icon_id) + '.jpg'
    if 'venue' in game and 'id' in game['venue']:
        fanart = 'http://cd-images.mlbstatic.com/stadium-backgrounds/color/light-theme/1920x1080/%s.png' % game['venue']['id']
    else:
        fanart = FANART

    game_time = ''
    suspended = 'False'
    display_time = 'TBD'
    relative_inning = None
    spoiler = 'True'
    today = localToEastern()
    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) or (NO_SPOILERS == '3' and game_day == today) or (NO_SPOILERS == '4' and game_day < today):
        spoiler = 'False'

    if 'gameDate' in game:
        display_time = stringToDate(game['gameDate'], "%Y-%m-%dT%H:%M:%SZ")
        display_time = UTCToLocal(display_time)

        if TIME_FORMAT == '0':
            display_time = display_time.strftime('%I:%M %p').lstrip('0')
        else:
            display_time = display_time.strftime('%H:%M')

    scheduled_innings = 9
    if 'linescore' in game and 'scheduledInnings' in game['linescore']:
        scheduled_innings = int(game['linescore']['scheduledInnings'])

    #if game['status']['abstractGameState'] == 'Preview':
    if game['status']['detailedState'].lower() == 'scheduled' or game['status']['detailedState'].lower() == 'pre-game':
        if game['status']['startTimeTBD'] is True:
            game_time = 'TBD'
        else:
            game_time = display_time

        game_time = colorString(game_time, UPCOMING)

    else:
        #game_time = game['status']['abstractGameState']
        game_state = game['status']['detailedState']
        game_time = game_state

        if game_state != 'Postponed':
            # if we've requested to see scores at a particular inning
            if start_inning != 'False' and 'linescore' in game:
                relative_inning = (int(start_inning) - (9 - scheduled_innings))
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

                if game['linescore']['currentInning'] >= scheduled_innings and spoiler == 'False':
                    game_time = str(scheduled_innings) + 'th+'
                else:
                    game_time = top_bottom + ' ' + game['linescore']['currentInningOrdinal']

            try:
                if 'resumeGameDate' in game or 'resumedFromDate' in game:
                    suspended = 'True'
                    if 'resumeGameDate' in game:
                        game_time += ' (Suspended)'
                    elif 'resumedFromDate' in game:
                        game_time = display_time + ' ' + game_time + ' (Resumed)'
            except:
                pass

        if game_state == 'Final' or game_state == 'Postponed':
            game_time = colorString(game_time, FINAL)

        elif game['status']['abstractGameState'] == 'Live':
            if 'linescore' in game and game['linescore']['currentInning'] >= scheduled_innings:
                color = CRITICAL
            else:
                color = LIVE

            game_time = colorString(game_time, color)

        else:
            game_time = colorString(game_time, LIVE)

    game_pk = game['gamePk']

    desc = game['teams']['home']['team']['sport']['name'] + ' ' + game['teams']['home']['team']['league']['name'] + '[CR]' + game['teams']['away']['team']['name'] + ' at ' + game['teams']['home']['team']['name']
    probables = ''
    if ('probablePitcher' in game['teams']['away'] and 'fullName' in game['teams']['away']['probablePitcher']) or ('probablePitcher' in game['teams']['home'] and 'fullName' in game['teams']['home']['probablePitcher']):
        desc += '[CR]'
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
        probables = colorString(probables, FINAL)

    if 'venue' in game and 'name' in game['venue']:
        desc += '[CR]From ' + game['venue']['name']

    if 'description' in game and game['description'] != "":
        desc += '[CR]' + game['description']

    name = game_time  + ' ' + level_abbr + ': ' + away_team
    if game['status']['abstractGameState'] == 'Preview' or (start_inning == 'False' and spoiler == 'False'):
        name += ' at ' + home_team
    else:
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

        name += away_score + ' at ' + home_team + home_score

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

    name += probables
    if scheduled_innings != 9:
        desc += '[CR]' + str(scheduled_innings) + '-inning game'

    if fav_game:
        name = '[B]' + name + '[/B]'

    resolution = 'HD'
    # Set audio/video info based on stream quality setting
    if 'videoResolution' in broadcast:
        resolution = broadcast['videoResolution']['resolutionShort']

    audio_info, video_info = getAudioVideoInfo(resolution)

    info = {'plot': desc, 'tvshowtitle': 'MiLB', 'title': title, 'originaltitle': title, 'aired': game_day, 'genre': LOCAL_STRING(700), 'mediatype': 'video'}

    status = game['status']['abstractGameState']

    add_stream(name, title, game_pk, icon, fanart, info, video_info, audio_info, spoiler, suspended, start_inning, status)


def stream_select(game_pk, spoiler, suspended, start_inning, status):
    stream_url = ''
    start = '-1' # offset to pass to inputstream adaptive
    broadcast_start_timestamp = None # to pass to skip monitor
    skip_possible = True # to determine if possible to show skip options dialog
    skip_type = 0
    skip_adjust = 0
    is_live = False # to pass to skip monitor
    # convert start inning values to integers
    if start_inning == 'False':
        start_inning = 0
    else:
        start_inning = int(start_inning)
    start_inning_half = 'top'
    # define a dialog that we can use as needed
    dialog = xbmcgui.Dialog()

    if status == 'Live':
        is_live = True

    if status != 'Live' and status != 'Final':
        msg = LOCAL_STRING(30414)
        dialog.notification(LOCAL_STRING(30415), msg, ICON, 5000, False)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
        sys.exit()
    else:
        account = Account()
        stream_url, headers = account.get_stream(game_pk)

        # only show the start point dialog if not using Kodi's default resume ability, the "ask to catch up" option is enabled, we don't already have a start inning, and it's not a suspended/resumed game
        if sys.argv[3] != 'resume:true' and CATCH_UP == 'true' and start_inning == 0 and suspended == 'False':
            # beginning as start point options
            start_options = [LOCAL_STRING(30426)]
            live_offset = 0
            if is_live == True:
                start_options.append(LOCAL_STRING(30427))
                live_offset = 1
            # add inning start options
            start_options += get_inning_start_options()

            # start point selection dialog
            p = dialog.select(LOCAL_STRING(30425), start_options)
            # beginning or inning
            if p == 0 or p > live_offset:
                start = '1'
                if p > live_offset:
                    # inning top/bottom calculation
                    p = p - live_offset
                    start_inning, start_inning_half = calculate_inning_from_index(p)
                else:
                    start_inning = 1
            # live
            elif p == live_offset:
                skip_possible = False
            # cancel will exit
            elif p == -1:
                sys.exit()

        # show automatic skip dialog, if enabled and it's not a suspended/resumed game
        if ASK_TO_SKIP == 'true' and skip_possible == True and suspended == 'False':
            # get broadcast start timestamp from M3U
            broadcast_start_timestamp = get_broadcast_start_timestamp(stream_url)

            if broadcast_start_timestamp is not None:
                # automatic skip dialog with options to skip nothing, breaks, breaks + idle time, breaks + idle time + non-action pitches
                skip_type = dialog.select(LOCAL_STRING(30416), [LOCAL_STRING(30417), LOCAL_STRING(30418), LOCAL_STRING(30419), LOCAL_STRING(30420)])
                # cancel will exit
                if skip_type == -1:
                    sys.exit()
                elif skip_type > 0:
                    # skip adjust dialog
                    skip_adjust_options = ['-15', '-10', '-5', '0', '5', '10', '15']
                    p = dialog.select(LOCAL_STRING(30428), skip_adjust_options)
                    # cancel will exit
                    if p == -1:
                        sys.exit()
                    else:
                        skip_adjust = int(skip_adjust_options[p])

        if DISABLE_VIDEO_PADDING == 'false' and is_live is False and spoiler == 'False':
            pad = random.randint((3600 / SECONDS_PER_SEGMENT), (7200 / SECONDS_PER_SEGMENT))
            headers += '&pad=' + str(pad)
            stream_url = 'http://127.0.0.1:43671/' + stream_url

        if '.m3u8' in stream_url:
            play_stream(stream_url, headers, start)
            # start the skip monitor if a skip type or start inning has been requested and we have a broadcast start timestamp
            if (skip_type > 0 or start_inning > 0) and broadcast_start_timestamp is not None and suspended == 'False':
                milbmonitor = MILBMonitor()
                milbmonitor.skip_monitor(skip_type, game_pk, broadcast_start_timestamp, skip_adjust, is_live, start_inning, start_inning_half)
        else:
            sys.exit()


def play_stream(stream_url, headers, start):
    listitem = stream_to_listitem(stream_url, headers, start)
    xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=listitem)

