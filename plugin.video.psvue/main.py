from resources.lib.ps_vue import *

params=get_params()
url=None
name=None
mode=None
show_id=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    show_id=params["show_id"]
except:
    pass


check_device_id()

sony = SONY()
if mode < 998:
    if ADDON.getSetting(id='last_auth') != '':
        last_auth = stringToDate(ADDON.getSetting(id='last_auth'), "%Y-%m-%dT%H:%M:%S.%fZ")
        if (datetime.utcnow() - last_auth).total_seconds() > 900: sony.check_auth()
    else:
        sony.check_auth()

if mode == None and mode < 998:
    if ADDON.getSetting(id='default_profile') == '' or ADDON.getSetting(id='always_ask_profile') == 'true': sony.get_profiles()
    main_menu()

elif mode == 50:
    timeline()

elif mode == 100:
    my_shows()

elif mode == 150:
    list_episodes(show_id)

elif mode == 200:
    favorite_channels()

elif mode == 300:
    live_tv()

elif mode == 400:
    sports()

elif mode == 500:
    kids()

elif mode == 600:
    recently_watched()

elif mode == 700:
    featured()

elif mode == 750:
    search()

elif mode == 800:
    sony.get_profiles()
    main_menu()

elif mode == 900:
    get_stream(url)

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

if mode != None and mode != 800 and mode != 750:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 800:
    xbmcplugin.endOfDirectory(addon_handle, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)
