# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import datetime
from resources.lib import chn_class
from resources.lib.mediaitem import MediaItem
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.parserdata import ParserData
from resources.lib.regexer import Regexer
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    This channel is based on the peperzaken apps for Android
    """

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # configure login stuff
        # setup the urls
        self.noImage = "flevoimage.png"
        self.mainListUri = "https://www.omroepflevoland.nl/block/missed/list?category=Gemist&page=1"
        self.baseUrl = "https://www.omroepflevoland.nl"
        self.channelBitrate = 780

        video_item_regex = r'<a[^>]+href="(?<url>[^"]+)"(?:[^>]+>\W*){2}<picture[^>]+>\s*' \
                           r'<source[^>]+srcset="(?<thumburl>[^"]+)"[^>]*>\s*(?:[^>]+>){9}\s*<h5>' \
                           r'(?<title>[^<]+)<[^>]*>\s*(?<date>\d+-\d+-\d+\s+\d+:\d+)(?:[^>]+>)' \
                           r'{11}\W*(?<description>[^<]+)</p>'
        video_item_regex = Regexer.from_expresso(video_item_regex)

        self._add_data_parser(self.mainListUri, preprocessor=self.add_live_streams,
                              parser=video_item_regex, creator=self.create_video_item)

        self._add_data_parser("https://[^/]*.cloudfront.net/live/", updater=self.update_live_urls,
                              match_type=ParserData.MatchRegex)

        self._add_data_parser("*", preprocessor=self.add_live_streams,
                              parser=video_item_regex, creator=self.create_video_item,
                              updater=self.update_video_item)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

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

        items = []
        if self.parentItem is None:
            live_item = MediaItem(
                "\a.: Live TV :.",
                "https://d5ms27yy6exnf.cloudfront.net/live/omroepflevoland/tv/index.m3u8"
            )
            live_item.type = 'video'
            live_item.dontGroup = True
            now = datetime.datetime.now()
            live_item.set_date(now.year, now.month, now.day, now.hour, now.minute, now.second)
            items.append(live_item)

            live_item = MediaItem(
                "\a.: Live Radio :.",
                "https://d5ms27yy6exnf.cloudfront.net/live/omroepflevoland/radio/index.m3u8"
            )
            live_item.type = 'video'
            live_item.dontGroup = True
            now = datetime.datetime.now()
            live_item.set_date(now.year, now.month, now.day, now.hour, now.minute, now.second)
            items.append(live_item)

        # add "More"
        more = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
        current_url = self.parentItem.url if self.parentItem is not None else self.mainListUri
        url, page = current_url.rsplit("=", 1)
        url = "{}={}".format(url, int(page) + 1)

        item = MediaItem(more, url)
        item.complete = True
        items.append(item)

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

        item = chn_class.Channel.create_video_item(self, result_set)
        if item is None:
            return item

        time_stamp = DateHelper.get_date_from_string(result_set["date"], "%d-%m-%Y %H:%M")
        item.set_date(*time_stamp[0:6])
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

        data = UriHandler.open(item.url, proxy=self.proxy)
        stream = Regexer.do_regex(r'data-file="([^"]+)+', data)[0]

        part = item.create_new_empty_media_part()
        if ".mp3" in stream:
            item.complete = True
            part.append_media_stream(stream, 0)
        elif stream.endswith(".mp4"):
            item.complete = True
            part.append_media_stream(stream, 2500)
        elif ".m3u8" in stream:
            item.url = stream
            return self.update_live_urls(item)
        return item

    def update_live_urls(self, item):
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

        part = item.create_new_empty_media_part()
        if AddonSettings.use_adaptive_stream_add_on():
            stream = part.append_media_stream(item.url, 0)
            M3u8.set_input_stream_addon_input(stream, self.proxy)
            item.complete = True
        else:

            for s, b in M3u8.get_streams_from_m3u8(item.url, self.proxy):
                item.complete = True
                part.append_media_stream(s, b)
            item.complete = True
        return item
