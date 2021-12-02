# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later

import uuid
import time
import datetime

from resources.lib import chn_class, mediatype
from resources.lib.mediaitem import MediaItem
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.subtitlehelper import SubtitleHelper
from resources.lib.parserdata import ParserData
from resources.lib.urihandler import UriHandler
from resources.lib.streams.m3u8 import M3u8
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.logger import Logger
from resources.lib.xbmcwrapper import XbmcWrapper


# noinspection PyIncorrectDocstring
class Channel(chn_class.Channel):

    def __init__(self, channel_info):
        """Initialisation of the class.

        Arguments:
        channel_info: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.mainListUri = "#programs"
        self.programPageSize = 100
        self.videoPageSize = 100
        self.swfUrl = "http://player.dplay.se/4.0.6/swf/AkamaiAdvancedFlowplayerProvider_v3.8.swf"
        self.subtitleKey = "subtitles_{0}_srt".format(self.language)
        self.channelSlugs = ()
        self.liveUrl = None
        self.recentUrl = None
        self.primaryChannelId = None
        self.baseUrlApi = "disco-api.dplay.{0}".format(self.language)

        if self.channelCode == "tv5json":
            self.noImage = "tv5seimage.png"
            self.baseUrl = "http://www.dplay.se/api/v2/ajax"
            # No live stream: self.liveUrl = "https://secure.dplay.se/secure/api/v2/user/authorization/stream/132040"
            self.primaryChannelId = 21

        elif self.channelCode == "tv9json":
            self.noImage = "tv9seimage.png"
            self.baseUrl = "http://www.dplay.se/api/v2/ajax"
            # No live stream: self.liveUrl = "https://secure.dplay.se/secure/api/v2/user/authorization/stream/132043"
            self.primaryChannelId = 26

        elif self.channelCode == "tv11json":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.se/api/v2/ajax"
            # No live stream: self.liveUrl = "https://secure.dplay.se/secure/api/v2/user/authorization/stream/132039"
            self.primaryChannelId = 22

        elif self.channelCode == "dplayse":
            self.noImage = "dplusimage.png"
            self.baseUrl = "http://www.dplay.se/api/v2/ajax"

        elif self.channelCode == "dplayno":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"

        elif self.channelCode == "tlcnorge":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"
            self.primaryChannelId = 15

        elif self.channelCode == "tvnorge":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"
            self.primaryChannelId = 28

        elif self.channelCode == "femnorge":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"
            self.primaryChannelId = 29

        elif self.channelCode == "maxnorge":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"
            self.primaryChannelId = 30

        elif self.channelCode == "voxnorge":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"
            self.primaryChannelId = 31

        elif self.channelCode == "animalplanetnorge":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"
            self.primaryChannelId = 35

        elif self.channelCode == "discoverynorge":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"
            self.primaryChannelId = 45

        elif self.channelCode == "discoverysciencenorge":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"
            self.primaryChannelId = 71

        elif self.channelCode == "discoveryworldnorge":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"
            self.primaryChannelId = 72

        elif self.channelCode == "investigationdiscoverynorge":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.no/api/v2/ajax"
            self.primaryChannelId = 73

        elif self.channelCode == "dplaydk":
            self.noImage = "dplayimage.png"
            self.baseUrl = "http://www.dplay.dk/api/v2/ajax"

        else:
            raise NotImplementedError("ChannelCode %s is not implemented" % (self.channelCode, ))

        if self.primaryChannelId:
            self.recentUrl = "https://{0}/content/videos?decorators=viewingHistory&" \
                             "include=images%2CprimaryChannel%2Cshow&" \
                             "filter%5BvideoType%5D=EPISODE&" \
                             "filter%5BprimaryChannel.id%5D={1}&" \
                             "page%5Bsize%5D={2}&" \
                             "sort=-publishStart"\
                .format(self.baseUrlApi, self.primaryChannelId, self.videoPageSize)

        #===========================================================================================
        # THIS CHANNEL DOES NOT SEEM TO WORK WITH PROXIES VERY WELL!
        #===========================================================================================
        self._add_data_parser("#programs", preprocessor=self.load_programs)
        # self._add_data_parser("https://secure.dplay.\w+/secure/api/v2/user/authorization/stream/",
        #                     matchType=ParserData.MatchRegex,
        #                     updater=self.update_channel_item)

        # Recent
        self._add_data_parser("/content/videos?decorators=viewingHistory&"
                              "include=images%2CprimaryChannel%2Cshow&filter%5BvideoType%5D=EPISODE&"
                              "filter%5BprimaryChannel.id%5D=",
                              name="Recent video items", json=True,
                              preprocessor=self.__get_images_from_meta_data,
                              match_type=ParserData.MatchContains,
                              parser=["data", ], creator=self.create_video_item_with_show_title)

        self._add_data_parser("/content/videos?decorators=viewingHistory&"
                              "include=images%2CprimaryChannel%2Cshow&filter%5BvideoType%5D=EPISODE&"
                              "filter%5BprimaryChannel.id%5D=",
                              name="Recent more pages", json=True,
                              preprocessor=self.__get_images_from_meta_data,
                              match_type=ParserData.MatchContains,
                              parser=["data", ], creator=self.create_video_item)

        # Search
        self._add_data_parser(r"http.+content/shows\?.+query=.+", match_type=ParserData.MatchRegex,
                              name="Search shows", json=True,
                              preprocessor=self.__get_images_from_meta_data,
                              parser=["data", ], creator=self.create_program_item)

        self._add_data_parser(r"http.+content/videos\?.+query=.+", match_type=ParserData.MatchRegex,
                              name="Search videos", json=True,
                              preprocessor=self.__get_images_from_meta_data,
                              parser=["data", ], creator=self.create_video_item_with_show_title)

        self._add_data_parser(r"http.+content/videos\?.+query=.+", match_type=ParserData.MatchRegex,
                              name="Search Pages", json=True,
                              parser=["meta", ], creator=self.create_page_item)

        # Others
        self._add_data_parser("*", json=True,
                              preprocessor=self.__get_images_from_meta_data,
                              parser=["data", ], creator=self.create_video_item,
                              updater=self.update_video_item)

        self._add_data_parser("*", json=True,
                              parser=["meta", ], creator=self.create_page_item)

        #===========================================================================================
        # non standard items
        api_cookie = UriHandler.get_cookie("st", self.baseUrlApi)
        api_cookie_set = AddonSettings.get_channel_setting(self, "api_cookie_set", store=LOCAL) or 0
        # The cookie is invalid earler then its expire date. Let's limit it at 30 days
        if time.time() - api_cookie_set > 30 * 24 * 3600:
            Logger.debug("Resetting api_cookie for %s", self)
            api_cookie = None

        if not api_cookie:
            guid = uuid.uuid4()
            guid = str(guid).replace("-", "")
            # https://disco-api.dplay.se/token?realm=dplayse&deviceId
            # =aa9ef0ed760df76d184b262d739299a75ccae7b67eec923fe3fcd861f97bcc7f&shortlived=true
            url = "https://{0}/token?realm=dplay{1}&deviceId={2}&shortlived=true"\
                .format(self.baseUrlApi, self.language, guid)
            JsonHelper(UriHandler.open(url))
            # noinspection PyTypeChecker
            AddonSettings.set_channel_setting(self, "api_cookie_set", time.time(), store=LOCAL)

        self.imageLookup = {}
        self.showLookup = {}
        self.__REQUIRES_LOGIN = "requires_login"
        self.__now = datetime.datetime.utcnow()
        self.__has_premium = False

        #===========================================================================================
        # Test cases:
        #  Arga snickaren : Has clips

        # ====================================== Actual channel setup STOPS here ===================
        return

    # noinspection PyUnusedLocal
    def load_programs(self, data):
        """ Performs pre-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        # fetch al pages
        p = 1
        url_format = "https://{0}/content/shows?" \
                     "include=images" \
                     "&page%5Bsize%5D=100&page%5Bnumber%5D={{0}}".format(self.baseUrlApi)
        # "include=images%2CprimaryChannel" \
        url = url_format.format(p)
        data = UriHandler.open(url)
        json = JsonHelper(data)
        pages = json.get_value("meta", "totalPages")
        programs = json.get_value("data") or []

        # extract the images
        self.__update_image_lookup(json)

        for p in range(2, pages + 1, 1):
            url = url_format.format(p)
            Logger.debug("Loading: %s", url)

            data = UriHandler.open(url)
            json = JsonHelper(data)
            programs += json.get_value("data") or []

            # extract the images
            self.__update_image_lookup(json)

        Logger.debug("Found a total of %s items over %s pages", len(programs), pages)

        for p in programs:
            item = self.create_program_item(p)
            if item is not None:
                items.append(item)

        if self.recentUrl:
            recent_text = LanguageHelper.get_localized_string(LanguageHelper.Recent)
            recent = MediaItem("\b.: {} :.".format(recent_text), self.recentUrl)
            recent.dontGroup = True
            items.append(recent)

        # live items
        if self.liveUrl:
            live = MediaItem("\b.: Live :.", self.liveUrl)
            live.media_type = mediatype.EPISODE
            live.dontGroup = True
            live.isGeoLocked = True
            live.isLive = True
            items.append(live)

        search = MediaItem("\a.: S&ouml;k :.", "searchSite")
        search.dontGroup = True
        items.append(search)

        return data, items

    def create_program_item(self, result_set):
        """ Creates a new MediaItem for a program.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        url_format = "https://{0}/content/videos?decorators=viewingHistory&" \
                     "include=images%2CprimaryChannel%2Cshow&" \
                     "filter%5BvideoType%5D=EPISODE%2CLIVE%2CFOLLOW_UP%2CSTANDALONE&" \
                     "filter%5Bshow.id%5D={{0}}&" \
                     "page%5Bsize%5D={1}&" \
                     "page%5Bnumber%5D=1&" \
                     "sort=-seasonNumber%2C-episodeNumber%2CvideoType%2CearliestPlayableStart".\
            format(self.baseUrlApi, self.videoPageSize)
        item = self.__create_generic_item(result_set, "show", url_format)
        if item is None:
            return None

        # set the date
        video_info = result_set["attributes"]  # type: dict
        if "newestEpisodePublishStart" in video_info:
            date = video_info["newestEpisodePublishStart"]
            date_part, time_part = date[0:-3].split("T")
            year, month, day = date_part.split("-")
            item.set_date(year, month, day)

        if item.thumb != self.noImage:
            item.fanart = item.thumb
        return item

    def create_page_item(self, result_set):
        """ Creates a MediaItem of type 'page' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'page'.
        :rtype: MediaItem|None

        """

        if "totalPages" not in result_set:
            return None

        Logger.debug("Starting create_page_item")

        # current page?
        page_uri_part = "page%5Bnumber%5D="
        if page_uri_part not in self.parentItem.url:
            page = 1
            url_format = "{0}&page%5Bnumber%5D={{0:d}}".format(self.parentItem.url)
        else:
            base_url, page_part = self.parentItem.url.rsplit(page_uri_part, 1)
            next_part = page_part.find("&")
            if next_part < 0:
                # end
                page = int(page_part)
                url_format = "{0}&page%5Bnumber%5D={{0:d}}".format(base_url)
            else:
                page = int(page_part[0:next_part])
                url_format = "{0}&page%5Bnumber%5D={{0:d}}&{1}".format(base_url, page_part[next_part:])

        max_pages = result_set.get("totalPages", 0)
        Logger.trace("Current Page: %d of %d (%s)", page, max_pages, self.parentItem.url)

        if page + 1 > max_pages:
            return None

        title = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
        url = url_format.format(page + 1)
        item = MediaItem(title, url)
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

        if self.primaryChannelId:
            shows_url = "https://{0}/content/shows?" \
                        "include=genres%%2Cimages%%2CprimaryChannel.images&" \
                        "filter%%5BprimaryChannel.id%%5D={1}&" \
                        "page%%5Bsize%%5D={2}&query=%s"\
                .format(self.baseUrlApi, self.primaryChannelId or "", self.programPageSize)

            videos_url = "https://{0}/content/videos?decorators=viewingHistory&" \
                         "include=images%%2CprimaryChannel%%2Cshow&" \
                         "filter%%5BprimaryChannel.id%%5D={1}&" \
                         "page%%5Bsize%%5D={2}&query=%s"\
                .format(self.baseUrlApi, self.primaryChannelId or "", self.videoPageSize)
        else:
            shows_url = "https://{0}/content/shows?" \
                        "include=genres%%2Cimages%%2CprimaryChannel.images&" \
                        "page%%5Bsize%%5D={1}&query=%s" \
                .format(self.baseUrlApi, self.programPageSize)

            videos_url = "https://{0}/content/videos?decorators=viewingHistory&" \
                         "include=images%%2CprimaryChannel%%2Cshow&" \
                         "page%%5Bsize%%5D={1}&query=%s" \
                .format(self.baseUrlApi, self.videoPageSize)

        needle = XbmcWrapper.show_key_board()
        if needle:
            Logger.debug("Searching for '%s'", needle)
            needle = HtmlEntityHelper.url_encode(needle)

            search_url = videos_url % (needle, )
            temp = MediaItem("Search", search_url)
            episodes = self.process_folder_list(temp)

            search_url = shows_url % (needle, )
            temp = MediaItem("Search", search_url)
            shows = self.process_folder_list(temp)
            return shows + episodes

        return []

    def create_video_item_with_show_title(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex. These items
        Include the show title in the episode name.

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
        return self.create_video_item(result_set, include_show_title=True)

    def create_video_item(self, result_set, include_show_title=False):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

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

        if not result_set:
            return None

        url_format = "https://{0}/playback/videoPlaybackInfo/{{0}}".format(self.baseUrlApi)
        item = self.__create_generic_item(result_set, "video", url_format)
        if item is None:
            return None

        item.media_type = mediatype.EPISODE
        video_info = result_set["attributes"]  # type: dict
        if "publishStart" in video_info or "airDate" in video_info:
            date = video_info.get("airDate", video_info["publishStart"])
            # 2018-03-20T20:00:00Z
            air_date = DateHelper.get_date_from_string(date,  date_format="%Y-%m-%dT%H:%M:%SZ")
            item.set_date(*air_date[0:6])
            if datetime.datetime(*air_date[0:6]) > datetime.datetime.now():
                item.isPaid = True

        episode = video_info.get("episodeNumber", 0)
        season = video_info.get("seasonNumber", 0)
        if episode > 0 and season > 0:
            item.name = "s{0:02d}e{1:02d} - {2}".format(season, episode, item.name)
            item.set_season_info(season, episode)

        if include_show_title:
            show_id = result_set["relationships"].get("show", {}).get("data", {}).get("id")
            if show_id:
                show = self.showLookup[show_id]
                item.name = "{0} - {1}".format(show, item.name)

        if "videoDuration" in video_info:
            item.set_info_label(MediaItem.LabelDuration, video_info["videoDuration"] / 1000)

        return item

    def update_channel_item(self, item):
        """ Updates an existing  Live channel MediaItem with more data.

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

        video_id = item.url.rsplit("/", 1)[-1]
        item.complete = self.__get_video_streams(video_id, item)
        return item

    def log_on(self, username=None, password=None):
        """ Logs on to a website, using an url.

        :param username:    If provided overrides the Kodi stored username
        :param password:    If provided overrides the Kodi stored username

        :return: indication if the login was successful.
        :rtype: bool

        First checks if the channel requires log on. If so and it's not already
        logged on, it should handle the log on. That part should be implemented
        by the specific channel.

        More arguments can be passed on, but must be handled by custom code.

        After a successful log on the self.loggedOn property is set to True and
        True is returned.

        """

        username = username or AddonSettings.get_setting("dplayse_username")
        if self.__is_already_logged_on(username):
            return True

        # Local import to not slow down any other stuff
        import os
        import binascii
        import pyaes
        import random

        now = int(time.time())
        b64_now = binascii.b2a_base64(str(now).encode()).decode().strip()

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
                     "(KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36"
        device_id = AddonSettings.get_client_id().replace("-", "")
        window_id = "{}|{}".format(
            binascii.hexlify(os.urandom(16)).decode(), binascii.hexlify(os.urandom(16)).decode())

        fe = ["DNT:unknown", "L:en-US", "D:24", "PR:1", "S:1920,975", "AS:1920,935", "TO:-120",
              "SS:true", "LS:true", "IDB:true", "B:false", "ODB:true", "CPUC:unknown",
              "PK:Win32", "CFP:990181251", "FR:false", "FOS:false", "FB:false", "JSF:Arial",
              "P:Chrome PDF Plugin", "T:0,false,false", "H:4", "SWF:false"]
        fs_murmur_hash = '48bf49e1796939175b0406859d00baec'

        data = [
            {"key": "api_type", "value": "js"},
            {"key": "p", "value": 1},                       # constant
            {"key": "f", "value": device_id},               # browser instance ID
            {"key": "n", "value": b64_now},                 # base64 encoding of time.now()
            {"key": "wh", "value": window_id},              # WindowHandle ID
            {"key": "fe", "value": fe},                     # browser properties
            {"key": "ife_hash", "value": fs_murmur_hash},   # hash of browser properties
            {"key": "cs", "value": 1},                      # canvas supported 0/1
            {"key": "jsbd", "value": "{\"HL\":41,\"NCE\":true,\"DMTO\":1,\"DOTO\":1}"}
        ]
        data_value = JsonHelper.dump(data)

        stamp = now - (now % (60 * 60 * 6))
        key_password = "{}{}".format(user_agent, stamp)

        salt_bytes = os.urandom(8)
        key_iv = self.__evp_kdf(key_password.encode(), salt_bytes, key_size=8, iv_size=4,
                                iterations=1, hash_algorithm="md5")
        key = key_iv["key"]
        iv = key_iv["iv"]

        encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv))
        encrypted = encrypter.feed(data_value)
        # Again, make a final call to flush any remaining bytes and strip padding
        encrypted += encrypter.feed()

        salt_hex = binascii.hexlify(salt_bytes)
        iv_hex = binascii.hexlify(iv)
        encrypted_b64 = binascii.b2a_base64(encrypted)
        bda = {
            "ct": encrypted_b64.decode(),
            "iv": iv_hex.decode(),
            "s": salt_hex.decode()
        }
        bda_str = JsonHelper.dump(bda)
        bda_base64 = binascii.b2a_base64(bda_str.encode())

        req_dict = {
            "bda": bda_base64.decode(),
            "public_key": "FE296399-FDEA-2EA2-8CD5-50F6E3157ECA",
            "site": "https://client-api.arkoselabs.com",
            "userbrowser": user_agent,
            "simulate_rate_limit": "0",
            "simulated": "0",
            "rnd": "{}".format(random.random())
        }

        req_data = ""
        for k, v in req_dict.items():
            req_data = "{}{}={}&".format(req_data, k, HtmlEntityHelper.url_encode(v))
        req_data = req_data.rstrip("&")

        arkose_data = UriHandler.open(
            "https://client-api.arkoselabs.com/fc/gt2/public_key/FE296399-FDEA-2EA2-8CD5-50F6E3157ECA",
            data=req_data, additional_headers={"user-agent": user_agent}, no_cache=True
        )
        arkose_json = JsonHelper(arkose_data)
        arkose_token = arkose_json.get_value("token")
        if "rid=" not in arkose_token:
            Logger.error("Error logging in. Invalid Arkose token.")
            return False
        Logger.debug("Succesfully required a login token from Arkose.")

        UriHandler.open(
            "https://disco-api.dplay.se/token?realm=dplayse&deviceId={}&shortlived=true".format(device_id),
            no_cache=True
        )

        if username is None or password is None:
            from resources.lib.vault import Vault
            v = Vault()
            password = v.get_setting("dplayse_password")

        dplay_username = username
        dplay_password = password
        creds = {"credentials": {"username": dplay_username, "password": dplay_password}}
        headers = {
                "x-disco-arkose-token": arkose_token,
                "Origin": "https://auth.dplay.se",
                "x-disco-client": "WEB:10:AUTH_DPLAY_V1:2.4.1",
                # is not specified a captcha is required
                # "Sec-Fetch-Site": "same-site",
                # "Sec-Fetch-Mode": "cors",
                # "Sec-Fetch-Dest": "empty",
                "Referer": "https://auth.dplay.se/login",
                "User-Agent": user_agent
            }
        result = UriHandler.open("https://disco-api.dplay.se/login",
                                 json=creds, additional_headers=headers)
        if UriHandler.instance().status.code > 200:
            Logger.error("Failed to log in: %s", result)
            return False

        Logger.debug("Succesfully logged in")
        return True

    def update_video_item(self, item):
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

        if item.metaData.get(self.__REQUIRES_LOGIN, False):
            logged_in = self.log_on()
            if not logged_in:
                XbmcWrapper.show_dialog(LanguageHelper.LoginErrorTitle, LanguageHelper.LoginErrorText)
                return item

        video_data = UriHandler.open(item.url)
        if not video_data:
            return item

        video_data = JsonHelper(video_data)
        video_info = video_data.get_value("data", "attributes")
        errors = video_data.get_value("errors")
        Logger.error("Error updating items: %s", errors)
        if errors:
            return item

        m3u8url = video_info["streaming"]["hls"]["url"]
        m3u8data = UriHandler.open(m3u8url)
        if AddonSettings.use_adaptive_stream_add_on():
            stream = item.add_stream(m3u8url, 0)
            item.complete = True
            M3u8.set_input_stream_addon_input(stream)
        else:
            # user agent for all sub m3u8 and ts requests needs to be the same
            stream_headers = {"user-agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)"}
            for s, b, a in M3u8.get_streams_from_m3u8(m3u8url, append_query_string=False,
                                                      map_audio=True, play_list_data=m3u8data):
                item.complete = True
                if a:
                    audio_part = a.split("-prog_index.m3u8", 1)[0]
                    audio_id = audio_part.rsplit("/", 1)[-1]
                    s = s.replace("-prog_index.m3u8", "-{0}-prog_index.m3u8".format(audio_id))
                stream = item.add_stream(s, b)
                stream.HttpHeaders.update(stream_headers)

        if self.language == "se":
            vtt_url = M3u8.get_subtitle(m3u8url, m3u8data, language="sv")
        elif self.language == "dk":
            vtt_url = M3u8.get_subtitle(m3u8url, m3u8data, language="da")
        else:
            vtt_url = M3u8.get_subtitle(m3u8url, m3u8data)

        # https://dplaynordics-vod-80.akamaized.net/dplaydni/259/0/hls/243241001/1112635959-prog_index.m3u8?version_hash=bb753129&hdnts=st=1518218118~exp=1518304518~acl=/*~hmac=bdeefe0ec880f8614e14af4d4a5ca4d3260bf2eaa8559e1eb8ba788645f2087a
        vtt_url = vtt_url.replace("-prog_index.m3u8", "-0.vtt")
        item.subtitle = SubtitleHelper.download_subtitle(vtt_url, format='srt')

        # if the user has premium, don't show any warnings
        if self.__has_premium:
            item.isPaid = False
        return item

    def _is_paid_or_logged_on_item(self, result_set):
        """ Check whether an item is paid or not?

        :param dict result_set:

        :return: Indication if the item is paid?
        :rtype: tuple[bool,bool]

        """

        active = set()
        date_format = "%Y-%m-%dT%H:%M:%SZ"

        availability_windows = result_set.get("attributes", {}).get("availabilityWindows")

        if availability_windows is not None:
            for availability in availability_windows:
                start = availability["playableStart"]
                start_date = DateHelper.get_datetime_from_string(start, date_format)
                end = availability.get("playableEnd")
                if end is None:
                    end_date = datetime.datetime.max
                else:
                    end_date = DateHelper.get_datetime_from_string(end, date_format)
                package = availability["package"].lower()

                if start_date < self.__now < end_date:
                    active.add(package)
        else:
            content_packages = result_set.get("relationships", {}).get("contentPackages")
            if content_packages is not None:
                for account_info in result_set["relationships"]["contentPackages"]["data"]:
                    account_type = account_info.get("id", "free").lower()
                    active.add(account_type)

        if "free" in active:
            return False, False
        if "registered" in active:
            return False, True
        return True, True

    def __is_already_logged_on(self, username):
        """ Check if the given user is logged on and sets what packages he/she has.

        :param str username:
        :return: Indicator if the user is alreadly logged in
        :rtype: bool

        """

        me = UriHandler.open("https://disco-api.dplay.se/users/me", no_cache=True)
        if UriHandler.instance().status.code >= 300:
            return False

        account_data = JsonHelper(me)
        signed_in_user = account_data.get_value("data", "attributes", "username")
        if signed_in_user is not None and signed_in_user != username:
            # Log out
            UriHandler.open("https://disco-api.dplay.se/logout", data="", no_cache=True)
            return False

        logged_in = not account_data.get_value("data", "attributes", "anonymous")
        if logged_in:
            Logger.debug("Already logged in")
            packages = account_data.get_value("data", "attributes", "packages", fallback=[])
            self.__has_premium = "Premium" in packages
            return True
        else:
            return False

    def __get_images_from_meta_data(self, data):
        items = []
        data = JsonHelper(data)
        self.__update_image_lookup(data)
        return data, items

    # noinspection PyTypeChecker
    def __update_image_lookup(self, json_data):
        images = filter(lambda a: a["type"] == "image" and "src" in a["attributes"], json_data.get_value("included"))
        images = {str(image["id"]): image["attributes"]["src"] for image in images}

        shows = filter(lambda a: a["type"] == "show", json_data.get_value("included"))
        shows = {str(show["id"]): show["attributes"]["name"] for show in shows}
        self.showLookup.update(shows)
        self.imageLookup.update(images)

    def __get_video_streams(self, video_id, item):
        """ Fetches the video stream for a given videoId

        :param int video_id:        The videoId
        :param MediaItem item:      The mediapart to add the streams to

        :returns: indicating a successfull retrieval
        :rtype: bool

        """

        # hardcoded for now as it does not seem top matter
        dscgeo = '{"countryCode":"%s","expiry":1446917369986}' % (self.language.upper(),)
        dscgeo = HtmlEntityHelper.url_encode(dscgeo)
        headers = {"Cookie": "dsc-geo=%s" % (dscgeo, )}

        # send the data
        http, nothing, host, other = self.baseUrl.split("/", 3)
        subdomain, domain = host.split(".", 1)
        url = "https://secure.%s/secure/api/v2/user/authorization/stream/%s?stream_type=hls" \
              % (domain, video_id,)
        data = UriHandler.open(url, additional_headers=headers, no_cache=True)
        json = JsonHelper(data)
        url = json.get_value("hls")

        if url is None:
            return False

        streams_found = False
        if "?" in url:
            qs = url.split("?")[-1]
        else:
            qs = None
        for s, b in M3u8.get_streams_from_m3u8(url):
            # and we need to append the original QueryString
            if "X-I-FRAME-STREAM" in s:
                continue

            streams_found = True
            if qs is not None:
                if "?" in s:
                    s = "%s&%s" % (s, qs)
                else:
                    s = "%s?%s" % (s, qs)

            item.add_stream(s, b)

        return streams_found

    def __create_generic_item(self, result_set, expected_item_type, url_format):
        video_info = result_set["attributes"]
        name = video_info["name"]

        if expected_item_type != result_set["type"]:
            Logger.warning("Not %s, excluding %s", expected_item_type, name)
            return None

        channel_id = int(result_set["relationships"]["primaryChannel"]["data"]["id"])
        if self.primaryChannelId is not None and channel_id != self.primaryChannelId:
            return None

        item_id = result_set["id"]
        # Show the slug?
        # showSlug = video_info["alternateId"]

        url = url_format.format(item_id)
        item = MediaItem(name, url)
        item.description = video_info.get("description")

        geo_info = video_info.get("geoRestrictions", {"countries": ["world"]})
        item.isGeoLocked = "world" not in geo_info.get("countries")

        # set the images
        if "images" in result_set["relationships"]:
            thumb_id = result_set["relationships"]["images"]["data"][0]["id"]
            item.thumb = self.imageLookup.get(thumb_id, self.noImage)
            if item.thumb == self.noImage:
                Logger.warning("No thumb found for %s", thumb_id)

        # paid or not?
        item.isPaid, logon_required = self._is_paid_or_logged_on_item(result_set)
        if logon_required:
            item.metaData[self.__REQUIRES_LOGIN] = True

        return item

    def __evp_kdf(self, passwd, salt, key_size=8, iv_size=4, iterations=1, hash_algorithm="md5"):
        """
        https://gist.github.com/adrianlzt/d5c9657e205b57f687f528a5ac59fe0e

        :param byte passwd:
        :param byte salt:
        :param int key_size:
        :param int iv_size:
        :param int iterations:
        :param str hash_algorithm:

        :return:

        """

        import hashlib

        target_key_size = key_size + iv_size
        derived_bytes = b""
        number_of_derived_words = 0
        block = None
        hasher = hashlib.new(hash_algorithm)

        while number_of_derived_words < target_key_size:
            if block is not None:
                hasher.update(block)

            hasher.update(passwd)
            hasher.update(salt)
            block = hasher.digest()

            hasher = hashlib.new(hash_algorithm)

            for _ in range(1, iterations):
                hasher.update(block)
                block = hasher.digest()
                hasher = hashlib.new(hash_algorithm)

            derived_bytes += block[0: min(len(block), (target_key_size - number_of_derived_words) * 4)]

            number_of_derived_words += len(block)/4

        return {
            "key": derived_bytes[0: key_size * 4],
            "iv": derived_bytes[key_size * 4:]
        }
