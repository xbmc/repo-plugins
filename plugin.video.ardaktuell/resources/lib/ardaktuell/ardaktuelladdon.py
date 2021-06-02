from resources.lib.rssaddon.abstract_rss_addon import AbstractRssAddon

import xbmcplugin


class ArdAktuellAddon(AbstractRssAddon):

    __PLUGIN_ID__ = "plugin.video.ardaktuell"

    QUALITY_LEVEL = ["webxl", "webl", "webm", "webs"]

    BROADCASTS = [
        {
            "name": "ARD Tagesschau",
            "icon": "https://www.tagesschau.de/image/podcast/ts-1400.jpg",
            "video_url": "https://www.tagesschau.de/export/video-podcast/%s/tagesschau_https/",
            "audio_url": "https://www.tagesschau.de/export/podcast/tagesschau_https/"
        },
        {
            "name": "ARD Tagesschau mit Gebärdensprache",
            "icon": "https://www.tagesschau.de/image/podcast/tsg-1400.jpg",
            "video_url": "https://www.tagesschau.de/export/video-podcast/%s/tagesschau-mit-gebaerdensprache_https/"
        },
        {
            "name": "ARD Tagesschau in 100 Sekunden",
            "icon": "https://www.tagesschau.de/image/podcast/ts100s-1400.jpg",
            "video_url": "https://www.tagesschau.de/export/video-podcast/%s/tagesschau-in-100-sekunden_https/",
            "audio_url": "https://www.tagesschau.de/export/podcast/hi/tagesschau-in-100-sekunden/"
        },
        {
            "name": "ARD Tagesthemen",
            "icon": "https://www.tagesschau.de/image/podcast/tt-1400.jpg",
            "video_url": "https://www.tagesschau.de/export/video-podcast/%s/tagesthemen_https/",
            "audio_url": "https://www.tagesschau.de/export/podcast/tagesthemen_https/"
        },
        {
            "name": "ARD Nachtmagazin",
            "icon": "https://www.tagesschau.de/image/podcast/nm-1400.jpg",
            "video_url": "https://www.tagesschau.de/export/video-podcast/%s/nachtmagazin_https/",
            "audio_url": "https://www.tagesschau.de/export/podcast/nachtmagazin_https/"
        },
        {
            "name": "ARD Bericht aus Berlin",
            "icon": "https://www.tagesschau.de/image/podcast/bab-1400.jpg",
            "video_url": "https://www.tagesschau.de/export/video-podcast/%s/bab_https/",
            "audio_url": "https://www.tagesschau.de/export/podcast/bab_https/",
            "type": "video"

        },
        {
            "name": "ARD Tagesschau vor 20 Jahren",
            "icon": "https://www.tagesschau.de/image/podcast/tsv20-1997-1400.jpg",
            "video_url": "https://www.tagesschau.de/export/video-podcast/%s/tagesschau-vor-20-jahren_https/",
            "audio_url": "https://www.tagesschau.de/export/podcast/tagesschau-vor-20-jahren_https/",
            "type": "video"
        },
        {
            "name": "ARD Mal angenommen...",
            "icon": "https://www.tagesschau.de/multimedia/bilder/mal-angenommen-podcast-cover-105~_v-original.jpg",
            "audio_url": "https://www.tagesschau.de/multimedia/podcasts/mal-angenommen-feed-101.xml",
            "type": "audio"
        }
    ]

    def __init__(self, addon_handle):

        AbstractRssAddon.__init__(self, self.__PLUGIN_ID__, addon_handle)

    def _build_dir_structure(self):

        def _make_node(index, broadcast, type, url, latest_only):

            _node = {
                "path": "latest" if latest_only else str(index),
                "name": broadcast["name"],
                "icon": broadcast["icon"],
                "type": type,
                "params": [
                    {
                        "play_latest" if latest_only else "rss": url
                    }
                ]
            }

            if not latest_only:
                _node["node"] = []

            return _node

        _nodes = []
        for i, broadcast in enumerate(self.BROADCASTS):

            _quality = int(self.addon.getSetting("quality"))
            if "video_url" in broadcast and _quality < 4:
                _nodes.append(_make_node(
                    i, broadcast, "video", broadcast["video_url"] % self.QUALITY_LEVEL[_quality], self.addon.getSetting("archive") != "true"))

            elif "audio_url" in broadcast:
                _nodes.append(_make_node(i, broadcast, "music",
                                         broadcast["audio_url"], self.addon.getSetting("archive") != "true"))

        return [
            {  # root
                "path": "",
                "node": _nodes
            }
        ]

    def _browse(self, dir_structure, path, updateListing=False):

        def _get_node_by_path(path):

            if path == "/":
                return dir_structure[0]

            tokens = path.split("/")[1:]
            node = dir_structure[0]

            while len(tokens) > 0:
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

    def route(self, path, url_params):
        
        _dir_structure = self._build_dir_structure()
        self._browse(dir_structure=_dir_structure, path=path)
