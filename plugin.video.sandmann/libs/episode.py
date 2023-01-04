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

from libs.network import getJsonFromUrl


def mapEpisode(episode):
    return {
        "date": getDate(episode),
        "desc": getDescription(episode),
        "dgs": getDgs(episode),
        "duration": episode["duration"],
        "fanart": getImage(episode, 1920),
        "thumb": getImage(episode, 640),
        "title": getTitle(episode),
        "url": episode["links"]["target"]["href"],
    }


def appendStreams(episode):
    details = getJsonFromUrl(episode["url"])

    streams_data = details["widgets"][0]["mediaCollection"]["embedded"]["_mediaArray"][0]
    mediaStreamArray = streams_data["_mediaStreamArray"]

    streams = {}
    for stream in mediaStreamArray:
        streams[stream["_quality"]] = stream["_stream"]

    return {
        "date": episode["date"],
        "desc": episode["desc"],
        "dgs": episode["dgs"],
        "duration": episode["duration"],
        "fanart": episode["fanart"],
        "streams": streams,
        "thumb": episode["thumb"],
        "title": episode["title"]
    }


def getEpisodes(episodes_url, quality):
    episodes_json = getJsonFromUrl(episodes_url)
    episodes_list = episodes_json["teasers"]

    item_list = []
    for episode in episodes_list:
        item_list.append(getEpisodeData(episode, quality))

    return item_list


def getDate(content):
    return content["broadcastedOn"].split("T")[0]


def getDescription(content):
    return content["images"]["aspect16x9"]["alt"]


def getDgs(content):
    return "mit Gebärdensprache" in content["shortTitle"]


def getImage(content, width):
    return content["images"]["aspect16x9"]["src"].replace("{width}", str(width))


def getTitle(content):
    return content["shortTitle"].split(" | ")[0]
