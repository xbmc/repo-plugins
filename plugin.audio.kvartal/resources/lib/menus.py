import os
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItems, addSortMethod, endOfDirectory, \
    setResolvedUrl
from resources.lib.api import Kvartal
from resources.lib.kodiutils import AddonUtils


class MenuList():

    def __init__(self):
        self.kvartal = Kvartal()
        self.addon_utils = AddonUtils()

    def _add_folder_item(self, items, title, url, icon_url=None, fanart_url=None,
                         isfolder=True, isplayable=False, context_menu_items=None,
                         offscreen=True):

        if fanart_url is None:
            fanart_url = os.path.join(self.addon_utils.resources, "fanart.jpg")

        if icon_url is None:
            icon_url = os.path.join(self.addon_utils.resources, "icon.png")

        list_item = ListItem(label=title, offscreen=offscreen)
        list_item.setArt({"thumb": icon_url, "fanart": fanart_url})
        list_item.setInfo("music", {"title": title})

        if isplayable:
            list_item.setProperty("IsPlayable", "true")
        else:
            list_item.setProperty("IsPlayable", "false")

        if context_menu_items is not None:
            list_item.addContextMenuItems(context_menu_items)

        items.append((url, list_item, isfolder))

    def _end_folder(self, items, sort_methods=()):
        addDirectoryItems(self.addon_utils.handle, items, totalItems=len(items))

        for sort_method in sort_methods:
            addSortMethod(self.addon_utils.handle, sort_method)

        endOfDirectory(self.addon_utils.handle)

    def root_menu(self):
        items = []
        for (show_id, show) in enumerate(self.kvartal.shows):
            url = "{0}?action=listshows&show_id={1}".format(
                self.addon_utils.url, show_id)
            context_url = "{0}?action={1}&show_id={2}".format(
                self.addon_utils.url, "getshowsummary", show_id)
            context_menu = [(self.addon_utils.localize(30004),
                             "RunPlugin({0})".format(context_url))]
            icon_url = os.path.join(self.addon_utils.media,
                show["suburl"] + ".png")
            self._add_folder_item(items, show["name"], url, icon_url=icon_url,
                context_menu_items=context_menu)

        self._end_folder(items)

    def content_menu(self, show_id):
        episodes = self.kvartal.get_content(int(show_id))

        items = []
        for episode in episodes:
            url = "{0}?action=play&audio={1}".format(self.addon_utils.url,
                episode["media_url"])
            title = "{0} ({1})".format(episode["label"], episode["date"])
            context_url = "{0}?action={1}&show_id={2}&episode_id={3}".format(
                self.addon_utils.url, "getepisodesummary", show_id,
                episode["media_url"])
            context_menu = [(self.addon_utils.localize(30004),
                             "RunPlugin({0})".format(context_url))]
            self._add_folder_item(items, title, url, episode["image_url"],
                isplayable=True, isfolder=False, context_menu_items=context_menu)

        self._end_folder(items)

    def view_show_summary(self, show_id):
        summary = self.kvartal.get_show_summary(int(show_id))
        Dialog().textviewer(self.addon_utils.name, summary)

    def view_episode_summary(self, show_id, episode_id):
        episodes = self.kvartal.get_content(int(show_id))

        for episode in episodes:
            if episode["media_url"] == episode_id:
                Dialog().textviewer(self.addon_utils.name, episode["summary"])
                break

    def play_audio(self, path):
        play_item = ListItem(path=path)
        setResolvedUrl(self.addon_utils.handle, True, listitem=play_item)
