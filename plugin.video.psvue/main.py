from resources.lib.ps_vue import *
import xbmcgui

params = get_params()
url = None
name = None
mode = None
vod = 'null'
airing_id = 'null'
channel_id = 'null'
program_id = 'null'
series_id = 'null'
tms_id = 'null'
title = 'null'
plot = '[B][I][COLOR=FFFFFF66]Live[/COLOR][/I][/B]'
icon = 'null'
offset = '0'
movie_size = '40'

if 'url' in params:
    url = urllib.unquote_plus(params["url"])
if 'name' in params:
    name = urllib.unquote_plus(params["name"])
if 'title' in params:
    title = params["title"]
if 'plot' in params:
    plot = params["plot"]
if 'vod' in params:
    vod = params["vod"]
if 'icon' in params:
    icon = params["icon"]
if 'mode' in params:
    mode = int(params["mode"])
if 'airing_id' in params:
    airing_id = params["airing_id"]
if 'channel_id' in params:
    channel_id = params["channel_id"]
if 'program_id' in params:
    program_id = params["program_id"]
if 'series_id' in params:
    series_id = params["series_id"]
if 'tms_id' in params:
    tms_id = params["tms_id"]
if 'offset' in params:
    offset = params['offset']

check_device_id()

sony = SONY()

if mode < 998:
    if ADDON.getSetting(id='last_auth') != '':
        last_auth = string_to_date(ADDON.getSetting(id='last_auth'), "%Y-%m-%dT%H:%M:%S.%fZ")
        if (datetime.utcnow() - last_auth).total_seconds() >= 5400:
            sony.check_auth()
    else:
        sony.check_auth()

if mode is None and mode < 998:
    if ADDON.getSetting(id='always_ask_profile') == 'true':
        sony.get_profiles()

    main_menu()

elif mode == 30:
    all_channels()

elif mode == 50:
    next_airings()

elif mode == 75:
    trending()

elif mode == 100:
    my_shows()

elif mode == 150:
    list_episodes(program_id)

elif mode == 200:
    favorite_channels()

elif mode == 300:
    live_tv()
    
elif mode == 350:
    on_demand(channel_id)

elif mode == 400:
    sports()

elif mode == 500:
    kids()

elif mode == 550 or mode == 551 or mode == 552:
    if mode == 550:
        get_genre()
        movies(offset, movie_size)
    if mode == 551 or mode == 552:
        movies(offset, movie_size)

elif mode == 600:
    recently_watched()

elif mode == 700:
    featured()

elif mode == 750:
    search()

elif mode == 800:
    sony.get_profiles()
    main_menu()

elif mode == 850:
    export_show(program_id, plot, icon)

elif mode == 900:
    get_stream(url, airing_id, channel_id, program_id, series_id, tms_id, title, plot, icon)

elif mode == 950:
    if vod != airing_id:
        choice = xbmcgui.Dialog().yesno("Where would you like to watch this episode?","Click an item below to choose your preference", nolabel='ON DEMAND', yeslabel='DVR')
        if choice:
            get_stream(url, airing_id, channel_id, program_id, series_id, tms_id, title, plot, icon)
        else:
            airing_id = vod
            url = SHOW_URL + vod
            get_stream(url, airing_id, channel_id, program_id, series_id, tms_id, title, plot, icon)
    else:
        get_stream(url, airing_id, channel_id, program_id, series_id, tms_id, title, plot, icon)

elif mode == 997:
    epg_service = xbmcaddon.Addon('service.psvue.epg')
    epg_file_path = xbmc.translatePath(epg_service.getSetting(id='location'))

    epg_toggle_off = '{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", ' \
                     '"params": {"addonid": "service.psvue.epg", "enabled": false}, "id": 1}'
    xbmc.executeJSONRPC(epg_toggle_off)
    xbmcvfs.delete(os.path.join(epg_file_path, 'epg.db'))
    xbmcvfs.delete(os.path.join(epg_file_path, 'epg.xml'))
    xbmcvfs.delete(os.path.join(epg_file_path, 'playlist.m3u'))

    epg_toggle_on = '{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", ' \
                    '"params": {"addonid": "service.psvue.epg", "enabled": true}, "id": 1}'
    xbmc.executeJSONRPC(epg_toggle_on)

elif mode == 998:
    sys.exit()

elif mode == 999:
    sony.logout()
    sony.notification_msg(LOCAL_STRING(30006), LOCAL_STRING(30007))
    main_menu()

elif mode == 1000:
    sony.logout()
    ADDON.setSetting(id='deviceId', value='')
    sony.notification_msg(LOCAL_STRING(30006), LOCAL_STRING(30007))

elif mode == 1001:
    ids ={
        'channel_id': channel_id,
        'program_id': program_id,
        'series_id': series_id,
        'tms_id': tms_id
    }

    fav_type = ''
    if 'fav_type' in params:
        fav_type = params['fav_type']
    sony.add_to_favorites(fav_type, ids)

elif mode == 1002:
    ids ={
        'channel_id': channel_id,
        'program_id': program_id,
        'series_id': series_id,
        'tms_id': tms_id
    }

    fav_type = ''
    if 'fav_type' in params:
        fav_type = params['fav_type']
    sony.remove_from_favorites(fav_type, ids)


if mode == 800 or mode == 551 or mode == 552:
    xbmcplugin.endOfDirectory(addon_handle, updateListing=True)
elif mode is not None and mode != 750:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(addon_handle)
