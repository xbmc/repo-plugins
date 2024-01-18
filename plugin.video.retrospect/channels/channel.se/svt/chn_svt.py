# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
from typing import Optional, List, Tuple

import pytz

from resources.lib import chn_class, mediatype, contenttype
from resources.lib.helpers.htmlhelper import HtmlHelper

from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.regexer import Regexer
from resources.lib.helpers import subtitlehelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.mpd import Mpd
from resources.lib.channelinfo import ChannelInfo
from resources.lib.addonsettings import AddonSettings

from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "svtimage.png"

        self.__show_program_folder = self._get_setting("show_programs_folder", "true") == "true"
        self.__program_url = self.__get_api_url(
            "ProgramsListing", "17252e11da632f5c0d1b924b32be9191f6854723a0f50fb2adb35f72bb670efa",
            {})

        if self.channelCode == "oppetarkiv":
            self.mainListUri = "#genre_item"
        else:
            self.mainListUri = "#mainlist"

        # Setup the urls
        self.baseUrl = "https://www.svtplay.se"
        self.swfUrl = "https://media.svt.se/swf/video/svtplayer-2016.01.swf"

        # If we have a separate listing for the mainlist (#mainlist) then only run a preprocessor
        # that generates the list
        self._add_data_parser("#mainlist", preprocessor=self.add_live_items_and_genres)

        self._add_data_parser(self.__program_url,
                              match_type=ParserData.MatchStart, json=True,
                              preprocessor=self.folders_or_clips,
                              parser=["data", "programAtillO", "flat"],
                              creator=self.create_api_typed_item)

        # This one contructs an API url using the metaData['slug'] and then retrieves either the all
        # folders, just the videos in a folder if that is the only folder, or it retrieves the
        # content of a folder with a given metaData['folder_id'].
        self._add_data_parser("#program_item", json=True,
                              name="Data retriever for API folder.",
                              preprocessor=self.fetch_program_api_data)
        self._add_data_parser("#program_item", json=True,
                              name="Folder parser for show listing via API",
                              parser=["folders"], creator=self.create_api_typed_item)
        self._add_data_parser("#program_item", json=True,
                              name="video parser for show listing via API",
                              parser=["videos"], creator=self.create_api_typed_item)

        self._add_data_parser("https://api.svt.se/contento/graphql?operationName=CategoryPageQuery",
                              json=True, name="New on SVT GraphQL",
                              parser=["data", "categoryPage", "lazyLoadedTabs", ("slug", "all", 0),
                                      "selections", 0, "items"],
                              creator=self.create_api_typed_item)

        self._add_data_parser("https://api.svt.se/contento/graphql?operationName=GridPage",
                              name="Default GraphQL GridePage parsers", json=True,
                              parser=["data", "selectionById", "items"],
                              creator=self.create_api_typed_item)

        self._add_data_parsers([
                "https://api.svt.se/contento/graphql?operationName=FionaPage",
                "https://contento.svt.se/graphql?operationName=FionaPage"
            ],
            name="GraphQL FionaPage parsers for Nytt pa Play", json=True,
            parser=["data", "selectionById", "items"],
            creator=self.create_api_typed_item)

        self._add_data_parser("https://api.svt.se/contento/graphql?operationName=MainGenres",
                              name="GraphQL for main genre listding", json=True,
                              parser=["data", "genresInMain", "genres"],
                              creator=self.create_api_typed_item)

        self._add_data_parser("#genre_item", json=True,
                              name="Genre data retriever for GraphQL",
                              preprocessor=self.fetch_genre_api_data)
        self._add_data_parser("#genre_item", json=True,
                              name="Genre episode parser for GraphQL",
                              parser=["programs"],
                              creator=self.create_api_typed_item)
        self._add_data_parser("#genre_item", json=True,
                              name="Genre clip parser for GraphQL",
                              parser=["videos"],
                              creator=self.create_api_typed_item)

        self._add_data_parser("https://www.svtplay.se", match_type=ParserData.MatchExact,
                              name="SVTPlay data retriever for New on SVT",
                              preprocessor=self.extract_new_on_svt_id)

        # Setup channel listing based on JSON data in the HTML
        self._add_data_parser(
            "https://api.svt.se/contento/graphql?operationName=BroadcastSchedule",
            name="Live streams", json=True,
            parser=["data", "channels", "channels"],
            creator=self.create_channel_item)

        # Searching
        self._add_data_parser("https://contento-search.svt.se/graphql",
                              json=True,
                              parser=["data", "searchPage", "flat", "hits"],
                              creator=self.create_api_typed_item)

        # Generic updating of videos
        self._add_data_parser("https://api.svt.se/videoplayer-api/video/",
                              updater=self.update_video_api_item)
        # Update via HTML pages
        self._add_data_parser("https://www.svtplay.se/video/", updater=self.update_video_html_item)
        self._add_data_parser("https://www.svtplay.se/klipp/", updater=self.update_video_html_item)

        # Update via the new API urls
        self._add_data_parser("https://www.svt.se/videoplayer-api/",
                              updater=self.update_video_api_item)

        # ===============================================================================================================
        # non standard items
        self.__folder_id = "folder_id"
        self.__genre_id = "genre_id"
        self.__filter_subheading = "filter_subheading"
        self.__parent_images = "parent_thumb_data"
        self.__apollo_data = None
        self.__timezone = pytz.timezone("Europe/Stockholm")

        self.__show_videos = True
        self.__show_folders = True

        # ===============================================================================================================
        # Test cases:
        #   Affaren Ramel: just 1 folder -> should only list videos

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def add_live_items_and_genres(self, data):
        """ Adds the Live items, Channels and Last Episodes to the listing.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        # Specify the name, url and whether or not to filter out some subheadings:
        # https://api.svt.se/contento/graphql?operationName=BroadcastSchedule
        # &variables={"day":"2023-09-11"}&extensions={"persistedQuery":{"sha256Hash":"464905fb9c6f51510427f3b913fde66cb43fa5b7f9197bcd13815800758a599b","version":1}}&ua=svtplaywebb-render-low-prio-client
        now = datetime.datetime.now() - datetime.timedelta(hours=6)
        extra_items = {
            LanguageHelper.get_localized_string(LanguageHelper.LiveTv): (
                self.__get_api_url(
                    "BroadcastSchedule",
                    "464905fb9c6f51510427f3b913fde66cb43fa5b7f9197bcd13815800758a599b",
                    {"day": "{:04}-{:02}-{:02}".format(now.year, now.month, now.day)}),
                False),

            LanguageHelper.get_localized_string(LanguageHelper.CurrentlyPlayingEpisodes): (
                self.__get_api_url(
                    "GridPage",
                    "a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40",
                    variables={"includeFullOppetArkiv": True, "selectionId": "live_start"}),
                False),

            LanguageHelper.get_localized_string(LanguageHelper.Search): (
                "searchSite", False),

            LanguageHelper.get_localized_string(LanguageHelper.Recent): (
                self.__get_api_url(
                    "GridPage",
                    "a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40",
                    variables={"includeFullOppetArkiv": True, "selectionId": "latest_start"}),
                False),

            LanguageHelper.get_localized_string(LanguageHelper.LastChance): (
                self.__get_api_url(
                    "GridPage",
                    "a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40",
                    variables={"includeFullOppetArkiv": True, "selectionId": "lastchance_start"}),
                False),

            LanguageHelper.get_localized_string(LanguageHelper.MostViewedEpisodes): (
                self.__get_api_url("GridPage",
                                   "a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40",
                                   variables={"includeFullOppetArkiv": True,
                                              "selectionId": "popular_start"}),
                False),

            LanguageHelper.get_localized_string(LanguageHelper.LatestNews): (
                self.__get_api_url(
                    "CategoryPageQuery",
                    "00be06320342614f4b186e9c7710c29a7fc235a1936bde08a6ab0f427131bfaf",
                    variables={"id": "nyheter", "includeFullOppetArkiv": True, "tab": "all"}),
                False
            ),

            # The selection ID might change over time.
            # We need to determine the `selectionId`
            LanguageHelper.get_localized_string(LanguageHelper.NewOnChannel) % self.channelName: (
                # self.__get_api_url(
                #     "FionaPage",
                #     "b4e65a8f4cedc6bd9981e3539690908443f625c6854ea65f18c4b3b3be66b5dc",
                #     variables={"includeFullOppetArkiv": True, "selectionId": "svtId_jGVZ7AL"}),
                "https://www.svtplay.se",
                False)
        }
        # https://api.svt.se/contento/graphql?operationName=FionaPage&variables={"includeFullOppetArkiv":true,"selectionId":"svtId_egWQ3y7","userIsAbroad":true}&extensions={"persistedQuery":{"sha256Hash":"dc8f85e195903fe6227a76ec1e1d300d470ee8ea123bea6bee26215cc6e4959d","version":1}}&ua=svtplaywebb-render-low-prio-client

        for title, (url, include_subheading) in extra_items.items():
            new_item = FolderItem("\a.: %s :." % (title,), url, content_type=contenttype.VIDEOS)
            new_item.complete = True
            new_item.dontGroup = True
            new_item.metaData[self.__filter_subheading] = include_subheading
            items.append(new_item)

        genre_tags = "\a.: {}/{} :.".format(
            LanguageHelper.get_localized_string(LanguageHelper.Genres),
            LanguageHelper.get_localized_string(LanguageHelper.Tags).lower()
        )

        genre_url = self.__get_api_url("MainGenres",
                                       "65b3d9bccd1adf175d2ad6b1aaa482bb36f382f7bad6c555750f33322bc2b489",
                                       {})
        genre_item = FolderItem(genre_tags, genre_url, content_type=contenttype.VIDEOS)
        genre_item.complete = True
        genre_item.dontGroup = True
        items.append(genre_item)

        category_items = {
            "Drama": (
                "drama",
                "https://www.svtstatic.se/image/medium/480/7166155/1458037803"
            ),
            "Dokumentär": (
                "dokumentar",
                "https://www.svtstatic.se/image/medium/480/7166209/1458037873"
            ),
            "Humor": (
                "humor",
                "https://www.svtstatic.se/image/medium/480/7166065/1458037609"
            ),
            "Barn": (
                "barn",
                "https://www.svtstatic.se/image/medium/480/22702778/1560934663"
            ),
            "Nyheter": (
                "nyheter",
                "https://www.svtstatic.se/image/medium/480/7166089/1458037651"
            ),
            "Sport": (
                "sport",
                "https://www.svtstatic.se/image/medium/480/7166143/1458037766"
            ),
            "Serier": (
                "serier",
                "https://www.svtstatic.se/image/medium/480/20888260/1548755402"
            ),
            "Scen": (
                "scen",
                "https://www.svtstatic.se/image/medium/480/26157824/1585127128"
            ),
            "Livsstil & reality": (
                "livsstil-och-reality",
                "https://www.svtstatic.se/image/medium/480/29184042/1605884325"
            ),
            "Underhållning": (
                "underhallning",
                "https://www.svtstatic.se/image/medium/480/7166041/1458037574"
            ),
            "Filmer": (
                "filmer",
                "https://www.svtstatic.se/image/medium/480/20888292/1548755428"
            ),
            "Kultur": (
                "kultur",
                "https://www.svtstatic.se/image/medium/480/7166119/1458037729"
            ),
            "Samhälle": (
                "samhalle",
                "https://www.svtstatic.se/image/medium/480/7166173/1458037837"
            ),
            "Fakta": (
                "fakta",
                "https://www.svtstatic.se/image/medium/480/29184042/1605884325"
            ),
            "Musik": (
                "musik",
                "https://www.svtstatic.se/image/medium/480/19417384/1537791920"
            ),
            "Djur & natur": (
                "djur-och-natur",
                "https://www.svtstatic.se/image/medium/480/32904903/1634633546"
            ),
            "Öppet arkiv": (
                "oppet-arkiv",
                "https://www.svtstatic.se/image/medium/480/14077904/1497449020"
            )
        }

        category_title = "\a.: {} :.".format(
            LanguageHelper.get_localized_string(LanguageHelper.Categories))
        new_item = FolderItem(category_title, "https://www.svtplay.se/genre",
                              content_type=contenttype.VIDEOS)
        new_item.complete = True
        new_item.dontGroup = True

        for title, (category_id, thumb) in category_items.items():
            # https://api.svt.se/contento/graphql?ua=svtplaywebb-play-render-prod-client&operationName=GenreProgramsAO&variables={"genre": ["action-och-aventyr"]}&extensions={"persistedQuery": {"version": 1, "sha256Hash": "189b3613ec93e869feace9a379cca47d8b68b97b3f53c04163769dcffa509318"}}
            cat_item = FolderItem(title, "#genre_item", content_type=contenttype.TVSHOWS)
            cat_item.complete = True
            cat_item.thumb = thumb or self.noImage
            cat_item.fanart = thumb or self.fanart
            cat_item.dontGroup = True
            cat_item.metaData[self.__genre_id] = category_id
            new_item.items.append(cat_item)
        items.append(new_item)

        progs = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.TvShows),
            self.__program_url, content_type=contenttype.TVSHOWS)
        items.append(progs)

        if self.__show_program_folder:
            clips = FolderItem(
                "\a.: {} :.".format(
                    LanguageHelper.get_localized_string(LanguageHelper.SingleEpisodes)),
                self.__program_url, content_type=contenttype.VIDEOS
            )
            items.append(clips)

            # split the item types
            clips.metaData["list_type"] = "videos"
            progs.metaData["list_type"] = "folders"

        # Clean up the titles
        for item in items:
            item.name = item.name.strip("\a.: ")

        oppet_arkiv = FolderItem("Öppet arkiv", "#genre_item", content_type=contenttype.TVSHOWS)
        oppet_arkiv.metaData[self.__genre_id] = "oppet-arkiv"
        items.append(oppet_arkiv)

        return data, items

    def folders_or_clips(self, data):
        """ Adds the Live items, Channels and Last Episodes to the listing.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        if self.parentItem:
            list_type = self.parentItem.metaData.get("list_type")
            if list_type == "folders":
                self.__show_folders = True
                self.__show_videos = False
            elif list_type == "videos":
                self.__show_folders = False
                self.__show_videos = True

        # For now we either show all or none.
        # else:
        #     self.__show_folders = True
        #     self.__show_videos = False

        json_data = JsonHelper(data)
        flat = []
        for r in json_data.get_value("data", "programAtillO", "selections"):
            flat += r["items"]

        json_data.json["data"]["programAtillO"]["flat"] = flat
        return json_data, items

    def create_api_typed_item(self, result_set, add_parent_title=False):
        """ Creates a new MediaItem based on the __typename attribute.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex
        :param bool add_parent_title: Should the parent's title be included?

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        api_type = result_set["__typename"]
        Logger.trace("%s: %s", api_type, result_set)

        if api_type == "TvSeries":
            item = self.create_api_tvserie_type(result_set)
        elif api_type == "Selection":
            item = self.create_api_selection_type(result_set)
        elif api_type == "Teaser":
            item = self.create_api_teaser_type(result_set)
        elif api_type == "Genre":
            item = self.create_api_genre_type(result_set)
        elif api_type == "TvShow" or api_type == "KidsTvShow":
            item = self.create_api_tvshow_type(result_set)

        # Search Result
        elif api_type == "SearchPageHit":
            # item = self.create_api_typed_item(result_set["item"], add_parent_title=True)
            item = self.create_api_search_hit(result_set)

        # Video items
        elif api_type == "Single":
            item = self.create_api_single_type(result_set)
        elif api_type == "Clip" or api_type == "Trailer":
            item = self.create_api_clip_type(result_set)
        elif api_type == "Episode" or api_type == "Variant":
            item = self.create_api_episode_type(result_set, add_parent_title)
        else:
            Logger.warning("Missing type: %s", api_type)
            return None

        return item

    def create_api_tvserie_type(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        if not self.__show_folders:
            return None

        url = result_set["urls"]["svtplay"]
        item = FolderItem(result_set['name'], "#program_item", content_type=contenttype.EPISODES)
        item.metaData["slug"] = url
        item.tv_show_title = item.name
        item.isGeoLocked = result_set.get('restrictions', {}).get('onlyAvailableInSweden', False)
        item.description = result_set.get('longDescription')

        self.__extract_artwork(result_set.get("images"), item)
        return item

    def create_api_tvshow_type(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        This works for:
            __typename=TvShow, KidsTvShow, Single

        """

        if not self.__show_folders:
            return None

        url = result_set["urls"]["svtplay"]
        item = FolderItem(result_set['name'], "#program_item", content_type=contenttype.EPISODES)
        item.metaData["slug"] = url
        item.tv_show_title = item.name
        item.isGeoLocked = result_set.get('restrictions', {}).get('onlyAvailableInSweden', False)
        item.description = result_set.get('description')
        self.__extract_artwork(result_set.get("images"), item)
        return item

    def create_api_selection_type(self, result_set):
        """ Creates a new MediaItem for the new GraphQL Api.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        This works for:
            __typename=Selection

        """

        if not self.__show_folders:
            return None

        if result_set.get("type", "").lower() == "upcoming":
            return None

        name = result_set["name"]
        if not name:
            # If there is no name, use the ID for it and split the ID off.
            name = result_set["id"].rsplit("-", 1)[0].replace("-", " ").title()

        item = MediaItem(name, self.parentItem.url)
        item.metaData[self.__folder_id] = result_set["id"]
        item.metaData.update(self.parentItem.metaData)
        item.thumb = self.__get_thumb(result_set[self.__parent_images], width=720)
        item.fanart = self.__get_thumb(result_set[self.__parent_images])
        return item

    def create_api_teaser_type(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the API.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        This works for:
            __typename=Teaser

        """

        # if not self.__show_folders:
        #     return None

        title = result_set.get("heading")
        sub_heading = result_set.get("subHeading")
        new_result_set = result_set["item"]

        new_result_set["name"] = title
        # We need to get rid of some subheadings for which we already have information elsewhere.
        if bool(sub_heading):
            new_result_set["name"] = "{} - {}".format(title, sub_heading)
            # See if we need to filter out some of the headings? Defaults to True
            if self.parentItem.metaData.get(self.__filter_subheading, True) and (
                    "Idag" in sub_heading
                    or "Ikväll" in sub_heading
                    or "Igår" in sub_heading
                    or sub_heading.endswith(" sek")
                    or sub_heading.endswith(" min")
                    or sub_heading.endswith(" tim")):
                Logger.trace("Ignoring subheading: %s", sub_heading)
                new_result_set["name"] = title

        # Transfer some items
        new_result_set[self.__parent_images] = result_set.get(self.__parent_images)

        badge = (result_set.get("badge") or {}).get("altText")
        description = result_set.get("description")
        if badge and description:
            new_result_set["longDescription"] = f"[COLOR gold]{badge}[/COLOR]\n\n{description}"
        elif badge:
            new_result_set["longDescription"] = f"[COLOR gold]{badge}[/COLOR]"
        elif description:
            new_result_set["longDescription"] = description

        if "images" in result_set:
            new_result_set["images"] = result_set["images"]
        item = self.create_api_typed_item(result_set["item"])
        return item

    def create_api_episode_type(self, result_set, add_parent_title=False):
        """ Creates a MediaItem of type 'video' using the result_set from the API.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict result_set: The result_set of the self.episodeItemRegex
        :param bool add_parent_title: Should the parent's title be included?

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        This works for:
            __typename=Episode

        """

        if not self.__show_videos:
            return None

        svt_video_id = result_set.get("videoSvtId", result_set.get("svtId", None))
        if svt_video_id:
            # API style
            url = "https://api.svt.se/videoplayer-api/video/{}".format(svt_video_id)
        else:
            # HTML style
            url = "{}{}".format(self.baseUrl, result_set['urls']['svtplay'])

        title = result_set.get("name", "")
        if "parent" in result_set and add_parent_title:
            title = "{} - {}".format(result_set["parent"]["name"], title)

        item = MediaItem(title, url)
        item.description = result_set.get("longDescription")
        item.set_info_label("duration", int(result_set.get("duration", 0)))
        item.isGeoLocked = result_set.get("restrictions", {}).get("onlyAvailableInSweden", False)

        parent_images = result_set.get(self.__parent_images)
        if bool(parent_images):
            item.fanart = self.__get_thumb(parent_images)

        if "image" in result_set:
            item.thumb = self.__get_thumb(result_set["image"], width=720)
        self.__extract_artwork(result_set.get("images"), item)

        valid_from: Optional[str] = result_set.get("validFrom", None)
        if bool(valid_from) and valid_from.endswith("Z"):
            # We need to change the timezone
            valid_from_date = DateHelper.get_datetime_from_string(valid_from[:-1], time_zone="UTC")
            valid_from_date = valid_from_date.astimezone(self.__timezone)
            item.set_date(valid_from_date.year, valid_from_date.month, valid_from_date.day,
                          valid_from_date.hour, valid_from_date.minute, valid_from_date.second)
        elif bool(valid_from):
            # Remove the Timezone information
            valid_from = valid_from.split("+")[0]
            valid_from_date = DateHelper.get_date_from_string(valid_from, "%Y-%m-%dT%H:%M:%S")
            item.set_date(*valid_from_date[0:6])

        valid_to: Optional[str] = result_set.get("validTo", None)
        if valid_to:
            self.__set_expire_time(valid_to, item)

        live_data = result_set.get("live")
        if live_data:
            is_live_now = live_data["liveNow"]
            if is_live_now:
                item.name = "{} [COLOR gold](live)[/COLOR]".format(item.name)

            start = live_data["start"]
            if start.endswith("Z"):
                start_time = DateHelper.get_datetime_from_string(start, "%Y-%m-%dT%H:%M:%SZ", "UTC")
                start_time = start_time.astimezone(self.__timezone)
                item.set_date(start_time.year, start_time.month, start_time.day,
                              start_time.hour, start_time.minute, start_time.second)
                hour = start_time.hour
                minute = start_time.minute
            else:
                start = start.split('.')[0].split("+")[0]
                start_time = DateHelper.get_date_from_string(start, "%Y-%m-%dT%H:%M:%S")
                item.set_date(*start_time[0:6])
                hour = start_time.tm_hour
                minute = start_time.tm_min

            item.name = "{:02}:{:02} - {}".format(hour, minute, item.name)

        elif "live just nu" in item.description.lower():
            item.name = "{} [COLOR gold](live)[/COLOR]".format(item.name)

        item.media_type = mediatype.VIDEO
        season_info = result_set.get("positionInSeason")
        if bool(season_info):
            Logger.debug("Found season info: %s", season_info)
            try:
                episode_info = season_info.split(" ")
                if not len(episode_info) == 5:
                    return item

                item.set_season_info(episode_info[1], episode_info[4])
                item.media_type = mediatype.EPISODE
                item.name = result_set.get("nameRaw", item.name) or item.name
            except:
                Logger.warning("Failed to set season info: %s", season_info, exc_info=True)

        return item

    def create_api_single_type(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the API.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        This works for:
            __typename=Episode

        """

        if not self.__show_videos:
            return None

        title = result_set['name']
        url = '{}{}'.format(self.baseUrl, result_set['urls']['svtplay'])

        item = MediaItem(title, url)
        item.media_type = mediatype.VIDEO
        item.description = result_set.get('longDescription')

        self.__extract_artwork(result_set.get("images"), item)
        item.isGeoLocked = result_set.get('restrictions', {}).get('onlyAvailableInSweden', False)

        duration = int(result_set.get("duration", 0))
        if duration > 0:
            item.set_info_label("duration", duration)
        return item

    def create_api_clip_type(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the API.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        This works for:
            __typename=Episode

        """

        if not self.__show_videos:
            return None

        title = result_set['name']
        svt_video_id = result_set.get("videoSvtId", result_set.get("svtId", None))
        if svt_video_id:
            # API style
            url = "https://api.svt.se/videoplayer-api/video/{}".format(svt_video_id)
        else:
            # HTML style
            url = "{}{}".format(self.baseUrl, result_set['urls']['svtplay'])

        item = MediaItem(title, url)
        item.media_type = mediatype.VIDEO
        item.description = result_set.get('longDescription')
        item.isGeoLocked = result_set['restrictions']['onlyAvailableInSweden']

        self.__extract_artwork(result_set.get("images"), item)

        duration = int(result_set.get("duration", 0))
        item.set_info_label("duration", duration)

        return item

    def create_api_genre_type(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the API.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        This works for:
            __typename=Genre

        """

        if not self.__show_folders:
            return None

        item = FolderItem(result_set["name"], "#genre_item", content_type=contenttype.VIDEOS)
        item.metaData[self.__genre_id] = result_set["id"]


        image_info = result_set.get("image")
        if image_info:
            item.thumb = self.__get_thumb(image_info, width=720)
            item.fanart = self.__get_thumb(image_info)
        else:
            self.__extract_artwork(result_set.get("images"), item)
        return item

    def create_api_search_hit(self, result_set):
        """ Creates a MediaItem of type 'video' or 'folder' using the result_set from the API.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        teaser = result_set["teaser"]
        result_set.update(teaser or {})
        category_teaser = result_set["categoryTeaser"]
        result_set.update(category_teaser or {})

        # Clean up the name and description and highlight the search results.
        name = result_set["heading"]
        name = name.replace("<em>", "[COLOR=yellow]").replace("</em>", "[/COLOR]")
        name = HtmlHelper.to_text(name)

        description = result_set.get("description", "")
        description = description.replace("<em>", "[COLOR=yellow]").replace("</em>", "[/COLOR]")
        description = HtmlHelper.to_text(description)

        result_set["name"] = name
        result_set["heading"] = name
        result_set["description"] = description

        if teaser:
            return self.create_api_typed_item(result_set)
        else:
            return self.create_api_genre_type(result_set)

    def extract_new_on_svt_id(self, data: str) -> Tuple[str, List[MediaItem]]:
        new_id = Regexer.do_regex(r'href="/lista/([^/]+)/nytt-pa-play"', data)[0]
        url = self.__get_api_url(
            "FionaPage",
            "b4e65a8f4cedc6bd9981e3539690908443f625c6854ea65f18c4b3b3be66b5dc",
            variables={"includeFullOppetArkiv": True, "selectionId": new_id})

        self.parentItem.url = url
        items = self.process_folder_list(self.parentItem)
        return data, items

    # noinspection PyUnusedLocal
    def fetch_program_api_data(self, data):
        """ Loaded the data that contains the main episodes for a show.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        This is done to prevent performance issues of the self.__get_api_url() method when
        a lot of items are generated.

        """

        items = []
        slug = self.parentItem.metaData["slug"]
        variables = {"includeFullOppetArkiv": True, "path": slug}
        # https://api.svt.se/contento/graphql?ua=svtplaywebb-render-low-prio-client
        hash_value = "e240d515657bbb54f33cf158cea581f6303b8f01f3022ea3f9419fbe3a5614b0"
        url = self.__get_api_url("DetailsPageQuery", hash_value, variables)
        data = UriHandler.open(url)
        json_data = JsonHelper(data)

        # Get the parent thumb info
        parent_item_thumb_data = json_data.get_value("data", "detailsPageByPath", "images", "wide")

        possible_folders = json_data.get_value("data", "detailsPageByPath", "associatedContent")
        possible_folders = [p for p in possible_folders if p["id"] != "upcoming"]

        if self._get_setting("show_accessibility_videos") == "false":
            possible_folders = [p for p in possible_folders if
                                p.get("selectionType") != "accessibility"]

        if self.__folder_id in self.parentItem.metaData:
            folder_id = self.parentItem.metaData[self.__folder_id]
            Logger.debug("Retrieving folder with id='%s'", folder_id)
            json_data.json = {
                "videos": [f for f in possible_folders if f["id"] == folder_id][0]["items"]}

        elif len(possible_folders) == 1:
            json_data.json = {"videos": possible_folders[0]["items"]}

        else:
            json_data.json = {"folders": possible_folders}

        if "folders" in json_data.json:
            [folder.update({self.__parent_images: parent_item_thumb_data}) for folder in
             json_data.json["folders"]]
        if "videos" in json_data.json:
            [video.update({self.__parent_images: parent_item_thumb_data}) for video in
             json_data.json["videos"]]

        return json_data, items

    # noinspection PyUnusedLocal
    def fetch_genre_api_data(self, data):
        if self.channelCode == "oppetarkiv" and self.parentItem is None:
            genre = "oppet-arkiv"
        else:
            genre = self.parentItem.metaData[self.__genre_id]

        url = self.__get_api_url(
            "CategoryPageQuery",
            "00be06320342614f4b186e9c7710c29a7fc235a1936bde08a6ab0f427131bfaf",
            {"id": genre, "tab": "all", "includeFullOppetArkiv": True}
        )

        data = UriHandler.open(url)
        json_data = JsonHelper(data)
        possible_lists = json_data.get_value("data", "categoryPage", "lazyLoadedTabs", 1, "selections")
        program_items = [genres["items"] for genres in possible_lists if
                         genres["selectionType"] == "all"]
        json_data.json = {
            "programs": [p for p in program_items[0]],
        }
        return json_data, []

    def create_channel_item(self, channel):
        """ Creates a MediaItem of type 'video' for a live channel using the result_set
        from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict channel: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(channel)

        # Channel data
        channel_title = channel["name"]
        channel_id = channel["id"]
        if channel_id == "svtb":
            channel_id = "barnkanalen"
        elif channel_id == "svtk":
            channel_id = "kunskapskanalen"

        # Running data
        schedule = channel["schedule"]
        running = None
        upcoming = None
        for epg in schedule:
            if running:
                upcoming = epg
                break

            if epg["state"] != "running":
                continue

            running = epg

        if not running:
            return None

        title = running["name"]
        episode = running.get("subHeading", None)
        thumb = None
        if "image" in running:
            thumb = self.__get_thumb(running["image"], width=720)
        elif "item" in running and running["item"]:
            if "image" in running["item"]:
                thumb = self.__get_thumb(running["item"]["image"], width=720)
            elif "parent" in running["item"] and running["item"]["parent"] and "images" in running["item"]["parent"] and running["item"]["parent"]["images"]:
                thumb = self.__get_thumb(running["item"]["parent"]["images"]["wide"], width=720)

        description = running.get("description")

        date_format = "%Y-%m-%dT%H:%M:%S"
        start_time = DateHelper.get_date_from_string(running["start"][:19], date_format)
        end_time = None
        if upcoming:
            end_time = DateHelper.get_date_from_string(upcoming["start"][:19], date_format)

        if episode:
            if end_time:
                title = "%s: %s - %s (%02d:%02d - %02d:%02d)" \
                        % (channel_title, title, episode,
                           start_time.tm_hour, start_time.tm_min, end_time.tm_hour, end_time.tm_min)
            else:
                title = "%s: %s - %s (%02d:%02d)" \
                        % (channel_title, title, episode, start_time.tm_hour, start_time.tm_min)
        else:
            if end_time:
                title = "%s: %s (%02d:%02d - %02d:%02d)" \
                        % (channel_title, title,
                           start_time.tm_hour, start_time.tm_min, end_time.tm_hour, end_time.tm_min)
            else:
                title = "%s: %s (%02d:%02d)" \
                        % (channel_title, title, start_time.tm_hour, start_time.tm_min)

        channel_item = MediaItem(
            title,
            "https://www.svt.se/videoplayer-api/video/%s" % (channel_id.lower(),)
        )
        channel_item.media_type = mediatype.VIDEO
        channel_item.isLive = True
        channel_item.isGeoLocked = True
        channel_item.description = description

        channel_item.thumb = thumb
        if "episodeThumbnailIds" in channel and channel["episodeThumbnailIds"]:
            channel_item.thumb = "https://www.svtstatic.se/image/wide/650/%s.jpg" % (
                channel["episodeThumbnailIds"][0],)
        return channel_item

    def search_site(self, url=None):  # @UnusedVariable
        """ Creates an list of items by searching the site.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with an URL encoded representation of the
        text to search for.

        :param str url:     Url to use to search with a %s for the search parameters.

        :return: A list with search results as MediaItems.
        :rtype: list[MediaItem]

        """

        url = self.__get_api_url(
            "AutoCompleteSearch", "8989b62115022fda8a6129d0f512b94f4d2de3bf2110415647c09c4316ce4a91",
            {"querystring": "----", "searchClickHistory": []}
        )

        url = url.replace("https://api.svt.se/contento/graphql",
                          "https://contento-search.svt.se/graphql")
        url = url.replace("%", "%%")
        url = url.replace("----", "%s")
        return chn_class.Channel.search_site(self, url)

    def extract_json_data(self, data):
        """ Extracts JSON data from the HTML for __svtplay and __reduxStore json data.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        return self.__extract_json_data(data, "(?:__svtplay|__reduxStore)")

    def extract_live_channel_data(self, data):
        """ Adds the channel items to the listing.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        json_data = JsonHelper(data)
        channels = json_data.get_value("data", "channels", "channels")
        channel_list = {}

        # get a dictionary with channels
        for channel_data in channels:
            channel_tag = channel_data["urlName"]
            # find the corresponding episode
            channel_list[channel_tag] = channel_data

        programs = dict([kv for kv in json_data.get_value("guidePage", "programs").items() if
                         kv[1].get("isActiveBroadcast", False)])
        schedules = json_data.get_value("guidePage", "schedules")
        for channel_name, program_ids in schedules.items():
            channel_tag = channel_name.split(":")[0]
            channel = channel_list.get(channel_tag, None)
            if channel is None:
                continue

            # see what program is playing
            program_id = [p for p in program_ids if p in programs]
            if not program_id:
                del channel_list[channel_tag]
                continue

            program_id = program_id[0]
            if program_id.startswith("TT"):
                del channel_list[channel_tag]
                continue

            program = programs.get(program_id)
            if program is None:
                del channel_list[channel_tag]
                continue

            channel.update(program)

        json_data.json = channel_list.values()
        return json_data, []

    def update_video_api_item(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaSteam then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting UpdateChannelItem for %s (%s)', item.name, self.channelName)

        data = UriHandler.open(item.url)

        json = JsonHelper(data, logger=Logger.instance())
        videos = json.get_value("videoReferences")
        subtitles = json.get_value("subtitleReferences")
        Logger.trace(videos)
        return self.__update_item_from_video_references(item, videos, subtitles)

    def update_video_html_item(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaSteam then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        data = UriHandler.open(item.url)
        video_id = Regexer.do_regex(r'play-button"[^>]+href="/video/[^?]+\?id=([^"]+)', data)[0]
        item.url = "https://api.svt.se/video/{}".format(video_id)
        return self.update_video_api_item(item)

    def __set_expire_time(self, expire_date, item):
        """ Sets the expire time

        :param str expire_date:
        :param MediaItem item:

        """

        try:
            if expire_date.endswith("z"):
                valid_to = DateHelper.get_datetime_from_string(expire_date, "%Y-%m-%dT%H:%M:%SZ",
                                                               "UTC")
                valid_to = valid_to.astimezone(self.__timezone)
                item.set_expire_datetime(timestamp=valid_to)
            else:
                expire_date = expire_date.split("+")[0].replace("T", " ")
                year = expire_date.split("-")[0]
                if len(year) == 4 and int(year) < datetime.datetime.now().year + 50:
                    expire_date = DateHelper.get_datetime_from_string(expire_date,
                                                                      date_format="%Y-%m-%d %H:%M:%S")
                    item.set_expire_datetime(timestamp=expire_date)
        except:
            Logger.warning("Error setting expire date from: %s", expire_date)

    def __get_thumb(self, thumb_data, width=1920):
        """ Generates a full thumbnail url based on the "id" and "changed" values in a thumbnail
        data object from the API.

        :param dict[string, string] thumb_data: The data for the thumb

        :return: full string url
        :rtype: str
        """

        return "https://www.svtstatic.se/image/wide/{}/{}/{}?quality=70".format(
            width, thumb_data["id"], thumb_data["changed"])

    def __extract_artwork(self, images: dict, item: MediaItem) -> None:
        if not images:
            return

        def create_url(image: dict, art: str, width: int) -> str:
            return f"https://www.svtstatic.se/image/{art}/{width}/{image['id']}/{image['changed']}?quality=70"

        description = None
        if "wide" in images:
            item.thumb = create_url(images["wide"], "wide", width=720)
            item.fanart = create_url(images["wide"], "wide", width=1920)
            description = images["wide"].get("description")
        elif "cleanWide" in images:
            item.thumb = create_url(images["cleanWide"], "wide", width=720)
            item.fanart = create_url(images["cleanWide"], "wide", width=1920)
            description = images["wide"].get("description")

        if description and item.description:
            item.description = f"{item.description}\n\n{description}"
        elif description:
            item.description = description

        # if "portrait" in images:
        #     item.poster = create_url(images["portrait"], "portrait", width=512)
        # if "cleanPortrait" in images:
        #     item.poster = create_url(images["cleanPortrait"], "portrait", width=512)
        return

    def __extract_json_data(self, data, root):
        """ Performs pre-process actions for data processing

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Extracting JSON data during pre-processing")
        data = Regexer.do_regex(r'root\[[\'"]%s[\'"]\] = ([\w\W]+?);\W*root\[' % (root,), data)[-1]
        items = []
        Logger.trace("JSON data found: %s", data)
        return data, items

    def __get_api_url(self, operation, hash_value, variables):
        """ Generates a GraphQL url

        :param str operation:   The operation to use
        :param str hash_value:  The hash of the Query
        :param dict variables:  Any variables to pass

        :return: A GraphQL string
        :rtype: str

        """

        extensions = {"persistedQuery": {"version": 1, "sha256Hash": hash_value}}
        extensions = HtmlEntityHelper.url_encode(JsonHelper.dump(extensions, pretty_print=False))

        variables = HtmlEntityHelper.url_encode(JsonHelper.dump(variables, pretty_print=False))

        url = "https://api.svt.se/contento/graphql?" \
              "operationName={}&" \
              "variables={}&" \
              "extensions={}&" \
              "ua=svtplaywebb-play-render-prod-client".format(operation, variables, extensions)
        return url

    def __update_item_from_video_references(self, item, videos, subtitles=None):  # NOSONAR
        """

        :param MediaItem item:      The original MediaItem that needs updating.
        :param list[any] videos:    Videos to add.
        :param dict subtitles:      Subtitle information.

        :return: Updated MediaItem
        :rtype: MediaItem

        """

        item.streams = []
        use_input_stream = AddonSettings.use_adaptive_stream_add_on(channel=self)
        in_sweden = self.__validate_location()
        Logger.debug("Streaming location within GEO area: %s", in_sweden)

        # Dictionary with supported video formats and their priority.
        if in_sweden or not item.isGeoLocked:
            # For the Dash streams:
            # "dash-full" has HEVC and x264 video, with multi stream audio, both 5.1 and 2.0 streams
            # "dash-hbbtv-avc" has x264 multi stream audio, but only 5.1
            # "dash" has x264 single stream audio and only 2.0
            # supported_formats = {"dash": 2, "dash-full": 3, "hls": 0, "hls-ts-full": 1}
            supported_formats = {"dash": 2, "dash-hbbtv-avc": 3, "hls": 0, "hls-ts-full": 1}
        else:
            supported_formats = {"dash": 2, "dash-avc-51": 3, "hls": 0, "hls-ts-avc-51": 1}
        Logger.debug("Looking for formats: %s", ", ".join(supported_formats.keys()))

        for video in videos:
            video_format = video.get("format", "")
            if not video_format:
                video_format = video.get("playerType", "")
            video_format = video_format.lower()

            if video_format not in supported_formats:
                Logger.debug("Skipping video format: %s", video_format)
                continue
            Logger.debug("Found video item for format: %s", video_format)

            url = video['url']
            if any(filter(lambda s: s.Url == url, item.streams)):
                Logger.debug("Skippping duplicate Stream url: %s", url)
                continue

            if "dash" in video_format and use_input_stream:
                stream = item.add_stream(video['url'], supported_formats[video_format])
                Mpd.set_input_stream_addon_input(stream)

            elif "m3u8" in url:
                alt_index = url.find("m3u8?")
                if alt_index > 0:
                    url = url[0:alt_index + 4]

                if "-fmp4.m3u8" in url or "-lowbw.m3u8" in url:
                    Logger.trace("Ignoring: %s", url)
                    continue

                M3u8.update_part_with_m3u8_streams(
                    item,
                    url,
                    encrypted=False,
                    channel=self,
                    bitrate=supported_formats[video_format]
                )

            elif video["url"].startswith("rtmp"):
                # just replace some data in the URL
                item.add_stream(
                    self.get_verifiable_video_url(video["url"]).replace("_definst_", "?slist="),
                    video[1])
            else:
                item.add_stream(url, 0)

        if subtitles:
            Logger.info("Found subtitles to play")
            for sub in subtitles:
                sub_format = sub["format"].lower()
                url = sub["url"]
                if sub_format == "websrt":
                    sub_url = url
                elif sub_format == "webvtt":
                    sub_url = url
                else:
                    # look for more
                    continue

                item.subtitle = subtitlehelper.SubtitleHelper.download_subtitle(
                    sub_url, format="srt", replace={"&amp;": "&"})
                # stop when finding one
                break

        item.complete = True
        return item

    def __validate_location(self):
        url = "https://api.svt.se/geo.modernizr.js"
        data = UriHandler.open(url, force_text=True, no_cache=True)
        return "return true" in data
