import json
import os
import re

import xbmc
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup
from resources.lib.rssaddon.abstract_rss_addon import AbstractRssAddon
from resources.lib.rssaddon.http_client import http_request


class BbcPodcastsAddon(AbstractRssAddon):

    BBC_BASE_URL = "https://www.bbc.co.uk"
    PODCASTS_URL = "/sounds/podcasts"

    RSS_URL_PATTERN = "https://podcasts.files.bbci.co.uk/%s.rss"

    def __init__(self, addon_handle):

        super().__init__(addon_handle)

    def _make_root_menu(self):

        entries = list()
        entries += self._get_entries_for_categories()

        for entry in entries:
            self.add_list_item(entry, "")

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=True)

    def _make_menu(self, path, page=None):

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

    def _get_podcasts(self, url, page=None):

        def _parse_pager(soup):

            navs = soup.select("nav")
            if len(navs) == 3:
                lis = navs[2].find_all("li")
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

    def _get_entries_for_categories(self):

        _data, _cookies = http_request(self.addon,
                                       "%s%s" % (self.BBC_BASE_URL, self.PODCASTS_URL))
        soup = BeautifulSoup(_data, 'html.parser')

        result = list()
        for _h3 in soup.select("h3"):
            for _footer in _h3.parent.parent.select("footer"):
                result.append({
                    "path": _footer.a["href"],
                    "name": _h3.text,
                    "icon": os.path.join(self.addon_dir, "resources", "assets", "icon_category.png"),
                    "node": []
                })

        return result

    def _parse_podcast_tile(self, tile):

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

        if path in ["/"]:
            self._make_root_menu()

        elif len(splitted_path) in [4, 5] and path.startswith(self.PODCASTS_URL):
            page = self.decode_param(
                url_params["page"][0]) if "page" in url_params else None

            self._make_menu(path, page=page)
