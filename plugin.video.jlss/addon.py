# Copyright (c) 2018 Lab Rat Media
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# -*- coding: utf-8 -*-

import feedparser
import xbmc
import xbmcgui

PLAYLIST_URL = "http://jimmylloyd.com/feedsite/feedW.xml"

def entry_to_playlist_item(entry):
    url = entry["media_content"][0]["url"]
    thumbnail = entry["media_thumbnail"][0]["url"]
    info = {}
    info["title"] = entry["title"]
    info["plot"] = entry["summary"]
    info["genre"] = entry["category"]
    info["duration"] = int(entry["media_content"][0]["duration"])
    info["mediatype"] = "episode"
    
    listitem = xbmcgui.ListItem(info["title"])
    listitem.setInfo("video", info)
    listitem.setArt({"thumb": thumbnail})
    return (url, listitem)
    
def get_all_videos(url):
    feed = feedparser.parse(url)
    return map(entry_to_playlist_item, feed["entries"])

playlist = xbmc.PlayList(1)
playlist.clear()
for item in get_all_videos(PLAYLIST_URL):
    url, listitem = item
    playlist.add(url, listitem)
    xbmc.log(str(url))
playlist.shuffle()

xbmc.Player().play(playlist)