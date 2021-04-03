import urllib.parse
import xbmcgui

from resources.lib.models.list_item import ListItem


class Group(ListItem):
    thumb = ""
    info = {}
    uri = ""

    def to_list_item(self, addon, addon_base):
        list_item = xbmcgui.ListItem(label=self.label, label2=self.label2)
        list_item.setArt({"thumb": self.thumb})
        list_item.setInfo("video", {
            "year": self.info.get("date")[:4]
        })
        url = addon_base + "/?" + urllib.parse.urlencode({
            "action": "call",
            "call": self.uri
        })

        return url, list_item, True
