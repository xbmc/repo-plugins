import sys, urllib, xbmc, xbmcgui, xbmcplugin, xbmcaddon, os
from lib import get_season_list, get_episode_list, get_episode
from urllib.parse import parse_qs, urlencode

base_url     = sys.argv[0]
addon_handle = int(sys.argv[1])
args         = parse_qs(sys.argv[2][1:])
ADDON_PATH = xbmcaddon.Addon().getAddonInfo('path')

xbmcplugin.setContent(addon_handle, "movies")

def build_url(query):
    return base_url  + "?" + urlencode(query)

mode = args.get('mode', None)

if mode is None:
    season_list = get_season_list()
    list_items=[]
    for season in season_list:
        season_display, season_link = season
        season_display = season_display.replace("&nbsp;"," ")
        url = build_url({'mode': 'season', 'season': season_link})
        li  = xbmcgui.ListItem(season_display) 
        li.setArt({'icon':   'DefaultFolder.png',
                   'fanart': os.path.join(ADDON_PATH,'fanart.jpg')})
        list_items.append((url, li, True,))
    xbmcplugin.addDirectoryItems(
            handle = addon_handle,
            items = list_items,
            totalItems = len(list_items))
    xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'season':
    season_link = args['season'][0]
    episode_list = get_episode_list(season_link)
    list_items=[]
    for episode in episode_list:
        episode_display, episode_link = episode
        url = build_url({'mode': 'episode', 'season': season_link, 'episode': episode_link, 'display': episode_display})
        li  = xbmcgui.ListItem(episode_display)
        li.setArt({'icon':      os.path.join(ADDON_PATH,'icon.png'),
                   'thumbnail': os.path.join(ADDON_PATH,'icon.png'),
                   'poster':    os.path.join(ADDON_PATH,'icon.png'),
                   'fanart':    os.path.join(ADDON_PATH,'fanart.jpg')})
        li.setInfo(type="Video", infoLabels={"Title": episode_display})
        li.setProperty('IsPlayable', 'true')
        list_items.append((url, li, False,))
    xbmcplugin.addDirectoryItems(
            handle = addon_handle,
            items = list_items,
            totalItems = len(list_items))
    xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'episode':
    season_link = args['season'][0]
    episode_link = args['episode'][0]
    episode_display = args['display'][0]
    mp4_link = get_episode(season_link, episode_link)
    li = xbmcgui.ListItem(path=mp4_link)
    li.setProperty('IsPlayable', 'true')
    li.setInfo(type="Video", infoLabels={"Title": episode_display})
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=li)

