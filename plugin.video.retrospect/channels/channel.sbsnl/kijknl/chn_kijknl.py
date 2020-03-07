# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import datetime

from resources.lib import chn_class
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.subtitlehelper import SubtitleHelper
from resources.lib.parserdata import ParserData

from resources.lib.mediaitem import MediaItem
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.mpd import Mpd
from resources.lib.regexer import Regexer
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.addonsettings import AddonSettings
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
        # setup the urls
        self.baseUrl = "https://www.kijk.nl"
        # Just retrieve a single page with 500 items (should be all)

        use_html = False
        if use_html:
            self.mainListUri = "https://www.kijk.nl/programmas"
        else:
            self.mainListUri = "https://api.kijk.nl/v1/default/sections/programs-abc-0123456789abcdefghijklmnopqrstuvwxyz?limit=350&offset=0"

        self.__channelId = self.channelCode
        if self.channelCode == 'veronica':
            self.noImage = "veronicaimage.png"
            self.__channelId = "veronicatv"

        elif self.channelCode == 'sbs':
            self.noImage = "sbs6image.jpg"
            self.__channelId = "sbs6"

        elif self.channelCode == 'sbs9':
            self.noImage = "sbs9image.png"

        elif self.channelCode == 'net5':
            self.noImage = "net5image.png"

        else:
            self.noImage = "kijkimage.png"

        # setup the main parsing data
        self._add_data_parser("https://api.kijk.nl/v1/default/sections/programs-abc",
                              name="Mainlist Json", json=True,
                              preprocessor=self.add_others,
                              parser=["items", ], creator=self.create_json_episode_item)

        self._add_data_parser("https://www.kijk.nl/programmas", match_type=ParserData.MatchExact,
                              name="Mainlist from HTML", json=True,
                              preprocessor=self.extract_main_list_json)

        self._add_data_parser("https://api.kijk.nl/v2/templates/page/format/",
                              name="Videos from the main show format page", json=True,
                              parser=["components", 3, "data", "items", 2, "data", "items"],
                              creator=self.create_json_season_item)

        self._add_data_parser("#lastweek",
                              name="Last week listing", json=True,
                              preprocessor=self.list_dates)

        self._add_data_parsers(["https://api.kijk.nl/v2/templates/page/missed/all/",
                               "https://api.kijk.nl/v1/default/sections/missed-all-"],
                               name="Day listing", json=True, preprocessor=self.extract_day_items)

        self._add_data_parser("https://api.kijk.nl/v1/default/searchresultsgrouped",
                              name="VideoItems Json", json=True,
                              parser=[], creator=self.create_json_search_item)

        self._add_data_parsers(["https://api.kijk.nl/v1/default/sections/series",
                               "https://api.kijk.nl/v1/default/seasons/"],
                               name="VideoItems Json", json=True,
                               parser=["items", ], creator=self.create_json_video_item)

        self._add_data_parser("https://api.kijk.nl/v2/default/sections/popular",
                              name="Popular items Json", json=True,
                              parser=["items", ], creator=self.create_json_popular_item)

        self._add_data_parser("https://embed.kijk.nl/",
                              updater=self.update_json_video_item)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:
        #  Piets Weer: no clips
        #  Achter gesloten deuren: seizoenen
        #  Wegmisbruikers: episodes and clips and both pages
        #  Utopia: no clips
        #  Grand Designs has almost all encrypted/non-encrypted/brigthcove streams

        # ====================================== Actual channel setup STOPS here =======================================
        UriHandler.set_cookie(name="OPTOUTMULTI", value="0:0%7Cc5:0%7Cc1:0%7Cc4:0%7Cc3:0%7Cc2:0", domain=".kijk.nl")
        return

    def extract_main_list_json(self, data):
        """ Extracts the main list JSON data from the HTML response.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        data, items = self.add_others(data)
        start_string = "window.__REDUX_STATE__ = "
        start_data = data.index(start_string)
        end_data = data.index("</script><script async=")
        data = data[start_data + len(start_string):end_data]
        data = JsonHelper(data)
        letters = data.get_value("reduxAsyncConnect", "page", "components", 1, "data", "items", 1, "data", "items")
        for letter_data in letters:
            letter_data = letter_data["data"]
            Logger.trace("Processing '%s'", letter_data["title"])
            for item in letter_data["items"]:
                episode = self.create_json_episode_item(item)
                items.append(episode)
        return data, items

    def add_others(self, data):
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

        others = MediaItem("\b.: Populair :.", "https://api.kijk.nl/v2/default/sections/popular_PopularVODs?offset=0")
        items.append(others)

        days = MediaItem("\b.: Deze week :.", "#lastweek")
        items.append(days)

        search = MediaItem("\b.: Zoeken :.", "searchSite")
        search.complete = True
        search.dontGroup = True
        search.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        items.append(search)

        if self.channelCode == "veronica":
            live = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
            live_radio = MediaItem("Radio Veronica {}".format(live), "")
            live_radio.type = "video"
            live_radio.dontGroup = True

            part = live_radio.create_new_empty_media_part()
            live_stream = "https://talparadiohls-i.akamaihd.net/hls/live/585615/VR-Veronica-1/playlist.m3u8"
            if AddonSettings.use_adaptive_stream_add_on(with_encryption=False, channel=self):
                stream = part.append_media_stream(live_stream, 0)
                M3u8.set_input_stream_addon_input(stream, self.proxy)
                live_radio.complete = True
            else:
                for s, b in M3u8.get_streams_from_m3u8(live_stream, self.proxy):
                    live_radio.complete = True
                    part.append_media_stream(s, b)

            items.append(live_radio)

        Logger.debug("Pre-Processing finished")
        return data, items

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

        url = "https://api.kijk.nl/v1/default/searchresultsgrouped?search=%s"
        return chn_class.Channel.search_site(self, url)

    def list_dates(self, data):
        """ Generates a list of the past week days.

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

        # https://api.kijk.nl/v2/templates/page/missed/all/20180201
        days = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        for i in range(0, 7):
            date = datetime.datetime.now() - datetime.timedelta(days=i)
            # https://api.kijk.nl/v2/templates/page/missed/all/20180626
            # url = "https://api.kijk.nl/v2/templates/page/missed/all/{0}{1:02d}{2:02d}".format(date.year, date.month, date.day)
            # https://api.kijk.nl/v1/default/sections/missed-all-20180619
            url = "https://api.kijk.nl/v1/default/sections/missed-all-{0}{1:02d}{2:02d}".format(date.year, date.month, date.day)
            if i == 0:
                title = LanguageHelper.get_localized_string(LanguageHelper.Today)
            elif i == 1:
                title = LanguageHelper.get_localized_string(LanguageHelper.Yesterday)
            elif i == 2:
                title = LanguageHelper.get_localized_string(LanguageHelper.DayBeforeYesterday)
            else:
                day_name = days[date.weekday()]
                title = day_name

            date_item = MediaItem(title, url)
            date_item.set_date(date.year, date.month, date.day)
            items.append(date_item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def extract_day_items(self, data):
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
        json = JsonHelper(data)
        page_items = json.get_value('items')
        for item in page_items:
            video_item = self.create_json_video_item(item, prepend_serie=True)
            if video_item:
                items.append(video_item)

        return data, items

    def create_json_search_item(self, result_set):
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

        if 'type' in result_set:
            item_type = result_set['type']
            if item_type == 'series':
                return self.create_json_episode_item(result_set)
            elif item_type == 'episode' or item_type == 'clip':
                return self.create_json_video_item(result_set, prepend_serie=True)
        return None

    def create_json_season_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        # {
        #     "seasonNumber": 3,
        #     "id": "season-3",
        #     "episodesId": "achtergeslotendeuren.net5-season-3-episodes",
        #     "clipsId": "achtergeslotendeuren.net5-season-3-clips",
        #     "title": "Seizoen 3",
        #     "format": "achtergeslotendeuren",
        #     "channel": "net5",
        #     "episodesLink": "https://api.kijk.nl/v1/default/seasons/achtergeslotendeuren.net5/3/episodes",
        #     "clipsLink": "https://api.kijk.nl/v1/default/seasons/achtergeslotendeuren.net5/3/clips"
        # }
        # https://api.kijk.nl/v1/default/seasons/achtergeslotendeuren.net5/2/episodes?limit=100&offset=1

        url = "{}?limit=100&offset=1".format(result_set["episodesLink"])
        item = MediaItem(result_set["title"], url)
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

        channel_id = result_set["channel"]
        if self.__channelId and channel_id != self.__channelId:
            return None

        title = result_set["title"]

        use_season = False
        if use_season:
            url = "https://api.kijk.nl/v2/templates/page/format/{}".format(result_set["id"])
        else:
            url = "https://api.kijk.nl/v1/default/sections/series-%(id)s_Episodes-season-0?limit=100&offset=0" % result_set

        item = MediaItem(title, url)
        item.description = result_set.get("synopsis", None)

        if "retina_image_pdp_header" in result_set["images"]:
            # noinspection PyTypeChecker
            item.fanart = result_set["images"]["retina_image_pdp_header"]
        if "retina_image" in result_set["images"]:
            # noinspection PyTypeChecker
            item.thumb = result_set["images"]["retina_image"]
        elif "nonretina_image" in result_set["images"]:
            # noinspection PyTypeChecker
            item.thumb = result_set["images"]["nonretina_image"]

        return item

    def create_json_popular_item(self, result_set):
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

        item = self.create_json_video_item(result_set, prepend_serie=True)
        if item is None:
            return None

        item.name = "%s - %s" % (item.name, result_set["seriesTitle"])
        return item

    def create_json_video_item(self, result_set, prepend_serie=False):
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

        if not result_set.get("available", True):
            Logger.warning("Item not available: %s", result_set)
            return None

        item = self.create_json_episode_item(result_set)
        if item is None:
            return None

        if prepend_serie and 'seriesTitle' in result_set:
            item.name = "{0} - {1}".format(item.name, result_set['seriesTitle'])
        elif 'seriesTitle' in result_set:
            item.name = result_set['seriesTitle']

        item.type = "video"
        # Older URL
        item.url = "https://embed.kijk.nl/api/video/%(id)s?id=kijkapp&format=DASH&drm=CENC" % result_set
        # New URL
        # item.url = "https://embed.kijk.nl/video/%(id)s" % result_set

        if 'subtitle' in result_set:
            item.name = "{0} - {1}".format(item.name, result_set['subtitle'])

        if "date" in result_set:
            date = result_set["date"].split("+")[0]
            # 2016-12-25T17:58:00+01:00
            time_stamp = DateHelper.get_date_from_string(date, "%Y-%m-%dT%H:%M:%S")
            item.set_date(*time_stamp[0:6])

        return item

    def update_json_video_item(self, item):
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

        headers = {"accept": "application/vnd.sbs.ovp+json; version=2.0"}
        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=headers)

        if UriHandler.instance().status.code == 404:
            Logger.warning("No normal stream found. Trying newer method")
            new_url = item.url.replace("https://embed.kijk.nl/api/", "https://embed.kijk.nl/")
            item.url = new_url[:new_url.index("?")]
            return self.__update_embedded_video(item)

        json = JsonHelper(data)
        embed_url = json.get_value("metadata", "embedURL")
        if embed_url:
            Logger.warning("Embed URL found. Using that to determine the streams.")
            item.url = embed_url
            try:
                return self.__update_embedded_video(item)
            except:
                Logger.warning("Failed to update embedded item:", exc_info=True)

        use_adaptive_with_encryption = AddonSettings.use_adaptive_stream_add_on(with_encryption=True, channel=self)
        mpd_info = json.get_value("entitlements", "play")

        # is there MPD information in the API response?
        if mpd_info is not None:
            return self.__update_video_from_mpd(item, mpd_info, use_adaptive_with_encryption)

        # Try the plain M3u8 streams
        part = item.create_new_empty_media_part()
        m3u8_url = json.get_value("playlist")
        use_adaptive = AddonSettings.use_adaptive_stream_add_on(channel=self)

        # with the Accept: application/vnd.sbs.ovp+json; version=2.0 header, the m3u8 streams that
        # are brightcove based have an url paramter instead of an empty m3u8 file
        Logger.debug("Trying standard M3u8 streams.")
        if m3u8_url != "https://embed.kijk.nl/api/playlist/.m3u8" \
                and "hostingervice=brightcove" not in m3u8_url:
            for s, b in M3u8.get_streams_from_m3u8(m3u8_url, self.proxy, append_query_string=True):
                if "_enc_" in s:
                    continue

                if use_adaptive:
                    # we have at least 1 none encrypted streams
                    Logger.info("Using HLS InputStreamAddon")
                    strm = part.append_media_stream(m3u8_url, 0)
                    M3u8.set_input_stream_addon_input(strm, proxy=self.proxy)
                    item.complete = True
                    return item

                part.append_media_stream(s, b)
                item.complete = True
            return item

        Logger.warning("No M3u8 data found. Falling back to BrightCove")
        video_id = json.get_value("vpakey")
        # videoId = json.get_value("videoId") -> Not all items have a videoId
        mpd_manifest_url = "https://embed.kijk.nl/video/%s?width=868&height=491" % (video_id,)
        referer = "https://embed.kijk.nl/video/%s" % (video_id,)

        data = UriHandler.open(mpd_manifest_url, proxy=self.proxy, referer=referer)
        # First try to find an M3u8
        m3u8_urls = Regexer.do_regex('https:[^"]+.m3u8', data)
        for m3u8_url in m3u8_urls:
            m3u8_url = m3u8_url.replace("\\", "")

            # We need the actual URI to make this work, so fetch it.
            m3u8_url = UriHandler.header(m3u8_url, proxy=self.proxy)[-1]
            Logger.debug("Found direct M3u8 in brightcove data.")
            if use_adaptive:
                # we have at least 1 none encrypted streams
                Logger.info("Using HLS InputStreamAddon")
                strm = part.append_media_stream(m3u8_url, 0)
                M3u8.set_input_stream_addon_input(strm, proxy=self.proxy)
                item.complete = True
                return item

            for s, b in M3u8.get_streams_from_m3u8(m3u8_url, self.proxy, append_query_string=True):
                item.complete = True
                part.append_media_stream(s, b)

            return item

        return self.__update_video_from_brightcove(item, data, use_adaptive_with_encryption)

    def __update_embedded_video(self, item):
        """ Updates video items that are encrypted. This could be the default for Krypton!

        :param MediaItem item: The item to update.

        :return: An updated item.
        :rtype: MediaItem

        """

        data = UriHandler.open(item.url, proxy=self.proxy)
        start_needle = "var playerConfig ="
        start_data = data.index(start_needle) + len(start_needle)
        end_data = data.index("var talpaPlayer")
        data = data[start_data:end_data].strip().rstrip(";")

        json = JsonHelper(data)
        has_drm_only = True
        adaptive_available = AddonSettings.use_adaptive_stream_add_on(with_encryption=False, channel=self)
        adaptive_available_encrypted = AddonSettings.use_adaptive_stream_add_on(with_encryption=True, channel=self)

        for play_list_entry in json.get_value("playlist"):
            part = item.create_new_empty_media_part()
            for source in play_list_entry["sources"]:
                stream_type = source["type"]
                stream_url = source["file"]
                stream_drm = source.get("drm")

                if not stream_drm:
                    has_drm_only = False
                    if stream_type == "m3u8":
                        Logger.debug("Found non-encrypted M3u8 stream: %s", stream_url)
                        M3u8.update_part_with_m3u8_streams(part, stream_url, proxy=self.proxy, channel=self)
                        item.complete = True
                    elif stream_type == "dash" and adaptive_available:
                        Logger.debug("Found non-encrypted Dash stream: %s", stream_url)
                        stream = part.append_media_stream(stream_url, 1)
                        Mpd.set_input_stream_addon_input(stream, proxy=self.proxy)
                        item.complete = True
                    else:
                        Logger.debug("Unknown stream source: %s", source)

                else:
                    compatible_drm = "widevine"
                    if compatible_drm not in stream_drm or stream_type != "dash":
                        Logger.debug("Found encrypted %s stream: %s", stream_type, stream_url)
                        continue

                    Logger.debug("Found Widevine encrypted Dash stream: %s", stream_url)
                    license_url = stream_drm[compatible_drm]["url"]
                    pid = stream_drm[compatible_drm]["releasePid"]
                    encryption_json = '{"getRawWidevineLicense":' \
                                      '{"releasePid":"%s", "widevineChallenge":"b{SSM}"}' \
                                      '}' % (pid,)

                    headers = {
                        "Content-Type": "application/json",
                        "Origin": "https://embed.kijk.nl",
                        "Referer": stream_url
                    }

                    encryption_key = Mpd.get_license_key(
                        license_url, key_type=None, key_value=encryption_json, key_headers=headers)

                    stream = part.append_media_stream(stream_url, 0)
                    Mpd.set_input_stream_addon_input(
                        stream, proxy=self.proxy, license_key=encryption_key)
                    item.complete = True

            subs = [s['file'] for s in play_list_entry.get("tracks", []) if s.get('kind') == "captions"]
            if subs:
                subtitle = SubtitleHelper.download_subtitle(subs[0], format="webvtt")
                part.Subtitle = subtitle

        if has_drm_only and not adaptive_available_encrypted:
            XbmcWrapper.show_dialog(
                LanguageHelper.get_localized_string(LanguageHelper.DrmTitle),
                LanguageHelper.get_localized_string(LanguageHelper.WidevineLeiaRequired)
            )
        return item

    def __update_video_from_mpd(self, item, mpd_info, use_adaptive_with_encryption):
        """ Updates an existing MediaItem with more data based on an MPD stream.

        :param dict[str,str] mpd_info:              Stream info retrieved from the stream json.
        :param bool use_adaptive_with_encryption:   Do we use the Adaptive InputStream add-on?
        :param MediaItem item:                      The original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug("Updating streams using BrightCove data.")

        part = item.create_new_empty_media_part()
        mpd_manifest_url = "https:{0}".format(mpd_info["mediaLocator"])
        mpd_data = UriHandler.open(mpd_manifest_url, proxy=self.proxy)
        subtitles = Regexer.do_regex(r'<BaseURL>([^<]+\.vtt)</BaseURL>', mpd_data)

        if subtitles:
            Logger.debug("Found subtitle: %s", subtitles[0])
            subtitle = SubtitleHelper.download_subtitle(subtitles[0],
                                                        proxy=self.proxy,
                                                        format="webvtt")
            part.Subtitle = subtitle

        if use_adaptive_with_encryption:
            # We can use the adaptive add-on with encryption
            Logger.info("Using MPD InputStreamAddon")
            license_url = Regexer.do_regex('licenseUrl="([^"]+)"', mpd_data)[0]
            token = "Bearer {0}".format(mpd_info["playToken"])
            key_headers = {"Authorization": token}
            license_key = Mpd.get_license_key(license_url, key_headers=key_headers)

            stream = part.append_media_stream(mpd_manifest_url, 0)
            Mpd.set_input_stream_addon_input(stream, self.proxy, license_key=license_key)
            item.complete = True
        else:
            XbmcWrapper.show_dialog(
                LanguageHelper.get_localized_string(LanguageHelper.DrmTitle),
                LanguageHelper.get_localized_string(LanguageHelper.WidevineLeiaRequired)
            )

        return item

    def __update_video_from_brightcove(self, item, data, use_adaptive_with_encryption):
        """ Updates an existing MediaItem with more data based on an MPD stream.

        :param str data:                            Stream info retrieved from BrightCove.
        :param bool use_adaptive_with_encryption:   Do we use the Adaptive InputStream add-on?
        :param MediaItem item:                      The original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        part = item.create_new_empty_media_part()
        # Then try the new BrightCove JSON
        bright_cove_regex = '<video[^>]+data-video-id="(?<videoId>[^"]+)[^>]+data-account="(?<videoAccount>[^"]+)'
        bright_cove_data = Regexer.do_regex(Regexer.from_expresso(bright_cove_regex), data)
        if not bright_cove_data:
            Logger.warning("Error updating using BrightCove data: %s", item)
            return item

        Logger.info("Found new BrightCove JSON data")
        bright_cove_url = 'https://edge.api.brightcove.com/playback/v1/accounts/' \
                          '%(videoAccount)s/videos/%(videoId)s' % bright_cove_data[0]
        headers = {
            "Accept": "application/json;pk=BCpkADawqM3ve1c3k3HcmzaxBvD8lXCl89K7XEHiKutxZArg2c5RhwJHJANOwPwS_4o7UsC4RhIzXG8Y69mrwKCPlRkIxNgPQVY9qG78SJ1TJop4JoDDcgdsNrg"
        }

        bright_cove_data = UriHandler.open(bright_cove_url, proxy=self.proxy, additional_headers=headers)
        bright_cove_json = JsonHelper(bright_cove_data)
        streams = [d for d in bright_cove_json.get_value("sources") if d["container"] == "M2TS"]
        # Old filter
        # streams = filter(lambda d: d["container"] == "M2TS", bright_cove_json.get_value("sources"))
        if not streams:
            Logger.warning("Error extracting streams from BrightCove data: %s", item)
            return item

        # noinspection PyTypeChecker
        stream_url = streams[0]["src"]

        # these streams work better with the the InputStreamAddon because it removes the
        # "range" http header
        if use_adaptive_with_encryption:
            Logger.info("Using InputStreamAddon for playback of HLS stream")
            strm = part.append_media_stream(stream_url, 0)
            strm.add_property("inputstreamaddon", "inputstream.adaptive")
            strm.add_property("inputstream.adaptive.manifest_type", "hls")
            item.complete = True
            return item

        for s, b in M3u8.get_streams_from_m3u8(stream_url, self.proxy):
            item.complete = True
            part.append_media_stream(s, b)
        return item
