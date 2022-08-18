import xbmcgui
from resources.lib.models.list_item import ListItem


class Driver(ListItem):
    info = {}

    def to_list_item(self, addon_base):
        list_item = xbmcgui.ListItem(label=self.label)
        list_item.setArt({
            "thumb": self.thumb,
        })
        list_item.setInfo("video", {
            "plot": self.info["team"],
        })
        list_item.setProperty("isPlayable", "false")

        return None, list_item, False

    @staticmethod
    def get_label(item):
        return "{} - {} {} - {} PTS".format(
            item.get("positionNumber", "?"),
            item["driverFirstName"],
            item["driverLastName"],
            str(item.get("championshipPoints", 0))
        )
