import os
import sys
from urllib.parse import urlparse, parse_qsl
from xbmcvfs import translatePath
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItems, addSortMethod, \
        endOfDirectory, setResolvedUrl
from xbmcaddon import Addon
from xbmc import Keyboard
from resources.lib.utils import WebScraper


class DocumentaryHeaven():

    addon = Addon()
    addon_url = sys.argv[0]
    addon_handle = int(sys.argv[1])
    addon_name = Addon().getAddonInfo("name")
    addon_id = Addon().getAddonInfo("id")
    addon_path = addon.getAddonInfo("path")
    addon_resources = translatePath(addon_path + "resources/")
    addon_media = translatePath(addon_resources + "media/")

    localize = addon.getLocalizedString
    BASE_URL = "https://documentaryheaven.com/"

    menu_items = [{"label": localize(30000),
                   "url": BASE_URL + "all",
                   "action": "listall"},
                  {"label": localize(30001),
                   "url": BASE_URL + "watch-online",
                   "action": "listcategories"},
                  {"label": localize(30002),
                   "url": BASE_URL + "popular",
                   "action": "listalltime"},
                  {"label": localize(30003),
                   "url": BASE_URL + "best",
                   "action": "listthisyear"},
                  {"label": localize(30004),
                   "url": "Search",
                   "action": "search"}]

    YOUTUBE_PLUGIN = "plugin://plugin.video.youtube/"
    VIMEO_PLUGIN = "plugin://plugin.video.vimeo/"
    DAILYMOTION_PLUGIN = "plugin://plugin.video.dailymotion_com/"


    def __init__(self):
        self.scraper = WebScraper()


    def _add_folder_item(self, items, title, url, icon_url, fanart_url,
                         sort_title="", isfolder=True, isplayable=False,
                         date=None, info=None, context_menu_items=None):

        if fanart_url is None:
            fanart_url = os.path.join(self.addon_media, "fanart_blur.jpg")

        if icon_url is None:
            icon_url = os.path.join(self.addon_media, "icon_trans.png")

        li = ListItem(label=title)
        li.setArt({"thumb": icon_url, "fanart": fanart_url})
        li.setInfo("video", {"title": title, "sorttitle": sort_title})

        if isplayable:
            li.setProperty("IsPlayable", "true")
        else:
            li.setProperty("IsPlayable", "false")

        if date is not None:
            li.setInfo("video", {"date": date})

        if info is not None:
            li.setInfo("video", {"plot": info})

        if context_menu_items is not None:
            li.addContextMenuItems(context_menu_items)

        items.append((url, li, isfolder))


    def _end_folder(self, items, sort_methods=()):
        addDirectoryItems(self.addon_handle, items, totalItems=len(items))

        for sort_method in sort_methods:
            addSortMethod(self.addon_handle, sort_method)

        endOfDirectory(self.addon_handle)


    def main_menu_list(self):
        items = []
        for item in self.menu_items:
            url = "{0}?action={1}&url={2}".format(self.addon_url,
                                                  item["action"],
                                                  item["url"])
            self._add_folder_item(items, item["label"], url, None, None)

        self._end_folder(items)


    def all_list(self, content_url):
        html = self.scraper.get_html(content_url)
        videos = html.find_all("div", {"class": "post-thumbnail"})

        items = []
        for video in videos:
            try:
                video_url = video.find("a", href=True).get("href")
            except AttributeError:
                continue

            try:
                label = video.find("a", title=True).get("title")
            except AttributeError:
                label = "no title"

            try:
                icon = video.find("img", src=True).get("src")
            except AttributeError:
                icon = None

            try:
                video_info = video.next_sibling.text
            except AttributeError:
                video_info = None

            url = "{0}?action={1}&url={2}".format(self.addon_url,
                                                  "playmedia",
                                                  video_url)

            context_url = "{0}?action={1}&url={2}".format(self.addon_url,
                                                          "showplot",
                                                          url)
            context_menu = [(self.localize(30005),
                             "RunPlugin({0})".format(context_url))]
            self._add_folder_item(items, label, url, icon, None,
                                  info=video_info, isplayable=True,
                                  isfolder=False,
                                  context_menu_items=context_menu)
        try:
            next_page_url = html.find("link", {"rel": "next"}).get("href")
            url = "{0}?action={1}&url={2}".format(self.addon_url,
                                                  "listall",
                                                  next_page_url)
            self._add_folder_item(items, self.localize(30006), url, None, None)
        except AttributeError:
            pass

        self._end_folder(items)


    def categories_list(self, content_url):
        html = self.scraper.get_html(content_url)
        categories = html.find_all("a", {"class": "browse-all"})

        items = []
        for category in categories:
            try:
                label = category.text
                start = len("Browse ")
                end = label.find(" Documentaries")
                label = label[start:end]
                media_url = self.BASE_URL + category.get("href")
                url = "{0}?action={1}&url={2}".format(self.addon_url,
                                                      "listall",
                                                      media_url)
            except AttributeError:
                continue

            self._add_folder_item(items, label, url, None, None)

        self._end_folder(items)


    def toplist(self, content_url):
        html = self.scraper.get_html(content_url)
        videos = html.find_all("a", {"itemprop": "url"})

        items = []
        for (rank, video) in enumerate(videos):
            try:
                video_url = video.get("href")
            except AttributeError:
                continue

            try:
                label = video.get("title")
                label = "{0}. {1}".format(rank+1, label)
            except AttributeError:
                label = "no title"

            try:
                icon = video.find("img", src=True).get("src")
            except AttributeError:
                icon = None

            try:
                video_info = video.text
            except AttributeError:
                video_info = None

            url = "{0}?action={1}&url={2}".format(self.addon_url,
                                                  "playmedia",
                                                  video_url)

            context_url = "{0}?action={1}&url={2}".format(self.addon_url,
                                                          "showplot",
                                                          url)
            context_menu = [(self.localize(30005),
                             "RunPlugin({0})".format(context_url))]
            self._add_folder_item(items, label, url, icon, None,
                                  info=video_info, isplayable=True,
                                  isfolder=False,
                                  context_menu_items=context_menu)
        self._end_folder(items)


    def search(self):
        query = self.get_user_input(prompt_msg=self.localize(30004))
        if query == "":
            return

        items = []
        url = "{0}?action={1}&query={2}&offset=0".format(self.addon_url,
                                                         "listsearch",
                                                         query)
        self._add_folder_item(items, query, url, None, None)
        self._end_folder(items)


    def search_list(self, query, offset):
        query = query.replace(" ", "+")
        search_url = "https://api.qwant.com/v3/search/web/?" \
            "q=site%3Adocumentaryheaven.com+AND+{0}" \
            "&count=10&locale=en_gb&offset={1}".format(query, offset)

        json = self.scraper.get_json(search_url)
        if json["status"] != "success":
            return

        contents = json["data"]["result"]["items"]["mainline"]
        for content in contents:
            if content["type"] == "web":
                web_content = content
                break
        else:
            return

        items = []
        for item in web_content["items"]:
            video_url = item["url"]
            url = "{0}?action={1}&url={2}".format(self.addon_url,
                                                  "playmedia",
                                                  video_url)

            # Only want urls corresponding to videos
            if ".com/all/" in video_url or \
                    ".com/best/" in video_url or \
                    ".com/category/" in video_url or \
                    ".com/popular/" in video_url or \
                    ".com/watch-online/" in video_url:
                continue

            label = item["title"].split(" | Docu")[0].split(" - Docu")[0]
            context_url = "{0}?action={1}&url={2}".format(self.addon_url,
                                                          "showplot",
                                                          url)
            context_menu = [(self.localize(30005),
                        "RunPlugin({0})".format(context_url))]

            self._add_folder_item(items, label, url, None, None,
                                  isplayable=True, isfolder=False,
                                  info=item["desc"],
                                  context_menu_items=context_menu)

        url = "{0}?action={1}&query={2}&offset={3}".format(self.addon_url,
                                                           "listsearch",
                                                           query,
                                                           offset+10)
        self._add_folder_item(items, self.localize(30006), url, None, None)

        self._end_folder(items)


    def show_plot(self, documentary_url):
        html = self.scraper.get_html(documentary_url)

        try:
            title = html.find("meta", {"property": "og:title"}).get("content")
        except AttributeError:
            title = ""

        try:
            plot_text = html.find("div", {"class": "entry-content"}).text
            Dialog().textviewer("{0} - {1}".format(self.addon_name, title), plot_text)
        except AttributeError:
            Dialog().textviewer(self.addon_name, self.localize(30007))


    def play_video(self, documentary_url):
        html = self.scraper.get_html(documentary_url)
        video_url = html.find("meta", {"itemprop": "embedUrl"}).get("content")
        if ".youtube" in video_url:
            path = self._extract_youtube_video(video_url)
        elif ".vimeo" in video_url:
            path = self._extract_vimeo_video(video_url)
        elif ".dailymotion" in video_url:
            path = self._extract_dailymotion_video(video_url)
        elif "https://archive.org/" in video_url:
            path = self._extract_archive_video(video_url)

        play_item = ListItem(path=path)
        setResolvedUrl(self.addon_handle, True, listitem=play_item)


    def _extract_youtube_video(self, video_url):
        path = self.YOUTUBE_PLUGIN
        parsed_video_url = urlparse(video_url)
        video_path = parsed_video_url.path
        if "embed/" in video_path:
            video_id = video_path.split("embed/")[-1]
        elif "/p/" in video_path:
            video_id = video_path.split("/p/")[-1]

        video_params = dict(parse_qsl(parsed_video_url.query))
        if video_id == "videoseries":
            playlist_id = video_params["list"]
            path = path + "play/?playlist_id={0}&order=default&play=1".format(playlist_id)
        else:
            path = path + "play/?video_id={0}".format(video_id)
        return path


    def _extract_vimeo_video(self, video_url):
        path = self.VIMEO_PLUGIN
        parsed_video_url = urlparse(video_url)
        video_path = parsed_video_url.path
        video_id = video_path.split("video/")[-1]
        path = path + "play/?video_id={0}".format(video_id)
        return path


    def _extract_dailymotion_video(self, video_url):
        path = self.DAILYMOTION_PLUGIN
        parsed_video_url = urlparse(video_url)
        video_path = parsed_video_url.path
        video_id = video_path.split("video/")[-1]
        path = path + "?url={0}&mode=playVideo".format(video_id)
        return path


    def _extract_archive_video(self, video_url):
        html = self.scraper.get_html(video_url)
        path = html.find("meta", {"property": "og:video"}).get("content")
        return path


    @staticmethod
    def get_user_input(prompt_msg=""):
        keyboard = Keyboard("", prompt_msg)
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return ""

        input_str = keyboard.getText()
        return input_str
