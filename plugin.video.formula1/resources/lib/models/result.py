from future import standard_library
from future.utils import PY2
standard_library.install_aliases()  # noqa: E402

from resources.lib.models.list_item import ListItem
import xbmcgui


class Result(ListItem):
    thumb = ""
    info = {}

    def to_list_item(self, addon_base):
        template = u"{} / {}" if PY2 else "{} / {}"

        list_item = xbmcgui.ListItem(label=self.label)
        list_item.setArt({
            "thumb": self.thumb,
        })
        list_item.setInfo("video", {
            "plot": template.format(self.info["name"], self.info["team"]),
        })
        list_item.setProperty("isPlayable", "false")

        return None, list_item, False

    @staticmethod
    def get_label(item):
        if PY2:
            template = u"{} - {} - {} PTS - {}"
        else:
            template = "{} - {} - {} PTS - {}"

        return template.format(
            "DNF" if item["positionNumber"] == "666" else item["positionNumber"],
            item["driverTLA"],
            str(item["racePoints"]),
            "+{}s".format(item["gapToPrevious"]) if item["gapToPrevious"] else item["raceTime"]
        )
