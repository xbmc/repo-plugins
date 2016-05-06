# -*- coding: utf-8 -*-
# Module: plugin.video.magaritv
# Version: 1.0.0
# Author: Orazio Giliberti
# Created on: 29.04.2016
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
# This module was a modificated version of
# https://github.com/romanvm/plugin.video.example/releases
# released by Roman V M under License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
# Thanks Roman !


import sys
import json
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin


__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

url = "http://serviceone.magari.tv/video_json2.html"

try:
    # For Python 3.0 and later
    import urllib
    from urllib.request import urlopen
    response = urlopen(url)

except ImportError:
    # Fall back to Python 2's urllib2
    import urllib2
    from urllib2 import urlopen
    response = urllib2.urlopen(url)

print(sys.version[0])

string = response.read().decode('utf-8')
VIDEOS = json.loads(string)

def get_categories():
    """
    Get the list of video categories.
    Here you can insert some parsing code that retrieves
    the list of video categories (e.g. 'Movies', 'TV-shows', 'Documentaries' etc.)
    from some site or server.
    :return: list
    """
    return VIDEOS.keys()


def get_videos(category):
    """
    Get the list of videofiles/streams.
    Here you can insert some parsing code that retrieves
    the list of videostreams in a given category from some site or server.
    :param category: str
    :return: list
    """
    return VIDEOS[category]


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    :return: None
    """
    categories = get_categories()
    listing = []
    for category in categories:
        list_item = xbmcgui.ListItem(label=category, thumbnailImage=VIDEOS[category][0]['thumb'])
        list_item.setProperty('fanart_image', VIDEOS[category][0]['thumb'])
        list_item.setInfo('video', {'title': category, 'genre': category})
        url = '{0}?action=listing&category={1}'.format(__url__, category)
        is_folder = True
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(__handle__)


def list_videos(category):
    """
    Create the list of playable videos in the Kodi interface.
    :param category: str
    :return: None
    """
    videos = get_videos(category)
    listing = []
    for video in videos:
        list_item = xbmcgui.ListItem(label=video['name'], thumbnailImage=video['thumb'])
        list_item.setProperty('fanart_image', video['thumb'])
        list_item.setInfo('video', {'title': video['name'], 'genre': video['genre']})
        list_item.setProperty('IsPlayable', 'true')
        url = '{0}?action=play&video={1}'.format(__url__, video['video'])
        is_folder = False
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(__handle__)


def play_video(path):
    """
    Play a video by the provided path.
    :param path: str
    :return: None
    """
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(__handle__, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring:
    :return:
    """
    params = dict(parse_qsl(paramstring[1:]))
    if params:
        if params['action'] == 'listing':
            list_videos(params['category'])
        elif params['action'] == 'play':
            play_video(params['video'])
    else:
        list_categories()


if __name__ == '__main__':
    router(sys.argv[2])
