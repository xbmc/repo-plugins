import xbmcgui
from resources.lib.models.list_item import ListItem


class Constructor(ListItem):
    info = {}

    def to_list_item(self, addon_base):
        list_item = xbmcgui.ListItem(label=self.label)
        list_item.setArt({
            "thumb": self.thumb,
        })
        list_item.setInfo("video", {
            "plot": self.info["drivers"],
        })
        list_item.setProperty("isPlayable", "false")

        return None, list_item, False

    @staticmethod
    def get_label(item):
        return "{} - {} - {} PTS".format(
            item["positionNumber"],
            item["teamName"],
            str(item["seasonPoints"])
        )

    @staticmethod
    def get_drivers(drivers):
        combined_drivers = ""

        for driver in drivers:
            combined_drivers += "{} {}\n".format(
                driver["driverFirstName"],
                driver["driverLastName"]
            )

        return combined_drivers
