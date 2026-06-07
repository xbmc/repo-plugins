from resources.lib.models.list_item import ListItem
import urllib.parse
import xbmcaddon
import xbmcgui

likes = xbmcaddon.Addon().getLocalizedString(30905)


class Playlist(ListItem):
    thumb = ""
    info = {}
    is_album = False

    def to_list_item(self, addon_base):
        list_item = xbmcgui.ListItem(label=self.label, label2=self.label2)
        list_item.setArt({"thumb": self.thumb})
        list_item.setIsFolder(True)
        list_item.setProperty("isPlayable", "false")
        # We have to use the `video`-type in order to display a proper folder description
        list_item.setInfo("video", {
            "plot": self._get_description()
        })

        url = addon_base + "/?" + urllib.parse.urlencode({
            "action": "call",
            "call": "/playlists/{id}".format(id=self.id)
        })

        return url, list_item, True

    def _get_description(self):
        return "{}\n{} {}\n\n{}".format(
            self.info.get("artist"),
            self.info.get("likes"),
            likes,
            self.info.get("description") or ""
        )
