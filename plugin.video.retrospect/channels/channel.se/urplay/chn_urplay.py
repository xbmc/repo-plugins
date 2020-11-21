# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later
import pytz

from resources.lib import chn_class
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.subtitlehelper import SubtitleHelper

from resources.lib.mediaitem import MediaItem
from resources.lib.parserdata import ParserData
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper


class Channel(chn_class.Channel):

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes ====
        self.noImage = "urplayimage.png"

        # setup the urls
        self.mainListUri = "#mainlist_merge"
        self.baseUrl = "https://urplay.se"
        self.swfUrl = "https://urplay.se/assets/jwplayer-6.12-17973009ab259c1dea1258b04bde6e53.swf"

        # Match the "series" API -> shows TV Shows
        self._add_data_parser(self.mainListUri, json=True,
                              name="Show parser with categories",
                              match_type=ParserData.MatchExact,
                              preprocessor=self.merge_add_categories_and_search,
                              parser=["results"], creator=self.create_episode_json_item)

        # Match Videos (programs)
        self._add_data_parser("https://urplay.se/api/bff/v1/search?product_type=program",
                              name="Most viewed", json=True,
                              parser=["results"], creator=self.create_video_item_json_with_show_title)

        self._add_data_parser("*", json=True,
                              name="Json based video parser",
                              preprocessor=self.extract_json_data,
                              parser=["currentProduct", "series", "programs"],
                              creator=self.create_video_item_json)

        self._add_data_parser("*", updater=self.update_video_item)

        # Categories
        cat_reg = r'<a[^>]+href="(?<url>/blad[^"]+/(?<slug>[^"]+))"[^>]*>' \
                  r'(?:<svg[\w\W]{0,2000}?</svg>)?(?<title>[^<]+)<'
        cat_reg = Regexer.from_expresso(cat_reg)
        self._add_data_parser("https://urplay.se/", name="Category parser",
                              match_type=ParserData.MatchExact,
                              parser=cat_reg,
                              creator=self.create_category_item)

        self._add_data_parsers(["https://urplay.se/api/bff/v1/search?play_category",
                                "https://urplay.se/api/bff/v1/search?main_genre",
                                "https://urplay.se/api/bff/v1/search?response_type=category",
                                "https://urplay.se/api/bff/v1/search?type=programradio",
                                "https://urplay.se/api/bff/v1/search?age=",
                                "https://urplay.se/api/bff/v1/search?response_type=limited"],
                               name="Category content", json=True,
                               preprocessor=self.merge_category_items,
                               parser=["results"], creator=self.create_json_item)

        # Searching
        self._add_data_parser("https://urplay.se/search/json", json=True,
                              parser=["programs"], creator=self.create_search_result_program)
        self._add_data_parser("https://urplay.se/search/json", json=True,
                              parser=["series"], creator=self.create_search_result_serie)

        self.mediaUrlRegex = r"urPlayer.init\(([^<]+)\);"

        #===========================================================================================
        # non standard items
        self.__videoItemFound = False

        # There is either a slug lookup or an url lookup
        self.__cateogory_slugs = {
        }

        self.__cateogory_urls = {
            "alla-program":
                "https://urplay.se/api/bff/v1/search?"
                "response_type=limited&"
                "product_type=series&"
                "rows={}&start={}&view=title",

            "barn":
                "https://urplay.se/api/bff/v1/search?"
                "age=children&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}"
                "&view=title",

            "dokumentarfilmer":
                "https://urplay.se/api/bff/v1/search?"
                "main_genre[]=dokument%C3%A4rfilm&main_genre[]=dokument%C3%A4rserie&"
                # "platform=urplay&"
                "singles_and_series=true&view=title&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}"
                "&view=title",

            "drama":
                "https://urplay.se/api/bff/v1/search?"
                "main_genre[]=drama&main_genre[]=kortfilm&main_genre[]=fiktiva%20ber%C3%A4ttelser&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "forelasningar":
                "https://urplay.se/api/bff/v1/search?"
                "main_genre[]=f%C3%B6rel%C3%A4sning&main_genre[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "halsa-och-relationer":
                "https://urplay.se/api/bff/v1/search?"
                "main_genre_must_not[]=forelasning&"
                "main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=kropp%20%26%20sinne&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",
            
            "kultur-och-historia":
                "https://urplay.se/api/bff/v1/search?"
                "main_genre_must_not[]=forelasning&main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=kultur%20%26%20historia&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "natur-och-resor":
                "https://urplay.se/api/bff/v1/search?"
                "main_genre_must_not[]=forelasning&main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=natur%20%26%20resor&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "radio":
                "https://urplay.se/api/bff/v1/search?"
                "type=programradio&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "samhalle":
                "https://urplay.se/api/bff/v1/search?"
                "main_genre_must_not[]=forelasning&main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=samh%C3%A4lle&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "sprak":
                "https://urplay.se/api/bff/v1/search?"
                "main_genre_must_not[]=forelasning&main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=spr%C3%A5k&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "syntolkat":
                "https://urplay.se/api/bff/v1/search?"
                "response_type=category&"
                "is_audio_described=true&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "teckensprak":
                "https://urplay.se/api/bff/v1/search?"
                "response_type=category&"
                "language=sgn-SWE&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "utbildning-och-media":
                "https://urplay.se/api/bff/v1/search?"
                "main_genre_must_not[]=forelasning&"
                "main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=utbildning%20%26%20media&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "vetenskap":
                "https://urplay.se/api/bff/v1/search?"
                "main_genre_must_not[]=forelasning&main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=vetenskap%20%26%20teknik&"
                "singles_and_series=true&"
                "start={}&"
                "view=title"
        }

        self.__timezone = pytz.timezone("Europe/Amsterdam")
        self.__episode_text = LanguageHelper.get_localized_string(LanguageHelper.EpisodeId)
        #===========================================================================================
        # Test cases:
        #   Anaconda Auf Deutch : RTMP, Subtitles

        # ====================================== Actual channel setup STOPS here ===================
        return

    def merge_category_items(self, data):
        """ Merge the multipage category result items into a single list.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        url = self.parentItem.url
        if "{" not in url:
            return data, items

        data = self.__iterate_results(url, max_iterations=10, results_per_page=150)
        return data, items

    def create_category_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        if 'thumburl' in result_set and not result_set['thumburl'].startswith("http"):
            result_set['thumburl'] = "%s/%s" % (self.baseUrl, result_set["thumburl"])

        slug = result_set["slug"]
        url = self.__cateogory_urls.get(slug)

        if url is None:
            Logger.warning("Missing category in list: %s", slug)
            return None

        result_set["url"] = url
        return chn_class.Channel.create_folder_item(self, result_set)

    # noinspection PyUnusedLocal
    def merge_add_categories_and_search(self, data):
        """ Adds some generic items such as search and categories to the main listing.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []
        max_items = 150

        # merge the main list items:
        data = self.__iterate_results(
            "https://urplay.se/api/bff/v1/search?product_type=series&rows={}&start={}",
            results_per_page=max_items,
            max_iterations=11
        )

        categories = {
            LanguageHelper.Popular: "https://urplay.se/api/bff/v1/search?product_type=program&query=&rows={}&start=0&view=most_viewed".format(max_items),
            LanguageHelper.MostRecentEpisodes: "https://urplay.se/api/bff/v1/search?product_type=program&rows={}&start=0&view=published".format(max_items),
            LanguageHelper.LastChance: "https://urplay.se/api/bff/v1/search?product_type=program&rows={}&start=0&view=last_chance".format(max_items),
            LanguageHelper.Categories: "https://urplay.se/",
            LanguageHelper.Search: "searchSite"
        }

        for cat in categories:
            title = "\a.: {} :.".format(LanguageHelper.get_localized_string(cat))
            item = MediaItem(title, categories[cat])
            item.complete = True
            item.dontGroup = True
            items.append(item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def extract_json_data(self, data):
        """ Extracts the JSON data for video parsing

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []
        json_text = Regexer.do_regex(r'ProgramDescription" data-react-props="([^"]+)', data)[0]
        json_text = HtmlEntityHelper.convert_html_entities(json_text)
        json_data = JsonHelper(json_text)

        Logger.debug("Pre-Processing finished")
        return json_data, items

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

        url = "https://urplay.se/search/json?query=%s"
        return chn_class.Channel.search_site(self, url)

    def create_json_item(self, result_set):
        """ Creates a new MediaItem for an folder or video.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        item_type = result_set["format"]
        if item_type == "video":
            return self.create_video_item_json(result_set)
        elif item_type == "audio":
            # Apparently the audio is always linking to a show folder.
            return self.create_episode_json_item(result_set)
        else:
            Logger.warning("Found unknown type: %s", item_type)
            return None

    def create_episode_json_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        title = "%(title)s" % result_set
        url = "%s/serie/%s" % (self.baseUrl, result_set["slug"])
        fanart = "https://assets.ur.se/id/%(id)s/images/1_hd.jpg" % result_set
        thumb = "https://assets.ur.se/id/%(id)s/images/1_l.jpg" % result_set
        item = MediaItem(title, url)
        item.thumb = thumb
        item.description = result_set.get("description")
        item.fanart = fanart
        return item

    def create_video_item_json_with_show_title(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict result_set:             The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        return self.create_video_item_json(result_set, include_show_title=True)

    def create_video_item_json(self, result_set, include_show_title=False):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict result_set:             The result_set of the self.episodeItemRegex
        :param bool include_show_title:     Should we include the show title in the title

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        title = result_set["title"]
        # We could add the main title

        show_title = result_set.get('mainTitle')
        episode = result_set.get('episodeNumber')

        if show_title and include_show_title:
            if bool(episode):
                title = "{} - {} {:02d} - {}".format(show_title, self.__episode_text, episode, title)
            else:
                title = "{} - {}".format(show_title, title)

        elif bool(episode):
            title = "{} {:02d} - {}".format(self.__episode_text, episode, title)

        slug = result_set['slug']
        url = "%s/%s" % (self.baseUrl, slug)

        item = MediaItem(title, url)
        item.type = "video"
        item.description = result_set['description']
        item.complete = False

        images = result_set["image"]
        thumb_fanart = None
        for dimension, url in images.items():
            if dimension.startswith("640x"):
                item.thumb = url
            elif dimension.startswith("1280x"):
                thumb_fanart = url

            if item.thumb and thumb_fanart:
                break

        # if there was a high quality thumb and no fanart (default one), the use the thumb.
        if item.fanart == self.fanart and thumb_fanart:
            item.fanart = thumb_fanart

        duration = result_set.get("duration")
        if duration:
            item.set_info_label("duration", int(duration))

        # Determine the date and keep timezones into account
        # date = result_set.get('publishedAt')
        if "accessiblePlatforms" in result_set and "urplay" in result_set["accessiblePlatforms"]:
            start_date = result_set["accessiblePlatforms"]["urplay"]["startTime"]
            end_date = result_set["accessiblePlatforms"]["urplay"]["endTime"]

            if start_date:
                start_date = start_date.replace(".000Z", "Z")
                date_time = DateHelper.get_datetime_from_string(
                    start_date, date_format="%Y-%m-%dT%H:%M:%SZ", time_zone="UTC")
                date_time = date_time.astimezone(self.__timezone)
                item.set_date(date_time.year, date_time.month, date_time.day,
                              date_time.hour, date_time.minute, date_time.second)
            if end_date:
                end_date = end_date.replace(".000Z", "Z")
                end_date_time = DateHelper.get_datetime_from_string(
                    end_date, date_format="%Y-%m-%dT%H:%M:%SZ", time_zone="UTC")
                end_date_time = end_date_time.astimezone(self.__timezone)
                item.set_expire_datetime(end_date_time)

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
        <script type="text/javascript">/* <![CDATA[ */ var movieFlashVars = "
        image=http://assets.ur.se/id/147834/images/1_l.jpg
        file=/147000-147999/147834-20.mp4
        plugins=http://urplay.se/jwplayer/plugins/gapro-1.swf,http://urplay.se/jwplayer/plugins/sharing-2.swf,http://urplay.se/jwplayer/plugins/captions/captions.swf
        sharing.link=http://urplay.se/147834
        gapro.accountid=UA-12814852-8
        captions.margin=40
        captions.fontsize=11
        captions.back=false
        captions.file=http://undertexter.ur.se/147000-147999/147834-19.tt
        streamer=rtmp://streaming.ur.se/ondemand
        autostart=False"; var htmlVideoElementSource = "http://streaming.ur.se/ondemand/mp4:147834-23.mp4/playlist.m3u8?location=SE"; /* //]]> */ </script>

        """

        data = UriHandler.open(item.url, proxy=self.proxy)
        # Extract stream JSON data from HTML
        streams = Regexer.do_regex(r'Player"[^>]+data-react-props="({[^"]+})"', data)
        json_data = streams[0]
        json_data = HtmlEntityHelper.convert_html_entities(json_data)
        json = JsonHelper(json_data, logger=Logger.instance())
        Logger.trace(json.json)

        item.MediaItemParts = []

        # generic server information
        proxy_data = UriHandler.open("https://streaming-loadbalancer.ur.se/loadbalancer.json",
                                     proxy=self.proxy, no_cache=True)
        proxy_json = JsonHelper(proxy_data)
        proxy = proxy_json.get_value("redirect")
        Logger.trace("Found RTMP Proxy: %s", proxy)

        stream_infos = json.get_value("currentProduct", "streamingInfo")
        part = item.create_new_empty_media_part()
        for stream_type, stream_info in stream_infos.items():
            Logger.trace(stream_info)
            default_stream = stream_info.get("default", False)
            bitrates = {"mp3": 400, "m4a": 250, "sd": 1200, "hd": 2000, "tt": None}
            for quality, bitrate in bitrates.items():
                stream = stream_info.get(quality)
                if stream is None:
                    continue
                stream_url = stream["location"]
                if quality == "tt":
                    part.Subtitle = SubtitleHelper.download_subtitle(
                        stream_url, format="webvtt", proxy=self.proxy)
                    continue

                bitrate = bitrate if default_stream else bitrate + 1
                url = "https://%s/%smaster.m3u8" % (proxy, stream_url)
                part.append_media_stream(url, bitrate)

        item.complete = True
        return item

    def create_search_result_program(self, result_set):
        return self.__create_search_result(result_set, "program")

    def create_search_result_serie(self, result_set):
        return self.__create_search_result(result_set, "serie")

    def __create_search_result(self, result_set, result_type):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex
        :param str result_type:                    Either a Serie or Program

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        # Logger.trace(result_set)

        url = "https://urplay.se/{}/{}".format(result_type, result_set["slug"])
        item = MediaItem(result_set["title"], url)

        asset_id = result_set["ur_asset_id"]
        item.thumb = "https://assets.ur.se/id/{}/images/1_hd.jpg".format(asset_id)
        item.fanart = "https://assets.ur.se/id/{}/images/1_l.jpg".format(asset_id)
        if result_type == "program":
            item.set_info_label("duration", result_set["duration"] * 60)
            item.type = "video"
        return item

    def __iterate_results(self, url_format, results_per_page=150, max_iterations=10):
        """ Retrieves the full dataset for a multi-set search action.

        :param str url_format:             The url format with start and count placeholders
        :param int results_per_page:       The maximum results per request
        :param int max_iterations:         The maximum number of iterations

        :returns A Json response with all results
        :rtype JsonHelper

        Url format should be like:
            https://urplay.se/api/bff/v1/search?product_type=series&rows={}&start={}

        """

        results = None
        for p in range(0, max_iterations):
            url = url_format.format(results_per_page, p * results_per_page)
            data = UriHandler.open(url)
            json_data = JsonHelper(data)
            result_items = json_data.get_value("results", fallback=[])
            if results is None:
                results = json_data
            else:
                results.json["results"] += result_items

            if len(result_items) < results_per_page:
                break

        return results or ""
