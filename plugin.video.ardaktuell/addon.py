from datetime import datetime
import base64
import json
import os
import re
import requests
import sys
import urllib.parse
import xmltodict

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

__PLUGIN_ID__ = "plugin.video.ardaktuell"

QUALITY_LEVEL = ["webxl", "webl", "webm", "webs"]

BROADCASTS = [
    {
        "name": "ARD Tagesschau",
        "icon": "https://www.tagesschau.de/image/podcast/ts-1400.jpg",
        "video_url": "https://www.tagesschau.de/export/video-podcast/%s/tagesschau_https/",
        "audio_url": "https://www.tagesschau.de/export/podcast/tagesschau_https/"
    },
    {
        "name": "ARD Tagesschau mit Gebärdensprache",
        "icon": "https://www.tagesschau.de/image/podcast/tsg-1400.jpg",
        "video_url": "https://www.tagesschau.de/export/video-podcast/%s/tagesschau-mit-gebaerdensprache_https/"
    },
    {
        "name": "ARD Tagesschau in 100 Sekunden",
        "icon": "https://www.tagesschau.de/image/podcast/ts100s-1400.jpg",
        "video_url": "https://www.tagesschau.de/export/video-podcast/%s/tagesschau-in-100-sekunden_https/",
        "audio_url": "https://www.tagesschau.de/export/podcast/hi/tagesschau-in-100-sekunden/"
    },
    {
        "name": "ARD Tagesthemen",
        "icon": "https://www.tagesschau.de/image/podcast/tt-1400.jpg",
        "video_url": "https://www.tagesschau.de/export/video-podcast/%s/tagesthemen_https/",
        "audio_url": "https://www.tagesschau.de/export/podcast/tagesthemen_https/"
    },
    {
        "name": "ARD Nachtmagazin",
        "icon": "https://www.tagesschau.de/image/podcast/nm-1400.jpg",
        "video_url": "https://www.tagesschau.de/export/video-podcast/%s/nachtmagazin_https/",
        "audio_url": "https://www.tagesschau.de/export/podcast/nachtmagazin_https/"
    },
    {
        "name": "ARD Bericht aus Berlin",
        "icon": "https://www.tagesschau.de/image/podcast/bab-1400.jpg",
        "video_url": "https://www.tagesschau.de/export/video-podcast/%s/bab_https/",
        "audio_url": "https://www.tagesschau.de/export/podcast/bab_https/",
        "type": "video"

    },
    {
        "name": "ARD Tagesschau vor 20 Jahren",
        "icon": "https://www.tagesschau.de/image/podcast/tsv20-1997-1400.jpg",
        "video_url": "https://www.tagesschau.de/export/video-podcast/%s/tagesschau-vor-20-jahren_https/",
        "audio_url": "https://www.tagesschau.de/export/podcast/tagesschau-vor-20-jahren_https/",
        "type": "video"
    },
    {
        "name": "ARD Mal angenommen...",
        "icon": "https://www.tagesschau.de/multimedia/bilder/mal-angenommen-podcast-cover-105~_v-original.jpg",
        "audio_url": "https://www.tagesschau.de/multimedia/podcasts/mal-angenommen-feed-101.xml",
        "type": "audio"
    }
]

# see https://forum.kodi.tv/showthread.php?tid=112916
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May",
           "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

settings = xbmcaddon.Addon(id=__PLUGIN_ID__)
addon_dir = xbmcvfs.translatePath(settings.getAddonInfo('path'))


class HttpStatusError(Exception):

    message = ""

    def __init__(self, msg):

        self.message = msg


class Mediathek:

    _menu = None

    addon_handle = None

    def __init__(self):

        def _make_node(broadcast, type, url, latest_only):

            _node = {
                "path": "latest" if latest_only else str(base64.urlsafe_b64encode(broadcast["name"].encode("utf-8"))),
                "name": broadcast["name"],
                "icon": broadcast["icon"],
                "type": type,
                "params": [
                    {
                        "play_latest" if latest_only else "rss": url
                    }
                ]
            }

            if not latest_only:
                _node["node"] = []

            return _node

        _nodes = []
        for broadcast in BROADCASTS:

            _quality = int(settings.getSetting("quality"))
            if "video_url" in broadcast and _quality < 4:
                _nodes.append(_make_node(
                    broadcast, "video", broadcast["video_url"] % QUALITY_LEVEL[_quality], settings.getSetting("archive") != "true"))

            elif "audio_url" in broadcast:
                _nodes.append(_make_node(broadcast, "music",
                                         broadcast["audio_url"], settings.getSetting("archive") != "true"))

        self._menu = [
            {  # root
                "path": "",
                "node": _nodes
            }
        ]

    def _play_latest(self, url):

        try:
            title, description, image, items = self._load_rss(url)
            item = items[0]
            li = self._create_list_item(item)
            xbmcplugin.setResolvedUrl(self.addon_handle, True, li)

        except HttpStatusError as error:

            xbmcgui.Dialog().notification(settings.getLocalizedString(32090), error.message)

    def _create_list_item(self, item):

        li = xbmcgui.ListItem(label=item["name"])

        if "description" in item:
            li.setProperty("label2", item["description"])

        if "stream_url" in item:
            li.setPath(item["stream_url"])

        if "type" in item:
            infos = {
                "title": item["name"]
            }

            if item["type"] == "video":
                infos["plot"] = item["description"] if "description" in item else ""

            if "duration" in item and item["duration"] >= 0:
                infos["duration"] = item["duration"]

            li.setInfo(item["type"], infos)

        if "icon" in item and item["icon"]:
            li.setArt({"icon": item["icon"]})
        else:
            li.setArt({"icon": os.path.join(
                addon_dir, "resources", "assets", "icon.png")}
            )

        if "date" in item and item["date"]:
            if "setDateTime" in dir(li):  # available since Kodi v20
                li.setDateTime(item["date"].strftime("%Y-%m-%dT%H:%M:%SZ"))
            else:
                pass

        if "specialsort" in item:
            li.setProperty("SpecialSort", item["specialsort"])

        return li

    def _add_list_item(self, entry, path):

        def _build_param_string(params, current=""):

            if params == None:
                return current

            for obj in params:
                for name in obj:
                    enc_value = base64.urlsafe_b64encode(
                        obj[name].encode("utf-8"))
                    current += "?" if len(current) == 0 else "&"
                    current += name + "=" + str(enc_value, "utf-8")

            return current

        if path == "/":
            path = ""

        item_path = path + "/" + entry["path"]

        param_string = ""
        if "params" in entry:
            param_string = _build_param_string(entry["params"],
                                               current=param_string)

        li = self._create_list_item(entry)

        if "stream_url" in entry:
            url = entry["stream_url"]

        else:
            url = "".join(
                ["plugin://", __PLUGIN_ID__, item_path, param_string])

        is_folder = "node" in entry
        li.setProperty("IsPlayable", "false" if is_folder else "true")

        xbmcplugin.addDirectoryItem(handle=self.addon_handle,
                                    listitem=li,
                                    url=url,
                                    isFolder=is_folder)

    def _http_request(self, url, headers={}, method="GET"):

        useragent = f"{settings.getAddonInfo('id')}/{settings.getAddonInfo('version')} (Kodi/{xbmc.getInfoLabel('System.BuildVersionShort')})"
        headers["User-Agent"] = useragent

        if method == "GET":
            req = requests.get
        elif method == "POST":
            req = requests.post
        else:
            raise HttpStatusError(settings.getLocalizedString(32091) % method)

        try:
            res = req(url, headers=headers)
        except requests.exceptions.RequestException as error:
            xbmc.log("Request Exception: %s" % str(error), xbmc.LOGERROR)
            raise HttpStatusError(settings.getLocalizedString(32092))

        if res.status_code == 200:
            return res.text, res.cookies

        else:
            raise HttpStatusError(settings.getLocalizedString(
                32093) % (res.status_code, url))

    def _load_rss(self, url):

        def _parse_item(_ci, fallback_image):

            if "enclosure" not in _ci or "@url" not in _ci["enclosure"]:
                return None

            item = {
                "name": _ci["title"],
                "description": _ci["description"] if "description" in _ci else "",
                "stream_url": _ci["enclosure"]["@url"],
                "type": "video" if _ci["enclosure"]["@type"].split("/")[0] == "video" else "music",
                "icon": _ci["itunes:image"]["@href"] if "itunes:image" in _ci and "@href" in _ci["itunes:image"] else fallback_image
            }

            if "pubDate" in _ci:
                _f = re.findall(
                    "(\d{1,2}) (\w{3}) (\d{4}) (\d{2}):(\d{2}):(\d{2})", _ci["pubDate"])

                if _f:
                    _m = _MONTHS.index(_f[0][1]) + 1
                    item["date"] = datetime(year=int(_f[0][2]), month=_m, day=int(_f[0][0]), hour=int(
                        _f[0][3]), minute=int(_f[0][4]), second=int(_f[0][5]))

            if "itunes:duration" in _ci:
                try:
                    duration = 0
                    for i, s in enumerate(reversed(_ci["itunes:duration"].split(":"))):
                        duration += 60**i * int(s)

                    item["duration"] = duration

                except:
                    pass

            return item

        res, cookies = self._http_request(url)

        if not res.startswith("<?xml"):
            raise HttpStatusError("%s %s" % (
                settings.getLocalizedString(32094), url))

        else:
            rss_feed = xmltodict.parse(res)

        channel = rss_feed["rss"]["channel"]

        title = channel["title"] if "title" in channel else ""
        description = channel["description"] if "description" in channel else ""

        if "image" in channel and "url" in channel["image"]:
            image = channel["image"]["url"]
        elif "itunes:image" in channel:
            image = channel["itunes:image"]["@href"]
        else:
            image = None

        items = []
        _cis = channel["item"] if type(channel["item"]) is list else [
            channel["item"]]
        for _ci in _cis:
            item = _parse_item(_ci, image)
            if item is not None:
                items += [item]

        return title, description, image, items

    def _render_rss(self, path, url):

        try:
            title, description, image, items = self._load_rss(url)

        except HttpStatusError as error:
            xbmc.log("HTTP Status Error: %s, path=%s" %
                     (error.message, path), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(settings.getLocalizedString(32090), error.message)

        else:
            if len(items) > 0:
                entry = {
                    "path": "latest",
                    "name": "%s (%s)" % (title, settings.getLocalizedString(32052)),
                    "description": description,
                    "icon": image,
                    "date": datetime.now(),
                    "specialsort": "top",
                    "type": items[0]["type"],
                    "params": [
                        {
                            "play_latest": url
                        }
                    ]
                }
                self._add_list_item(entry, path)

            for item in items:
                li = self._create_list_item(item)
                xbmcplugin.addDirectoryItem(handle=self.addon_handle,
                                            listitem=li,
                                            url=item["stream_url"],
                                            isFolder=False)

            if "setDateTime" in dir(li):  # available since Kodi v20
                xbmcplugin.addSortMethod(
                    self.addon_handle, xbmcplugin.SORT_METHOD_DATE)
            xbmcplugin.endOfDirectory(self.addon_handle)

    def _browse(self, path):

        def _get_node_by_path(path):

            if path == "/":
                return self._menu[0]

            tokens = path.split("/")[1:]
            node = self._menu[0]

            while len(tokens) > 0:
                path = tokens.pop(0)
                for n in node["node"]:
                    if n["path"] == path:
                        node = n
                        break

            return node

        node = _get_node_by_path(path)
        for entry in node["node"]:
            self._add_list_item(entry, path)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def handle(self, argv):

        def decode_param(encoded_param):

            return base64.urlsafe_b64decode(encoded_param).decode("utf-8")

        self.addon_handle = int(argv[1])

        path = urllib.parse.urlparse(argv[0]).path.replace("//", "/")
        url_params = urllib.parse.parse_qs(argv[2][1:])

        if "rss" in url_params:
            url = decode_param(url_params["rss"][0])
            self._render_rss(path, url)
        elif "play_latest" in url_params:
            url = decode_param(url_params["play_latest"][0])
            self._play_latest(url)
        else:
            self._browse(path=path)


if __name__ == '__main__':

    mediathek = Mediathek()
    mediathek.handle(sys.argv)
