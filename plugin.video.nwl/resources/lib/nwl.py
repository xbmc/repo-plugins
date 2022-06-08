# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for NWL compatibility and code cleanup

from resources.lib.globals import *


def categories():
    addDir(LOCAL_STRING(30360), 100)
    addDir(LOCAL_STRING(30362), 101)


def list_games(schedule_type='today', page_start=0):
    today = localToEastern()
    yesterday = yesterdays_date()
    #now = datetime.now(pytz.timezone('UTC'))
    if schedule_type == 'today':
        dir_title = None
        dir_mode = 100
    else:
        dir_mode = 101

    if page_start > 0:
        addDir('[B]<< %s[/B]' % LOCAL_STRING(30010), dir_mode, (page_start-PAGE_LENGTH))

    url = 'https://core.stretchlive.com/event/' + schedule_type + '/213934?ppv=true'
    r = requests.get(url,headers=HEADERS, verify=VERIFY)
    json_source = r.json()

    page_end = page_start + PAGE_LENGTH
    scores = dict()
    try:
        for index, game in enumerate(json_source):
            if index >= page_start and index < page_end:
                if game['hasVideo'] is True and game['ppv'] is False:
                    game_time = game['startTime']
                    utc_game_time = stringToDate(game_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                    # add 25 minutes to broadcast time for first pitch time
                    utc_game_time = utc_game_time + timedelta(minutes=25)
                    utc_game_hour = str(utc_game_time.hour)
                    game_time = UTCToLocal(utc_game_time)
                    game_day = game_time.strftime("%Y-%m-%d")

                    # show date header based on first live/upcoming game
                    if schedule_type == 'today' and dir_title is None:
                        dir_title = '[B][I]' + colorString(stringToDate(game_day, "%Y-%m-%d").strftime("%A, %m/%d/%Y"), GAMETIME_COLOR) + '[/I][/B]'
                        addDir(dir_title, dir_mode)

                    # get scores for today or yesterday
                    if game_day not in scores and (game_day == today or game_day == yesterday):
                        scores[game_day] = dict()
                        try:
                            url = 'https://scorebook.northwoodsleague.com/standalone/scoreboard/' + game_day

                            headers = {
                                'User-Agent': UA_PC,
                                'Origin': 'https://northwoodsleague.com',
                                'Referer': 'https://northwoodsleague.com/'
                            }
                            r = requests.get(url,headers=headers, verify=VERIFY)
                            #xbmc.log(r.text)

                            # parse the scores page
                            page = re.findall('(?s)(?<=<div class="top-info">).*?(?=<div class="extra-links">)', r.text)
                            print('Number of games in scores page: ' + str(len(page)))
                            utc = pytz.timezone('UTC')

                            # loop through games from the scores page
                            for item in page:
                                team_names = re.findall('<span class="team-name">([^<]*)<\/span>', item)
                                team_results = re.findall('<span class="team-result">([^<]*)<\/span>', item)
                                prob_pitchers = re.findall('<span class="prob-pitcher">([^<]*)<\/span>', item)
                                inning = re.findall('<span class="align-right">([^<]*)<\/span>', item)
                                misc = re.findall('(?s)(?<=<span class="align-right">).*?(?=<div class="team-grid">)', item)
                                venue_and_time = re.findall('<div>([^<]*)<\/div>', misc[0])

                                # use the game title as the first dict key
                                game_title = team_names[0] + ' Baseball at ' + team_names[1]
                                if game_title not in scores[game_day]:
                                    scores[game_day][game_title] = dict()

                                # use the first pitch utc hour as the second dict key to distinguish between games for a doubleheader
                                first_pitch_time = venue_and_time[1].split(')')[0].strip().upper()
                                first_pitch_time = first_pitch_time.replace('(EASTERN','-0400').replace('(CENTRAL','-0500')
                                first_pitch_time = parse(first_pitch_time)
                                hour = first_pitch_time.astimezone(utc).strftime('%H')
                                if hour.startswith('0'):
                                    hour = hour[1:]

                                scores[game_day][game_title][hour] = {
                                    'away_team': html.unescape(team_names[0].strip()),
                                    'home_team': html.unescape(team_names[1].strip()),
                                    'home_score': html.unescape(team_results[1].strip()),
                                    'away_score': html.unescape(team_results[0].strip()),
                                    'home_score': html.unescape(team_results[1].strip()),
                                    'away_probable': html.unescape(prob_pitchers[0].split(' (')[0].strip()),
                                    'home_probable': html.unescape(prob_pitchers[1].split(' (')[0].strip()),
                                    'inning': html.unescape(inning[0].strip().replace('In progress / ', '').replace('Bottom ', 'B ').replace('Top ', 'T ')),
                                    'venue': html.unescape(venue_and_time[0].strip())
                                }
                        except:
                            pass

                    score_details = dict()
                    if game_day in scores and game['title'] in scores[game_day] and utc_game_hour in scores[game_day][game['title']]:
                        score_details = scores[game_day][game['title']][utc_game_hour]

                    create_game_listitem(game, game_time, game_day, today, score_details)
            elif index >= page_end:
                break
    except:
        pass

    if len(json_source) >= page_end:
        addDir('[B]%s >>[/B]' % LOCAL_STRING(30011), dir_mode, (page_start+PAGE_LENGTH))


def create_game_listitem(game, game_time, game_day, today, score_details):
    title = game['title'].replace(' Baseball at ', ' at ')

    if game_day == today:
        if TIME_FORMAT == '0':
            game_time_display = game_time.strftime('%I:%M %p').lstrip('0')
        else:
            game_time_display = game_time.strftime('%H:%M')
    else:
        if TIME_FORMAT == '0':
            game_time_display = game_time.strftime('%m/%d/%Y').lstrip('0') + ' ' + game_time.strftime('%I:%M %p').lstrip('0')
        else:
            game_time_display = game_time.strftime('%m/%d/%Y %H:%M').lstrip('0')

    desc = ''
    probables = ''
    if ('away_probable' in score_details and score_details['away_probable'] != '') or ('home_probable' in score_details and score_details['home_probable'] != ''):
        probables = ' ('
        if 'away_probable' in score_details and score_details['away_probable'] != '':
            probable_pitcher = score_details['away_probable'][10:]
            desc += probable_pitcher
            probables += get_last_name(probable_pitcher)
        else:
            desc += 'TBD'
            probables += 'TBD'
        desc += ' vs. '
        probables += ' vs '
        if 'home_probable' in score_details and score_details['home_probable'] != '':
            probable_pitcher = score_details['home_probable'][10:]
            desc += probable_pitcher
            probables += get_last_name(probable_pitcher)
        else:
            desc += 'TBD'
            probables += 'TBD'
        desc += '[CR]'
        probables += ')'
        probables = colorString(probables, FINAL)

    if 'venue' in score_details:
        desc += 'From ' + score_details['venue'] + '[CR]'

    desc += game_time_display

    if game['eventStatus'] == 'live':
        if 'inning' in score_details:
            game_time_display = score_details['inning']
        else:
            game_time_display = game['eventStatus'].upper() + ' ' + game_time_display

        color = LIVE
        #if (now + timedelta(minutes=60)) > parse(game['startTime']):
        #    color = CRITICAL
        game_time_display = colorString(game_time_display, color)
    elif game['eventStatus'] == 'on-demand':
        game_time_display = colorString(game_time_display, FINAL)
    else:
        game_time_display = colorString(game_time_display, UPCOMING)

    name = game_time_display + ' '

    fav_game = False
    if FAV_TEAM in title:
        fav_game = True

    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) or (NO_SPOILERS == '3' and game['eventStatus'] == 'live') or (NO_SPOILERS == '4' and game['eventStatus'] == 'on-demand'):
        name += title
    else:
        if (game['eventStatus'] == 'live' or game['eventStatus'] == 'on-demand') and 'away_team' in score_details and 'home_team' in score_details and 'away_score' in score_details and 'home_score' in score_details:
            name += score_details['away_team'] + ' ' + score_details['away_score'] + ' at ' + score_details['home_team'] + ' ' + score_details['home_score']
        else:
            name += title

    icon = ICON
    #if 'eventCardUrl' in game and game['eventCardUrl'] is not None:
    #    icon = 'https://' + game['eventCardUrl']
    home_team = 'None'
    if fav_game:
        name = '[B]' + name.replace(FAV_TEAM, colorString(FAV_TEAM, FAV_TEAM_COLOR)) + '[/B]'
        home_team = FAV_TEAM
    else:
        title_array = title.split(' at ')
        home_team = title_array[len(title_array)-1]

    if home_team in TEAM_LOGOS:
        if TEAM_LOGOS[home_team].startswith('http'):
            icon = TEAM_LOGOS[home_team]
        else:
            icon = 'https://assets.northwoodsleague.com/scorebook/images/teams/' + TEAM_LOGOS[home_team] + '.png'

    id = game['id']

    info = {'plot': desc, 'tvshowtitle': 'NWL', 'title': title, 'originaltitle': title, 'aired': game_day, 'genre': LOCAL_STRING(700), 'mediatype': 'video'}

    add_stream((name + probables), title, id, icon, info)


def stream_select(id):
    url = 'https://core.stretchlive.com/event/id/' + id + '/video'
    r = requests.get(url, headers=HEADERS, verify=VERIFY)
    json_source = r.json()

    # define a dialog that we can use as needed
    dialog = xbmcgui.Dialog()
    if 'url' in json_source:
        stream_url = 'https://' + json_source['url']
        start = '-1'
        # only show the start point dialog if not using Kodi's default resume ability, the "ask to start live at beginning" option is enabled, and it's a live game
        if sys.argv[3] != 'resume:true' and CATCH_UP == 'true' and 'status' in json_source and json_source['status'] == 'live':
            # beginning and live as start point options
            start_options = [LOCAL_STRING(30398), LOCAL_STRING(30399)]

            # start point selection dialog
            p = dialog.select(LOCAL_STRING(30396), start_options)
            # beginning
            if p == 0:
                start = '1'
            # cancel will exit
            elif p == -1:
                sys.exit()
        play_stream(stream_url, start)
    else:
        dialog.notification(LOCAL_STRING(30383), LOCAL_STRING(30384), ICON, 5000, False)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
        sys.exit()
        sys.exit()


def play_stream(stream_url, start):
    listitem = stream_to_listitem(stream_url, start)
    xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=listitem)

