# -*- coding: utf-8 -*-
# Copyright 2011 Jörn Schumacher 
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

import urllib2, datetime

import xbmcplugin, xbmcgui, xbmcaddon

import parserss

# -- Podcast Configuration -----------------------------------
podcast_config = {
    "tagesschau": { "url": {"M": "http://www.tagesschau.de/export/video-podcast/webm/tagesschau",
                            "L": "http://www.tagesschau.de/export/video-podcast/webl/tagesschau" },
                    "name": "Tagesschau"},
    "tagesschau100": { "url": { "default": "http://www.tagesschau.de/export/video-podcast/tagesschau-in-100-sekunden" },
                       "name": "Tagesschau in 100 Sekunden" },
    "tagesthemen": { "url": { "M": "http://www.tagesschau.de/export/video-podcast/webm/tagesthemen",
                            "L": "http://www.tagesschau.de/export/video-podcast/webl/tagesthemen" },
                     "name": "Tagesthemen" },
    "tageswebschau": { "url": { "M": "http://www.tagesschau.de/export/video-podcast/webm/tageswebschau" },
                       "name": "tagesWEBschau" }, 
    "nachtmagazin": { "url": { "M": "http://www.tagesschau.de/export/video-podcast/webm/nachtmagazin",
                               "L": "http://www.tagesschau.de/export/video-podcast/webl/nachtmagazin" },
                      "name": "Nachtmagazin" },
    "berichtausberlin": { "url": { "M": "http://www.tagesschau.de/export/video-podcast/webm/bab",
                                   "L": "http://www.tagesschau.de/export/video-podcast/webl/bab" },
                          "name": "Bericht aus Berlin" },
    "wochenspiegel": { "url": {"M": "http://www.tagesschau.de/export/video-podcast/webm/wochenspiegel",
                               "L": "http://www.tagesschau.de/export/video-podcast/webl/wochenspiegel" },
                       "name": "Wochenspiegel" },
    "deppendorfswoche": { "url": { "default": "http://www.tagesschau.de/export/video-podcast/deppendorfswoche" },
                          "name": "Deppendorfs Woche" },
    "tagesschauvor20jahren": { "url": { "M": "http://www.tagesschau.de/export/video-podcast/webm/tagesschau-vor-20-jahren",
                                        "L": "http://www.tagesschau.de/export/video-podcast/webl/tagesschau-vor-20-jahren" },
                               "name": "Tagesschau vor 20 Jahren" }
    }
# ------------------------------------------------------------

# -- Settings -----------------------------------------------
settings = xbmcaddon.Addon(id='plugin.video.tagesschau')
quality_id = settings.getSetting("quality")
quality = ['M', 'L'][int(quality_id)]

# change order here or remove elements if you like
podcasts = ("tagesschau", "tagesschau100", "tagesthemen", "tageswebschau", "nachtmagazin", 
            "berichtausberlin", "wochenspiegel", "deppendorfswoche", "tagesschauvor20jahren")

# Time format
datetimeformat = "%a %d. %B %Y, %H:%M"
dateformat = "%a %d. %B %Y"
# ------------------------------------------------------------

def getUrl(podcast, quality):
    """Returns podcast URL in the desired quality (if available)"""
    config = podcast_config[podcast]["url"]
    if quality in config.keys():
        return config[quality]

    default_quality = config.keys()[0]
    return config[default_quality]

def getName(podcast, item):
    """Returns a proper name for an item"""
    if item["datetime"]:
        name = podcast_config[podcast]["name"]
        date, time = item["datetime"]
        timestr = ""

        # special treatment for "Tagesschau vor 20 Jahren"
        if podcast == "tagesschauvor20jahren":
            date = datetime.date(date.year - 20, date.month, date.day)

        if date and time:
            timestr = datetime.datetime.combine(date,time).strftime(datetimeformat)
        else:
            timestr = date.strftime(dateformat)
        return name + " (" + timestr + ")"

    return item["title"]

def addLink(name, url, iconimage, description):
        ok = True
        liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description } )
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
        return ok

for podcast in podcasts:
    feed = parserss.parserss(getUrl(podcast, quality))
    if len(feed["items"]) > 0:
        item = feed["items"][0]
        addLink(getName(podcast, item), item["media"]["url"], feed["image"], item.get("description", ""))

xbmcplugin.endOfDirectory(int(sys.argv[1]))
