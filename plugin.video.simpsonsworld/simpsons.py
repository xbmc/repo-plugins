from resources.lib.globals import *

params=get_params()
url=None
name=None
mode=None

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


if mode==None or url==None or len(url)<1:                    
    listSeasons()
elif mode==101:
    listEpisodes(url)  
elif mode==102:
    getStream(url)
elif mode==999:
	deauthorize()

xbmcplugin.endOfDirectory(addon_handle)