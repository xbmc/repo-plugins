# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import chn_class
from helpers.languagehelper import LanguageHelper

from mediaitem import MediaItem
from parserdata import ParserData
from regexer import Regexer
from helpers import subtitlehelper
from logger import Logger
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper


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
        self.mainListUri = "https://urplay.se/api/bff/v1/search?product_type=series&rows=10000&start=0"
        self.baseUrl = "https://urplay.se"
        self.swfUrl = "https://urplay.se/assets/jwplayer-6.12-17973009ab259c1dea1258b04bde6e53.swf"

        # Match the "series" API -> shows TV Shows
        self._add_data_parser(self.mainListUri, json=True,
                              name="Show parser with categories",
                              match_type=ParserData.MatchExact,
                              preprocessor=self.add_categories_and_search,
                              parser=["results"], creator=self.create_json_episode_item)

        # Match Videos (programs)
        self._add_data_parser("https://urplay.se/api/bff/v1/search?product_type=program",
                              name="Most viewed", json=True,
                              parser=["results"], creator=self.create_json_video_item)

        item_regex = r'href="/(?<url>[^/]+/(?<id>\d+)[^"]+)"[^>]*>[^<]+</a>\W+<figure>[\W\w]' \
                     r'{0,3000}?<h2[^>]*>(?<title>[^<]+)</h2>\W+<p[^>]+>\s*(?<description>[^<]+?)' \
                     r'\s*<span class="usp">(?<description2>[^<]+)'
        item_regex = r'href="/(?<url>[^/]+/(?<id>\d+)[^"]+)"[^>]*>[^<]+</a>\W+<figure>[\W\w]' \
                     r'{0,3000}?<h2[^>]*>(?<title>[^<]+)</h2>\W+<p[^>]+>\s{0,4}(?<description>[^<]*?)' \
                     r'\s+(?:(?<duration>\d{1,3})\smin\s.\s+)?<span class="usp">(?<description2>[^<]+)'
        item_regex = Regexer.from_expresso(item_regex)

        single_video_regex = r'<meta \w+="name" content="(?:[^:]+: )?(?<title>[^"]+)' \
                             r'"[^>]*>\W*<meta \w+="description" content="(?<description>[^"]+)"' \
                             r'[^>]*>\W*<meta \w+="url" content="(?:[^"]+/(?<url>\w+/' \
                             r'(?<id>\d+)[^"]+))"[^>]*>\W*<meta \w+="thumbnailURL[^"]*" ' \
                             r'content="(?<thumbnail>[^"]+)"[^>]*>\W+<meta \w+="uploadDate" ' \
                             r'content="(?<date>[^"]+)"'
        single_video_regex = Regexer.from_expresso(single_video_regex)

        self._add_data_parser("*", parser=item_regex, preprocessor=self.get_video_section,
                              creator=self.create_video_item)
        self._add_data_parser("*", parser=single_video_regex, preprocessor=self.get_video_section,
                              creator=self.create_single_video_item, updater=self.update_video_item)

        # Folders (Seasons)
        season_regex = '<li[^>]+>[^>]+data-description="(?<description>[^"]+)"[^>]+' \
                       'data-asset-id="(?<id>[^"]+)"[^>]+>[\n\r ]*(?<title>[^<]+?)[\n\r ]*<'
        season_regex = Regexer.from_expresso(season_regex)
        self._add_data_parser("*", name="Season Folders",
                              parser=season_regex, creator=self.create_folder_item)

        # Categories
        cat_reg = r'<a[^>]+href="(?<url>/blad[^"]+)"[^>]*>(?<title>[^<]+)<'
        cat_reg = Regexer.from_expresso(cat_reg)
        self._add_data_parser("https://urplay.se/", name="Category parser",
                              match_type=ParserData.MatchExact,
                              parser=cat_reg,
                              creator=self.create_category_item)

        self._add_data_parser("https://urplay.se/bladdra/", name="Category listing Videos",
                              preprocessor=self.__find_category_videos,
                              parser=item_regex, creator=self.create_video_item)

        self._add_data_parser("https://urplay.se/bladdra/", name="Category listing Folders",
                              preprocessor=self.__find_category_folders,
                              parser=item_regex, creator=self.create_folder_item)

        # Searching
        self._add_data_parser("https://urplay.se/search/json", json=True,
                              parser=["programs"], creator=self.create_search_result_program)
        self._add_data_parser("https://urplay.se/search/json", json=True,
                              parser=["series"], creator=self.create_search_result_serie)

        self.mediaUrlRegex = r"urPlayer.init\(([^<]+)\);"

        #===========================================================================================
        # non standard items
        self.__videoItemFound = False

        #===========================================================================================
        # Test cases:
        #   Anaconda Auf Deutch : RTMP, Subtitles

        # ====================================== Actual channel setup STOPS here ===================
        return

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

        result_set["url"] = "%s?rows=1000&start=0" % (result_set["url"],)
        return chn_class.Channel.create_folder_item(self, result_set)

    def add_categories_and_search(self, data):
        """ Adds some generic items such as search and categories to the main listing.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []
        max_items = 200
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
            item.thumb = self.noImage
            item.complete = True
            item.icon = self.icon
            item.dontGroup = True
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

        url = "https://urplay.se/search/json?query=%s"
        return chn_class.Channel.search_site(self, url)

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

        title = "%(title)s" % result_set
        url = "%s/serie/%s" % (self.baseUrl, result_set["slug"])
        fanart = "https://assets.ur.se/id/%(id)s/images/1_hd.jpg" % result_set
        thumb = "https://assets.ur.se/id/%(id)s/images/1_l.jpg" % result_set
        item = MediaItem(title, url)
        item.thumb = thumb
        item.description = result_set.get("description")
        item.fanart = fanart
        item.icon = self.icon
        return item

    def create_folder_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        result_set["url"] = "https://urplay.se/series/list_programs?ur_asset_id={}".format(result_set["id"])
        item = chn_class.Channel.create_folder_item(self, result_set)
        if item is None:
            return item

        item.HttpHeaders["X-Requested-With"] = "XMLHttpRequest"
        return item

    def get_video_section(self, data):
        """ Finds the part in the HTML that contains the videos for a show.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        data = data[:data.find('<h2>Relaterade</h2>')]
        Logger.debug("Pre-Processing finished")
        return data, items

    def create_json_video_item(self, result_set):
        """ This method creates a new MediaItem from the Regular Expression or Json
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

        main_title = result_set.get("mainTitle")
        if main_title:
            title = "{} - {}".format(main_title, result_set["title"])
        else:
            title = "%(title)s" % result_set
        url = "%s/program/%s" % (self.baseUrl, result_set["slug"])
        fanart = "https://assets.ur.se/id/%(id)s/images/1_hd.jpg" % result_set
        thumb = "https://assets.ur.se/id/%(id)s/images/1_l.jpg" % result_set
        item = MediaItem(title, url)
        item.type = "video"
        item.thumb = thumb
        item.description = result_set.get("description")
        item.fanart = fanart
        item.icon = self.icon
        if "duration" in result_set:
            item.set_info_label("duration", result_set["duration"])

        if "accessiblePlatforms" in result_set and "urplay" in result_set["accessiblePlatforms"]:
            start_time = result_set["accessiblePlatforms"]["urplay"]["startTime"]
            start_date_parts = [int(x) for x in start_time[0:10].split("-")]
            item.set_date(*start_date_parts)
        return item

    def create_single_video_item(self, result_set):
        """ If no items were found, we should find the main item on the page and create a
        MediaItem of type 'video' using the result_set from the regex for this item.

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

        if self.__videoItemFound:
            return None
        return self.create_video_item(result_set)

    def create_video_item(self, result_set):
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

        # Logger.Trace(resultSet)

        title = result_set["title"]
        url = "%s/%s" % (self.baseUrl, result_set["url"])
        thumb = "https://assets.ur.se/id/%(id)s/images/1_l.jpg" % result_set
        item = MediaItem(title, url)
        item.type = "video"
        item.thumb = thumb
        item.description = "%(description)s\n%(description2)s" % result_set
        item.fanart = self.parentItem.fanart
        item.icon = self.icon
        item.complete = False

        duration = result_set.get("duration")
        if duration:
            item.set_info_label("duration", int(duration) * 60)

        self.__videoItemFound = True
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
        streams = Regexer.do_regex(self.mediaUrlRegex, data)
        json_data = streams[0]
        json = JsonHelper(json_data, logger=Logger.instance())
        Logger.trace(json.json)

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()

        streams = {
            # No longer used I think
            "file_flash": 900,
            "file_mobile": 750,
            "file_hd": 2000,
            "file_html5": 850,
            "file_html5_hd": 2400,

            'file_rtmp': 900,
            'file_rtmp_hd': 2400,
            'file_http_sub': 750,
            'file_http': 900,
            'file_http_sub_hd': 2400,
            'file_http_hd': 2500
        }

        # u'file_rtmp_hd': u'urplay/mp4: 178000-178999/178963-7.mp4',
        # u'file_rtmp': u'urplay/mp4: 178000-178999/178963-11.mp4',
        #
        # u'file_http': u'urplay/_definst_/mp4: 178000-178999/178963-11.mp4/',
        # u'file_http_sub_hd': u'urplay/_definst_/mp4: 178000-178999/178963-25.mp4/',
        # u'file_http_sub': u'urplay/_definst_/mp4: 178000-178999/178963-28.mp4/',
        # u'file_http_hd': u'urplay/_definst_/mp4: 178000-178999/178963-7.mp4/',

        # generic server information
        proxy = json.get_value("streaming_config", "streamer", "redirect")
        if proxy is None:
            proxy_data = UriHandler.open("https://streaming-loadbalancer.ur.se/loadbalancer.json",
                                         proxy=self.proxy, no_cache=True)
            proxy_json = JsonHelper(proxy_data)
            proxy = proxy_json.get_value("redirect")
        Logger.trace("Found RTMP Proxy: %s", proxy)

        rtmp_application = json.get_value("streaming_config", "rtmp", "application")
        Logger.trace("Found RTMP Application: %s", rtmp_application)

        # find all streams
        for stream_type in streams:
            if stream_type not in json.json:
                Logger.debug("%s was not found as stream.", stream_type)
                continue

            bitrate = streams[stream_type]
            stream_url = json.get_value(stream_type)
            Logger.trace(stream_url)
            if not stream_url:
                Logger.debug("%s was found but was empty as stream.", stream_type)
                continue

            if stream_url.startswith("se/") or ":se/" in stream_url:
                # or json.get_value("only_in_sweden"): -> will be in the future

                only_sweden = True
                Logger.warning("Streams are only available in Sweden: onlySweden=%s", only_sweden)
                # No need to replace the se/ part. Just log.
                # streamUrl = streamUrl.replace("se/", "", 1)

            # although all urls can be handled via RTMP, let's not do that and make
            # the HTTP ones HTTP
            always_rtmp = False
            if always_rtmp or "_rtmp" in stream_type:
                url = "rtmp://%s/%s/?slist=mp4:%s" % (proxy, rtmp_application, stream_url)
                url = self.get_verifiable_video_url(url)
            elif "_http" in stream_type:
                url = "https://%s/%smaster.m3u8" % (proxy, stream_url)
            else:
                Logger.warning("Unsupported Stream Type: %s", stream_type)
                continue
            part.append_media_stream(url.strip("/"), bitrate)

        # get the subtitles
        captions = json.get_value("subtitles")
        subtitle = None
        for caption in captions:
            language = caption["label"]
            default = caption["default"]
            url = caption["file"]
            if url.startswith("//"):
                url = "https:%s" % (url, )
            Logger.debug("Found subtitle language: %s [Default=%s]", language, default)
            if "Svenska" in language:
                Logger.debug("Selected subtitle language: %s", language)
                file_name = caption["file"]
                file_name = file_name[file_name.rindex("/") + 1:] + ".srt"
                if url.endswith("vtt"):
                    subtitle = subtitlehelper.SubtitleHelper.download_subtitle(
                        url, file_name, "webvtt", proxy=self.proxy)
                else:
                    subtitle = subtitlehelper.SubtitleHelper.download_subtitle(
                        url, file_name, "ttml", proxy=self.proxy)
                break

        if subtitle is not None:
            part.Subtitle = subtitle

        item.complete = True
        return item

    def create_search_result_program(self, result_set):
        return self.__create_search_result(result_set, "program")

    def create_search_result_serie(self, result_set):
        return self.__create_search_result(result_set, "serie")

    def __find_category_videos(self, data):
        data = data[:data.find("product-browsing-list")]
        return self.__split_categories(data)[0], []

    def __find_category_folders(self, data):
        return self.__split_categories(data)[1], []

    def __split_categories(self, data):
        return data.split("product-browsing-list")

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
