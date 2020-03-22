# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.parserdata import ParserData
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.datehelper import DateHelper


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
        if self.channelCode == "sporza":
            self.noImage = "sporzaimage.jpg"
            self.mainListUri = "http://sporza.be/cm/sporza/videozone"
            self.baseUrl = "http://sporza.be"
        else:
            raise IndexError("Invalid Channel Code")

        # elif self.channelCode == "ketnet":
        #     self.noImage = "ketnetimage.png"
        #     self.mainListUri = "http://video.ketnet.be/cm/ketnet/ketnet-mediaplayer"
        #     self.baseUrl = "http://video.ketnet.be"
        #
        # elif self.channelCode == "cobra":
        #     self.noImage = "cobraimage.png"
        #     self.mainListUri = "http://www.cobra.be/cm/cobra/cobra-mediaplayer"
        #     self.baseUrl = "http://www.cobra.be"

        # setup the urls
        self.swfUrl = "%s/html/flash/common/player.5.10.swf" % (self.baseUrl,)

        # setup the main parsing data
        episode_regex = r'<li[^>]*>\W*<a href="(/cm/[^"]+/videozone/programmas/[^"]+)" ' \
                        r'title="([^"]+)"\W*>'
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              preprocessor=self.add_live_channel,
                              parser=episode_regex,
                              creator=self.create_episode_item)

        # extract the right section, although it is hard to determine the actual one
        self._add_data_parser("*", preprocessor=self.extract_video_section)

        # the main video of the page
        regex = Regexer.from_expresso(
            r'<img[^>]+src="(?<thumburl>[^"]+)"[^>]*>[\w\W]{0,700}<p>(?<description>[^<]+)</p>'
            r'[\w\W]{0,500}?<a href="(?<url>/cm/[^/]+/videozone/[^?"]+)" >(?<title>[^<]+)</a>')
        self._add_data_parser("*", name="Main video of the page",
                              parser=regex, creator=self.create_video_item)

        # other videos in the side bar
        regex = Regexer.from_expresso(
            r'<a[^>]*href="(?<url>[^"]+)"[^>]*class="videolink"[^>]*>\W*<span[^>]*>(?<title>[^"]+)'
            r'</span>\W*(?:<span[^>]*>(?<desciption>[^"]+)</span>\W*)?<span[^>]*>\W*<img[^>]*'
            r'src="(?<thumburl>[^"]+)"')
        self._add_data_parser("*", name="Other videos in the sidebar",
                              parser=regex, creator=self.create_video_item,
                              updater=self.update_video_item)

        # live streams
        live_regex = r'data-video-title="([^"]+)"\W+data-video-iphone-server="([^"]+)"\W+' \
                     r'[\w\W]{0,1000}data-video-sitestat-pubdate="(\d+)"[\w\W]{0,2000}' \
                     r'data-video-geoblocking="(\w+)"[^>]+>\W*<img[^>]*src="([^"]+)"'
        self._add_data_parser("http://sporza.be/cm/sporza/matchcenter/mc_livestream",
                              creator=self.create_live_channel,
                              parser=live_regex)
        self._add_data_parser("http://live.stream.vrt.be", updater=self.update_live_item)

        self.mediaUrlRegex = r'data-video-((?:src|rtmp|iphone|mobile)[^=]*)="([^"]+)"\W+' \
                             r'(?:data-video-[^"]+path="([^"]+)){0,1}'

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def add_live_channel(self, data):
        """ Adds the live channel.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        # Only get the first bit
        items = []

        item = MediaItem("\a.: Live :.", "http://sporza.be/cm/sporza/matchcenter/mc_livestream")
        item.type = "folder"
        item.dontGroup = True
        item.complete = False
        items.append(item)
        return data, items

    def create_live_channel(self, result_set):
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

        item = MediaItem(result_set[0], result_set[1])
        item.type = "video"
        item.isGeoLocked = result_set[3].lower() == "true"

        date_time = DateHelper.get_date_from_posix(int(result_set[2]) * 1 / 1000)
        item.set_date(date_time.year, date_time.month, date_time.day, date_time.hour, date_time.minute,
                      date_time.second)

        thumb = result_set[4]
        if not thumb.startswith("http"):
            thumb = "%s%s" % (self.baseUrl, thumb)
        item.thumb = thumb

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

        url = "%s%s" % (self.baseUrl, result_set[0])
        name = result_set[1]

        item = MediaItem(name.capitalize(), url)
        item.type = "folder"
        item.complete = True
        return item

    def extract_video_section(self, data):
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
        data = data[0:data.find('<div class="splitter split24">')]
        Logger.debug("Pre-Processing finished")
        return data, items

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

        url = "%s%s" % (self.baseUrl, result_set["url"])
        if self.parentItem.url not in url:
            return None

        name = result_set["title"]
        desc = result_set.get("description", "")
        thumb = result_set["thumburl"]

        if thumb and not thumb.startswith("http://"):
            thumb = "%s%s" % (self.baseUrl, thumb)

        item = MediaItem(name, url)
        item.thumb = thumb
        item.description = desc
        item.type = 'video'
        item.complete = False

        try:
            name_parts = name.rsplit("/", 3)
            if len(name_parts) == 3:
                Logger.debug("Found possible date in name: %s", name_parts)
                year = name_parts[2]
                if len(year) == 2:
                    year = 2000 + int(year)
                month = name_parts[1]
                day = name_parts[0].rsplit(" ", 1)[1]
                Logger.trace("%s - %s - %s", year, month, day)
                item.set_date(year, month, day)
        except:
            Logger.warning("Apparently it was not a date :)")
        return item

    def update_live_item(self, item):
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

        # http://services.vrt.be/videoplayer/r/live.json?_1466364209811=
        channel_data = UriHandler.open("http://services.vrt.be/videoplayer/r/live.json",
                                       proxy=self.proxy)
        channel_data = JsonHelper(channel_data)
        url = None
        for channel_id in channel_data.json:
            if channel_id not in item.url:
                continue
            else:
                url = channel_data.json[channel_id].get("hls")

        if url is None:
            Logger.error("Could not find stream for live channel: %s", item.url)
            return item

        Logger.debug("Found stream url for %s: %s", item, url)
        part = item.create_new_empty_media_part()
        for s, b in M3u8.get_streams_from_m3u8(url, self.proxy):
            item.complete = True
            part.append_media_stream(s, b)
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
        data-video-id="1613274"
        data-video-type="video"
        data-video-src="http://media.vrtnieuws.net/2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-title="Het journaal 1 - 25/04/13"
        data-video-rtmp-server="rtmp://vrt.flash.streampower.be/vrtnieuws"
        data-video-rtmp-path="2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-rtmpt-server="rtmpt://vrt.flash.streampower.be/vrtnieuws"
        data-video-rtmpt-path="2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-iphone-server="http://iphone.streampower.be/vrtnieuws_nogeo/_definst_"
        data-video-iphone-path="2013/04/135132051ONL1304255866693.urlMP4_H.264.m4v"
        data-video-mobile-server="rtsp://mp4.streampower.be/vrt/vrt_mobile/vrtnieuws_nogeo"
        data-video-mobile-path="2013/04/135132051ONL1304255866693.url3GP_MPEG4.3gp"
        data-video-sitestat-program="het_journaal_1_-_250413_id_1-1613274"
        """

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.open(item.url, proxy=self.proxy)
        data = data.replace("\\/", "/")
        urls = Regexer.do_regex(self.mediaUrlRegex, data)
        part = item.create_new_empty_media_part()
        for url in urls:
            Logger.trace(url)
            if url[0] == "src":
                flv = url[1]
                bitrate = 750
            else:
                flv_server = url[1]
                flv_path = url[2]

                if url[0] == "rtmp-server":
                    flv = "%s//%s" % (flv_server, flv_path)
                    bitrate = 750

                elif url[0] == "rtmpt-server":
                    continue
                    # Not working for now
                    #flv = "%s//%s" % (flv_server, flv_path)
                    #flv = self.get_verifiable_video_url(flv)
                    #bitrate = 1500

                elif url[0] == "iphone-server":
                    flv = "%s/%s" % (flv_server, flv_path)
                    if not flv.endswith("playlist.m3u8"):
                        flv = "%s/playlist.m3u8" % (flv,)

                    for s, b in M3u8.get_streams_from_m3u8(flv, self.proxy):
                        item.complete = True
                        part.append_media_stream(s, b)
                    # no need to continue adding the streams
                    continue

                elif url[0] == "mobile-server":
                    flv = "%s/%s" % (flv_server, flv_path)
                    bitrate = 250

                else:
                    flv = "%s/%s" % (flv_server, flv_path)
                    bitrate = 0

            part.append_media_stream(flv, bitrate)

        item.complete = True
        return item
