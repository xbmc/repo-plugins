# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import re
from typing import Union, List, Optional, Tuple, Dict

import pytz

from resources.lib import chn_class, contenttype, mediatype
from resources.lib.addonsettings import AddonSettings
from resources.lib.authentication.authenticator import Authenticator
from resources.lib.authentication.gigyahandler import GigyaHandler
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.parserdata import ParserData
from resources.lib.streams.mpd import Mpd
from resources.lib.textures import TextureHandler
from resources.lib.urihandler import UriHandler
from resources.lib.xbmcwrapper import XbmcWrapper


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "videolandnl-thumb.jpg"
        self.httpHeaders = {
            "X-Client-Release": "5.81.1",
            "X-Customer-Name": "rtlnl"
        }

        # setup the urls
        self.mainListUri = "https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/alias/home/layout?nbPages=1"
        # https://pc.middleware.videoland.bedrock.tech/6play/v2/platforms/m6group_web/services/videoland/programs?limit=999&offset=0&csa=tot_18_jaar&with=rights
        # https://pc.middleware.videoland.bedrock.tech/6play/v2/platforms/m6group_web/services/videoland/programs/first-letters?csa=tot_18_jaar

        self._add_data_parser(self.mainListUri, requires_logon=True, json=True,
                              name="Mainlist for Videoland",
                              preprocessor=self.add_others_and_check_correct_url,
                              parser=["blocks"], creator=self.create_mainlist_item)

        self._add_data_parsers([
            r"^https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/service/videoland_root/block/",
            r"^https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/program/\d+/block/"],
            match_type=ParserData.MatchRegex,
            name="Main processor that create content items (folders/videos) from blocks",
            json=True, requires_logon=True,
            postprocessor=self.postprocess_episodes,
            parser=["content", "items"], creator=self.create_content_item)

        self._add_data_parser(
            r"https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/program/\d+/layout",
            match_type=ParserData.MatchRegex, json=True, requires_logon=True,
            name="Parser for the main folder of a show show/program.",
            preprocessor=self.extract_program_id,
            parser=["blocks"], creator=self.create_program_item)

        self._add_data_parser(
            "https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/video/",
            requires_logon=True,
            name="Video updater", json=True, updater=self.update_video_item)

        self._add_data_parser("algolia.net", match_type=ParserData.MatchContains, json=True,
                              name="Search results",
                              parser=["results", 0, "hits"], creator=self.create_search_result)

        # Authentication
        handler = GigyaHandler(
            "videoland.com", "3_t2Z1dFrbWR-IjcC-Bod1kei6W91UKmeiu3dETVG5iKaY4ILBRzVsmgRHWWo0fqqd",
            "4_hRanGnYDFjdiZQfh-ghhhg", AddonSettings.get_client_id())
        self.__authenticator = Authenticator(handler)
        self.__jwt = None
        self.__uid = None
        self.__has_premium = False

        # ===============================================================================================================
        # non standard items
        self.__program_id = None
        self.__pages = 10
        self.__timezone = pytz.timezone("Europe/Amsterdam")

    def add_others_and_check_correct_url(self, data: str) -> Tuple[JsonHelper, List[MediaItem]]:
        items = []
        search = FolderItem(LanguageHelper.get_localized_string(LanguageHelper.Search),
                            "#searchSite", content_type=contenttype.TVSHOWS)
        items.append(search)

        extras: Dict[int, Tuple[str, str]] = {
            LanguageHelper.Recent: (
                "page_6599c70de291a2.86703456--6918fda7-49db-49d5-b7f3-1e4a5b6bfab3",
                contenttype.TVSHOWS),
            # Already a standard item
            # LanguageHelper.Popular: ("page_6599c70de291a2.86703456--47a90b2c-669e-453f-8e3d-07eebbe4d4d0_167", contenttype.TVSHOWS)
        }

        for lang_id, extra in extras.items():
            page_id, content_type = extra
            title = LanguageHelper.get_localized_string(lang_id)
            url = f"https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/service/videoland_root/block/{page_id}?nbPages={self.__pages}"
            item = FolderItem(title, url, content_type=content_type)
            items.append(item)

        # Now apparently the root of Videoland returns a different response every now and then. We
        # need to check that and retry otherwise.
        json_data = JsonHelper(data)
        blockes = json_data.get_value("blocks")
        if len(blockes) > 10:
            fallback = [
                {
                    "title": {"long": LanguageHelper.get_localized_string(LanguageHelper.Popular)},
                    "id": "page_65a44d889f7982.33185461--6d1869d5-ef61-461c-b634-226a1bb29c7d",
                    "featureId": "programs_by_segment"
                },
                {
                    "title": {"long": "Verder kijken"},
                    "id": "page_65a44d889f7982.33185461--2d2d40f6-8648-449a-9af4-a68162e6404a",
                    "featureId": "recommended_videos_by_user"
                },
                {
                    "title": {"long": "Dagelijkse programma's"},
                    "id": "page_65a453843fcbe7.99183628--35d0c383-60fb-49b0-9852-f05bfa1bfeaa_494",
                    "featureId": "programs_by_folder_by_service"
                },
                {
                    "title": {"long": "RTL 4"},
                    "id": "page_65a45411767f89.39008634--582cb0eb-3bd2-4d20-9732-8963d05d05ef",
                    "featureId": "videos_by_tags"
                },
                {
                    "title": {"long": "RTL 5"},
                    "id": "page_65a45411767f89.39008634--810d0bf5-2bd9-4e79-8ad1-af5700fa614c",
                    "featureId": "videos_by_tags"
                },
                {
                    "title": {"long": "RTL 7"},
                    "id": "page_65a45411767f89.39008634--2cf10b26-4064-49d3-9729-69011dba752e",
                    "featureId": "videos_by_tags"
                },
                {
                    "title": {"long": "RTL 8"},
                    "id": "page_65a45411767f89.39008634--7099088c-902b-4d43-817e-c6b0661f0ba5",
                    "featureId": "videos_by_tags"
                },
                {
                    "title": {"long": "RTL Z"},
                    "id": "page_65a45411767f89.39008634--a97c9122-7731-45be-a884-fd7cc1399250",
                    "featureId": "videos_by_tags"
                }
            ]
            for result_set in fallback:
                items.append(self.create_mainlist_item(result_set))

        return json_data, items

    def create_mainlist_item(self, result_set: Union[str, dict]) -> Union[
        MediaItem, List[MediaItem], None]:
        if not result_set["title"]:
            return None
        title = result_set["title"].get("long", result_set["title"].get("short"))
        page_id = result_set["id"]
        url = f"https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/service/videoland_root/block/{page_id}?nbPages={self.__pages}"

        feature_id = result_set["featureId"]
        item = FolderItem(title, url, content_type=contenttype.EPISODES if "videos" in feature_id else contenttype.TVSHOWS)

        if title.lower().startswith("rtl"):
            poster_slug = title.lower().replace(" ", "")
            poster = f"{poster_slug}-poster.png"
            poster_url = TextureHandler.instance().get_texture_uri(self, poster)
            item.poster = poster_url
        return item

    def create_content_item(self, result_set: Union[str, dict]) -> Union[
        MediaItem, List[MediaItem], None]:
        result_set: dict = result_set["itemContent"]

        title = result_set["title"]
        extra_title = result_set.get("extraTitle")
        if extra_title and title:
            title = f"{title} - {extra_title}"
        elif not title and extra_title:
            title = extra_title

        # What type is it
        action_info = result_set.get("action", {})
        action = action_info.get("label", "").lower()
        item_id = action_info["target"]["value_layout"]["id"]
        if "content" in action:
            url = f"https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/program/{item_id}/layout?nbPages={self.__pages}"
            item = FolderItem(title, url, content_type=contenttype.TVSHOWS)
        elif "collectie" in action:
            return None
        else:
            url = f"https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/video/{item_id}/layout?nbPages=2"
            item = MediaItem(title, url, media_type=mediatype.EPISODE)
        item.isPaid = action == "abonneren"

        def set_images(item: MediaItem, image_info: dict, set_fanart: bool, set_poster: bool):
            for ratio, image_id in image_info["idsByRatio"].items():
                image_url = f"https://images-fio.videoland.bedrock.tech/v2/images/{image_id}/raw"
                if ratio == "16:9":
                    item.thumb = image_url
                    if set_fanart:
                        item.fanart = image_url
                elif ratio == "2:3" and set_poster:
                    item.poster = image_url

        if "image" in result_set and item.is_playable:
            set_images(item, result_set["image"], set_fanart=False, set_poster=False)
        elif "secondaryImage" in result_set and not item.is_playable:
            set_images(item, result_set["secondaryImage"], set_fanart=True, set_poster=True)

        time_value = result_set["highlight"]
        if time_value and "min" in time_value:
            # 20min or 1uur20min
            hours = 0
            mins = 0
            if "uur" in time_value:
                hours, others = time_value.split("uur")
                mins, _ = others.split("min")
            elif "min" in time_value:
                mins, _ = time_value.split("min")
            item.set_info_label(MediaItem.LabelDuration, 60 * int(hours) + int(mins))

        date_value = (result_set["details"] or "").lower()
        if date_value:
            if date_value == "vandaag":
                # Vandaag
                time_stamp = datetime.datetime.now()
                item.set_date(time_stamp.year, time_stamp.month, time_stamp.day)
            elif date_value == "gisteren":
                # Gisteren
                time_stamp = datetime.datetime.now() - datetime.timedelta(days=1)
                item.set_date(time_stamp.year, time_stamp.month, time_stamp.day)
            elif date_value[-2].isnumeric():
                # 'Di 09 jan 24'
                weekday, day, month, year = date_value.split(" ")
                month = DateHelper.get_month_from_name(month, language="nl", short=True)
                year = 2000 + int(year)
                item.set_date(year, month, day)

        return item

    def extract_program_id(self, data: str) -> Tuple[Union[str, JsonHelper], List[MediaItem]]:
        json_data = JsonHelper(data)
        self.__program_id = json_data.get_value("entity", "id", fallback=None)
        return json_data, []

    def postprocess_episodes(self, data, items: List[MediaItem]) -> List[MediaItem]:
        # Season episodes can be named ["Aflevering 1", "Aflevering 2"] and so on, or ["Some episode name", "Another episode name", "Yet another episode name"]
        # without an episode number. Some episodes have a date, and some have no date, even within a single season.

        # All this messes up Kodi episode ordering by either date or name:
        # If no episodes have a date, Kodi orders by name, so "Another episode name" becomes the first episode instead of the second.
        # If some episodes have a date and some later ones don't, Kodi shows the later ones as the first episodes (mindate), followed by the ones with a date.

        # This postprocessing function fixes name ordering by adding an episode number in front of the title if the episodes
        # are not like "Aflevering 1", "Aflevering 2" and so on.
        # Episode names become ["01 Some episode name", "02 Another episode name", "03 Yet another episode name"].
        # Numbered episodes are fairly common, and in this case it is useful to achieve the right sort order by name.

        # This postprocessing function fixes date ordering by setting the date of an episode, if it has no date, to the date of the previous episode.
        # This is probably not the real broadcast date, but it at least fixes the order.
        if (len(items) > 1
            and data.json.get("featureId") == "videos_by_season_by_program"
            and all(item.media_type == mediatype.EPISODE and not re.match("[Aa]flevering \d+", item.name) for item in items)):
            date = ""
            for index, item in enumerate(items, start=1):
                item.name = f"{index:02} {item.name}"
                if (not item.has_date() and date):
                    previous_episode_date = DateHelper.get_datetime_from_string(date, "%Y-%m-%d")
                    item.set_date(previous_episode_date.year, previous_episode_date.month, previous_episode_date.day)
                    item.name = f"{item.name} [date unknown]"
                else:
                    date = item.get_date()

        return items

    def create_program_item(self, result_set: dict) -> Union[MediaItem, List[MediaItem], None]:
        if not result_set["title"]:
            return None

        title = result_set["title"].get("long", result_set["title"].get("short"))
        page_id = result_set["id"]
        url = f"https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/program/{self.__program_id}/block/{page_id}?nbPages=10&page=1"
        item = FolderItem(title, url, content_type=contenttype.EPISODES)

        # Preload them, but this makes paging difficult.
        # for sub_result in result_set["content"].get("items", []) or []:
        #     sub_item = self.create_content_item(sub_result)
        #     if sub_item:
        #         item.items.append(sub_item)

        return item

    def search_site(self, url=None):
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

        needle = XbmcWrapper.show_key_board()
        if not needle:
            return []

        url = "https://nhacvivxxk-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.14.2)%3B%20Browser"
        data = {"requests": [{
            "indexName": "videoland_prod_bedrock_layout_items_v2_rtlnl_main",
            "query": needle,
            "params": "hitsPerPage=50&facetFilters=%5B%5B%22metadata.item_type%3Aprogram%22%5D%2C%5B%22metadata.platforms_assets%3Am6group_web%22%5D%5D"
        }]}

        headers = {
            "X-Algolia-Api-Key": "6ef59fc6d78ac129339ab9c35edd41fa",
            "X-Algolia-Application-Id": "NHACVIVXXK"
        }
        search_item = FolderItem("search", url, content_type=contenttype.TVSHOWS)
        search_item.HttpHeaders = headers
        search_item.postJson = data
        return self.process_folder_list(search_item)

    def create_search_result(
            self, result_set: Union[str, dict]) -> Union[MediaItem, List[MediaItem], None]:
        last_activity_date = result_set["metadata"].get("last_activity_date")

        result_set = result_set["item"]
        item = self.create_content_item(result_set)
        if not item:
            return None

        if not item.has_date():
            # 2021-11-30 00:00:00
            time_stamp = DateHelper.get_date_from_string(last_activity_date, "%Y-%m-%d %H:%M:%S")
            item.set_date(*time_stamp[0:6])
        return item

    def filter_premium(self) -> Optional[bool]:
        filter_paid = int(self._get_setting("filter_premium", '0'))
        if not filter_paid:
            return None

        # 0: Default, 1: Show all, 2: Filter
        return filter_paid > 1

    def update_video_item(self, item: MediaItem) -> MediaItem:
        data = JsonHelper(UriHandler.open(item.url, additional_headers=self.httpHeaders))
        video_info = data.get_value("blocks", 0, "content", "items", 0, "itemContent", "video")
        video_id = video_info["id"]

        # Construct license info
        license_token_url = f"https://drm.videoland.bedrock.tech/v1/customers/rtlnl/platforms/m6group_web/services/videoland_catchup/users/{self.__uid}/videos/{video_id}/upfront-token"
        license_token = JsonHelper(
            UriHandler.open(license_token_url, additional_headers=self.httpHeaders)).get_value(
            "token")
        license_key = Mpd.get_license_key("https://lic.drmtoday.com/license-proxy-widevine/cenc/",
                                          key_headers={
                                              "x-dt-auth-token": license_token,
                                              "content-type": "application/octstream"
                                          }, json_filter="JBlicense")

        for asset in video_info["assets"]:
            quality = asset["video_quality"]
            url = asset["path"]
            video_type = asset["video_container"]
            # video_container = asset["container"]
            video_format = asset["format"]

            if quality == "hd":
                continue

            if video_type == "mpd" or video_format == "dashcenc" or video_format == "dash":
                stream = item.add_stream(url, 2000 if quality == "hd" else 1200)
                Mpd.set_input_stream_addon_input(stream, license_key=license_key)
                item.complete = True
            # elif video_type == "m3u8":
            #     # Not working in Kodi
            #     stream = item.add_stream(url, 2000 if quality == "hd" else 1200)
            #     item.complete = True
            #     M3u8.set_input_stream_addon_input(stream)
        return item

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

        # Always try to log on. If the username was changed to empty, we should clear the current
        # log in.
        username: Optional[str] = self._get_setting("videolandnl_username", value_for_none=None)
        if not username:
            XbmcWrapper.show_dialog(None, LanguageHelper.MissingCredentials)

        result = self.__authenticator.log_on(username=username, channel_guid=self.guid,
                                             setting_id="videolandnl_password")

        # Set some defaults
        self.__uid = result.uid
        self.__has_premium = result.has_premium
        self.__jwt = result.jwt if result.jwt else self.__authenticator.get_authentication_token()
        self.httpHeaders["Authorization"] = f"Bearer {self.__jwt}"
        return result.logged_on
