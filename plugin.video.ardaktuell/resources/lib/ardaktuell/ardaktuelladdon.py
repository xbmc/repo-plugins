from resources.lib.rssaddon.abstract_rss_addon import AbstractRssAddon

import xbmcgui
import xbmcplugin
from datetime import datetime


class ArdAktuellAddon(AbstractRssAddon):

    BROADCASTS = [
        {
            "name": "ARD Tagesschau um 20 Uhr",
            "icon": "https://images.tagesschau.de/image/eb0b0d74-03ac-45ec-9300-0851fd6823d3/AAABiE1u1f0/AAABg8tMMaM/1x1-1400/sendungslogo-tagesschau-100.jpg",
            "video_url": "https://www.tagesschau.de/multimedia/sendung/tagesschau_20_uhr/podcast-ts2000-video-100~podcast.xml",
            "date_format": "%d.%m.%Y"
        },
        {
            "name": "ARD Tagesschau um 20 Uhr mit Gebärdensprache",
            "icon": "https://images.tagesschau.de/image/eb0b0d74-03ac-45ec-9300-0851fd6823d3/AAABiE1u1f0/AAABg8tMMaM/1x1-1400/sendungslogo-tagesschau-100.jpg",
            "video_url": "https://www.tagesschau.de/multimedia/sendung/tagesschau_mit_gebaerdensprache/podcast-tsg-100~podcast.xml",
            "date_format": "%d.%m.%Y"
        },
        {
            "name": "ARD Tagesschau in 100 Sekunden",
            "icon": "https://images.tagesschau.de/image/559ce6ba-91f3-495c-b36d-77115c440dd0/AAABiE1fSSM/AAABg8tMMaM/1x1-1400/sendungslogo-tsh-100.jpg",
            "video_url": "https://www.tagesschau.de/multimedia/sendung/tagesschau_in_100_sekunden/podcast-ts100-video-100~podcast.xml",
            "date_format": "%d.%m.%Y %H:%M"
        },
        {
            "name": "ARD Tagesthemen",
            "icon": "https://images.tagesschau.de/image/6b0ab906-0dcf-432f-807c-1d10f8a0a73a/AAABiE1uG-U/AAABg8tMMaM/1x1-1400/sendungslogo-tagesthemen-100.jpg",
            "video_url": "https://www.tagesschau.de/multimedia/sendung/tagesthemen/podcast-tt-video-100~podcast.xml",
            "date_format": "%d.%m.%Y"
        },
        {
            "name": "ARD Tagesschau vor 20 Jahren",
            "icon": "https://images.tagesschau.de/image/2a6f7e91-d939-4fde-98b8-9d7fb54be721/AAABiB8Zoe4/AAABg8tMMaM/1x1-1400/tagesschau-logo-105.jpg",
            "video_url": "https://www.tagesschau.de/multimedia/sendung/tagesschau_vor_20_jahren/podcast-tsv20-video-100~podcast.xml",
            "type": "video",
            "date_format": ""
        },
        {
            "name": "ARD Mal angenommen...",
            "icon": "https://images.tagesschau.de/image/d5f4c036-3eca-4b59-9a11-1acd53814639/AAABiB7_Ajo/AAABg8tMMaM/1x1-1400/podcast-mal-angenommen-102.jpg",
            "audio_url": "https://www.tagesschau.de/multimedia/podcast/malangenommen/mal-angenommen-feed-101~podcast.xml",
            "type": "audio",
            "date_format": "%d.%m.%Y"
        },
        {
            "name": "Ideenimport",
            "icon": "https://images.tagesschau.de/image/ab2459a5-283e-41be-ad3f-5e323ffb7c5a/AAABiGJ5xhQ/AAABg8tMMaM/1x1-1400/podcast-ideenimport-104.jpg",
            "audio_url": "https://www.tagesschau.de/multimedia/podcast/ideenimport/ideenimport-feed-105~podcast.xml",
            "type": "audio",
            "date_format": "%d.%m.%Y"
        },
        {
            "name": "faktenfinder",
            "icon": "https://images.tagesschau.de/image/582386c7-f443-4560-baaa-688cb2773d25/AAABiB78cks/AAABg8tMMaM/1x1-1400/podcast-faktenfinder-104.jpg",
            "audio_url": "https://www.tagesschau.de/multimedia/podcast/faktenfinder/faktenfinder-feed-101~podcast.xml",
            "type": "audio",
            "date_format": "%d.%m.%Y"
        }
    ]

    def __init__(self, addon_handle) -> None:

        super().__init__(addon_handle)

    def _build_dir_structure(self) -> None:

        def _make_node(index, broadcast, type, url, latest_only):

            _node = {
                "path": "latest" if latest_only else str(index),
                "name": broadcast["name"],
                "icon": broadcast["icon"],
                "type": type,
                "params": [
                    {
                        "play_latest" if latest_only else "rss": url
                    },
                    {
                        "date_format": broadcast["date_format"]
                    }
                ]
            }

            if not latest_only:
                _node["node"] = []

            return _node

        _nodes = []
        for i, broadcast in enumerate(self.BROADCASTS):

            if "video_url" in broadcast:
                _nodes.append(_make_node(
                    i, broadcast, "video", broadcast["video_url"], self.addon.getSetting("archive") != "true"))

            elif "audio_url" in broadcast:
                _nodes.append(_make_node(i, broadcast, "music",
                                         broadcast["audio_url"], self.addon.getSetting("archive") != "true"))

        return [
            {  # root
                "path": "",
                "node": _nodes
            }
        ]

    def _browse(self, dir_structure, path: str, updateListing=False):

        def _get_node_by_path(path):

            if path == "/":
                return dir_structure[0]

            tokens = path.split("/")[1:]
            node = dir_structure[0]

            while tokens:
                path = tokens.pop(0)
                for n in node["node"]:
                    if n["path"] == path:
                        node = n
                        break

            return node

        node = _get_node_by_path(path)
        for entry in node["node"]:
            self.add_list_item(entry, path)

        xbmcplugin.endOfDirectory(
            self.addon_handle, updateListing=updateListing)

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

    def route(self, path, url_params):

        _dir_structure = self._build_dir_structure()
        self._browse(dir_structure=_dir_structure, path=path)

    def build_label(self, item, params: dict = None) -> str:

        if params and "date_format" in params and params["date_format"] and "date" in item:
            return "%s (%s)" % (item["name"], datetime.strftime(item["date"], params["date_format"]))
        else:
            return super().build_label(item)
