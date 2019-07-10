# -*- coding: utf-8 -*-
# Copyright 2019 sorax
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import urllib
import urlparse

try:
    import json
except ImportError:
    import simplejson as json

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon


episodes_url = "https://appdata.ardmediathek.de/appdata/servlet/tv/Sendung?documentId=6503982&json"


def getJsonFromUrl(url):
    document = urllib.urlopen(url).read()
    return json.loads(document)


def getTitle(content):
    return content["ueberschrift"]


def getImage(content, width):
    image_url = content["bilder"][0]["schemaUrl"]
    return image_url.replace("##width##", str(width))


def getEpisodeUrl(content):
    return content["link"]["url"]


def getStreamId(episode_url):
    url_path = episode_url.split("?")[0]
    return url_path.split("/").pop()


episodes = getJsonFromUrl(episodes_url)
episode_data = episodes["sections"][0]["modCons"][1]["mods"][0]["inhalte"][0]
title = getTitle(episode_data)
thumbnail_image = getImage(episode_data, 640)
fanart_image = getImage(episode_data, 1920)

episode_url = getEpisodeUrl(episode_data)
sendung_id = getStreamId(episode_url)

streams_url = "https://appdata.ardmediathek.de/appdata/servlet/play/media/" + sendung_id
result = getJsonFromUrl(streams_url)

mediaStreamArray = result["_mediaArray"][0]["_mediaStreamArray"]
streams = {
    0: mediaStreamArray[0]["_stream"],  # "auto"
    1: mediaStreamArray[1]["_stream"],  # "128k"
    2: mediaStreamArray[2]["_stream"][1],  # "256k"
    3: mediaStreamArray[2]["_stream"][0],  # "512k"
    4: mediaStreamArray[3]["_stream"][0],  # "1024k
    5: mediaStreamArray[3]["_stream"][1]  # "1800k
}

addon = xbmcaddon.Addon()
quality = int(addon.getSetting("quality"))

li = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_image)
li.setProperty("fanart_image", fanart_image)

addon_handle = int(sys.argv[1])
xbmcplugin.addDirectoryItem(addon_handle, streams[quality], li, False)
xbmcplugin.endOfDirectory(addon_handle)
