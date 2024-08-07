# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
from typing import Tuple, List, Optional, Union

import pytz

# noinspection PyUnresolvedReferences
from awsidp import AwsIdp
from resources.lib import chn_class, contenttype, mediatype
from resources.lib.actions import keyword, action
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, MediaItemResult, FolderItem
from resources.lib.regexer import Regexer
from resources.lib.retroconfig import Config
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.mpd import Mpd
from resources.lib.urihandler import UriHandler
from resources.lib.vault import Vault
from resources.lib.xbmcwrapper import XbmcWrapper


class NextJsParser:
    def __init__(self, regex: str):
        self.__regex = regex

    def __call__(self, data: str) -> Tuple[JsonHelper, List[MediaItem]]:
        nextjs_regex = self.__regex
        try:
            nextjs_data = Regexer.do_regex(nextjs_regex, data)[0]
        except:
            Logger.debug(f"RAW NextJS: {data}")
            raise

        Logger.trace(f"NextJS: {nextjs_data}")
        nextjs_json = JsonHelper(nextjs_data)
        return nextjs_json, []

    def __str__(self):
        return f"NextJS parser: {self.__regex}"


class Channel(chn_class.Channel):
    """
    main class from resources.lib.which all channels inherit
    """

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # setup the main parsing data
        self.baseUrl = "https://www.goplay.be"
        self.httpHeaders = {"rsc": "1"}

        if self.channelCode == "vijfbe":
            self.noImage = "vijffanart.png"
            self.mainListUri = "https://www.goplay.be/programmas/play-5"
            self.__channel_brand = "play5"
            self.__channel_slug = "vijf"

        elif self.channelCode == "zesbe":
            self.noImage = "zesfanart.png"
            self.mainListUri = "https://www.goplay.be/programmas/play-6"
            self.__channel_brand = "play6"
            self.__channel_slug = "zes"

        elif self.channelCode == "zevenbe":
            self.noImage = "zevenfanart.png"
            self.mainListUri = "https://www.goplay.be/programmas/play-7"
            self.__channel_brand = "play7"
            self.__channel_slug = "zeven"

        elif self.channelCode == "goplay":
            self.noImage = "goplayfanart.png"
            # self.mainListUri = "https://www.goplay.be/programmas/"
            self.mainListUri = "#goplay"
            self.__channel_brand = None
        else:
            self.noImage = "vierfanart.png"
            self.mainListUri = "https://www.goplay.be/programmas/play-4"
            self.__channel_brand = "play4"
            self.__channel_slug = "vier"

        self._add_data_parser("#goplay", preprocessor=self.add_specials)

        self._add_data_parser("#recent", preprocessor=self.add_recent_items)

        self._add_data_parser("https://www.goplay.be/programmas/", json=True,
                              preprocessor=NextJsParser(
                                  r"{\"brand\":\".+?\",\"results\":(.+),\"categories\":"))

        self._add_data_parser("https://www.goplay.be/programmas/", json=True,
                              preprocessor=self.add_recents,
                              parser=[], creator=self.create_typed_nextjs_item)

        self._add_data_parser("https://www.goplay.be/", json=True, name="Main show parser",
                              preprocessor=NextJsParser(r"{\"playlists\":(.+)}\]}\]\]$"),
                              parser=[], creator=self.create_season_item,
                              postprocessor=self.show_single_season)

        self._add_data_parser("https://www.goplay.be/tv-gids/", json=True, name="TV Guides",
                              preprocessor=NextJsParser(
                                  r"children\":(\[\[\"\$\",[^{]+{\"program.+\])}\]\]}\]"),
                              parser=[], creator=self.create_epg_item)

        self._add_data_parser("https://api.goplay.be/web/v1/search", json=True,
                              name="Search results parser",
                              parser=["hits", "hits"], creator=self.create_search_result)

        self._add_data_parser("https://api.goplay.be/web/v1/videos/long-form/",
                              updater=self.update_video_item_with_id)
        self._add_data_parser("https://www.goplay.be/video/",
                              updater=self.update_video_item_from_nextjs)
        self._add_data_parser("https://www.goplay.be/",
                              updater=self.update_video_item)

        # ==========================================================================================
        # Channel specific stuff
        self.__idToken = None
        self.__tz = pytz.timezone("Europe/Brussels")

        # ==========================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here ===================
        return

    def add_specials(self, data: JsonHelper) -> Tuple[JsonHelper, List[MediaItem]]:
        if self.channelCode != "goplay":
            return data, []

        search_title = LanguageHelper.get_localized_string(LanguageHelper.Search)
        search_item = FolderItem(search_title, self.search_url, content_type=contenttype.VIDEOS)

        url_format = f"plugin://{Config.addonId}/?{keyword.CHANNEL}={{}}&{keyword.ACTION}={action.LIST_FOLDER}"
        vier = FolderItem("4: Vier", url_format.format("channel.be.vier"),
                          content_type=contenttype.TVSHOWS)
        vier.set_artwork(
            poster=self.get_image_location("vierposter.png"),
            fanart=self.get_image_location("vierfanart.jpg"),
            icon=self.get_image_location("viericon.png")
        )

        vijf = FolderItem("5: Vijf", url_format.format("channel.be.vier-vijfbe"),
                          content_type=contenttype.TVSHOWS)
        vijf.set_artwork(
            poster=self.get_image_location("vijfposter.png"),
            fanart=self.get_image_location("vijffanart.jpg"),
            icon=self.get_image_location("vijficon.png")
        )

        zes = FolderItem("6: Zes", url_format.format("channel.be.vier-zesbe"),
                         content_type=contenttype.TVSHOWS)
        zes.set_artwork(
            poster=self.get_image_location("zesposter.png"),
            fanart=self.get_image_location("zesfanart.jpg"),
            icon=self.get_image_location("zesicon.png")
        )

        zeven = FolderItem("7: Zeven", url_format.format("channel.be.vier-zevenbe"),
                           content_type=contenttype.TVSHOWS)
        zeven.set_artwork(
            poster=self.get_image_location("zevenposter.jpg"),
            fanart=self.get_image_location("zevenfanart.jpg"),
            icon=self.get_image_location("zevenicon.png")
        )

        all_items = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.TvShows),
            "https://www.goplay.be/programmas/",
            content_type=contenttype.TVSHOWS
        )
        return data, [search_item, vier, vijf, zes, zeven, all_items]

    def add_recents(self, data: JsonHelper) -> Tuple[JsonHelper, List[MediaItem]]:
        title = LanguageHelper.get_localized_string(LanguageHelper.Recent)
        recent = FolderItem(title, "#recent", content_type=contenttype.TVSHOWS)
        recent.dontGroup = True
        recent.name = f".: {title} :."
        return data, [recent]

    def add_recent_items(self, data: JsonHelper) -> Tuple[JsonHelper, List[MediaItem]]:
        """ Performs pre-process actions for data processing.

        Accepts a data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        today = datetime.datetime.now()
        days = LanguageHelper.get_days_list()
        for d in range(0, 7, 1):
            air_date = today - datetime.timedelta(d)
            Logger.trace("Adding item for: %s", air_date)

            # Determine a nice display date
            day = days[air_date.weekday()]
            if d == 0:
                day = LanguageHelper.get_localized_string(LanguageHelper.Today)
            elif d == 1:
                day = LanguageHelper.get_localized_string(LanguageHelper.Yesterday)

            title = "%04d-%02d-%02d - %s" % (air_date.year, air_date.month, air_date.day, day)
            url = "https://www.goplay.be/tv-gids/{}/{:04d}-{:02d}-{:02d}".\
                format(self.__channel_slug, air_date.year, air_date.month, air_date.day)

            extra = MediaItem(title, url)
            extra.complete = True
            extra.dontGroup = True
            extra.HttpHeaders = self.httpHeaders
            extra.set_date(air_date.year, air_date.month, air_date.day, text="")
            extra.content_type = contenttype.VIDEOS
            items.append(extra)

        return data, items

    def search_site(self, url: Optional[str] = None, needle: Optional[str] = None) -> List[MediaItem]:
        """ Creates a list of items by searching the site.

        This method is called when and item with `self.search_url` is opened. The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with a URL encoded representation of the
        text to search for.

        :param url:     Url to use to search with an %s for the search parameters.
        :param needle:  The needle to search for.

        :return: A list with search results as MediaItems.

        """

        if not needle:
            raise ValueError("No needle present")

        url = f"https://api.goplay.be/web/v1/search"
        payload = {"mode": "byDate", "page": 0, "query": needle}
        temp = MediaItem("Search", url, mediatype.FOLDER)
        temp.postJson = payload
        return self.process_folder_list(temp)

    def create_typed_nextjs_item(self, result_set: dict) -> MediaItemResult:
        item_type = result_set["type"]
        item_sub_type = result_set["subtype"]

        if item_type == "program":
            return self.create_program_typed_item(result_set)
        else:
            Logger.warning(f"Unknown type: {item_type}:{item_sub_type}")
        return None

    def create_program_typed_item(self, result_set: dict) -> MediaItemResult:
        item_sub_type = result_set["subtype"]
        data = result_set.get("data")

        if not data:
            return None

        brand = data["brandName"].lower()
        if self.__channel_brand and brand != self.__channel_brand:
            return None

        title = data["title"]
        path = data["path"]
        url = f"{self.baseUrl}{path}"

        if item_sub_type == "movie":
            url = f"{self.baseUrl}/video{path}"
            item = MediaItem(title, url, media_type=mediatype.MOVIE)
            # item.metaData["retrospect:parser"] = "movie"
        else:
            item = FolderItem(title, url, content_type=contenttype.EPISODES)

        if "brandName" in data:
            item.metaData["brand"] = data["brandName"]
        if "categoryName" in data:
            item.metaData["category"] = data["categoryName"]
        if "parentalRating" in data:
            item.metaData["parental"] = data["parentalRating"]

        self.__extract_artwork(item, data.get("images"))
        return item

    def create_season_item(self, result_set):
        season_item = None
        season = result_set.get("season", 0)

        if season:
            title = f"{LanguageHelper.get_localized_string(LanguageHelper.SeasonId)} {season}"
            season_item = FolderItem(title, result_set["uuid"], content_type=contenttype.EPISODES)

        videos = []
        video_info: dict
        for video_info in result_set.get("videos", []):
            title = video_info["title"]
            url = f"{self.baseUrl}{video_info['path']}"
            video_date = video_info["dateCreated"]
            description = video_info["description"]
            # video_id = video_info["uuid"]
            episode = video_info.get("episodeNumber", 0)

            item = MediaItem(title, url, media_type=mediatype.EPISODE)
            item.description = description

            self.__extract_artwork(item, video_info.get("images"), set_fanart=False)

            if episode and season:
                item.set_season_info(season, episode)

            date_stamp = DateHelper.get_date_from_posix(int(video_date), tz=self.__tz)
            item.set_date(date_stamp.year, date_stamp.month, date_stamp.day, date_stamp.hour,
                          date_stamp.minute, date_stamp.second)

            duration = (video_info.get("streamCollection", {}) or {}).get("duration", 0)
            if duration:
                item.set_info_label(MediaItem.LabelDuration, duration)

            videos.append(item)
            if season_item:
                season_item.items.append(item)

        if season_item:
            return season_item
        return videos

    # noinspection PyUnusedLocal
    def show_single_season(self, data: Union[str, JsonHelper], items: List[MediaItem]) -> List[MediaItem]:
        if len(items) == 1 and len(items[0].items) > 0:
            Logger.info("Showing the full listing of a single season.")
            return items[0].items
        return items

    def create_search_result(self, result_set: dict) -> MediaItemResult:
        data = result_set["_source"]

        title = data["title"]
        url = data["url"]
        description = data["intro"]
        thumb = data["img"]
        video_date = data["created"]
        item_type = data["bundle"]

        if item_type == "video":
            item = MediaItem(title, url, media_type=mediatype.VIDEO)
        elif item_type == "program":
            if (data["tracking"] and data["tracking"]["item_category"] == "Film") or data["program"] == "":
                url = url.replace(self.baseUrl, f"{self.baseUrl}/video")
                item = MediaItem(title, url, media_type=mediatype.MOVIE)
            else:
                item = FolderItem(title, url, content_type=contenttype.EPISODES)
        else:
            Logger.warning("Unknown search result type.")
            return None

        item.description = description
        item.set_artwork(thumb=thumb)
        date_stamp = DateHelper.get_date_from_posix(int(video_date), tz=self.__tz)
        item.set_date(date_stamp.year, date_stamp.month, date_stamp.day, date_stamp.hour,
                      date_stamp.minute, date_stamp.second)
        return item

    def create_epg_item(self, result_set: dict) -> MediaItemResult:
        data = result_set[-1]["program"]
        if not data["video"]:
            return None

        title = data["programTitle"]
        episode_title = data["episodeTitle"]
        time_value = data["timeString"]
        if episode_title:
            title = f"{time_value} - {title} - {episode_title}"
        else:
            title = f"{time_value} - {title}"

        description = data["contentEpisode"]
        time_stamp = data["timestamp"]
        duration = data["duration"]

        video_info = data["video"]["data"]
        path = video_info["path"]
        video_type = video_info["type"]
        if video_type != "video":
            Logger.warning(f"Unknown EPG type: {video_type}")

        item = MediaItem(title, f"{self.baseUrl}{path}", media_type=mediatype.EPISODE)
        item.description = description
        item.set_info_label(MediaItem.LabelDuration, duration)

        # Setting this messes up the sorting.
        # episode = data["episodeNr"]
        # season = data["season"]
        # item.set_season_info(season, episode)

        date_stamp = DateHelper.get_date_from_posix(time_stamp, tz=self.__tz)
        item.set_date(date_stamp.year, date_stamp.month, date_stamp.day, date_stamp.hour,
                      date_stamp.minute, date_stamp.second)
        self.__extract_artwork(item, video_info["images"], set_fanart=False)
        return item

    # def add_specials(self, data):
    #     """ Performs pre-process actions for data processing.
    #
    #     Accepts an data from the process_folder_list method, BEFORE the items are
    #     processed. Allows setting of parameters (like title etc) for the channel.
    #     Inside this method the <data> could be changed and additional items can
    #     be created.
    #
    #     The return values should always be instantiated in at least ("", []).
    #
    #     :param str data: The retrieve data that was loaded for the current item and URL.
    #
    #     :return: A tuple of the data and a list of MediaItems that were generated.
    #     :rtype: tuple[str|JsonHelper,list[MediaItem]]
    #
    #     """
    #
    #     items = []
    #
    #     specials = {
    #         "https://www.goplay.be/api/programs/popular/{}".format(self.__channel_slug): (
    #             LanguageHelper.get_localized_string(LanguageHelper.Popular),
    #             contenttype.TVSHOWS
    #         ),
    #         "#tvguide": (
    #             LanguageHelper.get_localized_string(LanguageHelper.Recent),
    #             contenttype.FILES
    #         )
    #     }
    #
    #     for url, (title, content) in specials.items():
    #         item = MediaItem("\a.: {} :.".format(title), url)
    #         item.content_type = content
    #         items.append(item)
    #
    #     return data, items

    def log_on(self):
        """ Logs on to a website, using an url.

        First checks if the channel requires log on. If so and it's not already
        logged on, it should handle the log on. That part should be implemented
        by the specific channel.

        More arguments can be passed on, but must be handled by custom code.

        After a successful log on the self.loggedOn property is set to True and
        True is returned.

        :return: indication if the login was successful.
        :rtype: bool

        """

        if self.__idToken:
            return True

        # check if there is a refresh token
        refresh_token = AddonSettings.get_setting("viervijfzes_refresh_token")
        client = AwsIdp("eu-west-1_dViSsKM5Y", "6s1h851s8uplco5h6mqh1jac8m",
                        logger=Logger.instance())
        if refresh_token:
            id_token = client.renew_token(refresh_token)
            if id_token:
                self.__idToken = id_token
                return True
            else:
                Logger.info("Extending token for VierVijfZes failed.")

        username = AddonSettings.get_setting("viervijfzes_username")
        v = Vault()
        password = v.get_setting("viervijfzes_password")
        if not username or not password:
            XbmcWrapper.show_dialog(
                title=None,
                message=LanguageHelper.get_localized_string(LanguageHelper.MissingCredentials),
            )
            return False

        id_token, refresh_token = client.authenticate(username, password)
        if not id_token or not refresh_token:
            Logger.error("Error getting a new token. Wrong password?")
            return False

        self.__idToken = id_token
        AddonSettings.set_setting("viervijfzes_refresh_token", refresh_token)
        return True

    def update_video_item(self, item: MediaItem) -> MediaItem:
        data = UriHandler.open(item.url, additional_headers=self.httpHeaders)
        list_id = Regexer.do_regex(r"listId\":\"([^\"]+)\"", data)[0]
        item.url = f"https://api.goplay.be/web/v1/videos/long-form/{list_id}"
        return self.update_video_item_with_id(item)

    def update_video_item_from_nextjs(self, item: MediaItem) -> MediaItem:
        data = UriHandler.open(item.url, additional_headers=self.httpHeaders)
        json_data = Regexer.do_regex(r"({\"video\":{.+?})\]}\],", data)[0]
        nextjs_json = JsonHelper(json_data)
        video_id = nextjs_json.get_value("videoId")
        item.metaData["whatsonId"] = nextjs_json.get_value("video", "tracking", "whatsonId")
        item.url = f"https://api.goplay.be/web/v1/videos/long-form/{video_id}"
        return self.update_video_item_with_id(item)

    def update_video_item_with_id(self, item: MediaItem) -> MediaItem:
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

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        # We need to log in
        if not self.loggedOn:
            self.log_on()

        # add authorization header
        authentication_header = {
            "authorization": "Bearer {}".format(self.__idToken),
            "content-type": "application/json"
        }

        data = UriHandler.open(item.url, additional_headers=authentication_header, no_cache=True)
        json_data = JsonHelper(data)

        if json_data.get_value("ssai") is not None:
            return self.__get_ssai_streams(item, json_data)

        m3u8_url = json_data.get_value("manifestUrls", "hls")

        # # If there's no m3u8 URL, try to use a SSAI stream instead
        # if m3u8_url is None and json_data.get_value("ssai") is not None:
        #     return self.__get_ssai_streams(item, json_data)

        if m3u8_url is None and json_data.get_value('message') is not None:
            error_message = json_data.get_value('message')
            if error_message == "Locked":
                # set it for the error statistics
                item.isGeoLocked = True

                whatson_id = item.metaData.get("whatsonId", None)
                if whatson_id:
                    # 2615619 = GoPlay contentSourceID.
                    return self.__get_ssai_streams_for_content_source(item, 2615619, whatson_id, None)

            Logger.info("No stream manifest found: {}".format(error_message))
            item.complete = False
            return item

        # Geo Locked?
        if "/geo/" in m3u8_url.lower():
            # set it for the error statistics
            item.isGeoLocked = True

        item.complete = M3u8.update_part_with_m3u8_streams(
            item, m3u8_url, channel=self, encrypted=False)

    def __extract_artwork(self, item: MediaItem, images: dict, set_fanart: bool = True):
        if not images:
            return

        if "poster" in images:
            item.poster = images["poster"]
        if "default" in images:
            item.thumb = images["default"]
            if set_fanart:
                item.fanart = images["default"]
        elif "posterLandscape" in images:
            item.thumb = images["posterLandscape"]
            if set_fanart:
                item.fanart = images["posterLandscape"]

    def __get_ssai_streams(self, item, json_data):
        Logger.info("No stream data found, trying SSAI data")
        content_source_id = json_data.get_value("ssai", "contentSourceID")
        video_id = json_data.get_value("ssai", "videoID")
        drm_header = json_data.get_value("drmXml", fallback=None)
        return self.__get_ssai_streams_for_content_source(item, content_source_id, video_id, drm_header)
    
    def __get_ssai_streams_for_content_source(self, item, content_source_id, video_id, drm_header):
        Logger.info("No stream data found, trying SSAI data")
        
        streams_url = 'https://dai.google.com/ondemand/dash/content/{}/vid/{}/streams'.format(
            content_source_id, video_id)
        # streams_url = "https://pubads.g.doubleclick.net/ondemand/dash/content/{}/vid/{}/streams".format(
        #     content_source_id, video_id)

        streams_input_data = {
            "api-key": "null"
            # "api-key": item.metaData.get("drm", "null")
        }
        streams_headers = {
            "content-type": "application/json"
        }
        data = UriHandler.open(streams_url, data=streams_input_data,
                               additional_headers=streams_headers, no_cache=True)
        json_data = JsonHelper(data)
        mpd_url = json_data.get_value("stream_manifest")

        stream = item.add_stream(mpd_url, 0)

        if drm_header:
            header = {"customdata": drm_header, "content-type": "application/octet-stream"}
            license_key = Mpd.get_license_key(
                "https://wv-keyos.licensekeyserver.com/", key_type="R",
                key_headers=header)
            Mpd.set_input_stream_addon_input(stream, license_key=license_key)
        else:
            Mpd.set_input_stream_addon_input(stream)
        item.complete = True
        return item
