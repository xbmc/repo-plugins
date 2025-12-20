import json
import os
import sys
from datetime import datetime
from typing import Any, Iterator
from urllib.parse import parse_qs, urlencode

import inputstreamhelper
import invidious_api
import requests
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
from infotagger.listitem import ListItemInfoTag


class SearchHistory:
    """Keep fixed length list of search queries, with the latest search
    query top."""

    def __init__(self, history_path: str, depth: int = 10):
        self.history_path = history_path
        self.depth = depth

        d = os.path.dirname(history_path)
        if not os.path.exists(d):
            xbmc.log(f"invidous created state directory {d}.", xbmc.LOGDEBUG)
            os.mkdir(d)

    def push(self, query: str):
        if xbmcvfs.exists(self.history_path):
            with open(self.history_path, "r") as file:
                queries = json.load(file)
        else:
            queries = []

        if query in queries:
            # Remove existing entry to move it forward
            queries.remove(query)

        queries.insert(0, query)

        queries = queries[: self.depth]

        with open(self.history_path, "w+") as file:
            json.dump(queries, file)

    def queries(self):
        if not xbmcvfs.exists(self.history_path):
            return []
        with open(self.history_path, "r") as file:
            return json.load(file)


class InvidiousPlugin:

    INSTANCESURL = "https://api.invidious.io/instances.json?sort_by=type,health"

    def __init__(self, base_url: str, addon_handle: int, args: dict[str, Any]):
        self.base_url = base_url
        self.addon_handle = addon_handle
        self.addon = xbmcaddon.Addon()
        self.args = args
        self.api_client = None
        path = xbmcvfs.translatePath(self.addon.getAddonInfo("profile"))
        self.search_history = SearchHistory(path + "search-history.json", 20)

        settings = self.addon.getSettings()
        self.auto_instance = settings.getBool("auto_instance")
        self.disable_dash = settings.getBool("disable_dash")
        self.show_instance_trending = settings.getBool("show_instance_trending")
        self.show_instance_popular = settings.getBool("show_instance_popular")
        instance_auth = None
        if self.auto_instance or not settings.getString("instance_url"):
            instance_url = self.instance_autodetect()
            self.addon.setSetting("instance_url", instance_url)
        else:
            instance_url = self.addon.getSetting("instance_url")
            if settings.getString("instance_username") and not self.auto_instance:
                instance_auth = {
                    "username": settings.getString("instance_username"),
                    "password": settings.getString("instance_password"),
                }
        if not instance_url:
            return

        xbmc.log(f"invidous using instance {instance_url}.", xbmc.LOGINFO)
        self.api_client = invidious_api.InvidiousAPIClient(
            instance_url, auth=instance_auth
        )

    def instance_autodetect(self):
        xbmc.log("invidious picking instance automatically.", xbmc.LOGINFO)

        response = requests.get(self.INSTANCESURL, timeout=5)
        data = response.json()
        for instanceinfo in data:
            xbmc.log(
                "invidious considering instance " + str(instanceinfo), xbmc.LOGDEBUG
            )
            instancename, instance = instanceinfo
            if "https" == instance["type"] \
               and instance["api"] is not False \
               and instance["monitor"]["down_since"] is None:
                instance_url = instance["uri"]
                # Make sure the instance work for us.  This test avoid
                # those rejecting us with HTTP status 429.  Some
                # instances return a sensible value for the special
                # lists but not for an individual video, so test with
                # a fairly randomly picked video id to avoid partly
                # working instances.
                test_video_id = "1l2_uCyBXQ0"
                api_client = invidious_api.InvidiousAPIClient(instance_url)
                try:
                    api_client.fetch_video_information(test_video_id)
                    return instance_url
                except Exception:
                    xbmc.log(
                        f"rejecting non-working instance {instanceinfo}", xbmc.LOGDEBUG
                    )

        xbmc.log(
            "invidious no working https type instance with API support returned from api.invidious.io.",
            xbmc.LOGWARNING,
        )
        # FIXME figure out how to show failing autodetection to the user.
        dialog = xbmcgui.Dialog()
        dialog.notification(
            self.addon.getLocalizedString(30012),
            self.addon.getLocalizedString(30013),
            "error",
        )
        return None

    def build_url(self, action, **kwargs):
        if not action:
            raise ValueError("you need to specify an action")

        kwargs["action"] = action

        return self.base_url + "?" + urlencode(kwargs)

    def add_directory_item(self, *args, **kwargs):
        xbmcplugin.addDirectoryItem(self.addon_handle, *args, **kwargs)

    def end_of_directory(self):
        xbmcplugin.endOfDirectory(self.addon_handle)

    def display_search_results(
        self, results: Iterator[invidious_api.InvidiousApiResponseType]
    ):
        # FIXME Add pagination support?
        for result in results:
            if result.type not in ["video", "channel", "playlist"]:
                raise RuntimeError("unknown result type " + result.type)

            list_item = xbmcgui.ListItem(result.heading)
            list_item.setArt(
                {
                    "thumb": result.thumbnail_url,
                }
            )

            # if this is NOT set, the plugin is called with an invalid handle when trying to play this item
            # seriously, Kodi? come on...
            # https://forum.kodi.tv/showthread.php?tid=173986&pid=1519987#pid1519987
            list_item.setProperty("IsPlayable", "true")
            if isinstance(result, invidious_api.VideoSearchResult):
                datestr = datetime.utcfromtimestamp(result.published).date().isoformat()

                info_tag = ListItemInfoTag(list_item, "video")
                info_tag.set_info(
                    {
                        "title": result.heading,
                        "mediatype": "video",
                        "plot": result.description,
                        "credits": result.author,
                        "date": datestr,
                        "dateadded": datestr,
                        "premiered": datestr,
                        "duration": result.duration,
                    }
                )

                url = self.build_url("play_video", video_id=result.id)
                self.add_directory_item(url=url, listitem=list_item)
            elif isinstance(result, invidious_api.ChannelSearchResult):
                url = self.build_url("view_channel", channel_id=result.id)
                info_tag = ListItemInfoTag(list_item, "video")
                info_tag.set_info(
                    {
                        "title": result.heading,
                        "plot": result.description,
                    }
                )
                self.add_directory_item(url=url, listitem=list_item, isFolder=True)
            elif isinstance(result, invidious_api.PlaylistSearchResult):
                url = self.build_url("view_playlist", playlist_id=result.id)
                self.add_directory_item(url=url, listitem=list_item, isFolder=True)

        self.end_of_directory()

    def display_new_search(self):
        # query search with a dialog
        dialog = xbmcgui.Dialog()
        search_input = dialog.input(
            self.addon.getLocalizedString(30001), type=xbmcgui.INPUT_ALPHANUM
        )

        self.display_search_result(search_input)

    def display_search_result(self, search_input):
        if len(search_input) == 0:
            return

        self.search_history.push(search_input)

        xbmc.log(f"invidious searching for {search_input}.", xbmc.LOGDEBUG)

        # pass search query to Invidious
        results = self.api_client.search(search_input)

        # assemble menu with the results
        self.display_search_results(results)

    def display_channel_list(self, channel_id):
        videos = self.api_client.fetch_channel_list(channel_id)

        self.display_search_results(videos)

    def display_playlist_list(self, playlist_id):
        videos = self.api_client.fetch_playlist_list(playlist_id)

        self.display_search_results(videos)

    def play_video(self, id):
        # TODO: add support for adaptive streaming
        video_info = self.api_client.fetch_video_information(id)

        xbmc.log(f"invidious playing video {video_info}.", xbmc.LOGDEBUG)

        listitem = None
        # check if playback via MPEG-DASH is possible
        if not self.disable_dash and "dashUrl" in video_info:
            is_helper = inputstreamhelper.Helper("mpd")

            if is_helper.check_inputstream():
                url = video_info["dashUrl"]
                xbmc.log(f"invidious using mpeg-dash stream {url}.", xbmc.LOGDEBUG)
                listitem = xbmcgui.ListItem(path=url)
                listitem.setProperty("inputstream", is_helper.inputstream_addon)
                listitem.setProperty("inputstream.adaptive.manifest_type", "mpd")
            else:
                xbmc.log(
                    "invidious mpeg-dash input helper not available.", xbmc.LOGDEBUG
                )

        # as a fallback, we use the last oldschool stream, as it is
        # often the best quality.
        if listitem is None:
            url = video_info["formatStreams"][-1]["url"]
            xbmc.log(
                f"invidious playback failing back to non-dash stream {url}!",
                xbmc.LOGINFO,
            )
            # it's pretty complicated to play a video by its URL in Kodi...
            listitem = xbmcgui.ListItem(path=url)

        datestr = datetime.utcfromtimestamp(video_info["published"]).date().isoformat()
        info_tag = ListItemInfoTag(listitem, "video")
        info_tag.set_info(
            {
                "title": video_info["title"],
                "mediatype": "video",
                "plot": video_info["description"],
                "credits": video_info["author"],
                "date": datestr,
                "dateadded": datestr,
                "premiered": datestr,
                "duration": str(video_info["lengthSeconds"]),
            }
        )

        if self.addon.getSettingBool("mark_items_watched") and self.api_client.username:
            try:
                self.api_client.mark_watched(id)
            except Exception as e:
                xbmc.log(f"invidious: Failed to mark item watched: {e}", xbmc.LOGERROR)
                # TODO: logging, alerting, moving on.

        # basilgello: calling 'RunPlugin' via kodi-send results in CScriptRunner::ExecuteScript
        # which in turn sets addon_handle to -1 breaking the playback
        if self.addon_handle > -1:
            xbmcplugin.setResolvedUrl(
                self.addon_handle, succeeded=True, listitem=listitem
            )
        else:
            xbmc.Player().play(url, listitem)

    def display_main_menu(self):
        def add_list_item(label, path):
            listitem = xbmcgui.ListItem(
                label,
                path=path,
            )
            self.add_directory_item(
                url=self.build_url(path), listitem=listitem, isFolder=True
            )

        # video search item
        add_list_item(self.addon.getLocalizedString(30001), "search_menu")

        if self.api_client.username:
            add_list_item("Feed", "user_feed")
            add_list_item("Subscriptions", "user_subscriptions")

        if self.show_instance_popular:
            add_list_item(self.addon.getLocalizedString(30020), "popular")

        if self.show_instance_trending:
            add_list_item(self.addon.getLocalizedString(30021), "trending")

        self.end_of_directory()

    def display_search_submenu(self):
        def add_list_item(label, path):
            listitem = xbmcgui.ListItem(
                label,
                path=path,
            )
            self.add_directory_item(
                url=self.build_url(path), listitem=listitem, isFolder=True
            )

        # New search on top.
        add_list_item(self.addon.getLocalizedString(30002), "new_search")

        for query in self.search_history.queries():
            url = self.build_url("search", q=query)
            listitem = xbmcgui.ListItem(
                query,
                path=query,
            )
            self.add_directory_item(url=url, listitem=listitem, isFolder=True)

        self.end_of_directory()

    def run(self):
        """
        Web application style method dispatching.
        Uses querystring only, which is pretty oldschool CGI-like stuff.
        """

        action = self.args.get("action", [None])[0]
        if not self.api_client:
            return

        # debugging
        xbmc.log("invidous --------------------------------------------", xbmc.LOGDEBUG)
        xbmc.log("invidous base url:" + str(self.base_url), xbmc.LOGDEBUG)
        xbmc.log("invidous handle:" + str(self.addon_handle), xbmc.LOGDEBUG)
        xbmc.log("invidous args:" + str(self.args), xbmc.LOGDEBUG)
        xbmc.log("invidous action:" + str(action), xbmc.LOGDEBUG)
        xbmc.log("invidous --------------------------------------------", xbmc.LOGDEBUG)

        # for the sake of simplicity, we just handle HTTP request errors here centrally
        try:
            if not action:
                self.display_main_menu()

            elif action == "search_menu":
                self.display_search_submenu()

            elif action == "new_search":
                self.display_new_search()

            elif action == "search":
                self.display_search_result(self.args["q"][0])

            elif action == "play_video":
                self.play_video(self.args["video_id"][0])

            elif action == "view_channel":
                self.display_channel_list(self.args["channel_id"][0])

            elif action == "view_playlist":
                self.display_playlist_list(self.args["playlist_id"][0])

            elif action == "user_feed":
                self.display_search_results(self.api_client.fetch_feed())

            elif action == "user_subscriptions":
                self.display_search_results(self.api_client.fetch_subscribed_channels())

            elif action in ("trending", "popular"):
                self.display_search_results(self.api_client.fetch_special_list(action))

            else:
                raise RuntimeError("unknown action " + action)

        except requests.HTTPError as e:
            xbmc.log(
                f"invidous HTTP status {e.response.status_code} during action processing: {e.response.reason}",
                xbmc.LOGWARNING,
            )
            dialog = xbmcgui.Dialog()
            dialog.notification(
                self.addon.getLocalizedString(30003),
                self.addon.getLocalizedString(30004) + str(e.response.status_code),
                "error",
            )

        except requests.Timeout:
            xbmc.log(
                "invidous HTTP timed out during action processing", xbmc.LOGWARNING
            )
            dialog = xbmcgui.Dialog()
            dialog.notification(
                self.addon.getLocalizedString(30005),
                self.addon.getLocalizedString(30006),
                "error",
            )

    @classmethod
    def from_argv(cls):
        base_url = sys.argv[0]
        addon_handle = int(sys.argv[1])
        args = parse_qs(sys.argv[2][1:])

        return cls(base_url, addon_handle, args)
