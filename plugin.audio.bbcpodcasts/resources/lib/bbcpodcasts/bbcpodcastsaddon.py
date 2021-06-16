from resources.lib.rssaddon.abstract_rss_addon import AbstractRssAddon
from resources.lib.rssaddon.http_client import http_request

from bs4 import BeautifulSoup
from datetime import datetime

import os
import re
import urllib.parse

import xbmc
import xbmcplugin
import xbmcgui


class BbcPodcastsAddon(AbstractRssAddon):

    __PLUGIN_ID__ = "plugin.audio.bbcpodcasts"

    BBC_BASE_URL = "https://www.bbc.co.uk"
    PODCASTS_URL = "/podcasts"
    STATION_URL = "/podcasts/%s"
    CATEGORY_URL = "/podcasts/category/%s"

    RSS_URL_PATTERN = "https://podcasts.files.bbci.co.uk/%s.rss"
    PROGRAMS_URL_PATTERN = "/programmes/([^\/]+)/episodes/downloads"
    DURATION_PATTERN = "Duration: ([0-9]+h)? *([0-9]+m)? *([0-9]+s)?"

    _CATEGORY = "category"
    _STATION = "station"

    def __init__(self, addon_handle):

        super().__init__(self.__PLUGIN_ID__, addon_handle)

    def _make_root_menu(self):

        entries = list()
        entries.append({
            "path": "search",
            "name": self.addon.getLocalizedString(32004),
            "icon": os.path.join(
                    self.addon_dir, "resources", "assets", "icon_search.png"),
            "specialsort": "bottom",
            "node": []
        })
        entries.append({
            "path": "editors-picks",
            "name": self.addon.getLocalizedString(32001),
            "icon": os.path.join(
                    self.addon_dir, "resources", "assets", "icon_selection.png"),
            "specialsort": "top",
            "node": []
        })
        categories_n_stations = self._get_entries_for_categories_stations()
        entries += categories_n_stations[self._CATEGORY]
        entries += categories_n_stations[self._STATION]

        for entry in entries:
            self.add_list_item(entry, "")

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _make_menu(self, path, page=None, query=None):

        splitted_path = path.split("/")
        if splitted_path[1] == "category":
            url = self.CATEGORY_URL % splitted_path[2]
        elif splitted_path[1] == "station":
            url = self.STATION_URL % splitted_path[2]
        else:
            url = self.PODCASTS_URL

        entries = self._get_podcasts(url, page, query)
        for entry in entries:
            self.add_list_item(entry, path)

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _make_editors_picks(self, path):

        _data, _cookies = http_request(self.addon,
                                       "%s%s" % (self.BBC_BASE_URL, self.PODCASTS_URL))
        soup = BeautifulSoup(_data, 'html.parser')

        for _pick in list(filter(lambda h2: h2.text == "Editors Picks", soup.select("h2.grid-unit"))):
            for _podcast in _pick.parent.select("div.podcast"):
                self.add_list_item(
                    self._parse_podcast_tile(_podcast, latest=True), path)

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _get_podcasts(self, url, page=None, query=None):

        def _parse_pager(soup, direction="next"):
            pager = soup.select("li.pgn__page--%s>a" % direction)
            if len(pager) == 1:
                m = re.match("\?.*page=([0-9]+).*", pager[0]["href"])
                return m.group(1) if m else "1"
            else:
                return None

        params = list()
        if page:
            params.append("page=%s" % page)
        if query:
            params.append("q=%s" % urllib.parse.quote(query))

        _url_param = "?%s" % "&".join(params) if len(params) > 0 else ""

        _data, _cookies = http_request(self.addon, "%s%s%s" % (
            self.BBC_BASE_URL, url, _url_param))
        soup = BeautifulSoup(_data, 'html.parser')

        entries = list()

        for _podcast in soup.select("div.podcast"):
            entries.append(
                self._parse_podcast_tile(_podcast, latest=False))

        pager_next = _parse_pager(soup, "next")
        if pager_next:
            _params = [
                {
                    "page": pager_next,
                }
            ]
            if query:
                _params.append({
                    "query": query,
                })

            entries.append({
                "path": "",
                "name": self.addon.getLocalizedString(32003) % pager_next,
                "icon": os.path.join(
                    self.addon_dir, "resources", "assets", "icon_arrow_right.png"),
                "specialsort": "bottom",
                "params": _params,
                "node": []
            })

        return entries

    def _get_entries_for_categories_stations(self):

        _data, _cookies = http_request(self.addon,
                                       "%s%s" % (self.BBC_BASE_URL, self.PODCASTS_URL))
        soup = BeautifulSoup(_data, 'html.parser')

        result = {
            self._CATEGORY: list(),
            self._STATION: list()
        }

        for _type in list(filter(lambda h3: h3.text in ["Stations", "Categories"], soup.select("h3.pc-filter__section-heading"))):
            for _entry in _type.parent.parent.select("a.pc-filter__link"):

                _splitted_path = _entry["href"].split("/")
                station_or_category = self._CATEGORY if _splitted_path[-2] == self._CATEGORY else self._STATION
                _path = "/%s/%s" % (station_or_category, _splitted_path[-1])

                result[station_or_category].append({
                    "path": _path,
                    "name": _entry.text,
                    "icon": os.path.join(
                        self.addon_dir, "resources", "assets", "icon_category.png" if _splitted_path[-2] == self._CATEGORY else "icon_station.png"),
                    "node": []
                })

        return result

    def _parse_podcast_tile(self, tile, latest=False):

        # url for rss
        _href = tile.find("a")["href"]
        m = re.match(self.PROGRAMS_URL_PATTERN, _href)
        if not m:
            return None

        _rss = self.RSS_URL_PATTERN % m.group(1)
        _title = " ".join(tile.find("h3").stripped_strings)
        _description = " ".join(tile.select(
            "p.podcast__description")[0].stripped_strings)
        _img = tile.select("img")[0]["src"]
        _author = " ".join(tile.find("h4").stripped_strings)

        _duration = " ".join(tile.select(
            "li.podcast-duration")[0].stripped_strings)
        _d = list(re.match(self.DURATION_PATTERN, _duration).groups())
        _secs = int(_d[0][:-1]) * 3600 if _d[0] else 0 + int(_d[1][:-1]
                                                             ) * 60 if _d[1] else 0 + int(_d[2][:-1]) if _d[2] else 0

        entry = {
            "path": m.group(1),
            "name": _title,
            "description": _description,
            "icon": "https:%s" % _img,
            "type": "music",
            "duration": _secs,
            "author": _author,
            "params": [
                {
                    "play_latest" if latest else "rss": _rss
                }
            ]
        }
        if not latest:
            entry["node"] = []

        return entry

    def search(self, path):

        query = xbmcgui.Dialog().input(heading=self.addon.getLocalizedString(32004),
                                       type=xbmcgui.INPUT_ALPHANUM)
        if query != "":
            self._make_menu(path, query=query)

    def check_disclaimer(self):

        if self.addon.getSetting("agreement") != "1":
            answer = xbmcgui.Dialog().yesno(self.addon.getLocalizedString(32005),
                                            self.addon.getLocalizedString(32010))

            if answer:
                self.addon.setSetting("agreement", "1")
                return True
            else:
                return False

        else:
            return True

    def route(self, path, url_params):

        splitted_path = path.split("/")
        if len(splitted_path) == 2 and splitted_path[1] == "search":
            self.search(path)

        elif len(splitted_path) == 2 and splitted_path[1] == "editors-picks":
            self._make_editors_picks(path)

        elif path in ["/", "/category/", "/station/"]:
            self._make_root_menu()

        else:
            page = self.decode_param(
                url_params["page"][0]) if "page" in url_params else None
            query = self.decode_param(
                url_params["query"][0]) if "query" in url_params else None

            self._make_menu(path, page=page, query=query)
