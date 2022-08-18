# SPDX-License-Identifier: GPL-3.0-or-later
import datetime

from resources.lib import chn_class, mediatype
from resources.lib.helpers.htmlhelper import HtmlHelper

from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediatype import EPISODE
from resources.lib.parserdata import ParserData
from resources.lib.streams.m3u8 import M3u8
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
        self.noImage = "at5image.png"
        self.apiFormat = None

        # setup the urls
        if self.channelCode == "rtvnh":
            self.mainListUri = "https://www.nhnieuws.nl/media"
            self.apiFormat = "https://ditisdesupercooleappapi.nhnieuws.nl/api/news?source=web&slug=themas&page={}"
            self.baseUrl = "https://ditisdesupercooleappapi.nhnieuws.nl"
        else:
            self.mainListUri = "http://www.at5.nl/gemist/tv"
            self.apiFormat = "https://ditisdesupercooleappapi.at5.nl/api/news?source=web&slug=tv&page={}"
            self.baseUrl = "https://ditisdesupercooleappapi.at5.nl"

        self.mainListUri = "#json_episodes"

        # setup the main parsing data
        epside_item_regex = r'<option value="(\d+)"[^>]*>([^<]+)'
        self._add_data_parser("http://www.at5.nl/gemist/tv", match_type=ParserData.MatchExact,
                              parser=epside_item_regex, creator=self.create_episode_item,
                              preprocessor=self.add_live_channel)

        self._add_data_parser("#json_episodes",
                              name="JSON based mainlist", json=True,
                              preprocessor=self.load_all_episodes,
                              parser=[], creator=self.create_episode_item_json)

        self._add_data_parser("https://ditisdesupercooleappapi.[^/]+.nl/api/article",
                              match_type=ParserData.MatchRegex,
                              name="JSON video parser", json=True,
                              parser=["article", "children"], creator=self.create_video_item_json)

        # Main video items
        video_item_regex = r'data-href="/(gemist/tv/\d+/(\d+)/[^"]+)"[^>]*>\W*<div class="uitz_new">' \
                           r'\W*<div class="uitz_new_image">\W*<img src="([^"]+)[^>]*>\W+</div>\W+' \
                           r'<div class="uitz_new_desc">(?:\W*<div[^>]*>){1,2}[^-]*-([^<]+)</div>' \
                           r'\W+div class="uitz_new_desc_title_time">\W+\w+ (\d+) (\w+) (\d+) (\d+):(\d+)'
        self._add_data_parser("*",
                              parser=video_item_regex, creator=self.create_video_item,
                              updater=self.update_video_item)

        # Paging
        self.pageNavigationRegexIndex = 1
        page_navigation_regex = r'<a[^>]+href="([^"]+/)(\d+)"[^>]*>\W+gt;\W+</a>'
        self._add_data_parser("*", parser=page_navigation_regex, creator=self.create_page_item)

        self._add_data_parser("#livestream", updater=self.update_live_stream)

        #===============================================================================================================
        # non standard items
        self.mediaUrlRegex = r'.setup([^<]+);\W*</script>'

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def load_all_episodes(self, data):
        episodes_json = []

        data, items = self.add_live_channel(data)

        for i in range(0, 20):
            url = self.apiFormat.format(i)
            data = UriHandler.open(url)
            json_data = JsonHelper(data)
            item_data = json_data.get_value("category", "news", fallback=[])
            episodes_json += item_data
            if len(item_data) < json_data.get_value("pageSize"):
                break

        amsterdam_vandaag = MediaItem(
            "Amsterdam Vandaag",
            "https://ditisdesupercooleappapi.at5.nl/api/article/p123")
        amsterdam_vandaag.thumb = "https://media.at5.nl/cache/i/459000/images/459628.w1600.r16-9.6ef7807.q90.jpg"
        now = datetime.datetime.now() - datetime.timedelta(days=1)
        amsterdam_vandaag.set_date(now.year, now.month, now.day)
        items.append(amsterdam_vandaag)

        dummy = JsonHelper("{}")
        dummy.json = episodes_json
        return dummy, items

    def add_live_channel(self, data):
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

        title = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
        item = MediaItem("\a.: {} :.".format(title), "")
        now = datetime.datetime.now()
        item.set_date(now.year, now.month, now.day, 23, 59, 58)
        items.append(item)

        live_item = MediaItem(title, "#livestream")
        live_item.media_type = mediatype.EPISODE
        live_item.isLive = True
        item.items.append(live_item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_episode_item_json(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        time_stamp = result_set["created"]
        if time_stamp <= 1420070400:
            # older items don't have videos for now
            return None

        url = "{}/api/article/{}".format(self.baseUrl, result_set["externalId"])
        item = MediaItem(result_set["title"], url)
        item.description = HtmlHelper.to_text(result_set.get("text"))

        date_time = DateHelper.get_date_from_posix(time_stamp)
        item.set_date(date_time.year, date_time.month, date_time.day)

        # noinspection PyTypeChecker
        image_data = result_set.get("media", [])
        video_url = None
        for image in image_data:
            item.thumb = image.get("imageHigh", image.get("image"))
            video_url = image.get("url")

        # In some cases the main list only has videos
        if result_set.get("video", False):
            if video_url is None:
                return None

            item.media_type = EPISODE
            item.url = video_url

        return item

    def create_video_item_json(self, result_set):
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

        image_data = result_set.get("media", [])
        thumb = None
        for image in image_data:
            thumb = image.get("imageHigh", image["image"])

        video_info = result_set.get("video")
        if video_info:
            url = video_info["externalId"]
        else:
            return None

        item = MediaItem(result_set["title"], url, media_type=EPISODE)
        item.thumb = thumb or self.noImage
        item.description = HtmlHelper.to_text(result_set.get("text"))

        # Let's not do the time now
        time_stamp = result_set["created"]
        date_time = DateHelper.get_date_from_posix(time_stamp)
        item.set_date(date_time.year, date_time.month, date_time.day, date_time.hour,
                      date_time.minute,
                      date_time.second)
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

        item.complete = M3u8.update_part_with_m3u8_streams(item, item.url, channel=self)
        return item

    def update_live_stream(self, item):
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

        Logger.debug("Updating the live stream")
        url = "https://rrr.sz.xlcdn.com/?account=atvijf" \
              "&file=live&type=live&service=wowza&protocol=https&output=playlist.m3u8"

        item.complete = \
            M3u8.update_part_with_m3u8_streams(item, url, channel=self)

        return item
