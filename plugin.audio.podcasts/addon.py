from datetime import datetime
import base64
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

__PLUGIN_ID__ = "plugin.audio.podcasts"

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

    _GROUPS = 10
    _ENTRIES = 10

    _menu = None

    addon_handle = None

    def __init__(self):

        groups = []

        # build opml feeds
        for g in range(self._GROUPS):

            if settings.getSetting("opml_file_%i" % g) == "":
                continue

            path = os.path.join(
                addon_dir, settings.getSetting("opml_file_%i" % g))
            opml_data = self._load_opml(path)
            try:
                entries = []
                for o in opml_data["opml"]["body"]["outline"]:
                    if o["@type"] == "rss":
                        entries += [{
                            "path": "%i/%i" % (g, len(entries)),
                            "name": o["@title"],
                            "params": [
                                {
                                    "rss": o["@xmlUrl"]
                                }
                            ],
                            "node": []
                        }]

                groups += [{
                    "path": "opml-%i" % g,
                    "name": opml_data["opml"]["head"]["title"],
                    "node": entries
                }]

            except:
                xbmc.log("Cannot parse opml file %s" % path, xbmc.LOGERROR)
                pass

        # build groups acc. settings
        for g in range(self._GROUPS):

            if settings.getSetting("group_%i_enable" % g) == "false":
                continue

            entries = []
            for e in range(self._ENTRIES):

                if settings.getSetting("group_%i_rss_%i_enable" % (g, e)) == "false":
                    continue

                icon = settings.getSetting("group_%i_rss_%i_icon"
                                           % (g, e))

                entries += [{
                    "path": "%i" % e,
                    "name": settings.getSetting("group_%i_rss_%i_name"
                                                % (g, e)),
                    "params": [
                        {
                            "rss": settings.getSetting("group_%i_rss_%i_url" % (g, e))
                        }
                    ],
                    "icon": icon,
                    "node": []
                }]

            groups += [{
                "path": "pod-%i" % g,
                "name": settings.getSetting("group_%i_name" % g),
                "node": entries
            }]

        self._menu = [
            {  # root
                "path": "",
                "node": groups
            }
        ]

    def _play_latest(self, url):

        try:
            title, description, image, items = self._load_rss(url)
            item = items[0]
            li = self._create_list_item(item)
            xbmcplugin.setResolvedUrl(self.addon_handle, True, li)

        except HttpStatusError as error:

            xbmcgui.Dialog().notification("HTTP Status Error", error.message)

    def _create_list_item(self, item):

        li = xbmcgui.ListItem(label=item["name"])

        if "name2" in item:
            li.setProperty("label2", item["name2"])

        if "stream_url" in item and "type" in item:
            li.setPath(item["stream_url"])
            li.setInfo(item["type"], {})

        if "icon" in item and item["icon"]:
            li.setArt({"icon": item["icon"]})
        else:
            li.setArt({"icon": os.path.join(
                addon_dir, "resources", "assets", "icon.png")}
            )

        if "date" in item and item["date"]:
            li.setDateTime(item["date"].strftime("%Y-%m-%dT%H:%M:%SZ"))

        return li

    def _add_list_item(self, entry, path, playable=False):

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

        is_folder = "node" in entry
        if not is_folder and playable:
            li.setProperty("IsPlayable", "true")

        xbmcplugin.addDirectoryItem(handle=self.addon_handle,
                                    listitem=li,
                                    url="".join(
                                        ["plugin://", __PLUGIN_ID__, item_path, param_string]),
                                    isFolder=is_folder)

    def _load_opml(self, path):

        try:
            with open(path) as _opml_file:
                _data = _opml_file.read()
                return xmltodict.parse(_data)
        except:
            xbmc.log("Cannot open opml file", xbmc.LOGERROR)
            return None

    def _load_rss(self, url):

        def _parse_item(_ci):

            if "enclosure" in _ci and "@url" in _ci["enclosure"]:
                stream_url = _ci["enclosure"]["@url"]
                _type = _ci["enclosure"]["@type"].split("/")[0]
            elif "guid" in _ci and _ci["guid"]:
                # not supported yet
                return None
            else:
                return None

            if "itunes:image" in _ci and "@href" in _ci["itunes:image"]:
                item_image = _ci["itunes:image"]["@href"]
            else:
                item_image = image

            if "pubDate" in _ci:
                _f = re.findall(
                    "(\d{1,2}) (\w{3}) (\d{4}) (\d{2}):(\d{2}):(\d{2})", _ci["pubDate"])

                if _f:
                    _m = _MONTHS.index(_f[0][1]) + 1
                    pubDate = datetime(year=int(_f[0][2]), month=_m, day=int(_f[0][0]), hour=int(
                        _f[0][3]), minute=int(_f[0][4]), second=int(_f[0][5]))

                else:
                    pubDate = None

            return {
                "name": _ci["title"],
                "name2": _ci["description"] if "description" in _ci else "",
                "date": pubDate,
                "icon": item_image,
                "stream_url": stream_url,
                "type": _type
            }

        res = requests.get(url)
        if res.status_code == 200 and res.text.startswith("<?xml"):
            rss_feed = xmltodict.parse(res.text)

        elif res.status_code != 200:
            raise HttpStatusError(
                "Unexpected HTTP Status %i for podcast %s" % (res.status_code, url))

        else:
            raise HttpStatusError("Unexpected content for podcast %s" % url)

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
        if type(channel["item"]) is list:
            for _ci in channel["item"]:
                item = _parse_item(_ci)
                if item is not None:
                    items += [item]

        else:
            item = _parse_item(channel["item"])
            if item is not None:
                items += [item]

        return title, description, image, items

    def _render_rss(self, path, url):

        def _update_Image(path, image):

            if path.startswith("/pod-"):
                _p = path[5:].split("/")
                settings.setSetting("group_%i_rss_%i_icon" %
                                    (int(_p[0]), int(_p[1])), image)

        try:
            title, description, image, items = self._load_rss(url)
            if image:
                _update_Image(path, image)

        except HttpStatusError as error:
            xbmc.log("HTTP Status Error: %s, path=%s" %
                     (error.message, path), xbmc.LOGERROR)
            xbmcgui.Dialog().notification("HTTP Status Error", error.message)
            items = []

        if len(items) > 0:
            entry = {
                "path": "latest",
                "name": title,
                "name2": description,
                "icon": image,
                "date": datetime.now(),
                "params": [
                    {
                        "play_latest": url
                    }
                ]
            }
            self._add_list_item(entry, path, playable=True)

        for item in items:
            li = self._create_list_item(item)
            xbmcplugin.addDirectoryItem(handle=self.addon_handle,
                                        listitem=li,
                                        url=item["stream_url"],
                                        isFolder=False)
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

        xbmcplugin.endOfDirectory(self.addon_handle)

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
