import sys
import os
from string import ascii_lowercase
from collections import namedtuple
from typing import Tuple
from urllib.parse import parse_qsl, quote_plus, urlparse
import requests

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
import inputstreamhelper

from resources.lib.utils import to_bool
from resources.lib.settings import Settings
from resources.lib.router import Router
from resources.lib.logger import Logger
from resources.lib.srgssr_api_client import (
    SRGSSRVideoApiClient,
    SRGSSRSubtitlesApiClient,
    InvalidCredentialsException,
)


MainMenuItem = namedtuple("MainMenuItem", ["name", "url", "icon"])


class Plugin:
    """Plugin's main class"""

    KODI_VERSION_MAJOR = int(xbmc.getInfoLabel("System.BuildVersion").split(".", maxsplit=1)[0])
    ADDON = xbmcaddon.Addon()
    ADDON_ID = ADDON.getAddonInfo("id")
    ADDON_URL = f"plugin://{ADDON_ID}"
    HANDLE = int(sys.argv[1])
    SRG_API_BASE_URL = "https://api.srgssr.ch"

    settings = Settings()

    def __init__(self):
        self.tr = self.ADDON.getLocalizedString
        self.icon = self.ADDON.getAddonInfo("icon")
        self.path = self.ADDON.getAddonInfo("path")
        self.logger = Logger(self)
        self.router = Router(self)
        xbmcplugin.setContent(self.HANDLE, "tv_shows")
        self._create_work_folder()

        # check if default BU is set in the settings
        self.bu = self.settings.default_bu if self.settings.default_bu != "choose" else ""

        try:
            self.video_client, self.subs_client = self._create_api_clients()
        except InvalidCredentialsException as exc:
            xbmcgui.Dialog().ok(self.tr(30096).format(exc.api_name), self.tr(30097))
            sys.exit(1)

    def _create_work_folder(self):
        """Creating the addon work folder if it doesn't exist"""
        userdata_path = xbmcvfs.translatePath(self.ADDON.getAddonInfo("profile"))
        if not os.path.isdir(userdata_path):
            os.mkdir(userdata_path)

    def _create_api_clients(self) -> Tuple[SRGSSRVideoApiClient, SRGSSRSubtitlesApiClient]:
        """Creates and returns the Video and Subtitles API clients"""
        self._check_api_credentials_set("consumerKey", "consumerSecret")
        video_client = SRGSSRVideoApiClient(
            self.SRG_API_BASE_URL,
            {
                "key": self.settings.consumerKey,
                "secret": self.settings.consumerSecret,
            },
            self,
        )

        subs_client = None
        if to_bool(self.settings.enable_subtitles):
            self._check_api_credentials_set("consumerKeySubtitles", "consumerSecretSubtitles")
            subs_client = SRGSSRSubtitlesApiClient(
                self.SRG_API_BASE_URL,
                {
                    "key": self.settings.consumerKeySubtitles,
                    "secret": self.settings.consumerSecretSubtitles,
                },
                self,
            )

        return (video_client, subs_client)

    def _check_api_credentials_set(self, key_setting: str, secret_setting: str):
        """Checks that Video or Subtitles API credentials are set, and open the settings if not"""
        while (
            getattr(self.settings, key_setting) == ""
            or getattr(self.settings, secret_setting) == ""
        ):
            xbmcgui.Dialog().ok(self.tr(30099), self.tr(30098))
            self.ADDON.openSettings()

    def _bu_menu_items(self):
        """The BU menu items"""
        return [
            MainMenuItem(self.tr(30014), self.router.url("srf"), self.router.icon_path("srf")),
            MainMenuItem(self.tr(30015), self.router.url("swi"), self.router.icon_path("swi")),
            MainMenuItem(self.tr(30016), self.router.url("rts"), self.router.icon_path("rts")),
            MainMenuItem(self.tr(30017), self.router.url("rsi"), self.router.icon_path("rsi")),
            MainMenuItem(self.tr(30018), self.router.url("rtr"), self.router.icon_path("rtr")),
        ]

    def _main_menu_items(self):
        """The Main menu items"""
        return [
            MainMenuItem(
                self.tr(30021),
                self.router.url(mode="all_shows"),
                self.router.icon_path(self.bu),
            ),
            MainMenuItem(
                self.tr(30022),
                self.router.url(mode="shows_by_letters"),
                self.router.icon_path(self.bu),
            ),
            MainMenuItem(
                self.tr(30023),
                self.router.url(mode="videos_by_topic"),
                self.router.icon_path(self.bu),
            ),
            MainMenuItem(
                self.tr(30024),
                self.router.url(mode="trending"),
                self.router.icon_path(self.bu),
            ),
            MainMenuItem(
                self.tr(30025),
                self.router.url(mode="search"),
                self.router.icon_path(self.bu),
            ),
        ]

    def run(self):
        """Plugin main method"""
        self.logger.debug("Starting SRGSSR plugin")
        self.logger.debug(
            f"Argv[0]: {sys.argv[0]} ; Argv[1]: {sys.argv[1]} ; Argv[2]: {sys.argv[2]} ; "
        )
        kwargs = dict(parse_qsl(sys.argv[2].lstrip("?")))
        self.router.dispatch(**kwargs)
        self.logger.debug("End of SRGSSR plugin")

    def bu_menu(self):
        """Builds the Business Units Menu"""
        for bu in self._bu_menu_items():
            self._add_item_to_directory(
                bu.name, url=bu.url, thumbnail_image=bu.icon, is_folder=True
            )
        xbmcplugin.endOfDirectory(self.HANDLE)

    def main_menu(self):
        """Builds the Main Menu"""
        for menu in self._main_menu_items():
            self._add_item_to_directory(
                menu.name, menu.url, thumbnail_image=menu.icon, is_folder=True
            )
        xbmcplugin.endOfDirectory(self.HANDLE)

    def all_tv_shows(self):
        """Menu that lists all the TV Shows"""
        only_active_shows = not to_bool(self.settings.show_inactive_shows)
        shows = self.video_client.get_tv_shows(self.bu, only_active_shows=only_active_shows)[
            "showList"
        ]
        self.tv_shows_menu(shows)
        xbmcplugin.endOfDirectory(self.HANDLE)

    def tv_shows_by_letter(self, letter: str = ""):
        """Menu that lists the TV Shows sorted by their first letter"""
        if not letter:
            self._add_item_to_directory(
                self.tr(30019),
                self.router.url(mode="shows_by_letters", **{"letter": "#"}),
                is_folder=True,
            )

            for char in ascii_lowercase:
                self._add_item_to_directory(
                    char,
                    self.router.url(mode="shows_by_letters", **{"letter": char}),
                    is_folder=True,
                )
        else:
            only_active_shows = not to_bool(self.settings.show_inactive_shows)
            shows = self.video_client.get_tv_shows(
                self.bu, letter, only_active_shows=only_active_shows
            )["showList"]
            self.tv_shows_menu(shows)
        xbmcplugin.endOfDirectory(self.HANDLE)

    def tv_shows_menu(self, shows: list):
        """Helper building a menu containing TV Shows
        :param shows: List containg the TV Shows collected from the API
        """
        self.logger.debug("Builds TV Shows Menu")
        for show in shows:
            image_url = show.get("imageUrl", "")

            description = show.get("description")
            if not description:  # sometimes lead contains th description
                description = show.get("lead", "")

            url_args = {
                "number_of_episodes": show.get("numberOfEpisodes", 0),
                "tv_show_id": quote_plus(show.get("id")),
            }

            name = show.get("title", "")
            self._add_item_to_directory(
                name,
                self.router.url(mode="list_episodes_by_show", **url_args),
                description,
                video_info={"title": name, "plot": description, "plotoutline": description},
                thumbnail_image=image_url,
                fanart=image_url,
                is_folder=True,
            )

    def videos_by_topic(self):
        """Menu listing the topics"""
        topics = self.video_client.get_topics(self.bu)["topicList"]

        for topic in topics:
            image_url = topic.get("imageUrl", "")
            name = topic.get("title", "")
            topic_id = topic.get("id", "")
            self._add_item_to_directory(
                name,
                self.router.url(mode="list_videos_by_topic", **{"topic_id": topic_id}),
                thumbnail_image=image_url,
                is_folder=True,
            )
        xbmcplugin.endOfDirectory(self.HANDLE)

    def list_videos_by_topic(
        self, topic_id: str, current_page: int, number_of_episodes: int, next_page_id=""
    ):
        """Menu listing the Videos of a topic"""
        number_of_episodes_per_page = int(self.settings.number_of_episodes_per_page)
        res = self.video_client.get_latest_episodes(
            self.bu,
            topic_id=topic_id,
            page_size=number_of_episodes_per_page,
            next_page_id=next_page_id,
        )

        media_list = res.get("mediaList")
        for media in media_list:
            episode = media.get("episode")
            show = media.get("show")
            self._add_video_to_directory(show, episode, media)

        next_page_url = res.get("next")
        if next_page_url:
            self._add_next_page_to_directory(
                current_page,
                next_page_url,
                number_of_episodes,
                "list_videos_by_topic",
                {"topic_id": topic_id},
            )
        xbmcplugin.endOfDirectory(self.HANDLE)

    def list_episodes_by_show(
        self, tv_show_id: str, current_page: int, number_of_episodes: int, next_page_id=""
    ):
        """Lists the latest episodes of a TV Show
        :param tv_show_id: The id of the TV Show
        :param current_page: Index of the current episodes page
        :param number_of_episodes: Total number of episodes of the show
        :param next_page_id: ID of the next page of episodes
        """
        xbmcplugin.setContent(self.HANDLE, "episodes")

        number_of_episodes_per_page = int(self.settings.number_of_episodes_per_page)
        res = self.video_client.get_latest_episodes(
            self.bu, tv_show_id, page_size=number_of_episodes_per_page, next_page_id=next_page_id
        )

        show = res.get("show")
        episodes = res.get("episodeList")

        if show and episodes:
            for episode in episodes:
                media = episode.get("mediaList")[0]
                self._add_video_to_directory(show, episode, media)

            next_page_url = res.get("next")
            if next_page_url:
                self._add_next_page_to_directory(
                    current_page,
                    next_page_url,
                    number_of_episodes,
                    "list_episodes_by_show",
                    {"tv_show_id": quote_plus(show.get("id"))},
                )
        xbmcplugin.endOfDirectory(self.HANDLE)

    def trending(self, current_page: int, next_page_id=""):
        """Menu listing the Trending videos"""
        number_of_episodes_per_page = int(self.settings.number_of_episodes_per_page)
        res = self.video_client.get_trendings(self.bu, number_of_episodes_per_page, next_page_id)

        for media in res.get("mediaList"):
            show = media.get("show")
            episode = media.get("episode")
            self._add_video_to_directory(show, episode, media)

        next_page_url = res.get("next")
        if next_page_url:
            self._add_next_page_to_directory(
                current_page,
                next_page_url,
                0,
                "trending",
            )
        xbmcplugin.endOfDirectory(self.HANDLE)

    def search_menu(self, search_type: str = ""):
        """Search menu.
        :param search_type: Either "tv_shows", "videos", or empty.
                            If empty, listing the type available type of search. Else, showing a keyboard to search.
        """
        if not search_type:
            self._add_item_to_directory(
                self.tr(30031),
                self.router.url(mode="search", **{"type": "tv_shows"}),
                is_folder=True,
            )
            self._add_item_to_directory(
                self.tr(30032),
                self.router.url(mode="search", **{"type": "videos"}),
                is_folder=True,
            )
        else:
            if search_type == "tv_shows":
                search_string = xbmcgui.Dialog().input(self.tr(30031))
                if search_string != '':
                    res = self.video_client.get_tv_shows(self.bu, string_filter=search_string)
                    self.tv_shows_menu(res.get("searchResultListShow"))
                else:
                    return
            elif search_type == "videos":
                search_string = xbmcgui.Dialog().input(self.tr(30032))
                if search_string != '':
                    res = self.video_client.search_video(self.bu, search_string, page_size=20)
                    for media in res.get("searchResultListMedia"):
                        show = media.get("show")
                        episode = media.get("episode")
                        self._add_video_to_directory(show, episode, media)
                        # TODO: Add next page
                else:
                    return

        xbmcplugin.endOfDirectory(self.HANDLE)

    def play_video(self, video_id: str, media_id: str):
        """Plays the selected video
        :param video_id: The video ID
        :param media_id: The media ID
        """
        media_composition = self.video_client.get_media_composition(self.bu, media_id)
        resource = self._get_media_resource(media_composition)
        media_url = self._get_media_url(resource["url"])

        liz = xbmcgui.ListItem(path=media_url)
        liz.setProperty("isPlayable", "true")
        self._set_inputstream_params(liz, resource["protocol"].lower(), resource["mimeType"])
        self._add_subtitles(liz, video_id)
        self.logger.debug(f"Playing episode {self.bu} {media_id} (media URL: {media_url})")
        xbmcplugin.setResolvedUrl(self.HANDLE, True, liz)

    def _get_media_resource(self, media_composition) -> dict:
        """Parses the media composition object to find the best resource and return it"""
        resource_list = media_composition["chapterList"][0]["resourceList"]
        sd_hls_resources = []
        for resource in resource_list:
            if resource["protocol"] == "HLS":
                if resource["quality"] == "HD":
                    return resource
                else:
                    sd_hls_resources.append(resource)

        if not sd_hls_resources:
            return resource_list[0]
        else:
            return sd_hls_resources[0]

    def _get_media_url(self, resource_url: str) -> str:
        """Parses the resource URL and constructs the media URL from it"""
        parsed_url = urlparse(resource_url)
        media_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        # add authentication token for akamaihd
        if "akamaihd" in parsed_url.netloc:
            self.logger.debug("AkamaiHD video")
            token_url = f"http://tp.srgssr.ch/akahd/token?acl={parsed_url.path}"
            response = requests.get(token_url).json()
            token = response["token"]["authparams"]
            media_url += "?" + token
        return media_url

    def _set_inputstream_params(self, listitem, protocol, mime_type):
        """If Inputstream Adaptive is enabled and available, configure it and update the ListItem"""
        is_helper = inputstreamhelper.Helper(protocol)
        if to_bool(self.settings.enable_inputstream_adaptive) and is_helper.check_inputstream():
            listitem.setContentLookup(False)
            listitem.setMimeType(mime_type)
            listitem.setProperty("inputstream", is_helper.inputstream_addon)
            listitem.setProperty("inputstream.adaptive.manifest_type", protocol)

    def _add_subtitles(self, listitem, video_id):
        """If subtitles are enable and available, add them to the ListItem"""
        self.logger.debug(f"Getting subtitles for video {video_id}")
        if to_bool(self.settings.enable_subtitles):
            video_urn = f"urn:{self.bu}:episode:tv:{video_id}"
            resp = self.subs_client.get_subtitles(video_urn)

            subs = []
            for asset in resp["data"]["assets"]:
                if asset is not None:
                    for sub in asset["hasSubtitling"]:
                        subs.append(sub["identifier"])
            if subs:
                self.logger.debug(f"Found subtitles: {subs}")
                listitem.setSubtitles(subs)

    # ================================= Helper methods ==================================

    def _add_video_to_directory(self, show: dict, episode: dict, media: dict):
        """Helper that adds a "Video" item to the Directory"""
        url_args = {
            "video_id": episode.get("id"),
            "media_id": media.get("id"),
        }

        vid_name = episode.get("title", "") + " - " + media.get("title", "") if episode.get("title", "") != media.get("title", "") else episode.get("title", "")
        vid_desc = media.get("description", "")
        duration = int(media.get("duration", 0) // 1000)

        self._add_item_to_directory(
            vid_name,
            self.router.url(mode="play_video", **url_args),
            label2=vid_desc,
            thumbnail_image=media.get("imageUrl", ""),
            fanart=show.get("imageUrl", ""),
            video_info={
                "Title": vid_name,
                "Duration": duration,
                "Plot": vid_desc,
                "Aired": episode.get("publishedDate", ""),
            },
            properties={"IsPlayable": "true"},
        )

    def _add_next_page_to_directory(
        self,
        current_page: int,
        next_page_url: str,
        number_of_episodes: int,
        url_mode: str,
        url_args: dict = None,
    ):
        """Helper method to adds a "next page" item to the directory"""
        url_args = {} if url_args is None else url_args
        number_of_episodes_per_page = int(self.settings.number_of_episodes_per_page)
        number_of_pages = self._compute_number_of_pages(
            number_of_episodes_per_page, number_of_episodes
        )
        liz_name = self.tr(30020).format(current_page, f"/{number_of_pages}" if number_of_pages else "")
        next_page_id = dict(parse_qsl(urlparse(next_page_url).query)).get("next")
        next_page = current_page + 1

        url_args.update({"next_page_id": next_page_id, "current_page": next_page, "number_of_episodes": number_of_episodes })

        self._add_item_to_directory(
            liz_name,
            self.router.url(mode=url_mode, **url_args),
            label2=str(next_page),
            video_info={"title": liz_name, "plot": str(next_page), "plotoutline": str(next_page)},
            is_folder=True,
        )

    def _compute_number_of_pages(
        self, number_of_episodes_per_page: int, number_of_episodes: int
    ) -> int:
        """Helper method returning on how many pages the episodes are displayed"""
        return int(
            (number_of_episodes_per_page - 1 + number_of_episodes) / number_of_episodes_per_page
        )

    def _add_item_to_directory(
        self,
        name: str,
        url: str,
        label2: str = "",
        icon_image: str = "",
        thumbnail_image: str = "",
        poster: dict = None,
        fanart: dict = None,
        video_info: dict = None,
        properties: dict = None,
        subtitles: dict = None,
        is_folder: bool = False,
    ):
        """Helper method that creates a ListItem and adds it to the xbmcplugin Directory"""
        liz = xbmcgui.ListItem(name, label2)
        if properties:
            liz.setProperties(properties)
        if video_info:
            liz.setInfo("video", video_info)
        if poster:
            liz.setArt({"poster": poster})
        if fanart:
            liz.setArt({"fanart": fanart})
        if thumbnail_image:
            liz.setArt({"thumb": thumbnail_image})
        if icon_image:
            liz.setArt({"icon": icon_image})
        if subtitles:
            liz.setSubtitles(subtitles)

        xbmcplugin.addDirectoryItem(
            self.HANDLE,
            url,
            listitem=liz,
            isFolder=is_folder,
        )
