# -*- coding: utf-8 -*-

import time
from datetime import datetime

import requests
import pytz
import routing

import xbmcaddon
from xbmcplugin import addDirectoryItem, endOfDirectory
from xbmcgui import ListItem


plugin = routing.Plugin()
addon = xbmcaddon.Addon()


@plugin.route('/scheduler/')
def scheduler():
    res = requests.get('http://tagen.tv/api/events/')
    for item in res.json():
        try:
            date = datetime.strptime(item['date'], "%Y-%m-%dT%H:%M:%SZ")
        except TypeError:
            # known issue with the datetime python module
            # http://forum.kodi.tv/showthread.php?tid=112916
            date = datetime.fromtimestamp(time.mktime(time.strptime(item['date'], "%Y-%m-%dT%H:%M:%SZ")))
        date = date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Europe/Warsaw'))
        li = ListItem(u'{:%d.%m %H:%M} [COLOR yellow]{}[/COLOR]'.format(date, item['title']))
        cover = item.get('cover_url')
        if cover:
            li.setArt({'thumb': cover})
        description = item.get('description')
        if description:
            li.setInfo('video', {'plot': description})
        addDirectoryItem(plugin.handle, plugin.url_for(index), li, isFolder=True)

    endOfDirectory(plugin.handle)


@plugin.route('/')
def index():

    url = "rtmp://stream.tagen.tv:80/live/ playpath=glowna-sd live=true"
    li = ListItem(addon.getLocalizedString(30001))
    li.setProperty('isplayable', 'true')
    li.addStreamInfo('video', {'codec': 'h264', 'width': 854, 'height': 480})
    li.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
    addDirectoryItem(plugin.handle, url, li, isFolder=False)

    url = plugin.url_for(scheduler)
    li = ListItem(addon.getLocalizedString(30003))
    addDirectoryItem(plugin.handle, url, li, isFolder=True)

    endOfDirectory(plugin.handle)


if __name__ == '__main__':
    plugin.run()
