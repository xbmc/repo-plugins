import os
from datetime import datetime

import xbmc
import xbmcplugin
from resources.lib.podcasts.opml_file import open_opml_file, parse_opml
from resources.lib.rssaddon.abstract_rss_addon import AbstractRssAddon

GROUPS = 10
ENTRIES = 10


class PodcastsAddon(AbstractRssAddon):

    def __init__(self, addon_handle) -> None:

        super().__init__(addon_handle)
        self.anchor_for_latest = "true" == self.addon.getSetting("anchor")

    def load_rss(self, url) -> 'tuple[str,str,str,list[dict]]':

        return self._load_rss(url)

    def on_rss_loaded(self, url: str, title: str, description: str, image: str, items: 'list[dict]'):

        # update image
        for g in range(GROUPS):

            if self.addon.getSetting("group_%i_enable" % g) == "false":
                continue

            for e in range(ENTRIES):

                if self.addon.getSetting("group_%i_rss_%i_enable" % (g, e)) == "false":
                    continue

                elif url == self.addon.getSetting("group_%i_rss_%i_url" % (g, e)):
                    self.addon.setSetting(
                        "group_%i_rss_%i_icon" % (g, e), image)

    def _browse(self, dir_structure: str, path: str, updateListing=False) -> None:

        def _get_node_by_path(path: str) -> dict:

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

        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_FULLPATH)
        xbmcplugin.addSortMethod(
            self.addon_handle, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(
            self.addon_handle, updateListing=updateListing)

    def _build_dir_structure(self) -> None:

        groups = []

        limit = self.addon.getSettingInt("limit_episodes")

        # opml files / podcasts lists
        for g in range(GROUPS):

            if self.addon.getSetting("opml_file_%i" % g) == "":
                continue

            path = os.path.join(
                self.addon_dir, self.addon.getSetting("opml_file_%i" % g))

            try:
                name, nodes = parse_opml(open_opml_file(path), limit=limit)
                groups.append({
                    "path": "opml-%i" % g,
                    "name": name,
                    "node": nodes
                })

            except:
                xbmc.log("Cannot read opml file %s" % path, xbmc.LOGERROR)

        #  rss feeds from addon
        for g in range(GROUPS):

            if self.addon.getSetting("group_%i_enable" % g) == "false":
                continue

            entries = []
            for e in range(ENTRIES):

                if self.addon.getSetting("group_%i_rss_%i_enable" % (g, e)) == "false":
                    continue

                icon = self.addon.getSetting("group_%i_rss_%i_icon"
                                             % (g, e))

                entries += [{
                    "path": "%i" % e,
                    "name": self.addon.getSetting("group_%i_rss_%i_name"
                                                  % (g, e)),
                    "params": [
                        {
                            "rss": self.addon.getSetting("group_%i_rss_%i_url" % (g, e)),
                            "limit": str(limit)
                        }
                    ],
                    "icon": icon,
                    "node": []
                }]

            groups += [{
                "path": "pod-%i" % g,
                "name": self.addon.getSetting("group_%i_name" % g),
                "node": entries
            }]

        return [
            {  # root
                "path": "",
                "node": groups
            }
        ]

    def route(self, path) -> None:

        _dir_structure = self._build_dir_structure()
        self._browse(dir_structure=_dir_structure, path=path)

    def build_plot(self, item) -> str:

        plot = list()
        if "description" in item:
            plot.append(item["description"])

        if "date" in item:
            plot.append(datetime.strftime(item["date"], "%Y-%m-%d %H:%M"))

        return "\n".join(plot)
