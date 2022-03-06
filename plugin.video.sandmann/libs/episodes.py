# -*- coding: utf-8 -*-
# Copyright 2022 sorax
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

from urllib.request import urlopen


def getJsonFromUrl(url):
    document = urlopen(url).read()
    return json.loads(document)


def getEpisodes(episodes_url, quality):
    episodes_json = getJsonFromUrl(episodes_url)
    episodes_list = episodes_json["teasers"]

    item_list = []
    for episode in episodes_list:
        item_list.append(getEpisodeData(episode, quality))

    return item_list


def getEpisodeData(data, quality):
    episode_url = data["links"]["target"]["href"]
    episode_details = getJsonFromUrl(episode_url)
    streams_data = episode_details["widgets"][0]["mediaCollection"]["embedded"]["_mediaArray"][0]
    mediaStreamArray = streams_data["_mediaStreamArray"]

    streams = {
        0: mediaStreamArray[4],
        1: mediaStreamArray[5],
        2: mediaStreamArray[1],
        3: mediaStreamArray[2],
        4: mediaStreamArray[0],
        5: mediaStreamArray[3]
    }

    return {
        "desc": getDescription(data),
        "duration": data["duration"],
        "fanart": getImage(data, 1920),
        "stream": streams[quality]["_stream"],
        "thumb": getImage(data, 640),
        "title": data["shortTitle"],
        "dgs": getDgs(data["shortTitle"])
    }


def getDescription(content):
    return content["images"]["aspect16x9"]["alt"].split(" (Quelle:")[0]


def getImage(content, width):
    return content["images"]["aspect16x9"]["src"].replace("{width}", str(width))


def getDgs(title):
    return ' - mit Gebärdensprache' in title
