# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for MiLB.TV compatibility and code cleanup

from resources.lib.globals import *
from .account import Account


def categories():
    addDir(LOCAL_STRING(30360), 100, ICON, FANART)
    addDir(LOCAL_STRING(30361), 105, ICON, FANART)
    addDir(LOCAL_STRING(30362), 200, ICON, FANART)


def levels(game_day):
    addDir(LOCAL_STRING(30363), 11, ICON, FANART, game_day)
    addDir(LOCAL_STRING(30364), 12, ICON, FANART, game_day)
    addDir(LOCAL_STRING(30365), 13, ICON, FANART, game_day)
    addDir(LOCAL_STRING(30366), 14, ICON, FANART, game_day)
    addDir(LOCAL_STRING(30367), 17, ICON, FANART, game_day)

    if FAV_TEAM != 'None':
        addDir(FAV_TEAM + LOCAL_STRING(30368), 18, ICON, FANART, game_day, None, AFFILIATES[FAV_TEAM])


def todays_games(game_day, level, teams=None):
    if game_day is None:
        game_day = localToEastern()

    display_day = stringToDate(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)

    addDir('[B]<< %s[/B]' % LOCAL_STRING(30010), 101, PREV_ICON, FANART, prev_day.strftime("%Y-%m-%d"), level, teams)

    date_display = '[B][I]' + colorString(display_day.strftime("%A, %m/%d/%Y"), GAMETIME_COLOR) + '[/I][/B]'

    addDir(date_display, 100, ICON, FANART, game_day, level, teams)

    url = 'https://statsapi.mlb.com/api/v1/schedule'
    url += '?hydrate=broadcasts(all),game(content(all)),linescore,team'
    url += '&sportId=' + str(level)
    url += '&date=' + game_day
    if teams is not None:
        url += '&teamId=' + teams

    headers = {
        'User-Agent': UA_PC
    }
    r = requests.get(url,headers=headers, verify=VERIFY)
    json_source = r.json()

    try:
        for game in json_source['dates'][0]['games']:
            for broadcast_index in range(0, 4):
                try:
                    if game['broadcasts'][broadcast_index]['name'] == 'MiLB.TV':
                        create_game_listitem(game, game_day, broadcast_index)
                        break
                except:
                    pass
    except:
        pass

    next_day = display_day + timedelta(days=1)
    addDir('[B]%s >>[/B]' % LOCAL_STRING(30011), 101, NEXT_ICON, FANART, next_day.strftime("%Y-%m-%d"), level, teams)


def create_game_listitem(game, game_day, broadcast_index):
    level_abbr = game['teams']['home']['team']['league']['name']
    if level_abbr[0] == 'T':
        level_abbr = 'AAA'
    elif level_abbr[0] == 'D':
        level_abbr = 'AA'
    elif level_abbr[0] == 'H':
        level_abbr = 'A+'
    elif level_abbr[0] == 'L':
        level_abbr = 'A-'

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
    if away_org in FAV_TEAM:
        fav_game = True
        away_team = colorString(away_team, FAV_TEAM_COLOR)

    if home_org in FAV_TEAM:
        fav_game = True
        home_team = colorString(home_team, FAV_TEAM_COLOR)

    game_time = ''
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
        game_time = game['status']['detailedState']

        if game_time == 'Final':
            game_time = colorString(game_time, FINAL)

        elif game['status']['abstractGameState'] == 'Live':
            if game['linescore']['isTopInning']:
                top_bottom = "T"
            else:
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

    game_pk = game['gamePk']

    stream_date = str(game_day)

    desc = game['teams']['home']['team']['league']['name']
    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) or (NO_SPOILERS == '3' and game_day == localToEastern()) or (NO_SPOILERS == '4' and game_day < localToEastern()) or game['status']['abstractGameState'] == 'Preview':
        name = game_time + ' ' + level_abbr + ': ' + away_team + ' at ' + home_team
    else:
        name = game_time + ' ' + level_abbr + ': ' + away_team
        if 'linescore' in game: name += ' ' + colorString(str(game['linescore']['teams']['away']['runs']), SCORE_COLOR)
        name += ' at ' + home_team
        if 'linescore' in game: name += ' ' + colorString(str(game['linescore']['teams']['home']['runs']), SCORE_COLOR)

    name = name
    if fav_game:
        name = '[B]' + name + '[/B]'

    # Set audio/video info based on stream quality setting
    resolution = 'HD'
    if 'videoResolution' in game['broadcasts'][broadcast_index]:
        resolution = game['broadcasts'][broadcast_index]['videoResolution']['resolutionShort']
    audio_info, video_info = getAudioVideoInfo(resolution)
    # 'duration':length
    info = {'plot': desc, 'tvshowtitle': 'MiLB', 'title': title, 'originaltitle': title, 'aired': game_day, 'genre': LOCAL_STRING(700), 'mediatype': 'video'}

    add_stream(name, title, game_pk, ICON, FANART, info, video_info, audio_info, stream_date)


def stream_select(game_pk):
    url = 'https://statsapi.mlb.com/api/v1/game/' + game_pk + '/content'
    headers = {
        'User-Agent': UA_PC
    }
    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    media_state = []
    epg = json_source['media']['epg'][0]['items']
    for item in epg:
        if item['mediaState'] != 'MEDIA_OFF':
            title = str(item['mediaFeedType']).title()
            title = title.replace('_', ' ')
            if 'HOME' in title.upper():
                media_state.insert(0, item['mediaState'])
            else:
                media_state.append(item['mediaState'])

    stream_url = ''
    if len(media_state) != 1:
        msg = LOCAL_STRING(30414)
        dialog = xbmcgui.Dialog()
        dialog.notification(LOCAL_STRING(30415), msg, ICON, 5000, False)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
        sys.exit()
    else:
        account = Account()
        stream_url, headers = account.get_stream(game_pk)

    if '.m3u8' in stream_url:
        play_stream(stream_url, headers)
    else:
        sys.exit()


def play_stream(stream_url, headers):
    listitem = stream_to_listitem(stream_url, headers)
    xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=listitem)

