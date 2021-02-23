from future import standard_library
standard_library.install_aliases()  # noqa: E402

import urllib.parse
import xbmcaddon
import xbmcgui

from resources.lib.models.list_item import ListItem

live = xbmcaddon.Addon().getLocalizedString(30902)
trailer = xbmcaddon.Addon().getLocalizedString(30903)


class Video(ListItem):
    thumb = ""
    uri = ""
    info = {}
    hasSubtitles = None

    def to_list_item(self, addon, addon_base):
        text_tracks = "{}/texttracks".format(self.uri) if self.hasSubtitles else ""

        list_item = xbmcgui.ListItem(label=(self._get_label_prefix() + self.label))
        list_item.setArt({
            "thumb": self.thumb,
            "poster": self.info.get("picture", ""),
        })
        list_item.setCast([
            {
                "name": self.info.get("user", ""),
                "role": addon.getLocalizedString(30401),
                "thumbnail": self.info.get("userThumb", ""),
            },
        ])
        list_item.setInfo("video", {
            "artist": [self.info.get("user", "")],
            "duration": self.info.get("duration"),
            "plot": self.info.get("description", ""),
            "title": self.label,
            "year": self.info.get("date")[:4],
        })
        list_item.setProperty("isPlayable", "true")
        list_item.setProperty("mediaUrl", self.uri)
        list_item.setProperty("textTracks", text_tracks)

        url = addon_base + "/play/?" + urllib.parse.urlencode({
            "uri": self.uri,
            "texttracks": text_tracks,
        })

        return url, list_item, False

    def _get_label_prefix(self):
        if self.info.get("onDemand"):
            return "[{}] ".format(trailer)

        if self.info.get("live"):
            return "[{}] ".format(live)

        return ""
