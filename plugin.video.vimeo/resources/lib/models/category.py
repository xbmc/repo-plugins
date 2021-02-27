import urllib.parse
import xbmcgui

from resources.lib.models.list_item import ListItem


class Category(ListItem):
    thumb = ""
    uri = ""

    def to_list_item(self, addon, addon_base):
        list_item = xbmcgui.ListItem(label=self.label, label2=self.label2)
        list_item.setArt({"thumb": self.thumb})
        url = addon_base + "/?" + urllib.parse.urlencode({
            "action": "call",
            "call": self.uri + "?filter=conditional_featured"
        })

        return url, list_item, True
