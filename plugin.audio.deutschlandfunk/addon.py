from bs4 import BeautifulSoup
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

__PLUGIN_ID__ = "plugin.audio.deutschlandfunk"

URL_STREAMS_RPC = "https://srv.deutschlandradio.de/config-feed.2828.de.rpc"

URL_PODCASTS_DLF = "https://www.deutschlandfunk.de/podcasts.2516.de.html?drpp%3Ahash=displayAllBroadcasts"
URL_PODCASTS_DLK = "https://www.deutschlandfunkkultur.de/podcasts.2502.de.html?drpp%3Ahash=displayAllBroadcasts"
URL_PODCASTS_NOVA = "https://www.deutschlandfunknova.de/podcasts"

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

    addon_handle = None

    def __init__(self):

        pass

    def _make_root_menu(self):

        nodes = [
            {
                "path": "dlf",
                "name": "Deutschlandfunk",
                "icon": os.path.join(
                    addon_dir, "resources", "assets", "icon_dlf.png"),
                "node": []
            },
            {
                "path": "dkultur",
                "name": "Deutschlandfunk Kultur",
                "icon": os.path.join(
                    addon_dir, "resources", "assets", "icon_drk.png"),
                "node": []
            },
            {
                "path": "nova",
                "name": "Deutschlandfunk Nova",
                "icon": os.path.join(
                    addon_dir, "resources", "assets", "icon_nova.png"),
                "node": []
            }
        ]

        for entry in nodes:
            self._add_list_item(entry, "/")

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _make_station_menu(self, path):

        try:
            _json, _cookies = self._http_request(URL_STREAMS_RPC)
            meta = json.loads(_json)

        except HttpStatusError as error:
            xbmc.log("HTTP Status Error: %s, path=%s" %
                     (error.message, path), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(settings.getLocalizedString(32090), error.message)
            return

        nodes = list()
        if "/dlf" == path:
            nodes.append({
                "path": "stream",
                "name": "Deutschlandfunk",
                "icon": os.path.join(
                        addon_dir, "resources", "assets", "icon_dlf.png"),
                "stream_url": meta['livestreams']['dlf']['mp3']['high'],
                "type": "music",
                "specialsort": "top"
            })
            nodes.append({
                "path": "podcasts",
                "name": "Podcasts",
                "icon": os.path.join(
                        addon_dir, "resources", "assets", "icon_dlf_rss.png"),
                "node": []
            })

        elif "/dkultur" == path:
            nodes.append({
                "path": "stream",
                "name": "Deutschlandfunk Kultur",
                "icon": os.path.join(
                        addon_dir, "resources", "assets", "icon_drk.png"),
                "stream_url": meta['livestreams']['dlf_kultur']['mp3']['high'],
                "type": "music",
                "specialsort": "top"
            })
            nodes.append({
                "path": "podcasts",
                "name": "Podcasts",
                "icon": os.path.join(
                        addon_dir, "resources", "assets", "icon_drk_rss.png"),
                "node": []
            })

        elif "/nova" == path:
            nodes.append({
                "path": "stream",
                "name": "Deutschlandfunk Nova",
                "icon": os.path.join(
                        addon_dir, "resources", "assets", "icon_nova.png"),
                "stream_url": meta['livestreams']['dlf_nova']['mp3']['high'],
                "type": "music",
                "specialsort": "top"
            })
            nodes.append({
                "path": "podcasts",
                "name": "Podcasts",
                "icon": os.path.join(
                        addon_dir, "resources", "assets", "icon_nova_rss.png"),
                "node": []
            })

        for entry in nodes:
            self._add_list_item(entry, path)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _parse_nova(self, path):

        _BASE_URL = "https://www.deutschlandfunknova.de/podcast/"

        # download html site with podcast overview
        _data, _cookies = self._http_request(URL_PODCASTS_NOVA)

        # parse site and read podcast meta data kindly provided as js
        soup = BeautifulSoup(_data, 'html.parser')
        _casts = soup.select('li.item')

        for _cast in _casts:

            _href = _cast.a.get("href")
            _path = _href.replace("/podcasts/download/", "")
            _img = _cast.img

            entry = {
                "path": _path,
                "name": _img.get("alt"),
                "icon": _img.get("src"),
                "params": [
                    {
                        "rss": _BASE_URL + _path
                    }
                ],
                "node": []
            }
            self._add_list_item(entry, path)

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _parse_dlf(self, path, url):

        # download html site with podcast overview
        _data, _cookies = self._http_request(url)

        soup = BeautifulSoup(_data, 'html.parser')
        _js_cast_defs = soup.select('span.abo.dradio-podlove')

        for _def in _js_cast_defs:
            entry = {
                "path": _def["data-buttonid"],
                "name": _def["data-title"],
                "icon": _def["data-logosrc"],
                "params": [
                    {
                        "rss": _def["data-url"]
                    }
                ],
                "node": []
            }
            self._add_list_item(entry, path)

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

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

    def handle(self, argv):

        def decode_param(encoded_param):

            return base64.urlsafe_b64decode(encoded_param).decode("utf-8")

        self.addon_handle = int(argv[1])

        path = urllib.parse.urlparse(argv[0]).path.replace("//", "/")
        splitted_path = path.split("/")
        url_params = urllib.parse.parse_qs(argv[2][1:])

        if "rss" in url_params:
            url = decode_param(url_params["rss"][0])
            self._render_rss(path, url)

        elif "play_latest" in url_params:
            url = decode_param(url_params["play_latest"][0])
            self._play_latest(url)

        elif len(splitted_path) == 3 and splitted_path[2] == "podcasts":
            if splitted_path[1] == "dlf":
                self._parse_dlf(path, URL_PODCASTS_DLF)
            elif splitted_path[1] == "dkultur":
                self._parse_dlf(path, URL_PODCASTS_DLK)
            elif splitted_path[1] == "nova":
                self._parse_nova(path)

        elif len(splitted_path) == 2 and splitted_path[1] != "":
            self._make_station_menu(path)

        else:
            self._make_root_menu()


if __name__ == '__main__':

    mediathek = Mediathek()
    mediathek.handle(sys.argv)
