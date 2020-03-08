# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.regexer import Regexer
from resources.lib.parserdata import ParserData
from resources.lib.logger import Logger
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.urihandler import UriHandler


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
        # setup the main parsing data
        self.noImage = "nickjrimage.jpg"
        self.__mgid = "arc:video:nickjr.tv"

        if self.channelCode == 'nickjrnl':
            self.mainListUri = "http://www.nickjr.nl/"
            self.baseUrl = "http://www.nickjr.nl"
            self.__apiKey = "nl_global_Nickjr_web"

        elif self.channelCode == 'nickjrintl':
            self.mainListUri = "http://www.nickjr.tv/"
            self.baseUrl = "http://www.nickjr.tv"
            self.__apiKey = "global_Nickjr_web"

        elif self.channelCode == "nickse":
            self.noImage = "nickelodeonimage.png"
            self.mainListUri = "http://www.nickelodeon.se/"
            self.baseUrl = "http://www.nickelodeon.se"
            self.__apiKey = "sv_SE_Nick_Web"
            self.__mgid = "arc:video:nick.intl"

        else:
            raise NotImplementedError("Unknown channel code")

        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.extract_json,
                              parser=[], creator=self.create_episode_item)

        self._add_data_parser("*", json=True,
                              parser=["stream", ],
                              creator=self.create_video_items,
                              updater=self.update_video_item)

        self._add_data_parser("*", json=True,
                              parser=["pagination", ],
                              creator=self.create_page_item)

        self.mediaUrlRegex = '<param name="src" value="([^"]+)" />'    # used for the update_video_item
        self.swfUrl = "http://origin-player.mtvnn.com/g2/g2player_2.1.7.swf"

        #===============================================================================================================
        # Test cases:
        #  NO: Avator -> Other items
        #  SE: Hotel 13 -> Other items
        #  NL: Sam & Cat -> Other items

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def extract_json(self, data):
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

        json_data = Regexer.do_regex('type="application/json">([^<]+)<', data)
        if not json_data:
            Logger.warning("No JSON data found.")
            return data, items

        json = JsonHelper(json_data[0])
        result = []
        for key, value in json.json.items():
            result.append(value)
            value["title"] = key

        # set new json and return JsonHelper object
        json.json = result
        return json, items

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
        title = result_set["title"].replace("-", " ").title()

        # http://www.nickjr.nl/data/propertyStreamPage.json?&urlKey=dora&apiKey=nl_global_Nickjr_web&page=1
        url = "%s/data/propertyStreamPage.json?&urlKey=%s&apiKey=%s&page=1" % (self.baseUrl, result_set["seriesKey"], self.__apiKey)
        item = MediaItem(title, url)
        item.complete = True
        item.HttpHeaders = self.httpHeaders
        return item

    def create_page_item(self, result_set):
        """ Creates a MediaItem of type 'page' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'page'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        next_page = result_set["next"]
        if not next_page:
            Logger.debug("No more items available")
            return None

        more = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
        url = "%s=%s" % (self.parentItem.url.rsplit("=", 1)[0], next_page)
        item = MediaItem(more, url)
        item.complete = True
        return item

    def create_video_items(self, result_sets):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict[str,Any] result_sets: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        items = []
        for result_set in result_sets.get("items", []):
            if "data" in result_set and result_set["data"]:
                item = self.create_video_item(result_set["data"])
                if item:
                    items.append(item)

        return items

    def create_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict[str,str|dict] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        is_serie_title = result_set["seriesTitle"]
        if not is_serie_title:
            return None

        if result_set["mediaType"] == "game":
            return None
        elif result_set["mediaType"] == "episode":
            title = "%(title)s (Episode)" % result_set
        else:
            title = result_set["title"]

        video_id = result_set["id"]
        url = "http://media.mtvnservices.com/pmt/e1/access/index.html?uri=mgid:%s:%s&configtype=edge" \
              % (self.__mgid, video_id, )

        item = MediaItem(title, url)
        item.description = result_set.get("description", None)
        item.type = "video"
        item.HttpHeaders = self.httpHeaders
        item.complete = False

        if "datePosted" in result_set:
            date = DateHelper.get_date_from_posix(float(result_set["datePosted"]["unixOffset"]) / 1000)
            item.set_date(date.year, date.month, date.day, date.hour, date.minute, date.second)

        if "images" in result_set:
            images = result_set.get("images", {})
            thumbs = images.get("thumbnail", {})
            item.thumb = thumbs.get("r16-9", self.noImage)

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

        meta_data = UriHandler.open(item.url, proxy=self.proxy, referer=self.baseUrl)
        meta = JsonHelper(meta_data)
        stream_parts = meta.get_value("feed", "items")
        for stream_part in stream_parts:
            stream_url = stream_part["group"]["content"]
            stream_url = stream_url.replace("{device}", "html5")
            stream_url = "%s&format=json" % (stream_url, )
            stream_data = UriHandler.open(stream_url, proxy=self.proxy)
            stream = JsonHelper(stream_data)

            # subUrls = stream.get_value("package", "video", "item", 0, "transcript", 0, "typographic")  # NOSONAR
            part = item.create_new_empty_media_part()

            # m3u8Url = stream.get_value("package", "video", "item", 0, "rendition", 0, "src")  # NOSONAR
            # for s, b in M3u8.get_streams_from_m3u8(m3u8Url, self.proxy):
            #     item.complete = True
            #     part.append_media_stream(s, b)

            rtmp_datas = stream.get_value("package", "video", "item", 0, "rendition")
            for rtmp_data in rtmp_datas:
                rtmp_url = rtmp_data["src"]
                bitrate = rtmp_data["bitrate"]
                part.append_media_stream(rtmp_url, bitrate)

        item.complete = True
        Logger.trace("Media url: %s", item)
        return item
