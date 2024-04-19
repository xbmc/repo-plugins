from resources.lib.globals import *
from resources.lib.stream import *
from resources.lib.game import *


def categories():
    add_dir(LOCAL_STRING(30360), '/live', 100, ICON, FANART)
    add_dir(LOCAL_STRING(30361), '/live', 105, ICON, FANART)
    add_dir(LOCAL_STRING(30364), '/date', 200, ICON, FANART)


def todays_games(game_day):
    if game_day is None:
        game_day = local_to_eastern()

    xbmc.log("GAME DAY = " + str(game_day))
    settings.setSetting(id='stream_date', value=game_day)
    display_day = string_to_date(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)
    next_day = display_day + timedelta(days=1)
    add_dir('[B]<< %s[/B]' % LOCAL_STRING(30010), '/live', 101, PREV_ICON, FANART, prev_day.strftime("%Y-%m-%d"))
    date_display = '[B][I]%s[/I][/B]' % display_day.strftime("%A, %m/%d/%Y")
    addPlaylist(date_display, display_day, '/playhighlights', 900, ICON, FANART)


    url = "https://nhltv.nhl.com/api/v2/events" \
          f"?date_time_from={game_day}T00:00:00-04:00" \
          f"&date_time_to={next_day.strftime('%Y-%m-%d')}T00:00:00-04:00" \
          "&sort_direction=asc"

    headers = {'User-Agent': UA_PC}
    xbmc.log(url)
    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)

    global RECAP_PLAYLIST
    global EXTENDED_PLAYLIST
    RECAP_PLAYLIST.clear()
    EXTENDED_PLAYLIST.clear()
    # try:
    for game_json in r.json()['data']:
        if game_json["srMatchId"]:
            game = Game(game_json)
            game.create_listitem()
    # except:
    #     pass


    add_dir('[B]%s >>[/B]' % LOCAL_STRING(30011), '/live', 101, NEXT_ICON, FANART, next_day.strftime("%Y-%m-%d"))

def stream_select(stream1_id, stream2_id, stream3_id, stream1_name, stream2_name, stream3_name, highlight_id):
    xbmc.log(f"stream1_id: {stream1_id}, stream1_name: {stream1_name}")
    xbmc.log(f"stream2_id: {stream2_id}, stream2_name: {stream2_name}")
    xbmc.log(f"stream3_id: {stream3_id}, stream3_name: {stream3_name}")
    xbmc.log(f"highlight_id: {highlight_id}")

    options = []
    if stream1_id != "":
        options.append(stream1_name)
    if stream2_id != "":
        options.append(stream2_name)
    if stream3_id != "":
        options.append(stream3_name)
    if highlight_id != "":
        options.append("Highlights")

    dialog = xbmcgui.Dialog()
    n = dialog.select('Choose Stream', options)
    if n > -1:
        if options[n] == stream1_name:
            id = stream1_id
        elif options[n] == stream2_name:
            id = stream2_id
        elif options[n] == stream3_name:
            id = stream3_id
        elif options[n] == "Highlights":
            id = highlight_id
    else:
        sys.exit()


    if options[n] != "Highlights":
        update_user_token()

    stream = Stream(id)
    stream_url = stream.get_manifest()
    xbmc.log(str(stream_url))
    listitem = stream_to_listitem(stream_url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem)

def update_user_token():
    url = "https://nhltv.nhl.com/api/v3/cleeng/user"
    headers = {'User-Agent': UA_PC}
    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
    if r.ok:
        save_cookies(r.cookies)
    else:
        login()

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
        url = 'https://nhltv.nhl.com/api/v3/sso/nhl/login'
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": UA_PC,
            "Origin": "https://nhltv.nhl.com",
        }

        login_data = {"email":USERNAME,
                      "password":PASSWORD
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

