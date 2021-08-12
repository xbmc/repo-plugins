# SPDX-License-Identifier: GPL-3.0-or-later

import datetime

from resources.lib import chn_class, mediatype
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper

from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData
from resources.lib.streams.m3u8 import M3u8


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info):
        """Initialisation of the class.

        Arguments:
        channel_info: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = ""

        # setup the urls
        if self.channelCode == '538':
            self.noImage = "radio538image.png"
            self.mainListUri = "https://content.talparad.io/spaces/3p0bn61n86ty/environments/master/entries?content_type=overview&fields.slug=programmas&include=4"
            self.baseUrl = "http://www.538.nl"
            self.swfUrl = "http://www.538.nl/jwplayer/player.swf"
            self.__authenticationHeaders = {
                "Authorization": "Bearer e5aefe8ddfa10084ddde98b1736a7c8141802257ba66853b96e8b241803eb12c"
            }

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, preprocessor=self.extract_assets)
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.add_live_streams)
        # self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
        #                       preprocessor=self.add_days)

        self._add_data_parser("https://graph.talparad.io/?query=", json=True,
                              preprocessor=self.add_missing_live_streams,
                              parser=["data", "getStations", 0, "items"], creator=self.create_api_typed_item)

        # updater for live streams
        self._add_data_parsers(["https://talparadiohls-i.akamaihd.net/hls/live/",
                                "http://538hls.lswcdn.triple-it.nl/content/slamwebcam/",
                                "https://hls.slam.nl/streaming/hls/"],
                               updater=self.update_live_stream_m3u8)

        self._add_data_parser("https://playerservices.streamtheworld.com/api/livestream-redirect",
                              updater=self.update_live_stream_redirect)
        # self._add_data_parser("https://playerservices.streamtheworld.com/api/livestream",
        #                       updater=self.update_live_stream_xml)

        #===========================================================================================
        # non standard items

        #===========================================================================================
        # Test cases:

        #============================= Actual channel setup STOPS here =============================
        return

    def add_days(self, data):
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

        now = datetime.datetime.now()
        from_date = now - datetime.timedelta(6)
        Logger.debug("Showing dates starting from %02d%02d%02d to %02d%02d%02d",
                     from_date.year, from_date.month, from_date.day, now.year, now.month, now.day)

        current = from_date
        while current <= now:
            url = "https://api.538.nl/api/v1/schedule/station/radio-538" \
                  "?since=%s-%s-%sT00%%3A00%%3A00%%2B01%%3A00" \
                  "&until=%s-%s-%sT23%%3A59%%3A59%%2B01%%3A00" % \
                  (current.year, current.month, current.day,
                   current.year, current.month, current.day)

            # "&_=1483280915489%%02d%%02d%%02d"
            title = "Afleveringen van %02d-%02d-%02d" % (current.year, current.month, current.day)
            date_item = MediaItem(title, url)
            date_item.complete = True
            items.append(date_item)
            current = current + datetime.timedelta(1)

        return data, items

    def add_live_streams(self, data):
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

        live_stream_data = """{
  getStations(profile: "radio-brand-web", slug: "stations-radio-538") {
    title
    slug
    images {
      imageType
      title
      uri
      __typename
    }
    items {
      title
      shortTitle
      slug
      media {
        uri
        source
        __typename
      }
      images {
        title
        uri
        imageType
        __typename
      }
      __typename
    }
    __typename
  }
}"""

        live_stream_url = "https://graph.talparad.io/?query={}&variables={}".format(
            HtmlEntityHelper.url_encode(live_stream_data),
            HtmlEntityHelper.url_encode("{}")
        )

        # add live stuff
        live = MediaItem("\bLive streams", live_stream_url)
        live.complete = True
        live.HttpHeaders["x-api-key"] = "da2-abza7qpnqbfe5ihpk4jhcslpgy"
        items = [live]
        return data, items

    def extract_assets(self, data):
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
        return data, items

    # noinspection PyUnusedLocal
    def create_api_typed_item(self, result_set):
        """ Creates a new MediaItem based on the __typename attribute.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        api_type = result_set["__typename"].lower()
        custom_type = result_set.get("type")
        Logger.trace("%s: %s", api_type, result_set)

        item = None
        if custom_type is not None:
            # Use the 538 custom type
            pass

        if api_type == "station":
            item = self.create_api_station(result_set)
        else:
            Logger.warning("Missing type: %s", api_type)
            return None

        return item

    def add_missing_live_streams(self, data):
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

        slam = MediaItem("Slam! TV", "https://hls.slam.nl/streaming/hls/SLAM!/playlist.m3u8")
        slam.media_type = mediatype.EPISODE
        slam.isLive = True
        items.append(slam)

        slam_fm = MediaItem("Slam! FM", "https://18973.live.streamtheworld.com/SLAM_AAC.aac"
                                        "?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9"
                                        "&pname=TDSdk&pversion=2.9&banners=none")
        slam_fm.media_type = mediatype.AUDIO
        slam_fm.isLive = True
        slam_fm.add_stream(slam_fm.url)
        slam_fm.complete = True
        items.append(slam_fm)
        return data, items

    def create_api_station(self, result_set):
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
        items = []

        title = result_set['title']
        stream_types = result_set["media"]
        for stream in stream_types:
            url = stream["uri"]
            if not url.startswith("http"):
                continue

            source = stream["source"]

            if "video" in source:
                item = MediaItem(
                    "{} Video".format(title), url, media_type=mediatype.VIDEO)
                item.isLive = True
                items.append(item)

            else:
                item = MediaItem(
                    title, url, media_type=mediatype.AUDIO)
                items.append(item)

            Logger.debug("Found stream for %s: %s (%s)", title, url, source)

        return items

    # No longer used
    # def create_show_item(self, result_set):
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
    #     :param dict[str,Any] result_set: The result_set of the self.episodeItemRegex
    #
    #     :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
    #     :rtype: MediaItem|None
    #
    #     """
    #
    #     Logger.trace(result_set)
    #
    #     start_date = result_set['start']  # 2017-01-01T00:00:00+01:00
    #     start_time_stamp = DateHelper.get_date_from_string(start_date.split("+")[0], "%Y-%m-%dT%H:%M:%S")
    #     end_date = result_set['end']
    #     end_time_stamp = DateHelper.get_date_from_string(end_date.split("+")[0], "%Y-%m-%dT%H:%M:%S")
    #     title = "%02d:%02d - %02d:%02d: %s" % (start_time_stamp.tm_hour, start_time_stamp.tm_min,
    #                                            end_time_stamp.tm_hour, end_time_stamp.tm_min,
    #                                            result_set['title'])
    #     item = MediaItem(title, "", media_type=mediatype.EPISODE)
    #     item.description = result_set.get("description")
    #
    #     if "image" in result_set:
    #         if not item.description:
    #             item.description = result_set["image"].get("alt", None)
    #         item.thumb = "https://static.538.nl/%s" % (result_set["image"]['src'],)
    #
    #     item.set_date(*start_time_stamp[0:6])
    #     item.description = result_set.get('description')
    #     if "playbackUrls" in result_set and result_set["playbackUrls"]:
    #         title_format = "%%02d:%%02d - %s" % (result_set['title'],)
    #         item.complete = True
    #         hour = start_time_stamp.tm_hour
    #         for stream in result_set["playbackUrls"]:
    #             if stream.startswith("//"):
    #                 stream = "https:%s" % (stream, )
    #             part = item.create_new_empty_media_part()
    #             part.Name = title_format % (hour, start_time_stamp.tm_min)
    #             part.append_media_stream(stream, 0)
    #             hour += 1
    #     elif "showUrl" in result_set and result_set["showUrl"]:
    #         title_format = "%%02d:%%02d - %s" % (result_set['title'],)
    #         stream = result_set["showUrl"]
    #         item.complete = True
    #         hour = start_time_stamp.tm_hour
    #         if stream.startswith("//"):
    #             stream = "https:%s" % (stream,)
    #         part = item.create_new_empty_media_part()
    #         part.Name = title_format % (hour, start_time_stamp.tm_min)
    #         part.append_media_stream(stream, 0)
    #         hour += 1
    #     else:
    #         Logger.warning("Found item without streams: %s", item)
    #         return None
    #     return item
    #
    # def update_live_stream_xml(self, item):
    #     """ Updates an existing MediaItem with more data.
    #
    #     Used to update none complete MediaItems (self.complete = False). This
    #     could include opening the item's URL to fetch more data and then process that
    #     data or retrieve it's real media-URL.
    #
    #     The method should at least:
    #     * cache the thumbnail to disk (use self.noImage if no thumb is available).
    #     * set at least one MediaStream.
    #     * set self.complete = True.
    #
    #     if the returned item does not have a MediaSteam then the self.complete flag
    #     will automatically be set back to False.
    #
    #     :param MediaItem item: the original MediaItem that needs updating.
    #
    #     :return: The original item with more data added to it's properties.
    #     :rtype: MediaItem
    #
    #     """
    #
    #     data = UriHandler.open(item.url)
    #     xml = parseString(data)
    #     stream_xmls = xml.getElementsByTagName("mountpoint")
    #     Logger.debug("Found %d streams", len(stream_xmls))
    #     part = item.create_new_empty_media_part()
    #     for stream_xml in stream_xmls:
    #         server_xml = stream_xml.getElementsByTagName("server")[0]
    #         server = server_xml.getElementsByTagName("ip")[0].firstChild.nodeValue
    #         port_node = server_xml.getElementsByTagName("port")[0]
    #         port = port_node.firstChild.nodeValue
    #         protocol = port_node.attributes["type"].firstChild.nodeValue
    #         entry = stream_xml.getElementsByTagName("mount")[0].firstChild.nodeValue
    #         if entry.endswith("AAC2"):
    #             continue
    #         bitrate = int(stream_xml.getElementsByTagName("bitrate")[0].firstChild.nodeValue)
    #
    #         transports = stream_xml.getElementsByTagName("transport")
    #         for transport in transports:
    #             transport_type = transport.firstChild.nodeValue
    #             if transport_type == "http":
    #                 url = "{0}://{1}:{2}/{3}".format(protocol, server, port, entry)
    #             elif transport_type == "hls":
    #                 suffix = transport.attributes["mountSuffix"].firstChild.nodeValue
    #                 url = "{0}://{1}:{2}/{3}{4}".format(protocol, server, port, entry, suffix)
    #             else:
    #                 Logger.debug("Ignoring transport type: %s", transport_type)
    #                 continue
    #
    #             part.append_media_stream(url, bitrate)
    #             item.complete = True
    #     return item

    def update_live_stream_m3u8(self, item):
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

        for s, b in M3u8.get_streams_from_m3u8(item.url):
            item.complete = True
            item.add_stream(s, b)

        item.complete = True
        return item

    def update_live_stream_redirect(self, item):
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

        _, url = UriHandler.header(item.url)
        item.add_stream(url.replace(".mp3", ""))
        item.complete = True
        return item
