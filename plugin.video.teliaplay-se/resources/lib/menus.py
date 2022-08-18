import os
import functools
import datetime
import uuid
import urllib.parse
import dateutil.parser
import pytz
import inputstreamhelper
import xbmc
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItems, addSortMethod, \
        endOfDirectory, setResolvedUrl, SORT_METHOD_TITLE, \
        SORT_METHOD_UNSORTED, SORT_METHOD_DATEADDED
from resources.lib.api import TeliaPlay, TeliaException
from resources.lib.kodiutils import AddonUtils, UserDataHandler, \
    SearchHistory
from resources.lib.timeutils import TimezoneStamps


def logging(method):
    addon = AddonUtils()
    debug = addon.get_setting_as_bool("debug")

    @functools.wraps(method)
    def wrapped_method_call(*args, **kwargs):
        if debug:
            args_repr = [repr(arg) for arg in args]
            kwargs_repr = [
                "{0}={1!r}".format(key, val)
                for (key, val) in list(kwargs.items())
            ]
            arguments = ", ".join(args_repr + kwargs_repr)
            addon.log("Calling {0}({1})".format(method.__name__, arguments))
        retval = method(*args, **kwargs)
        if debug:
            addon.log("Call returned successfully")
        return retval
    return wrapped_method_call


class MenuList():

    def __init__(self):
        self.addon = AddonUtils()
        self.userdata_handler = UserDataHandler()

        username = self.addon.get_setting(
            "user" + self.addon.get_setting("defaultUser")
        )

        password = self.addon.get_setting(
            "pass" + self.addon.get_setting("defaultUser")
        )

        self.search_history = SearchHistory(username)
        userdata = self.userdata_handler.get(username)

        if not userdata:
            userdata = self.telia_login(username, password)
            self.userdata_handler.add(username, userdata)
            userdata = self.userdata_handler.get(username)

        self.telia_play = TeliaPlay(userdata)

        token_valid_time = dateutil.parser.isoparse(
            userdata["tokenData"]["validTo"]
        ) - datetime.timedelta(minutes=30)

        time_now = datetime.datetime.now(pytz.timezone("Europe/Stockholm"))

        if time_now >= token_valid_time:
            token_data = self.telia_play.refresh_token()
            userdata["tokenData"] = token_data
            self.userdata_handler.add(username, userdata)

    def _add_folder_item(
        self, items, label, url, icon=None, fanart=None, sort_title="",
        genre="", info="", datetime_str="", duration=0, is_folder=True,
        is_playable=False, context_menu_items=None, offscreen=True,
        imdb="", rating="", title=""
    ):

        if not fanart:
            fanart = os.path.join(self.addon.resources, "fanart.jpg")

        if not icon:
            icon = os.path.join(self.addon.media, "telia_logo.png")

        list_item = ListItem(label=label, offscreen=offscreen)
        list_item.setArt({"thumb": icon, "fanart": fanart})
        if title:
            list_item.setInfo("video", {
                "title": title, "sorttitle": sort_title
            })
        else:
            list_item.setInfo("video", {
                "title": label, "sorttitle": sort_title
            })

        if is_playable:
            list_item.setProperty("IsPlayable", "true")
        else:
            list_item.setProperty("IsPlayable", "false")

        if datetime_str:
            list_item.setInfo("video", {"dateadded": datetime_str})

        if duration:
            list_item.setInfo("video", {"duration": duration})

        if info:
            list_item.setInfo("video", {"plot": info})

        if imdb:
            list_item.setInfo("video", {"imdbnumber": imdb})

        if rating:
            list_item.setInfo("video", {"rating": rating})

        if genre:
            list_item.setInfo("video", {"genre": genre})

        if context_menu_items:
            list_item.addContextMenuItems(context_menu_items)

        items.append((url, list_item, is_folder))

    def _end_folder(self, items, sort_methods=()):
        addDirectoryItems(self.addon.handle, items, totalItems=len(items))

        for sort_method in sort_methods:
            addSortMethod(self.addon.handle, sort_method)

        endOfDirectory(self.addon.handle)

    @logging
    def telia_login(self, username, password):
        boot_uuid = str(uuid.uuid4())
        device_uuid = "WEB-" + boot_uuid
        userdata = {
            "bootUUID": boot_uuid,
            "deviceUUID": device_uuid,
            "tokenData": None
        }
        telia_play = TeliaPlay(userdata)
        token_data = telia_play.login(username, password)
        telia_play.validate_login()
        userdata["tokenData"] = token_data
        return userdata

    @logging
    def main_menu(self):
        menu_items = self.telia_play.get_main_menu()

        items = []
        for item in menu_items:
            plugin_url = self.addon.plugin_url({
                "menu": "page",
                "pageId": item["id"]
            })
            self._add_folder_item(items, item["name"], plugin_url)

        plugin_url = self.addon.plugin_url({
            "menu": "searchmenu",
        })
        self._add_folder_item(items, self.addon.localize(30016), plugin_url)
        self._end_folder(items)

    @logging
    def search_menu(self):
        items = []
        plugin_url = self.addon.plugin_url({
            "menu": "newsearch",
        })
        self._add_folder_item(items, self.addon.localize(30017), plugin_url)

        plugin_url = self.addon.plugin_url({
            "menu": "history",
        })
        self._add_folder_item(items, self.addon.localize(30018), plugin_url)
        self._end_folder(items)

    @logging
    def search(self):
        query = self.addon.get_user_input(self.addon.localize(30102))
        if query != "":
            self.search_history.add(query)
            return self.search_history.get_id(query, reload_data=True)
        return None

    @logging
    def show_search_history(self):
        items = []
        for (query_id, query) in enumerate(self.search_history.get_queries()):
            url = "{0}?menu={1}&panelId={2}&page=0".format(
                self.addon.url, "search", query_id
            )
            remove_url = "{0}?menu={1}&panelId={2}".format(
                self.addon.url, "removesearch", query_id
            )
            clear_url = "{0}?menu={1}".format(self.addon.url, "clearsearch")
            context_menu = [
                (self.addon.localize(30103), "RunPlugin({0})".format(remove_url)),
                (self.addon.localize(30104), "RunPlugin({0})".format(clear_url))
            ]
            self._add_folder_item(
                items, query, url, None, None, context_menu_items=context_menu)

        self._end_folder(items)

    @logging
    def search_history_update(self, action, remove_id=None):
        if action == "removesearch":
            if remove_id is not None:
                self.search_history.remove(remove_id)
        elif action == "clearsearch":
            self.search_history.clear()

    def refresh(self):
        xbmc.executebuiltin("Container.Refresh")

    @logging
    def page_menu(self, page_id):
        menu_items = self.telia_play.get_page(page_id)

        items = []
        for item in menu_items:
            plugin_url = self.addon.plugin_url({
                "menu": "page", "pageId": page_id, "mode": item["title"]
            })
            if item["title"] != "":
                self._add_folder_item(items, item["title"], plugin_url)
        self._end_folder(items)

    @logging
    def page_submenu(self, page_id, menu_id):
        start_menu = self.telia_play.get_page(page_id)

        for submenu in start_menu:
            if menu_id == submenu["title"]:
                if submenu["__typename"] == "SelectionMediaPanel":
                    menu = submenu["selectionMediaContent"]
                elif submenu["__typename"] == "MediaPanel":
                    menu = submenu["mediaContent"]
                elif submenu["__typename"] == "ContinueWatchingPanel":
                    menu = submenu["continueWatchingContent"]
                elif submenu["__typename"] == "MyListPanel":
                    menu = submenu["myListContent"]
                elif submenu["__typename"] == "TimelinePanel":
                    menu = submenu["timelineContent"]
                elif submenu["__typename"] == "RentalsPanel":
                    menu = submenu["rentalsContent"]
                elif submenu["__typename"] == "ShowcasePanel":
                    menu = submenu["showcaseContent"]
                elif submenu["__typename"] == "SingleFeaturePanel":
                    self.play_stream(submenu["id"], "vod")
                elif submenu["__typename"] == "StoresPanel":
                    menu = submenu["storesContent"]
                    self.play_stores_menu(menu["items"])
                    return
                break
        else:
            return

        menu_items = menu["items"]
        if not menu_items:
            menu_items = []

        items = []
        for item in menu_items:
            media = item["media"]

            try:
                icon = urllib.parse.unquote(
                    media["images"]["showcard2x3"]["source"]
                )
            except Exception:
                icon = None

            try:
                fanart = urllib.parse.unquote(
                    media["images"]["showcard16x9"]["source"]
                )
            except Exception:
                fanart = None

            try:
                genre = media["genre"]
            except Exception:
                genre = ""

            try:
                desc = media["description"]
            except Exception:
                desc = ""

            if not desc:
                try:
                    desc = media["descriptionLong"]
                except Exception:
                    desc = ""

            try:
                imdb_url = media["ratings"]["imdb"]["url"]
                imdb = imdb_url.split("/")[-1]
            except Exception:
                imdb = ""

            try:
                rating = media["ratings"]["imdb"]["readableScore"]
            except Exception:
                rating = ""

            try:
                duration = media["duration"]["readableShort"]
                duration = TimezoneStamps(
                    "Europe/Stockholm"
                ).convert_to_seconds(duration)
            except Exception:
                duration = 0

            context_url_add = self.addon.plugin_url({
                "menu": "addToList" if menu_id != "Min lista"
                else "removeFromList",
                "mediaId": media["id"],
            })
            context_menu = [
                (self.addon.localize(
                    30103 if menu_id == "Min lista" else 30020
                ),
                 "RunPlugin({0})".format(context_url_add))
            ]

            try:
                title = media["title"]
                label = "{0} [COLOR red]({1})[/COLOR]".format(
                    title, media["price"]["readable"]
                )
                context_url_rent = self.addon.plugin_url({
                    "menu": "rent",
                    "videoId": media["id"]
                })
                context_url_trailer = self.addon.plugin_url({
                    "menu": "play",
                    "streamType": "trailer",
                    "streamId": media["id"]
                })
                context_menu.append(
                    (self.addon.localize(30019),
                     "PlayMedia({0})".format(context_url_trailer))
                )
                context_menu.append(
                    (self.addon.localize(30015),
                     "RunPlugin({0})".format(context_url_rent))
                )
                is_rental = True
            except Exception:
                label = media["title"]
                is_rental = False

            if media["id"].startswith("s"):
                plugin_url = self.addon.plugin_url({
                    "menu": "series",
                    "seriesId": media["id"]
                })
                is_folder = True
                is_playable = False
            elif media["id"].startswith("m"):
                plugin_url = self.addon.plugin_url({
                    "menu": "play",
                    "streamType": "rental" if is_rental else "vod",
                    "streamId": media["id"]
                })
                is_folder = False
                is_playable = True

            self._add_folder_item(
                items, label, plugin_url, icon, fanart, genre=genre,
                is_playable=is_playable, is_folder=is_folder, info=desc,
                imdb=imdb, duration=duration, context_menu_items=context_menu,
                rating=rating, title=title
            )

        if "pageInfo" in menu and menu["pageInfo"]["hasNextPage"]:
            plugin_url = self.addon.plugin_url({
                "menu": "panel",
                "panelId": submenu["id"],
                "page": 0
            })

            self._add_folder_item(
                items, self.addon.localize(30013), plugin_url
            )

        self._end_folder(items)

    @logging
    def play_stores_menu(self, channels=None):

        def add_channel(items, channel):
            try:
                icon = urllib.parse.unquote(
                    channel["icons"]["dark"]["source"]
                )
            except Exception:
                icon = None

            plugin_url = self.addon.plugin_url({
                "menu": "page",
                "mode": "Alla Playtjänster",
                "storeId": channel["id"]
            })

            self._add_folder_item(
                items, channel["name"], plugin_url, icon=icon
            )

        items = []
        if channels is None:
            services = self.telia_play.get_page("all-stores")

            for service in services:
                for channel in service["storesContent"]["items"]:
                    add_channel(items, channel)
        else:
            for channel in channels:
                add_channel(items, channel)

        self._end_folder(items, (SORT_METHOD_UNSORTED, SORT_METHOD_TITLE))

    @logging
    def play_store_menu(self, store_id):
        store_panels = self.telia_play.get_store(store_id)

        items = []
        for panel in store_panels["pagePanels"]["items"]:
            try:
                icon = urllib.parse.unquote(
                    store_panels["icons"]["dark"]["source"]
                )
            except Exception:
                icon = None

            if not panel["title"]:
                panel["title"] = self.addon.localize(30011)

            plugin_url = self.addon.plugin_url({
                "menu": "storePanel",
                "storeId": store_id,
                "panelId": panel["id"]
            })

            self._add_folder_item(
                items, panel["title"], plugin_url, icon=icon
            )

        self._end_folder(items, (SORT_METHOD_UNSORTED, SORT_METHOD_TITLE))

    @logging
    def store_panel_menu(self, store_id, panel_id):
        store_panels = self.telia_play.get_store(store_id)["pagePanels"]

        for panel in store_panels["items"]:
            if panel_id == panel["id"]:
                if panel["__typename"] == "SelectionMediaPanel":
                    panel = panel["selectionMediaContent"]
                elif panel["__typename"] == "MediaPanel":
                    panel = panel["mediaContent"]
                break
        else:
            return

        items = []
        for item in panel["items"]:
            media = item["media"]
            try:
                icon = urllib.parse.unquote(
                    media["images"]["showcard2x3"]["source"]
                )
            except Exception:
                icon = None

            try:
                fanart = urllib.parse.unquote(
                    media["images"]["showcard16x9"]["source"]
                )
            except Exception:
                fanart = None

            try:
                description = media["descriptionLong"]
            except Exception:
                description = ""

            try:
                genre = media["genre"]
            except Exception:
                genre = ""

            try:
                imdb_url = media["ratings"]["imdb"]["url"]
                imdb = imdb_url.split("/")[-1]
            except Exception:
                imdb = ""

            try:
                rating = media["ratings"]["imdb"]["readableScore"]
            except Exception:
                rating = ""

            try:
                duration = media["duration"]["readableShort"]
                duration = TimezoneStamps(
                    "Europe/Stockholm"
                ).convert_to_seconds(duration)
            except Exception:
                duration = 0

            context_url_add = self.addon.plugin_url({
                "menu": "addToList",
                "mediaId": media["id"],
            })
            context_menu = [
                (self.addon.localize(30020),
                 "RunPlugin({0})".format(context_url_add))
            ]
            try:
                title = media["title"]
                label = "{0} [COLOR red]({1})[/COLOR]".format(
                    title, media["price"]["readable"]
                )
                context_url_rent = self.addon.plugin_url({
                    "menu": "rent",
                    "videoId": media["id"]
                })
                context_url_trailer = self.addon.plugin_url({
                    "menu": "play",
                    "streamType": "trailer",
                    "streamId": media["id"]
                })
                context_menu.append(
                    (self.addon.localize(30019),
                     "PlayMedia({0})".format(context_url_trailer))
                )
                context_menu.append(
                    (self.addon.localize(30015),
                     "RunPlugin({0})".format(context_url_rent))
                )
                is_rental = True
            except Exception:
                label = media["title"]
                is_rental = False

            if media["id"].startswith("s"):
                plugin_url = self.addon.plugin_url({
                    "menu": "series",
                    "seriesId": media["id"]
                })
                is_folder = True
                is_playable = False
            elif media["id"].startswith("m"):
                plugin_url = self.addon.plugin_url({
                    "menu": "play",
                    "streamType": "rental" if is_rental else "vod",
                    "streamId": media["id"]
                })
                is_folder = False
                is_playable = True

            self._add_folder_item(
                items, label, plugin_url, icon, fanart,
                info=description, genre=genre, is_playable=is_playable,
                is_folder=is_folder, imdb=imdb, duration=duration,
                context_menu_items=context_menu, rating=rating, title=title
            )

        if "pageInfo" in panel and panel["pageInfo"]["hasNextPage"]:
            plugin_url = self.addon.plugin_url({
                "menu": "panel",
                "panelId": panel_id,
                "page": 0
            })

            self._add_folder_item(
                items, self.addon.localize(30013), plugin_url
            )

        self._end_folder(items)

    @logging
    def panel_menu(self, panel_id, page, search=False):
        results_per_page = self.addon.get_setting_as_int("moviesPerPage")
        offset = page*results_per_page

        if not search:
            panel = self.telia_play.get_panel(
                panel_id, results_per_page, offset
            )
        else:
            # Reuse panel menu for search menu; no need to reinvent the wheel.
            query = self.search_history.get(panel_id)
            # Searching won't work if the number of results per page is too large.
            results_per_page = 50
            offset = page*results_per_page
            panel = self.telia_play.search(query, results_per_page, offset)

        items = []
        try:
            if not search:
                panel_items = panel["items"]
            else:
                panel_items = panel["searchItems"]
        except KeyError:
            panel_items = []

        for item in panel_items:
            media = item["media"]
            try:
                icon = urllib.parse.unquote(
                    media["images"]["showcard2x3"]["source"]
                )
            except Exception:
                icon = None

            try:
                fanart = urllib.parse.unquote(
                    media["images"]["showcard16x9"]["source"]
                )
            except Exception:
                fanart = None

            try:
                description = media["descriptionLong"]
            except Exception:
                description = ""

            try:
                genre = media["genre"]
            except Exception:
                genre = ""

            try:
                imdb_url = media["ratings"]["imdb"]["url"]
                imdb = imdb_url.split("/")[-1]
            except Exception:
                imdb = ""

            try:
                rating = media["ratings"]["imdb"]["readableScore"]
            except Exception:
                rating = ""

            try:
                duration = media["duration"]["readableShort"]
                duration = TimezoneStamps(
                    "Europe/Stockholm"
                ).convert_to_seconds(duration)
            except Exception:
                duration = 0

            context_url_add = self.addon.plugin_url({
                "menu": "addToList",
                "mediaId": media["id"],
            })
            context_menu = [
                (self.addon.localize(30020),
                 "RunPlugin({0})".format(context_url_add))
            ]
            try:
                title = media["title"]
                label = "{0} [COLOR red]({1})[/COLOR]".format(
                    title, media["price"]["readable"]
                )
                context_url_rent = self.addon.plugin_url({
                    "menu": "rent",
                    "videoId": media["id"]
                })
                context_url_trailer = self.addon.plugin_url({
                    "menu": "play",
                    "streamType": "trailer",
                    "streamId": media["id"]
                })
                context_menu.append(
                    (self.addon.localize(30019),
                     "PlayMedia({0})".format(context_url_trailer))
                )
                context_menu.append(
                    (self.addon.localize(30015),
                     "RunPlugin({0})".format(context_url_rent))
                )
                is_rental = True
            except Exception:
                label = media["title"]
                is_rental = False

            if media["id"].startswith("s"):
                plugin_url = self.addon.plugin_url({
                    "menu": "series",
                    "seriesId": media["id"]
                })
                is_folder = True
                is_playable = False
            elif media["id"].startswith("m"):
                plugin_url = self.addon.plugin_url({
                    "menu": "play",
                    "streamType": "rental" if is_rental else "vod",
                    "streamId": media["id"]
                })
                is_folder = False
                is_playable = True

            self._add_folder_item(
                items, label, plugin_url, icon, fanart,
                info=description, genre=genre, is_playable=is_playable,
                is_folder=is_folder, imdb=imdb, rating=rating,
                context_menu_items=context_menu, title=title, duration=duration
            )

        if "pageInfo" in panel and panel["pageInfo"]["hasNextPage"]:
            plugin_url = self.addon.plugin_url({
                "menu": "search" if search else "panel",
                "panelId": panel_id,
                "page": page+1
            })

            self._add_folder_item(
                items, self.addon.localize(30014), plugin_url
            )

        self._end_folder(items)

    @logging
    def rent_menu(self, video_id):
        rent_ok = Dialog().yesno(self.addon.name, self.addon.localize(30101))

        if rent_ok:
            tz_sthlm_stamps = TimezoneStamps("Europe/Stockholm")
            pin_code = self.addon.get_setting(
                "PIN" + self.addon.get_setting("DefaultUser")
            )
            vod = self.telia_play.get_vod(video_id)
            try:
                receipt = self.telia_play.rent_video(
                    vod["id"], pin_code
                )["mediaRentals"][0]
            except TeliaException as te:
                if str(te) == "Pincode is invalid":
                    pin_code = Dialog().numeric(0, self.addon.localize(30105))
                    receipt = self.telia_play.rent_video(
                        vod["id"], pin_code
                    )["mediaRentals"][0]
                else:
                    raise

            receipt["startTime"] = tz_sthlm_stamps.local_datetime_str(
                receipt["startTime"], "%c", "ms"
            )
            receipt["endTime"] = tz_sthlm_stamps.local_datetime_str(
                receipt["endTime"], "%c", "ms"
            )

            # Display super fancy invoice
            receipt_str = ""
            for (key, val) in list(receipt.items()):
                receipt_str = receipt_str + \
                    "[COLOR blue]{0}[/COLOR]: {1}\n".format(key, val)
            header = "{0} - {1}".format(
                self.addon.name, self.addon.localize(30106)
            )
            Dialog().textviewer(header, receipt_str)

    @logging
    def series_menu(self, series_id):
        series = self.telia_play.get_series(series_id)
        if not series:
            return

        media = series["suggestedEpisode"]
        if not media:
            return

        try:
            icon = urllib.parse.unquote(
                series["images"]["backdrop16x9"]["source"]
            )
        except Exception:
            icon = None

        try:
            fanart = urllib.parse.unquote(
                series["images"]["backdrop16x9"]["source"]
            )
        except Exception:
            fanart = None

        try:
            description = media["descriptionLong"]
        except Exception:
            description = ""

        try:
            genre = media["genre"]
        except Exception:
            genre = ""

        try:
            duration = media["duration"]["readableShort"]
            duration = TimezoneStamps(
                "Europe/Stockholm"
            ).convert_to_seconds(duration)
        except Exception:
            duration = 0

        context_url_add = self.addon.plugin_url({
            "menu": "addToList",
            "mediaId": media["id"],
        })
        context_menu = [
            (self.addon.localize(30020),
             "RunPlugin({0})".format(context_url_add))
        ]
        try:
            label = "{0} [COLOR red]({1})[/COLOR]".format(
                media["episodeNumber"]["readable"], media["price"]["readable"]
            )
            context_url_rent = self.addon.plugin_url({
                "menu": "rent",
                "videoId": media["id"]
            })
            context_url_trailer = self.addon.plugin_url({
                "menu": "play",
                "streamType": "trailer",
                "streamId": media["id"]
            })
            context_menu.append(
                (self.addon.localize(30019),
                 "PlayMedia({0})".format(context_url_trailer))
            )
            context_menu.append(
                (self.addon.localize(30015),
                 "RunPlugin({0})".format(context_url_rent))
            )
            is_rental = True
        except Exception:
            label = media["episodeNumber"]["readable"]
            is_rental = False

        if media["id"].startswith("s"):
            plugin_url = self.addon.plugin_url({
                "menu": "series",
                "seriesId": media["id"]
            })
            is_folder = True
            is_playable = False
        elif media["id"].startswith("m"):
            plugin_url = self.addon.plugin_url({
                "menu": "play",
                "streamType": "rental" if is_rental else "vod",
                "streamId": media["id"]
            })
            is_folder = False
            is_playable = True

        items = []
        self._add_folder_item(
            items, label, plugin_url, icon, fanart, info=description,
            is_folder=is_folder, is_playable=is_playable, genre=genre,
            duration=duration, context_menu_items=context_menu
        )

        for season in media["series"]["seasonLinks"]["items"]:
            try:
                icon = urllib.parse.unquote(
                    series["images"]["showcard2x3"]["source"]
                )
            except Exception:
                icon = None

            try:
                fanart = urllib.parse.unquote(
                    series["images"]["backdrop16x9"]["source"]
                )
            except Exception:
                fanart = None

            try:
                description = season["descriptionLong"]
            except Exception:
                description = ""

            plugin_url = self.addon.plugin_url({
                "menu": "season",
                "seasonId": season["id"]
            })

            label = "{0} {1}".format(
                self.addon.localize(30012), season["seasonNumber"]["number"])

            self._add_folder_item(
                items, label, plugin_url, icon, fanart, info=description
            )

        self._end_folder(items)

    @logging
    def season_menu(self, season_id):
        episodes = self.telia_play.get_season(season_id)

        items = []
        for episode in episodes:
            episode = episode["episode"]
            try:
                icon = urllib.parse.unquote(
                    episode["images"]["showcard2x3"]["source"]
                )
            except Exception:
                icon = None

            try:
                fanart = urllib.parse.unquote(
                    episode["images"]["showcard16x9"]["source"]
                )
            except Exception:
                fanart = None

            try:
                description = episode["descriptionLong"]
            except Exception:
                description = ""

            try:
                tz_sthlm_stamps = TimezoneStamps("Europe/Stockholm")
                datetime_str = tz_sthlm_stamps.local_datetime_str(
                    episode["availableFrom"]["timestamp"],
                    "%Y-%m-%d %H:%M:%S", "ms"
                )
                date_label = tz_sthlm_stamps.local_datetime_str(
                    episode["availableFrom"]["timestamp"], "%x", "ms"
                )
                time_label = tz_sthlm_stamps.local_datetime_str(
                    episode["availableFrom"]["timestamp"], "%X", "ms"
                )
                time_label = tz_sthlm_stamps.strip_seconds(time_label)
            except Exception:
                datetime_str = ""
                date_label = ""
                time_label = ""

            try:
                duration = episode["duration"]["readableShort"]
                duration = TimezoneStamps(
                    "Europe/Stockholm"
                ).convert_to_seconds(duration)
            except Exception:
                duration = 0

            try:
                episode_label = "{0} [COLOR red]({1})[/COLOR]".format(
                    episode["episodeNumber"]["readable"],
                    episode["price"]["readable"]
                )
                context_url = self.addon.plugin_url({
                    "menu": "rent",
                    "videoId": episode["id"]
                })
                context_menu = [
                    (self.addon.localize(30015),
                     "RunPlugin({0})".format(context_url))
                ]
                is_rental = True
            except Exception:
                episode_label = episode["episodeNumber"]["readable"]
                context_menu = None
                is_rental = False

            plugin_url = self.addon.plugin_url({
                "menu": "play",
                "streamType": "rental" if is_rental else "vod",
                "streamId": episode["id"]
            })

            label = "{0} [COLOR orange]{1}[/COLOR] [COLOR yellow]{2}[/COLOR]".format(
                episode_label, date_label, time_label
            )

            self._add_folder_item(
                items, label, plugin_url, icon, fanart, info=description,
                is_playable=True, is_folder=False, datetime_str=datetime_str,
                duration=duration, context_menu_items=context_menu
            )

        self._end_folder(items, sort_methods=(SORT_METHOD_DATEADDED,))

    @logging
    def tv_channels_menu(self, page=0):
        channel_limit = self.addon.get_setting_as_int("channelsPerPage")
        offset = channel_limit*page
        tz_sthlm_stamps = TimezoneStamps("Europe/Stockholm")
        menu = self.telia_play.get_channels(
            tz_sthlm_stamps.now("ms"), channel_limit, offset
        )

        items = []
        for channel in menu["channelItems"]:
            try:
                icon = urllib.parse.unquote(channel["icons"]["dark"]["source"])
            except Exception:
                icon = None
            try:
                program = channel["programs"]["programItems"][0]
            except IndexError:
                continue
            try:
                fanart = urllib.parse.unquote(
                    program["media"]["images"]["showcard16x9"]["source"]
                )
            except Exception:
                fanart = None

            context_url = self.addon.plugin_url({
                "menu": "page",
                "pageId": "epg",
                "dayOffset": "{0}",
                "channelId": channel["id"]
            })

            tz_sthlm_stamps = TimezoneStamps("Europe/Stockholm")
            context_menu = []
            for day_offset in range(-7, 8):
                timestamp = tz_sthlm_stamps.today(day_offset, units="ms")
                menu_entry_label = tz_sthlm_stamps.local_datetime_str(
                    timestamp, "%a %d %b", "ms"
                )
                if day_offset == 0:
                    menu_entry_label = "[COLOR blue]{0}[/COLOR]".format(
                        menu_entry_label
                    )
                context_menu.append(
                    (menu_entry_label,
                     "ActivateWindow(videos, {0}, return)".format(
                         urllib.parse.unquote(context_url).format(day_offset)
                     ))
                )

            plugin_url = self.addon.plugin_url({
                "menu": "play",
                "streamType": "live",
                "streamId": channel["id"]
            })

            program_description = program["media"]["descriptionLong"]
            self._add_folder_item(
                items, program["media"]["title"], plugin_url, icon=icon,
                fanart=fanart, info=program_description, is_folder=False,
                is_playable=True, offscreen=False,
                context_menu_items=context_menu
            )

        if "pageInfo" in menu and menu["pageInfo"]["hasNextPage"]:
            plugin_url = self.addon.plugin_url({
                "menu": "page",
                "pageId": "epg",
                "page": page+1
            })

            self._add_folder_item(
                items, self.addon.localize(30013), plugin_url
            )
        self._end_folder(items)

    @logging
    def tv_programs_menu(self, channel_id, day_offset):
        tz_sthlm_stamps = TimezoneStamps("Europe/Stockholm")
        timestamp = tz_sthlm_stamps.today(int(day_offset), "ms")

        channel = self.telia_play.get_channel(
            channel_id, timestamp
        )

        items = []
        for program in channel["programs"]["programItems"]:
            try:
                icon = urllib.parse.unquote(
                    program["media"]["images"]["showcard2x3"]["source"]
                )
            except Exception:
                icon = None
            try:
                fanart = urllib.parse.unquote(
                    program["media"]["images"]["showcard16x9"]["source"]
                )
            except Exception:
                fanart = None

            try:
                imdb_url = program["media"]["ratings"]["imdb"]["url"]
                imdb = imdb_url.split("/")[-1]
            except Exception:
                imdb = ""

            try:
                rating = program["media"]["ratings"]["imdb"]["readableScore"]
            except Exception:
                rating = ""

            timestamp_now = tz_sthlm_stamps.now("ms")

            start_timestamp = program["startTime"]["timestamp"]
            end_timestamp = program["endTime"]["timestamp"]
            is_live = start_timestamp <= timestamp_now <= end_timestamp
            duration = (end_timestamp - start_timestamp) // 1000

            start_time = tz_sthlm_stamps.local_datetime_str(
                start_timestamp, "%X", "ms"
            )
            start_time = tz_sthlm_stamps.strip_seconds(start_time)

            end_time = tz_sthlm_stamps.local_datetime_str(
                end_timestamp, "%X", "ms"
            )
            end_time = tz_sthlm_stamps.strip_seconds(end_time)

            title = program["media"]["title"]
            label = "[COLOR yellow]{2}[/COLOR] [COLOR {0}]{1}[/COLOR]".format(
                "blue" if is_live else "white", title, start_time
            )

            if is_live:
                stream_type = "live_vod"
            else:
                stream_type = "vod"

            plugin_url = self.addon.plugin_url({
                "menu": "play",
                "streamType": stream_type,
                "streamId": program["media"]["id"]
            })

            self._add_folder_item(
                items, label, plugin_url, icon=icon, fanart=fanart,
                info=program["media"]["descriptionLong"], is_folder=False,
                is_playable=True, duration=duration, imdb=imdb, rating=rating,
                title=title
            )

        self._end_folder(items)

    @logging
    def play_stream(self, stream_id, stream_type):
        if stream_type == "live_vod":
            stream_type = "vod"
            is_live_vod = True
        else:
            is_live_vod = False

        self.telia_play.validate_stream()
        stream = self.telia_play.get_stream(stream_id, stream_type)

        is_helper = inputstreamhelper.Helper("mpd", drm="com.widevine.alpha")
        if is_helper.check_inputstream():
            play_item = ListItem(path=stream["url"])
            play_item.setContentLookup(False)
            play_item.setMimeType("application/dash+xml")
            play_item.setProperty("inputstream", is_helper.inputstream_addon)
            play_item.setProperty("inputstream.adaptive.manifest_type", "mpd")
            if stream_type != "trailer":
                license_url = stream["drm"]["licenseUrl"]
                license_headers = "User-Agent=kodi.tv&Content-Type=&{0}".format(
                    urllib.parse.urlencode(stream["drm"]["headers"])
                )
                play_item.setProperty(
                    "inputstream.adaptive.license_type", "com.widevine.alpha"
                )
                play_item.setProperty(
                    "inputstream.adaptive.license_key",
                    "{url}|{headers}|R{{SSM}}|".format(
                        url=license_url,
                        headers=license_headers
                    )
                )

        if is_live_vod and Dialog().yesno(
            self.addon.name, self.addon.localize(30100)
        ):
            setResolvedUrl(self.addon.handle, True, listitem=play_item)
            # Wait for vod stream to start and set playback from the beginning
            xbmc.sleep(4000)
            xbmc.Player().seekTime(0.0)
        else:
            setResolvedUrl(self.addon.handle, True, listitem=play_item)
            xbmc.sleep(4000)

        while xbmc.Player().isPlaying():
            xbmc.sleep(250)

        self.telia_play.delete_stream()
