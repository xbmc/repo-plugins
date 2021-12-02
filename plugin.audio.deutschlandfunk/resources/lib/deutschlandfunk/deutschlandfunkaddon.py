import json
import os
import re

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
    URL_PODCASTS_DLK = "https://www.deutschlandfunkkultur.de/program-and-podcast"
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

        soup = BeautifulSoup(_data, 'html.parser')
        _div_podcast_teasers = soup.select('div.b-podcast-teaser')

        for _teaser in _div_podcast_teasers:
            try:
                _img = _teaser.findChild("img")["src"]
                _name = _teaser.findChild("h4").text
                _rss = _teaser.find_all("a", class_=["is-rss"])[0]["href"]
                m = re.match(r"^.*([^/]+)\.xml$", _rss)
                if m:
                    entry = {
                        "path": m.groups()[0],
                        "name": _name,
                        "icon": _img,
                        "params": [
                            {
                                "rss": _rss
                            }
                        ],
                        "node": []
                    }
                    self.add_list_item(entry, path)

            except:
                pass

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _parse_drk(self, path, url):

        # download html site with podcast overview
        _data, _cookies = http_request(self.addon, url)

        soup = BeautifulSoup(_data, 'html.parser')
        _div_podcast_teasers = soup.select('div.b-teaser-podcast')

        for _teaser in _div_podcast_teasers:
            try:
                _img = _teaser.findChild("img")["src"]
                _name = _teaser.findChild("h3").text
                _rss = _teaser.find_all("a", class_=["is-rss"])[0]["href"]
                m = re.match(r"^.*([^/]+)\.xml$", _rss)
                if m:
                    entry = {
                        "path": m.groups()[0],
                        "name": _name,
                        "icon": _img,
                        "params": [
                            {
                                "rss": _rss
                            }
                        ],
                        "node": []
                    }
                    self.add_list_item(entry, path)

            except:
                pass

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def route(self, path, url_params):

        splitted_path = list(filter(lambda n: n != "", path.split("/")))
        if len(splitted_path) == 2 and splitted_path[1] == DeutschlandfunkAddon.PATH_PODCASTS:

            if splitted_path[0] == DeutschlandfunkAddon.PATH_DLF:
                self._parse_dlf(path, self.URL_PODCASTS_DLF)

            elif splitted_path[0] == DeutschlandfunkAddon.PATH_DLK:
                self._parse_drk(path, self.URL_PODCASTS_DLK)

            elif splitted_path[0] == DeutschlandfunkAddon.PATH_NOVA:
                self._parse_nova(path)

        elif len(splitted_path) == 1 and splitted_path[0] in [DeutschlandfunkAddon.PATH_DLF, DeutschlandfunkAddon.PATH_DLK, DeutschlandfunkAddon.PATH_NOVA]:
            self._make_station_menu(splitted_path[0])

        else:
            self._make_root_menu()
