from datetime import datetime

import xbmcgui
from resources.lib.podcasts.actions.opml_action import OpmlAction
from resources.lib.podcasts.util import get_asset_path


class ExportOpmlAction(OpmlAction):

    def _write_opml_file(self, path: str) -> bool:

        def _get_rfc822_date(_dt: datetime) -> str:

            _month = ["Jan",  "Feb",  "Mar",  "Apr",  "May",  "Jun",
                      "Jul",  "Aug",  "Sep",  "Oct",  "Nov",  "Dec"]
            _day = ["Sun", "Mon", "Tue",  "Wed", "Thu", "Fri", "Sat"]

            return "%s, %i %s %i %s +0000" % (_day[int(_dt.strftime("%w"))], _dt.day, _month[_dt.month - 1], _dt.year, _dt.strftime("%H:%M:%S"))

        def _escape(str: str) -> str:
            str = str.replace("&", "&amp;")
            str = str.replace("<", "&lt;")
            str = str.replace(">", "&gt;")
            str = str.replace("\"", "&quot;")
            return str

        outlines = list()
        for g in range(self._GROUPS):
            if self.addon.getSetting("group_%i_enable" % g) == "true":
                _group = _escape(self.addon.getSetting("group_%i_name" % g))
                for e in range(self._ENTRIES):
                    if self.addon.getSetting("group_%i_rss_%i_enable" % (g, e)) == "true":
                        _url = _escape(self.addon.getSetting(
                            "group_%i_rss_%i_url" % (g, e)))
                        _name = _escape(self.addon.getSetting(
                            "group_%i_rss_%i_name" % (g, e)))
                        if _url and _name:
                            outlines.append(
                                "<outline xmlUrl=\"%s\" description=\"%s\" type=\"rss\" htmlUrl=\"\" title=\"%s\" text=\"%s\"/>" % (_url, _group, _name, _name))

        title = self.addon.getAddonInfo("name")
        created = _get_rfc822_date(datetime.now())

        _xml = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<opml version=\"2.0\"><head><title>%s</title><dateCreated>%s</dateCreated></head><body>%s</body></opml>" % (
            title, created, "".join(outlines))

        try:
            with open("%s%s.opml" % (path, title), mode="w") as _file:
                _file.writelines(_xml)
                _file.close()

            return True

        except:
            return False

    def export_opml(self) -> None:

        # Step 1: Select folder
        path = xbmcgui.Dialog().browse(type=3, heading=self.addon.getLocalizedString(
            32090), shares="")
        if not path:
            return

        # Step 2: Write file
        if self._write_opml_file(path):
            # Success
            xbmcgui.Dialog().notification(heading=self.addon.getLocalizedString(
                32091), message=self.addon.getLocalizedString(32086), icon=get_asset_path("notification.png"))
        else:
            xbmcgui.Dialog().notification(heading=self.addon.getLocalizedString(
                32092), message=self.addon.getLocalizedString(32086), icon=get_asset_path("notification.png"))
