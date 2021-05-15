# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class, mediatype, contenttype

from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.regexer import Regexer
from resources.lib.helpers.datehelper import DateHelper

from resources.lib.logger import Logger
from resources.lib.streams.m3u8 import M3u8
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
                              r'[^>]*>(?<month>\w+) (?<day>\d+)\D+(?<year>\d+)'
        self.videoItemRegex = Regexer.from_expresso(self.videoItemRegex)
        self._add_data_parser("*",
                              parser=self.videoItemRegex, creator=self.create_video_item,
                              updater=self.update_video_item)

        self.folderItemRegex = r'<div class="all-episodes">\W*<a href="(?<url>[^"]+)"[^>]*>(?<title>[^>]+)</a>'
        self.folderItemRegex = Regexer.from_expresso(self.folderItemRegex)
        self._add_data_parser("*",
                              parser=self.folderItemRegex,
                              creator=self.create_folder_item)

        self._add_data_parser("*",
                              parser=r'<a class="next" href="(\?page=(\d+)[^"]+)">',
                              creator=self.create_page_item)

        self._add_data_parser(".m3u8", match_type=ParserData.MatchEnd, updater=self.update_m3u8)
        self.mediaUrlRegex = r'<a href="([^"]+(?:_(\d+))?.mp4)"[^>]+download>'

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

        item = MediaItem("\a.: TWiT.TV Live :.",
                         "http://iphone-streaming.ustream.tv/uhls/1524/streams/live/iphone/playlist.m3u8",
                         media_type=mediatype.VIDEO)
        item.complete = False
        item.isLive = True

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

        # https://twit.tv/list/episodes?page=2&filter%5Bshows%5D=1635
        url = "%s/%s" % (self.baseUrl, result_set["url"])
        item = FolderItem(result_set["title"], url, content_type=contenttype.EPISODES, media_type=mediatype.TVSHOW)

        item.thumb = result_set["thumburl"]
        if not item.thumb.startswith("http"):
            item.thumb = "%s%s" % (self.baseUrl, item.thumb)
        item.thumb = item.thumb.replace("coverart-small", "coverart")
        item.complete = True
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

        Logger.debug("Starting create_page_item")

        item = FolderItem(result_set[1], "{}/list/episodes{}".format(self.baseUrl, result_set[0]),
                          content_type=contenttype.NONE, media_type=mediatype.PAGE)
        Logger.debug("Created '%s' for url %s", item.name, item.url)
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

        item = MediaItem(name, url, media_type=mediatype.EPISODE)
        month = result_set["month"]
        month = DateHelper.get_month_from_name(month, "en")
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
        * set at least one MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaSteam then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        data = UriHandler.open(item.url)
        streams = Regexer.do_regex(self.mediaUrlRegex, data)

        item.streams = []
        for stream in streams:
            Logger.trace(stream)
            item.add_stream(stream[0], stream[1] or 0)

        item.complete = True
        return item

    def update_m3u8(self, item):
        # http://iphone-streaming.ustream.tv/uhls/1524/streams/live/iphone/playlist.m3u8
        part = item.create_new_empty_media_part()
        item.complete = M3u8.update_part_with_m3u8_streams(part, item.url, encrypted=False)
        return item
