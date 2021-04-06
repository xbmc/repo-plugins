import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
import sys
import requests
import json

addonID = 'plugin.video.funcarrun'
addonVersion = '0.0.3'
addonDate = "4/4/2021"

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__quality__ = xbmcaddon.Addon(id=addonID).getSetting('quality')


def get_channel_content():
    url = "https://www.funcarrun.eu/apiv2.php?type=video"
    r = requests.get(url)
    result = r.text
    data = json.loads(result)
    return data


def get_data():
    video_list = get_channel_content()

    data = video_list['items']
    video_list = []
    for v in data:
        if v['id']['kind'] == 'youtube#video':
            video_list.append(v)
    return video_list


def show_notification(msg):
    xbmc.executebuiltin('Notification(' + __addonname__ + ',' + msg + ',5000,' + __icon__ + ')')


def run():
    addon_handle = int(sys.argv[1])
    xbmcplugin.setContent(addon_handle, 'videos')
    __addon__ = xbmcaddon.Addon()
    __addonname__ = __addon__.getAddonInfo('name')
    __icon__ = __addon__.getAddonInfo('icon')

    videoList = get_channel_content()
    for v in videoList:
        videoId = v['videoId']
        uri = "plugin://plugin.video.youtube/?action=play_video&videoid=" + videoId
        title = v['title']
        description = v['description']
        thumbnail = v['thumbUrl']
        description = description + "\n\nKijk voor inschrijven op https://www.funcarrun.eu"
        listitem = xbmcgui.ListItem(label=title)
        listitem.setInfo('video', {'plot': description })
        listitem.setInfo('video', {'plotoutline': description })
        listitem.setProperty('IsPlayable', 'true')
        listitem.setArt({'icon': thumbnail})

        xbmcplugin.addDirectoryItem(handle=addon_handle, url=uri, listitem=listitem, isFolder=False)

    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle)


def start():
    videoList = get_channel_content()
    print(videoList)
