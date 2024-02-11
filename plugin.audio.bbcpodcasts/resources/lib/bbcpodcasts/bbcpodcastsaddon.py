import json
import os

import xbmcgui
import xbmcplugin
from resources.lib.rssaddon.abstract_rss_addon import AbstractRssAddon
from resources.lib.rssaddon.http_client import http_request


class BbcPodcastsAddon(AbstractRssAddon):

    API_BASE = "https://rms.api.bbc.co.uk"
    API_SPEECH = "/v2/experience/inline/speech"
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

    def _make_menu(self, path: str, params: 'dict[str]') -> None:

        if path.endswith("/"):
            path = path[:-1]

        entries = self._get_podcasts(path, params)
        for entry in entries:
            self.add_list_item(entry, path)

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(self.addon_handle, updateListing=False)

    def _get_podcasts(self, url: str, params: 'dict[str]') -> 'list[dict]':

        url_param = "?%s" % "&".join(
            ["%s=%s" % (k, params[k][0]) for k in params]) if len(params) > 0 else ""
        url = self.API_BASE + "/" + "/".join(url.split("/")[2:])
        _data, _cookies = http_request(self.addon, url + url_param)
        _json = json.loads(_data)

        entries = list()

        for _d in _json["data"]:
            if "uris" not in _d or "download" not in _d or not _d["download"] or "quality_variants" not in _d["download"]:
                continue

            has_media = [True for _quality in _d["download"]["quality_variants"]
                         if _d["download"]["quality_variants"][_quality]["file_url"]]

            entry = {
                "path": "",
                "name": _d["titles"]["primary"] + ("" if has_media else " ˟"),
                "icon": _d["image_url"].replace("{recipe}", "896x896"),
                "type": "music",
                "params": [
                    {
                        "rss": self.RSS_URL_PATTERN % _d["container"]["id"]
                    }
                ],
                "node": []
            }

            entries.append(entry)

        return entries

    def _get_entries_for_categories(self) -> 'list[dict]':

        _data, _cookies = http_request(
            self.addon, "%s%s" % (self.API_BASE, self.API_SPEECH))
        _json = json.loads(_data)

        result = list()

        for _d in _json["data"]:

            if _d["type"] != "inline_display_module" or not _d["uris"]:
                continue

            _name = _d["title"].strip()
            _path: str = _d["uris"]["pagination"]["uri"]
            _path = _path.replace("{offset}", str(
                _d["uris"]["pagination"]["offset"]))
            _path = _path.replace("{limit}", str(
                _d["uris"]["pagination"]["total"]))
            _data = "data" in _d and type(_d["data"]) == list

            if _path and _name and _data:
                result.append({
                    "path": "/__CATEGORIES__%s" % _path,
                    "name": _name,
                    "icon": os.path.join(self.addon_dir, "resources", "assets", "icon_category.png"),
                    "node": []
                })

        return result

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

        if path in ["/"]:
            self._make_root_menu()

        elif "__CATEGORIES__" in path:
            self._make_menu(path, url_params)
