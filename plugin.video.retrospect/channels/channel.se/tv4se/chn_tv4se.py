# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later

import pytz
import datetime

from resources.lib import chn_class, mediatype, contenttype
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.jsonhelper import JsonHelper

from resources.lib.regexer import Regexer
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.streams.mpd import Mpd
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.subtitlehelper import SubtitleHelper


class Channel(chn_class.Channel):

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.__channelId = "tv4"
        self.mainListUri = self.__get_api_query(
            '{indexPage{panels{__typename,...on SwipeModule{title,subheading,cards{__typename,'
            '... on ProgramCard{title,program{name,id,nid,description,image}}}}}}}')

        if self.channelCode == "tv4segroup":
            self.noImage = "tv4image.png"

        elif self.channelCode == "tv4se":
            self.noImage = "tv4image.png"
            self.__channelId = "tv4"

        elif self.channelCode == "tv7se":
            self.noImage = "tv7image.png"
            self.__channelId = "sjuan"

        elif self.channelCode == "tv12se":
            self.noImage = "tv12image.png"
            self.__channelId = "tv12"

        else:
            raise Exception("Invalid channel code")

        # setup the urls
        # self.mainListUri = "https://api.tv4play.se/play/programs?is_active=true&platform=tablet&per_page=1000" \
        #                    "&fl=nid,name,program_image&start=0"

        self.baseUrl = "http://www.tv4play.se"
        self.swfUrl = "http://www.tv4play.se/flash/tv4playflashlets.swf"

        self._add_data_parser(self.mainListUri, json=True,
                              name="GraphQL mainlist parser",
                              preprocessor=self.add_categories_and_specials,
                              parser=["data", "indexPage", "panels"],
                              creator=self.create_api_typed_item)

        # noinspection PyTypeChecker
        self._add_data_parser("https://graphql.tv4play.se/graphql?query=query%7Btags%7D",
                              name="Tag overview", json=True,
                              parser=["data", "tags"], creator=self.create_api_tag)

        self._add_data_parser("https://graphql.tv4play.se/graphql?query=%7Bprogram%28nid",
                              name="GraphQL seasons/folders for program listing", json=True,
                              preprocessor=self.detect_single_folder,
                              parser=["data", "program", "videoPanels"],
                              creator=self.create_api_videopanel_type)

        self._add_data_parser("https://graphql.tv4play.se/graphql?query=%7BvideoPanel%28id%3A",
                              name="GraphQL single season/folder listing", json=True,
                              postprocessor=self.add_next_page,
                              parser=["data", "videoPanel", "videoList", "videoAssets"],
                              creator=self.create_api_video_asset_type)

        self._add_data_parsers(["https://graphql.tv4play.se/graphql?query=query%7BprogramSearch",
                                "https://graphql.tv4play.se/graphql?query=%7BprogramSearch"],
                               name="GraphQL search results and show listings", json=True,
                               parser=["data", "programSearch", "programs"],
                               creator=self.create_api_typed_item)

        self._add_data_parser("https://graphql.tv4play.se/graphql?operationName=LiveVideos",
                              name="GraphQL currently playing", json=True,
                              parser=["data", "liveVideos", "videoAssets"],
                              creator=self.create_api_typed_item)

        # self._add_data_parser("https://www.tv4play.se/_next", json=True,
        self._add_data_parser("https://www.tv4play.se/alla-program", json=True,
                              name="Specific Program list API",
                              preprocessor=self.extract_tv_show_list,
                              parser=["props", "pageProps", "initialApolloState"],
                              creator=self.create_api_typed_item)

        self._add_data_parser("http://tv4live-i.akamaihd.net/hls/live/",
                              updater=self.update_live_item)
        self._add_data_parser("http://tv4events1-lh.akamaihd.net/i/EXTRAEVENT5_1",
                              updater=self.update_live_item)

        self._add_data_parser("*", updater=self.update_video_item)

        #===============================================================================================================
        # non standard items
        self.__maxPageSize = 100  # The Android app uses a page size of 20
        self.__program_fields = '{__typename,description,displayCategory,id,image,images{main16x9},name,nid,genres,videoPanels{id}}'
        self.__season_count_meta = "season_count"
        self.__timezone = pytz.timezone("Europe/Stockholm")

        #===============================================================================================================
        # Test cases:
        #   Batman - WideVine
        #   Antikdeckarna - Clips

        # ====================================== Actual channel setup STOPS here =======================================
        return

    # No logon for now
    # def log_on(self):
    #     """ Makes sure that we are logged on. """
    #
    #     username = AddonSettings.get_setting("channel_tv4play_se_username")
    #     if not username:
    #         Logger.Info("No user name for TV4 Play, not logging in")
    #         return False
    #
    #     # Fetch an existing token
    #     tokenSettingId = "channel_tv4play_se_token"
    #     token = AddonSettings.get_setting(tokenSettingId)
    #     sessionToken = None
    #     if token:
    #         expiresAt, vimondSessionToken, sessionToken = token.split("|")
    #         expireDate = DateHelper.get_date_from_posix(float(expiresAt))
    #         if expireDate > datetime.datetime.now():
    #             Logger.Info("Found existing valid TV4Play token (valid until: %s)", expireDate)
    #             self.httpHeaders["Cookie"] = "JSESSIONID=%s; sessionToken=%s" % (vimondSessionToken, sessionToken)
    #             return True
    #         Logger.Warning("Found existing expired TV4Play token")
    #
    #     Logger.Info("Fetching a new TV4Play token")
    #     data = None
    #     if sessionToken:
    #         # 2a: try reauthenticating
    #         # POST https://account.services.tv4play.se/session/reauthenticate
    #         # session_token=<sessionToken>&client=tv4play-web
    #         # returns the same as authenticate
    #         Logger.Info("Reauthenticating based on the old TV4Play token")
    #         params = "session_token=%s&" \
    #                  "client=tv4play-web" % (
    #                      HtmlEntityHelper.url_encode(sessionToken)
    #                  )
    #         data = UriHandler.open("https://account.services.tv4play.se/session/reauthenticate",
    #                                noCache=True, params=params)
    #
    #     if not data or "vimond_session_token" not in data:
    #         # 1: https://www.tv4play.se/session/new
    #         # Extract the "authenticity_token"
    #         Logger.Info("Authenticating based on username and password")
    #
    #         v = Vault()
    #         password = v.get_setting("channel_tv4play_se_password")
    #         if not password:
    #             XbmcWrapper.show_dialog(
    #                 title=None,
    #                 lines=LanguageHelper.get_localized_string(LanguageHelper.MissingCredentials),
    #                 # notificationType=XbmcWrapper.Error,
    #                 # displayTime=5000
    #             )
    #
    #         # 2b: https://account.services.tv4play.se/session/authenticate
    #         # Content-Type: application/x-www-form-urlencoded; charset=UTF-8
    #         params = "username=%s&" \
    #                  "password=%s&" \
    #                  "remember_me=true&" \
    #                  "client=tv4play-web" % (
    #                      HtmlEntityHelper.url_encode(username),
    #                      HtmlEntityHelper.url_encode(password),
    #                  )
    #         data = UriHandler.open("https://account.services.tv4play.se/session/authenticate",
    #                                noCache=True, params=params)
    #         if not data:
    #             Logger.Error("Error logging in")
    #             return
    #
    #     # Extract the data we need
    #     data = JsonHelper(data)
    #     vimondSessionToken = data.get_value('vimond_session_token')
    #     # vimondRememberMe = data.get_value('vimond_remember_me')
    #     sessionToken = data.get_value('session_token')
    #
    #     # 2c: alternative: POST https://account.services.tv4play.se/session/keep_alive
    #     # vimond_session_token=<vimondSessionToken>&session_token=<sessionToken>&client=tv4play-web
    #     # returns:
    #     # {"vimond_session_token":".....", # "vimond_remember_me":"......"}
    #
    #     # 3: https://token.services.tv4play.se/jwt?jsessionid=<vimondSessionToken>&client=tv4play-web
    #     # Get an OAuth token -> not really needed for the standard HTTP calls but it gets us the
    #     # expiration date
    #     tokenUrl = "https://token.services.tv4play.se/jwt?jsessionid=%s&client=tv4play-web" % (vimondSessionToken, )
    #     token = UriHandler.open(tokenUrl, noCache=True)
    #     # Figure out the expiration data
    #     data, expires, other = token.split('.')
    #     expires += "=" * (4 - len(expires) % 4)
    #     Logger.Debug("Found data: \n%s\n%s\n%s", data, expires, other)
    #     tokenData = EncodingHelper.decode_base64(expires)
    #     tokenData = JsonHelper(tokenData)
    #     expiresAt = tokenData.get_value("exp")
    #
    #     Logger.Debug("Token expires at: %s (%s)", DateHelper.get_date_from_posix(float(expiresAt)), expiresAt)
    #     # AddonSettings.set_setting(tokenSettingId, "%s|%s" % (expiresAt, token))
    #     AddonSettings.set_setting(tokenSettingId, "%s|%s|%s" % (expiresAt, vimondSessionToken, sessionToken))
    #
    #     # 4: use with: Authorization: Bearer <token>
    #     # 4: use cookies:
    #     #  Cookie: JSESSIONID=<vimondSessionToken>;
    #     #  Cookie: sessionToken=<sessionToken>;
    #     #  Cookie: rememberme=<sessionToken>;
    #
    #     # return {"JSESSIONID": vimondSessionToken, "sessionToken": sessionToken}
    #     self.httpHeaders["Cookie"] = "JSESSIONID=%s; sessionToken=%s" % (vimondSessionToken, sessionToken)
    #     return True

    def create_api_tag(self, result_set):
        """ Creates a new MediaItem for tag listing items

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param str result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        query = 'query{programSearch(tag:"%s",per_page:1000){__typename,programs' \
                '%s,' \
                'totalHits}}' % (result_set, self.__program_fields)
        query = HtmlEntityHelper.url_encode(query)
        url = "https://graphql.tv4play.se/graphql?query={}".format(query)
        item = MediaItem(result_set, url)
        return item

    def create_api_typed_item(self, result_set):
        """ Creates a new MediaItem based on the __typename attribute.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        api_type = result_set["__typename"]
        Logger.trace("%s: %s", api_type, result_set)

        if api_type == "Program":
            item = self.create_api_program_type(result_set)
        elif api_type == "ProgramCard":
            item = self.create_api_program_type(result_set.get("program"))
        elif api_type == "VideoAsset":
            item = self.create_api_video_asset_type(result_set)
        elif api_type == "SwipeModule":
            item = self.create_api_swipefolder_type(result_set)
        elif api_type == "VideoPanel":
            item = self.create_api_videopanel_type(result_set)
        else:
            Logger.warning("Missing type: %s", api_type)
            return None

        return item

    def create_api_program_type(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set:   The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        json = result_set
        title = json["name"]

        # https://graphql.tv4play.se/graphql?operationName=cdp&variables={"nid":"100-penisar"}&extensions={"persistedQuery":{"version":1,"sha256Hash":"255449d35b5679b2cb5a9b85e63afd532c68d50268ae2740ae82f24d83a84774"}}
        program_id = json["nid"]
        url = self.__get_api_query('{program(nid:"%s"){name,description,videoPanels{id,name,subheading,assetType}}}' % (program_id,))

        item = FolderItem(title, url, content_type=contenttype.EPISODES)
        item.tv_show_title = title
        item.description = result_set.get("description", None)

        item.thumb = result_set.get("image")
        if item.thumb is not None:
            item.thumb = "https://imageproxy.b17g.services/?format=jpg&shape=cut" \
                         "&quality=70&resize=520x293&source={}"\
                .format(HtmlEntityHelper.url_encode(item.thumb))

        item.fanart = result_set.get("image")
        if item.fanart is not None:
            item.fanart = "https://imageproxy.b17g.services/?format=jpg&shape=cut" \
                         "&quality=70&resize=1280x720&source={}" \
                .format(HtmlEntityHelper.url_encode(item.fanart))

        item.isPaid = result_set.get("is_premium", False)

        return item

    def create_api_videopanel_type(self, result_set):
        """ Creates a new MediaItem for a folder listing

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        title = result_set["name"]
        folder_id = result_set["id"]
        url = self.__get_api_folder_url(folder_id)
        item = FolderItem(title, url, content_type=contenttype.EPISODES)
        item.metaData["offset"] = 0
        item.metaData["folder_id"] = folder_id
        return item

    def create_api_swipefolder_type(self, result_set):
        """ Creates a new MediaItem for a folder listing

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        title = result_set["title"]

        if title == "Sista chansen":
            title = LanguageHelper.get_localized_string(LanguageHelper.LastChance)
        elif title == "Mest sedda programmen":
            title = LanguageHelper.get_localized_string(LanguageHelper.MostViewedEpisodes)
        elif title.startswith("Popul"):
            title = LanguageHelper.get_localized_string(LanguageHelper.Popular)
        elif title.startswith("Nyheter"):
            title = LanguageHelper.get_localized_string(LanguageHelper.LatestNews)

        item = FolderItem(title, "swipe://{}".format(HtmlEntityHelper.url_encode(title)), content_type=contenttype.VIDEOS)
        for card in result_set["cards"]:
            child = self.create_api_typed_item(card)
            if not child:
                continue

            item.items.append(child)

        if not item.items:
            return None

        return item

    def create_api_video_asset_type(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

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

        Logger.trace('starting FormatVideoItem for %s', self.channelName)

        program_id = result_set["id"]
        url = "https://playback-api.b17g.net/media/{}?service=tv4&device=browser&protocol=dash".\
            format(program_id)

        name = result_set["title"]
        season = result_set.get("season", 0)
        episode = result_set.get("episode", 0)
        is_episodic = 0 < season < 1900 and not episode == 0
        is_live = result_set.get("live", False)
        if is_episodic and not is_live:
            episode_text = None
            if " del " in name:
                name, episode_text = name.split(" del ", 1)
                episode_text = episode_text.lstrip("0123456789")

            if episode_text:
                episode_text = episode_text.lstrip(" -")
                name = episode_text
            else:
                name = "{} {}".format("Avsnitt", episode)

        item = MediaItem(name, url)
        item.description = result_set["description"]
        if item.description is None:
            item.description = item.name

        if is_episodic and not is_live:
            item.set_season_info(season, episode)

        # premium_expire_date_time=2099-12-31T00:00:00+01:00
        expire_in_days = result_set.get("daysLeftInService", 0)
        if 0 < expire_in_days < 10000:
            item.set_expire_datetime(
                timestamp=datetime.datetime.now() + datetime.timedelta(days=expire_in_days))

        date = result_set["broadcastDateTime"]
        broadcast_date = DateHelper.get_datetime_from_string(date, "%Y-%m-%dT%H:%M:%SZ", "UTC")
        broadcast_date = broadcast_date.astimezone(self.__timezone)
        item.set_date(broadcast_date.year,
                      broadcast_date.month,
                      broadcast_date.day,
                      broadcast_date.hour,
                      broadcast_date.minute,
                      0)

        item.fanart = result_set.get("program_image", self.parentItem.fanart)
        thumb_url = result_set.get("image", result_set.get("program_image"))
        # some images need to come via a proxy:
        if thumb_url and "://img.b17g.net/" in thumb_url:
            item.thumb = "https://imageproxy.b17g.services/?format=jpg&shape=cut" \
                         "&quality=70&resize=520x293&source={}" \
                .format(HtmlEntityHelper.url_encode(thumb_url))
        else:
            item.thumb = thumb_url

        item.media_type = mediatype.EPISODE
        item.complete = False
        item.isGeoLocked = True
        # For now, none are paid.
        # item.isPaid = not result_set.get("freemium", False)
        if "drmProtected" in result_set:
            item.isDrmProtected = result_set["drmProtected"]
        elif "is_drm_protected" in result_set:
            item.isDrmProtected = result_set["is_drm_protected"]

        item.isLive = result_set.get("live", False)
        if item.isLive:
            item.name = "{:02d}:{:02d} - {}".format(broadcast_date.hour, broadcast_date.minute, name)
            item.url = "{0}&is_live=true".format(item.url)
        if item.isDrmProtected:
            item.url = "{}&drm=widevine&is_drm=true".format(item.url)

        item.set_info_label("duration", int(result_set.get("duration", 0)))
        return item

    def extract_tv_show_list(self, data):
        """ Performs pre-process actions and converts the dictionary to a proper list

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        # Find the build id for the current CMS build
        # build_id = Regexer.do_regex(r'"buildId"\W*:\W*"([^"]+)"', data)[0]
        # data = UriHandler.open("https://www.tv4play.se/_next/data/{}/allprograms.json".format(build_id))

        data = Regexer.do_regex(r'__NEXT_DATA__" type="application/json">(.*?)</script>', data)[0]
        json_data = JsonHelper(data)
        json_data.json["props"]["pageProps"]["initialApolloState"] = list(json_data.json["props"]["pageProps"]["initialApolloState"].values())
        return json_data, []

    def add_next_page(self, data, items):
        """ Performs post-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str|JsonHelper data:     The retrieve data that was loaded for the
                                         current item and URL.
        :param list[MediaItem] items:   The currently available items

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: list[MediaItem]

        """

        Logger.info("Performing Post-Processing")

        total_hits = data.get_value('data', 'videoPanel', 'videoList', 'totalHits')
        if total_hits > len(items):
            Logger.debug("Adding items from next page")
            offset = self.parentItem.metaData.get("offset", 0) + self.__maxPageSize
            folder_id = self.parentItem.metaData.get("folder_id")
            if not folder_id:
                Logger.warning("Cannot find 'folder_id' in MediaItem")
                return items

            url = self.__get_api_folder_url(folder_id, offset)
            data = UriHandler.open(url)
            json_data = JsonHelper(data)
            extra_results = json_data.get_value("data", "videoPanel", "videoList", "videoAssets", fallback=[])
            Logger.debug("Adding %d extra results from next page", len(extra_results or []))
            for result in extra_results:
                item = self.create_api_video_asset_type(result)
                if item:
                    items.append(item)

        Logger.debug("Post-Processing finished")
        return items

    def detect_single_folder(self, data):
        """ Performs pre-process actions and detect single folder items

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        json_data = JsonHelper(data)
        panels = json_data.get_value("data", "program", "videoPanels")
        if len(panels) != 1:
            return data, []

        items = []
        item = self.create_api_videopanel_type(panels[0])
        data = UriHandler.open(item.url)
        json_data = JsonHelper(data)
        assets = json_data.get_value("data", "videoPanel", "videoList", "videoAssets")
        for asset in assets:
            item = self.create_api_video_asset_type(asset)
            if item:
                items.append(item)

        return "", items

    def add_categories_and_specials(self, data):
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

        Logger.info("Performing Pre-Processing")
        items = []

        extras = {
            LanguageHelper.get_localized_string(LanguageHelper.Search): ("searchSite", None, False),
            LanguageHelper.get_localized_string(LanguageHelper.TvShows): (
                "https://www.tv4play.se/alla-program",
                None, False
            ),
            LanguageHelper.get_localized_string(LanguageHelper.Categories): (
                "https://graphql.tv4play.se/graphql?query=query%7Btags%7D", None, False
            ),
            LanguageHelper.get_localized_string(LanguageHelper.CurrentlyPlayingEpisodes): (
                self.__get_api_url("LiveVideos", "9b3d0d2f039089311cde2989760744844f7c4bb5033b0ce5643676ee60cb0901"),
                None, False
            )
        }

        # No more extras
        # today = datetime.datetime.now()
        # days = [LanguageHelper.get_localized_string(LanguageHelper.Monday),
        #         LanguageHelper.get_localized_string(LanguageHelper.Tuesday),
        #         LanguageHelper.get_localized_string(LanguageHelper.Wednesday),
        #         LanguageHelper.get_localized_string(LanguageHelper.Thursday),
        #         LanguageHelper.get_localized_string(LanguageHelper.Friday),
        #         LanguageHelper.get_localized_string(LanguageHelper.Saturday),
        #         LanguageHelper.get_localized_string(LanguageHelper.Sunday)]
        # for i in range(0, 7, 1):
        #     start_date = today - datetime.timedelta(i)
        #     end_date = start_date + datetime.timedelta(1)
        #
        #     day = days[start_date.weekday()]
        #     if i == 0:
        #         day = LanguageHelper.get_localized_string(LanguageHelper.Today)
        #     elif i == 1:
        #         day = LanguageHelper.get_localized_string(LanguageHelper.Yesterday)
        #
        #     Logger.trace("Adding item for: %s - %s", start_date, end_date)
        #     url = "https://api.tv4play.se/play/video_assets?exclude_node_nids=" \
        #           "&platform=tablet&is_live=false&product_groups=2&type=episode&per_page=100"
        #     url = "%s&broadcast_from=%s&broadcast_to=%s&" % (url, start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"))
        #     extras[day] = (url, start_date, False)
        #
        # extras[LanguageHelper.get_localized_string(LanguageHelper.CurrentlyPlayingEpisodes)] = (
        #     "https://api.tv4play.se/play/video_assets?exclude_node_nids=&platform=tablet&"
        #     "is_live=true&product_groups=2&type=episode&per_page=100", None, False)

        # Actually add the extra items
        for name in extras:
            title = name
            url, date, is_live = extras[name]   # type: str, datetime.datetime, bool
            item = FolderItem(title, url, content_type=contenttype.VIDEOS)
            item.dontGroup = True
            item.complete = True
            item.HttpHeaders = self.httpHeaders
            item.isLive = is_live

            if date is not None:
                item.set_date(date.year, date.month, date.day, 0, 0, 0, text=date.strftime("%Y-%m-%d"))

            items.append(item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def search_site(self, url=None):
        """ Creates an list of items by searching the site.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with an URL encoded representation of the
        text to search for.

        :param str|None url:     Url to use to search with a %s for the search parameters.

        :return: A list with search results as MediaItems.
        :rtype: list[MediaItem]

        """

        url = self.__get_api_query('{programSearch(q:"",perPage:100){totalHits,programs%s}}' % self.__program_fields)
        url = url.replace("%", "%%")
        url = url.replace("%%22%%22", "%%22%s%%22")
        return chn_class.Channel.search_site(self, url)

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

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        # noinspection PyStatementEffect
        """
                C:\temp\rtmpdump-2.3>rtmpdump.exe -z -o test.flv -n "cp70051.edgefcs.net" -a "tv
                4ondemand" -y "mp4:/mp4root/2010-06-02/pid2780626_1019976_T3MP48_.mp4?token=c3Rh
                cnRfdGltZT0yMDEwMDcyNjE2NDYyNiZlbmRfdGltZT0yMDEwMDcyNjE2NDgyNiZkaWdlc3Q9ZjFjN2U1
                NTRiY2U5ODMxMDMwYWQxZWEwNzNhZmUxNjI=" -l 2

                C:\temp\rtmpdump-2.3>rtmpdump.exe -z -o test.flv -r rtmpe://cp70051.edgefcs.net/
                tv4ondemand/mp4root/2010-06-02/pid2780626_1019976_T3MP48_.mp4?token=c3RhcnRfdGlt
                ZT0yMDEwMDcyNjE2NDYyNiZlbmRfdGltZT0yMDEwMDcyNjE2NDgyNiZkaWdlc3Q9ZjFjN2U1NTRiY2U5
                ODMxMDMwYWQxZWEwNzNhZmUxNjI=
                """

        # retrieve the mediaurl
        data = UriHandler.open(item.url)
        stream_info = JsonHelper(data)
        stream_url = stream_info.get_value("playbackItem", "manifestUrl")
        if stream_url is None:
            return item

        if ".mpd" in stream_url:
            return self.__update_dash_video(item, stream_info)

        if AddonSettings.use_adaptive_stream_add_on() and False:
            subtitle = M3u8.get_subtitle(stream_url)
            stream = item.add_stream(stream_url, 0)
            M3u8.set_input_stream_addon_input(stream)
            item.complete = True
        else:
            m3u8_data = UriHandler.open(stream_url)
            subtitle = M3u8.get_subtitle(stream_url, play_list_data=m3u8_data)
            for s, b, a in M3u8.get_streams_from_m3u8(stream_url,
                                                      play_list_data=m3u8_data, map_audio=True):
                item.complete = True
                if not item.isLive and "-video" not in s:
                    continue

                if a and "-audio" not in s:
                    # remove any query parameters
                    video_part = s.rsplit("?", 1)[0]
                    video_part = video_part.rsplit("-", 1)[-1]
                    video_part = "-%s" % (video_part,)
                    s = a.replace(".m3u8", video_part)
                item.add_stream(s, b)

        if subtitle:
            subtitle = subtitle.replace(".m3u8", ".webvtt")
            item.subtitle = SubtitleHelper.download_subtitle(subtitle, format="m3u8srt")
        return item

    def update_live_item(self, item):
        """ Updates an existing MediaItem for a live stream with more data.

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

        Logger.debug('Starting update_live_item for %s (%s)', item.name, self.channelName)

        item.streams = []
        for s, b in M3u8.get_streams_from_m3u8(item.url):
            item.add_stream(s, b)

        item.complete = True
        return item

    def __get_api_url(self, operation, hash_value, variables=None):  # NOSONAR
        """ Generates a GraphQL url

        :param str operation:   The operation to use
        :param str hash_value:  The hash of the Query
        :param dict variables:  Any variables to pass

        :return: A GraphQL string
        :rtype: str

        """

        extensions = {"persistedQuery": {"version": 1, "sha256Hash": hash_value}}
        extensions = HtmlEntityHelper.url_encode(JsonHelper.dump(extensions, pretty_print=False))

        final_vars = {"order_by": "NAME", "per_page": 1000}
        if variables:
            final_vars = variables
        final_vars = HtmlEntityHelper.url_encode(JsonHelper.dump(final_vars, pretty_print=False))

        url = "https://graphql.tv4play.se/graphql?" \
              "operationName={}&" \
              "variables={}&" \
              "extensions={}".format(operation, final_vars, extensions)
        return url

    def __get_api_query(self, query):
        return "https://graphql.tv4play.se/graphql?query={}".format(HtmlEntityHelper.url_encode(query))

    def __get_api_folder_url(self, folder_id, offset=0):
        return self.__get_api_query(
            '{videoPanel(id: "%s"){name,videoList(limit: %s, offset:%d, '
            'sortOrder: "broadcastDateTime"){totalHits,videoAssets'
            '{title,id,description,season,episode,daysLeftInService,broadcastDateTime,image,'
            'freemium,drmProtected,live,duration}}}}' % (folder_id, self.__maxPageSize, offset))

    def __update_dash_video(self, item, stream_info):
        """

        :param MediaItem item:          The item that was updated
        :param JsonHelper stream_info:  The stream info
        """

        if not AddonSettings.use_adaptive_stream_add_on(with_encryption=True):
            XbmcWrapper.show_dialog(
                LanguageHelper.get_localized_string(LanguageHelper.DrmTitle),
                LanguageHelper.get_localized_string(LanguageHelper.WidevineLeiaRequired))
            return item

        playback_item = stream_info.get_value("playbackItem")

        stream_url = playback_item["manifestUrl"]
        stream = item.add_stream(stream_url, 0)

        license_info = playback_item.get("license", None)
        if license_info is not None:
            license_key_token = license_info["token"]
            auth_token = license_info["castlabsToken"]
            header = {
                "x-dt-auth-token": auth_token,
                "content-type": "application/octstream"
            }
            license_url = license_info["castlabsServer"]
            license_key = Mpd.get_license_key(
                license_url, key_value=license_key_token, key_headers=header)

            Mpd.set_input_stream_addon_input(
                stream, license_key=license_key)
            item.isDrmProtected = False
        else:
            Mpd.set_input_stream_addon_input(stream)

        item.complete = True
        return item
