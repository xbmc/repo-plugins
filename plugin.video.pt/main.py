import os
import sys
import requests
import json
import xbmcvfs
from urllib.parse import urlencode, parse_qsl

import xbmcgui
import xbmcplugin
from xbmcaddon import Addon
from xbmcvfs import translatePath

URL = sys.argv[0]
HANDLE = int(sys.argv[1])
ADDON_PATH = translatePath(Addon().getAddonInfo('path'))
ICONS_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'icons')
FANART_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'fanart')
ADDON_ID = 'plugin.video.pt'
USERDATA_PATH = f'special://userdata/addon_data/{ADDON_ID}/'

def get_url(**kwargs):
    return '{}?{}'.format(URL, urlencode(kwargs))

def get_instances():
    filename = "instances.json"
    if not os.path.exists(USERDATA_PATH):
        os.makedirs(USERDATA_PATH)        
    FILE_PATH = os.path.join(USERDATA_PATH, filename)
    if not xbmcvfs.exists(FILE_PATH):
        print("No file, requesting new data!")
        request = requests.get('https://instances.joinpeertube.org/api/v1/instances/hosts?count=1000&start=0&sort=createdAt')
        r = request.json()
        with xbmcvfs.File(FILE_PATH) as instances_file:
            instances_file.write(json.dumps(r, ensure_ascii=False, indent=4))
    else:
        with xbmcvfs.File(FILE_PATH) as instances_file:
            r = json.load(instances_file)
    return r["data"]

def list_instances():
    xbmcplugin.setPluginCategory(HANDLE, 'Peertube Servers')
    xbmcplugin.setContent(HANDLE, 'movies')
    instances = get_instances()
    for index, genre_info in enumerate(instances):
        list_item = xbmcgui.ListItem(label=genre_info['host'])
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType('video')
        info_tag.setTitle(genre_info['host'])
        info_tag.setGenres([genre_info['host']])
        url = get_url(action='listing', host=genre_info['host'])
        is_folder = True
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)

def get_videos(host):
    request = requests.get('https://%s/api/v1/videos?isLocal=true' % (host))
    r = request.json()
    return r["data"]

def generate_item_info(self, name, url, is_folder=True, thumbnail="",
                        aired="", duration=0, plot="",):
    return {
        "name": name,
        "url": url,
        "is_folder": is_folder,
        "art": {
            "thumb": thumbnail,
        },
        "info": {
            "aired": aired,
            "duration": duration,
            "plot": plot,
            "title": name
        }
    }

def list_videos(host):
    genre_info = get_videos(host)
    xbmcplugin.setPluginCategory(HANDLE, 'Videos')
    xbmcplugin.setContent(HANDLE, 'movies')
    videos = genre_info
    for video in videos:
        list_item = xbmcgui.ListItem(label=video['name'])
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType('movie')
        info_tag.setTitle(video['name'])
        list_item.setProperty('IsPlayable', 'true')
        url = get_url(action='play', video=get_video(host, video['id']))
        is_folder = False
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.endOfDirectory(HANDLE)

def get_video(host, id):
    print(host)
    print(id)
    request = requests.get('https://%s/api/v1/videos/%d' % (host, id))
    r = request.json()
    print(r)
    return r["streamingPlaylists"][0]["playlistUrl"]


def play_video(path):
    play_item = xbmcgui.ListItem(offscreen=True)
    play_item.setPath(path)
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if not params:
        list_instances()

    elif params['action'] == 'listing':
        list_videos(params['host'])

    elif params['action'] == 'play':
        play_video(params['video'])
    else:
        raise ValueError(f'Invalid paramstring: {paramstring}!')


if __name__ == '__main__':
    router(sys.argv[2][1:])
