from resources.globals import *





params=get_params()
url=None
name=None
mode=None
event_id=None
owner_id=None
video_id=None
icon = None
cat_info = None

if 'url' in params:
    url=urllib.unquote_plus(params["url"])

if 'name' in params:
    name=urllib.unquote_plus(params["name"])

if 'mode' in params:
    mode=int(params["mode"])

if 'event_id' in params:
    event_id=urllib.unquote_plus(params["event_id"])

if 'owner_id' in params:
    owner_id=urllib.unquote_plus(params["owner_id"])

if 'icon' in params:
    icon=urllib.unquote_plus(params["icon"])

if 'video_id' in params:
    video_id=urllib.unquote_plus(params["video_id"])

if 'cat_info' in params:
    cat_info=urllib.unquote_plus(params["cat_info"])


if mode==None or url==None or len(url)<1:    
    categories()          

elif mode==100:                
    getCategories()

elif mode==101:        
    getStream(owner_id,event_id,video_id)

elif mode==102:
    #searchLive()
    search()

elif mode==104:
    getStream(owner_id,event_id,video_id)

elif mode==105:
    getAccountStreams(owner_id)

elif mode==106:
    getCategoryEvents(cat_info)

elif mode==107:
    getHistory()

elif mode==150:
    login()

elif mode==160:
    manualEvent()

elif mode==999:
    sys.exit()

if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(addon_handle)