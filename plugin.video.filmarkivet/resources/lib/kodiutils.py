import sys, os, xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs


class AddonUtils():
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.name = self.addon.getAddonInfo("name")
        self.id = self.addon.getAddonInfo("id")
        self.handle = int(sys.argv[1])
        self.url = sys.argv[0]
        self.icon = os.path.join(self.addon.getAddonInfo("path"), "icon.png")
        self.fanart = os.path.join(self.addon.getAddonInfo("path"), "fanart.jpg")
        self.profile_dir = xbmcvfs.translatePath(self.addon.getAddonInfo("Profile"))
        os.makedirs(self.profile_dir, exist_ok=True)
        self.cache_file = xbmcvfs.translatePath(os.path.join(self.profile_dir,
                                                             "requests_cache"))

    def localize(self, *args):
        if len(args) < 1:
            raise ValueError("String id missing")
        elif len(args) == 1:
            string_id = args[0]
            return self.addon.getLocalizedString(string_id)
        else:
            return [self.addon.getLocalizedString(string_id) for string_id in args]

    def view_menu(self, menu):
        items = []
        for item in menu:
            li = xbmcgui.ListItem(label=item.title, offscreen=True)
            li.setArt({"thumb": item.icon})
            li.setInfo("video", {"title": item.title, "year": item.year,
                "duration": item.duration})
            if item.playable:
                li.setProperty("IsPlayable", "true")
                li.setInfo("video", {"plot": item.description})
                context_url = "{0}?mode={1}&title={2}&url={3}".format(
                    self.url, "plot", item.title, item.url)
                context_menu = [(self.localize(30024),
                                 "RunPlugin({0})".format(context_url))]
                li.addContextMenuItems(context_menu)
            items.append((item.url, li, not item.playable))
        xbmcplugin.addDirectoryItems(self.handle, items)
        xbmcplugin.endOfDirectory(self.handle)

    def url_for(self, url):
        return "plugin://{0}{1}".format(self.id, url)

    def show_error(self, e):
        xbmcgui.Dialog().textviewer("{0} - {1}".format(
            self.name, self.localize(30002)), "Error: {0}".format(str(e)))


def keyboard_get_string(default, message):
    keyboard = xbmc.Keyboard(default, message)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return keyboard.getText()
    else:
        return None
