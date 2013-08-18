import os
import sys
import xbmcaddon
import xbmcgui
import xbmcplugin


class Menu(object):
    _plugin_url = sys.argv[0]
    _handle = int(sys.argv[1])
    _addon_path = None

    def __init__(self):
        addon = xbmcaddon.Addon(id="plugin.video.nfl-teams")
        self._addon_path = addon.getAddonInfo("path")

    def add_sort_method(self, sort_method="none"):
        if sort_method == "none":
            xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_NONE)
        elif sort_method == "alpha":
            xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_LABEL)
            xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        elif sort_method == "date":
            xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_DATE)

    def add_item(self, url_params, name, folder=False, thumbnail=None, date=None, fanart=None):
        params = ["?"]
        for key, value in url_params.iteritems():
            params.append("%s=%s&" % (str(key), str(value)))
            if key is "team" and not fanart:
                fanart = os.path.join(self._addon_path, "resources", "images", "fanart", value + ".jpg")

        url = self._plugin_url + "".join(params)

        if not thumbnail.startswith("http://"):
            thumbnail = os.path.join(self._addon_path, thumbnail)

        item = xbmcgui.ListItem()
        item.setLabel(name)

        if thumbnail:
            item.setThumbnailImage(thumbnail)
        if fanart:
            item.setProperty("fanart_image", fanart)
        if date:
            item.setInfo("video", {"date": date, "title": name})
        else:
            item.setInfo("video", {"title": name})

        if folder:
            xbmcplugin.addDirectoryItem(self._handle, url, item, isFolder=folder)
        else:
            xbmcplugin.addDirectoryItem(self._handle, url, item)

    def end_directory(self):
        xbmcplugin.endOfDirectory(self._handle)

    def dialog_ok(self, header, line1, line2=None, line3=None):
        dialog = xbmcgui.Dialog()
        if not line2 and not line3:
            return dialog.ok(header, line1)
        elif line2 and not line3:
            return dialog.ok(header, line1, line2)
        elif not line2 and line3:
            return dialog.ok(header, line1, line3)
        elif line2 and line3:
            return dialog.ok(header, line1, line2, line3)
