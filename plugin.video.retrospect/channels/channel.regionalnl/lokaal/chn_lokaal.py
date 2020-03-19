# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.backtothefuture import PY2
if PY2:
    # noinspection PyUnresolvedReferences
    import urlparse as parse
else:
    # noinspection PyUnresolvedReferences
    import urllib.parse as parse

from resources.lib import chn_class
from resources.lib.mediaitem import MediaItem
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.parserdata import ParserData
from resources.lib.logger import Logger
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.htmlhelper import HtmlHelper
from resources.lib.urihandler import UriHandler
from resources.lib.streams.m3u8 import M3u8


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

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============

        # configure login stuff
        # setup the urls
        self.channelBitrate = 850  # : the default bitrate
        self.liveUrl = None        # : the live url if present

        if self.channelCode == "rtvrijnmond":
            self.noImage = "rtvrijnmondimage.png"
            self.mainListUri = "http://rijnmond.api.regiogrid.nl/apps/v520/programs.json"
            self.baseUrl = "http://rijnmond.api.regiogrid.nl"
            self.liveUrl = "https://d3r4bk4fg0k2xi.cloudfront.net/rijnmondTv/index.m3u8"
            self.channelBitrate = 900

        elif self.channelCode == "rtvdrenthe":
            self.noImage = "rtvdrentheimage.png"
            self.mainListUri = "http://drenthe.api.regiogrid.nl/apps/v520/programs.json"
            self.baseUrl = "http://drenthe.api.regiogrid.nl"
            # TODO: move to chn_rpoapp?
            # Taken from: https://drenthe.rpoapp.nl/v01/livestreams/AndroidPhone.json
            self.liveUrl = "https://cdn.rtvdrenthe.nl/live/rtvdrenthe/tv/index.m3u8"
            self.channelBitrate = 1350

        elif self.channelCode == "rtvnoord":
            self.noImage = "rtvnoordimage.png"
            self.mainListUri = "http://noord.api.regiogrid.nl/apps/v520/programs.json"
            self.baseUrl = "http://noord.api.regiogrid.nl"
            # Uses NPO stream with smshield cookie
            # self.liveUrl = "http://noord.api.regiogrid.nl/apps/v520/tv-live-kiezer.json"
            self.liveUrl = "https://media.rtvnoord.nl/live/rtvnoord/tv/index.m3u8"
            self.channelBitrate = 1350

        elif self.channelCode == "rtvoost":
            self.noImage = "rtvoostimage.png"
            self.mainListUri = "http://mobileapp.rtvoost.nl/v520/feeds/programmas.aspx"
            self.baseUrl = "http://mobileapp.rtvoost.nl"
            self.liveUrl = "http://mobileapp.rtvoost.nl/v520/feeds/tv.aspx"
            # the v500 has http://145.58.83.153:80/tv/live.stream/playlist.m3u8
            # the v520 has rtsp://145.58.83.153:554/tv/live.stream and NPO streams
            self.channelBitrate = 1350

        elif self.channelCode == "rtvnh":
            self.noImage = "rtvnhimage.png"
            self.baseUrl = "http://www.rtvnh.nl"
            self.liveUrl = "https://rrr.sz.xlcdn.com/?account=nhnieuws&file=live&type=live&service=wowza&protocol=https&output=playlist.m3u8"
            self.channelBitrate = 1200

        elif self.channelCode == "omroepwest":
            self.noImage = "omroepwestimage.png"
            self.mainListUri = "http://west.api.regiogrid.nl/apps/v520/programs.json"
            self.baseUrl = "http://www.omroepwest.nl"
            self.liveUrl = "http://feeds.omroepwest.nl/v520/tv.json"
            self.channelBitrate = 1500

        elif self.channelCode == "omroepgelderland":
            # TODO: move to chn_rpoapp?
            self.noImage = "omroepgelderlandimage.png"
            self.mainListUri = "https://web.omroepgelderland.nl/json/v400/programmas.json"
            self.baseUrl = "https://web.omroepgelderland.nl"
            self.liveUrl = "https://gelderland.rpoapp.nl/v02/livestreams/AndroidTablet.json"
            self.channelBitrate = 1500

        elif self.channelCode == "omroepbrabant":
            self.noImage = "omroepbrabantimage.png"
            self.mainListUri = "http://feed.omroepbrabant.nl/v520/UGSeries.json"
            self.baseUrl = "http://www.omroepbrabant.nl"
            self.liveUrl = "http://feed.omroepbrabant.nl/s520/tv.json"
            self.channelBitrate = 1500

        elif self.channelCode == "omropfryslan":
            self.noImage = "omropfryslanimage.png"
            self.mainListUri = "http://www.omropfryslan.nl/feeds/v520/uitzendinggemist.php"
            self.baseUrl = "http://www.omropfryslan.nl"
            self.liveUrl = "http://www.omropfryslan.nl/feeds/v520/tv.php"
            self.channelBitrate = 1500

        else:
            raise NotImplementedError("Channelcode '%s' not implemented" % (self.channelCode, ))

        # setup the main parsing data
        self.episodeItemJson = []
        self.videoItemJson = ["items", ]

        self._add_data_parser(self.mainListUri, preprocessor=self.add_live_items, match_type=ParserData.MatchExact,
                              parser=self.episodeItemJson, creator=self.create_episode_item,
                              json=True)

        if self.liveUrl and "rpoapp" not in self.liveUrl:
            self._add_data_parser(self.liveUrl, preprocessor=self.process_live_items, updater=self.update_video_item)

        elif self.liveUrl:
            self._add_data_parser(self.liveUrl, name="Live Stream Creator",
                                  creator=self.create_live_item, json=True, parser=[])

        self._add_data_parser("*", parser=self.videoItemJson, creator=self.create_video_item, updater=self.update_video_item,
                              json=True)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:
        #   Omroep Zeeland: M3u8 playist
        #   Omroep Brabant: Same M3u8 for al streams
        #   RTV Utrecht: Multiple live channels Type #1
        #   Omrop Fryslan: Multiple live channels Type #2

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def add_live_items(self, data):
        """ Performs pre-process actions for data processing and adds the live channels if present.

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
        if self.liveUrl:
            Logger.debug("Adding live item")
            live_item = MediaItem("\aLive TV", self.liveUrl)
            live_item.dontGroup = True
            items.append(live_item)

        return data, items

    def process_live_items(self, data):  # NOSONAR
        """ Performs pre-process actions that either return multiple live channels that are present
        in the live url or an actual list item if a single live stream is present.

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

        Logger.info("Adding Live Streams")

        if self.liveUrl.endswith(".m3u8"):
            # We actually have a single stream.
            title = "{} - {}".format(self.channelName, LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId))
            live_item = MediaItem(title, self.liveUrl)
            live_item.type = 'video'
            live_item.isLive = True
            if self.channelCode == "rtvdrenthe":
                # RTV Drenthe actually has a buggy M3u8 without master index.
                live_item.append_single_stream(live_item.url, 0)
                live_item.complete = True

            items.append(live_item)
            return "", items

        # we basically will check for live channels
        json_data = JsonHelper(data, logger=Logger.instance())
        live_streams = json_data.get_value()

        Logger.trace(live_streams)
        if "videos" in live_streams:
            Logger.debug("Multiple streams found")
            live_streams = live_streams["videos"]
        elif not isinstance(live_streams, (list, tuple)):
            Logger.debug("Single streams found")
            live_streams = (live_streams, )
        else:
            Logger.debug("List of stream found")

        live_stream_value = None
        for streams in live_streams:
            Logger.debug("Adding live stream")
            title = streams.get('name') or "%s - Live TV" % (self.channelName, )

            live_item = MediaItem(title, self.liveUrl)
            live_item.type = 'video'
            live_item.complete = True
            live_item.isLive = True
            part = live_item.create_new_empty_media_part()
            for stream in streams:
                Logger.trace(stream)
                bitrate = None

                # used in Omrop Fryslan
                if stream == "android" or stream == "iPhone":
                    bitrate = 250
                    url = streams[stream]["videoLink"]
                elif stream == "iPad":
                    bitrate = 1000
                    url = streams[stream]["videoLink"]

                # used in RTV Utrecht
                elif stream == "androidLink" or stream == "iphoneLink":
                    bitrate = 250
                    url = streams[stream]
                elif stream == "ipadLink":
                    bitrate = 1000
                    url = streams[stream]
                elif stream == "tabletLink":
                    bitrate = 300
                    url = streams[stream]

                # These windows stream won't work
                # elif stream == "windowsLink":
                #     bitrate = 1200
                #     url = streams[stream]
                # elif stream == "wpLink":
                #     bitrate = 1200
                #     url = streams[stream]

                elif stream == "name":
                    Logger.trace("Ignoring stream '%s'", stream)
                else:
                    Logger.warning("No url found for type '%s'", stream)

                # noinspection PyUnboundLocalVariable
                if "livestreams.omroep.nl/live/" in url and url.endswith("m3u8"):
                    Logger.info("Found NPO Stream, adding ?protection=url")
                    url = "%s?protection=url" % (url, )

                if bitrate:
                    part.append_media_stream(url, bitrate)

                    if url == live_stream_value and ".m3u8" in url:
                        # if it was equal to the previous one, assume we have a m3u8. Reset the others.
                        Logger.info("Found same M3u8 stream for all streams for this Live channel, using that one: %s", url)
                        live_item.MediaItemParts = []
                        live_item.url = url
                        live_item.complete = False
                        break
                    elif "playlist.m3u8" in url:
                        # if we have a playlist, use that one. Reset the others.
                        Logger.info("Found M3u8 playlist for this Live channel, using that one: %s", url)
                        live_item.MediaItemParts = []
                        live_item.url = url
                        live_item.complete = False
                        break
                    else:
                        # add it to the possibilities
                        live_stream_value = url
            items.append(live_item)
        return "", items

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
        title = result_set.get("title")

        if not title:
            return None

        if title.islower():
            title = "%s%s" % (title[0].upper(), title[1:])

        link = result_set.get("feedLink")
        if not link.startswith("http"):
            link = parse.urljoin(self.baseUrl, link)

        item = MediaItem(title, link)
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

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        media_link = result_set.get("ipadLink")
        title = result_set.get("title")

        # it seems overkill, but not all items have a contentLink and of we set
        # the url to self.baseUrl it will be a duplicate item if the titles are
        # equal
        url = result_set.get("contentLink") or media_link or self.baseUrl
        if not url.startswith("http"):
            url = parse.urljoin(self.baseUrl, url)

        item = MediaItem(title, url)

        if media_link:
            item.append_single_stream(media_link, self.channelBitrate)

        # get the thumbs from multiple locations
        thumb_urls = result_set.get("images", None)
        thumb_url = None
        if thumb_urls:
            # noinspection PyUnresolvedReferences
            thumb_url = \
                thumb_urls[0].get("fullScreenLink", None) or \
                thumb_urls[0].get("previewLink", None) or \
                result_set.get("imageLink", None)

        if thumb_url and not thumb_url.startswith("http"):
            thumb_url = parse.urljoin(self.baseUrl, thumb_url)

        if thumb_url:
            item.thumb = thumb_url

        item.type = 'video'
        item.description = HtmlHelper.to_text(result_set.get("text"))

        posix = result_set.get("timestamp", None)
        if posix:
            broadcast_date = DateHelper.get_date_from_posix(int(posix))
            item.set_date(broadcast_date.year,
                          broadcast_date.month,
                          broadcast_date.day,
                          broadcast_date.hour,
                          broadcast_date.minute,
                          broadcast_date.second)

        item.complete = True
        return item

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

        if result_set["mediaType"].lower() == "audio":
            item.append_single_stream(item.url)
            item.complete = True
            return item

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

        Logger.debug("Updating a (Live) video item")
        content, url = UriHandler.header(item.url, proxy=self.proxy)

        part = item.create_new_empty_media_part()
        if AddonSettings.use_adaptive_stream_add_on():
            part = item.create_new_empty_media_part()
            stream = part.append_media_stream(url, 0)
            M3u8.set_input_stream_addon_input(stream, self.proxy, item.HttpHeaders)
            item.complete = True
        else:
            for s, b in M3u8.get_streams_from_m3u8(url, self.proxy, append_query_string=True):
                item.complete = True
                part.append_media_stream(s, b)
            item.complete = True

        return item
