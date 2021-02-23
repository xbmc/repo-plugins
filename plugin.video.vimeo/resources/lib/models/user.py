from future import standard_library
from future.utils import PY2
standard_library.install_aliases()  # noqa: E402

import urllib.parse
import xbmcgui

from resources.lib.models.list_item import ListItem
from resources.lib.kodi.utils import format_bold
from resources.routes import PATH_PROFILE


class User(ListItem):
    thumb = ""
    uri = ""
    data = {}

    def to_list_item(self, addon, addon_base):
        list_item = xbmcgui.ListItem(label=self.label, label2=self.label2)
        list_item.setArt({"thumb": self.data["pictures"]["sizes"][-1]["link"]})
        list_item.setInfo("video", {
            "plot": self._get_description(self.data),
        })
        url = addon_base + PATH_PROFILE + "?" + urllib.parse.urlencode({
            "uri": self.data["uri"],
        })

        return url, list_item, True

    @staticmethod
    def _get_description(data):
        if PY2:
            template = u"{}\n{}{}\n{}: {}\n{}: {}\n{}: {}\n\n{}"
        else:
            template = "{}\n{}{}\n{}: {}\n{}: {}\n{}: {}\n\n{}"

        return template.format(
            format_bold(data["name"]),
            data["location"] + "\n" if data["location"] else "",
            "\n" + data["short_bio"] + "\n" if data["short_bio"] else "",
            "Followers",
            data["metadata"]["connections"]["followers"]["total"],
            "Following",
            data["metadata"]["connections"]["following"]["total"],
            "Likes",
            data["metadata"]["connections"]["likes"]["total"],
            "\n".join([site["link"] for site in data["websites"]]) if data["websites"] else ""
        )
