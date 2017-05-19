from resources.lib.globals import *

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

if mode != 900: check_reqpayload()

if mode == None:                        
    if ADDON.getSetting(id='default_profile') == '':
        get_profiles()
    
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

elif mode == 800:
    get_profiles()
    main_menu()

elif mode == 900:
    get_stream(url)

elif mode == 998:
    sys.exit()

elif mode == 999:
    logout()
    main_menu()


if mode != None and mode != 800:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 800:
    xbmcplugin.endOfDirectory(addon_handle, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)