from resources.lib.models.list_item import ListItem
import urllib.parse
import xbmcgui


class Playlist(ListItem):
    thumb = ""
    info = {}
    is_album = False

    def to_list_item(self, addon_base):
        list_item = xbmcgui.ListItem(label=self.label, label2=self.label2)
        list_item.setArt({"thumb": self.thumb})
        list_item.setInfo("music", {
            "title": self.label
        })
        url = addon_base + "/?" + urllib.parse.urlencode({
            "action": "call",
            "call": "/playlists/{id}".format(id=self.id)
        })

        return url, list_item, True
