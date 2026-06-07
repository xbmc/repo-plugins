from resources.lib.models.list_item import ListItem
from resources.routes import *
import urllib.parse
import xbmcaddon
import xbmcgui

followers = xbmcaddon.Addon().getLocalizedString(30904)


class User(ListItem):
    thumb = ""
    info = {}

    def to_list_item(self, addon_base):
        list_item = xbmcgui.ListItem(label=self.label, label2=self.label2)
        list_item.setArt({"thumb": self.thumb})
        list_item.setIsFolder(True)
        list_item.setProperty("isPlayable", "false")
        # We have to use the `video`-type in order to display a proper folder description
        list_item.setInfo("video", {
            "plot": self._get_description()
        })

        url = addon_base + PATH_USER + "?" + urllib.parse.urlencode({
            "id": self.id,
            "call": "/users/{id}/tracks".format(id=self.id)
        })

        return url, list_item, True

    def _get_description(self):
        return "{}\n{} {}\n\n{}".format(
            self.label2 if self.label2 != "" else self.label,
            self.info.get("followers"),
            followers,
            self.info.get("description") or ""
        )
