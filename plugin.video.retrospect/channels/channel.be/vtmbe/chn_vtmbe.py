# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import base64
import random
import time
import datetime

from resources.lib import chn_class
from resources.lib.helpers.htmlhelper import HtmlHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem
from resources.lib.streams.mpd import Mpd
from resources.lib.vault import Vault
from resources.lib.urihandler import UriHandler
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.streams.m3u8 import M3u8
from resources.lib.regexer import Regexer
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.parserdata import ParserData

from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper


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
        self.__api = None
        self.__sso = None

        if self.channelCode == "vtm":
            self.__app = "vtm_watch"
            self.__sso = "vtm-sso"
            self.__apiKey = "vtm-b7sJGrKwMJj0VhdZvqLDFvgkJF5NLjNY"
            self.baseUrl = "https://vtm.be"

            self.noImage = "vtmbeimage.jpg"
            self.mainListUri = "https://vtm.be/programmas/az"
            # Uncomment the line below for full JSON listing, but it will contain many empty shows!
            # self.mainListUri = "https://vtm.be/feed/programs?format=json&type=all&only_with_video=true"

            # setup the main parsing data in case of HTML
            recent_regex = r'<a href="/(?<url>[^"]+)"[^>]*>\W+(?:<div[^>]+>\W+)+<img[^>]+src="' \
                           r'(?<thumburl>[^"]+)"[^>]+>\W*<span[^>]*>\W*(?<subtitle>[^<]+)' \
                           r'[\w\W]{0,300}?(?:<div[^>]+class="item-caption-program"[^>]*>' \
                           r'(?<title>[^<]+)</div>\W*)</div>\W*</div>\W*</div>\W*</a'
            recent_regex = Regexer.from_expresso(recent_regex)
            self._add_data_parser("https://vtm.be/video/volledige-afleveringen/id",
                                  match_type=ParserData.MatchExact,
                                  name="Recent Items HTML Video Parser",
                                  parser=recent_regex, creator=self.create_video_item_html)

            episode_regex = r'<li>\s*<a[^>]+href="(?<url>[^"]+)"[^>]*>(?<title>[^<]+)</a>\s*</li>'
            episode_regex = Regexer.from_expresso(episode_regex)
            self._add_data_parser("https://vtm.be/programmas/az",
                                  name="New VTM parser",
                                  preprocessor=self.add_live_channel,
                                  parser=episode_regex, creator=self.create_episode_item_html)

            clip_regex = r'image-container">\W*<a[^>]+href="(?<url>[^"]+)">[\W\w]{0,500}?<div ' \
                         r'class="card-duration">[\W\w]{0,500}?<img[^>]*src="(?<thumburl>[^"]+)' \
                         r'[\W\w]{0,1000}?<h3[^>]*>\s+<a[^>]+>(?<title>[^<]+)'
            clip_regex = Regexer.from_expresso(clip_regex)
            self._add_data_parser("*", name="New Video parser for VTM Clips",
                                  parser=clip_regex, creator=self.create_video_item_html,
                                  updater=self.update_html_clip_item)

            self._add_data_parser("*", name="New Video parser for VTM Videos", json=True,
                                  preprocessor=self.extract_vtm_id_from_json,
                                  parser=["response", "videos"], creator=self.create_video_item_json)

        elif self.channelCode == "q2":
            self.__app = "q2"
            self.__sso = "q2-sso"
            self.__apiKey = "q2-html5-NNSMRSQSwGMDAjWKexV4e5Vm6eSPtupk"
            self.baseUrl = "https://www.q2.be"

            self.noImage = "q2beimage.jpg"
            self.mainListUri = "https://www.q2.be/feed/programs?format=json&type=all&only_with_video=true"
            # Uncomment the line below for full JSON listing, but it will contain many empty shows!
            self.mainListUri = "https://www.q2.be/video?f%5B0%5D=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen"

            html_video_regex = r'<a[^>]+class="cta-full[^>]+href="/(?<url>[^"]+)"[^>]*>[^<]*</a>' \
                               r'\W*<span[^>]*>[^<]*</[^>]*\W*<div[^>]*>\W*<img[^>]+src="' \
                               r'(?<thumburl>[^"]+)[\w\W]{0,1000}?<h3[^>]*>(?<title>[^<]+)'
            html_video_regex = Regexer.from_expresso(html_video_regex)
            self._add_data_parser(
                "https://www.q2.be/video/?f%5B0%5D=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&",
                name="HTML Page Video Parser for Q2",
                parser=html_video_regex, creator=self.create_video_item_html)

            html_episode_regex = '<a[^>]+href="(?<url>[^"]+im_field_program[^"]+)"[^>]+>(?<title>[^(<]+)'
            html_episode_regex = Regexer.from_expresso(html_episode_regex)
            self._add_data_parser("sm_field_video_origin_cms_longform%3AVolledige%20afleveringen",
                                  match_type=ParserData.MatchEnd,
                                  name="HTML Page Show Parser",
                                  preprocessor=self.add_live_channel,
                                  parser=html_episode_regex,
                                  creator=self.create_episode_item_html)

        elif self.channelCode == "stievie":
            self.__app = "stievie"
            self.__sso = "stievie-sso"
            self.__apiKey = "stievie-web-2.8-yz4DSTPshescHUytkWwU9jDxQ28PKTGn"
            self.noImage = "stievieimage.jpg"
            self.httpHeaders["Authorization"] = "apikey=%s" % (self.__apiKey, )

            self.mainListUri = "https://channels.medialaan.io/channels/v1/channels?preview=false"
            self._add_data_parser(self.mainListUri,
                                  json=True, requires_logon=True,
                                  preprocessor=self.stievie_menu,
                                  name="JSON Channel overview",
                                  parser=["response", "channels"],
                                  creator=self.stievie_create_channel_item)

            self._add_data_parser("#channel", name="Channel menu parser",
                                  preprocessor=self.stievie_channel_menu)

            # main list parsing
            self._add_data_parser("https://vod.medialaan.io/vod/v2/programs?offset=0&limit=0",
                                  json=True,
                                  name="Main program list parsing for Stievie",
                                  # If we want to add live: preprocessor=self.add_live_channel,
                                  creator=self.stievie_create_episode,
                                  parser=["response", "videos"])

            # self._add_data_parser("https://epg.medialaan.io/epg/v2/", json=True,
            #                       name="EPG Stievie parser",
            #                       creator=self.stievie_create_epg_items,
            #                       parser=["channels", ])

            self._add_data_parser("https://epg.medialaan.io/epg/v3/", json=True,
                                  name="EPG Stievie parser for API Version 3",
                                  creator=self.stievie_create_epg_items_v3,
                                  parser=["response", "broadcasts", ])

            self._add_data_parser("https://vod.medialaan.io/vod/v2/programs?query=",
                                  name="Stievie Search Parser", json=True,
                                  creator=self.stievie_create_episode,
                                  parser=["response", "videos"])

        else:
            raise NotImplementedError("%s not supported yet" % (self.channelCode, ))

        self._add_data_parser(
            r"https://(?:vtm.be|www.q2.be)/video/?.+=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&.+id=\d+",
            match_type=ParserData.MatchRegex,
            name="HTML Page Video Updater",
            updater=self.update_video_item, requires_logon=True)

        self._add_data_parser("https://vtm.be/video/volledige-afleveringen/id/",
                              name="HTML Page Video Updater New Style (add_more_recent_videos)",
                              updater=self.update_video_item, requires_logon=True)

        # setup the main parsing data in case of JSON mainlist of the V2 API
        self._add_data_parser("/feed/programs?format=json&type=all&only_with_video=true",
                              match_type=ParserData.MatchEnd,
                              name="JSON Feed Show Parser for Medialaan",
                              json=True, preprocessor=self.add_live_channel_and_fetch_all_data,
                              creator=self.create_episode_item_json, parser=["response", "items"])

        self._add_data_parser("https://vod.medialaan.io/vod/v2/videos/",
                              match_type=ParserData.MatchRegex,
                              name="JSON Video Updater for Medialaan",
                              updater=self.update_video_item_json, requires_logon=True)

        self._add_data_parser("https://vod.medialaan.io/vod/v2/videos?", json=True,
                              preprocessor=self.add_video_page_items_json,
                              parser=["response", "videos"], creator=self.create_video_item_json,
                              name="JSON Video Listing for Medialaan with programOID")

        self._add_data_parser("https://vod.medialaan.io/vod/v2/videos?", json=True,
                              name="JSON Video Updater for Medialaan with programOID",
                              updater=self.update_video_epg_item_json, requires_logon=True)

        self._add_data_parser("#livestream", name="Live Stream Updater for Q2, VTM and Stievie",
                              requires_logon=True, updater=self.update_live_stream)

        # ===============================================================================================================
        # non standard items
        self.__signature = None
        self.__signatureTimeStamp = None
        self.__userId = None
        self.__hasPremium = False
        self.__premium_channels = {}
        self.__adaptiveStreamingAvailable = \
            AddonSettings.use_adaptive_stream_add_on(with_encryption=True)

        # Mappings from the normal URL (which has all shows with actual videos and very little
        # video-less shows) to the JSON ids. Loading can be done using:
        #     import json
        #     fp = file("c:\\temp\\ff.json")
        #     data = json.load(fp)
        #     fp.close()
        #     mapping = dict()
        #     for item in data["response"]["items"]:
        #         if not item["parent_series_oid"]:
        #             continue
        #         mapping[item["title"]] = item["parent_series_oid"]
        #     print json.dumps(mapping)
        #
        # TODO: perhaps we can do this dynamically?
        # VTM: https://vtm.be/feed/programs?format=json&type=all&only_with_video=true
        # Q2: https://www.q2.be/feed/programs?format=json&type=all&only_with_video=true

        self.__mappings = {
            "q2": {
                "Grimm": "256511352168527", "Grounded for Life": "256575957717527",
                "Crimi Clowns": "256403636905527", "At The Festivals": "257152544383527",
                "Sleepy Hollow": "256576898469527", "Taken": "256676853145527",
                "The Nanny": "256577036328527", "Life in Pieces": "256651006814527",
                "Absurdistan": "256688131946527", "Scream Queens": "256650984248527",
                "Modern Family": "256467031756527", "Game of Thrones": "256588988771527",
                "The Big Bang Theory": "256467024031527", "Foute Vrienden": "256403630232527",
                "The Last Man on Earth": "256596883888527", "That '70s Show": "256467039034527",
                "Prison Break": "257042962946527", "The X-Files": "256676844763527",
                "APB": "257060802802527", "The Graham Norton Show": "256943055386527",
                "Superstaar": "256577029073527", "Top Gear": "256528438369527",
                "American Horror Story": "256466896013527", "New Girl": "256467032228527",
                "Tricked": "256573688559527", "Community": "256973035121527",
                "UEFA Champions League": "256584896142527", "Bones": "256404132799527",
                "Married with Children": "256576831734527", "Peking Express": "257101660737527"
            },
            "vtm": {}
        }

        self.__set_cookie()

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def __set_cookie(self):
        # Example: Cookie: pwv=1; pws=functional|analytics|content_recommendation|targeted_advertising|social_media
        domain = self.mainListUri.replace("https://", "").split("/", 1)[0]
        UriHandler.set_cookie(name="pwv", value="1", domain=domain)
        UriHandler.set_cookie(name="pws", value="functional|analytics|content_recommendation|targeted_advertising|social_media", domain=domain)

    def log_on(self):
        signature_settings = "mediaan_signature"
        login_token = AddonSettings.get_setting(signature_settings, store=LOCAL)
        api_key = "3_OEz9nzakKMkhPdUnz41EqSRfhJg5z9JXvS4wUORkqNf2M2c1wS81ilBgCewkot97"  # from Stievie
        # from VTM:  api_key = "3_HZ0FtkMW_gOyKlqQzW5_0FHRC7Nd5XpXJZcDdXY4pk5eES2ZWmejRW5egwVm4ug-"

        # Common Query Parameters between the acounts.login and the accounts.getAccountInfo calls
        # "&include=profile%%2Cdata" \
        # "&includeUserInfo=true" \
        # "&includeSSOToken=true" \
        # "&sdk=js_latest" \
        common_data = "APIKey=%s" \
                      "&authMode=cookie" % (api_key,)

        login_cookie = UriHandler.get_cookie("gmid", domain=".gigya.com")

        if login_token and "|" not in login_token and login_cookie is not None:
            # only retrieve the account information using the cookie and the token
            account_info_url = "https://accounts.eu1.gigya.com/accounts.getAccountInfo?{}" \
                               "&login_token={}".format(common_data, login_token)
            account_info = UriHandler.open(account_info_url, proxy=self.proxy, no_cache=True)

            # See if it was successfull
            if self.__extract_session_data(account_info, signature_settings):
                return True
            Logger.warning("Failed to extend the VTM.be session.")

        # We actually need to login to stievie or VTM
        Logger.info("Logging onto Stievie.be/VTM.be")
        v = Vault()
        password = v.get_setting("mediaan_password")
        username = AddonSettings.get_setting("mediaan_username")
        if not username or not password:
            XbmcWrapper.show_dialog(
                title=None,
                message=LanguageHelper.get_localized_string(LanguageHelper.MissingCredentials),
            )
            return False
        Logger.debug("Using: %s / %s", username, "*" * len(password))

        # clean older data
        UriHandler.delete_cookie(domain=".gigya.com")

        # first we need a random context_id R<10 numbers>
        context_id = int(random.random() * 8999999999) + 1000000000

        # then we do an initial bootstrap call, which retrieves the `gmid` and `ucid` cookies
        url = "https://accounts.eu1.gigya.com/accounts.webSdkBootstrap?apiKey={}" \
              "&pageURL=https%3A%2F%2Fwatch.stievie.be%2F&format=jsonp" \
              "&callback=gigya.callback&context=R{}".format(api_key, context_id)
        init_login = UriHandler.open(url, proxy=self.proxy, no_cache=True)
        init_data = JsonHelper(init_login)
        if init_data.get_value("statusCode") != 200:
            Logger.error("Error initiating login")

        # actually do the login request, which requires an async call to retrieve the result
        login_url = "https://accounts.eu1.gigya.com/accounts.login" \
                    "?context={0}" \
                    "&saveResponseID=R{0}".format(context_id)
        login_data = "loginID=%s" \
                     "&password=%s" \
                     "&context=R%s" \
                     "&targetEnv=jssdk" \
                     "&sessionExpiration=-2" \
                     "&%s" % \
                     (HtmlEntityHelper.url_encode(username), HtmlEntityHelper.url_encode(password),
                      context_id, common_data)
        UriHandler.open(login_url, params=login_data, proxy=self.proxy, no_cache=True)

        #  retrieve the result
        login_retrieval_url = "https://accounts.eu1.gigya.com/socialize.getSavedResponse" \
                              "?APIKey={0}" \
                              "&saveResponseID=R{1}" \
                              "&noAuth=true" \
                              "&sdk=js_latest" \
                              "&format=json" \
                              "&context=R{1}".format(api_key, context_id)
        login_response = UriHandler.open(login_retrieval_url, proxy=self.proxy, no_cache=True)
        return self.__extract_session_data(login_response, signature_settings)

    # region Stievie listings/menus
    def stievie_menu(self, data):
        """ Creates the main Stievie menu.

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
        if not self.__adaptiveStreamingAvailable:
            return data, items

        # No more programs. Stievie became VTM GO
        # programs = MediaItem("\b.: Programma's :.", "https://vod.medialaan.io/vod/v2/programs?offset=0&limit=0")
        # programs.dontGroup = True
        # items.append(programs)
        #
        # search = MediaItem("Zoeken", "searchSite")
        # search.complete = True
        # search.dontGroup = True
        # items.append(search)
        return data, items

    def stievie_channel_menu(self, data):
        """ Creates the main Stievie Channels menu.

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
        live = MediaItem("Live %s" % (self.parentItem.name, ), "#livestream")
        live.isLive = True
        live.type = "video"
        live.description = self.parentItem.description
        live.metaData = self.parentItem.metaData
        items.append(live)

        if not self.__adaptiveStreamingAvailable:
            # Only list the channel content if DASH is supported
            return data, items

        # https://epg.medialaan.io/epg/v2/schedule?date=2017-04-25&channels%5B%5D=vtm&channels%5B%5D=2be&channels%5B%5D=vitaya&channels%5B%5D=caz&channels%5B%5D=kzoom&channels%5B%5D=kadet&channels%5B%5D=qmusic
        # https://epg.medialaan.io/epg/v2/schedule?date=2017-04-25&channels[]=vtm&channels[]=2be&channels[]=vitaya&channels[]=caz&channels[]=kzoom&channels[]=kadet&channels[]=qmusic
        # https://epg.medialaan.io/epg/v2/schedule?date=2017-05-04&channels[]=vtm&channels[]=2be&channels[]=vitaya&channels[]=caz&channels[]=kzoom&channels[]=kadet&channels[]=qmusic

        # No more EPG items as Stievie became VTM GO
        # channel_id = self.parentItem.metaData["channelId"]
        # channels = (channel_id, )
        # query = "channels%%5B%%5D=%s" % ("&channels%5B%5D=".join(channels), )
        # today = datetime.datetime.now()
        # days = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        # for i in range(0, 7, 1):
        #     air_date = today - datetime.timedelta(i)
        #     until_air_date = today - datetime.timedelta(i) + datetime.timedelta(1)
        #     Logger.trace("Adding item for: %s", air_date)
        #
        #     day = days[air_date.weekday()]
        #     if i == 0:
        #         day = "Vandaag"
        #     elif i == 1:
        #         day = "Gisteren"
        #     elif i == 2:
        #         day = "Eergisteren"
        #     title = "%04d-%02d-%02d - %s" % (air_date.year, air_date.month, air_date.day, day)
        #     # url = "https://epg.medialaan.io/epg/v2/schedule?date=%d-%02d-%02d%s" % (air_date.year, air_date.month, air_date.day, query)
        #     # https://epg.medialaan.io/epg/v3/broadcasts?channels%5B%5D=zes&from=2019-05-29T03%3A00%3A00.000Z&until=2019-05-30T03%3A00%3A00.000Z
        #
        #     url = "https://epg.medialaan.io/epg/v3/broadcasts?%s&" \
        #           "from=%d-%02d-%02dT03%%3A00%%3A00.000Z&" \
        #           "until=%d-%02d-%02dT03%%3A00%%3A00.000Z" % (
        #             query,
        #             air_date.year, air_date.month, air_date.day,
        #             until_air_date.year, until_air_date.month, until_air_date.day)
        #
        #     extra = MediaItem(title, url)
        #     extra.complete = True
        #     extra.dontGroup = True
        #     extra.set_date(air_date.year, air_date.month, air_date.day, text="")
        #     extra.metaData["airDate"] = air_date
        #     items.append(extra)

        return data, items

    def stievie_create_channel_item(self, result_set):
        """ Creates a Channel MediaItem of type 'video' using the result_set from the regex.

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

        Logger.trace(result_set)

        if result_set['premium'] and not self.__hasPremium:
            return None

        item = MediaItem(result_set["name"], "#livestream")
        item.description = result_set.get("slogan", None)
        item.metaData["channelId"] = result_set["id"]
        item.type = "video"
        item.isLive = True
        item.isPaid = True  # result_set.get("premium", False)  All content requires a premium account
        item.isGeoLocked = True

        if "icons" in result_set:
            # noinspection PyTypeChecker
            item.thumb = result_set["icons"]["default"]
            if not item.thumb:
                # noinspection PyTypeChecker
                item.thumb = result_set["icons"]["white"]
        return item

    def stievie_create_epg_items_v3(self, result_set):
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

        Logger.trace(result_set)

        episode_info = result_set["episode"]
        video_id = episode_info.get("vodId")
        if video_id is None:
            return None

        url = "https://vod.medialaan.io/vod/v2/videos/{}".format(video_id)

        summer_time = time.localtime().tm_isdst
        now = datetime.datetime.now()

        title = episode_info["title"]
        if episode_info["number"] and result_set["season"] and result_set["season"]["number"] < 1000:
            title = "%s - s%02de%02d" % (title, result_set["season"]["number"], episode_info["number"])

        if "subtitle" in episode_info and episode_info["subtitle"]:
            title = "{} - {}".format(title, episode_info["subtitle"])

        start_time = result_set["start"]["display"].split(".")[0]
        start_time_tuple = DateHelper.get_date_from_string(start_time, date_format="%Y-%m-%dT%H:%M:%S")
        start_time_dt = datetime.datetime(*start_time_tuple[:6])
        # Correct for the UTC+0100 (or UTC+0200 in DST)
        start_time_tz_dt = start_time_dt + datetime.timedelta(hours=1 + summer_time)
        title = "%02d:%02d - %s" % (start_time_tz_dt.hour, start_time_tz_dt.minute, title)

        # Check for items in their black-out period
        if "blackout" in result_set and result_set["blackout"]["enabled"]:
            blackout_duration = result_set["blackout"]["duration"]
            blackout_start = start_time_tz_dt + datetime.timedelta(seconds=blackout_duration)
            if blackout_start < now:
                Logger.debug("Found item in Black-out period: %s (started at %s)", title,
                             blackout_start)
                return None

        item = MediaItem(title, url)
        item.type = "video"
        item.isGeoLocked = result_set["geoblock"]
        item.description = episode_info["description"]
        # item.set_date(startTime.year, startTime.month, startTime.day)

        if "images" in episode_info and episode_info["images"]:
            for image_info in episode_info["images"]:
                if image_info["resolution"] == "800x450":
                    item.thumb = image_info["url"]

        return item

    # The old V2 API code
    # def stievie_create_epg_items(self, epg):
    #     """ Creates a MediaItem of type 'video' using the result_set from the regex.
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
    #     :param list[str]|dict epg: The result_set of the self.episodeItemRegex
    #
    #     :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
    #     :rtype: MediaItem|None
    #
    #     """
    #
    #     Logger.trace(epg)
    #     Logger.debug("Processing EPG for channel %s", epg["id"])
    #
    #     items = []
    #     summer_time = time.localtime().tm_isdst
    #     now = datetime.datetime.now()
    #
    #     for result_set in epg["items"]:
    #         # if not resultSet["parentSeriesOID"]:
    #         #     continue
    #
    #         # Does not always work
    #         # videoId = resultSet["epgId"].replace("-", "_")
    #         # url = "https://vod.medialaan.io/vod/v2/videos/%s_Stievie_free" % (videoId, )
    #         video_id = result_set["programOID"]
    #         url = "https://vod.medialaan.io/vod/v2/videos?episodeIds=%s&limit=10&offset=0&sort=broadcastDate&sortDirection=asc" % (video_id, )
    #         title = result_set["title"]
    #         if result_set["episode"] and result_set["season"]:
    #             title = "%s - s%02de%02d" % (title, result_set["season"], result_set["episode"])
    #
    #         if "startTime" in result_set and result_set["startTime"]:
    #             date_time = result_set["startTime"]
    #             date_value = DateHelper.get_date_from_string(date_time, date_format="%Y-%m-%dT%H:%M:%S.000Z")
    #             # Convert to Belgium posix time stamp
    #             date_value2 = time.mktime(date_value) + (1 + summer_time) * 60 * 60
    #             # Conver the posix to a time stamp
    #             start_time = DateHelper.get_date_from_posix(date_value2)
    #
    #             title = "%02d:%02d - %s" % (start_time.hour, start_time.minute, title)
    #
    #             # Check for items in their black-out period
    #             if "blackout" in result_set and result_set["blackout"]["enabled"]:
    #                 blackout_duration = result_set["blackout"]["duration"]
    #                 blackout_start = start_time + datetime.timedelta(seconds=blackout_duration)
    #                 if blackout_start < now:
    #                     Logger.debug("Found item in Black-out period: %s (started at %s)", title, blackout_start)
    #                     continue
    #
    #         # else:
    #         #     startTime = self.parentItem.metaData["airDate"]
    #
    #         item = MediaItem(title, url)
    #         item.type = "video"
    #         item.isGeoLocked = result_set["geoblock"]
    #         item.description = result_set["shortDescription"]
    #         # item.set_date(startTime.year, startTime.month, startTime.day)
    #
    #         if "images" in result_set and result_set["images"] and "styles" in result_set["images"][0]:
    #             images = result_set["images"][0]["styles"]
    #             # Fanart image
    #             # if "1520x855" in images:
    #             #     item.fanart = images["1520x855"]
    #             if "400x225" in images:
    #                 item.thumb = images["400x225"]
    #
    #         items.append(item)
    #
    #     return items

    def stievie_create_episode(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        title = result_set['title']
        url = "https://vod.medialaan.io/vod/v2/videos?limit=18" \
              "&apikey=%s" \
              "&sort=broadcastDate&sortDirection=desc" \
              "&programIds=%s" % (self.__apiKey, result_set['id'],)
        item = MediaItem(title, url)
        item.thumb = self.__find_image(result_set, self.noImage)
        return item
    # endregion

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

        # nieuws
        url = "https://vod.medialaan.io/vod/v2/programs?query=%s"
        return chn_class.Channel.search_site(self, url)

    def add_live_channel_and_fetch_all_data(self, data):
        """ Preprocesses that data and adds live channels and fetches al related data via extra
        json calls.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        data, items = self.add_live_channel(data)

        # The current issue with this is that the API is providing only the videos and not
        # the full episodes.

        json = JsonHelper(data)
        json_items = json.get_value("response", "items")
        count = json.get_value("response", "total")
        for i in range(100, count, 100):
            url = "%s&from=%s" % (self.mainListUri, i)
            Logger.debug("Retrieving more items from: %s", url)
            more_data = UriHandler.open(url, proxy=self.proxy)
            more_json = JsonHelper(more_data)
            more_items = more_json.get_value("response", "items")
            if more_items:
                json_items += more_items

        Logger.debug("Added: %s extra items", len(json_items))
        return json, items

    def create_episode_item_json(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        title = result_set['title']

        if result_set["parent_series_oid"] is None:
            return None

        # Exclude some items?
        # if not result_set["is_featured"]:
        #     # most of them are empty anyways
        #     return None
        # if result_set.get("archived", False):
        #     return None

        url = "https://vod.medialaan.io/vod/v2/videos?limit=18" \
              "&apikey=%s" \
              "&sort=broadcastDate&sortDirection=desc" \
              "&programIds=%s" % (self.__apiKey, result_set['parent_series_oid'],)

        item = MediaItem(title, url)
        item.description = result_set.get('body', None)
        if item.description:
            # Clean HTML
            item.description = item.description.replace("<br />", "\n\n")
            item.description = HtmlHelper.to_text(item.description)

        if 'images' in result_set and 'image' in result_set['images']:
            # noinspection PyTypeChecker
            item.thumb = result_set['images']['image'].get('full', self.noImage)
        return item

    def add_video_page_items_json(self, data):
        """ Preprocesses that data and adds next page items.

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
        json = JsonHelper(data)
        current_offset = json.get_value("request", "offset") or 0
        items_on_this_page = len(json.get_value("response", "videos") or [])
        total_items = json.get_value("response", "total")

        if total_items > current_offset + items_on_this_page:
            # add next page items
            new_offset = current_offset + items_on_this_page
            series_id = json.get_value("request", "programIds")[0]

            url = "https://vod.medialaan.io/vod/v2/videos?limit=18" \
                  "&offset=%s" \
                  "&apikey=%s" \
                  "&sort=broadcastDate&sortDirection=desc" \
                  "&programIds=%s" % (new_offset, self.__apiKey, series_id,)

            more = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
            item = MediaItem(more, url)
            item.complete = True
            items.append(item)

        return json, items

    def extract_vtm_id_from_json(self, data):
        """ Preprocesses data and extracts the VTM IDs from the json.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        show_id = Regexer.do_regex(r'[\[|=]"(\d{15})"', data)[0]
        url = "https://vod.medialaan.io/vod/v2/videos?limit=18" \
              "&apikey=%s" \
              "&sort=broadcastDate&sortDirection=desc" \
              "&programIds=%s" % (self.__apiKey, show_id)
        data = UriHandler.open(url, proxy=self.proxy)
        return data, []

    def create_video_item_json(self, result_set):
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

        Logger.trace(result_set)

        if 'episode' in result_set:
            # noinspection PyTypeChecker
            title = result_set['episode']['title']
        else:
            title = result_set['title']

        url = "https://vod.medialaan.io/vod/v2/videos/%(id)s" % result_set
        item = MediaItem(title, url, type="video")
        item.description = result_set.get('text')
        item.thumb = self.__find_image(result_set.get('episode', {}), self.parentItem.thumb)

        # broadcastDate=2018-05-31T18:39:36.840Z
        date = result_set.get('broadcastDate', None) or result_set.get('created', None)
        if date is None:
            return item

        created = DateHelper.get_date_from_string(date.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        item.set_date(*created[0:6])

        return item

    def update_video_item_json(self, item):
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

        video_id = item.url.rsplit("/", 1)[-1]
        return self.__update_video_item(item, video_id)

    def update_video_epg_item_json(self, item):
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

        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=self.httpHeaders)
        json_data = JsonHelper(data)
        video_id = json_data.get_value("response", "videos", 0, "id")
        return self.__update_video_item(item, video_id)

    def add_live_channel(self, data):
        """ Preprocesses that data and adds live channels.

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

        username = AddonSettings.get_setting("mediaan_username")
        if not username:
            return data, []

        items = []

        if self.channelCode == "vtm":
            item = MediaItem("Live VTM", "#livestream")
        else:
            item = MediaItem("Live Q2", "#livestream")
        item.type = "video"
        item.isLive = True
        now = datetime.datetime.now()
        item.set_date(now.year, now.month, now.day, now.hour, now.minute, now.second)
        items.append(item)

        # No more recent items
        # if self.channelCode == "vtm":
        #     recent = MediaItem("\a.: Recent :.", "https://vtm.be/video/volledige-afleveringen/id")
        #     item.dontGroup = True
        #     items.append(recent)

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_episode_item_html(self, result_set):
        """Creates a new MediaItem for an episode

       Arguments:
       result_set : list[string] - the result_set of the self.episodeItemRegex

       Returns:
       A new MediaItem of type 'folder'

       This method creates a new MediaItem from the Regular Expression or Json
       results <result_set>. The method should be implemented by derived classes
       and are specific to the channel.

       """

        Logger.trace(result_set)

        title = result_set['title']
        url = result_set['url']
        if url.endswith("vtm-nieuws-0"):
            return None

        if not url.startswith("http"):
            url = "%s%s" % (self.baseUrl, url)
        # Try to mix the Medialaan API with HTML is not working
        # programId = result_set['url'].split('%3A')[-1]
        program_id = title.rstrip()
        if program_id in self.__mappings.get(self.channelCode, {}):
            series_id = self.__mappings[self.channelCode][program_id]
            Logger.debug("Using JSON SeriesID '%s' for '%s' (%s)", series_id, title, program_id)
            url = "https://vod.medialaan.io/vod/v2/videos?limit=18" \
                  "&apikey=%s" \
                  "&sort=broadcastDate&sortDirection=desc" \
                  "&programIds=%s" % (self.__apiKey, series_id, )
        else:
            url = HtmlEntityHelper.strip_amp(url)
        # We need to convert the URL
        # http://vtm.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&amp;f[1]=sm_field_program_active%3AAlloo%20bij%20de%20Wegpolitie
        # http://vtm.be/video/?amp%3Bf[1]=sm_field_program_active%3AAlloo%20bij%20de%20Wegpolitie&f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&f[1]=sm_field_program_active%3AAlloo%20bij%20de%20Wegpolitie

        item = MediaItem(title, url)
        return item

    def add_more_recent_videos(self, data):
        """ Preprocesses the data and adds more recent videos.

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

        video_id = self.parentItem.url.rsplit("%3A", 1)[-1]
        recent_url = "https://vtm.be/block/responsive/medialaan_vod/program?offset=0&limit=10&program=%s" % (video_id, )
        recent_data = UriHandler.open(recent_url, proxy=self.proxy)

        # https://vtm.be/video/volledige-afleveringen/id/257124125192000
        regex = r'<a href="/(?<url>[^"]+)"[^>]*>\W+<img[^>]+src="(?<thumburl>[^"]+)"[\w\W]{0,1000}?' \
                r'<div class="item-date">(?<day>\d+)/(?<month>\d+)/(?<year>\d+)</div>\W+<[^>]+>\W+' \
                r'<div[^>]+class="item-caption-title">(?<title>[^<]+)'
        regex = Regexer.from_expresso(regex)
        results = Regexer.do_regex(regex, recent_data)
        for result in results:
            Logger.trace(result)
            item = self.create_video_item_html(result)
            items.append(item)

        return data, items

    def create_video_item_html(self, result_set):
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

        title = result_set['title']
        if title:
            title = title.strip()

        if 'subtitle' in result_set and title:
            title = "%s - %s" % (title, result_set['subtitle'].strip())
        elif 'subtitle' in result_set:
            title = result_set['subtitle'].strip()

        if not title:
            Logger.warning("Item without title found: %s", result_set)
            return None

        url = result_set["url"].replace('  ', ' ')
        if not result_set["url"].startswith("http"):
            url = "%s/%s" % (self.baseUrl, result_set["url"])
        item = MediaItem(title, url, type="video")
        item.thumb = result_set['thumburl']
        item.complete = False

        if "year" in result_set and result_set["year"]:
            item.set_date(result_set["year"], result_set["month"], result_set["day"])
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

        if not self.loggedOn:
            Logger.warning("Cannot log on")
            return None

        data = UriHandler.open(item.url, proxy=self.proxy)
        video_id_regex = '"vodId":"([^"]+)"'
        video_id = Regexer.do_regex(video_id_regex, data)[0]
        return self.__update_video_item(item, video_id)

    def update_live_stream(self, item):
        """ Updates an existing Live Stream MediaItem with more data.

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

        Logger.debug("Updating Live stream")
        item.isPaid = item.isPaid and not self.__hasPremium

        # let's request a token
        token = self.__get_token()

        # What is the channel name to play
        channel = self.channelCode
        if self.channelCode == "q2":
            channel = "2be"
        elif self.channelCode == "stievie":
            channel = item.metaData["channelId"]

        url = "https://stream-live.medialaan.io/stream-live/v1/channels/%s/broadcasts/current/video/?deviceId=%s" % (
            channel,
            AddonSettings.get_client_id().replace("-", "")  # Could be a random int
        )

        auth = {"Authorization": "apikey=%s&access_token=%s" % (self.__apiKey, token)}
        if self.localIP:
            auth.update(self.localIP)

        data = UriHandler.open(url, proxy=self.proxy, no_cache=True, additional_headers=auth)
        json_data = JsonHelper(data)
        hls = json_data.get_value("response", "url", "hls-aes-linear")
        if not hls:
            return item

        # We can do this without DRM apparently.
        if AddonSettings.use_adaptive_stream_add_on(with_encryption=False) or True:
            # get the cookies
            license_server_url = json_data.get_value("response", "drm", "format", "hls-aes", "licenseServerUrl")
            UriHandler.open(license_server_url, proxy=self.proxy, no_cache=True)
            domain = ".license.medialaan.io"
            channel_path = json_data.get_value("response", "broadcast", "channel")

            # we need to fetch the specific cookies to pass on to the Adaptive add-on
            if channel_path == "2be":
                channel_path = "q2"
            path = '/keys/{0}/aes'.format(channel_path)
            cookies = ["CloudFront-Key-Pair-Id", "CloudFront-Policy", "CloudFront-Signature"]
            license_key = ""
            for c in cookies:
                cookie = UriHandler.get_cookie(c, domain, path=path)
                if cookie is None:
                    Logger.error("Missing cookie: %s", c)
                    return item

                value = cookie.value
                license_key = "{0}; {1}={2}".format(license_key, c, value)

            license_key = license_key[2:]
            license_key = "|Cookie={0}|R{{SSM}}|".format(HtmlEntityHelper.url_encode(license_key))
            part = item.create_new_empty_media_part()
            stream = part.append_media_stream(hls, 0)
            M3u8.set_input_stream_addon_input(stream, license_key=license_key)
            item.complete = True
        else:
            Logger.error("Cannot play live-stream without encryption support.")
        return item

    def update_html_clip_item(self, item):
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

        data = UriHandler.open(item.url)
        json_data = Regexer.do_regex(r"Drupal\.settings,\s*({[\w\W]+?})\);\s*//-->", data)
        json_data = JsonHelper(json_data[-1])
        video_info = json_data.get_value('medialaan_player', )

        video_config = None
        for key in video_info:
            Logger.trace("Checking key: %s", key)
            if "videoConfig" not in video_info[key]:
                continue

            video_config = video_info[key]['videoConfig']['video']
            break

        if not video_config:
            Logger.error("No video info found.")

        streams = video_config['formats']
        for stream in streams:
            stream_url = stream['url']
            if stream['type'] == "mp4":
                item.append_single_stream(stream_url, 0)
                item.complete = True

        return item

    def __find_image(self, result_set, fallback=None):
        if "images" in result_set and result_set["images"]:
            first_key = list(result_set["images"].keys())[0]
            images = result_set["images"][first_key]
            images = images.get("16_9_Landscape", images.get("default", {}))
            if "styles" in images and "large" in images["styles"]:
                return images["styles"]["large"]
        return fallback

    def __update_video_item(self, item, video_id):
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
        :param str video_id: the video ID of the item to update.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        # we need a token:
        token = self.__get_token()

        # Set a fixed device ID?
        # deviceId = AddonSettings.get_client_id()
        media_url = "https://vod.medialaan.io/vod/v2/videos/" \
                    "%s" \
                    "/watch?deviceId=%s" % (
                        video_id,
                        AddonSettings.get_client_id().replace("-", "")
                    )

        auth = "apikey=%s&access_token=%s" % (self.__apiKey, token)
        headers = {"Authorization": auth}
        data = UriHandler.open(media_url, proxy=self.proxy, additional_headers=headers)

        json_data = JsonHelper(data)
        dash_info = json_data.get_value("response", "dash-cenc")
        if self.__adaptiveStreamingAvailable and dash_info:
            Logger.debug("Using Dash streams to playback")
            dash_info = json_data.get_value("response", "dash-cenc")
            license_url = dash_info["widevineLicenseServerURL"]
            stream_url = dash_info["url"]
            session_id = json_data.get_value("request", "access_token")

            license_header = {
                "merchant": "medialaan",
                "userId": self.__userId,
                "sessionId": session_id
            }
            license_header = JsonHelper.dump(license_header, False)
            license_headers = "x-dt-custom-data={0}&Content-Type=application/octstream".format(base64.b64encode(license_header))
            license_key = "{0}?specConform=true|{1}|R{{SSM}}|".format(license_url, license_headers or "")

            part = item.create_new_empty_media_part()
            stream = part.append_media_stream(stream_url, 0)
            Mpd.set_input_stream_addon_input(stream, self.proxy, license_key=license_key, license_type="com.widevine.alpha")
            item.complete = True
        else:
            Logger.debug("No Dash streams supported or no Dash streams available. Using M3u8 streams")

            m3u8_url = json_data.get_value("response", "hls-encrypted", "url")
            if not m3u8_url:
                m3u8_url = json_data.get_value("response", "uri")
                # not supported by Kodi: m3u8_url = jsonData.get_value("response", "hls-drm-uri")

            if not m3u8_url:
                XbmcWrapper.show_dialog(
                    LanguageHelper.get_localized_string(LanguageHelper.DrmTitle),
                    LanguageHelper.get_localized_string(LanguageHelper.WidevineLeiaRequired)
                )
                return item

            part = item.create_new_empty_media_part()
            # Set the Range header to a proper value to make all streams start at the beginning. Make
            # sure that a complete TS part comes in a single call otherwise we get stuttering.
            byte_range = 10 * 1024 * 1024
            Logger.debug("Setting an 'Range' http header of bytes=0-%d to force playback at the start "
                         "of a stream and to include a full .ts part.", byte_range)
            part.HttpHeaders["Range"] = 'bytes=0-%d' % (byte_range, )

            for s, b in M3u8.get_streams_from_m3u8(m3u8_url, self.proxy):
                item.complete = True
                part.append_media_stream(s, b)

        return item

    def __get_token(self):
        """ Requests a playback token

        :return: The token data
        :rtype: str

        """
        if not self.loggedOn:
            self.loggedOn = self.log_on()
        if not self.loggedOn:
            Logger.warning("Cannot log on")
            return None

        # Q2:  https://user.medialaan.io/user/v1/gigya/request_token?uid=897b786c46e3462eac81549453680c0d&signature=SM7b5ciP09Z0gbcaCoZ%2B7r4b3uk%3D&timestamp=1484691251&apikey=q2-html5-NNSMRSQSwGMDAjWKexV4e5Vm6eSPtupk&database=q2-sso&_=1484691247493
        # VTM: https://user.medialaan.io/user/v1/gigya/request_token?uid=897b786c46e3462eac81549453680c0d&signature=Ak10FWFpuF2cSXfmGnNIBsJV4ss%3D&timestamp=1481233821&apikey=vtm-b7sJGrKwMJj0VhdZvqLDFvgkJF5NLjNY&database=vtm-sso

        url = "https://user.medialaan.io/user/v1/gigya/request_token?uid=%s&signature=%s&timestamp=%s&apikey=%s&database=%s" % (
            self.__userId,
            HtmlEntityHelper.url_encode(self.__signature),
            self.__signatureTimeStamp,
            HtmlEntityHelper.url_encode(self.__apiKey),
            self.__sso)
        data = UriHandler.open(url, proxy=self.proxy, no_cache=True)
        json_data = JsonHelper(data)
        return json_data.get_value("response")

    def __extract_session_data(self, logon_data, signature_settings):
        logon_json = JsonHelper(logon_data)
        result_code = logon_json.get_value("statusCode")
        Logger.trace("Logging in returned: %s", result_code)
        if result_code != 200:
            Logger.error("Error loging in: %s - %s", logon_json.get_value("errorMessage"),
                         logon_json.get_value("errorDetails"))
            return False

        user_name = logon_json.get_value("profile", "email") or ""
        user_name_configured = AddonSettings.get_setting("mediaan_username") or ""
        if user_name.lower() != user_name_configured.lower():
            Logger.warning("Username for Medialaan changed.")
            return False

        signature_setting = logon_json.get_value("sessionInfo", "login_token")
        if signature_setting:
            Logger.info("Found 'login_token'. Saving it.")
            AddonSettings.set_setting(signature_settings, signature_setting.split("|")[0], store=LOCAL)

        self.__signature = logon_json.get_value("UIDSignature")
        self.__userId = logon_json.get_value("UID")
        self.__signatureTimeStamp = logon_json.get_value("signatureTimestamp")

        self.__hasPremium = logon_json.get_value(
            "data", "authorization", "Stievie_free", "subscription", "id") == "premium"
        self.__premium_channels = logon_json.get_value(
            "data", "authorization", "Stievie_free", "channels")
        return True
