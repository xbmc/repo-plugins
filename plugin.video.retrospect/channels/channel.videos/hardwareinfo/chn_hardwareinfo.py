# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.helpers import xmlhelper
from resources.lib.streams.youtube import YouTube
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.logger import Logger


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

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = "hardwareinfoimage.png"

        # setup the urls
        self.mainListUri = "http://nl.hardware.info/tv/rss-private/streaming"
        self.baseUrl = "http://www.youtube.com"

        # setup the main parsing data
        # self.episodeItemRegex = '<name>([^-]+) - (\d+)-(\d+)-(\d+)[^<]*</name>'
        # self._add_data_parser(self.mainListUri, preprocessor=self.add_episode_paging,
        #                     parser=self.episodeItemRegex, creator=self.create_episode_item)

        self.videoItemRegex = r'<(?:entry|item)>([\w\W]+?)</(?:entry|item)>'
        self._add_data_parser("http://nl.hardware.info/tv/rss-private/streaming",
                              parser=self.videoItemRegex, creator=self.create_video_item_hw_info,
                              updater=self.update_video_item)
        self._add_data_parser("*",
                              parser=self.videoItemRegex, creator=self.create_video_item,
                              updater=self.update_video_item)

        self.pageNavigationIndicationRegex = r'<page>(\d+)</page>'
        self.pageNavigationRegex = r'<page>(\d+)</page>'
        self.pageNavigationRegexIndex = 0
        self._add_data_parser("*", parser=self.pageNavigationRegex, creator=self.create_page_item)

        # ==========================================================================================
        # non standard items

        # ============================ Actual channel setup STOPS here =============================
        return

    # noinspection PyUnusedLocal
    def add_episode_paging(self, data):
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

        # we need to create page items. So let's just spoof the paging. Youtube has
        # a 50 max results per query limit.
        items_per_page = 50
        data = UriHandler.open(self.mainListUri, proxy=self.proxy)
        xml = xmlhelper.XmlHelper(data)
        nr_items = xml.get_single_node_content("openSearch:totalResults")

        for index in range(1, int(nr_items), items_per_page):
            items.append(self.create_episode_item([index, items_per_page]))

        # Continue working normal!
        return data, items

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[int] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        url = "http://gdata.youtube.com/feeds/api/users/hardwareinfovideo/uploads?max-results=%s&start-index=%s" % (
            result_set[1], result_set[0])
        title = "Hardware Info TV %04d-%04d" % (result_set[0], result_set[0] + result_set[1])
        item = MediaItem(title, url)
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

        xml_data = xmlhelper.XmlHelper(result_set)

        title = xml_data.get_single_node_content("title")

        # Retrieve an ID and create an URL like: http://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=OHqu64Qnz9M
        video_id = xml_data.get_single_node_content("id")
        last_slash = video_id.rfind(":") + 1
        video_id = video_id[last_slash:]
        # The old url does no longer work:
        # url = "http://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=%s" % (videoId,)
        url = "http://www.youtube.com/watch?v=%s" % (video_id, )

        item = MediaItem(title, url)
        item.type = 'video'

        # date stuff
        date = xml_data.get_single_node_content("published")
        year = date[0:4]
        month = date[5:7]
        day = date[8:10]
        hour = date[11:13]
        minute = date[14:16]
        # Logger.Trace("%s-%s-%s %s:%s", year, month, day, hour, minute)
        item.set_date(year, month, day, hour, minute, 0)

        # description stuff
        description = xml_data.get_single_node_content("media:description")
        item.description = description

        # thumbnail stuff
        thumb_url = xml_data.get_tag_attribute("media:thumbnail", {'url': None}, {'height': '360'})
        # <media:thumbnail url="http://i.ytimg.com/vi/5sTMRR0_Wo8/0.jpg" height="360" width="480" time="00:09:52.500" xmlns:media="http://search.yahoo.com/mrss/" />
        if thumb_url != "":
            item.thumb = thumb_url

        # finish up
        item.complete = False
        return item

    def create_video_item_hw_info(self, result_set):
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

        xml_data = xmlhelper.XmlHelper(result_set)

        title = xml_data.get_single_node_content("title")

        # Retrieve an ID and create an URL like: http://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=OHqu64Qnz9M
        url = xml_data.get_tag_attribute("enclosure", {'url': None}, {'type': 'video/youtube'})
        Logger.trace(url)

        item = MediaItem(title, url)
        item.type = 'video'

        # date stuff
        date = xml_data.get_single_node_content("pubDate")
        dayname, day, month, year, time, zone = date.split(' ', 6)
        month = DateHelper.get_month_from_name(month, language="en")
        hour, minute, seconds = time.split(":")
        Logger.trace("%s-%s-%s %s:%s", year, month, day, hour, minute)
        item.set_date(year, month, day, hour, minute, 0)

        # description stuff
        description = xml_data.get_single_node_content("description")
        item.description = description

        # thumbnail stuff
        thumb_urls = xml_data.get_tag_attribute("enclosure", {'url': None}, {'type': 'image/jpg'}, firstOnly=False)
        for thumb_url in thumb_urls:
            if thumb_url != "" and "thumb" not in thumb_url:
                item.thumb = thumb_url

        # finish up
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

        part = item.create_new_empty_media_part()
        for s, b in YouTube.get_streams_from_you_tube(item.url, self.proxy):
            item.complete = True
            part.append_media_stream(s, b)

        item.complete = True
        return item
