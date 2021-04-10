import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
import sys
import requests
import json
from urllib.parse import urlparse, parse_qs


addonID = 'plugin.video.funcarrun'
addonVersion = '0.0.3'
addonDate = "4/9/2021"

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])


def get_channel_content(category=None):
    if not category:
        url = "https://www.funcarrun.eu/apiv2.php?type=video"
    else:
        url = "https://www.funcarrun.eu/apiv2.php?type=video&category=" + category
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


def videos_by_category(category=None):
    videoList = get_channel_content(category=category)
    for v in videoList:
        videoId = v['videoId']
        uri = "plugin://plugin.video.youtube/?action=play_video&videoid=" + videoId
        title = v['title']
        description = v['description']
        thumbnail = v['thumbUrl']
        fanart = v['fanartUrl']
        description = description + "\n\nKijk voor inschrijven op https://www.funcarrun.eu"
        listitem = xbmcgui.ListItem(label=title)
        listitem.setInfo('video', {'plot': description, 'plotoutline': description})
        listitem.setArt({'icon': thumbnail, 'poster': thumbnail, 'fanart': fanart})

        xbmcplugin.addDirectoryItem(handle=__handle__, url=uri, listitem=listitem, isFolder=False)

    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL)


def list_categories():
    url = "https://www.funcarrun.eu/apiv2.php?type=video_categories"
    r = requests.get(url)
    result = r.text
    categories = json.loads(result)

    listing = []
    for category in categories:
        list_item = xbmcgui.ListItem(label=category['title'])
        list_item.setProperty('fanart_image', category['fanart'])
        list_item.setArt({'icon': category['thumb'], 'poster': category['thumb']})
        url = '{0}?action=listing&category={1}'.format(__url__, category['category'])
        is_folder = True
        listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)


def run():
    xbmcplugin.setContent(__handle__, 'videos')
    if "category=" in sys.argv[2]:
        o = urlparse(sys.argv[2])
        query = parse_qs(o.query)
        category = query['category'][0]
        videos_by_category(category=category)
    else:
        list_categories()

    xbmcplugin.endOfDirectory(__handle__)


def start():
    videoList = get_channel_content()
