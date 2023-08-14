import base64
import os
import re
import urllib.parse
from datetime import datetime
from io import StringIO
from xml.etree.ElementTree import iterparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
from resources.lib.rssaddon.http_client import http_request
from resources.lib.rssaddon.http_status_error import HttpStatusError

# see https://forum.kodi.tv/showthread.php?tid=112916
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May",
           "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class AbstractRssAddon:

    addon = None
    addon_handle = None
    addon_dir = None
    anchor_for_latest = True

    def __init__(self, addon_handle):

        self.addon = xbmcaddon.Addon()
        self.addon_handle = addon_handle
        self.addon_dir = xbmcvfs.translatePath(self.addon.getAddonInfo('path'))

        self.params = dict()

    def handle(self, argv: 'list[str]') -> None:

        path = urllib.parse.urlparse(argv[0]).path.replace("//", "/")
        url_params = urllib.parse.parse_qs(argv[2][1:])

        if not self.check_disclaimer():
            self.route("/", dict())
            return

        self.params = {key: self.decode_param(
            url_params[key][0]) for key in url_params}

        if "rss" in self.params:
            url = self.params["rss"]
            limit = int(self.params["limit"]
                        ) if "limit" in self.params else 0
            offset = int(self.params["offset"]
                         ) if "offset" in self.params else 0
            self.render_rss(path, url, limit=limit, offset=offset)

        elif "play_latest" in self.params:
            url = self.params["play_latest"]
            self.play_latest(url)
        else:
            self.route(path)

    def decode_param(self, encoded_param: str) -> str:

        return base64.urlsafe_b64decode(encoded_param).decode("utf-8")

    def check_disclaimer(self) -> bool:

        return True

    def route(self, path: str):

        pass

    def is_force_http(self) -> bool:

        return False

    def _load_rss(self, url: str) -> 'tuple[str,str,str,list[dict]]':

        def parse_rss_feed(xml: str) -> 'tuple[str,str,str,list[dict]]':

            path = list()

            title = None
            description = ""
            image = None
            items = list()

            for event, elem in iterparse(StringIO(xml), ("start", "end")):

                if event == "start":
                    path.append(elem.tag)

                    if path == ["rss", "channel", "item"]:
                        item = dict()

                elif event == "end":

                    if path == ["rss", "channel"]:
                        pass

                    elif path == ["rss", "channel", "title"] and elem.text:
                        title = elem.text.strip()

                    elif path == ["rss", "channel", "description"] and elem.text:
                        description = elem.text.strip()

                    elif path == ["rss", "channel", "image", "url"] and elem.text:
                        image = elem.text.strip()

                    elif (path == ["rss", "channel", "{http://www.itunes.com/dtds/podcast-1.0.dtd}image"]
                            and "href" in elem.attrib and not image):
                        image = elem.attrib["href"]

                    elif path == ["rss", "channel", "item", "title"] and elem.text:
                        item["name"] = elem.text.strip()

                    elif path == ["rss", "channel", "item", "description"] and elem.text:
                        item["description"] = elem.text.strip()

                    elif path == ["rss", "channel", "item", "enclosure"]:
                        item["stream_url"] = elem.attrib["url"] if not self.is_force_http(
                        ) else elem.attrib["url"].replace("https://", "http://")
                        item["type"] = "video" if elem.attrib["type"].split(
                            "/")[0] == "video" else "music"

                    elif (path == ["rss", "channel", "item", "{http://www.itunes.com/dtds/podcast-1.0.dtd}image"]
                            and elem.attrib["href"]):
                        item["icon"] = elem.attrib["href"]

                    elif path == ["rss", "channel", "item", "pubDate"] and elem.text:
                        _f = re.findall(
                            "(\d{1,2}) (\w{3}) (\d{4}) (\d{2}):(\d{2}):(\d{2})", elem.text)

                        if _f:
                            _m = _MONTHS.index(_f[0][1]) + 1
                            item["date"] = datetime(year=int(_f[0][2]), month=_m, day=int(_f[0][0]), hour=int(
                                _f[0][3]), minute=int(_f[0][4]), second=int(_f[0][5]))

                    elif path == ["rss", "channel", "item", "{http://www.itunes.com/dtds/podcast-1.0.dtd}duration"] and elem.text:
                        try:
                            duration = 0
                            for i, s in enumerate(reversed(elem.text.split(":"))):
                                duration += 60**i * int(s)

                            item["duration"] = duration

                        except:
                            pass

                    elif path == ["rss", "channel", "item"]:

                        if "description" not in item:
                            item["description"] = ""

                        if "icon" not in item:
                            item["icon"] = image

                        if "stream_url" in item and item["stream_url"]:
                            items.append(item)

                    elem.clear()
                    path.pop()

            return title, description, image, items

        xml, cookies = http_request(self.addon, url)

        if not xml.startswith("<?xml") and not xml.startswith("<rss"):
            raise HttpStatusError("%s %s" % (
                self.addon.getLocalizedString(32155), url))

        title, description, image, items = parse_rss_feed(xml=xml)

        self.on_rss_loaded(url, title, description, image, items)

        return title, description, image, items

    def on_rss_loaded(self, url: str, title: str, description: str, image: str, items: 'list[dict]') -> None:

        pass

    def build_label(self, item) -> str:

        return item["name"]

    def build_plot(self, item) -> str:

        return item["description"] if "description" in item else ""

    def build_url(self, item) -> str:

        return item["stream_url"]

    def _create_list_item(self, item: dict) -> xbmcgui.ListItem:

        li = xbmcgui.ListItem(label=self.build_label(item))

        if "description" in item:
            li.setProperty("label2", item["description"])

        if "stream_url" in item:
            li.setPath(self.build_url(item))

        if "type" in item:
            infos = {
                "title": self.build_label(item)
            }

            if item["type"] == "video":
                infos["plot"] = self.build_plot(item)

            if "duration" in item and item["duration"] >= 0:
                infos["duration"] = item["duration"]

            li.setInfo(item["type"], infos)

        if "icon" in item and item["icon"]:
            li.setArt({"thumb": item["icon"]})
        else:
            addon_dir = xbmcvfs.translatePath(self.addon.getAddonInfo('path'))
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

    def add_list_item(self, entry: dict, path: str) -> None:

        def _build_param_string(params: 'list[str]', current="") -> str:

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
            url = self.build_url(entry)

        else:
            url = "".join(
                ["plugin://", self.addon.getAddonInfo("id"), item_path, param_string])

        is_folder = "node" in entry
        li.setProperty("IsPlayable", "false" if is_folder else "true")

        xbmcplugin.addDirectoryItem(handle=self.addon_handle,
                                    listitem=li,
                                    url=url,
                                    isFolder=is_folder)

    def render_rss(self, path: str, url: str, limit=0, offset=0) -> None:

        try:
            title, description, image, items = self._load_rss(url)

        except HttpStatusError as error:
            xbmc.log("HTTP Status Error: %s, path=%s" %
                     (error.message, path), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(32151), error.message)

        else:
            if len(items) > 0 and self.anchor_for_latest:
                entry = {
                    "path": "latest",
                    "name": "%s (%s)" % (title, self.addon.getLocalizedString(32101)),
                    "description": description,
                    "icon": image,
                    "specialsort": "top",
                    "type": items[0]["type"],
                    "params": [
                        {
                            "play_latest": url
                        }
                    ]
                }
                self.add_list_item(entry, path)

            li = None
            for i, item in enumerate(items):
                if i >= offset and (not limit or i < offset + limit):
                    li = self._create_list_item(item)
                    xbmcplugin.addDirectoryItem(handle=self.addon_handle,
                                                listitem=li,
                                                url=self.build_url(item),
                                                isFolder=False)

            if li and "setDateTime" in dir(li):  # available since Kodi v20
                xbmcplugin.addSortMethod(
                    self.addon_handle, xbmcplugin.SORT_METHOD_DATE)
            xbmcplugin.endOfDirectory(self.addon_handle)

    def play_latest(self, url: str) -> None:

        try:
            title, description, image, items = self._load_rss(url)
            item = items[0]
            li = self._create_list_item(item)
            xbmcplugin.setResolvedUrl(self.addon_handle, True, li)

        except HttpStatusError as error:

            xbmcgui.Dialog().notification(self.addon.getLocalizedString(32151), error.message)
