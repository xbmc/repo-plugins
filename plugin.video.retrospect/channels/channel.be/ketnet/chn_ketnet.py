# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.streams.m3u8 import M3u8


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

        if self.channelCode == "ketnet":
            self.noImage = "ketnetimage.jpg"
            self.mainListUri = "https://www.ketnet.be/kijken"
            self.baseUrl = "https://www.ketnet.be"
            self.mediaUrlRegex = r'playerConfig\W*=\W*(\{[\w\W]{0,2000}?);(?:.vamp|playerConfig)'

        elif self.channelCode == "cobra":
            self.noImage = "cobraimage.png"
            self.mainListUri = "http://www.cobra.be/cm/cobra/cobra-mediaplayer"
            self.baseUrl = "http://www.cobra.be"

        self.swfUrl = "%s/html/flash/common/player.swf" % (self.baseUrl,)

        episode_regex = r'<a[^>]+href="(?<url>/kijken[^"]+)"[^>]*>\W*<img[^>]+src="' \
                        r'(?<thumburl>[^"]+)"[^>]+alt="(?<title>[^"]+)"'
        episode_regex = Regexer.from_expresso(episode_regex)
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              parser=episode_regex, creator=self.create_episode_item)

        self._add_data_parser("*", preprocessor=self.select_video_section)

        video_regex = Regexer.from_expresso(r'<a title="(?<title>[^"]+)" href="(?<url>[^"]+)"[^>]*>'
                                            r'\W+<img src="(?<thumburl>[^"]+)"[^<]+<span[^<]+[^<]+'
                                            r'[^>]+></span>\W+(?<description>[^<]+)')
        self._add_data_parser("*", parser=video_regex, creator=self.create_video_item,
                              updater=self.update_video_item)

        folder_regex = Regexer.from_expresso(r'<span class="more-of-program" rel="/(?<url>[^"]+)">')
        self._add_data_parser("*", parser=folder_regex, creator=self.create_folder_item)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def select_video_section(self, data):
        """ Performs pre-process actions for data processing

        :param str|unicode data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        end_of_section = data.rfind('<div class="ketnet-abc-index">')
        if end_of_section > 0:
            data = data[:end_of_section]

        # find the first main video
        json_data = Regexer.do_regex(self.mediaUrlRegex, data)
        if not json_data:
            Logger.debug("No show data found as JSON")
            return data, items

        Logger.trace(json_data[0])
        json = JsonHelper(json_data[0])
        title = json.get_value("title")
        url = json.get_value("mzid") or self.parentItem.url
        item = MediaItem(title, url)
        item.type = 'video'
        item.description = json.get_value("description", fallback=None)
        item.thumb = json.get_value("image", fallback=self.noImage)
        item.complete = False
        items.append(item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_folder_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        result_set["title"] = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
        return chn_class.Channel.create_folder_item(self, result_set)

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
        if item.url.startswith("http"):
            data = UriHandler.open(item.url, proxy=self.proxy)
            json_data = Regexer.do_regex(self.mediaUrlRegex, data)

            json = JsonHelper(json_data[0])
            mzid = json.get_value("mzid")
            if not mzid:
                item.url = json.get_value("source", "hls")
                return self.__update_from_source(item)
        else:
            mzid = item.url

        hls_over_dash = self._get_setting("hls_over_dash", 'false') == 'true'

        from resources.lib.streams.vualto import Vualto
        v = Vualto(self, "ketnet@prod")
        item = v.get_stream_info(item, mzid, hls_over_dash=hls_over_dash)
        return item

    def __update_from_source(self, item):
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

        if not item.url.endswith("m3u8"):
            data = UriHandler.open(item.url, proxy=self.proxy)
            json_data = Regexer.do_regex(self.mediaUrlRegex, data)
            if not json_data:
                Logger.error("Cannot find JSON stream info.")
                return item

            json = JsonHelper(json_data[0])
            Logger.trace(json.json)
            stream = json.get_value("source", "hls")
            if stream is None:
                stream = json.get_value("mzsource", "hls")
            Logger.debug("Found HLS: %s", stream)
        else:
            stream = item.url

        part = item.create_new_empty_media_part()
        for s, b in M3u8.get_streams_from_m3u8(stream, self.proxy):
            item.complete = True
            part.append_media_stream(s, b)

        # var playerConfig = {"id":"mediaplayer","width":"100%","height":"100%","autostart":"false","image":"http:\/\/www.ketnet.be\/sites\/default\/files\/thumb_5667ea22632bc.jpg","brand":"ketnet","source":{"hls":"http:\/\/vod.stream.vrt.be\/ketnet\/_definst_\/mp4:ketnet\/2015\/12\/Ben_ik_familie_van_R001_A0023_20151208_143112_864.mp4\/playlist.m3u8"},"analytics":{"type_stream":"vod","playlist":"Ben ik familie van?","program":"Ben ik familie van?","episode":"Ben ik familie van?: Warre - Aflevering 3","parts":"1","whatson":"270157835527"},"title":"Ben ik familie van?: Warre - Aflevering 3","description":"Ben ik familie van?: Warre - Aflevering 3"}
        return item
