from resources.lib.models.list_item import ListItem
import xbmcgui


class Result(ListItem):
    thumb = ""
    info = {}

    def to_list_item(self, addon_base):
        list_item = xbmcgui.ListItem(label=self.label)
        list_item.setArt({
            "thumb": self.thumb,
        })
        list_item.setInfo("video", {
            "plot": "{} / {}".format(self.info["name"], self.info["team"]),
        })
        list_item.setProperty("isPlayable", "false")

        return None, list_item, False

    @staticmethod
    def get_label(item):
        return "{} - {} - {} PTS - {}".format(
            "DNF" if item["positionNumber"] == "666" else item["positionNumber"],
            item["driverTLA"],
            str(item["racePoints"]),
            "+{}s".format(item["gapToPrevious"]) if item["gapToPrevious"] else item["raceTime"]
        )
