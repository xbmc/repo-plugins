# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.regexer import Regexer
from resources.lib.helpers.datehelper import DateHelper

from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData


class Channel(chn_class.Channel):

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "twitimage.png"

        # setup the urls
        self.mainListUri = "https://twit.tv/shows"
        self.baseUrl = "https://twit.tv"

        # setup the main parsing data
        self.episodeItemRegex = r'<img[^>]+src="(?<thumburl>[^"]+)"[^>]*></a>\W+<div[^>]+>\W+' \
                                r'<h2[^>]*><a[^>]+href="/(?<url>shows/[^"]+)"[^>]*>(?<title>[^<]+)' \
                                r'</a></h2>\W+<div[^>]*>(?<description>[^<]+)'
        self.episodeItemRegex = Regexer.from_expresso(self.episodeItemRegex)
        self._add_data_parser(self.mainListUri,
                              preprocessor=self.add_live_stream, match_type=ParserData.MatchExact,
                              parser=self.episodeItemRegex, creator=self.create_episode_item)

        self.videoItemRegex = r'<div[^>]+class="episode item"[^>]*>\W+<a[^>]+href="(?<url>[^"]+)" ' \
                              r'title="(?<title>[^"]+)">[\w\W]{0,500}?<img[^>]+src="' \
                              r'(?<thumburl>[^"]+)"[^>]+>[\w\W]{0,500}?<span[^>]+class="date"' \
                              r'[^>]*>(?<month>\w+) (?<day>\d+)\w+ (?<year>\d+)'
        self.videoItemRegex = Regexer.from_expresso(self.videoItemRegex)
        self._add_data_parser("*",
                              parser=self.videoItemRegex, creator=self.create_video_item,
                              updater=self.update_video_item)

        self.mediaUrlRegex = r'<a href="([^"]+_(\d+).mp4)"[^>]+download>'

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def add_live_stream(self, data):
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

        item = MediaItem("\a.: TWiT.TV Live :.", "http://live.twit.tv/")
        item.complete = True

        playback_item = MediaItem("Play Live", "http://live.twit.tv/")
        playback_item.type = "playlist"
        playback_item.isLive = True
        playback_part = playback_item.create_new_empty_media_part()

        # noinspection PyStatementEffect
        """
        BitGravity
        There are two streams available from BitGravity; a 512 kbps low-bandwidth stream
        and a 1 Mbps high-bandwidth stream.

        UStream
        This is the default stream. The UStream stream is a variable stream that maxes at
        2.2 Mbps and adjusts down based on your bandwidth.
        Justin.tv

        The Justin.tv stream is a 2.2 mbps high-bandwidth stream that will adjust to lower
        bandwidth and resolutions.

        Flosoft.biz
        The Flosoft.biz stream is a 5 resolution/bitrate HLS stream, intended for our app developers.
        Please see Flosoft Developer Section. This stream is hosted by TWiT through Flosoft.biz
        """

        # http://wiki.twit.tv/wiki/TWiT_Live#Direct_links_to_TWiT_Live_Video_Streams
        media_urls = {
            # Justin TV
            # "2000": "http://usher.justin.tv/stream/multi_playlist/twit.m3u8",

            # Flosoft (http://wiki.twit.tv/wiki/Developer_Guide#Flosoft.biz)
            "264": "http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_240/playlist.m3u8",
            "512": "http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_360/playlist.m3u8",
            "1024": "http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_480/playlist.m3u8",
            "1475": "http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_540/playlist.m3u8",
            "1778": "http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_720/playlist.m3u8",

            # UStream
            "1524": "http://iphone-streaming.ustream.tv/ustreamVideo/1524/streams/live/playlist.m3u8",

            # BitGravity
            # "512": "http://209.131.99.99/twit/live/low",
            # "1024": "http://209.131.99.99/twit/live/high",
            #"512": "http://64.185.191.180/cdn-live-s1/_definst_/twit/live/low/playlist.m3u8",
            #"1024": "http://64.185.191.180/cdn-live-s1/_definst_/twit/live/high/playlist.m3u8",
        }

        for bitrate in media_urls:
            playback_part.append_media_stream(media_urls[bitrate], bitrate)

        Logger.debug("Streams: %s", playback_part)
        playback_item.complete = True
        item.items.append(playback_item)
        Logger.debug("Appended: %s", playback_item)

        items.append(item)
        return data, items

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        url = "%s/%s" % (self.baseUrl, result_set["url"])
        item = MediaItem(result_set["title"], url)

        item.thumb = result_set["thumburl"]
        if not item.thumb.startswith("http"):
            item.thumb = "%s%s" % (self.baseUrl, item.thumb)
        item.thumb = item.thumb.replace("coverart-small", "coverart")
        item.complete = True
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

        url = result_set["url"]
        if not url.startswith("http"):
            url = "%s%s" % (self.baseUrl, url)
        name = result_set["title"]

        item = MediaItem(name, url)
        item.type = 'video'
        month = result_set["month"]
        month = DateHelper.get_month_from_name(month, "en", False)
        day = result_set["day"]
        year = result_set["year"]
        item.set_date(year, month, day)

        item.complete = False
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
        streams = Regexer.do_regex(self.mediaUrlRegex, data)

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()
        for stream in streams:
            Logger.trace(stream)
            part.append_media_stream(stream[0], stream[1])

        item.complete = True
        return item
