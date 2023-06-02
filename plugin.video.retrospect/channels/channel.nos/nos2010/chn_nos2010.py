# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import pytz
import re

from resources.lib import chn_class
from resources.lib import contenttype
from resources.lib import mediatype
from resources.lib.logger import Logger
from resources.lib.regexer import Regexer
from resources.lib.helpers import subtitlehelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.streams.npostream import NpoStream
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.parserdata import ParserData
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.vault import Vault
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.actions import action


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info):
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
            self.baseUrl = "https://apps-api.uitzendinggemist.nl"
            self.mainListUri = "#mainlist"
            self.noImage = "nosimage.png"
        else:
            raise NotImplementedError("Code %s is not implemented" % (self.channelCode,))

        # mainlist stuff
        self._add_data_parser("#mainlist", preprocessor=self.get_initial_folder_items)

        # live stuff
        self.baseUrlLive = "https://www.npostart.nl"

        # live radio, the folders and items
        self._add_data_parser("https://start-api.npo.nl/page/live",
                              name="Live Radio Streams", json=True,
                              parser=["components", ("panel", "live.regular.1", 0), "epg"], creator=self.create_live_radio)

        self._add_data_parser("/live", match_type=ParserData.MatchEnd,
                              name="Main Live Stream HTML parser",
                              preprocessor=self.get_additional_live_items,
                              parser=r'<a href="[^"]+/live/([^"]+)" class="npo-tile-link"[^>]+>[\w\W]{0,1000}?<img data-src="([^"]+)"[\w\W]{0,1000}?<h2>(?:Nu: )?([^<]+)</h2>\W+<p>(?:Straks: )?([^<]*)</p>',
                              creator=self.create_live_tv,
                              updater=self.update_video_item_live)

        self._add_data_parser("https://www.npostart.nl/live/", name="Live Video Updater from HTML",
                              updater=self.update_video_item_live)

        # Use old urls with new Updater
        self._add_data_parser("http://e.omroep.nl/metadata/", name="e.omroep.nl classic parser",
                              updater=self.update_from_poms, requires_logon=True)

        # Standard updater
        self._add_data_parser("*", requires_logon=True,
                              updater=self.update_video_item)

        # recent and popular stuff and other Json data
        self._add_data_parser(".json", name="JSON List Parser for the recent/tips/populair",
                              parser=[], creator=self.create_video_item_json,
                              json=True, match_type=ParserData.MatchEnd)

        self._add_data_parser("#recent", name="Recent items list",
                              preprocessor=self.add_recent_items)

        self._add_data_parser("https://start-api.npo.nl/media/series/", json=True,
                              name="API based video items",
                              parser=["items", ], creator=self.create_api_video_item,
                              preprocessor=self.extract_api_pages)

        self._add_data_parser("https://start-api.npo.nl/epg/", json=True,
                              name="API based recent items",
                              parser=[], creator=self.create_api_epg_item,
                              preprocessor=self.extract_epi_epg_items)

        self._add_data_parser("https://start-api.npo.nl/page/franchise", json=True,
                              name="API based video items for a franchise",
                              parser=["items"],
                              creator=self.create_api_video_item,
                              preprocessor=self.process_franchise_page)

        # Alpha listing and paging for that list
        self._add_data_parser("#alphalisting", preprocessor=self.alpha_listing)

        episode_parser = Regexer.from_expresso(
            r'id="(?<powid>[^"]+)"[^>]*>\W*<a href="(?<url>[^"]+)" title="(?<title>[^"]+)"[^>]+\W+'
            r'<div[^(>]+>\s*(?:<img[^>]+data-src="(?<thumburl>[^"]+)")?')
        self._add_data_parsers(["https://www.npostart.nl/media/series?page=", ],
                               name="Parser for main series overview pages",
                               preprocessor=self.extract_tiles,
                               parser=episode_parser,
                               creator=self.create_episode_item)

        # very similar parser as the Live Channels!
        video_parser = Regexer.from_expresso(
            r'<div[^>]+class="(?<class>[^"]+)"[^>]+id="(?<powid>[^"]+)"[^>]*>\W*<a href="[^"]+/'
            r'(?<url>[^/"]+)" class="npo-tile-link"[^>]+(?:data-scorecard=\'(?<videodata>[^\']*)\')?'
            r'[^>]*>\W+<div[^>]+>\W+<div [^>]+data-from="(?<date>[^"]*)"[^>]+'
            r'data-premium-from="(?<datePremium>[^"]*)"(?<videoDetection>[\w\W]{0,1000}?)<img[^>]+'
            r'data-src="(?<thumburl>[^"]+)"[\w\W]{0,1000}?<h2>(?<title>[^<]+)</h2>\W+<p>'
            r'(?:\s*&nbsp;\s*)*(?<subtitle>[^<]*)</p>')
        self._add_data_parsers(["https://www.npostart.nl/media/series/",
                                "https://www.npostart.nl/search/extended",
                                "https://www.npostart.nl/media/collections/"],
                               name="Parser for shows on the main series sub pages, the search and the genres",
                               preprocessor=self.extract_tiles,
                               parser=video_parser,
                               creator=self.create_npo_item)

        # Genres
        self._add_data_parser("https://www.npostart.nl/programmas",
                              match_type=ParserData.MatchExact,
                              name="Genres",
                              parser=r'<a\W+class="close-dropdown"\W+href="/collectie/([^"]+)"\W+'
                                     r'title="([^"]+)"[^>]+data-value="([^"]+)"[^>]+',
                              creator=self.create_genre_item)

        # Favourites
        self._add_data_parser("https://www.npostart.nl/api/account/@me/profile",
                              match_type=ParserData.MatchExact, json=True, requires_logon=True,
                              name="Profile selection",
                              parser=["profiles"], creator=self.create_profile_item)
        self._add_data_parser("#list_profile",
                              name="List favourites for profile",
                              preprocessor=self.switch_profile,
                              requires_logon=True)
        self._add_data_parser("https://www.npostart.nl/ums/accounts/@me/favourites?",
                              preprocessor=self.extract_tiles,
                              parser=episode_parser,
                              creator=self.create_episode_item,
                              requires_logon=True)
        self._add_data_parser("https://www.npostart.nl/ums/accounts/@me/favourites/episodes?",
                              preprocessor=self.extract_tiles,
                              parser=video_parser,
                              creator=self.create_npo_item,
                              requires_logon=True)

        # Alpha listing based on JSON API
        # self._add_data_parser("https://start-api.npo.nl/page/catalogue", json=True,
        self._add_data_parser("https://start-api.npo.nl/media/series", json=True,
                              parser=["items"],
                              creator=self.create_json_episode_item,
                              preprocessor=self.extract_api_pages)

        # New API endpoints:
        # https://start-api.npo.nl/epg/2018-12-22?type=tv
        # https://start-api.npo.nl/page/catalogue?az=C&pageSize=1000
        # https://start-api.npo.nl/page/catalogue?pageSize=0
        # https://start-api.npo.nl/page/catalogue?pageSize=500
        # https://start-api.npo.nl/search?query=sinterklaas&pageSize=1000

        tv_guide_regex = r'data-channel="(?<channel>[^"]+)"[^>]+data-title="(?<title>[^"]+)"[^>]+' \
                         r'data-id=\'(?<url>[^\']+)\'[^>]*>\W*<div[^>]*>\W+<p>\W+<span[^>]+time"' \
                         r'[^>]*>(?<hours>\d+):(?<minutes>\d+)</span>\W+<span[^<]+</span>\W+<span ' \
                         r'class="npo-epg-active"></span>\W+<span class="npo-epg-play"></span>'
        tv_guide_regex = Regexer.from_expresso(tv_guide_regex)
        self._add_data_parser("https://www.npostart.nl/gids?date=",
                              parser=tv_guide_regex, creator=self.create_tv_guide_item)

        self.__ignore_cookie_law()

        # ===============================================================================================================
        # non standard items
        self.__NextPageAdded = False
        self.__jsonApiKeyHeader = {"apikey": "07896f1ee72645f68bc75581d7f00d54"}
        self.__useJson = True
        self.__pageSize = 50
        self.__max_page_count = 10
        self.__has_premium_cache = None
        self.__timezone = pytz.timezone("Europe/Amsterdam")

        # use a dictionary so the lookup is O(1)
        self.__channel_name_map = {
            "_101_": None,  # "NPO1 Extra", -> Mainly paid
            "CULT": None,   # "NPO2 Extra", -> Mainly paid
            "OPVO": None,   # "NPO Zappelin", -> Mainly paid
            "NOSJ": None,   # "NPO Nieuws" -> Cannot be played
            "_mcr_": None,  # "NPO Politiek" -> Niet gevonden
            "PO24": None,   # Cannot be played,
            "NED1": "NPO 1",
            "NED2": "NPO 2",
            "NED3": "NPO 3",
        }

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def log_on(self):
        return self.__log_on(False)

    def __log_on(self, force_log_off=False):
        """ Makes sure that we are logged on. """

        username = self._get_setting("username")
        previous_name = AddonSettings.get_channel_setting(self, "previous_username", store=LOCAL)
        log_out = previous_name != username
        if log_out or force_log_off:
            if log_out:
                Logger.info("Username changed for NPO from '%s' to '%s'", previous_name, username)
            else:
                Logger.info("Forcing a new login for NPO")
            UriHandler.delete_cookie(domain="www.npostart.nl")
            UriHandler.delete_cookie(domain=".npostart.nl")
            AddonSettings.set_channel_setting(self, "previous_username", username, store=LOCAL)

        if not username:
            Logger.info("No user name for NPO, not logging in")
            UriHandler.delete_cookie(domain="www.npostart.nl")
            return True

        cookie = UriHandler.get_cookie("isAuthenticatedUser", "www.npostart.nl")
        if cookie and not log_out:
            expire_date = DateHelper.get_date_from_posix(float(cookie.expires))
            Logger.info("Found existing valid NPO token (valid until: %s)", expire_date)
            return True

        v = Vault()
        password = v.get_channel_setting(self.guid, "password")
        if not bool(password):
            Logger.warning("No password found for %s", self)
            return False

        # Will redirect to the new id.npo.nl site with a return url given.
        data = UriHandler.open("https://www.npostart.nl/login", no_cache=True)

        # Find the return url.
        if "ReturnUrl" in UriHandler.instance().status.url:
            redirect_url = UriHandler.instance().status.url.split("ReturnUrl=")[-1]
            redirect_url = HtmlEntityHelper.url_decode(redirect_url)
        else:
            redirect_url = ""

        # Extract the verification token.
        verification_code = Regexer.do_regex(r'name="__RequestVerificationToken"[^>]+value="([^"]+)"', data)
        data = {
            "EmailAddress": username,
            "Password": password,
            "ReturnUrl": redirect_url,
            "__RequestVerificationToken": verification_code
        }

        # The actual call for logging in.
        UriHandler.open("https://id.npo.nl/account/login", no_cache=True, data=data)

        # The callback url to finish up.
        UriHandler.open("https://id.npo.nl{}".format(redirect_url), no_cache=True)
        return not UriHandler.instance().status.error

    def extract_tiles(self, data):  # NOSONAR
        """ Extracts the JSON tiles data from the HTML.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        new_data = ""

        json_data = JsonHelper(data)
        tiles = json_data.get_value("tiles")
        if not isinstance(tiles, (tuple, list)):
            Logger.debug("Found single tile data blob")
            new_data = tiles
        else:
            Logger.debug("Found multiple tile data blobs")
            for item_data in tiles:
                new_data = "%s%s\n" % (new_data, item_data)

        # More pages?
        max_count = 5
        current_count = 1
        next_page = json_data.get_value("nextLink")
        query_string = self.parentItem.url.split("&", 1)[-1]

        http_headers = {"X-Requested-With": "XMLHttpRequest"}
        http_headers.update(self.parentItem.HttpHeaders)
        http_headers.update(self.httpHeaders)
        while next_page and current_count < max_count:
            current_count += 1
            Logger.debug("Found next page: %s", next_page)
            if next_page.startswith("/search/extended") or next_page.startswith("/media/series"):
                next_page = next_page.split("&", 1)[0]
                next_page = "%s%s&%s" % (self.baseUrlLive, next_page, query_string)
            elif not next_page.startswith("http"):
                next_page = "%s%s&%s" % (self.baseUrlLive, next_page, query_string)
            else:
                next_page = "%s&%s" % (next_page, query_string)

            page_data = UriHandler.open(next_page, additional_headers=http_headers)
            json_data = JsonHelper(page_data)
            tiles = json_data.get_value("tiles")
            if not isinstance(tiles, (tuple, list)):
                Logger.debug("Found single tile data blob")
                new_data = "%s%s\n" % (new_data, tiles)
            else:
                Logger.debug("Found multiple tile data blobs")
                for item_data in tiles:
                    new_data = "%s%s\n" % (new_data, item_data)
            next_page = json_data.get_value("nextLink")

        if next_page and current_count == max_count:
            # There are more pages
            if next_page.startswith("/search/extended") or next_page.startswith("/media/series"):
                next_page = next_page.split("&", 1)[0]
                next_page = "%s%s&%s" % (self.baseUrlLive, next_page, query_string)
            elif not next_page.startswith("http"):
                next_page = "%s%s&%s" % (self.baseUrlLive, next_page, query_string)
            else:
                next_page = "%s&%s" % (next_page, query_string)

            title = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
            title = "\a.: %s :." % (title,)
            more = FolderItem(
                title, next_page, self.parentItem.content_type, self.parentItem.media_type)
            more.HttpHeaders = http_headers
            more.HttpHeaders.update(self.parentItem.HttpHeaders)
            items.append(more)

        return new_data, items

    def get_initial_folder_items(self, data):
        """ Creates the initial folder items for this channel.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        search = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.Search), "searchSite",
            content_type=contenttype.EPISODES)
        search.complete = True
        search.dontGroup = True
        search.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        items.append(search)

        # Favorite items that require login
        favs = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.FavouritesId),
            "https://www.npostart.nl/api/account/@me/profile",
            content_type=contenttype.NONE)
        favs.complete = True
        favs.description = "Favorieten van de NPO.nl website. Het toevoegen van favorieten " \
                           "wordt nog niet ondersteund."
        favs.dontGroup = True
        favs.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        items.append(favs)

        extra = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.LiveRadio),
            "https://start-api.npo.nl/page/live",
            content_type=contenttype.SONGS)
        extra.complete = True
        extra.dontGroup = True
        extra.isLive = True
        extra.HttpHeaders = self.__jsonApiKeyHeader
        items.append(extra)

        extra = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.LiveTv),
            "%s/live" % (self.baseUrlLive,),
            content_type=contenttype.VIDEOS)
        extra.complete = True
        extra.dontGroup = True
        extra.isLive = True
        items.append(extra)

        extra = FolderItem(
            "{} ({})".format(
                LanguageHelper.get_localized_string(LanguageHelper.TvShows),
                LanguageHelper.get_localized_string(LanguageHelper.FullList)
            ),
            "https://start-api.npo.nl/media/series?pageSize={}&dateFrom=2014-01-01".format(self.__pageSize),
            # "https://start-api.npo.nl/page/catalogue?pageSize={}".format(self.__pageSize),
            content_type=contenttype.TVSHOWS
        )
        extra.complete = True
        extra.dontGroup = True
        extra.description = "Volledige programma lijst van NPO Start."
        extra.HttpHeaders = self.__jsonApiKeyHeader
        # API Key from here: https://packagist.org/packages/kro-ncrv/npoplayer?q=&p=0&hFR%5Btype%5D%5B0%5D=concrete5-package
        items.append(extra)

        extra = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.Genres),
            "https://www.npostart.nl/programmas",
            content_type=contenttype.VIDEOS)
        extra.complete = True
        extra.dontGroup = True
        items.append(extra)

        extra = FolderItem(
            "{} (A-Z)".format(LanguageHelper.get_localized_string(LanguageHelper.TvShows)),
            "#alphalisting",
            content_type=contenttype.TVSHOWS)
        extra.complete = True
        extra.description = "Alfabetische lijst van de NPO.nl site."
        extra.dontGroup = True
        items.append(extra)

        recent = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.Recent), "#recent",
            content_type=contenttype.EPISODES)
        recent.complete = True
        recent.dontGroup = True
        items.append(recent)

        return data, items

    def add_recent_items(self, data):
        """ Builds the "Recent" folder for this channel.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        today = datetime.datetime.now() - datetime.timedelta(hours=5)
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

            # url = "https://www.npostart.nl/media/series?page=1&dateFrom=%04d-%02d-%02d&tileMapping=normal&tileType=teaser&pageType=catalogue" % \
            if self.__useJson:
                url = "https://start-api.npo.nl/epg/%04d-%02d-%02d?type=tv" % \
                      (air_date.year, air_date.month, air_date.day)
            else:
                url = "https://www.npostart.nl/gids?date=%04d-%02d-%02d&type=tv" % \
                      (air_date.year, air_date.month, air_date.day)
            extra = FolderItem(title, url, content_type=contenttype.EPISODES)
            extra.complete = True
            extra.dontGroup = True
            if self.__useJson:
                extra.HttpHeaders = self.__jsonApiKeyHeader
            else:
                extra.HttpHeaders["X-Requested-With"] = "XMLHttpRequest"
            extra.HttpHeaders["Accept"] = "text/html, */*; q=0.01"
            extra.set_date(air_date.year, air_date.month, air_date.day, text="")

            items.append(extra)

        return data, items

    def get_additional_live_items(self, data):
        """ Adds some missing live items to the list of live items.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Processing Live items")

        items = []
        if self.parentItem.url.endswith("/live"):
            # let's add the 3FM live stream
            parent = self.parentItem

            live_streams = {
                "3FM Live": {
                    "url": "http://e.omroep.nl/metadata/LI_3FM_300881",
                    "thumb": self.get_image_location("3fm-artwork.jpg")
                },
                "Radio 2 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RADIO2_300879",
                    "thumb": self.get_image_location("radio2image.jpg")
                    # "thumb": "http://www.radio2.nl/image/rm/48254/NPO_RD2_Logo_RGB_1200dpi.jpg?width=848&height=477"
                },
                "Radio 1 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RADIO1_300877",
                    # "thumb": "http://statischecontent.nl/img/tweederdevideo/1e7db3df-030a-4e5a-b2a2-840bd0fd8242.jpg"
                    "thumb": self.get_image_location("radio1image.jpg")
                },
                "Radio 4 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RA4_698901",
                    "thumb": self.get_image_location("radio4image.jpg")
                },
                "FunX": {
                    "url": "http://e.omroep.nl/metadata/LI_3FM_603983",
                    "thumb": self.get_image_location("funx.jpg")
                }
            }

            for stream in live_streams:
                Logger.debug("Adding video item to '%s' sub item list: %s", parent, stream)
                live_data = live_streams[stream]
                item = MediaItem(stream, live_data["url"], mediatype.VIDEO)
                item.icon = parent.icon
                item.thumb = live_data["thumb"]
                item.isLive = True
                item.complete = False
                items.append(item)
        return data, items

    def extract_json_for_live_radio(self, data):
        """ Extracts the JSON data from the HTML for the radio streams

        @param data: the HTML data
        @return:     a valid JSON string and no items

        """

        items = []
        data = Regexer.do_regex(r'NPW.config.channels\s*=\s*([\w\W]+?);\s*NPW\.config\.comscore', data)[-1].rstrip(";")
        # fixUp some json
        data = re.sub(r'(\w+):([^/])', '"\\1":\\2', data)
        Logger.trace(data)
        return data, items

    def alpha_listing(self, data):
        """ Creates a alpha listing with items pointing to the alpha listing on line.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Generating an Alpha list for NPO")

        items = []
        # https://www.npostart.nl/media/series?page=1&dateFrom=2014-01-01&tileMapping=normal&tileType=teaser
        # https://www.npostart.nl/media/series?page=2&dateFrom=2014-01-01&az=A&tileMapping=normal&tileType=teaser
        # https://www.npostart.nl/media/series?page=2&dateFrom=2014-01-01&az=0-9&tileMapping=normal&tileType=teaser
        # https://start-api.npo.nl/media/series?az=0-9&pageSize=200

        title_format = LanguageHelper.get_localized_string(LanguageHelper.StartWith)
        url_format = "https://www.npostart.nl/media/series?page=1&dateFrom=2014-01-01&az=%s&tileMapping=normal&tileType=teaser&pageType=catalogue"
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0":
            if char == "0":
                char = "0-9"
            sub_item = FolderItem(
                title_format % (char,), url_format % (char,),
                content_type=contenttype.TVSHOWS)
            sub_item.complete = True
            sub_item.dontGroup = True
            sub_item.content_type = contenttype.TVSHOWS
            sub_item.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
            items.append(sub_item)
        return data, items

    def create_profile_item(self, result_set):
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
        item.metaData["id"] = result_set["id"]
        return item

    def switch_profile(self, data):
        """ Switches to the selected profile.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        profile_id = self.parentItem.metaData.get("id", None)
        if not profile_id:
            return data, items

        profile_data = {"id": profile_id, "pinCode": ""}

        xsrf_token = self.__get_xsrf_token()
        UriHandler.open("https://www.npostart.nl/api/account/@me/profile/switch",
                        data=profile_data,
                        additional_headers={
                            "X-Requested-With": "XMLHttpRequest",
                            "X-XSRF-TOKEN": xsrf_token,
                            "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
                        })

        # Add the episodes/tvshows
        epsisodes = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.Episodes),
            "https://www.npostart.nl/ums/accounts/@me/favourites/episodes?page=1&dateFrom=2014-01-01&tileMapping=dedicated&tileType=asset",
            content_type=contenttype.EPISODES)
        items.append(epsisodes)

        tvshows = FolderItem(
            LanguageHelper.get_localized_string(LanguageHelper.TvShows),
            "https://www.npostart.nl/ums/accounts/@me/favourites?page=1&type=series&tileMapping=normal&tileType=teaser",
            content_type=contenttype.TVSHOWS)
        items.append(tvshows)
        return data, items

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        item = chn_class.Channel.create_episode_item(self, result_set)
        if not item:
            return None

        # Update the URL
        item.url = self.__get_url_for_pom(result_set["powid"])
        if self.__useJson:
            item.HttpHeaders = self.__jsonApiKeyHeader
        else:
            item.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        item.dontGroup = True
        item.content_type = contenttype.EPISODES
        return item

    def create_json_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        if not result_set:
            return None

        # if we should not use the mobile listing and we have a non-mobile ID)
        if 'id' in result_set:
            url = self.__get_url_for_pom(result_set['id'])
        else:
            Logger.warning("Skipping (no '(m)id' ID): %(title)s", result_set)
            return None

        name = result_set['title']
        description = result_set.get('description', '')

        item = FolderItem(name, url, media_type=mediatype.TVSHOW, content_type=contenttype.EPISODES)
        item.complete = True
        item.description = description
        if self.__useJson:
            item.HttpHeaders = self.__jsonApiKeyHeader
        else:
            item.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        # This should always be a full list as we already have a default alphabet listing available
        # from NPO
        item.dontGroup = True

        if "images" not in result_set:
            return item

        images = result_set["images"]
        for image_type, image_data in images.items():
            if image_type == "original" and "tv" in image_data["formats"]:
                item.fanart = image_data["formats"]["tv"]["source"]
            elif image_type == "grid.tile":
                item.thumb = image_data["formats"]["tv"]["source"]

        return item

    # noinspection PyUnusedLocal
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

        # The Videos
        url = "https://www.npostart.nl/search/extended?page=1&query=%s&filter=episodes&dateFrom=2014-01-01&tileMapping=search&tileType=asset&pageType=search"

        # The Shows
        # url = "https://www.npostart.nl/search/extended?page=1&query=%s&filter=programs&dateFrom=2014-01-01&tileMapping=normal&tileType=teaser&pageType=search"

        self.httpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        return chn_class.Channel.search_site(self, url)

    def create_tv_guide_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

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

        Logger.trace(result_set)
        channel = result_set["channel"].replace("NED", "NPO ")
        title = "{0[hours]}:{0[minutes]} - {1} - {0[title]}".format(result_set, channel)
        item = MediaItem(title, result_set["url"], media_type=mediatype.EPISODE)
        item.description = result_set["channel"]
        item.HttpHeaders = self.httpHeaders
        item.complete = False
        return item

    def create_npo_item(self, result_set):
        """ Creates a generic NPO MediaItem of type 'video' using the result_set from the regex.

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

        item = chn_class.Channel.create_video_item(self, result_set)

        # set the POW id based on either video of folder:
        # This no longer works. Assuming video for now.
        if "npo-asset-tile-timer" in result_set["videoDetection"]:
            item.media_type = mediatype.EPISODE
            item.url = result_set["powid"]
        else:
            item.media_type = mediatype.TVSHOW
            item.content_type = contenttype.EPISODES
            item.url = "https://www.npostart.nl/media/series/%(powid)s/episodes?page=1&tileMapping=dedicated&tileType=asset&pageType=franchise" % result_set
            item.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        item.isPaid = "premium" in result_set["class"]

        # figure out the date
        try:
            date_time = result_set["subtitle"].strip().replace("  ", " ").split(" ")
            date_premium = result_set["datePremium"]

            # For #933 we check for NOS Journaal
            if ":" in date_time[-1] and item.name == "NOS Journaal":
                item.name = "{0} - {1}".format(item.name, date_time[-1])

            if self.__determine_date_time_for_npo_item(item, date_time, date_premium):
                # We don't need the subtitle as it contained the date
                # item.name = result_set["title"]   # won't work when sorting by name
                Logger.trace("Date found in subtitle: %s", result_set.get("subtitle"))

        except:
            Logger.debug("Cannot set date from label: %s", result_set.get("subtitle"), exc_info=True)
            # 2016-07-05T00:00:00Z
            date_value = result_set.get("date")
            if date_value:
                time_stamp = DateHelper.get_date_from_string(date_value, "%Y-%m-%dT%H:%M:%SZ")
                item.set_date(*time_stamp[0:6])
            else:
                Logger.warning("Cannot set date from 'data-from': %s", result_set["date"],
                               exc_info=True)

        return item

    def process_franchise_page(self, data):
        """ Prepares the main folder for a show.

        Lists the most recent episodes as shown on the website and app, and adds
        folders for "Extra's" and "Fragmenten".

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        has_more_episodes = False
        has_extras = False
        has_fragments = False

        data = JsonHelper(data)
        # Create a list of episodes for the next processing step
        data.json["items"] = []

        # Parse the franchise JSON to find out which components are available
        for component in data.get_value("components"):
            Logger.debug(list(component.keys()))
            if component["id"] in ("lane-last-published", "grid-episodes"):
                # The most recent episodes, or the latest season
                data.json["items"] += component["data"]["items"]
                if "filter" in component and component["filter"] is not None:
                    # There is a season filter, so there may be more episodes
                    has_more_episodes = True
                if component["data"]["_links"] is not None and "next" in component["data"]["_links"]:
                    # There is a link to the next page with more episodes
                    has_more_episodes = True
            elif component["id"] == "grid-clips":
                # There is an "Extra's" tab
                has_extras = True
            elif component["id"] == "grid-fragments":
                # There is a "Fragmenten" tab
                has_fragments = True

        # Obtain the POM ID for this show
        pom = Regexer.do_regex(r'https://start-api.npo.nl/page/franchise/([^/?]+)',
                               self.parentItem.url)[0]

        # Generate folders for episodes, extras, and fragments
        links = [(LanguageHelper.AllEpisodes, "episodes", has_more_episodes),
                 (LanguageHelper.Extras, "clips", has_extras),
                 (LanguageHelper.Fragments, "fragments", has_fragments)]

        for (title, path, available) in links:
            if available:
                url = 'https://start-api.npo.nl/media/series/%s/%s?pageSize=50' % (pom, path)
                Logger.debug("Adding link to %s: %s", path, url)
                title = LanguageHelper.get_localized_string(title)
                item = FolderItem("\a.: %s :." % title, url, content_type=contenttype.EPISODES)
                item.complete = True
                item.HttpHeaders = self.__jsonApiKeyHeader
                item.dontGroup = True
                items.append(item)

        return data, items

    def extract_api_pages(self, data):
        """ Extracts the JSON tiles data from the HTML.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """
        items = []

        data = JsonHelper(data)
        next_url = data.get_value("_links", "next", "href")
        Logger.debug("Retrieving a total of %s items", data.get_value("total"))

        if not next_url:
            return data, items

        # We will just try to download all items.
        for _ in range(0, self.__max_page_count - 1):
            page_data = UriHandler.open(next_url, additional_headers=self.parentItem.HttpHeaders)
            page_json = JsonHelper(page_data)
            page_items = page_json.get_value("items")
            if page_items:
                data.json["items"] += page_items
            next_url = page_json.get_value("_links", "next", "href")
            if not next_url:
                break

        if next_url:
            next_title = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
            item = FolderItem("\b.: {} :.".format(next_title), next_url, content_type=contenttype.EPISODES)
            item.complete = True
            item.HttpHeaders = self.__jsonApiKeyHeader
            item.dontGroup = True
            items.append(item)

        return data, items

    def create_api_video_item(self, result_set, for_epg=False):
        """ Creates a MediaItem of type 'video' using the result_set from the API calls:

        - https://start-api.npo.nl/media/series/{POM_ID}/episodes
        - https://start-api.npo.nl/page/franchise/{POM_ID}

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict[str,Any] result_set:    The result_set of the self.episodeItemRegex
        :param bool for_epg:                Use this item in an EPG listing

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        
        name = self.__get_name_for_api_video(result_set, for_epg)
        description = result_set.get('descriptionLong')
        if not description:
            description = result_set.get('description')
        video_id = result_set['id']
        if video_id is None:
            return None

        item = MediaItem(name, video_id, media_type=mediatype.EPISODE)
        item.description = description

        season = result_set.get("seasonNumber")
        episode = result_set.get("episodeNumber")

        # Check for seasons but don't add then for EPG
        if bool(season) and bool(episode) and season < 100 and not for_epg:
            item.set_season_info(season, episode)
            # TODO: setting it now is to messy. Perhaps we should make it configurable?
            # item.name = "s{0:02d}e{1:02d} - {2}".format(season, episode, item.name)

        date_format = "%Y-%m-%dT%H:%M:%SZ"
        date = result_set.get('broadcastDate')
        if date:
            # The dates are in UTC, so we need to calculate the actual
            # time and take the DST in consideration for each item.
            date_time = DateHelper.get_datetime_from_string(
                date, date_format=date_format, time_zone="UTC")
            date_time = date_time.astimezone(self.__timezone)

            if for_epg:
                item.name = "{:02}:{:02} - {}".format(
                    date_time.hour, date_time.minute, item.name)
            else:
                item.set_date(date_time.year, date_time.month, date_time.day,
                              date_time.hour, date_time.minute, date_time.second)

            # For #933 we check for NOS Journaal
            if item.name == "NOS Journaal":
                item.name = "{2} - {0:02d}:{1:02d}".format(date_time.hour, date_time.minute, item.name)

        item.isPaid = result_set.get("isOnlyOnNpoPlus", False)
        availability = result_set.get("availability")
        if not item.isPaid and availability and availability["to"] and availability["to"] != availability["from"]:
            to_date = DateHelper.get_date_from_string(availability["to"], date_format=date_format)
            to_datetime = datetime.datetime(*to_date[:6])
            item.isPaid = to_datetime < datetime.datetime.now()

        item.set_info_label("duration", result_set['duration'])

        images = result_set["images"]
        for image_type, image_data in images.items():
            if image_type == "original" and "original" in image_data["formats"]:
                continue
                # No fanart for now.
                # item.fanart = image_data["formats"]["original"]["source"]
            elif image_type == "grid.tile":
                item.thumb = image_data["formats"]["web"]["source"]

        region_restrictions = result_set.get('regionRestrictions', [])
        # The PLUSVOD:EU is not a regional restriction as it seems (See #1392)
        item.isGeoLocked = any([r for r in region_restrictions if r != "PLUSVOD:EU"])
        return item

    def extract_epi_epg_items(self, data):
        """ Extracts the EPG items and wraps them in a JSON Helper objecgt.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        json = JsonHelper(data)
        epg_data = []

        for channel_epg in json.get_value("epg"):
            # Find the channel name
            channel = channel_epg["channel"]
            channel_name = channel["channel"]

            # Update all videos that don't have a channel specified
            epg_items = channel_epg.get("schedule", [])
            [e["program"].update({"channel": channel_name}) for e in epg_items if not e["program"]["channel"]]
            epg_data += epg_items

        json.json = epg_data
        return json, []

    def create_api_epg_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the API calls:

        - https://start-api.npo.nl/media/series/{POM_ID}/episodes
        - https://start-api.npo.nl/page/franchise/{POM_ID}

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict[str,dict[str,str]] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        epg_result_set = result_set["program"]

        # Check to see if the channel name needs updating. We check the mapping, if it is not
        # in the mapping, the channel name stays the same.
        # If the result from the mapping is None (or the channel name is None) filter them.
        channel_name = epg_result_set["channel"]
        channel_name = self.__channel_name_map.get(channel_name, channel_name)
        if channel_name is None:
            Logger.trace("Invalid EPG channel: %s", channel_name)
            return None

        epg_result_set["channel"] = channel_name
        epg_result_set["broadcastDate"] = result_set.get("startsAt", epg_result_set["broadcastDate"])
        item = self.create_api_video_item(epg_result_set, for_epg=True)

        return item

    def create_video_item_json(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

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

        Logger.trace(result_set)

        # In some cases the name, posix and description are in the root, in other cases in the
        # 'episode' node
        posix = result_set.get('starts_at')
        image = result_set.get('image')
        name = result_set.get('name')
        description = result_set.get('description', '')

        # the tips has an extra 'episodes' key
        if 'episode' in result_set:
            Logger.debug("Found subnode: episodes")
            # set to episode node
            data = result_set['episode']
        else:
            Logger.warning("No subnode 'episodes' found, trying anyways")
            data = result_set

        # look for better values
        posix = data.get('broadcasted_at', posix)
        # noinspection PyTypeChecker
        broadcasted = DateHelper.get_date_from_posix(posix)
        description = result_set.get('description', description)
        video_id = data.get('whatson_id')

        # try to fetch more name data
        names = []
        name = data.get("name", name)
        if name:
            names = [name, ]
        if "series" in data and "name" in data["series"]:
            # noinspection PyTypeChecker
            names.insert(0, data["series"]["name"])

        # Filter the duplicates
        title = " - ".join(set(names))

        item = MediaItem(title, video_id, media_type=mediatype.EPISODE)
        item.complete = False
        item.description = description

        images = data.get('stills')
        if images:
            # there were images in the stills
            # noinspection PyTypeChecker
            item.thumb = images[-1]['url']
        elif image:
            # no stills, or empty, check for image
            item.thumb = image

        item.set_date(broadcasted.year, broadcasted.month, broadcasted.day, broadcasted.hour,
                      broadcasted.minute,
                      broadcasted.second)

        return item

    def create_genre_item(self, result_set):
        """ Creates a MediaItem for a genre of type 'folder' using the result_set from the regex.

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

        Logger.trace(result_set)

        url = "https://www.npostart.nl/media/collections/%s?page=1&tileMapping=normal&tileType=asset&pageType=collection" % (result_set[0],)
        item = FolderItem(result_set[1], url, content_type=contenttype.TVSHOWS)
        item.HttpHeaders["X-Requested-With"] = "XMLHttpRequest"
        item.complete = True
        return item

    def create_live_tv(self, result_set):
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

        Logger.trace("Content = %s", result_set)

        # first regex matched -> video channel
        channel_id = result_set[0]
        if channel_id == "<exception>":
            name = "NPO 3"
        else:
            name = result_set[0].replace("-", " ").title().replace("Npo", "NPO")

        now_playing = result_set[2]
        next_up = result_set[3]
        name = "%s: %s" % (name, now_playing)
        if next_up:
            next_up = next_up.strip()
            next_up = next_up.replace("Straks: ", "")
            description = "Nu: %s\nStraks om %s" % (now_playing, next_up)
        else:
            description = "Nu: %s" % (result_set[3].strip(),)

        item = MediaItem(name, "%s/live/%s" % (self.baseUrlLive, result_set[0]), media_type=mediatype.VIDEO)
        item.description = description

        if result_set[1].startswith("http"):
            item.thumb = result_set[1].replace("regular_", "").replace("larger_", "")
        elif result_set[1].startswith("//"):
            item.thumb = "http:%s" % (result_set[1].replace("regular_", "").replace("larger_", ""),)
        else:
            item.thumb = "%s%s" % (self.baseUrlLive, result_set[1].replace("regular_", "").replace("larger_", ""))

        item.complete = False
        item.isLive = True
        return item

    def create_live_radio(self, result_set):
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
        result_set = result_set["channel"]

        name = result_set["name"]
        if name == "demo":
            return None

        url = "%s/live/%s" % (self.baseUrlLive, result_set["slug"])
        item = MediaItem(name, url, media_type=mediatype.VIDEO)
        item.isLive = True
        item.complete = False

        data = result_set.get("liveStream")
        # see if there is a video stream.
        if data:
            video = data.get("visualRadioAsset")
            if video:
                item.metaData["live_pid"] = video

        return item

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

        if "/radio/" in item.url or "/live/" in item.url or "/LI_" in item.url:
            Logger.info("Updating Live item: %s", item.url)
            return self.update_video_item_live(item)

        whatson_id = item.url
        return self.__update_video_item(item, whatson_id)

    def update_from_poms(self, item):
        """ Updates an existing MediaItem with more data based on the POMS Id.

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

        poms = item.url.split("/")[-1]
        return self.__update_video_item(item, poms)

    def update_video_item_live(self, item):
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

        mp3_urls = Regexer.do_regex("""data-streams='{"url":"([^"]+)","codec":"[^"]+"}'""", html_data)
        if len(mp3_urls) > 0:
            Logger.debug("Found MP3 URL")
            item.add_stream(mp3_urls[0], 192)
        else:
            Logger.debug("Finding the actual metadata url from %s", item.url)
            # NPO3 normal stream had wrong subs
            if "npo-3" in item.url and False:
                # NPO3 has apparently switched the normal and hearing impaired streams?
                json_urls = Regexer.do_regex('<div class="video-player-container"[^>]+data-alt-prid="([^"]+)"', html_data)
            else:
                json_urls = Regexer.do_regex('<npo-player[^-][^>]*media-id="([^"]+)"', html_data)

            for episode_id in json_urls:
                return self.__update_video_item(item, episode_id, False)

            Logger.warning("Cannot update live item: %s", item)
            return item

        item.complete = True
        return item

    def create_iptv_streams(self, parameter_parser):
        """ Fetch the available live channels using EPG endpoint and format them into JSON-STREAMS

        :param ActionParser parameter_parser: a ActionParser object to is used to parse and
                                                   create urls

        :return: Formatted stations
        :rtype: list
        """
        epg_url = datetime.datetime.now().strftime("https://start-api.npo.nl/epg/%Y-%m-%d?type=tv")
        epg_data = UriHandler.open(epg_url,
            no_cache=True,
            additional_headers=self.__jsonApiKeyHeader)
        epg = JsonHelper(epg_data)

        parent_item = MediaItem("Live", "https://www.npostart.nl/live", media_type=mediatype.FOLDER)
        items = []
        iptv_streams = []

        for stations in epg.get_value("epg"):
            livestream = JsonHelper.get_from(stations, "channel", "liveStream")
            item = MediaItem(JsonHelper.get_from(livestream, "title"), JsonHelper.get_from(livestream, "shareUrl"), media_type=mediatype.VIDEO)
            item.isLive = True
            item.isGeoLocked = True
            items.append(item)

            iptv_streams.append(dict(
                id=JsonHelper.get_from(livestream,"id"),
                name=JsonHelper.get_from(livestream,"title"),
                logo=JsonHelper.get_from(livestream,"images","original","formats","tv","source"),
                group=self.channelName,
                stream=parameter_parser.create_action_url(self, action=action.PLAY_VIDEO, item=item, store_id=parent_item.guid),
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

        parent = MediaItem("EPG", "https://start-api.npo.nl/epg/", media_type=mediatype.FOLDER)
        iptv_epg = dict()
        media_items = []

        start = datetime.datetime.now() - datetime.timedelta(days=3)
        for i in range(0, 7, 1):
            air_date = start + datetime.timedelta(i)
            data = UriHandler.open(air_date.strftime("https://start-api.npo.nl/epg/%Y-%m-%d?type=tv"),
                no_cache=True,
                additional_headers=self.__jsonApiKeyHeader)

            json_data = JsonHelper.loads(data)
            for epg_item in JsonHelper.get_from(json_data,"epg"):
                id = JsonHelper.get_from(epg_item,"channel",'liveStream','id')
                iptv_epg[id]=iptv_epg.get(id, [])
                for program in JsonHelper.get_from(epg_item,"schedule"):
                    media_item = MediaItem(JsonHelper.get_from(program,"program","title"), JsonHelper.get_from(program,"program","id"), media_type=mediatype.EPISODE)
                    region_restrictions = JsonHelper.get_from(program, "program", "regionRestrictions")
                    media_item.isGeoBlocked = any([r for r in region_restrictions if r != "PLUSVOD:EU"])
                    media_items.append(media_item)
                    iptv_epg[id].append(dict(
                        start=JsonHelper.get_from(program, "startsAt"),
                        stop=JsonHelper.get_from(program, "endsAt"),
                        title=JsonHelper.get_from(program, "program", "title"),
                        description=JsonHelper.get_from(program, "program","descriptionLong"),
                        image=JsonHelper.get_from(program, "program", "images", "header", "formats", "tv", "source"),
                        genre=JsonHelper.get_from(program, "program", "genres", 0, "terms"),
                        stream=parameter_parser.create_action_url(self, action=action.PLAY_VIDEO, item=media_item, store_id=parent.guid),
                    ))
        parameter_parser.pickler.store_media_items(parent.guid, parent, media_items)
        return iptv_epg

    def __has_premium(self):
        if self.__has_premium_cache is None:
            subscription_cookie = UriHandler.get_cookie("subscription", "www.npostart.nl")
            if subscription_cookie:
                self.__has_premium_cache = subscription_cookie.value == "npoplus"
                if self.__has_premium_cache:
                    Logger.debug("NPO Plus account, so all items can be played.")
            else:
                self.__has_premium_cache = False

        return self.__has_premium_cache

    def __update_video_item(self, item, episode_id, fetch_subtitles=True):
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
            sub_title_url = "https://assetscdn.npostart.nl/subtitles/original/nl/%s.vtt" % (episode_id,)
            sub_title_path = subtitlehelper.SubtitleHelper.download_subtitle(
                sub_title_url, episode_id + ".nl.srt", format='srt')

            if not sub_title_path:
                sub_title_url = "https://rs.poms.omroep.nl/v1/api/subtitles/%s/nl_NL/CAPTION.vtt" % (episode_id,)
                sub_title_path = subtitlehelper.SubtitleHelper.download_subtitle(
                    sub_title_url, episode_id + ".nl.srt", format='srt')

            if sub_title_path:
                item.subtitle = sub_title_path

        if AddonSettings.use_adaptive_stream_add_on(
                with_encryption=True, ignore_add_on_config=True):
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

    def __ignore_cookie_law(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        UriHandler.set_cookie(name='site_cookie_consent', value='yes',
                              domain='.www.uitzendinggemist.nl')
        UriHandler.set_cookie(name='npo_cc', value='tmp', domain='.www.uitzendinggemist.nl')

        UriHandler.set_cookie(name='site_cookie_consent', value='yes', domain='.npo.nl')
        UriHandler.set_cookie(name='npo_cc', value='30', domain='.npo.nl')

        UriHandler.set_cookie(name='site_cookie_consent', value='yes', domain='.npostart.nl')
        UriHandler.set_cookie(name='npo_cc', value='30', domain='.npostart.nl')
        return

    def __get_url_for_pom(self, pom):
        if self.__useJson:
            url = "https://start-api.npo.nl/page/franchise/{0}".format(pom)
            # The Franchise URL will give use seasons
            # url = "https://start-api.npo.nl/page/franchise/{0}".format(result_set['id'])
        else:
            url = "https://www.npostart.nl/media/series/{0}/episodes?page=1" \
                  "&tileMapping=dedicated&tileType=asset&pageType=franchise".format(pom)
        return url

    def __determine_date_time_for_npo_item(self, item, date_time, date_premium):
        """

        :param MediaItem item:              The current item.
        :param list[str|int] date_time:     The date time string items.
        :param str date_premium:            The premium start date that we use to get the year from.

        :return: whether the date time was found
        :rtype: True

        """

        if date_premium:
            date_premium = DateHelper.get_date_from_string(date_premium, "%Y-%m-%dT%H:%M:%SZ")

        Logger.trace("Date Parts: %s", date_time)

        if date_time[-2].lower() == "gisteren":
            date_time = datetime.datetime.now() + datetime.timedelta(days=-1)
            item.set_date(date_time.year, date_time.month, date_time.day)
        elif date_time[-2].lower() == "vandaag":
            date_time = datetime.datetime.now()
            item.set_date(date_time.year, date_time.month, date_time.day)
        elif ":" in date_time[-1]:
            if date_time[-2].isalpha():
                year = date_premium.tm_year if date_premium else datetime.datetime.now().year
                date_time.insert(-1, year)

            # For #933 we check for NOS Journaal
            if item.name.startswith("NOS Journaal"):
                item.name = "{0} - {1}".format(item.name, date_time[-1])
            year = int(date_time[-2])

            month = DateHelper.get_month_from_name(date_time[-3], language="nl")
            day = int(date_time[-4])

            stamp = datetime.datetime(year, month, day)
            if stamp > datetime.datetime.now():
                year -= 1
            item.set_date(year, month, day)
        else:
            # there is an actual date present
            if date_time[0].isalpha():
                # first part is ma/di/wo/do/vr/za/zo
                date_time.pop(0)

            # translate the month
            month = DateHelper.get_month_from_name(date_time[1], language="nl")

            # if the year is missing, let's assume it is this year
            if ":" in date_time[2]:
                date_time[2] = datetime.datetime.now().year
                # in the past of future, if future, we need to substract
                stamp = datetime.datetime(int(date_time[2]), month, int(date_time[0]))
                if stamp > datetime.datetime.now():
                    date_time[2] -= 1

            item.set_date(date_time[2], month, date_time[0])
        return True

    def __get_xsrf_token(self):
        """ Retrieves a JSON Token and XSRF token

        :return: XSRF Token and JSON Token
        :rtype: tuple[str|None,str|None]
        """

        # get a token (why?), cookies and an xsrf token
        UriHandler.open("https://www.npostart.nl/api/token",
                        no_cache=True,
                        additional_headers={"X-Requested-With": "XMLHttpRequest"})

        xsrf_token = UriHandler.get_cookie("XSRF-TOKEN", "www.npostart.nl").value
        xsrf_token = HtmlEntityHelper.url_decode(xsrf_token)
        return xsrf_token

    def __get_name_for_api_video(self, result_set, for_epg):
        """ Determines the name of the video item given the episode name, franchise name and
        show title.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex
        :param bool for_epg: use this item in an EPG listing

        :return: The name of the video item
        :rtype: string

        """

        # We need to strip the : because some shows have them and they make no sense.
        show_title = result_set["title"] or result_set["franchiseTitle"]
        show_title = show_title.strip(":")
        episode_title = result_set["episodeTitle"]
        if result_set["type"] == "fragment":
            episode_title = episode_title or result_set["title"]
        if for_epg:
            channel = result_set["channel"]
            name = "{} - {}".format(channel, show_title)
            if episode_title and show_title != episode_title:
                name = "{} - {}".format(name, episode_title)
        else:
            name = episode_title
            if not bool(name):
                name = result_set.get('franchiseTitle')

            # In some cases the title of the show (not episode) is different from the franchise
            # title. In that case we want to add the title of the show in front of the name, but
            # only if that does not lead to duplication
            elif show_title != result_set.get('franchiseTitle') \
                    and show_title != name:
                name = "{} - {}".format(show_title, name)

        return name
