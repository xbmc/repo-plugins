from future import standard_library
standard_library.install_aliases()  # noqa: E402

from resources.lib.models.list_item import ListItem
import urllib.parse
import xbmcaddon
import xbmcgui

blocked = xbmcaddon.Addon().getLocalizedString(30902)


class Video(ListItem):
    thumb = ""
    uri = ""
    info = {}

    def to_list_item(self, addon_base):
        list_item = xbmcgui.ListItem(label=self.label)
        url = addon_base + "/play/?" + urllib.parse.urlencode({"uri": self.uri})
        list_item.setArt({"thumb": self.thumb})
        list_item.setInfo("video", {
            "playcount": self.info.get("artist"),
            "duration": self.info.get("duration"),
            "year": self.info.get("date")[:4],
            "title": self.label,
            "plot": self.info.get("description", ""),
            "artist": [self.info.get("user", "")]
        })
        list_item.setProperty("isPlayable", "true")
        list_item.setProperty("mediaUrl", self.uri)

        return url, list_item, False
