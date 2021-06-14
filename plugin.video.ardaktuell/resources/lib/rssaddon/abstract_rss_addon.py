from datetime import datetime
from resources.lib.rssaddon.http_status_error import HttpStatusError
from resources.lib.rssaddon.http_client import http_request

import base64
import os
import re
import urllib.parse
import xmltodict

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

# see https://forum.kodi.tv/showthread.php?tid=112916
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May",
           "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class AbstractRssAddon:

    addon = None
    addon_handle = None
    plugin_id = None
    addon_dir = None
    anchor_for_latest = True

    def __init__(self, plugin_id, addon_handle):

        self.plugin_id = plugin_id
        self.addon = xbmcaddon.Addon(id=plugin_id)
        self.addon_handle = addon_handle
        self.addon_dir = xbmcvfs.translatePath(self.addon.getAddonInfo('path'))

    def handle(self, argv):

        path = urllib.parse.urlparse(argv[0]).path.replace("//", "/")
        url_params = urllib.parse.parse_qs(argv[2][1:])

        if not self.check_disclaimer():
            path = "/"
            url_params = list()

        if "rss" in url_params:
            url = self.decode_param(url_params["rss"][0])
            self.render_rss(path, url)

        elif "play_latest" in url_params:
            url = self.decode_param(url_params["play_latest"][0])
            self.play_latest(url)
        else:
            self.route(path, url_params)

    def decode_param(self, encoded_param):

        return base64.urlsafe_b64decode(encoded_param).decode("utf-8")

    def check_disclaimer(self):

        return True

    def route(self, path, url_params):

        pass

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

        res, cookies = http_request(self.addon, url)

        if not res.startswith("<?xml"):
            raise HttpStatusError("%s %s" % (
                self.addon.getLocalizedString(32155), url))

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

        self.on_rss_loaded(url, title, description, image, items)

        return title, description, image, items

    def on_rss_loaded(self, url, title, description, image, items):

        pass

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

    def add_list_item(self, entry, path):

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
                ["plugin://", self.plugin_id, item_path, param_string])

        is_folder = "node" in entry
        li.setProperty("IsPlayable", "false" if is_folder else "true")

        xbmcplugin.addDirectoryItem(handle=self.addon_handle,
                                    listitem=li,
                                    url=url,
                                    isFolder=is_folder)

    def render_rss(self, path, url):

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
                    "date": datetime.now(),
                    "specialsort": "top",
                    "type": items[0]["type"],
                    "params": [
                        {
                            "play_latest": url
                        }
                    ]
                }
                self.add_list_item(entry, path)

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

    def play_latest(self, url):

        try:
            title, description, image, items = self._load_rss(url)
            item = items[0]
            li = self._create_list_item(item)
            xbmcplugin.setResolvedUrl(self.addon_handle, True, li)

        except HttpStatusError as error:

            xbmcgui.Dialog().notification(self.addon.getLocalizedString(32151), error.message)
