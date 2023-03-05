import json
import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup
from resources.lib.rssaddon.abstract_rss_addon import AbstractRssAddon
from resources.lib.rssaddon.http_client import http_request
from resources.lib.rssaddon.http_status_error import HttpStatusError


class DeutschlandfunkAddon(AbstractRssAddon):

    __PLUGIN_ID__ = "plugin.audio.deutschlandfunk"

    URL_STREAMS_RPC = "https://srv.deutschlandradio.de/config-feed.2828.de.rpc"

    URL_PODCASTS_DLF = "https://www.deutschlandfunk.de/podcasts"
    URL_PODCASTS_DFK = "https://www.deutschlandfunkkultur.de/program-and-podcast"
    URL_PODCASTS_NOVA = "https://www.deutschlandfunknova.de/podcasts"

    PATH_DLF = "dlf"
    PATH_DLK = "dkultur"
    PATH_NOVA = "nova"
    PATH_PODCASTS = "podcasts"

    addon = xbmcaddon.Addon(id=__PLUGIN_ID__)

    def __init__(self, addon_handle):

        super().__init__(addon_handle)

    def _make_root_menu(self):

        nodes = [
            {
                "path": DeutschlandfunkAddon.PATH_DLF,
                "name": "Deutschlandfunk",
                "icon": os.path.join(
                    self.addon_dir, "resources", "assets", "icon_dlf.png"),
                "node": []
            },
            {
                "path": DeutschlandfunkAddon.PATH_DLK,
                "name": "Deutschlandfunk Kultur",
                "icon": os.path.join(
                    self.addon_dir, "resources", "assets", "icon_drk.png"),
                "node": []
            },
            {
                "path": DeutschlandfunkAddon.PATH_NOVA,
                "name": "Deutschlandfunk Nova",
                "icon": os.path.join(
                    self.addon_dir, "resources", "assets", "icon_nova.png"),
                "node": []
            }
        ]

        for entry in nodes:
            self.add_list_item(entry, "/")

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _make_station_menu(self, station):

        try:
            _json, _cookies = http_request(self.addon, self.URL_STREAMS_RPC)
            meta = json.loads(_json)

        except HttpStatusError as error:
            xbmc.log("HTTP Status Error: %s, station=%s" %
                     (error.message, station), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(self.addon.getLocalizedString(32151), error.message)
            return

        nodes = list()
        if DeutschlandfunkAddon.PATH_DLF == station:
            nodes.append({
                "path": "stream",
                "name": "Deutschlandfunk",
                "icon": os.path.join(
                        self.addon_dir, "resources", "assets", "icon_dlf.png"),
                "stream_url": meta['livestreams']['dlf']['mp3']['high'],
                "type": "music",
                "specialsort": "top"
            })
            nodes.append({
                "path": DeutschlandfunkAddon.PATH_PODCASTS,
                "name": "Podcasts",
                "icon": os.path.join(
                        self.addon_dir, "resources", "assets", "icon_dlf_rss.png"),
                "node": []
            })

        elif DeutschlandfunkAddon.PATH_DLK == station:
            nodes.append({
                "path": "stream",
                "name": "Deutschlandfunk Kultur",
                "icon": os.path.join(
                        self.addon_dir, "resources", "assets", "icon_drk.png"),
                "stream_url": meta['livestreams']['dlf_kultur']['mp3']['high'],
                "type": "music",
                "specialsort": "top"
            })
            nodes.append({
                "path": DeutschlandfunkAddon.PATH_PODCASTS,
                "name": "Podcasts",
                "icon": os.path.join(
                        self.addon_dir, "resources", "assets", "icon_drk_rss.png"),
                "node": []
            })

        elif DeutschlandfunkAddon.PATH_NOVA == station:
            nodes.append({
                "path": "stream",
                "name": "Deutschlandfunk Nova",
                "icon": os.path.join(
                        self.addon_dir, "resources", "assets", "icon_nova.png"),
                "stream_url": meta['livestreams']['dlf_nova']['mp3']['high'],
                "type": "music",
                "specialsort": "top"
            })
            nodes.append({
                "path": DeutschlandfunkAddon.PATH_PODCASTS,
                "name": "Podcasts",
                "icon": os.path.join(
                        self.addon_dir, "resources", "assets", "icon_nova_rss.png"),
                "node": []
            })

        for entry in nodes:
            self.add_list_item(entry, "/%s" % station)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _parse_nova(self, path):

        _BASE_URL = "https://www.deutschlandfunknova.de/podcast/"

        # download html site with podcast overview
        _data, _cookies = http_request(self.addon, self.URL_PODCASTS_NOVA)

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
            self.add_list_item(entry, path)

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _parse_dlf(self, path, url):

        # download html site with podcast overview
        _data, _cookies = http_request(self.addon, url)

        soup = BeautifulSoup(_data, "html.parser")
        main = soup.find("main")
        _script_js_client_queries = main.find_all(
            "script", class_="js-client-queries")

        entries = list()
        _img_src = None

        for _script in _script_js_client_queries:

            if not _script.has_attr("data-json"):
                continue

            try:
                _data_json = json.loads(_script["data-json"])
                if "value" not in _data_json or "__typename" not in _data_json["value"]:
                    continue

                if _data_json["value"]["__typename"] == "Image":
                    _img_src = _data_json["value"]["src"]

                elif _data_json["value"]["__typename"] == "Teaser" and "pathPodcast" in _data_json["value"]:
                    if not _data_json["value"]["pathPodcast"] or not _data_json["value"]["pathPodcast"].endswith(".xml"):
                        continue

                    entry = {
                        "path": _data_json["value"]["sophoraId"],
                        "name": _data_json["value"]["title"],
                        "icon": _img_src,
                        "params": [
                            {
                                "rss": _data_json["value"]["pathPodcast"]
                            }
                        ],
                        "node": []
                    }
                    entries.append(entry)

            except:
                _img_src = None

        uniq_entries = {entries[i]["params"][0]["rss"]: entries[i] for i in range(len(entries))}
        uniq_entries = [uniq_entries[e] for e in uniq_entries]
        uniq_entries.sort(key=lambda e: e["name"])

        for entry in uniq_entries:
            self.add_list_item(entry, path)

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def route(self, path, url_params):

        splitted_path = [n for n in path.split("/") if n != ""]
        if len(splitted_path) == 2 and splitted_path[1] == DeutschlandfunkAddon.PATH_PODCASTS:

            if splitted_path[0] == DeutschlandfunkAddon.PATH_DLF:
                self._parse_dlf(path, self.URL_PODCASTS_DLF)

            elif splitted_path[0] == DeutschlandfunkAddon.PATH_DLK:
                self._parse_dlf(path, self.URL_PODCASTS_DFK)

            elif splitted_path[0] == DeutschlandfunkAddon.PATH_NOVA:
                self._parse_nova(path)

        elif len(splitted_path) == 1 and splitted_path[0] in [DeutschlandfunkAddon.PATH_DLF, DeutschlandfunkAddon.PATH_DLK, DeutschlandfunkAddon.PATH_NOVA]:
            self._make_station_menu(splitted_path[0])

        else:
            self._make_root_menu()
