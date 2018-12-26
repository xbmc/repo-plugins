# coding: utf-8
# pylint: disable=import-error

import datetime
import email.utils
import gzip
import io
import json
import re
import sys
import urllib2
from urllib import urlencode
from urlparse import parse_qsl
from xml.etree import ElementTree

import xbmcaddon
import xbmcplugin
import xbmcgui


__author__ = "Petr Kutalek (petr@kutalek.cz)"
__copyright__ = "Copyright (c) Petr Kutalek, 2015-2018"
__license__ = "GPL 2, June 1991"
__version__ = "2.2.1"

HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon("plugin.video.aktualnetv")
ICON = ADDON.getAddonInfo("icon")


def _create_url(**kwargs):
    """Creates plugin: URL
    plugin://plugin.video.aktualnetv/?action=play&token=…
    plugin://plugin.video.aktualnetv/?action=list&offset=…
    """
    return "{0}?{1}".format(sys.argv[0], urlencode(kwargs))


def _download_file(url):
    """Downloads file from specified location
    Offers GZip transfer encoding
    Should be replaced by request from Python 3 in the future
    """
    req = urllib2.Request(url)
    req.add_header("Accept-Encoding", "gzip")
    content = ""
    try:
        f = urllib2.urlopen(req)
        ce = f.headers.get("Content-Encoding")
        if ce and "gzip" in ce:
            gzipf = gzip.GzipFile(fileobj=io.BytesIO(f.read()), mode="rb")
            content = gzipf.read()
        else:
            content = f.read()
    except (urllib2.HTTPError, urllib2.URLError) as err:
        print(err.reason)
    finally:
        try:
            f.close()
        except NameError:
            pass
    return content


def _parse_root(rss):
    """Parses RSS feed into a list of item dictionaries
    """
    def _parse_duration(duration="0"):
        """Parses duration in the format of 0:00, or 0:00:00
        Returns number of seconds
        """
        secs = 0
        j = 1
        for s in reversed(duration.split(":", 2)):
            secs = secs + int(s) * j
            j *= 60
        return secs

    def _parse_rfc822_date(date):
        """Parses RFC822 date into Python datetime object
        """
        return datetime.datetime.fromtimestamp(
            email.utils.mktime_tz(email.utils.parsedate_tz(date)))

    def _parse_cover(url):
        """Parses cover photo url
        Returns an address for square thumbnail (323 x 323 px)
        or original url if could not be modified
        """
        return re.sub(
            u".+/([0-9a-z]{2}/[0-9a-z]{2}/[0-9a-f]{28})_.+?\\.(jpg|png)\\?.+",
            u"https://cdn.i0.cz/thumb/public-data/\\1_r1:1_thumb.\\2",
            url)

    def _get_text(node, default=""):
        return node.text.strip() if node is not None else default

    NS = {
        "media": "http://search.yahoo.com/mrss/",
        "atom": "http://www.w3.org/2005/Atom",
        "blackbox": "http://i0.cz/bbx/rss/",
        "jwplayer": "http://developer.longtailvideo.com/trac/",
        "content": "http://purl.org/rss/1.0/modules/content/",
        }

    items = []
    root = ElementTree.fromstring(rss)
    for i in root.findall(".//channel/item", NS):
        if i.find(".//blackbox:extra", NS).attrib.get("videoType") != "bbxvideo":
            continue
        items.append({
            "title": _get_text(i.find(".//title", NS), "?"),
            "description": _get_text(i.find(".//description", NS)),
            "pubdate": _parse_rfc822_date(_get_text(i.find(".//pubDate", NS))),
            "duration": _parse_duration(
                i.find(".//blackbox:extra", NS).attrib.get("duration", "0")),
            "cover": _parse_cover(i.find(
                ".//media:group/media:content[@height='300']",
                NS).attrib.get("url", ICON)),
            # ideally XPath 2.0: ".//media:group/media:content[@height=
            # max(.//media:group/media:content/@height)]"
            "guid": _get_text(i.find(".//guid", NS)),
            "category": _get_text(i.find(".//category", NS)),
            })
    return items


def _build_list(items, offset=None):
    """Builds Kodi list from Python list
    """
    for i in items:
        li = xbmcgui.ListItem(label=i["title"])
        li.setInfo("video", {
            "title": i["title"],
            "plot": i["description"],
            "duration": i["duration"],
            "studio": u"Online Partners s.r.o.",
            "genre": u"News",
            "tvshowtitle": i["category"],
            "tag": i["category"],
            "imdbnumber": "tt7030366",
            })
        li.setArt({
            "thumb": i["cover"],
            "poster": i["cover"],
            "icon": ICON,
            })
        li.setProperty("IsPlayable", "true")
        url = _create_url(action="play", token=i["guid"])
        xbmcplugin.addDirectoryItem(HANDLE, url, li, False)
    if offset:
        li = xbmcgui.ListItem(label=ADDON.getLocalizedString(30020))
        url = _create_url(action="list", offset=offset)
        xbmcplugin.addDirectoryItem(HANDLE, url, li, True)
    xbmcplugin.endOfDirectory(HANDLE)


def _list_videos(offset=0):
    """Builds list of playable items
    """
    rss = _download_file(
        "https://video.aktualne.cz/mrss/?offset={0}".format(offset))
    items = _parse_root(rss)
    _build_list(items, offset + 30)


def _play_video(token):
    """Resolves file plugin into actual video file
    """
    webpage = _download_file(
        "https://video.aktualne.cz/-/r~{0}/".format(token)).decode("utf-8")
    sources = re.findall(u"tracks: ({.+?}\\]}),", webpage, re.DOTALL)[0]
    sources = u"{{ \"sources\": {0} }}".format(sources)
    sources = json.loads(sources)
    path = sources["sources"]["HLS"][0]["src"]
    item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=item)


def _router(paramstring):
    """Handles addon execution
    """
    params = dict(parse_qsl(paramstring))
    if params:
        if params.get("action") == "play":
            if "token" not in params:
                raise ValueError(
                    "Invalid plugin:// url. Missing token param: {0}".format(
                        paramstring))
            _play_video(params["token"])
        elif params.get("action") == "list":
            offset = 0
            if "offset" in params:
                offset = int(params["offset"])
            _list_videos(offset)
        else:
            raise ValueError(
                "Invalid plugin:// url. Unknown action param: {0}".format(
                    paramstring))
    else:
        _list_videos()


if __name__ == "__main__":
    _router(sys.argv[2][1:])
