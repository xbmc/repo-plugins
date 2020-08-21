from future import standard_library
standard_library.install_aliases()  # noqa: E402

from resources.lib.models.list_item import ListItem
import urllib.parse
import xbmcgui


class Video(ListItem):
    thumb = ""
    uri = ""
    info = {}

    def to_list_item(self, addon_base):
        list_item = xbmcgui.ListItem(label=self.label)
        list_item.setArt({
            "thumb": self.thumb,
        })
        list_item.setInfo("video", {
            "duration": self.info.get("duration"),
        })
        list_item.setProperty("isPlayable", "true")

        url = addon_base + "/play/?" + urllib.parse.urlencode({"embed_code": self.uri})

        return url, list_item, False
