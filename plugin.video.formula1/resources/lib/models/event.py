import urllib.parse
import xbmcgui
from resources.lib.models.list_item import ListItem


class Event(ListItem):
    info = {}

    def to_list_item(self, addon_base):
        list_item = xbmcgui.ListItem(label=self.label)
        list_item.setArt({
            "thumb": self.thumb,
        })
        list_item.setInfo("video", {
            "plot": self.info["description"],
        })
        url = addon_base + "/?" + urllib.parse.urlencode({
            "action": "call",
            "call": "fom-results/race?meeting={id}".format(id=self.id)
        })

        if self.info["hasEnded"]:
            return url, list_item, True

        return None, list_item, False

    @staticmethod
    def get_description(item, event_ended):
        return "{} / {}\nStart: {}\nStatus: {}".format(
            item["meetingCountryName"],
            item["meetingLocation"],
            item["meetingStartDate"],
            # Status with fallback for "raceresults" items
            item.get("status", "completed" if event_ended else "upcoming")
        )
