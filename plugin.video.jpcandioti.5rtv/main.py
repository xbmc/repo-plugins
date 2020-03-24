# -*- coding: utf-8 -*-
# Module: plugin.video.jpcandioti.5rtv
# Author: Juan Pablo Candioti - @JPCandioti
# Site: https://github.com/jpcandioti/plugin.video.jpcandioti.5rtv
# Created on: 2020-03-21

import sys
import xbmcgui
import xbmcplugin

_handle = int(sys.argv[1])

LIVESTREAM_CHANNEL  = '22636012'
LIVESTREAM_EVENT    = '8242619'
YOUTUBE_CHANNEL     = 'UCCvR_NFSKLkPM-7zbGV2Ckg'


def mainlist():
    listing = []

    list_item = xbmcgui.ListItem(label='En vivo', iconImage='DefaultTVShows.png')
    url = 'plugin://plugin.video.livestream/?url=%2Flive_now&mode=104&event_id=' + LIVESTREAM_EVENT + '&owner_id=' + LIVESTREAM_CHANNEL + '&video_id=LIVE'
    list_item.setProperty('IsPlayable', 'true')
    list_item.setInfo(type='video', infoLabels={'title': '5RTV en vivo'})
    is_folder = False
    listing.append((url, list_item, is_folder))

    list_item = xbmcgui.ListItem(label='Programas emitidos', iconImage='DefaultVideoPlaylists.png')
    url = 'plugin://plugin.video.youtube/channel/' + YOUTUBE_CHANNEL + '/playlists/'
    is_folder = True
    listing.append((url, list_item, is_folder))

    list_items(listing)


def list_items(listing):
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


if __name__ == '__main__':
    mainlist()
