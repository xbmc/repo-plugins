import os
from urllib.parse import urlparse
from xbmc import executebuiltin
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItems, addSortMethod, \
        endOfDirectory, setResolvedUrl
from resources.lib.api import DocumentaryHeaven
from resources.lib.kodiutils import AddonInfo


class MenuList():
    YOUTUBE_PLUGIN = "plugin://plugin.video.youtube/"
    VIMEO_PLUGIN = "plugin://plugin.video.vimeo/"
    DAILYMOTION_PLUGIN = "plugin://plugin.video.dailymotion_com/"


    def __init__(self):
        self.addon = AddonInfo()
        self.documentary_heaven = DocumentaryHeaven()


    def _add_folder_item(self, items, title, url, icon_url, fanart_url,
                         sort_title="", isfolder=True, isplayable=False,
                         date=None, info=None, context_menu_items=None,
                         offscreen=True):

        if fanart_url is None:
            fanart_url = os.path.join(self.addon.media, "fanart_blur.jpg")

        if icon_url is None:
            icon_url = os.path.join(self.addon.media, "icon_trans.png")

        list_item = ListItem(label=title, offscreen=offscreen)
        list_item.setArt({"thumb": icon_url, "fanart": fanart_url})
        list_item.setInfo("video", {"title": title, "sorttitle": sort_title})

        if isplayable:
            list_item.setProperty("IsPlayable", "true")
        else:
            list_item.setProperty("IsPlayable", "false")

        if date is not None:
            list_item.setInfo("video", {"date": date})

        if info is not None:
            list_item.setInfo("video", {"plot": info})

        if context_menu_items is not None:
            list_item.addContextMenuItems(context_menu_items)

        items.append((url, list_item, isfolder))


    def _end_folder(self, items, sort_methods=()):
        addDirectoryItems(self.addon.handle, items, totalItems=len(items))

        for sort_method in sort_methods:
            addSortMethod(self.addon.handle, sort_method)

        endOfDirectory(self.addon.handle)


    def show_main_menu(self):
        menu_items = [{"label": self.addon.localize(30000),
                       "path": "/all",
                       "action": "showdocs"},
                      {"label": self.addon.localize(30001),
                       "path": "/watch-online",
                       "action": "showcategories"},
                      {"label": self.addon.localize(30002),
                       "path": "/popular",
                       "action": "showtoplist"},
                      {"label": self.addon.localize(30003),
                       "path": "/best",
                       "action": "showtoplist"},
                      {"label": self.addon.localize(30004),
                       "path": "/search",
                       "action": "showsearchmenu"}]
        items = []
        for item in menu_items:
            url = "{0}?action={1}&path={2}&page=1".format(self.addon.url,
                                                         item["action"],
                                                         item["path"])
            self._add_folder_item(items, item["label"], url, None, None)
        self._end_folder(items)


    def show_documentaries(self, content_path, page):
        items = []
        for documentary in self.documentary_heaven.get_documentaries(content_path, page):
            documentary_path = urlparse(documentary["url"]).path
            url = "{0}?action={1}&path={2}".format(self.addon.url,
                                                  "playmedia",
                                                  documentary_path)

            context_url = "{0}?action={1}&path={2}".format(self.addon.url,
                                                          "showplot",
                                                          documentary_path)
            context_menu = [(self.addon.localize(30005),
                             "RunPlugin({0})".format(context_url))]
            self._add_folder_item(items, documentary["title"], url,
                                  documentary["icon"], None,
                                  info=documentary["plot"],
                                  isplayable=True, isfolder=False,
                                  context_menu_items=context_menu)

        url = "{0}?action={1}&path={2}&page={3}".format(self.addon.url,
                                                       "showdocs",
                                                       content_path,
                                                       int(page)+1)
        self._add_folder_item(items, self.addon.localize(30006), url, None,None)
        self._end_folder(items)


    def show_categories(self):
        items = []
        for category in self.documentary_heaven.get_categories():
            category_path = "/category" + urlparse(category["url"]).path
            url = "{0}?action={1}&path={2}&page=1".format(self.addon.url,
                                                          "showdocs",
                                                          category_path)

            self._add_folder_item(items, category["label"], url, None, None)
        self._end_folder(items)


    def show_toplist(self, content_path):
        items = []
        for documentary in self.documentary_heaven.get_toplist(content_path):
            documentary_path = urlparse(documentary["url"]).path
            url = "{0}?action={1}&path={2}".format(self.addon.url,
                                                  "playmedia",
                                                  documentary_path)

            context_url = "{0}?action={1}&path={2}".format(self.addon.url,
                                                          "showplot",
                                                           documentary_path)
            context_menu = [(self.addon.localize(30005),
                             "RunPlugin({0})".format(context_url))]
            self._add_folder_item(items, documentary["title"], url, documentary["icon"],
                                  None, info=documentary["plot"], isplayable=True,
                                  isfolder=False,
                                  context_menu_items=context_menu)

        self._end_folder(items)


    def search_history_update(self, action, remove_id=None):
        if action == "removesearch":
            if remove_id is not None:
                self.addon.search_history.remove(remove_id)
        elif action == "clearsearch":
            self.addon.search_history.clear()
        executebuiltin("Container.Refresh")


    def show_search_menu(self):
        items = []

        url = "{0}?action={1}".format(self.addon.url, "newsearch")
        self._add_folder_item(items, self.addon.localize(30008), url, None, None)

        url = "{0}?action={1}".format(self.addon.url, "showsearchhistory")
        self._add_folder_item(items, self.addon.localize(30009), url, None, None)

        self._end_folder(items)


    def search(self):
        search_history = self.addon.search_history
        query = self.addon.get_user_input(prompt_msg=self.addon.localize(30004))
        if query != "":
            search_history.add(query)
            return search_history.get_id(query, reload_data=True)
        return None


    def show_search_history(self):
        search_history = self.addon.search_history

        items = []
        for (query_id, query) in enumerate(search_history.get_queries()):
            url = "{0}?action={1}&query_id={2}&offset=0".format(self.addon.url,
                                                             "searchdocs",
                                                             query_id)
            remove_url = "{0}?action={1}&remove_id={2}".format(self.addon.url,
                                                              "removesearch",
                                                              query_id)
            clear_url = "{0}?action={1}".format(self.addon.url, "clearsearch")
            context_menu = [(self.addon.localize(30010),
                             "RunPlugin({0})".format(remove_url)),
                            (self.addon.localize(30011),
                             "RunPlugin({0})".format(clear_url))]
            self._add_folder_item(items, query, url, None,
                                  None, context_menu_items=context_menu)

        self._end_folder(items)


    def show_searched_documentaries(self, query_id, offset):
        query = self.addon.search_history.get(query_id)

        items = []
        for documentary in self.documentary_heaven.search(query, offset):
            documentary_path = urlparse(documentary["url"]).path
            context_url = "{0}?action={1}&path={2}".format(self.addon.url,
                                                          "showplot",
                                                          documentary_path)
            context_menu = [(self.addon.localize(30005),
                             "RunPlugin({0})".format(context_url))]

            url = "{0}?action={1}&path={2}".format(self.addon.url,
                                                  "playmedia",
                                                  documentary_path)
            self._add_folder_item(items, documentary["title"], url,
                                  None, None, isplayable=True,
                                  isfolder=False, info=documentary["plot"],
                                  context_menu_items=context_menu)

        url = "{0}?action={1}&query_id={2}&offset={3}".format(self.addon.url,
                                                           "searchdocs",
                                                           query_id,
                                                           offset+10)
        self._add_folder_item(items, self.addon.localize(30006), url, None, None)
        self._end_folder(items)


    def show_plot(self, documentary_url):
        plot = self.documentary_heaven.get_plot(documentary_url)
        Dialog().textviewer(plot["title"], plot["text"])


    def play_video(self, documentary_url):
        video = self.documentary_heaven.get_documentary_info(documentary_url)

        if video["player"] == "youtube":
            if not video["playlist"]:
                path = self.YOUTUBE_PLUGIN \
                       + "play/?video_id={}".format(video["id"])
            else:
                path = self.YOUTUBE_PLUGIN + "play/?playlist_id={0}&play=1" \
                       "&order=default&play=1&order=default".format(video["id"])
        elif video["player"] == "vimeo":
            path = self.VIMEO_PLUGIN + "play/?video_id=" + video["id"]
        elif video["player"] == "dailymotion":
            path = self.DAILYMOTION_PLUGIN \
                   + "?url={}&mode=playVideo".format(video["id"])
        elif video["player"] == "archive":
            path = video["path"]
        else:
            path = ""

        play_item = ListItem(path=path)
        setResolvedUrl(self.addon.handle, True, listitem=play_item)
