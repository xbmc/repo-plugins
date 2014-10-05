#!/usr/bin/env python

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import sys
import time
import urllib
import urlparse

from deredactie import VideoItem, parse_feed, START_URL

__addon__ = xbmcaddon.Addon()

self   = sys.argv[0]
handle = int(sys.argv[1])
qs     = sys.argv[2]

if len(qs) > 1:
    params = urlparse.parse_qs(qs[1:])
else:
    params = {}

if 'url' in params:
    url = params['url'][0]
else:
    url = START_URL

(title, entries) = parse_feed(url)
for entry in entries:
    is_video = isinstance(entry, VideoItem)
    if is_video:
        li = xbmcgui.ListItem(entry.title, thumbnailImage=entry.thumbnail_url)
        li.setProperty('mimetype', entry.mime_type)
        url = entry.url
    else:
        li = xbmcgui.ListItem(entry.title)
        url = self + '?' + urllib.urlencode({ 'url': entry.url })
    li.setInfo('video', {
        'title': entry.title,
        'date': time.strftime('%d.%m.%Y', entry.date)
    })
    xbmcplugin.addDirectoryItem(handle, url, li, not is_video)

xbmcplugin.endOfDirectory(handle, True)
