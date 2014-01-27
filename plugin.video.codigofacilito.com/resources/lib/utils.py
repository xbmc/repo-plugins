import urllib2
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

__addon__        = xbmcaddon.Addon()
__addon_id__     = __addon__.getAddonInfo('id')
__addon_id_int__ = int(sys.argv[1])
__addon_dir__    = xbmc.translatePath(__addon__.getAddonInfo('path'))
__language__ = __addon__.getLocalizedString

def log(message):
    xbmc.log(message)

def alert(title, message):
    xbmc.executebuiltin("Notification(" + title + "," + message + ")")

def get_localized_string(num):
    return __language__(num)

def get_params():
    params = {}
    paramstring = sys.argv[2]
    if len(paramstring)>=2:
        all_params = sys.argv[2]
        if (all_params[len(all_params)-1]=='/'):
            all_params = all_params[0:len(all_params)-2]
        all_params = all_params.replace('?', '')
        pair_params = all_params.split('&')

        for p in pair_params:
            split = p.split('=')
            params[split[0]] = split[1]

    return params

def add_directory_link(title, thumbnail, mode,url=None, is_folder=True, 
                       is_playable=False, total_items=0):
    final_url = "{0}?mode={1}&title={2}".format(sys.argv[0], 
                                                mode, 
                                                title)
    if url:
        final_url += "&url={0}".format(url)

    list_item = xbmcgui.ListItem(title,
                                 '',
                                 thumbnail,
                                 thumbnail)
    if is_playable:
        list_item.setProperty('IsPlayable', 'true') 

    return xbmcplugin.addDirectoryItem(__addon_id_int__, 
                                       final_url, 
                                       list_item, 
                                       isFolder=is_folder, 
                                       totalItems=total_items) 

def play_video(url):
    list_item = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(handle=__addon_id_int__,
                                     succeeded=True,
                                     listitem=list_item)

def end_directory():
    return xbmcplugin.endOfDirectory(__addon_id_int__)
