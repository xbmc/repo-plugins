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

import re
import datetime
import xml.dom.minidom as xml
import urllib2

_datere = re.compile("(\d\d)\.(\d\d)\.(\d\d\d\d)")
_timere = re.compile("(\d\d)\:(\d\d)")

def parserss(feedurl):
    """Returns a list of dictionaries describing media"""
    s = urllib2.urlopen(feedurl).read()
    dom = xml.parseString(s)

    rssElems = dom.getElementsByTagName("rss")
    if len(rssElems) == 0: return None
    channelElems = rssElems[0].getElementsByTagName("channel")
    if len(channelElems) == 0: return None

    feed = dict()
    feed["items"] = _handleItems(channelElems[0].getElementsByTagName("item"))
    feed["image"] = _handleImages(channelElems[0].getElementsByTagName("image"))
    return feed

def _handleImages(images):
    for imageElem in images:
        url = _handleStringTag(imageElem, "url", None)
        if url:
            return url

    return None

def _handleItems(items):
    return [_handleItem(i) for i in items]

def _handleItem(itemElem):
    """Handles a single <item> of the rss feed"""
    item = dict()
    item["title"] = _handleStringTag(itemElem, "title")
    item["description"] = _handleStringTag(itemElem, "description", "")
    item["media"] = _handleEnclosures(itemElem.getElementsByTagName("enclosure"))
    item["pubDate"] = _handleStringTag(itemElem, "pubDate", "")

    item["datetime"] = _parseDateTime(item["title"])
    
    # title and media are mandatory
    if not item["title"] or not item["media"]:
        return None

    return item

def _handleEnclosures(enclosures):
    for e in enclosures:
        media = _handleEnclosure(e)
        if media:
            return media
    return None

def _handleEnclosure(enclosure):
    m = dict()
    m["length"] = enclosure.getAttribute("length")
    m["type"] = enclosure.getAttribute("type")
    m["url"] = enclosure.getAttribute("url")

    if m["url"] == "":
        return None

    return m

def _handleStringTag(dom, tag, default = None):
    """Returns the value of string tags or a default value if the tag is not present"""
    strings = []
    elems = dom.getElementsByTagName(tag)
    for elem in elems:
        strings.append(_getText(elem.childNodes))
    string = "".join(strings)
    if string.strip() == "":
        return default
    else:
        return string


def _getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def _parseDateTime(title):
    """Try to parse Date and Time out of a given title"""
    datematch = _datere.search(title)
    timematch = _timere.search(title)
    date = None
    time = None
    if datematch:
        year = int(datematch.group(3))
        month = int(datematch.group(2))
        day = int(datematch.group(1))
        date = datetime.date(year, month, day)

    if timematch:
        minute = int(timematch.group(2))
        hour = int(timematch.group(1))
        time = datetime.time(hour, minute)

    if date:
        return date, time

    return None

if __name__ == "__main__":
    f = "http://www.tagesschau.de/export/video-podcast/webl/tagesschau"
    feed = parserss(f)

    import pprint


    for i in feed["items"]:
        pprint.pprint(i)
    print feed["image"]
