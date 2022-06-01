# SPDX-License-Identifier: GPL-2.0-or-later
# Original plugin.video.mlbtv © eracknaphobia
# Modified for NWL compatibility and code cleanup

from resources.lib.globals import *


def list_games(schedule_type='today', page_start=0):
    today = None
    if schedule_type == 'today':
        today = localToEastern()
        #now = datetime.now(pytz.timezone('UTC'))
        dir_title = stringToDate(today, "%Y-%m-%d").strftime("%A, %m/%d/%Y")
        dir_mode = 100
    else:
        dir_title = LOCAL_STRING(30362)
        dir_mode = 101

    dir_title = '[B][I]' + colorString(dir_title, GAMETIME_COLOR) + '[/I][/B]'

    addDir(dir_title, dir_mode)

    if page_start > 0:
        addDir('[B]<< %s[/B]' % LOCAL_STRING(30010), 101, (page_start-PAGE_LENGTH))

    url = 'https://core.stretchlive.com/event/' + schedule_type + '/213934?ppv=true'
    r = requests.get(url,headers=HEADERS, verify=VERIFY)
    json_source = r.json()

    page_end = page_start + PAGE_LENGTH
    #try:
    for index, game in enumerate(json_source):
        if index >= page_start and index < page_end:
            if game['hasVideo'] is True and game['ppv'] is False:
                create_game_listitem(game, today)
    #except:
    #    pass

    if len(json_source) >= page_end:
        addDir('[B]%s >>[/B]' % LOCAL_STRING(30011), 101, (page_start+PAGE_LENGTH))

    if schedule_type == 'today':
        addDir('[B]%s[/B]' % LOCAL_STRING(30362), 101)
    elif schedule_type == 'ondemand':
        addDir('[B]<< %s[/B]' % (LOCAL_STRING(30360) + LOCAL_STRING(30361)), 102)


def create_game_listitem(game, today):
    title = game['title'].replace(' Baseball at ', ' at ')

    game_time = game['startTime']
    game_time = stringToDate(game_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    game_time = UTCToLocal(game_time)
    game_date = game_time.strftime("%Y-%m-%d")
    if game_date == today:
        if TIME_FORMAT == '0':
            game_time_display = game_time.strftime('%I:%M %p').lstrip('0')
        else:
            game_time_display = game_time.strftime('%H:%M')
    else:
        if TIME_FORMAT == '0':
            game_time_display = game_time.strftime('%m/%d/%Y').lstrip('0') + ' ' + game_time.strftime('%I:%M %p').lstrip('0')
        else:
            game_time_display = game_time.strftime('%m/%d/%Y %H:%M').lstrip('0')

    desc = title + ', ' + game_time_display

    if game['eventStatus'] == 'live':
        game_time_display = game['eventStatus'].upper() + ' ' + game_time_display

        color = LIVE
        #if (now + timedelta(minutes=60)) > parse(game['startTime']):
        #    color = CRITICAL
        game_time_display = colorString(game_time_display, color)
    elif game['eventStatus'] == 'on-demand':
        game_time_display = colorString(game_time_display, FINAL)
    else:
        game_time_display = colorString(game_time_display, UPCOMING)

    name = game_time_display + ' ' + title

    icon = ICON
    #if 'eventCardUrl' in game and game['eventCardUrl'] is not None:
    #    icon = 'https://' + game['eventCardUrl']
    home_team = 'None'
    if FAV_TEAM in name:
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

    info = {'plot': desc, 'tvshowtitle': 'NWL', 'title': title, 'originaltitle': title, 'aired': game_date, 'genre': LOCAL_STRING(700), 'mediatype': 'video'}

    add_stream(name, title, id, icon, info)


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

