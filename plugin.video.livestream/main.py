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
    event_id=urllib.unquote_plus(params["event_id"])
except:
    pass
try:
    owner_id=urllib.unquote_plus(params["owner_id"])
except:
    pass
try:
    icon=urllib.unquote_plus(params["icon"])
except:
    pass
try:
    video_id=urllib.unquote_plus(params["video_id"])
except:
    pass
try:
    cat_info=urllib.unquote_plus(params["cat_info"])
except:
    pass

print "Mode: "+str(mode)
#print "URL: "+str(url)
print "Name: "+str(name)
print "Event ID:"+str(event_id)
print "Owner ID:"+str(owner_id)
print "Video ID:"+str(video_id)



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