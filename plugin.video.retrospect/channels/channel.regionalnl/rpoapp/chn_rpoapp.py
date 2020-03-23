# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class
from resources.lib.mediaitem import MediaItem
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.parserdata import ParserData
from resources.lib.logger import Logger
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.regexer import Regexer
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    THIS CHANNEL IS BASED ON THE PEPERZAKEN APPS FOR ANDROID
    """

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        self.liveUrl = None        # : the live url if present
        self.jsonParsing = False

        if self.channelCode == "omroepzeeland":
            self.noImage = "omroepzeelandimage.png"
            self.mainListUri = "https://www.omroepzeeland.nl/tvgemist"
            self.baseUrl = "https://www.omroepzeeland.nl"
            self.liveUrl = "https://zeeland.rpoapp.nl/v01/livestreams/AndroidTablet.json"

        elif self.channelCode == "rtvutrecht":
            self.noImage = "rtvutrechtimage.png"
            self.mainListUri = "https://www.rtvutrecht.nl/gemist/rtvutrecht/"
            self.baseUrl = "https://www.rtvutrecht.nl"
            # Uses NPO stream with smshield cookie
            self.liveUrl = "https://utrecht.rpoapp.nl/v02/livestreams/AndroidTablet.json"

        else:
            raise NotImplementedError("Channelcode '%s' not implemented" % (self.channelCode, ))

        # JSON Based Main lists
        self._add_data_parser("https://www.omroepzeeland.nl/tvgemist",
                              preprocessor=self.add_live_channel_and_extract_data,
                              match_type=ParserData.MatchExact,
                              parser=[], creator=self.create_json_episode_item,
                              json=True)

        # HTML Based Main lists
        html_episode_regex = r'<option\s+value="(?<url>/gemist/uitzending/[^"]+)">(?<title>[^<]*)'
        html_episode_regex = Regexer.from_expresso(html_episode_regex)
        self._add_data_parser("https://www.rtvutrecht.nl/gemist/rtvutrecht/",
                              preprocessor=self.add_live_channel_and_extract_data,
                              match_type=ParserData.MatchExact,
                              parser=html_episode_regex, creator=self.create_episode_item,
                              json=False)

        video_item_regex = r'<img src="(?<thumburl>[^"]+)"[^>]+alt="(?<title>[^"]+)"[^>]*/>\W*' \
                           r'</a>\W*<figcaption(?:[^>]+>\W*){2}<time[^>]+datetime="' \
                           r'(?<date>[^"]+)[^>]*>(?:[^>]+>\W*){3}<a[^>]+href="(?<url>[^"]+)"' \
                           r'[^>]*>\W*(?:[^>]+>\W*){3}<a[^>]+>(?<description>.+?)</a>'
        video_item_regex = Regexer.from_expresso(video_item_regex)
        self._add_data_parser("https://www.rtvutrecht.nl/",
                              name="HTML Video parsers and updater for JWPlayer embedded JSON",
                              parser=video_item_regex, creator=self.create_video_item,
                              updater=self.update_video_item_json_player)

        # Json based stuff
        self._add_data_parser("https://www.omroepzeeland.nl/RadioTv/Results?",
                              name="Video item parser", json=True,
                              parser=["searchResults", ], creator=self.create_json_video_item)

        self._add_data_parser("https://www.omroepzeeland.nl/",
                              name="Updater for Javascript file based stream data",
                              updater=self.update_video_item_javascript)

        # Live Stuff
        self._add_data_parser(self.liveUrl, name="Live Stream Creator",
                              creator=self.create_live_item, parser=[], json=True)

        self._add_data_parser(".+/live/.+", match_type=ParserData.MatchRegex,
                              updater=self.update_live_item)
        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:
        #   Omroep Zeeland: M3u8 playist

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def add_live_channel_and_extract_data(self, data):
        """ Add the live channel and extract the correct data to process further.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """
        Logger.info("Performing Pre-Processing")
        items = []

        title = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
        item = MediaItem("\a.: {} :.".format(title), self.liveUrl)
        item.type = "folder"
        items.append(item)

        if not data:
            return "[]", items

        json_data = Regexer.do_regex(r"setupBroadcastArchive\('Tv',\s*([^;]+)\);", data)
        if isinstance(json_data, (tuple, list)) and len(json_data) > 0:
            Logger.debug("Pre-Processing finished")
            return json_data[0], items

        Logger.info("Cannot extract JSON data from HTML.")
        return data, items

    def create_live_item(self, result_set):
        """ Creates a live MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict[str,str|dict[str,str]] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        url = result_set["stream"]["highQualityUrl"]
        title = result_set["title"] or result_set["id"].title()
        item = MediaItem(title, url)
        item.type = "video"
        item.isLive = True

        if item.url.endswith(".mp3"):
            item.append_single_stream(item.url)
            item.complete = True
            return item

        return item

    def create_json_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        url = "{}/RadioTv/Results?medium=Tv&query=&category={}&from=&to=&page=1"\
            .format(self.baseUrl, result_set["seriesId"])
        title = result_set["title"]
        item = MediaItem(title, url)
        item.type = "folder"
        item.complete = False
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

        item = chn_class.Channel.create_video_item(self, result_set)
        if item is None:
            return None

        # 2018-02-24 07:15:00
        time_stamp = DateHelper.get_date_from_string(result_set['date'], date_format="%Y-%m-%d %H:%M:%S")
        item.set_date(*time_stamp[0:6])
        return item

    def create_json_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict[str,str|None] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        url = result_set["url"]
        if not url.startswith("http"):
            url = "{}{}".format(self.baseUrl, url)

        title = result_set["title"]
        item = MediaItem(title, url)
        item.description = result_set.get("synopsis", None)
        item.thumb = result_set.get("photo", self.noImage)
        item.type = "video"

        if "publicationTimeString" in result_set:
            try:
                # publicationTimeString=7 jun 2018 17:20 uur
                date_parts = result_set["publicationTimeString"].split(" ")
                day = int(date_parts[0])
                month = DateHelper.get_month_from_name(date_parts[1], language="nl", short=True)
                year = int(date_parts[2])
                hours, minutes = date_parts[3].split(":")
                hours = int(hours)
                minutes = int(minutes)
                item.set_date(year, month, day, hours, minutes, 0)
            except:
                Logger.warning("Error parsing date %s", result_set["publicationTimeString"], exc_info=True)

        item.complete = False
        return item

    def update_live_item(self, item):
        """ Updates an existing live MediaItem with more data.

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

        part = item.create_new_empty_media_part()
        if AddonSettings.use_adaptive_stream_add_on():
            stream = part.append_media_stream(item.url, 0)
            M3u8.set_input_stream_addon_input(stream, self.proxy)
            item.complete = True
        else:
            for s, b in M3u8.get_streams_from_m3u8(item.url, self.proxy):
                item.complete = True
                part.append_media_stream(s, b)
        return item

    def update_video_item_json_player(self, item):
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

        data = UriHandler.open(item.url, proxy=self.proxy)
        streams = Regexer.do_regex(r'label:\s*"([^"]+)",\W*file:\s*"([^"]+)"', data)

        part = item.create_new_empty_media_part()
        bitrates = {"720p SD": 1200}
        for stream in streams:
            part.append_media_stream(stream[1], bitrates.get(stream[0], 0))
            item.complete = True

        return item

    def update_video_item_javascript(self, item):
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

        url_parts = item.url.rsplit("/", 3)
        if url_parts[-3] == "aflevering":
            video_id = url_parts[-2]
        else:
            video_id = url_parts[-1]
        Logger.debug("Found videoId '%s' for '%s'", video_id, item.url)

        url = "https://omroepzeeland.bbvms.com/p/regiogrid/q/sourceid_string:{}*.js".format(video_id)
        data = UriHandler.open(url, proxy=self.proxy)

        json_data = Regexer.do_regex(r'var opts\s*=\s*({.+});\W*//window', data)
        Logger.debug("Found jsondata with size: %s", len(json_data[0]))
        json_data = JsonHelper(json_data[0])
        clip_data = json_data.get_value("clipData", "assets")
        server = json_data.get_value("publicationData", "defaultMediaAssetPath")
        part = item.create_new_empty_media_part()
        for clip in clip_data:
            part.append_media_stream("{}{}".format(server, clip["src"]), int(clip["bandwidth"]))
            item.complete = True

        return item
