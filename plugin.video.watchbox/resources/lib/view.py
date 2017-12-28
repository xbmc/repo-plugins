# -*- coding: utf-8 -*-
# Watchbox
# Copyright (C) 2017 MrKrabat
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import urllib

import xbmc
import xbmcgui
import xbmcplugin


# keys allowed in setInfo
types = ["count", "size", "date", "genre", "year", "episode", "season", "top250", "tracknumber",
         "rating", "userrating", "watched", "playcount", "overlay", "cast", "castandrole", "director",
         "mpaa", "plot", "plotoutline", "title", "originaltitle", "sorttitle", "duration", "studio",
         "tagline", "writer", "tvshowtitle", "premiered", "status", "code", "aired", "credits", "lastplayed",
         "album", "artist", "votes", "trailer", "dateadded", "mediatype"]

def endofdirectory():
    # sort methods are required in library mode
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)

    # let xbmc know the script is done adding items to the list
    xbmcplugin.endOfDirectory(handle = int(sys.argv[1]))


def add_item(args, info, isFolder=True, total_items=0, mediatype="video"):
    """Add item to directory listing.
    """

    # create list item
    li = xbmcgui.ListItem(label = info["title"])

    # get infoLabels
    infoLabels = make_infolabel(args, info)

    # get url
    u = build_url(args, info)

    if isFolder:
        # directory
        li.setInfo(mediatype, infoLabels)
    else:
        # playable video
        infoLabels["mediatype"] = "video"
        li.setInfo(mediatype, infoLabels)
        li.addStreamInfo("video", {"codec": "h264", "aspect": 1.78, "width": 960, "height": 544})
        li.addStreamInfo("audio", {"codec": "aac", "channels": 2})
        li.setProperty("IsPlayable", "true")

    # set media image
    li.setArt({"thumb":  info.get("thumb",  "DefaultFolder.png"),
               "poster": info.get("thumb",  "DefaultFolder.png"),
               "banner": info.get("thumb",  "DefaultFolder.png"),
               "fanart": info.get("fanart", xbmc.translatePath(args._addon.getAddonInfo("fanart"))),
               "icon":   info.get("thumb",  "DefaultFolder.png")})

    # add item to list
    xbmcplugin.addDirectoryItem(handle     = int(sys.argv[1]),
                                url        = u,
                                listitem   = li,
                                isFolder   = isFolder,
                                totalItems = total_items)


def build_url(args, info):
    """Create url
    """
    s = ""
    # step 1 copy new information from info
    for key, value in info.iteritems():
        if value:
            s = s + "&" + key + "=" + urllib.quote_plus(value)

    # step 2 copy old information from args, but don't append twice
    for key, value in args.__dict__.iteritems():
        if value and key in types and not "&" + str(key) + "=" in s:
            s = s + "&" + key + "=" + urllib.quote_plus(value)

    return sys.argv[0] + "?" + s[1:]


def make_infolabel(args, info):
    """Generate infoLabels from existing dict
    """
    infoLabels = {}
    # step 1 copy new information from info
    for key, value in info.iteritems():
        if value and key in types:
            infoLabels[key] = value

    # step 2 copy old information from args, but don't overwrite
    for key, value in args.__dict__.iteritems():
        if value and key in types and key not in infoLabels:
            infoLabels[key] = value

    return infoLabels
