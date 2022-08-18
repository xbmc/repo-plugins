"""Routing in the plugin menus"""

from urllib.parse import urlencode

import xbmcplugin


class Router:
    """Router dispatching the queries on the Addon"""
    def __init__(self, plugin):
        self.plugin = plugin

    def url(self, bu: str = "", mode: str = "", **kwargs):
        """Constructs the plugin's URL"""
        if not bu:
            bu = self.plugin.bu
        return f"{self.plugin.ADDON_URL}?bu={bu}&mode={mode}&{urlencode(kwargs)}"

    def icon_path(self, name):
        return f"{self.plugin.path}/resources/media/{name}.png"

    def dispatch(self, **kwargs):
        """Dispatch to the plugin menu
        :param kwargs: url params
        """
        self.plugin.logger.debug(f"Route dispatcher: kwargs: {kwargs}")
        if kwargs.get("bu"):
            self.plugin.bu = kwargs.get("bu")
        mode = kwargs.get("mode", "")
        self.plugin.logger.debug(f"Mode: {mode}, BU:{self.plugin.bu}")

        if not self.plugin.bu:
            self.plugin.bu_menu()
        else:
            xbmcplugin.setPluginCategory(self.plugin.HANDLE, self.plugin.bu.upper())

            if not mode:
                self.plugin.main_menu()
            elif mode == "all_shows":
                self.plugin.all_tv_shows()
            elif mode == "shows_by_letters":
                letter = kwargs.get("letter", "")
                self.plugin.tv_shows_by_letter(letter)
            elif mode == "videos_by_topic":
                self.plugin.videos_by_topic()
            elif mode == "list_videos_by_topic":
                self.plugin.list_videos_by_topic(
                    kwargs["topic_id"],
                    int(kwargs.get("current_page", 1)),
                    int(kwargs.get("number_of_episodes", 0)),
                    kwargs.get("next_page_id", ""),
                )
            elif mode == "search":
                self.plugin.search_menu(kwargs.get("type", ""))
            elif mode == "trending":
                self.plugin.trending(
                    int(kwargs.get("current_page", 1)), kwargs.get("next_page_id", "")
                )
            elif mode == "list_episodes_by_show":
                self.plugin.list_episodes_by_show(
                    kwargs["tv_show_id"],
                    int(kwargs.get("current_page", 1)),
                    int(kwargs.get("number_of_episodes", 0)),
                    kwargs.get("next_page_id", ""),
                )
            elif mode == "play_video":
                video_id = kwargs.get("video_id", "")
                media_id = kwargs.get("media_id", "")
                self.plugin.play_video(video_id, media_id)
