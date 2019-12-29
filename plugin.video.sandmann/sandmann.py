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

import json

try:
    from html.parser import HTMLParser
    from urllib.request import urlopen
except ImportError:
    from HTMLParser import HTMLParser
    from urllib2 import urlopen

import xbmcaddon

addon = xbmcaddon.Addon()


def getJsonFromUrl(url):
    document = urlopen(url).read()
    return json.loads(document)


def sanitize(text):
    h = HTMLParser()
    return h.unescape(text)


def getTitle(content, dgs):
    outp = []
    outp.append(addon.getLocalizedString(30001))
    outp.append(addon.getLocalizedString(30002))
    outp.append(content["dachzeile"].split(" | ")[0])

    if dgs == 1:
        outp.append("(" + addon.getLocalizedString(30040) + ")")

    return sanitize(" ".join(outp))


def getDescription(content):
    desc = content["bilder"][0]["alt"].split(",")
    desc.pop()
    return sanitize("".join(desc))


def getImage(content, width):
    schema_url = content["bilder"][0]["schemaUrl"]
    image_url = schema_url.replace("##width##", str(width))
    return image_url.replace("?mandant=ard", "")


def getEpisodeUrl(content):
    return content["link"]["url"]


def getStreamId(episode_url):
    url_path = episode_url.split("?")[0]
    return url_path.split("/").pop()


def getDuration(content):
    return int(content["unterzeile"].split(" ")[0])


def getEpisodeData(data, quality, dgs):
    episode_url = getEpisodeUrl(data)
    stream_id = getStreamId(episode_url)
    streams_url = "https://appdata.ardmediathek.de/appdata/servlet/play/media/" + stream_id
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

    return {
        "desc": getDescription(data),
        "duration": getDuration(data),
        "fanart": getImage(data, 1920),
        "stream": streams[quality],
        "thumb": getImage(data, 640),
        "title": getTitle(data, dgs)
    }


def getEpisodes(episodes_url, quality, dgs):
    episodes_json = getJsonFromUrl(episodes_url)
    episodes = episodes_json["sections"][0]["modCons"][1]["mods"][0]["inhalte"]

    episode_list = []
    for i, episode in enumerate(episodes):
        if dgs == 1 or i % 2 == 0:
            episode_list.append(getEpisodeData(episode, quality, i % 2 != 0))

    return episode_list
