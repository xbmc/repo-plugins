# coding=utf-8

import sys
import os
import urllib
import urlparse
import xbmcaddon
import xbmcgui
import xbmcplugin
import requests
from bs4 import BeautifulSoup
import re


def build_url(query):
    """
    Build route url
    :param query: url query parameters
    :return: formatted url
    """
    base_url = sys.argv[0]
    return base_url + '?' + urllib.urlencode(query)


def get_rss(url):
    """
    download the source HTML for the page using requests
    and parse the page using BeautifulSoup
    :param url: rss file url
    :return:
    """
    return BeautifulSoup(requests.get(url).text, 'html.parser')


def get_channels():
    """
    Extract channels from rss
    :return: list of channels
    """
    rss = get_rss('http://eco99fm.maariv.co.il/RSS_MusicChannels_Index/')
    channels = {}
    index = 1

    for item in rss.find_all('item'):
        channels.update({
            index: {
                'album_cover': re.search("src='([^']+)'", item.find('description').string).group(1),
                'title': item.find('title').string,
                'description': item.find('itunes:summary').string,
                'url': build_url({'mode': 'playlist', 'url': item.find('link').string})
            }
        })
        index += 1
    return channels


def get_playlists(url):
    """
    Extract playlists from rss
    :return: list of playlists
    """
    rss = get_rss(url)
    playlists = {}
    index = 1

    for item in rss.find_all('item'):
        playlists.update({
            index: {
                'album_cover': re.search("src='([^']+)'", item.find('description').string).group(1),
                'title': item.find('title').string,
                'description': item.find('itunes:summary').string,
                'url': build_url({'mode': 'stream', 'url': item.find('guid').string})
            }
        })
        index += 1
    return playlists


def build_menu(items, is_folder):
    """
    Build menu control
    :param items: items of list
    :param is_folder: indicates whether list items are folders
    :return:
    """
    items_list = []

    for item in items:
        # create a list item using the song filename for the label
        li = xbmcgui.ListItem(label=items[item]['title'])
        # set the fanart to the album cover
        li.setProperty('fanart_image', os.path.join(ADDON_FOLDER, 'resources/media/fanart.jpg'))
        if not is_folder:
            li.setProperty('IsPlayable', 'true')
        li.setProperty('PlotOutline', items[item]['description'])
        li.setInfo('video', {
            'title': items[item]['title'],
            'genre': 'Podcast',
            'plot': items[item]['description']
        })
        li.setArt({
            'thumb': items[item]['album_cover'],
            'poster': items[item]['album_cover'],
            'fanart': os.path.join(ADDON_FOLDER, 'resources/media/fanart.jpg')
        })
        url = items[item]['url']
        items_list.append((url, li, is_folder))
    xbmcplugin.addDirectoryItems(ADDON_HANDLE, items_list, len(items_list))
    xbmcplugin.setContent(ADDON_HANDLE, 'songs')
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def play(url):
    """
    Play current playlist
    :param url: playlist URL
    :return:
    """
    play_item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem=play_item)


def main():
    """
    Main method
    :return:
    """
    args = urlparse.parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)
    if mode is None:
        items = get_channels()
        build_menu(items, True)
    elif mode[0] == 'playlist':
        items = get_playlists(args['url'][0])
        build_menu(items, False)
    elif mode[0] == 'stream':
        play(args['url'][0])


if __name__ == '__main__':
    ADDON_FOLDER = xbmcaddon.Addon().getAddonInfo('path')
    ADDON_HANDLE = int(sys.argv[1])
    main()
