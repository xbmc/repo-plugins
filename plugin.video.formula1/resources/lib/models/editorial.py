from resources.lib.models.list_item import ListItem
import urllib.parse
import xbmcgui


class Editorial(ListItem):
    thumb = ""
    uri = ""
    info = {}

    def to_list_item(self, addon_base):
        list_item = xbmcgui.ListItem(label=self.label, label2=self.label2)
        list_item.setArt({"thumb": self.thumb})
        list_item.setInfo("music", {
            "title": self.label,
        })
        url = addon_base + "/?" + urllib.parse.urlencode({
            "action": "call",
            "call": "fom-assets/videos?tag={tag}".format(tag=self.id),
        })

        return url, list_item, True
