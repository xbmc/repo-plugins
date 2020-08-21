from future import standard_library
from future.utils import PY2
standard_library.install_aliases()  # noqa: E402

from resources.lib.models.list_item import ListItem
import xbmcgui


class Constructor(ListItem):
    thumb = ""
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
        if PY2:
            template = u"{} - {} - {} PTS"
        else:
            template = "{} - {} - {} PTS"

        return template.format(
            item["positionNumber"],
            item["teamName"],
            str(item["seasonPoints"])
        )

    @staticmethod
    def get_drivers(drivers):
        combined_drivers = ""
        if PY2:
            template = u"{} {}\n"
        else:
            template = "{} {}\n"

        for driver in drivers:
            combined_drivers += template.format(
                driver["driverFirstName"],
                driver["driverLastName"]
            )

        return combined_drivers
