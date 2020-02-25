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

    def to_list_item(self, addon, addon_base):
        list_item = xbmcgui.ListItem(label=self.label)
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
            "playcount": self.info.get("playcount"),
            "plot": self.info.get("description", ""),
            "title": self.label,
            "year": self.info.get("date")[:4],
        })
        list_item.setProperty("isPlayable", "true")

        if self.info.get("mediaUrlResolved"):
            url = self.uri
            list_item.setProperty("mediaUrl", url)
        else:
            url = addon_base + "/play/?" + urllib.parse.urlencode({"uri": self.uri})
            list_item.setProperty("mediaUrl", self.uri)

        return url, list_item, False
