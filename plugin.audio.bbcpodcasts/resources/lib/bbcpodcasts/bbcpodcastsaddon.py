import json
import os
import re

import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup
from resources.lib.rssaddon.abstract_rss_addon import AbstractRssAddon
from resources.lib.rssaddon.http_client import http_request


class BbcPodcastsAddon(AbstractRssAddon):

    BBC_BASE_URL = "https://www.bbc.co.uk"
    PODCASTS_URL = "/sounds/podcasts"

    RSS_URL_PATTERN = "https://podcasts.files.bbci.co.uk/%s.rss"

    def __init__(self, addon_handle) -> None:

        super().__init__(addon_handle)

    def _make_root_menu(self) -> None:

        entries = list()
        entries += self._get_entries_for_categories()

        for entry in entries:
            self.add_list_item(entry, "")

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=True)

    def _make_menu(self, path: str, page=None) -> None:

        if path.endswith("/"):
            path = path[:-1]

        entries = self._get_podcasts(path, page)
        for entry in entries:
            self.add_list_item(entry, path)

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _get_podcasts(self, url: str, page=None) -> 'list[dict]':

        def _parse_pager(soup: BeautifulSoup) -> int:

            navs = soup.find_all("nav", attrs={"aria-label" : "Page Navigation"})
            if len(navs) == 1:
                lis = navs[0].find_all("li")
                if len(lis) > 0:
                    if lis[-1].a:
                        m = re.match(".*page=([0-9]+).*", lis[-1].a["href"])
                        return m.group(1) if m else None

            return None

        params = list()
        params.append("sort=title")
        if page:
            params.append("page=%s" % page)

        _url_param = "?%s" % "&".join(params) if len(params) > 0 else ""

        _data, _cookies = http_request(self.addon, "%s%s%s" % (
            self.BBC_BASE_URL, url, _url_param))
        soup = BeautifulSoup(_data, 'html.parser')

        entries = list()
        for _tile in soup.select("article"):
            entry = self._parse_podcast_tile(_tile)
            if entry:
                entries.append(entry)

        pager_next = _parse_pager(soup)
        if pager_next:
            _params = [
                {
                    "page": pager_next,
                }
            ]

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

    def _get_entries_for_categories(self) -> 'list[dict]':

        _data, _cookies = http_request(self.addon,
                                       "%s%s" % (self.BBC_BASE_URL, self.PODCASTS_URL))

        soup = BeautifulSoup(_data, 'html.parser')
        _json = None
        for _script in soup.select("script"):
            if "__PRELOADED_STATE__" not in str(_script):
                continue

            _s = str(_script).replace(
                "<script> window.__PRELOADED_STATE__ = ", "")
            _s = _s.replace("; </script>", "")
            _json = json.loads(_s)

        if not _json:
            return list()

        result = list()

        for _d in _json["modules"]["data"]:

            if "title" not in _d or not "controls" in _d or not _d["controls"] or not "navigation" in _d["controls"] or _d["controls"]["navigation"]["id"] != "see_more":
                continue

            _name = _d["title"]
            _path = _d["controls"]["navigation"]["target"]["urn"]
            _data = "data" in _d and type(_d["data"]) == list

            if _path and _name and _data:
                result.append({
                    "path": "%s/%s" % (self.PODCASTS_URL, _path.split(":")[-1]),
                    "name": _name,
                    "icon": os.path.join(self.addon_dir, "resources", "assets", "icon_category.png"),
                    "node": []
                })

        return result

    def _parse_podcast_tile(self, tile) -> dict:

        _more_episodes = tile.select("a.more-episodes")
        if len(_more_episodes) != 1:
            return None

        _bid = json.loads(_more_episodes[0]["data-bbc-metadata"])["BID"]
        _title = re.sub(" +", " ", tile.span.text).replace("\n", "").strip()
        _img = tile.a.div.img["src"]

        entry = {
            "path": _bid,
            "name": _title,
            "icon": _img,
            "type": "music",
            "params": [
                {
                    "rss": self.RSS_URL_PATTERN % _bid
                }
            ],
            "node": []
        }

        return entry

    def check_disclaimer(self) -> bool:

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

    def route(self, path: str, url_params: 'dict[str]') -> None:

        splitted_path = path.split("/")

        if path in ["/"]:
            self._make_root_menu()

        elif len(splitted_path) in [4, 5] and path.startswith(self.PODCASTS_URL):
            page = self.decode_param(
                url_params["page"][0]) if "page" in url_params else None

            self._make_menu(path, page=page)
