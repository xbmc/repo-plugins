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
    base_url = sys.argv[0]
    return base_url + '?' + urllib.urlencode(query)


def get_page(url):
    # download the source HTML for the page using requests
    # and parse the page using BeautifulSoup
    return BeautifulSoup(requests.get(url).text, 'html.parser')


def parse_page(page):
    songs = {}
    index = 1

    for item in page.find_all('item'):
        songs.update({
            index: {
                'album_cover': re.search("src='([^']+)'", item.find('description').string).group(1),
                'title': item.find('title').string,
                'description': item.find('itunes:summary').string,
                'url': item.find('guid').string
            }
        })
        index += 1
    return songs


def build_song_list(songs):
    song_list = []
    for song in songs:
        # create a list item using the song filename for the label
        li = xbmcgui.ListItem(label=songs[song]['title'])
        # set the fanart to the albumc cover
        li.setProperty('fanart_image', os.path.join(ADDON_FOLDER, 'resources/media/fanart.jpg'))
        # set the list item to playable
        li.setProperty('IsPlayable', 'true')
        li.setProperty('ChannelName', 'ECO 99FM')
        li.setProperty('PlotOutline', songs[song]['description'])
        li.setInfo('video', {
            'title': songs[song]['title'],
            'genre': 'Podcast',
            'plot': songs[song]['description']
        })
        li.setArt({
            'thumb': songs[song]['album_cover'],
            'poster': songs[song]['album_cover'],
            'fanart': os.path.join(ADDON_FOLDER, 'resources/media/fanart.jpg'),
        })
        # build the plugin url for Kodi
        url = build_url({'mode': 'stream', 'url': songs[song]['url'], 'title': songs[song]['title'].encode('utf-8')})
        # add the current list item to a list
        song_list.append((url, li, False))
    # add list to Kodi per Martijn
    # http://forum.kodi.tv/showthread.php?tid=209948&pid=2094170#pid2094170
    xbmcplugin.addDirectoryItems(addon_handle, song_list, len(song_list))
    # set the content of the directory
    xbmcplugin.setContent(addon_handle, 'songs')
    xbmcplugin.endOfDirectory(addon_handle)


def play_song(url):
    play_item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


def main():
    args = urlparse.parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)
    if mode is None:
        page = get_page(RSS)
        content = parse_page(page)
        build_song_list(content)
    elif mode[0] == 'stream':
        play_song(args['url'][0])


if __name__ == '__main__':
    ADDON_FOLDER = xbmcaddon.Addon().getAddonInfo("path")
    RSS = 'http://eco99fm.maariv.co.il/rss/'
    addon_handle = int(sys.argv[1])
    main()
