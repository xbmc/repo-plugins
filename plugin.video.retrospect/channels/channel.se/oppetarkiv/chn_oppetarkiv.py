# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import re

from resources.lib import chn_class
from resources.lib.retroconfig import Config

from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.encodinghelper import EncodingHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "oppetarkivimage.png"

        # setup the urls
        self.mainListUri = "https://www.oppetarkiv.se/kategori/titel"
        self.baseUrl = "https://www.oppetarkiv.se"
        self.swfUrl = "%s/public/swf/svtplayer-9017918b040e054d1e3c902fc13ceb5d.swf" % (self.baseUrl,)

        # setup the main parsing data
        self.episodeItemRegex = r'<li[^>]+data-genre="([^"]*)"[^>]+class="svtoa[^>]*>\W*<a[^>]+' \
                                r'href="([^"]+)"[^>]*>([^<]+)</a>\W*</li>'
        self._add_data_parser(self.mainListUri,
                              preprocessor=self.add_search_and_genres,
                              parser=self.episodeItemRegex, creator=self.create_episode_item)

        self.videoItemRegex = r'<img[^>]+src="([^"]+)"[^>]+>\W+</noscript>\W+</figure>\W+<[^>]+>' \
                              r'\W+(?:<h1[^>]+>([^<]*)</h1>\W+){0,1}<h\d[^>]+><a[^>]+title="' \
                              r'([^"]+)[^>]+href="([^"]+video/(\d+)/[^"]*)"[^>]*>[^>]+</a></h\d>' \
                              r'\W+<p class="svt-text-time[^>]+\W+([^>]+)'
        self._add_data_parser("*", parser=self.videoItemRegex, creator=self.create_video_item,
                              updater=self.update_video_item)

        self.pageNavigationRegex = r'<a href="(/[^?]+\?[^"]*sida=)(\d+)(&amp;sort=[^"]+)?'
        self.pageNavigationRegexIndex = 1
        self._add_data_parser("*", parser=self.pageNavigationRegex, creator=self.create_page_item)

        # ====================================== Actual channel setup STOPS here =======================================
        self.__genre = None
        return

    def add_search_and_genres(self, data):
        """ Performs pre-process actions for data processing and adds a search option and genres.

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

        if self.parentItem is not None and "genre" in self.parentItem.metaData:
            self.__genre = self.parentItem.metaData["genre"]
            Logger.debug("Parsing a specific genre: %s", self.__genre)
            return data, items

        search_item = MediaItem("\a.: S&ouml;k :.", "searchSite")
        search_item.complete = True
        search_item.dontGroup = True
        # search_item.set_date(2099, 1, 1, text="")
        # -> No items have dates, so adding this will force a date sort in Retrospect
        items.append(search_item)

        genres_item = MediaItem("\a.: Genrer :.", "")
        genres_item.complete = True
        genres_item.dontGroup = True
        items.append(genres_item)

        # find the actual genres
        genre_regex = '<li[^>]+genre[^>]*><button[^>]+data-value="(?<genre>[^"]+)"[^>]*>' \
                      '(?<title>[^>]+)</button></li>'
        genre_regex = Regexer.from_expresso(genre_regex)
        genres = Regexer.do_regex(genre_regex, data)
        for genre in genres:
            if genre["genre"] == "all":
                continue
            genre_item = MediaItem(genre["title"], self.mainListUri)
            genre_item.complete = True
            genre_item.metaData = {"genre": genre["genre"]}
            genres_item.items.append(genre_item)

        Logger.debug("Pre-Processing finished")
        return data, items

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

        url = "http://www.oppetarkiv.se/sok/?q=%s"
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

        item = chn_class.Channel.create_page_item(self, result_set)
        item.url = "%s&embed=true" % (item.url,)
        return item

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        genres = result_set[0]
        if self.__genre and self.__genre not in genres:
            Logger.debug("Item '%s' filtered due to genre: %s", result_set[2], genres)
            return None

        url = result_set[1]
        if "&" in url:
            url = HtmlEntityHelper.convert_html_entities(url)

        if not url.startswith("http:"):
            url = "%s%s" % (self.baseUrl, url)

        # get the ajax page for less bandwidth
        url = "%s?sida=1&amp;sort=tid_stigande&embed=true" % (url, )

        item = MediaItem(result_set[2], url)
        item.complete = True
        item.isGeoLocked = True
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

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        thumb_url = result_set[0]
        if thumb_url.startswith("//"):
            thumb_url = "http:%s" % (thumb_url, )
        elif not thumb_url.startswith("http"):
            thumb_url = "%s%s" % (self.baseUrl, thumb_url)
        Logger.trace(thumb_url)

        season = result_set[1]
        if season:
            name = "%s - %s" % (season, result_set[2])
        else:
            name = result_set[2]

        video_id = result_set[4]
        url = "http://www.oppetarkiv.se/video/%s?output=json" % (video_id,)
        item = MediaItem(name, url)
        item.type = 'video'
        item.thumb = thumb_url

        date = result_set[5]
        date_key = 'datetime="'
        if date_key in date:
            date = date[date.index(date_key) + len(date_key):date.index("T")]
            date = date.split("-")
            year = date[0]
            month = date[1]
            day = date[2]
            Logger.trace("%s - %s-%s-%s", date, year, month, day)
            item.set_date(year, month, day)
        else:
            Logger.debug("No date found")

        item.complete = False
        item.isGeoLocked = True
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

        data = UriHandler.open(item.url, proxy=self.proxy)
        json = JsonHelper(data, Logger.instance())
        video_data = json.get_value("video")
        if video_data:
            part = item.create_new_empty_media_part()
            if self.localIP:
                part.HttpHeaders.update(self.localIP)

            # get the videos
            video_urls = video_data.get("videoReferences")
            for video_url in video_urls:
                # Logger.Trace(videoUrl)
                stream_info = video_url['url']
                if "manifest.f4m" in stream_info:
                    continue
                elif "master.m3u8" in stream_info:
                    for s, b in M3u8.get_streams_from_m3u8(stream_info, self.proxy, headers=part.HttpHeaders):
                        item.complete = True
                        part.append_media_stream(s, b)

            # subtitles
            subtitles = video_data.get("subtitleReferences")
            if subtitles and subtitles[0]["url"]:
                Logger.trace(subtitles)
                sub_url = subtitles[0]["url"]
                file_name = "%s.srt" % (EncodingHelper.encode_md5(sub_url),)
                sub_data = UriHandler.open(sub_url, proxy=self.proxy)

                # correct the subs
                regex = re.compile(r"^1(\d:)", re.MULTILINE)
                sub_data = re.sub(regex, r"0\g<1>", sub_data)
                sub_data = re.sub(r"--> 1(\d):", r"--> 0\g<1>:", sub_data)

                local_complete_path = os.path.join(Config.cacheDir, file_name)
                Logger.debug("Saving subtitle to: %s", local_complete_path)
                with open(local_complete_path, 'w') as f:
                    f.write(sub_data)

                part.Subtitle = local_complete_path

            item.complete = True

        return item
