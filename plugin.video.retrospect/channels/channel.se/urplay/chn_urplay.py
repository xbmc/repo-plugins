# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later
import pytz

from resources.lib import chn_class, mediatype, contenttype
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.subtitlehelper import SubtitleHelper

from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.parserdata import ParserData
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.retroconfig import Config
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
                              preprocessor=self.merge_add_categories_and_search)

        self._add_data_parser("#tvshows", preprocessor=self.merge_tv_show,
                              name="Main listing of merged TV Shows.", json=True,
                              parser=["results"], creator=self.create_episode_json_item)

        self._add_data_parser("https://urplay.se/api/v1/series", json=True,
                              name="Main serie content parser",
                              parser=["programs"], creator=self.create_video_item_json)

        self._add_data_parser("https://urplay.se/api/v1/series", json=True,
                              name="Main serie season parser",
                              parser=["seasonLabels"], creator=self.create_season_item,
                              postprocessor=self.check_seasons)

        # Match Videos (programs)
        self._add_data_parser("https://urplay.se/api/v1/search?product_type=program",
                              name="Most viewed", json=True,
                              parser=["results"], creator=self.create_video_item_json_with_show_title)

        self._add_data_parser("*", json=True,
                              name="Json based video parser",
                              parser=["accessibleEpisodes"],
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
        self._add_data_parsers(["https://urplay.se/api/v1/search?play_category",
                                "https://urplay.se/api/v1/search?main_genre",
                                "https://urplay.se/api/v1/search?response_type=category",
                                "https://urplay.se/api/v1/search?type=programradio",
                                "https://urplay.se/api/v1/search?age=",
                                "https://urplay.se/api/v1/search?response_type=limited",
                                "#category"],
                               name="Category content", json=True,
                               preprocessor=self.merge_category_items,
                               parser=["results"], creator=self.create_search_result)

        # Searching
        self._add_data_parser("https://urplay.se/api/v1/search", json=True,
                              parser=["results"], creator=self.create_search_result)

        self.mediaUrlRegex = r"urPlayer.init\(([^<]+)\);"

        #===========================================================================================
        # non standard items
        self.__videoItemFound = False

        # There is either a slug lookup or an url lookup
        self.__cateogory_slugs = {
        }

        self.__cateogory_urls = {
            "alla-program":
                "https://urplay.se/api/v1/search?"
                "response_type=limited&"
                "product_type=series&"
                "rows={}&start={}&view=title",

            "barn":
                "https://urplay.se/api/v1/search?"
                "age=children&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}"
                "&view=title",

            "dokumentarfilmer":
                "https://urplay.se/api/v1/search?"
                "main_genre[]=dokument%C3%A4rfilm&main_genre[]=dokument%C3%A4rserie&"
                # "platform=urplay&"
                "singles_and_series=true&view=title&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}"
                "&view=title",

            "drama":
                "https://urplay.se/api/v1/search?"
                "main_genre[]=drama&main_genre[]=kortfilm&main_genre[]=fiktiva%20ber%C3%A4ttelser&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "forelasningar":
                "https://urplay.se/api/v1/search?"
                "main_genre[]=f%C3%B6rel%C3%A4sning&main_genre[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "halsa-och-relationer----old":
                "https://urplay.se/api/v1/search?"
                "main_genre_must_not[]=forelasning&"
                "main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=kropp%20%26%20sinne&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "halsa-och-relationer":
                "https://urplay.se/api/v1/search?"
                "category=H%C3%A4lsa%20%26%20relationer&"
                # "header=Senaste&"
                "is_audio_described=false&"
                "is_sign_language_interpreted=false&"
                "main_genre[]=Reportage&"
                "main_genre[]=L%C3%A4r-mer-program&"
                "main_genre[]=Fiktiva%20ber%C3%A4ttelser&"
                "main_genre[]=Dokument%C3%A4rserie&"
                "main_genre[]=Nyheter&"
                "main_genre[]=Drama&"
                "main_genre[]=Faktaprogram&"
                "main_genre[]=Dokument%C3%A4rfilm&"
                "main_genre[]=Talkshow&"
                "main_genre[]=Experiment&"
                "main_genre[]=Kortfilm&"
                "main_genre[]=Reality&"
                "main_genre[]=Reseprogram&"
                "main_genre[]=S%C3%A5nger&"
                "main_genre[]=Teaterf%C3%B6rest%C3%A4llning&"
                "main_genre[]=Explainer&"
                "platform=urplay&"
                "product_type=series&"
                # "response_type=limited&"
                "rows={}&"
                # "showFiltersAndSorting=false&"
                # "sort=published&"
                "start={}&"
                "typical_age_range[]=adults&"
                "typical_age_range[]=secondary&"
                "typical_age_range[]=primary7-9",
            
            "kultur-och-historia":
                "https://urplay.se/api/v1/search?"
                "main_genre_must_not[]=forelasning&main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=kultur%20%26%20historia&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "natur-och-resor":
                "https://urplay.se/api/v1/search?"
                "main_genre_must_not[]=forelasning&main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=natur%20%26%20resor&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "radio":
                "https://urplay.se/api/v1/search?"
                "type=programradio&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "samhalle":
                "https://urplay.se/api/v1/search?"
                "main_genre_must_not[]=forelasning&main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=samh%C3%A4lle&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "sprak":
                "https://urplay.se/api/v1/search?"
                "main_genre_must_not[]=forelasning&main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=spr%C3%A5k&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "syntolkat":
                "https://urplay.se/api/v1/search?"
                "response_type=category&"
                "is_audio_described=true&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "teckensprak":
                "https://urplay.se/api/v1/search?"
                "response_type=category&"
                "language=sgn-SWE&"
                "platform=urplay&"
                "rows={}&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "utbildning-och-media":
                "https://urplay.se/api/v1/search?"
                "main_genre_must_not[]=forelasning&"
                "main_genre_must_not[]=panelsamtal&"
                "platform=urplay&"
                "rows={}&"
                "sab_category=utbildning%20%26%20media&"
                "singles_and_series=true&"
                "start={}&"
                "view=title",

            "vetenskap":
                "https://urplay.se/api/v1/search?"
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
        if url.startswith("#category"):
            url = self.parentItem.metaData.get("url_format")

        if "{" not in url:
            return data, items

        data = self.__iterate_results(url, max_iterations=5, use_pb=True)
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

        item = chn_class.Channel.create_folder_item(self, result_set)
        item.url = "#category"
        if item is None:
            return None

        item.metaData["url_format"] = url
        return item

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
        max_items_per_page = 20

        categories = {
            LanguageHelper.Popular: "https://urplay.se/api/v1/search?product_type=program&query=&rows={}&start=0&view=most_viewed".format(max_items_per_page),
            LanguageHelper.MostRecentEpisodes: "https://urplay.se/api/v1/search?product_type=program&rows={}&start=0&view=published".format(max_items_per_page),
            LanguageHelper.LastChance: "https://urplay.se/api/v1/search?product_type=program&rows={}&start=0&view=last_chance".format(max_items_per_page),
            LanguageHelper.Categories: "https://urplay.se/",
            LanguageHelper.Search: "searchSite",
            LanguageHelper.TvShows: "#tvshows"
        }

        for cat in categories:
            title = LanguageHelper.get_localized_string(cat)
            item = FolderItem(title, categories[cat], content_type=contenttype.VIDEOS)
            item.complete = True
            item.dontGroup = True
            items.append(item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def merge_tv_show(self, data):
        """ Adds some generic items such as search and categories to the main listing.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        # merge the main list items:
        # https://urplay.se/api/v1/search?product_type=series&response_type=limited&rows=20&sort=title&start=20
        max_items_per_page = 20
        main_list_pages = int(self._get_setting("mainlist_pages"))
        data = self.__iterate_results(
            "https://urplay.se/api/v1/search?product_type=series&response_type=limited&rows={}&sort=published&start={}",
            results_per_page=max_items_per_page,
            max_iterations=main_list_pages,
            use_pb=True
        )

        return data, []

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

        url = "https://urplay.se/api/v1/search?query=%s"
        return chn_class.Channel.search_site(self, url)

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
        url = "https://urplay.se/api/v1/series?id={}".format(result_set["id"])
        fanart = "https://assets.ur.se/id/%(id)s/images/1_hd.jpg" % result_set
        thumb = "https://assets.ur.se/id/%(id)s/images/1_l.jpg" % result_set
        item = MediaItem(title, url)
        item.thumb = thumb
        item.description = result_set.get("description")
        item.fanart = fanart
        item.dontGroup = True
        return item

    def create_season_item(self, result_set):
        """ Creates a new MediaItem for a season.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        if self.parentItem.metaData.get("season", False):
            return None

        title = "%(label)s" % result_set
        url = "https://urplay.se/api/v1/series?id={}".format(result_set["id"])
        fanart = "https://assets.ur.se/id/%(id)s/images/1_hd.jpg" % result_set
        thumb = "https://assets.ur.se/id/%(id)s/images/1_l.jpg" % result_set
        item = FolderItem(title, url, content_type=contenttype.EPISODES, media_type=mediatype.FOLDER)
        item.thumb = thumb
        item.description = self.parentItem.description
        item.fanart = fanart
        item.metaData["season"] = True
        return item

    def check_seasons(self, data, items):
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

        # check if there are seasons, if so, filter all the videos out
        seasons = [i for i in items if i.metaData.get("season", False)]
        if seasons:
            Logger.debug("Seasons found, skipping any videos.")
            return seasons

        Logger.debug("Post-Processing finished")
        return items

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
        url = "%s/program/%s" % (self.baseUrl, slug)

        item = MediaItem(title, url)
        item.media_type = mediatype.EPISODE
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

        data = UriHandler.open(item.url)
        # Extract stream JSON data from HTML
        # streams = Regexer.do_regex(r'ProgramContainer" data-react-props="({[^"]+})"', data)
        # json_data = streams[0]
        # json_data = HtmlEntityHelper.convert_html_entities(json_data)
        json_data = Regexer.do_regex(r'__NEXT_DATA__" type="application/json">(.*?)</script>', data)[0]
        json = JsonHelper(json_data, logger=Logger.instance())
        Logger.trace(json.json)

        item.streams = []

        # generic server information
        proxy_data = UriHandler.open("https://streaming-loadbalancer.ur.se/loadbalancer.json",
                                     no_cache=True)
        proxy_json = JsonHelper(proxy_data)
        proxy = proxy_json.get_value("redirect")
        Logger.trace("Found RTMP Proxy: %s", proxy)

        stream_infos = json.get_value("props", "pageProps", "program", "streamingInfo")
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
                    item.subtitle = SubtitleHelper.download_subtitle(
                        stream_url, format="ttml")
                    continue

                bitrate = bitrate if default_stream else bitrate + 1
                if stream_type == "raw":
                    bitrate += 1
                url = "https://%s/%smaster.m3u8" % (proxy, stream_url)
                item.add_stream(url, bitrate)

        item.complete = True
        return item

    def create_search_result(self, result_set):
        result_type = result_set["mediaType"].lower()
        if result_type == "series":
            return self.__create_search_result(result_set, "series")
        elif result_type == "episode" or result_type == "single":
            return self.__create_search_result(result_set, "program")

        Logger.error("Missing search result type: %s", result_type)
        return None

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

        if result_type == "series":
            url = "https://urplay.se/api/v1/series?id={}".format(result_set["id"])
            item = FolderItem(result_set["title"], url, contenttype.EPISODES, media_type=mediatype.FOLDER)
        else:
            url = "https://urplay.se/{}/{}".format(result_type, result_set["slug"])
            series_title = result_set.get("seriesTitle")
            if series_title:
                title = "{} - {}".format(series_title, result_set["title"])
            else:
                title = result_set["title"]
            item = MediaItem(title, url, media_type=mediatype.EPISODE)

        item.thumb = "https://assets.ur.se/id/{}/images/1_hd.jpg".format(result_set["id"])
        item.fanart = "https://assets.ur.se/id/{}/images/1_l.jpg".format(result_set["id"])

        if result_type == "program":
            item.set_info_label("duration", result_set["duration"] * 60)
            item.media_type = mediatype.EPISODE
        return item

    def __iterate_results(self, url_format, results_per_page=20, max_iterations=10, use_pb=False):
        """ Retrieves the full dataset for a multi-set search action.

        :param str url_format:             The url format with start and count placeholders
        :param int results_per_page:       The maximum results per request
        :param int max_iterations:         The maximum number of iterations
        :param bool use_pb:                Use a progress bar

        :returns A Json response with all results
        :rtype JsonHelper

        Url format should be like:
            https://urplay.se/api/v1/search?product_type=series&rows={}&start={}

        """

        # TODO: Currently the new (none bff API) ignores the "rows" parameters. Even on the website.
        #  This causes a response with 20 results only. So we need to load more pages.

        results = None
        from resources.lib.xbmcwrapper import XbmcDialogProgressWrapper
        status = LanguageHelper.get_localized_string(LanguageHelper.FetchMultiApi)
        updated = LanguageHelper.get_localized_string(LanguageHelper.PageOfPages)

        progress = None
        if use_pb:
            progress = XbmcDialogProgressWrapper("{} - {}".format(Config.appName, self.channelName), status)

        for p in range(0, max_iterations):
            url = url_format.format(results_per_page, p * results_per_page)
            if (progress and progress.progress_update(
                    p, max_iterations, int(p * 100 / max_iterations), False, updated.format(p + 1, max_iterations))):
                break

            data = UriHandler.open(url, force_cache_duration=24*3600)
            json_data = JsonHelper(data)
            result_items = json_data.get_value("results", fallback=[])
            # result_size = json_data.get_value("nextPageInfo", "rows")
            if results is None:
                results = json_data
            else:
                results.json["results"] += result_items

            if len(result_items) < results_per_page:
                break

        if progress:
            progress.close()
        return results or ""
