# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import datetime

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem, MediaItemPart
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.subtitlehelper import SubtitleHelper
from resources.lib.parserdata import ParserData
from resources.lib.addonsettings import AddonSettings
from resources.lib.streams.m3u8 import M3u8


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        # The following data was taken from http://playapi.mtgx.tv/v3/channels
        self.channelId = None
        if self.channelCode == "se3":
            self.mainListUri = "https://www.viafree.se/program/"
            self.noImage = "tv3seimage.png"
            self.channelId = (
                1209,  # TV4
                6000,  # MTV
                6001,  # Comedy Central
                7000,  # Online Only ???
            )

        elif self.channelCode == "se6":
            self.mainListUri = "https://www.viafree.se/program/"
            self.noImage = "tv6seimage.png"
            self.channelId = (959, )

        elif self.channelCode == "se8":
            self.mainListUri = "https://www.viafree.se/program/"
            self.noImage = "tv8seimage.png"
            self.channelId = (801, )

        elif self.channelCode == "se10":
            self.mainListUri = "https://www.viafree.se/program/"
            self.noImage = "tv10seimage.png"
            self.channelId = (5462, )

        elif self.channelCode == "ngse":
            self.mainListUri = "https://www.viafree.se/program/"
            self.noImage = "ngnoimage.jpg"
            self.channelId = (7300, )

        elif self.channelCode == "mtvse":
            self.mainListUri = "https://www.viafree.se/program"
            self.noImage = "mtvimage.png"
            self.channelId = (6000, )

        elif self.channelCode == "viafreese":
            self.mainListUri = "https://www.viafree.se/program/"
            self.noImage = "viafreeimage.png"
            self.channelId = None

        elif self.channelCode == "sesport":
            raise NotImplementedError('ViaSat sport is not in this channel anymore.')

        # Danish channels
        elif self.channelCode == "tv3dk":
            self.mainListUri = "http://www.viafree.dk/programmer"
            self.noImage = "tv3noimage.png"
            # self.channelId = (3687, 6200, 6201) -> show all for now

        # Norwegian Channels
        elif self.channelCode == "no3":
            self.mainListUri = "https://www.viafree.no/programmer"
            self.noImage = "tv3noimage.png"
            self.channelId = (1550, 6100, 6101)

        elif self.channelCode == "no4":
            self.mainListUri = "https://www.viafree.no/programmer"
            self.noImage = "viasat4noimage.png"
            self.channelId = (935,)

        elif self.channelCode == "no6":
            self.mainListUri = "https://www.viafree.no/programmer"
            self.noImage = "viasat4noimage.png"
            self.channelId = (1337,)

        self.baseUrl = self.mainListUri.rsplit("/", 1)[0]
        self.searchInfo = {
            "se": ["sok", "S&ouml;k"],
            "ee": ["otsing", "Otsi"],
            "dk": ["sog", "S&oslash;g"],
            "no": ["sok", "S&oslash;k"],
            "lt": ["paieska", "Paie&scaron;ka"],
            "lv": ["meklet", "Mekl&#275;t"]
        }

        # setup the urls
        self.swfUrl = "http://flvplayer.viastream.viasat.tv/flvplayer/play/swf/MTGXPlayer-1.8.swf"

        # New JSON page data
        self._add_data_parser(self.mainListUri, preprocessor=self.extract_json_data,
                              match_type=ParserData.MatchExact)
        self._add_data_parser(self.mainListUri, preprocessor=self.extract_categories_and_add_search,
                              json=True, match_type=ParserData.MatchExact,
                              parser=["page", "blocks", 0, "_embedded", "programs"],
                              creator=self.create_json_episode_item)

        # This is the new way, but more complex and some channels have items with missing
        # category slugs and is not compatible with the old method channels.
        self.useNewPages = False
        if self.useNewPages:
            self._add_data_parser("*", preprocessor=self.extract_json_data)
            self._add_data_parser("*", json=True, preprocessor=self.merge_season_data,
                                  # parser=["context", "dispatcher", "stores", "ContentPageProgramStore", "format", "videos", "0", "program"),
                                  # creator=self.create_json_video_item
                                  )

            self._add_data_parser("http://playapi.mtgx.tv/", updater=self.update_video_item)
        else:
            self._add_data_parser("*", parser=['_embedded', 'videos'], json=True, preprocessor=self.add_clips,
                                  creator=self.create_video_item, updater=self.update_video_item)
            self.pageNavigationJson = ["_links", "next"]
            self.pageNavigationJsonIndex = 0
            self._add_data_parser("*", json=True,
                                  parser=self.pageNavigationJson, creator=self.create_page_item)

        self._add_data_parser("https://playapi.mtgx.tv/v3/search?term=", json=True,
                              parser=["_embedded", "formats"], creator=self.create_json_search_item)

        self._add_data_parser("/api/playClient;isColumn=true;query=", json=True,
                              match_type=ParserData.MatchContains,
                              parser=["data", "formats"], creator=self.create_json_episode_item)
        self._add_data_parser("/api/playClient;isColumn=true;query=", json=True,
                              match_type=ParserData.MatchContains,
                              parser=["data", "clips"], creator=self.create_json_video_item)
        self._add_data_parser("/api/playClient;isColumn=true;query=", json=True,
                              match_type=ParserData.MatchContains,
                              parser=["data", "episodes"], creator=self.create_json_video_item)
        # ===============================================================================================================
        # non standard items
        self.episodeLabel = LanguageHelper.get_localized_string(LanguageHelper.EpisodeId)
        self.seasonLabel = LanguageHelper.get_localized_string(LanguageHelper.SeasonId)
        self.__categories = {}

        # ===============================================================================================================
        # Test Cases
        #  No GEO Lock: Extra Extra
        #  GEO Lock:
        #  Multi Bitrate: Glamourama

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def extract_categories_and_add_search(self, data):
        """ Extracts the Category information from the JSON data

        The return values should always be instantiated in at least ("", []).

        :param JsonHelper data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Extracting Category Information")
        dummy_data, items = self.add_search(data)

        # The data was already in a JsonHelper
        categories = data.get_value("page", "blocks", 0, "allPrograms", "categories")
        for category in categories:
            self.__categories[category["guid"]] = category

        Logger.debug("Extracting Category Information finished")
        return data, items

    def extract_json_data(self, data):
        """ Extracts the JSON data from the HTML page and passes it back to Retrospect.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        json_data = Regexer.do_regex(r'("staticpages":\s*{[^<]+),\s*"translations":', data)[0]
        # We need to put it in a JSON envelop as we are taking JSON from the 'middle'
        return_data = "{{{0}}}".format(json_data)
        Logger.trace("Found Json:\n%s", return_data)
        return JsonHelper(return_data), items

    def create_json_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        return self.__create_json_episode_item(result_set, check_channel=True)

    def create_json_search_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        return self.__create_json_episode_item(result_set, check_channel=False)

    def merge_season_data(self, data):
        """ Merge some season data to make it more easy for parsing.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """
        items = []

        json_data = JsonHelper(data)
        season_folders = json_data.get_value("context", "dispatcher", "stores",
                                             "ContentPageProgramStore", "format", "videos")
        for season in season_folders:
            for video in season_folders[season]['program']:
                items.append(self.create_json_video_item(video))

        return data, items

    def create_json_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict[str,any] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        url = "http://playapi.mtgx.tv/v3/videos/stream/%(id)s" % result_set
        item = MediaItem(result_set["title"], url)
        item.type = "video"
        item.description = result_set.get("summary", None)

        aired_at = result_set.get("airedAt", None)
        if aired_at is None:
            aired_at = result_set.get("publishedAt", None)
        if aired_at is not None:
            # 2016-05-20T15:05:00+00:00
            aired_at = aired_at.split("+")[0].rstrip('Z')
            time_stamp = DateHelper.get_date_from_string(aired_at, "%Y-%m-%dT%H:%M:%S")
            item.set_date(*time_stamp[0:6])

        item.thumb = self.__get_thumb_image(result_set.get("image"))

        # webvttPath / samiPath
        # loginRequired
        is_premium = result_set.get("loginRequired", False)
        if is_premium and AddonSettings.hide_premium_items():
            Logger.debug("Found premium item, hiding it.")
            return None

        srt = result_set.get("samiPath")
        if not srt:
            srt = result_set.get("subtitles_webvtt")
        if srt:
            Logger.debug("Storing SRT/WebVTT path: %s", srt)
            part = item.create_new_empty_media_part()
            part.Subtitle = srt
        return item

    def add_clips(self, data):
        """ Add an items that lists clips.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Adding Clips Pre-Processing")
        items = []

        # if the main list was retrieve using json, are the current data is json, just determine
        # the clip URL
        clip_url = None
        if data.lstrip().startswith("{"):
            if self.parentItem.url.endswith("type=program"):
                # http://playapi.mtgx.tv/v3/videos?format=6723&order=-airdate&type=program
                # http://playapi.mtgx.tv/v3/videos?format=6723&order=-updated&type=clip" % (data_id,)
                clip_url = self.parentItem.url.replace("type=program", "type=clip")
        else:
            # now we determine the ID and load the json data
            data_id = Regexer.do_regex(r'data-format-id="(\d+)"', data)[-1]
            Logger.debug("Found FormatId = %s", data_id)
            program_url = \
                "http://playapi.mtgx.tv/v3/videos?format=%s&order=-airdate&type=program" % (data_id,)
            data = UriHandler.open(program_url, proxy=self.proxy)
            clip_url = \
                "http://playapi.mtgx.tv/v3/videos?format=%s&order=-updated&type=clip" % (data_id,)

        if clip_url is not None:
            clip_title = LanguageHelper.get_localized_string(LanguageHelper.Clips)
            clip_item = MediaItem("\a.: %s :." % (clip_title,), clip_url)
            items.append(clip_item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def add_search(self, data):
        """ Adds a search item.

        The return values should always be instantiated in at least ("", []).

        :param JsonHelper data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        title = "\a.: %s :." % (self.searchInfo.get(self.language, self.searchInfo["se"])[1], )
        Logger.trace("Adding search item: %s", title)
        search_item = MediaItem(title, "searchSite")
        search_item.dontGroup = True
        items.append(search_item)

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

        # https://playapi.mtgx.tv/v3/search?term=nyheter&limit=20&columns=formats&with=format&device=web&include_prepublished=1&country=se&page=1

        url = "https://playapi.mtgx.tv/v3/search?term=%s&limit=50&columns=formats&with=format" \
              "&device=web&include_prepublished=1&country={0}&page=1".format(self.language)

        # # we need to do some ugly stuff to get the %s in the URL-Encoded query.
        # query = '{"term":"tttt","limit":2000,"columns":"formats,episodes,clips","with":"format"}'
        # query = HtmlEntityHelper.url_encode(query).replace("%", "%%").replace("tttt", "%s")
        # baseUrl = self.baseUrl.rsplit('/', 1)[0]
        # url = "%s/api/playClient;isColumn=true;query=%s;resource=search?returnMeta=true" % (baseUrl, query)

        Logger.debug("Using search url: %s", url)
        return chn_class.Channel.search_site(self, url)

    def create_page_item(self, result_set):
        """ Creates a MediaItem of type 'page' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'page'.
        :rtype: MediaItem|None

        """

        Logger.debug("Starting create_page_item")
        Logger.trace(result_set)

        url = result_set["href"]
        page = url.rsplit("=", 1)[-1]

        item = MediaItem(page, url)
        item.type = "page"

        Logger.trace("Created '%s' for url %s", item.name, item.url)
        return item

    def create_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict[str,dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        drm_locked = False
        geo_blocked = result_set["is_geo_blocked"]

        title = result_set["title"]
        if ("_links" not in result_set or
                "stream" not in result_set["_links"] or
                "href" not in result_set["_links"]["stream"]):
            Logger.warning("No streams found for %s", title)
            return None

        # the description
        description = result_set["description"].strip()  # The long version
        summary = result_set["summary"].strip()  # The short version
        # Logger.Trace("Comparing:\nDesc: %s\nSumm:%s", description, summary)
        if not description.startswith(summary):
            # the descripts starts with the summary. Don't show
            description = "%s\n\n%s" % (summary, description)

        video_type = result_set["type"]
        if not video_type == "program":
            title = "%s (%s)" % (title, video_type.title())

        elif result_set["format_position"]["is_episodic"]:  # and resultSet["format_position"]["episode"] != "0":
            # make sure we show the episodes and seaso
            season = result_set["format_position"].get("season", 0)
            episode = int(result_set["format_position"]["episode"] or "0")

            # Was it a webisode?
            # webisode = result_set.get("webisode", False)

            # if the name had the episode in it, translate it
            if episode > 0 and season > 0:  # and not webisode:
                description = "%s\n\n%s" % (title, description)
                title = "{0} - s{1:02d}e{2:02d}".format(result_set["format_title"],
                                                        season,
                                                        episode)
            else:
                Logger.debug("Found episode '0' or websido '%s': using name instead of episode number", title)

        mpx_guid = result_set.get('mpx_guid')
        if mpx_guid is None:
            url = result_set["_links"]["stream"]["href"]
        else:
            # we can use mpx_guid and https://viafree.mtg-api.com/stream-links/viafree/web/se/clear-media-guids/{}/streams
            url = "https://viafree.mtg-api.com/stream-links/viafree/web/{}/clear-media-guids/{}/streams".format(self.language, mpx_guid)
        item = MediaItem(title, url)

        date_info = None
        date_format = "%Y-%m-%dT%H:%M:%S"
        if "broadcasts" in result_set and len(result_set["broadcasts"]) > 0:
            date_info = result_set["broadcasts"][0]["air_at"]
            Logger.trace("Date set from 'air_at'")

            if "playable_from" in result_set["broadcasts"][0]:
                start_date = result_set["broadcasts"][0]["playable_from"]
                playable_from = DateHelper.get_date_from_string(start_date[0:-6], date_format)
                playable_from = datetime.datetime(*playable_from[0:6])
                if playable_from > datetime.datetime.now():
                    drm_locked = True

        elif "publish_at" in result_set:
            date_info = result_set["publish_at"]
            Logger.trace("Date set from 'publish_at'")

        if date_info is not None:
            # publish_at=2007-09-02T21:55:00+00:00
            info = date_info.split("T")
            date_info = info[0]
            time_info = info[1]
            date_info = date_info.split("-")
            time_info = time_info.split(":")
            item.set_date(date_info[0], date_info[1], date_info[2], time_info[0], time_info[1], 0)

        item.type = "video"
        item.complete = False
        item.isGeoLocked = geo_blocked
        item.isDrmProtected = drm_locked

        thumb_data = result_set['_links'].get('image', None)
        if thumb_data is not None:
            # Older version
            # item.thumbUrl = thumb_data['href'].replace("{size}", "thumb")
            item.thumb = self.__get_thumb_image(thumb_data['href'])

        item.description = description
        # unpublish_at=2099-12-31T00:00:00+01:00
        expire_date = result_set["unpublish_at"]
        if bool(expire_date):
            self.__set_expire_time(expire_date, item)

        srt = result_set.get("sami_path")
        if not srt:
            srt = result_set.get("subtitles_webvtt")
        if srt:
            Logger.debug("Storing SRT/WebVTT path: %s", srt)
            part = item.create_new_empty_media_part()
            part.Subtitle = srt

        item.set_info_label("duration", int(result_set.get("duration", 0)))
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
        use_kodi_hls = AddonSettings.use_adaptive_stream_add_on(channel=self)

        # User-agent (and possible other headers), should be consistent over all
        # M3u8 requests (See #864)
        headers = {}
        if not use_kodi_hls:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.13) "
                              "Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)",
            }
        if self.localIP:
            headers.update(self.localIP)

        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=headers or None)
        json = JsonHelper(data)

        embedded_data = json.get_value("embedded")
        if embedded_data is not None:
            return self.__update_embedded(item, embedded_data)

        # see if there was an srt already
        if item.MediaItemParts:
            part = item.MediaItemParts[0]
            if part.Subtitle and part.Subtitle.endswith(".vtt"):
                part.Subtitle = SubtitleHelper.download_subtitle(
                    part.Subtitle, format="webvtt", proxy=self.proxy)
            else:
                part.Subtitle = SubtitleHelper.download_subtitle(
                    part.Subtitle, format="dcsubtitle", proxy=self.proxy)
        else:
            part = item.create_new_empty_media_part()

        for quality in ("high", 3500), ("hls", 2700), ("medium", 2100):
            url = json.get_value("streams", quality[0])
            Logger.trace(url)
            if not url:
                continue

            if ".f4m" in url:
                # Kodi does not like the f4m streams
                continue

            if url.startswith("http") and ".m3u8" in url:
                self.__update_m3u8(url, part, headers, use_kodi_hls)

            elif url.startswith("rtmp"):
                self.__update_rtmp(url, part, quality)

            elif "[empty]" in url:
                Logger.debug("Found post-live url with '[empty]' in it. Ignoring this.")
                continue

            else:
                part.append_media_stream(url, quality[1])

        if not use_kodi_hls:
            part.HttpHeaders.update(headers)

        if part.MediaStreams:
            item.complete = True
        Logger.trace("Found mediaurl: %s", item)
        return item

    def __update_m3u8(self, url, part, headers, use_kodi_hls):
        """ Update a video that has M3u8 streams.

        :param str url:                 The URL for the stream.
        :param MediaItemPart part:      The new part that needs updating.
        :param dict[str,str] headers:   The URL headers to use.
        :param bool use_kodi_hls:       Should we use the InputStream Adaptive add-on?

        """
        # first see if there are streams in this file, else check the second location.
        for s, b in M3u8.get_streams_from_m3u8(url, self.proxy, headers=headers):
            if use_kodi_hls:
                strm = part.append_media_stream(url, 0)
                M3u8.set_input_stream_addon_input(strm, headers=headers)
                # Only the main M3u8 is needed
                break
            else:
                part.append_media_stream(s, b)

        if not part.MediaStreams and "manifest.m3u8" in url:
            Logger.warning("No streams found in %s, trying alternative with 'master.m3u8'", url)
            url = url.replace("manifest.m3u8", "master.m3u8")
            for s, b in M3u8.get_streams_from_m3u8(url, self.proxy, headers=headers):
                if use_kodi_hls:
                    strm = part.append_media_stream(url, 0)
                    M3u8.set_input_stream_addon_input(strm, headers=headers)
                    # Only the main M3u8 is needed
                    break
                else:
                    part.append_media_stream(s, b)

        # check for subs
        # https://mtgxse01-vh.akamaihd.net/i/201703/13/DCjOLN_1489416462884_427ff3d3_,48,260,460,900,1800,2800,.mp4.csmil/master.m3u8?__b__=300&hdnts=st=1489687185~exp=3637170832~acl=/*~hmac=d0e12e62c219d96798e5b5ef31b11fa848724516b255897efe9808c8a499308b&cc1=name=Svenska%20f%C3%B6r%20h%C3%B6rselskadade~default=no~forced=no~lang=sv~uri=https%3A%2F%2Fsubstitch.play.mtgx.tv%2Fsubtitle%2Fconvert%2Fxml%3Fsource%3Dhttps%3A%2F%2Fcdn-subtitles-mtgx-tv.akamaized.net%2Fpitcher%2F20xxxxxx%2F2039xxxx%2F203969xx%2F20396967%2F20396967-swt.xml%26output%3Dm3u8
        # https://cdn-subtitles-mtgx-tv.akamaized.net/pitcher/20xxxxxx/2039xxxx/203969xx/20396967/20396967-swt.xml&output=m3u8
        if "uri=" in url and not part.Subtitle:
            Logger.debug("Extracting subs from M3u8")
            sub_url = url.rsplit("uri=")[-1]
            sub_url = HtmlEntityHelper.url_decode(sub_url)
            sub_data = UriHandler.open(sub_url, proxy=self.proxy)
            subs = [line for line in sub_data.split("\n") if line.startswith("http")]
            if subs:
                part.Subtitle = SubtitleHelper.download_subtitle(subs[0], format='webvtt',
                                                                 proxy=self.proxy)
        return

    def __update_rtmp(self, url, part, quality):
        """ Update a video that has a RTMP stream.

        :param str url:                 The URL for the stream.
        :param MediaItemPart part:      The new part that needs updating.
        :param tuple[str,int] quality:  A quality tuple with quality name and bitrate

        """

        # rtmp://mtgfs.fplive.net/mtg/mp4:flash/sweden/tv3/Esport/Esport/swe_skillcompetition.mp4.mp4
        old_url = url
        if not url.endswith(".flv") and not url.endswith(".mp4"):
            url += '.mp4'

        if "/mp4:" in url:
            # in this case we need to specifically set the path
            # url = url.replace('/mp4:', '//') -> don't do this, but specify the path
            server, path = url.split("mp4:", 1)
            url = "%s playpath=mp4:%s" % (server, path)

        if old_url != url:
            Logger.debug("Updated URL from - to:\n%s\n%s", old_url, url)

        url = self.get_verifiable_video_url(url)
        part.append_media_stream(url, quality[1])
        return

    def __create_json_episode_item(self, result_set, check_channel=True):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict[str,any] result_set: The result_set of the self.episodeItemRegex
        :param bool check_channel:       Compare channel ID's and ignore that that do not match.

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        # make sure we use ID as GUID
        if "id" in result_set:
            result_set["guid"] = result_set["id"]

        if check_channel and self.channelId is not None:
            channels = [int(c["guid"]) for c in result_set.get("channels", [])]
            valid_channel_found = any([c for c in channels if c in self.channelId])
            if not valid_channel_found:
                Logger.trace("Found item for wrong channel %s instead of %s", channels, self.channelId)
                return None

        # For now we keep using the API, otherwise we need to do more complex VideoItem parsing
        if self.useNewPages:
            raise NotImplementedError("The 'slug' part is no longer working")
            # So this no longer works
            # category_slug = self.__categories[result_set["category"]]["guid"]
            # url = "%s/%s/%s" % (self.baseUrl, category_slug, result_set['slug'])
        else:
            url = "http://playapi.mtgx.tv/v3/videos?format=%(guid)s&order=-airdate&type=program" % result_set
        item = MediaItem(result_set['title'], url)

        # Find the possible images
        if "images" in result_set and "landscape" in result_set["images"]:
            image_url = result_set["images"]["landscape"]["href"]
            item.thumb = self.__get_thumb_image(image_url)
            item.fanart = self.__get_thumb_image(image_url, True)

        elif "image" in result_set:
            item.thumb = self.__get_thumb_image(result_set["image"])

        elif "_links" in result_set and "image" in result_set["_links"]:
            thumb_data = result_set["_links"]["image"]
            item.thumb = self.__get_thumb_image(thumb_data['href'])
            item.fanart = self.__get_thumb_image(thumb_data['href'], True)

        item.isGeoLocked = result_set.get('onlyAvailableInSweden', False)
        return item

    def __get_thumb_image(self, url, fanart_size=False):
        """ Create a thumb image based on a URL template.

        :param str url:             The URL template to use with {size} as a size placeholder.
        :param bool fanart_size:    Should we fetch fanart-size (1280x720) images or normal thumbs.

        :return: A full URL to a thumb or fanart image.
        :rtype: str

        """

        if not url:
            return url

        if fanart_size:
            return url.replace("{size}", "1280x720")
        return url.replace("{size}", "230x150")

    def __set_expire_time(self, expire_date, item):
        expire_date = expire_date.split("+")[0].replace("T", " ")
        year = expire_date.split("-")[0]
        if len(year) == 4 and int(year) < datetime.datetime.now().year + 50:
            expire_date = DateHelper.get_datetime_from_string(expire_date, date_format="%Y-%m-%d %H:%M:%S")
            item.set_expire_datetime(timestamp=expire_date)

    def __update_embedded(self, item, embedded_data):
        """ Updates a new "embedded" stream based on the json data

        :param MediaItem item:  The item to update
        :param embedded_data:   The json data

        :return: Updated MediaItem
        :rtype: MediaItem

        """

        stream_url = embedded_data["prioritizedStreams"][0]["links"]["stream"]["href"]
        part = item.create_new_empty_media_part()
        stream = part.append_media_stream(stream_url, 0)
        M3u8.set_input_stream_addon_input(stream, self.proxy)
        item.complete = True

        subtitle_urls = embedded_data["subtitles"]
        if subtitle_urls:
            subtitle_url = subtitle_urls[0]["link"]["href"]
            part.Subtitle = SubtitleHelper.download_subtitle(subtitle_url)

        return item
