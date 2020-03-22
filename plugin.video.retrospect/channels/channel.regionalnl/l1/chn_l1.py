# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class
from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler
from resources.lib.regexer import Regexer
from resources.lib.helpers.jsonhelper import JsonHelper


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
        self.noImage = "l1image.png"

        # setup the urls
        self.mainListUri = "https://l1.nl/gemist/"
        self.baseUrl = "https://l1.nl"

        # setup the main parsing data
        episode_regex = r'<li>\W*<a[^>]*href="(?<url>/[^"]+)"[^>]*>(?<title>[^<]+)</a>\W*</li>'
        episode_regex = Regexer.from_expresso(episode_regex)
        self._add_data_parser(self.mainListUri, preprocessor=self.pre_process_folder_list,
                              parser=episode_regex, creator=self.create_episode_item)

        # live stuff
        self._add_data_parsers(["#livetv", "#liveradio"], updater=self.update_live_stream)

        video_regex = r'<a[^>]*href="(?<url>/[^"]+)"[^>]*title="(?<title>[^"]+)"[^>]*>\W*<img[^>]+src="/(?<thumburl>[^"]+)'
        video_regex = Regexer.from_expresso(video_regex)
        self._add_data_parser("*", parser=video_regex, creator=self.create_video_item, updater=self.update_video_item)

        page_regex = r'<a[^>]+href="https?://l1.nl/([^"]+?pagina=)(\d+)"'
        page_regex = Regexer.from_expresso(page_regex)
        self.pageNavigationRegexIndex = 1
        self._add_data_parser("*", parser=page_regex, creator=self.create_page_item)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def pre_process_folder_list(self, data):
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

        if '>Populair<' in data:
            data = data[data.index('>Populair<'):]
        if '>L1-kanalen<' in data:
            data = data[:data.index('>L1-kanalen<')]

        Logger.debug("Pre-Processing finished")

        # add live items
        title = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
        item = MediaItem("\a.: {} :.".format(title), "")
        item.type = "folder"
        items.append(item)

        live_item = MediaItem("L1VE TV".format(title), "#livetv")
        live_item.type = "video"
        live_item.isLive = True
        item.items.append(live_item)

        live_item = MediaItem("L1VE Radio".format(title), "#liveradio")
        live_item.type = "video"
        live_item.isLive = True
        item.items.append(live_item)

        return data, items

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode but excludes L1 Gemist

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        item = chn_class.Channel.create_episode_item(self, result_set)
        if "L1 Gemist" in item.name:
            return None
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
        if not item.thumb.startswith("http"):
            item.thumb = "%s/%s" % (self.baseUrl, item.thumb)
        return item

    def update_live_stream(self, item):
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

        part = item.create_new_empty_media_part()
        if item.url == "#livetv":
            url = "https://d34pj260kw1xmk.cloudfront.net/live/l1/tv/index.m3u8"
            M3u8.update_part_with_m3u8_streams(part, url, encrypted=True, proxy=self.proxy)
        else:
            # the audio won't play with the InputStream Adaptive add-on.
            url = "https://d34pj260kw1xmk.cloudfront.net/live/l1/radio/index.m3u8"
            for s, b in M3u8.get_streams_from_m3u8(url, self.proxy):
                part.append_media_stream(s, b)

        item.complete = True
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

        if not item.url.endswith(".js"):
            data = UriHandler.open(item.url, proxy=self.proxy)
            data_id = Regexer.do_regex(r'data-id="(\d+)"[^>]+data-playout', data)
            if data_id is None:
                Logger.warning("Cannot find stream-id for L1 stream.")
                return item

            data_url = "https://limburg.bbvms.com/p/L1_video/c/{}.json".format(data_id[0])
        else:
            data_url = item.url

        data = UriHandler.open(data_url, proxy=self.proxy)
        json = JsonHelper(data, logger=Logger.instance())
        Logger.trace(json)

        base_url = json.get_value("publicationData", "defaultMediaAssetPath")
        streams = json.get_value("clipData", "assets")
        item.MediaItemParts = []
        part = item.create_new_empty_media_part()
        for stream in streams:
            url = stream.get("src", None)
            if "://" not in url:
                url = "{}{}".format(base_url, url)
            bitrate = stream.get("bandwidth", None)
            if url:
                part.append_media_stream(url, bitrate)

        if not item.thumb and json.get_value("thumbnails"):
            url = json.get_value("thumbnails")[0].get("src", None)
            if url and "http:/" not in url:
                url = "%s%s" % (self.baseUrl, url)
            item.thumb = url
        item.complete = True
        return item
