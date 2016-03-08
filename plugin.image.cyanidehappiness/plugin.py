# -*- coding: utf8 -*-

# Copyright (C) 2016- Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import xbmc
import xbmcplugin
import xbmcgui
import random
import datetime
import routing
import re
from resources.lib.Utils import *

plugin = routing.Plugin()

MAX_COUNT = 3868
ITEMS_PER_PAGE = 10


@plugin.route('/')
def root():
    items = [
        (plugin.url_for(todaysimages), xbmcgui.ListItem("Today´s images"), True),
        (plugin.url_for(browsebyoffset), xbmcgui.ListItem("Browse by offset"), True),
    ]
    xbmcplugin.addDirectoryItems(plugin.handle, items)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/todaysimages')
def todaysimages():
    xbmcplugin.setContent(plugin.handle, 'images')
    items = get_cyanide_images(randomize=True)
    for item in items:
        add_image(item)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/browsebyoffset')
def browsebyoffset():
    xbmcplugin.setContent(plugin.handle, 'genres')
    items = []
    for i in range(0, MAX_COUNT // ITEMS_PER_PAGE):
        items.append((plugin.url_for(browsebyoffset_view, i * ITEMS_PER_PAGE),
                      xbmcgui.ListItem("%s - %s" % (str(i * ITEMS_PER_PAGE + 1), str((i + 1) * ITEMS_PER_PAGE))),
                      True))
    xbmcplugin.addDirectoryItems(plugin.handle, items)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/browsebyoffset/<offset>')
def browsebyoffset_view(offset):
    xbmcplugin.setContent(plugin.handle, 'images')
    items = get_cyanide_images(offset=int(offset))
    for item in items:
        add_image(item)
    xbmcplugin.endOfDirectory(plugin.handle)


def get_cyanide_images(limit=ITEMS_PER_PAGE, offset=0, randomize=False):
    now = datetime.datetime.now()
    filename = "cyanide%ix%ix%i" % (now.month, now.day, now.year)
    path = xbmc.translatePath(ADDON_DATA_PATH + "/" + filename + ".txt")
    if xbmcvfs.exists(path) and randomize:
        return read_from_file(path)
    items = []
    for i in range(1, limit):
        comic_id = random.randrange(1, MAX_COUNT) if randomize else i + offset
        url = 'http://www.explosm.net/comics/%i/' % comic_id
        response = get_http(url)
        if response:
            keyword = re.search("<meta property=\"og:image\".*?content=\"([^\"]*)\"", response).group(1)
            url = re.search("<meta property=\"og:url\".*?content=\"([^\"]*)\"", response).group(1)
            newitem = {'thumb': keyword,
                       'index': comic_id,
                       'label': url}
            items.append(newitem)
    save_to_file(content=items,
                 filename=filename,
                 path=ADDON_DATA_PATH)
    return items

if (__name__ == "__main__"):
    plugin.run()
xbmc.log('finished')
