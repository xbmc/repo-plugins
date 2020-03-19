# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import math
import datetime

from resources.lib import chn_class
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.mediaitem import MediaItem
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.jsonhelper import JsonHelper

from resources.lib.parserdata import ParserData
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
        if self.channelCode == "tv4se":
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

        self.mainListUri = "#mainlisting"

        self.baseUrl = "http://www.tv4play.se"
        self.swfUrl = "http://www.tv4play.se/flash/tv4playflashlets.swf"

        self._add_data_parser(self.mainListUri, preprocessor=self.add_categories_and_specials)

        self.episodeItemJson = ["results", ]
        self._add_data_parser("https://api.tv4play.se/play/programs?", json=True,
                              # No longer used:  requiresLogon=True,
                              parser=self.episodeItemJson, creator=self.create_episode_item)

        self._add_data_parser("https://api.tv4play.se/play/categories.json",
                              json=True, match_type=ParserData.MatchExact,
                              parser=[], creator=self.create_category_item)
        self._add_data_parser("https://api.tv4play.se/play/programs?platform=tablet&category=",
                              json=True,
                              parser=self.episodeItemJson, creator=self.create_episode_item)

        self._add_data_parser("http://tv4live-i.akamaihd.net/hls/live/",
                              updater=self.update_live_item)
        self._add_data_parser("http://tv4events1-lh.akamaihd.net/i/EXTRAEVENT5_1",
                              updater=self.update_live_item)

        self.videoItemJson = ["results", ]
        self._add_data_parser("*", preprocessor=self.pre_process_folder_list, json=True,
                              parser=self.videoItemJson, creator=self.create_video_item,
                              updater=self.update_video_item)

        #===============================================================================================================
        # non standard items
        self.maxPageSize = 100  # The Android app uses a page size of 20

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
    #                                noCache=True, proxy=self.proxy, params=params)
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
    #                                noCache=True, proxy=self.proxy, params=params)
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
    #     token = UriHandler.open(tokenUrl, noCache=True, proxy=self.proxy)
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

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set:   The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        # Logger.Trace(result_set)
        json = result_set
        title = json["name"]

        program_id = json["nid"]
        program_id = HtmlEntityHelper.url_encode(program_id)
        url = "https://api.tv4play.se/play/video_assets" \
              "?platform=tablet&per_page=%s&is_live=false&type=episode&" \
              "page=1&node_nids=%s&start=0" % (self.maxPageSize, program_id, )

        if "channel" in json and json["channel"]:
            # noinspection PyTypeChecker
            channel_id = json["channel"]["nid"]
            Logger.trace("ChannelId found: %s", channel_id)
        else:
            channel_id = "tv4"
            Logger.warning("ChannelId NOT found. Assuming %s", channel_id)

        # match the exact channel or put them in TV4
        is_match_for_channel = channel_id.startswith(self.__channelId)
        is_match_for_channel |= self.channelCode == "tv4se" and not channel_id.startswith("sjuan") and not channel_id.startswith("tv12")
        if not is_match_for_channel:
            Logger.debug("Channel mismatch for '%s': %s vs %s", title, channel_id, self.channelCode)
            return None

        item = MediaItem(title, url)
        item.thumb = result_set.get("program_image", self.noImage)
        item.fanart = result_set.get("program_image", self.fanart)
        item.isPaid = result_set.get("is_premium", False)
        return item

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
                "https://api.tv4play.se/play/programs?is_active=true&platform=tablet"
                "&per_page=1000&fl=nid,name,program_image,is_premium,updated_at,channel&start=0",
                None,
                False
            )
        }

        # Channel 4 specific items
        if self.channelCode == "tv4se":
            extras.update({
                LanguageHelper.get_localized_string(LanguageHelper.Categories): (
                    "https://api.tv4play.se/play/categories.json", None, False
                ),
                LanguageHelper.get_localized_string(LanguageHelper.MostViewedEpisodes): (
                    "https://api.tv4play.se/play/video_assets/most_viewed?type=episode"
                    "&platform=tablet&is_live=false&per_page=%s&start=0" % (self.maxPageSize,),
                    None, False
                ),
            })

            today = datetime.datetime.now()
            days = [LanguageHelper.get_localized_string(LanguageHelper.Monday),
                    LanguageHelper.get_localized_string(LanguageHelper.Tuesday),
                    LanguageHelper.get_localized_string(LanguageHelper.Wednesday),
                    LanguageHelper.get_localized_string(LanguageHelper.Thursday),
                    LanguageHelper.get_localized_string(LanguageHelper.Friday),
                    LanguageHelper.get_localized_string(LanguageHelper.Saturday),
                    LanguageHelper.get_localized_string(LanguageHelper.Sunday)]
            for i in range(0, 7, 1):
                start_date = today - datetime.timedelta(i)
                end_date = start_date + datetime.timedelta(1)

                day = days[start_date.weekday()]
                if i == 0:
                    day = LanguageHelper.get_localized_string(LanguageHelper.Today)
                elif i == 1:
                    day = LanguageHelper.get_localized_string(LanguageHelper.Yesterday)

                Logger.trace("Adding item for: %s - %s", start_date, end_date)
                # Old URL:
                # url = "https://api.tv4play.se/play/video_assets?exclude_node_nids=" \
                #       "nyheterna,v%C3%A4der,ekonomi,lotto,sporten,nyheterna-blekinge,nyheterna-bor%C3%A5s," \
                #       "nyheterna-dalarna,nyheterna-g%C3%A4vle,nyheterna-g%C3%B6teborg,nyheterna-halland," \
                #       "nyheterna-helsingborg,nyheterna-j%C3%B6nk%C3%B6ping,nyheterna-kalmar,nyheterna-link%C3%B6ping," \
                #       "nyheterna-lule%C3%A5,nyheterna-malm%C3%B6,nyheterna-norrk%C3%B6ping,nyheterna-skaraborg," \
                #       "nyheterna-skellefte%C3%A5,nyheterna-stockholm,nyheterna-sundsvall,nyheterna-ume%C3%A5," \
                #       "nyheterna-uppsala,nyheterna-v%C3%A4rmland,nyheterna-v%C3%A4st,nyheterna-v%C3%A4ster%C3%A5s," \
                #       "nyheterna-v%C3%A4xj%C3%B6,nyheterna-%C3%B6rebro,nyheterna-%C3%B6stersund,tv4-tolken," \
                #       "fotbollskanalen-europa" \
                #       "&platform=tablet&per_page=32&is_live=false&product_groups=2&type=episode&per_page=100"
                url = "https://api.tv4play.se/play/video_assets?exclude_node_nids=" \
                      "&platform=tablet&per_page=32&is_live=false&product_groups=2&type=episode&per_page=100"
                url = "%s&broadcast_from=%s&broadcast_to=%s&" % (url, start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"))
                extras[day] = (url, start_date, False)

        extras[LanguageHelper.get_localized_string(LanguageHelper.CurrentlyPlayingEpisodes)] = (
            "https://api.tv4play.se/play/video_assets?exclude_node_nids=&platform=tablet&"
            "per_page=32&is_live=true&product_groups=2&type=episode&per_page=100", None, False)

        for name in extras:
            title = name
            url, date, is_live = extras[name]
            item = MediaItem(title, url)
            item.dontGroup = True
            item.complete = True
            item.HttpHeaders = self.httpHeaders
            item.isLive = is_live

            if date is not None:
                item.set_date(date.year, date.month, date.day, 0, 0, 0, text=date.strftime("%Y-%m-%d"))

            items.append(item)

        if not self.channelCode == "tv4se":
            return data, items

        # Add Live TV
        # live = MediaItem("\a.: Live-TV :.",
        #                            "http://tv4events1-lh.akamaihd.net/i/EXTRAEVENT5_1@324055/master.m3u8",
        #                            type="video")
        # live.dontGroup = True
        # # live.isDrmProtected = True
        # live.isGeoLocked = True
        # live.isLive = True
        # items.append(live)

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

        url = "https://api.tv4play.se/play/video_assets?platform=tablet&per_page=%s&page=1" \
              "&sort_order=desc&type=episode&q=%%s&start=0" % (self.maxPageSize, )
        return chn_class.Channel.search_site(self, url)

    def pre_process_folder_list(self, data):
        """ Performs pre-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str|unicode data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        # Add a klip folder only on the first page and only if it is not already a clip page
        if "type=clip" not in self.parentItem.url \
                and "&page=1&" in self.parentItem.url \
                and "node_nids=" in self.parentItem.url:
            # get the category ID
            cat_start = self.parentItem.url.rfind("node_nids=")
            cat_id = self.parentItem.url[cat_start + 10:]
            Logger.debug("Currently doing CatId: '%s'", cat_id)

            url = "https://api.tv4play.se/play/video_assets?platform=tablet&per_page=%s&" \
                  "type=clip&page=1&node_nids=%s&start=0" % (self.maxPageSize, cat_id,)
            clips_title = LanguageHelper.get_localized_string(LanguageHelper.Clips)
            clips = MediaItem(clips_title, url)
            clips.complete = True
            items.append(clips)

        # find the max number of items ("total_hits":2724)
        total_items = int(Regexer.do_regex(r'total_hits\W+(\d+)', data)[-1])
        Logger.debug("Found total of %s items. Only showing %s.", total_items, self.maxPageSize)
        if total_items > self.maxPageSize and "&page=1&" in self.parentItem.url:
            # create a group item
            more_title = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
            more = MediaItem(more_title, "")
            more.complete = True
            items.append(more)

            # what are the total number of pages?
            current_page = 1
            # noinspection PyTypeChecker
            total_pages = int(math.ceil(1.0 * total_items / self.maxPageSize))

            current_url = self.parentItem.url
            needle = "&page="
            while current_page < total_pages:
                # what is the current page
                current_page += 1

                url = current_url.replace("%s1" % (needle, ), "%s%s" % (needle, current_page))
                Logger.debug("Adding next page: %s\n%s", current_page, url)
                page = MediaItem(str(current_page), url)
                page.type = "page"
                page.complete = True

                if total_pages == 2:
                    items = [page]
                    break
                else:
                    more.items.append(page)

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_video_item(self, result_set):
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
        # Logger.Trace(result_set)

        # the vmanProgramId (like 1019976) leads to http://anytime.tv4.se/webtv/metafileFlash.smil?p=1019976&bw=1000&emulate=true&sl=true
        program_id = result_set["id"]
        # Logger.Debug("ProgId = %s", programId)

        # We can either use M3u8 or Dash
        # url = "https://playback-api.b17g.net/media/%s?service=tv4&device=browser&protocol=hls" % (program_id,)
        url = "https://playback-api.b17g.net/media/%s?service=tv4&device=browser&protocol=dash" % (program_id,)
        name = result_set["title"]
        season = result_set.get("season", 0)
        episode = result_set.get("episode", 0)
        is_episodic = 0 < season < 1900 and not episode == 0
        if is_episodic:
            episode_text = None
            if " del " in name:
                name, episode_text = name.split(" del ", 1)
                episode_text = episode_text.lstrip("0123456789")

            if episode_text:
                episode_text = episode_text.lstrip(" -")
                name = "{} - s{:02d}e{:02d} - {}".format(name, season, episode, episode_text)
            else:
                name = "{} - s{:02d}e{:02d}".format(name, season, episode)

        item = MediaItem(name, url)
        item.description = result_set["description"]
        if item.description is None:
            item.description = item.name

        if is_episodic:
            item.set_season_info(season, episode)

        # premium_expire_date_time=2099-12-31T00:00:00+01:00
        expire_date = result_set.get("expire_date_time")
        if bool(expire_date):
            self.__set_expire_time(expire_date, item)

        date = result_set["broadcast_date_time"]
        (date_part, time_part) = date.split("T")
        (year, month, day) = date_part.split("-")
        (hour, minutes, rest1, zone) = time_part.split(":")
        item.set_date(year, month, day, hour, minutes, 00)
        broadcast_date = datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))

        item.fanart = result_set.get("program_image", self.parentItem.fanart)
        thumb_url = result_set.get("image", result_set.get("program_image"))
        # some images need to come via a proxy:
        if thumb_url and "://img.b17g.net/" in thumb_url:
            item.thumb = "https://imageproxy.b17g.services/?format=jpg&shape=cut" \
                         "&quality=90&resize=520x293&source={}"\
                .format(HtmlEntityHelper.url_encode(thumb_url))
        else:
            item.thumb = thumb_url

        availability = result_set["availability"]
        # noinspection PyTypeChecker
        free_period = availability["availability_group_free"]
        # noinspection PyTypeChecker
        premium_period = availability["availability_group_premium"]

        now = datetime.datetime.now()
        if False and not premium_period == "0":
            # always premium
            free_expired = now - datetime.timedelta(days=99 * 365)
        elif free_period == "30+" or free_period is None:
            free_expired = broadcast_date + datetime.timedelta(days=99 * 365)
        else:
            free_expired = broadcast_date + datetime.timedelta(days=int(free_period))
        Logger.trace("Premium info for: %s\nPremium state: %s\nFree State:    %s\nBroadcast %s vs Expired %s",
                     name, premium_period, free_period, broadcast_date, free_expired)

        if now > free_expired:
            item.isPaid = True

        item.type = "video"
        item.complete = False
        item.isGeoLocked = result_set["is_geo_restricted"]
        item.isDrmProtected = result_set["is_drm_protected"]
        item.isLive = result_set.get("is_live", False)
        if item.isLive:
            item.name = "{}:{} - {}".format(hour, minutes, name)
            item.url = "{0}&is_live=true".format(item.url)
        if item.isDrmProtected:
            item.url = "{}&drm=widevine&is_drm=true".format(item.url)

        item.set_info_label("duration", int(result_set.get("duration", 0)))
        return item

    def create_category_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        cat = HtmlEntityHelper.url_encode(result_set['nid'])
        url = "https://api.tv4play.se/play/programs?platform=tablet&category=%s" \
              "&fl=nid,name,program_image,category,logo,is_premium" \
              "&per_page=1000&is_active=true&start=0" % (cat, )
        item = MediaItem(result_set['name'], url)
        item.type = 'folder'
        item.complete = True
        return item

    def update_video_item(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
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
        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=self.localIP)
        stream_info = JsonHelper(data)
        stream_url = stream_info.get_value("playbackItem", "manifestUrl")
        if stream_url is None:
            return item

        if ".mpd" in stream_url:
            return self.__update_dash_video(item, stream_info)

        part = item.create_new_empty_media_part()

        if AddonSettings.use_adaptive_stream_add_on() and False:
            subtitle = M3u8.get_subtitle(stream_url, proxy=self.proxy)
            stream = part.append_media_stream(stream_url, 0)
            M3u8.set_input_stream_addon_input(stream, self.proxy)
            item.complete = True
        else:
            m3u8_data = UriHandler.open(stream_url, proxy=self.proxy, additional_headers=self.localIP)
            subtitle = M3u8.get_subtitle(stream_url, proxy=self.proxy, play_list_data=m3u8_data)
            for s, b, a in M3u8.get_streams_from_m3u8(stream_url, self.proxy,
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
                part.append_media_stream(s, b)

        if subtitle:
            subtitle = subtitle.replace(".m3u8", ".webvtt")
            part.Subtitle = SubtitleHelper.download_subtitle(subtitle,
                                                             format="m3u8srt",
                                                             proxy=self.proxy)
        return item

    def update_live_item(self, item):
        """ Updates an existing MediaItem for a live stream with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_live_item for %s (%s)', item.name, self.channelName)

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()

        spoof_ip = self._get_setting("spoof_ip", "0.0.0.0")
        if spoof_ip:
            for s, b in M3u8.get_streams_from_m3u8(item.url, self.proxy,
                                                   headers={"X-Forwarded-For": spoof_ip}):
                part.append_media_stream(s, b)
        else:
            for s, b in M3u8.get_streams_from_m3u8(item.url, self.proxy):
                part.append_media_stream(s, b)

        item.complete = True
        return item

    def __set_expire_time(self, expire_date, item):
        """ Parses and sets the correct expire date.

        :param str expire_date:  The expire date value
        :param MediaItem item:   The item to update

        """

        expire_date = expire_date.split("+")[0]  # .replace("T", " ")
        year = expire_date.split("-", 1)[0]
        if len(year) == 4 and int(year) < datetime.datetime.now().year + 50:
            expire_date = DateHelper.get_datetime_from_string(expire_date)
            item.set_expire_datetime(timestamp=expire_date)

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
        part = item.create_new_empty_media_part()
        stream = part.append_media_stream(stream_url, 0)

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
                stream, proxy=self.proxy, license_key=license_key)
            item.isDrmProtected = False
        else:
            Mpd.set_input_stream_addon_input(stream, proxy=self.proxy)

        item.complete = True
        return item
