# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import time
from typing import Optional, List, Tuple, Union, Dict

import pytz

from resources.lib import chn_class
from resources.lib import contenttype
from resources.lib import mediatype
from resources.lib.channelinfo import ChannelInfo
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.logger import Logger
from resources.lib.parserdata import ParserData
from resources.lib.regexer import Regexer
from resources.lib.helpers import subtitlehelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.streams.npostream import NpoStream
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.vault import Vault
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.actions import action
from resources.lib.textures import TextureHandler


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info: ChannelInfo):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "nosimage.png"

        # setup the urls
        if self.channelCode == "uzgjson":
            self.baseUrl = "https://npo.nl/start/api/"
            self.mainListUri = "#mainlist"
            self.noImage = "nosimage.png"
        else:
            raise NotImplementedError("Code %s is not implemented" % (self.channelCode,))

        # mainlist stuff
        self._add_data_parser("#mainlist", preprocessor=self.get_initial_folder_items)

        # live stuff
        self.baseUrlLive = "https://www.npostart.nl"

        self.__user_name = self._get_setting("username")

        self._add_data_parser("https://npo.nl/start/api/domain/guide-channels",
                              name="Main Live TV Streams json", json=True,
                              requires_logon=True,
                              parser=[],
                              creator=self.create_api_live_tv,
                              updater=self.update_video_item_live)

        self._add_data_parser("https://npo.nl/start/api/domain/guide-channels",
                              name="Recent Items", label="recent", json=True,
                              preprocessor=self.create_epg_days)

        self._add_data_parser("#recentday", name="EPG listing", json=True,
                              preprocessor=self.load_all_epg_channels,
                              parser=[], creator=self.create_api_epg_item)

        self._add_data_parser("https://npo.nl/start/live?channel=",
                              name="Live Video Updater from json",
                              requires_logon=True,
                              updater=self.update_video_item_live)

        # If the user was logged in, we need to refresh the token otherwise it will result in 403
        self._add_data_parsers([
            "https://npo.nl/start/api/domain/page-collection?guid=",
            "https://npo.nl/start/api/domain/page-collection?type=series&guid=",
            "https://npo.nl/start/api/domain/search-results?searchType=series"],
            name="Collections with series", json=True, requires_logon=bool(self.__user_name),
            parser=["items"],
            creator=self.create_api_program_item)
        # Use the new `label` options for the collections
        self._add_data_parser(
            "https://npo.nl/start/api/domain/recommendation-collection?key=", name="Collection with series",
            json=True, label="collection-with-series", requires_logon=bool(self.__user_name),
            parser=["items"],
            creator=self.create_api_program_item)

        # If the user was logged in, we need to refresh the token otherwise it will result in 403
        self._add_data_parsers([
            "https://npo.nl/start/api/domain/search-results?searchType=broadcasts",
            "https://npo.nl/start/api/domain/page-collection?type=program&guid="
        ],
            name="Collections with videos", json=True, requires_logon=bool(self.__user_name),
            parser=["items"],
            creator=self.create_api_episode_item_with_data
        )
        # Use the new `label` options for the collections
        self._add_data_parser(
            "https://npo.nl/start/api/domain/recommendation-collection?key=", name="Collection with videos",
            json=True, label="collection-with-videos", requires_logon=bool(self.__user_name),
            parser=["items"],
            creator=self.create_api_episode_item_with_data)

        self._add_data_parser(
            "https://npo.nl/start/api/domain/series-seasons",
            name="Season API parser (and updater for EPG)", json=True,
            postprocessor=self.check_for_single_season,
            parser=[], creator=self.create_api_season_item,
            updater=self.update_epg_series_item)

        self._add_data_parsers([
            "https://npo.nl/start/api/domain/programs-by-season",
            "https://npo.nl/start/api/domain/programs-by-series"],
            name="Season content API parser", json=True,
            parser=[], creator=self.create_api_episode_item)

        self._add_data_parser("https://npo.nl/start/video/",
                              name="Single video items from recent guid",
                              updater=self.update_single_video)

        # Standard updater
        self._add_data_parser("*", requires_logon=True,
                              updater=self.update_video_item)

        self._add_data_parser("https://npo.nl/start/api/domain/page-layout?slug=",
                              name="Bare pages layout", json=True,
                              parser=["collections"], creator=self.create_api_page_layout)

        # Favourites (not yet implemented in the site).
        self._add_data_parser("https://npo.nl/start/api/domain/user-profiles",
                              match_type=ParserData.MatchExact, json=True, requires_logon=True,
                              name="Profile selection",
                              parser=[], creator=self.create_profile_item)

        self._add_data_parser("#list_profile", name="List profile content", json=True,
                              preprocessor=self.switch_profile,
                              parser=["collections"], creator=self.create_profile_content_item,
                              requires_logon=True)

        # OLD but still working?
        # live radio, the folders and items
        self._add_data_parser(
            "https://www.npoluister.nl/", name="Live Radio Streams",
            parser=Regexer.from_expresso('<li><a[^>]+href="(?<url>https:[^"]+)"[^>]*><img[^>]+src="(?<thumb>https:[^"]+)[^>]+alt="(?<title>[^"]+)"'),
            creator=self.create_live_radio
        )
        self._add_data_parser(
            "*", name="Live Radio Streams Updater",
            updater=self.update_live_radio,
            label="liveRadio"
        )

        self.__ignore_cookie_law()

        # ===============================================================================================================
        # non standard items
        self.__jsonApiKeyHeader = {"apikey": "07896f1ee72645f68bc75581d7f00d54"}
        self.__max_page_count = 10
        self.__has_premium_cache = None
        self.__timezone = pytz.timezone("Europe/Amsterdam")
        self.__show_future = self._get_setting("show_future", "true") == "true"

        # use a dictionary so the lookup is O(1)
        self.__channel_name_map = {
            "_101_": None,  # "NPO1 Extra", -> Mainly paid
            "CULT": None,  # "NPO2 Extra", -> Mainly paid
            "OPVO": None,  # "NPO Zappelin", -> Mainly paid
            "NOSJ": None,  # "NPO Nieuws" -> Cannot be played
            "_mcr_": None,  # "NPO Politiek" -> Niet gevonden
            "PO24": None,  # Cannot be played,
            "NED1": "NPO 1",
            "NED2": "NPO 2",
            "NED3": "NPO 3",
        }

        self.__collection_names = {
            "follows": LanguageHelper.Following,
            "trending": LanguageHelper.Trending,
            "because-you-watched": LanguageHelper.RecommendedTvShows,
            "recent": LanguageHelper.Recent,
            "public-value": None,
            "series": LanguageHelper.TvShows,
            "crime": None,
            "documentaries": None,
            "continue": LanguageHelper.ContinueWatching,
            "news": LanguageHelper.LatestNews,
            "popular": LanguageHelper.Popular,
            "recommended-for-you": LanguageHelper.RecommendedVideos,
            "films": LanguageHelper.Movies,
            "youth": None,
        }

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def log_on(self) -> bool:
        if self.loggedOn:
            return True

        return self.__log_on(False)

    def __log_on(self, force_log_off: bool = False) -> bool:
        """ Makes sure that we are logged on. """

        def log_out_npo() -> None:
            # Old cookies
            UriHandler.delete_cookie(domain=".npostart.nl")
            UriHandler.delete_cookie(domain=".npo.nl")
            UriHandler.delete_cookie(domain="www.npostart.nl")
            # New cookies
            UriHandler.delete_cookie(domain="id.npo.nl")
            UriHandler.delete_cookie(domain="npo.nl")
            AddonSettings.set_channel_setting(self, "previous_username", username, store=LOCAL)

        username = self.__user_name
        previous_name = AddonSettings.get_channel_setting(self, "previous_username", store=LOCAL)
        log_out = previous_name != username
        if log_out or force_log_off:
            if log_out:
                Logger.info("Username changed for NPO from '%s' to '%s'", previous_name, username)
            else:
                Logger.info("Forcing a new login for NPO")
            log_out_npo()

        if not username:
            log_out_npo()
            return False

        # https://ccm.npo.nl/sites/NPO/npo.nl/version.txt -> app version (for live channels?)

        # Check for a valid token.
        session_info_url = "https://npo.nl/start/api/auth/session"
        profile = UriHandler.open(session_info_url, no_cache=True)
        profile = JsonHelper(profile)
        expires = profile.get_value("tokenExpiresAt", fallback=0)
        if expires:
            Logger.debug("NPO Token expires at %s UTC",
                         datetime.datetime.utcfromtimestamp(expires).strftime('%Y-%m-%d %H:%M:%S'))
        if bool(profile.json) and expires > time.time():
            return True

        # Fetch a CSRF token
        data = UriHandler.open("https://npo.nl/start/api/auth/csrf", no_cache=True)
        csrf_token = JsonHelper(data).get_value("csrfToken")

        # Start an authentication session. Will redirect to the new id.npo.nl site with a return url given.
        sign_in_data = {
            "callbackUrl": session_info_url,
            "csrfToken": csrf_token,
            "json": True
        }
        login_form = UriHandler.open("https://npo.nl/start/api/auth/signin/npo-id",
                                     json=sign_in_data)

        if UriHandler.instance().status.url == session_info_url:
            # Already logged in so the login_form redirected to session info
            profile = JsonHelper(login_form)
            Logger.info("Refreshed NPO log in.")
            expires = profile.get_value("tokenExpiresAt", fallback=0)
            Logger.debug("NPO Token expires at %s UTC",
                         datetime.datetime.utcfromtimestamp(expires).strftime('%Y-%m-%d %H:%M:%S'))
            return bool(profile.json)

        # Force a full check-out -> This can't be done as it removes the XSRF tokens.
        # log_out_npo()

        Logger.info("Starting new NPO log in.")
        v = Vault()
        password = v.get_channel_setting(self.guid, "password")
        if not bool(password):
            Logger.warning("No password found for %s", self)
            return False

        # Extract the verification token & Return Url.
        return_url = Regexer.do_regex(r'name="ReturnUrl"[^>]+value="([^"]+)"', login_form)[
            0].replace("&amp;", "&")
        verification_code = \
            Regexer.do_regex(r'name="__RequestVerificationToken"[^>]+value="([^"]+)"', login_form)[
                0]
        data = {
            "EmailAddress": username,
            "Password": password,
            "ReturnUrl": return_url,
            "__RequestVerificationToken": verification_code,
            "button": "login"
        }

        # The actual call for logging in. It will result in the proper redirect.
        profile = UriHandler.open("https://id.npo.nl/account/login", no_cache=True, data=data)
        if "validation-summary" in profile:
            error = Regexer.do_regex(r"<ul><li>(.+?)</li", profile)
            if error:
                Logger.critical(error[0])
                XbmcWrapper.show_dialog(LanguageHelper.LoginErrorTitle, error[0])
            else:
                Logger.critical("Unknown NPO error.")
            return False
        return bool(JsonHelper(profile).json)

    def get_initial_folder_items(self, data: Union[str, JsonHelper]) -> Tuple[Union[str, JsonHelper], List[MediaItem]]:
        """ Creates the initial folder items for this channel.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        def add_item(language_id: int, url: str, content_type: str,
                     description: str = "", headers: Optional[dict] = None, parser: str = "") -> FolderItem:
            item = FolderItem(
                LanguageHelper.get_localized_string(language_id), url, content_type=content_type)
            item.description = description
            item.complete = True
            item.dontGroup = True
            if headers:
                item.HttpHeaders = headers
            if parser:
                item.metaData["retrospect:parser"] = parser
            items.append(item)
            return item

        add_item(LanguageHelper.Search, self.search_url, contenttype.EPISODES,
                 headers={"X-Requested-With": "XMLHttpRequest"})

        # Favorite items that require login
        if self.__user_name:
            add_item(LanguageHelper.Profiles, "https://npo.nl/start/api/domain/user-profiles",
                     contenttype.NONE,
                     description="Profile van de  npostart.nl website.")

        add_item(LanguageHelper.Trending,
                 "https://npo.nl/start/api/domain/recommendation-collection?key=trending-anonymous-v0",
                 content_type=contenttype.TVSHOWS, parser="collection-with-series")

        add_item(LanguageHelper.LatestNews,
                 "https://npo.nl/start/api/domain/recommendation-collection?key=news-anonymous-v0&partyId=unknown",
                 content_type=contenttype.TVSHOWS, parser="collection-with-videos")

        add_item(LanguageHelper.Popular,
                 "https://npo.nl/start/api/domain/recommendation-collection?key=popular-anonymous-v0&partyId=unknown",
                 content_type=contenttype.TVSHOWS, parser="collection-with-videos")

        # add_item(LanguageHelper.Categories,
        #     "https://npo.nl/start/api/domain/page-collection?guid=2670b702-d621-44be-b411-7aae3c3820eb",
        #         content_type=contenttype.TVSHOWS)

        add_item(LanguageHelper.TvShows,
                 "https://npo.nl/start/api/domain/page-layout?slug=programmas",
                 content_type=contenttype.TVSHOWS)

        live_radio = add_item(
            LanguageHelper.LiveRadio, "https://www.npoluister.nl/",
            content_type=contenttype.SONGS, headers=self.__jsonApiKeyHeader)
        live_radio.isLive = True

        live_tv = add_item(
            LanguageHelper.LiveTv, "https://npo.nl/start/api/domain/guide-channels",
            content_type=contenttype.VIDEOS)
        live_tv.isLive = True

        extra = FolderItem(
            "{} ({})".format(
                LanguageHelper.get_localized_string(LanguageHelper.TvShows),
                LanguageHelper.get_localized_string(LanguageHelper.FullList)
            ),
            f"https://start-api.npo.nl/media/series?pageSize={50}&dateFrom=2014-01-01",
            # "https://start-api.npo.nl/page/catalogue?pageSize={}".format(self.__pageSize),
            content_type=contenttype.TVSHOWS
        )
        extra.complete = True
        extra.dontGroup = True
        extra.description = "Volledige programma lijst van NPO Start."
        extra.HttpHeaders = self.__jsonApiKeyHeader
        # API Key from here: https://packagist.org/packages/kro-ncrv/npoplayer?q=&p=0&hFR%5Btype%5D%5B0%5D=concrete5-package
        # items.append(extra)

        # extra = FolderItem(
        #     LanguageHelper.get_localized_string(LanguageHelper.Genres),
        #     "https://www.npostart.nl/programmas",
        #     content_type=contenttype.VIDEOS)
        # extra.complete = True
        # extra.dontGroup = True
        # items.append(extra)

        recent = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.Recent), "https://npo.nl/start/api/domain/guide-channels",
            content_type=contenttype.VIDEOS)
        recent.complete = True
        recent.dontGroup = True
        recent.metaData["retrospect:parser"] = "recent"
        recent.cacheToDisc = False
        items.append(recent)

        return data, items

    def create_profile_item(self, result_set: dict) -> Optional[MediaItem]:
        """ Creates a new MediaItem for a the profiles in NPO Start.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict[str,str|None] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        profile_name = result_set.get("name")
        item = FolderItem(profile_name, "#list_profile", mediatype.FOLDER, contenttype.NONE)
        item.thumb = result_set.get("thumburl", None)
        item.description = result_set.get("description", "")
        item.complete = True
        item.metaData["id"] = result_set["guid"]
        return item

    def switch_profile(self, data: Union[str, JsonHelper]) -> Tuple[Union[str, JsonHelper], List[MediaItem]]:
        """ Switches to the selected profile.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        profile_id = self.parentItem.metaData.get("id", None)
        if not profile_id:
            return data, items

        xsrf_token = self.__get_xsrf_token()
        profile_data = {
            "csrfToken": xsrf_token,
            "data": {"profile": {"guid": "0dba0d55-640e-4e70-9b00-1449816f13cf"}}
        }
        headers = {"x-xsrf-token": xsrf_token}
        response = UriHandler.open(
            "https://npo.nl/start/api/auth/session",
            json=profile_data, additional_headers=headers)

        profile_content_url = (
            f"https://npo.nl/start/api/domain/recommendation-layout?"
            f"page=home&"
            #f"partyId=1%3Alp08hirt%3A2c8e90d7048a467babf108e0146ad52d&"
            f"profileGuid={profile_id}&"
            # f"subscriptionType=free"
        )

        data = UriHandler.open(profile_content_url)

        # data = JsonHelper(data)
        # t = data.get_value("collections")
        # s = [tt["key"] + ":" + tt["type"] for tt in t]
        # v = ", ".join(s)
        return data, items

    def create_profile_content_item(self, result_set: Dict[str, str]) -> Union[MediaItem, List[MediaItem], None]:
        profile_id = self.parentItem.metaData["id"]
        folder_key = result_set["key"]
        url = (
            f"https://npo.nl/start/api/domain/recommendation-collection?"
            f"key={folder_key}&"
            # f"partyId=1%3Alp08hirt%3A2c8e90d7048a467babf108e0146ad52d&"
            f"profileGuid={profile_id}&"
            # f"subscriptionType=free"
        )
        title_key = folder_key.rsplit("-", 2)[0]
        title_id = self.__collection_names.get(title_key, None)
        if not title_id:
            return None
        title = LanguageHelper.get_localized_string(title_id)

        list_type = result_set["type"].lower()
        if list_type == "program":
            result = FolderItem(title, url, content_type=contenttype.EPISODES, media_type=mediatype.TVSHOW)
            result.metaData["retrospect:parser"] = "collection-with-videos"
        elif list_type == "series":
            result = FolderItem(title, url, content_type=contenttype.TVSHOWS)
            result.metaData["retrospect:parser"] = "collection-with-series"
        else:
            Logger.warning(f"Missing list type: {list_type}")
            return None

        return result

    # noinspection PyUnusedLocal
    def check_for_single_season(self, data: JsonHelper, items: List[MediaItem]) -> List[MediaItem]:
        if len(items) == 1:
            # Retry with just this url.
            self.parentItem.url = items[0].url
            return self.process_folder_list(self.parentItem)

        # Not the perfect way as we don't know for sure if the seasonkey is the right value
        # to sort by.
        # def season_index(item: MediaItem):
        #     return int(item.metaData.get("seasonKey", 0))
        #
        # items.sort(key=season_index)
        # last_season = items.pop()
        # season_items = self.process_folder_list(last_season)
        # return items + season_items

        # If not seasons, or just one, fetch the episodes
        guid = self.parentItem.metaData.get("guid")
        if guid:
            url = f"https://npo.nl/start/api/domain/programs-by-series?seriesGuid={guid}&limit=20&sort=-firstBroadcastDate"
            recent_data = JsonHelper(UriHandler.open(url))
            for result_set in recent_data.get_value():
                item = self.create_api_episode_item(result_set)
                if item:
                    items.append(item)

        return items

    def create_api_program_item(self, result_set: dict) -> Optional[MediaItem]:
        title = result_set["title"]
        slug = result_set["slug"]
        item_type = result_set["type"]
        guid = result_set["guid"]

        # timebound_daily, timeless_series
        if item_type and item_type.endswith("series"):
            # Series go by season
            url = f"https://npo.nl/start/api/domain/series-seasons?slug={slug}&type={item_type}"
        else:
            # The dailies not.
            url = f"https://npo.nl/start/api/domain/programs-by-series?seriesGuid={guid}&limit=20&sort=-firstBroadcastDate"

        item = FolderItem(title, url, content_type=contenttype.EPISODES)
        # Store the series GUID as we need it later one.
        item.metaData["guid"] = guid
        if "images" in result_set and result_set["images"]:
            image_data = result_set["images"][0]
            item.set_artwork(thumb=image_data["url"], fanart=image_data["url"])
            item.description = image_data.get("description")
        return item

    def create_api_category_item(self, result_set: dict) -> Optional[MediaItem]:
        title = result_set["title"]
        slug = result_set["slug"]

        url = f"https://npo.nl/start/api/domain/page-layout?slug={slug}"
        item = FolderItem(title, url, content_type=contenttype.TVSHOWS)

        if "images" in result_set and result_set["images"]:
            image_data = result_set["images"][0]
            item.set_artwork(thumb=image_data["url"], fanart=image_data["url"])
            item.description = image_data.get("description")
        return item

    def create_api_page_layout(self, result_set: dict) -> Optional[MediaItem]:
        guid = result_set["guid"]
        page_type = result_set["type"]
        url = f"https://npo.nl/start/api/domain/page-collection?type={page_type.lower()}&guid={guid}"

        info = UriHandler.open(url)
        info = JsonHelper(info)
        title = info.get_value("title")

        if page_type == "SERIES":
            content_type = contenttype.TVSHOWS
        elif page_type == "PROGRAM":
            content_type = contenttype.EPISODES
        else:
            Logger.error(f"Missing for page type: {page_type}")
            return None

        item = FolderItem(title, url, content_type=content_type)
        return item

    def create_api_season_item(self, result_set: dict) -> Optional[MediaItem]:
        guid = result_set["guid"]
        label = result_set.get("label")
        title = f"{LanguageHelper.get_localized_string(LanguageHelper.SeasonId)} {result_set['seasonKey']}"
        if label:
            title = f"{title} - {label}"
        url = f"https://npo.nl/start/api/domain/programs-by-season?guid={guid}"
        item = FolderItem(title, url, content_type=contenttype.EPISODES,
                          media_type=mediatype.FOLDER)
        item.description = result_set.get("synopsis")
        item.metaData["seasonKey"] = result_set["seasonKey"]

        if "images" in result_set and result_set["images"]:
            image_data = result_set["images"][0]
            item.set_artwork(thumb=image_data["url"], fanart=image_data["url"])
        return item

    def create_api_episode_item_with_data(self, result_set: dict) -> Optional[MediaItem]:
        if "series" not in result_set:
            Logger.warning("Cannot create episode with show info without a show.")
            return None

        return self.create_api_episode_item(result_set, True)

    def create_api_episode_item(self, result_set: dict, show_info: bool = False) -> (
            Optional)[MediaItem]:
        title = result_set["title"]
        poms = result_set["productId"]
        serie_info = result_set.get("series") or {}

        if show_info and result_set["series"]:
            show_title = result_set["series"]["title"]
            if show_title:
                title = f"{show_title} - {title}"

        item = MediaItem(title, poms, media_type=mediatype.EPISODE)

        if "images" in result_set and result_set["images"]:
            image_data = result_set["images"][0]
            item.set_artwork(thumb=image_data["url"])

        item.description = (result_set.get("synopsis") or {}).get("long")
        item.set_info_label(MediaItem.LabelDuration, result_set.get("durationInSeconds", 0))

        # 'firstBroadcastDate'
        if result_set.get("firstBroadcastDate"):
            date_time = DateHelper.get_date_from_posix(result_set["firstBroadcastDate"],
                                                       tz=pytz.UTC)
            date_time = date_time.astimezone(self.__timezone)
            item.set_date(date_time.year, date_time.month, date_time.day, date_time.hour,
                          date_time.minute, date_time.second)

            serie_slug = serie_info.get("slug", "")
            if serie_slug in ("nos-journaal", "nos-journaal-met-gebarentaal"):
                item.name = f"{item.name} {date_time.hour:02d}:{round(date_time.minute, -1):02d}"

        if "restrictions" in result_set:
            for restriction in result_set["restrictions"]:
                subscription = restriction.get("subscriptionType", "free")
                has_stream = restriction.get("isStreamReady", False)
                if subscription == "free" and has_stream:
                    # Check if the 'till' date was in the past
                    till_stamp = restriction.get("available", {}).get("till", 0) or 0
                    till = DateHelper.get_date_from_posix(till_stamp, tz=pytz.UTC)
                    if till_stamp and till < datetime.datetime.now(tz=pytz.UTC):
                        item.isPaid = True
                        # Due to a bug in the NPO API, this content could be viewed for free.
                        # for now we just don't show it.
                        if not self.__has_premium():
                            return None
                        else:
                            break
                    item.isPaid = False
                    # Always stop after a "free"
                    break
                if subscription == "premium":
                    item.isPaid = True

        episode_number = result_set.get("programKey")
        season_number = (result_set.get("season") or {}).get("seasonKey")
        show_type = serie_info.get("type")
        if episode_number and season_number and show_type.endswith("series"):
            item.set_season_info(season_number, episode_number)

        return item

    # noinspection PyUnusedLocal
    def create_api_live_tv(self, result_set: dict, show_info: bool = False) -> Optional[MediaItem]:
        """ Creates a MediaItem for a live item of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        name = result_set["title"]
        guid = result_set["guid"]
        poms = result_set["externalId"]
        url = f"https://npo.nl/start/live?channel={name}"

        item = MediaItem(name, url, media_type=mediatype.VIDEO)
        item.metaData["poms"] = poms
        item.metaData["live_pid"] = poms
        # Store the series GUID as we need it later.
        item.metaData["guid"] = guid
        item.isLive = True
        item.isGeoLocked = True

        item.complete = False
        item.isLive = True
        return item

    def create_epg_days(self, data: Union[str, JsonHelper]) -> Tuple[Union[str, JsonHelper], List[MediaItem]]:
        items = []
        data = JsonHelper(data)
        channels = {}
        for channel in data.get_value():
            title = channel["title"]
            guid = channel["guid"]
            if title not in ["NPO1", "NPO2", "NPO3"]:
                continue
            channels[guid] = title

        today = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(self.__timezone)
        days = LanguageHelper.get_days_list()
        for i in range(0, 7, 1):
            air_date = today - datetime.timedelta(i)
            Logger.trace("Adding item for: %s", air_date)

            # Determine a nice display date
            day = days[air_date.weekday()]
            if i == 0:
                day = LanguageHelper.get_localized_string(LanguageHelper.Today)
            elif i == 1:
                day = LanguageHelper.get_localized_string(LanguageHelper.Yesterday)
            # elif i == 2:
            #     day = LanguageHelper.get_localized_string(LanguageHelper.DayBeforeYesterday)
            title = "%04d-%02d-%02d - %s" % (air_date.year, air_date.month, air_date.day, day)

            extra = FolderItem(title, "#recentday", content_type=contenttype.EPISODES)
            extra.complete = True
            extra.dontGroup = True
            extra.metaData["date"] = f"{air_date.day:02}-{air_date.month:02}-{air_date.year}"
            extra.metaData["channels"] = channels
            extra.set_date(air_date.year, air_date.month, air_date.day, text="")
            items.append(extra)

        return data, items

    # noinspection PyUnusedLocal
    def load_all_epg_channels(self, data: Union[str, JsonHelper]) -> Tuple[Union[str, JsonHelper], List[MediaItem]]:
        channels = self.parentItem.metaData["channels"]
        date = self.parentItem.metaData["date"]

        epg_data = None
        for guid, title in channels.items():

            data = JsonHelper(UriHandler.open(f"https://npo.nl/start/api/domain/guide-channel?guid={guid}&date={date}"))
            for item in data.json:
                item["channel"] = title
            if not epg_data:
                epg_data = data
            else:
                epg_data.json += data.json

        return epg_data, []

    def create_api_epg_item(self, result_set: dict) -> Optional[MediaItem]:
        Logger.debug(result_set)
        series_slug = (result_set.get("series") or {}).get("slug")
        program_guid = (result_set.get("program") or {}).get("guid")
        season_slug = None

        if not series_slug and program_guid:
            # It is a single video not belonging to a series.
            program_slug = result_set["program"]["slug"]
            url = f"https://npo.nl/start/video/{program_slug}"
        elif series_slug and program_guid:
            url = f"https://npo.nl/start/api/domain/series-seasons?slug={series_slug}"
            season_slug = result_set["season"]["slug"]
        else:
            return None

        name = result_set["title"]
        start = result_set["programStart"]
        channel = result_set["channel"]

        date_stamp = DateHelper.get_date_from_posix(start, tz=self.__timezone)
        # Check not needed. Programs in the future that are unavailable don't have a result_set.program property, which is already checked above.
        # https://github.com/retrospect-addon/plugin.video.retrospect/pull/1754#issuecomment-1884550951
        # if date_stamp > datetime.datetime.now(tz=pytz.UTC):
        #     return None

        item = MediaItem(f"{date_stamp.hour:02d}:{date_stamp.minute:02d} - {channel} - {name}", url, media_type=mediatype.EPISODE)
        if season_slug and program_guid:
            item.metaData = {
                "season_slug": season_slug,
                "program_guid": program_guid
            }
        item.set_date(date_stamp.year, date_stamp.month, date_stamp.day, date_stamp.hour, date_stamp.minute, date_stamp.second)

        duration = result_set.get("durationInSeconds")
        if duration:
            item.set_info_label(MediaItem.LabelDuration, duration)

        if "images" in result_set and result_set["images"]:
            image_data = result_set["images"][0]
            item.set_artwork(thumb=image_data["url"], fanart=image_data["url"])
            item.description = image_data.get("description")
        return item

    def update_single_video(self, item: MediaItem) -> MediaItem:
        data = UriHandler.open(item.url)
        whatson_info = Regexer.do_regex(r'"productId"\W+"([^"]+)"', data)
        if not whatson_info:
            # Retry as with a login it might fail
            data = UriHandler.open(item.url)
            whatson_info = Regexer.do_regex(r'"productId"\W+"([^"]+)"', data)

        whatson_id = whatson_info[0]
        return self.__update_video_item(item, whatson_id)

    def update_epg_series_item(self, item: MediaItem) -> MediaItem:
        # Go from season slug, show slug & program guid ->
        # ?? https://npo.nl/start/api/domain/series-detail?slug=boer-zoekt-vrouw
        # ?? Fetch the type
        # ?? https://npo.nl/start/api/domain/series-seasons?slug=boer-zoekt-vrouw&type=timebound_series
        # https://npo.nl/start/api/domain/series-seasons?slug=boer-zoekt-vrouw
        # Find the season guid for the season slug
        # https://npo.nl/start/api/domain/programs-by-season?guid=605eac92-8fb1-493c-a251-e572d4b7127f&type=timebound_series
        # From there with the video guid, find the POMS

        season_slug = item.metaData["season_slug"]
        season_info = UriHandler.open(item.url)
        season_info = JsonHelper(season_info)
        season = [s for s in season_info.json if s["slug"] == season_slug][0]
        season_guid = season["guid"]

        program_guid = item.metaData["program_guid"]
        season_content = UriHandler.open(f"https://npo.nl/start/api/domain/programs-by-season?guid={season_guid}")
        season_content = JsonHelper(season_content)
        program = [p for p in season_content.json if p["guid"] == program_guid][0]

        product_id = program["productId"]

        return self.__update_video_item(item, product_id)

    # noinspection PyUnusedLocal
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

        shows_url = "https://npo.nl/start/api/domain/search-results?searchType=series&searchQuery=%s&subscriptionType=anonymous"
        videos_url = "https://npo.nl/start/api/domain/search-results?searchType=broadcasts&searchQuery=%s&subscriptionType=anonymous"

        items = []
        needle = HtmlEntityHelper.url_encode(needle)
        search_url = shows_url % (needle, )
        temp = MediaItem("Search", search_url, mediatype.FOLDER)
        items += self.process_folder_list(temp)

        search_url = videos_url % (needle, )
        temp = MediaItem("Search", search_url, mediatype.FOLDER)
        items += self.process_folder_list(temp)
        return items

    # def process_old_franchise_page(self, data):
    #     """ Prepares the main folder for a show.
    #
    #     Lists the most recent episodes as shown on the website and app, and adds
    #     folders for "Extra's" and "Fragmenten".
    #
    #     :param str data: The retrieve data that was loaded for the current item and URL.
    #
    #     :return: A tuple of the data and a list of MediaItems that were generated.
    #     :rtype: tuple[str|JsonHelper,list[MediaItem]]
    #
    #     """
    #
    #     items = []
    #     has_more_episodes = False
    #     has_extras = False
    #     has_fragments = False
    #
    #     data = JsonHelper(data)
    #     # Create a list of episodes for the next processing step
    #     data.json["items"] = []
    #
    #     # Parse the franchise JSON to find out which components are available
    #     for component in data.get_value("components"):
    #         Logger.debug(list(component.keys()))
    #         if component["id"] in ("lane-last-published", "grid-episodes"):
    #             # The most recent episodes, or the latest season
    #             data.json["items"] += component["data"]["items"]
    #             if "filter" in component and component["filter"] is not None:
    #                 # There is a season filter, so there may be more episodes
    #                 has_more_episodes = True
    #             if component["data"]["_links"] is not None and "next" in component["data"][
    #                 "_links"]:
    #                 # There is a link to the next page with more episodes
    #                 has_more_episodes = True
    #         elif component["id"] == "grid-clips":
    #             # There is an "Extra's" tab
    #             has_extras = True
    #         elif component["id"] == "grid-fragments":
    #             # There is a "Fragmenten" tab
    #             has_fragments = True
    #
    #     # Obtain the POM ID for this show
    #     pom = Regexer.do_regex(r'https://start-api.npo.nl/page/franchise/([^/?]+)',
    #                            self.parentItem.url)[0]
    #
    #     # Generate folders for episodes, extras, and fragments
    #     links = [(LanguageHelper.AllEpisodes, "episodes", has_more_episodes),
    #              (LanguageHelper.Extras, "clips", has_extras),
    #              (LanguageHelper.Fragments, "fragments", has_fragments)]
    #
    #     for (title, path, available) in links:
    #         if available:
    #             url = 'https://start-api.npo.nl/media/series/%s/%s?pageSize=50' % (pom, path)
    #             Logger.debug("Adding link to %s: %s", path, url)
    #             title = LanguageHelper.get_localized_string(title)
    #             item = FolderItem("\a.: %s :." % title, url, content_type=contenttype.EPISODES)
    #             item.complete = True
    #             item.HttpHeaders = self.__jsonApiKeyHeader
    #             item.dontGroup = True
    #             items.append(item)
    #
    #     return data, items
    #
    # def extract_old_api_pages(self, data):
    #     """ Extracts the JSON tiles data from the HTML.
    #
    #     :param str data: The retrieve data that was loaded for the current item and URL.
    #
    #     :return: A tuple of the data and a list of MediaItems that were generated.
    #     :rtype: tuple[str|JsonHelper,list[MediaItem]]
    #
    #     """
    #     items = []
    #
    #     data = JsonHelper(data)
    #     next_url = data.get_value("_links", "next", "href")
    #     Logger.debug("Retrieving a total of %s items", data.get_value("total"))
    #
    #     if not next_url:
    #         return data, items
    #
    #     # We will just try to download all items.
    #     for _ in range(0, self.__max_page_count - 1):
    #         page_data = UriHandler.open(next_url, additional_headers=self.parentItem.HttpHeaders)
    #         page_json = JsonHelper(page_data)
    #         page_items = page_json.get_value("items")
    #         if page_items:
    #             data.json["items"] += page_items
    #         next_url = page_json.get_value("_links", "next", "href")
    #         if not next_url:
    #             break
    #
    #     if next_url:
    #         next_title = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
    #         item = FolderItem("\b.: {} :.".format(next_title), next_url,
    #                           content_type=contenttype.EPISODES)
    #         item.complete = True
    #         item.HttpHeaders = self.__jsonApiKeyHeader
    #         item.dontGroup = True
    #         items.append(item)
    #
    #     return data, items
    #
    # def create_old_api_video_item(self, result_set, for_epg=False):
    #     """ Creates a MediaItem of type 'video' using the result_set from the API calls:
    #
    #     - https://start-api.npo.nl/media/series/{POM_ID}/episodes
    #     - https://start-api.npo.nl/page/franchise/{POM_ID}
    #
    #     This method creates a new MediaItem from the Regular Expression or Json
    #     results <result_set>. The method should be implemented by derived classes
    #     and are specific to the channel.
    #
    #     If the item is completely processed an no further data needs to be fetched
    #     the self.complete property should be set to True. If not set to True, the
    #     self.update_video_item method is called if the item is focussed or selected
    #     for playback.
    #
    #     :param dict[str,Any] result_set:    The result_set of the self.episodeItemRegex
    #     :param bool for_epg:                Use this item in an EPG listing
    #
    #     :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
    #     :rtype: MediaItem|None
    #
    #     """
    #
    #     Logger.trace(result_set)
    #
    #     name = self.__get_name_for_api_video(result_set, for_epg)
    #     description = result_set.get('descriptionLong')
    #     if not description:
    #         description = result_set.get('description')
    #     video_id = result_set['id']
    #     if video_id is None:
    #         return None
    #
    #     item = MediaItem(name, video_id, media_type=mediatype.EPISODE)
    #     item.description = description
    #
    #     season = result_set.get("seasonNumber")
    #     episode = result_set.get("episodeNumber")
    #
    #     # Check for seasons but don't add then for EPG
    #     if bool(season) and bool(episode) and season < 100 and not for_epg:
    #         item.set_season_info(season, episode)
    #         # TODO: setting it now is to messy. Perhaps we should make it configurable?
    #         # item.name = "s{0:02d}e{1:02d} - {2}".format(season, episode, item.name)
    #
    #     date_format = "%Y-%m-%dT%H:%M:%SZ"
    #     date = result_set.get('broadcastDate')
    #     if date:
    #         # The dates are in UTC, so we need to calculate the actual
    #         # time and take the DST in consideration for each item.
    #         date_time = DateHelper.get_datetime_from_string(
    #             date, date_format=date_format, time_zone="UTC")
    #         date_time = date_time.astimezone(self.__timezone)
    #
    #         if for_epg:
    #             item.name = "{:02}:{:02} - {}".format(
    #                 date_time.hour, date_time.minute, item.name)
    #         else:
    #             item.set_date(date_time.year, date_time.month, date_time.day,
    #                           date_time.hour, date_time.minute, date_time.second)
    #
    #         # For #933 we check for NOS Journaal
    #         if item.name == "NOS Journaal":
    #             item.name = "{2} - {0:02d}:{1:02d}".format(date_time.hour, date_time.minute,
    #                                                        item.name)
    #
    #     item.isPaid = result_set.get("isOnlyOnNpoPlus", False)
    #     availability = result_set.get("availability")
    #     if not item.isPaid and availability and availability["to"] and availability["to"] != \
    #             availability["from"]:
    #         to_date = DateHelper.get_date_from_string(availability["to"], date_format=date_format)
    #         to_datetime = datetime.datetime(*to_date[:6])
    #         item.isPaid = to_datetime < datetime.datetime.now()
    #
    #     item.set_info_label("duration", result_set['duration'])
    #
    #     images = result_set["images"]
    #     for image_type, image_data in images.items():
    #         if image_type == "original" and "original" in image_data["formats"]:
    #             continue
    #             # No fanart for now.
    #             # item.fanart = image_data["formats"]["original"]["source"]
    #         elif image_type == "grid.tile":
    #             item.thumb = image_data["formats"]["web"]["source"]
    #
    #     region_restrictions = result_set.get('regionRestrictions', [])
    #     # The PLUSVOD:EU is not a regional restriction as it seems (See #1392)
    #     item.isGeoLocked = any([r for r in region_restrictions if r != "PLUSVOD:EU"])
    #     return item

    def create_live_radio(self, result_set: dict) -> Optional[MediaItem]:
        """ Creates a MediaItem for a live radio item of type 'video' using the
        result_set from the regex.

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

        """

        Logger.trace("Content = %s", result_set)
        # url = f"{result_set['url']}/live"
        url = result_set["url"].rstrip("/")
        if "blend" in url:
            return None
        title = result_set["title"]
        logo = result_set["thumb"]
        item = MediaItem(title, url, media_type=mediatype.VIDEO)
        item.isLive = True
        item.complete = False
        item.thumb = logo
        item.isLive = True
        item.metaData["retrospect:parser"] = "liveRadio"
        return item

    def update_live_radio(self, item: MediaItem) -> MediaItem:
        # First fetch the Javascript data file
        www_data = UriHandler.open(item.url)
        js_data_url = Regexer.do_regex(r'(_next/static/chunks/pages/_app[^"]+.js)', www_data)[0]
        js_data = UriHandler.open(f"{item.url}/{js_data_url}")

        # Then fetch the slug
        # slug = Regexer.do_regex(r'slug\W*:\W*"([^"]+)"', js_data)[0]
        slug = Regexer.do_regex(r'var\W*r\W*=\W*"(npo[^"]+)"', js_data)[0]

        # Get the channel info and media info.
        channel_json = JsonHelper(UriHandler.open(f"{item.url}/api/miniplayer/info?channel={slug}"))
        media_info = channel_json.get_value("data", "coreChannels", "data", 0, "liveVideo")
        if not media_info:
            media_info = channel_json.get_value("data", "coreChannels", "data", 0, "liveAudio")
        token_url = media_info["tokenUrl"]
        token_json = JsonHelper(UriHandler.open(token_url))

        mid = token_json.get_value("mid")
        return self.__update_video_item(item, mid, fetch_subtitles=False)

    def update_video_item(self, item: MediaItem) -> MediaItem:
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

        if "/radio/" in item.url or "/live/" in item.url or "/LI_" in item.url:
            Logger.info("Updating Live item: %s", item.url)
            return self.update_video_item_live(item)

        whatson_id = item.url
        return self.__update_video_item(item, whatson_id)

    def update_video_item_live(self, item: MediaItem) -> MediaItem:
        """ Updates an existing Live MediaItem with more data.

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

        Logger.debug('Starting update_video_item: %s', item.name)
        if "live_pid" in item.metaData:
            return self.__update_video_item(item, item.metaData["live_pid"], False)

        # we need to determine radio or live tv
        Logger.debug("Fetching live stream data from item url: %s", item.url)
        html_data = UriHandler.open(item.url)

        mp3_urls = Regexer.do_regex("""data-streams='{"url":"([^"]+)","codec":"[^"]+"}'""",
                                    html_data)
        if len(mp3_urls) > 0:
            Logger.debug("Found MP3 URL")
            item.add_stream(mp3_urls[0], 192)
        else:
            Logger.debug("Finding the actual metadata url from %s", item.url)
            # NPO3 normal stream had wrong subs
            if "npo-3" in item.url and False:
                # NPO3 has apparently switched the normal and hearing impaired streams?
                json_urls = Regexer.do_regex(
                    '<div class="video-player-container"[^>]+data-alt-prid="([^"]+)"', html_data)
            else:
                json_urls = Regexer.do_regex('<npo-player[^-][^>]*media-id="([^"]+)"', html_data)

            for episode_id in json_urls:
                return self.__update_video_item(item, episode_id, False)

            Logger.warning("Cannot update live item: %s", item)
            return item

        item.complete = True
        return item

    def create_iptv_streams(self, parameter_parser):
        """ Fetch the available live channels using guide-channels endpoint and format them into JSON-STREAMS

        :param ActionParser parameter_parser: a ActionParser object to is used to parse and
                                                   create urls

        :return: Formatted stations
        :rtype: list
        """
        channel_data = JsonHelper(UriHandler.open(f"https://npo.nl/start/api/domain/guide-channels"))
        parent_item = MediaItem("Live", "https://www.npostart.nl/live", media_type=mediatype.FOLDER)
        items = []
        iptv_streams = []

        logo_sources = {
            "NPO1": TextureHandler.instance().get_texture_uri(self, "npo1.png"),
            "NPO2": TextureHandler.instance().get_texture_uri(self, "npo2.png"),
            "NPO3": TextureHandler.instance().get_texture_uri(self, "npo3.png"),
            "NPO1 Extra": TextureHandler.instance().get_texture_uri(self, "npo1extra.png"),
            "NPO2 Extra": TextureHandler.instance().get_texture_uri(self, "npo2extra.png"),
            "NPO Politiek en Nieuws": TextureHandler.instance().get_texture_uri(self, "npopolitiekennieuws.png")
        }
        
        for livestream in channel_data.json:
            item = self.create_api_live_tv(livestream)
            items.append(item)

            iptv_streams.append(dict(
                id=JsonHelper.get_from(livestream, "guid"),
                name=JsonHelper.get_from(livestream, "title"),
                logo=logo_sources[JsonHelper.get_from(livestream, "title")],
                group=self.channelName,
                stream=parameter_parser.create_action_url(self, action=action.PLAY_VIDEO, item=item,
                                                          store_id=parent_item.guid),
            ))
        
        parameter_parser.pickler.store_media_items(parent_item.guid, parent_item, items)
        return iptv_streams

    def create_iptv_epg(self, parameter_parser):
        """ Fetch the EPG using the EPG endpoint and format it into JSON-EPG

        :param ActionParser parameter_parser: a ActionParser object to is used to parse and
                                                   create urls

        :return: Formatted stations
        :rtype: dict
        """

        channel_data = JsonHelper(UriHandler.open(f"https://npo.nl/start/api/domain/guide-channels"))
        parent = MediaItem("EPG", "https://start-api.npo.nl/epg/", media_type=mediatype.FOLDER)
        iptv_epg = dict()
        media_items = []
        
        for livestream in channel_data.json:
            iptv_epg[livestream["guid"]] = []
            
            # Fetch 3 days in the past and in the future
            start = datetime.datetime.now() - datetime.timedelta(days=3)
            for i in range(0, 6, 1):
                air_date = start + datetime.timedelta(i)
                date = air_date.strftime("%d-%m-%Y")
                guid = livestream["guid"]
                guide_data = JsonHelper(UriHandler.open(f"https://npo.nl/start/api/domain/guide-channel?guid={guid}&date={date}"))
        
                for item in guide_data.json:
                    item["channel"] = livestream["title"]
                    media_item = self.create_api_epg_item(item)
                    iptv_epg_item = dict(
                        start=datetime.datetime.fromtimestamp(JsonHelper.get_from(item, "programStart"), datetime.timezone.utc).isoformat(),
                        stop=datetime.datetime.fromtimestamp(JsonHelper.get_from(item, "programEnd"), datetime.timezone.utc).isoformat(),
                        title=JsonHelper.get_from(item, "title"))
                    
                    if len(JsonHelper.get_from(item, "images")) > 0:
                        iptv_epg_item["image"] = JsonHelper.get_from(item, "images")[0].get("url")

                    if media_item is not None:
                        iptv_epg_item["stream"] = parameter_parser.create_action_url(
                            self, action=action.PLAY_VIDEO, item=media_item, store_id=parent.guid)
                        media_items.append(media_item)

                    iptv_epg[livestream["guid"]].append(iptv_epg_item)

        parameter_parser.pickler.store_media_items(parent.guid, parent, media_items)
        return iptv_epg

    def __has_premium(self) -> bool:
        if self.__has_premium_cache is None:
            if not self.loggedOn:
                self.log_on()

            data = UriHandler.open("https://npo.nl/start/api/auth/session")
            json = JsonHelper(data)
            subscriptions = json.get_value("subscription", fallback=None)
            self.__has_premium_cache = subscriptions is not None
            Logger.debug("Found subscriptions: %s", subscriptions)

        return self.__has_premium_cache

    def __update_video_item(self, item: MediaItem, episode_id: str, fetch_subtitles: bool = True) -> MediaItem:
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

        :param MediaItem item:          the original MediaItem that needs updating.
        :param str episode_id:          the ID of the episode.
        :param bool fetch_subtitles:    should we fetch the subtitles (not for live items).

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.trace("Using Generic update_video_item method")

        # get the subtitle
        if fetch_subtitles:
            sub_title_url = f"https://cdn.npoplayer.nl/subtitles/nl/{episode_id}.vtt"
            sub_title_path = subtitlehelper.SubtitleHelper.download_subtitle(
                sub_title_url, episode_id + ".nl.srt", format='srt')

            if sub_title_path:
                item.subtitle = sub_title_path

        if AddonSettings.use_adaptive_stream_add_on(with_encryption=True,
                                                    ignore_add_on_config=True):
            error = NpoStream.add_mpd_stream_from_npo(None, episode_id, item, live=item.isLive)
            if bool(error) and self.__has_premium():
                self.__log_on(force_log_off=True)
                error = NpoStream.add_mpd_stream_from_npo(None, episode_id, item, live=item.isLive)

            if bool(error):
                XbmcWrapper.show_dialog(
                    LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                    error)
                # We don't want more errors to show
                item.isPaid = False
                return item

            item.complete = True
        else:
            XbmcWrapper.show_dialog(
                LanguageHelper.get_localized_string(LanguageHelper.DrmTitle),
                LanguageHelper.get_localized_string(LanguageHelper.WidevineLeiaRequired))

        if item.isPaid and self.__has_premium():
            item.isPaid = False

        # registering playback - The issue is that is linked to a profile, which we did not configure
        # if self.loggedOn:
        #     Logger.debug("Registering this playback with NPO")
        #     xsrf_token, token = self.__get_xsrf_token()
        #     data = {
        #         "_token": token,
        #         "progress": 10
        #     }
        #     UriHandler.open(
        #         "https://www.npostart.nl/api/progress/VPWON_1267211",
        #         data=data, additional_headers={
        #             "X-Requested-With": "XMLHttpRequest",
        #             "X-XSRF-TOKEN": xsrf_token,
        #             "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
        #         }
        #     )
        return item

    def __ignore_cookie_law(self) -> None:
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        UriHandler.set_cookie(name='site_cookie_consent', value='yes', domain='.npo.nl')
        UriHandler.set_cookie(name='npo_cc', value='30', domain='.npo.nl')

        UriHandler.set_cookie(name='site_cookie_consent', value='yes', domain='.npostart.nl')
        UriHandler.set_cookie(name='npo_cc', value='30', domain='.npostart.nl')
        return

    def __get_xsrf_token(self) -> str:
        """ Retrieves a JSON Token and XSRF token

        :return: XSRF Token and JSON Token
        :rtype: tuple[str|None,str|None]
        """

        # Fetch a CSRF token
        data = UriHandler.open("https://npo.nl/start/api/auth/csrf", no_cache=True)
        csrf_token = JsonHelper(data).get_value("csrfToken")
        return csrf_token
