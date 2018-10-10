from resources.lib.globals import *

params = get_params()
url = None
name = None
mode = None

if 'url' in params:
    url = urllib.unquote_plus(params["url"])

if 'name' in params:
    name = urllib.unquote_plus(params["name"])

if 'mode' in params:
    mode = int(params["mode"])

if mode is None or url is None or len(url)<1:
    listSeasons()
elif mode == 101:
    listEpisodes(url)  
elif mode == 102:
    getStream(url)
elif mode == 999:
    deauthorize()

xbmcplugin.endOfDirectory(addon_handle)