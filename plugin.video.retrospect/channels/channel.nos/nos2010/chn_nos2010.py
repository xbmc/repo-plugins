# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import datetime
import pytz
import re

from resources.lib import chn_class

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
from resources.lib.mediaitem import MediaItem
from resources.lib.xbmcwrapper import XbmcWrapper


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
        self._add_data_parser("http://radio-app.omroep.nl/player/script/",
                              name="Live Radio Streams",
                              preprocessor=self.extract_json_for_live_radio, json=True,
                              parser=[], creator=self.create_live_radio)

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
            r'(?<subtitle>[^<]*)</p>')
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
                                     r'title="([^"]+)"[^>]+data-value="([^"]+)"[^>]+'
                                     r'data-argument="genreId',
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
        self._add_data_parser("https://start-api.npo.nl/page/catalogue", json=True,
                              parser=["components", 1, "data", "items"],
                              creator=self.create_json_episode_item)

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
        self.__pageSize = 500
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

        xsrf_token = self.__get_xsrf_token()[0]
        if not xsrf_token:
            return False

        data = "username=%s&password=%s" % (HtmlEntityHelper.url_encode(username),
                                            HtmlEntityHelper.url_encode(password))
        UriHandler.open("https://www.npostart.nl/api/login", proxy=self.proxy, no_cache=True,
                        additional_headers={
                            "X-Requested-With": "XMLHttpRequest",
                            "X-XSRF-TOKEN": xsrf_token
                        },
                        params=data)

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

            page_data = UriHandler.open(next_page, proxy=self.proxy, additional_headers=http_headers)
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
            more = MediaItem(title, next_page)
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
        search = MediaItem(LanguageHelper.get_localized_string(LanguageHelper.Search), "searchSite")
        search.complete = True
        search.dontGroup = True
        search.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        items.append(search)

        # Favorite items that require login
        favs = MediaItem(LanguageHelper.get_localized_string(LanguageHelper.FavouritesId),
                         "https://www.npostart.nl/api/account/@me/profile")
        favs.complete = True
        favs.description = "Favorieten van de NPO.nl website. Het toevoegen van favorieten " \
                           "wordt nog niet ondersteund."
        favs.dontGroup = True
        favs.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        items.append(favs)

        extra = MediaItem(LanguageHelper.get_localized_string(LanguageHelper.LiveRadio),
                          "http://radio-app.omroep.nl/player/script/player.js")
        extra.complete = True
        extra.dontGroup = True
        items.append(extra)

        extra = MediaItem(LanguageHelper.get_localized_string(LanguageHelper.LiveTv),
                          "%s/live" % (self.baseUrlLive,))
        extra.complete = True
        extra.dontGroup = True
        items.append(extra)

        extra = MediaItem(
            "{} ({})".format(
                LanguageHelper.get_localized_string(LanguageHelper.TvShows),
                LanguageHelper.get_localized_string(LanguageHelper.FullList)
            ),
            "https://start-api.npo.nl/page/catalogue?pageSize={}".format(self.__pageSize))

        extra.complete = True
        extra.dontGroup = True
        extra.description = "Volledige programma lijst van NPO Start."
        extra.HttpHeaders = self.__jsonApiKeyHeader
        # API Key from here: https://packagist.org/packages/kro-ncrv/npoplayer?q=&p=0&hFR%5Btype%5D%5B0%5D=concrete5-package
        items.append(extra)

        extra = MediaItem(LanguageHelper.get_localized_string(LanguageHelper.Genres),
                          "https://www.npostart.nl/programmas")
        extra.complete = True
        extra.dontGroup = True
        items.append(extra)

        extra = MediaItem(
            "{} (A-Z)".format(LanguageHelper.get_localized_string(LanguageHelper.TvShows)),
            "#alphalisting")
        extra.complete = True
        extra.description = "Alfabetische lijst van de NPO.nl site."
        extra.dontGroup = True
        items.append(extra)

        recent = MediaItem(LanguageHelper.get_localized_string(LanguageHelper.Recent), "#recent")
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
        today = datetime.datetime.now()
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
            extra = MediaItem(title, url)
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
                    "thumb": "http://www.3fm.nl/data/thumb/abc_media_image/113000/113453/w210.1b764.jpg"
                },
                "Radio 2 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RADIO2_300879",
                    "thumb": self.get_image_location("radio2.png")
                    # "thumb": "http://www.radio2.nl/image/rm/48254/NPO_RD2_Logo_RGB_1200dpi.jpg?width=848&height=477"
                },
                "Radio 6 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RADIO6_300883",
                    # "thumb": "http://www.radio6.nl/data/thumb/abc_media_image/3000/3882/w500.1daa0.png"
                    "thumb": self.get_image_location("radio6.png")
                },
                "Radio 1 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RADIO1_300877",
                    # "thumb": "http://statischecontent.nl/img/tweederdevideo/1e7db3df-030a-4e5a-b2a2-840bd0fd8242.jpg"
                    "thumb": self.get_image_location("radio1.png")
                },
            }

            for stream in live_streams:
                Logger.debug("Adding video item to '%s' sub item list: %s", parent, stream)
                live_data = live_streams[stream]
                item = MediaItem(stream, live_data["url"])
                item.icon = parent.icon
                item.thumb = live_data["thumb"]
                item.type = 'video'
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
            sub_item = MediaItem(title_format % (char,), url_format % (char,))
            sub_item.complete = True
            sub_item.dontGroup = True
            sub_item.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
            items.append(sub_item)
        return data, items

    def create_profile_item(self, result_set):
        """ Creates a new MediaItem for a the profiles in NPO Start.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        profile_name = result_set.get("name")
        item = MediaItem(profile_name, "#list_profile")
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

        xsrf_token = self.__get_xsrf_token()[0]
        UriHandler.open("https://www.npostart.nl/api/account/@me/profile/switch",
                        proxy=self.proxy, data=profile_data,
                        additional_headers={
                            "X-Requested-With": "XMLHttpRequest",
                            "X-XSRF-TOKEN": xsrf_token,
                            "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
                        })

        # Add the episodes/tvshows
        epsisodes = MediaItem(
            LanguageHelper.get_localized_string(LanguageHelper.Episodes),
            "https://www.npostart.nl/ums/accounts/@me/favourites/episodes?page=1&dateFrom=2014-01-01&tileMapping=dedicated&tileType=asset")
        items.append(epsisodes)

        tvshows = MediaItem(
            LanguageHelper.get_localized_string(LanguageHelper.TvShows),
            "https://www.npostart.nl/ums/accounts/@me/favourites?page=1&type=series&tileMapping=normal&tileType=teaser")
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

        # Update the URL
        item.url = self.__get_url_for_pom(result_set["powid"])
        if self.__useJson:
            item.HttpHeaders = self.__jsonApiKeyHeader
        else:
            item.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        item.dontGroup = True
        return item

    def create_json_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

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

        item = MediaItem(name, url)
        item.type = 'folder'
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
        item = MediaItem(title, result_set["url"])
        item.description = result_set["channel"]
        item.type = 'video'
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
            item.type = "video"
            item.url = result_set["powid"]
        else:
            item.type = "folder"
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

    def extract_api_pages(self, data):
        """ Extracts the JSON tiles data from the HTML.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """
        items = []

        data = JsonHelper(data)
        next_url = data.get_value("_links", "next", "href")
        if next_url:
            next_title = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
            item = MediaItem(next_title, next_url)
            item.complete = True
            item.HttpHeaders = self.__jsonApiKeyHeader
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

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex
        :param bool for_epg: use this item in an EPG listing

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

        item = MediaItem(name, video_id)
        item.description = description
        item.type = "video"

        season = result_set.get("seasonNumber")
        episode = result_set.get("episodeNumber")
        if bool(season) and bool(episode) and season < 100:
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

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

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

        item = MediaItem(title, video_id)
        item.type = 'video'
        item.complete = False
        item.description = description
        #
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
        item = MediaItem(result_set[1], url)
        item.type = 'folder'
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

        item = MediaItem(name, "%s/live/%s" % (self.baseUrlLive, result_set[0]), type="video")
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

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace("Content = %s", result_set)
        name = result_set["name"]
        if name == "demo":
            return None

        item = MediaItem(name, "", type="audio")
        item.isLive = True
        item.complete = False

        # noinspection PyTypeChecker
        streams = result_set.get("audiostreams", [])
        part = item.create_new_empty_media_part()

        # first check for the video streams
        # noinspection PyTypeChecker
        for stream in result_set.get("videostreams", []):
            Logger.trace(stream)
            # url = stream["url"]
            # if not url.endswith("m3u8"):
            if not stream["protocol"] == "prid":
                continue
            item.url = "http://e.omroep.nl/metadata/%(url)s" % stream
            item.complete = False
            item.type = "video"
            return item

        # else the radio streams
        for stream in streams:
            Logger.trace(stream)
            if not stream["protocol"] or stream["protocol"] == "prid":
                continue
            bitrate = stream.get("bitrate", 0)
            url = stream["url"]
            part.append_media_stream(url, bitrate)
            item.complete = True
            # if not stream["protocol"] == "prid":
            #     continue
            # item.url = "http://e.omroep.nl/metadata/%(url)s" % stream
            # item.complete = False
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
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
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
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item: %s', item.name)

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()

        # we need to determine radio or live tv
        Logger.debug("Fetching live stream data from item url: %s", item.url)
        html_data = UriHandler.open(item.url, proxy=self.proxy)

        mp3_urls = Regexer.do_regex("""data-streams='{"url":"([^"]+)","codec":"[^"]+"}'""", html_data)
        if len(mp3_urls) > 0:
            Logger.debug("Found MP3 URL")
            part.append_media_stream(mp3_urls[0], 192)
        else:
            Logger.debug("Finding the actual metadata url from %s", item.url)
            # NPO3 normal stream had wrong subs
            if "npo-3" in item.url and False:
                # NPO3 has apparently switched the normal and hearing impaired streams?
                json_urls = Regexer.do_regex('<div class="video-player-container"[^>]+data-alt-prid="([^"]+)"', html_data)
            else:
                json_urls = Regexer.do_regex('<npo-player media-id="([^"]+)"', html_data)

            for episode_id in json_urls:
                return self.__update_video_item(item, episode_id, False)

            Logger.warning("Cannot update live item: %s", item)
            return item

        item.complete = True
        return item

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
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item:          the original MediaItem that needs updating.
        :param str episode_id:          the ID of the episode.
        :param bool fetch_subtitles:    should we fetch the subtitles (not for live items).

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.trace("Using Generic update_video_item method")

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()

        # get the subtitle
        if fetch_subtitles:
            sub_title_url = "https://rs.poms.omroep.nl/v1/api/subtitles/%s/nl_NL/CAPTION.vtt" % (episode_id,)
            sub_title_path = subtitlehelper.SubtitleHelper.download_subtitle(
                sub_title_url, episode_id + ".nl.srt", format='srt', proxy=self.proxy)
            if sub_title_path:
                part.Subtitle = sub_title_path

        if AddonSettings.use_adaptive_stream_add_on(
                with_encryption=True, ignore_add_on_config=True):
            error = NpoStream.add_mpd_stream_from_npo(None, episode_id, part, proxy=self.proxy, live=item.isLive)
            if bool(error) and self.__has_premium():
                self.__log_on(force_log_off=True)
                error = NpoStream.add_mpd_stream_from_npo(None, episode_id, part, proxy=self.proxy, live=item.isLive)

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
        #         proxy=self.proxy, data=data, additional_headers={
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
            url = "https://start-api.npo.nl/media/series/{0}/episodes?pageSize={1}"\
                .format(pom, self.__pageSize)
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
        token = UriHandler.open("https://www.npostart.nl/api/token", proxy=self.proxy,
                                no_cache=True,
                                additional_headers={"X-Requested-With": "XMLHttpRequest"})

        json_token = JsonHelper(token)
        token = json_token.get_value("token")
        if not token:
            return None, None

        xsrf_token = UriHandler.get_cookie("XSRF-TOKEN", "www.npostart.nl").value
        xsrf_token = HtmlEntityHelper.url_decode(xsrf_token)
        return xsrf_token, token

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
