from .globals import *
from .api import *
from .utils import *
import sys
import requests
from time import gmtime

def main_menu():
    add_dir(LOCAL_STRING(32000), 100, AHL_LOGO, FANART)
    add_dir(LOCAL_STRING(32001), 102, AHL_LOGO, FANART)
    add_dir(LOCAL_STRING(32002), 103, AHL_LOGO, FANART)

def daily_games(game_day):
    if game_day is None:
        game_day = local_to_eastern()

    display_day = string_to_date(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)
    add_dir('[B]<< %s[/B]' % LOCAL_STRING(32003), 101, AHL_LOGO, FANART, prev_day.strftime("%Y-%m-%d"))

    url = API_URL + '/htv2020/schedule_league/100008?start_date=' + game_day + '&end_date=' + game_day
    log('Loading games from: '+ url)
    headers = get_request_headers()

    r = requests.get(url, headers=headers, verify=VERIFY)
    log('games response code: '+ str(r.status_code))

    if r.status_code >= 400:
        dialog = xbmcgui.Dialog()
        dialog.ok(LOCAL_STRING(31010), LOCAL_STRING(32006) + ' ' + game_day)
    else:
        json_source = r.json()

        # Add the date header for the list
        day_games_label = game_day
        if "games" in json_source:
            day_games_label += " (" + str(len(json_source['games'])) + " " + LOCAL_STRING(32027) + ")"
        else:
            day_games_label += " " + LOCAL_STRING(32007)

        list_item = xbmcgui.ListItem(label=day_games_label, thumbnailImage=AHL_LOGO)
        list_item.setProperty('fanart_image', FANART)

        u = sys.argv[0] + "?mode=" + str(101) + "&game_day=" + quote(game_day)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=list_item, isFolder=False)

        if "games" in json_source:
            log("num games returned: " + str(len(json_source['games'])))
            try:
                if len(json_source['games']) > 0:
                    for game in json_source['games']:
                        create_game_listitem(game, game_day)
            except Exception as e:
                log('Failed to process games: '+ str(e), True)
                pass

        next_day = display_day + timedelta(days=1)
        add_dir('[B]%s >>[/B]' % LOCAL_STRING(32004), 101, AHL_LOGO, FANART, next_day.strftime("%Y-%m-%d"))

def create_game_listitem(game, game_day):
    icon = None
    home_team = game['homeTeam']
    visiting_team = game['visitingTeam']

    icon = get_game_icon(home_team['iteamid'], home_team['strteamlogoimageurl'], visiting_team['iteamid'], visiting_team['strteamlogoimageurl'])

    game_time = ''
    if game['blivegameflag'] == 2 and game['currentlyStreaming'] == False:
        game_time = game['dateTime']
        game_time = string_to_date(game_time, "%Y-%m-%dT%H:%M:%SZ")
        game_time = utc_to_local(game_time)
        game_time = game_time.strftime('%I:%M %p').lstrip('0')

    elif game['blivegameflag'] == 2 and game['currentlyStreaming'] == True:
        game_time = '(Live)'
    else:
        game_time = '(Final)'

    game_id = game['id']

    fanart = TEAM_FANART[home_team['iteamid']]
    name = '%s %s %s %s' % (game_time, visiting_team['strteamname'], LOCAL_STRING(32028), home_team['strteamname'])
    desc = '%s %s %s' % (visiting_team['strteamname'], LOCAL_STRING(32028), home_team['strteamname']) + ' - ' + game_day
    name = name.encode('utf-8')

    title = '%s %s %s' % (visiting_team['strteamname'], LOCAL_STRING(32028), home_team['strteamname'])
    title = title.encode('utf-8')

    # Label free game of the day
    try:
        if bool(game['free']):
            name = name + color_string(' (FREE)', COLOR_FREE)
    except:
        pass

    video_info = {}
    audio_info = {}

    info = {'plot': desc,
            'tvshowtitle': 'AHLTV',
            'title': title,
            'aired': game_day,
            'genre': 'Hockey'}

    add_game_listitem(name, title, game_id, icon, fanart, info, video_info, audio_info)

def color_string(string, color):
    return '[COLOR=' + color + ']' + string + '[/COLOR]'

def add_game_listitem(name, title, game_id, icon=None, fanart=None, info=None, video_info=None, audio_info=None):
    ok = True

    u = sys.argv[0] + "?url=&mode=" + str(104) + "&name=" + quote(name) + "&game_id=" + quote(str(game_id))

    liz = xbmcgui.ListItem(name)

    if icon is not None:
        liz.setArt({'icon': icon, 'thumb': icon, 'clearlogo': CLEARLOGO})
    else:
        liz.setArt({'icon': ICON, 'thumb': ICON, 'clearlogo': CLEARLOGO})

    if fanart is not None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    liz.setProperty("IsPlayable", "true")

    liz.setInfo(type="Video", infoLabels={"Title": title})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)
    if video_info is not None:
        liz.addStreamInfo('video', video_info)
    if audio_info is not None:
        liz.addStreamInfo('audio', audio_info)

    liz.setProperty('dbtype', 'video')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
    xbmcplugin.setContent(addon_handle, 'videos')

    return ok

def select_game(game_id):
    game_json = get_game_info(game_id)
    played_id = None

    if game_json['blivegameflag'] == 2 and not game_json['currentlyStreaming']: # Game is not streaming at the moment, but should be live
        dialog = xbmcgui.Dialog()
        dialog.ok(LOCAL_STRING(32011), LOCAL_STRING(32012))
        sys.exit()
    elif (game_json['blivegameflag'] <= -1 and game_json['blivegameflag'] >= -5) or (game_json['blivegameflag'] == 2 and game_json['currentlyStreaming']): # VOD game or Live game
        dialog = xbmcgui.Dialog()

        multiple_audio = game_json['multipleAudioSetting'] == 1
        stream_info = get_game_streams(game_id, multiple_audio)

        x = dialog.select(LOCAL_STRING(32013), stream_info['list_items'])
        log('user selected stream: '+ str(x))

        if x >= 0:
            seek_secs = 0
            selected_audio = stream_info['streams'][x]['audioId']
            if stream_info['streams'][x]['startSeconds'] is not None:
                seek_secs = stream_info['streams'][x]['startSeconds']

            xbmcplugin.setResolvedUrl(addon_handle, True, stream_info['list_items'][x])

            while not xbmc.Player().isPlayingVideo():
                xbmc.Monitor().waitForAbort(0.5)

            # Seek to the start time of the video if it is set
            if xbmc.Player().isPlayingVideo():
                xbmc.sleep(250)
                xbmc.executebuiltin('Seek(' + str(seek_secs) + ')')
                played_id = log_played(game_id, selected_audio)

            track_minute = gmtime().tm_min

            while xbmc.Player().isPlayingVideo() and not xbmc.Monitor().abortRequested():
                xbmc.Monitor().waitForAbort(10.00)
                new_minute = gmtime().tm_min # Update watched status every minute
                if new_minute > track_minute:
                    track_minute = new_minute
                    if played_id is not None:
                        marked = mark_end_time(played_id)
                        if marked == False:
                            played_id = None
        else:
            # No stream selected / selection aborted
            sys.exit()

    else:
        dialog = xbmcgui.Dialog()
        dialog.ok(LOCAL_STRING(32011), LOCAL_STRING(32012))
        sys.exit()

def select_date():
    # Goto Date
    dialog = xbmcgui.Dialog()
    game_day = ''

    # Year
    year_list = []
    min_year = 2018
    while min_year <= datetime.now().year:
        year_list.insert(0, str(min_year))
        min_year = min_year + 1

    ret = dialog.select(LOCAL_STRING(32014), year_list)

    if ret > -1:
        year = year_list[ret]

        mnth_name = [LOCAL_STRING(32016), LOCAL_STRING(32017), LOCAL_STRING(32018), LOCAL_STRING(32019), LOCAL_STRING(32020), LOCAL_STRING(32021), LOCAL_STRING(32022), LOCAL_STRING(32023), LOCAL_STRING(32024), LOCAL_STRING(32025)]
        mnth_num = ['1', '2', '3', '4', '5', '6', '9', '10', '11', '12']

        ret = dialog.select(LOCAL_STRING(32015), mnth_name)

        if ret > -1:
            mnth = mnth_num[ret]

            # Day
            day_list = []
            day_item = 1
            last_day = calendar.monthrange(int(year), int(mnth))[1]
            while day_item <= last_day:
                day_list.append(str(day_item))
                day_item = day_item + 1

            ret = dialog.select(LOCAL_STRING(32026), day_list)

            if ret > -1:
                day = day_list[ret]
                game_day = year + '-' + mnth.zfill(2) + '-' + day.zfill(2)

    if game_day != '':
        daily_games(game_day)
    else:
        sys.exit()

def add_dir(name, mode, icon, fanart=None, game_day=None, info=None, content_type='videos'):
    ok = True
    u = addon_url+"?mode="+str(mode)
    if game_day is not None:
        u = u + "&game_day=" + quote(game_day)
    liz=xbmcgui.ListItem(name)
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'fanart': fanart})
    if info is not None:
        liz.setInfo( type="video", infoLabels=info)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=True)
    xbmcplugin.setContent(addon_handle, content_type)
    return ok
