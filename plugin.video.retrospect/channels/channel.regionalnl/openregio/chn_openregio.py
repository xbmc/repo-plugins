# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.backtothefuture import PY2
from resources.lib.urihandler import UriHandler

if PY2:
    # noinspection PyUnresolvedReferences
    import urlparse as parse
else:
    # noinspection PyUnresolvedReferences
    import urllib.parse as parse

from resources.lib import chn_class
from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.parserdata import ParserData
from resources.lib.logger import Logger
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.htmlhelper import HtmlHelper
from resources.lib.streams.m3u8 import M3u8


class Channel(chn_class.Channel):
    """
    This channel is based on the Open JSON API for the Regionale Omroepen
    """

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.channelBitrate = 1350  # : the default bitrate
        self.liveUrl = None         # : the live url if present
        self.liveUrls = None        # : a collection of live streams
        self.recentUrl = None       # : the url for most recent items

        if self.channelCode == "wosnl":
            self.noImage = "wosnlimage.jpg"
            self.mainListUri = "https://media.wos.nl/retrospect/wos/wos-index.json"
            self.baseUrl = "https://media.wos.nl/retrospect/"
            self.liveUrl = "https://media.wos.nl/stream/wos/live.php"
            self.recentUrl = "https://media.wos.nl/retrospect/wos/wos-latest.json"

        elif self.channelCode == "dtvnl":
            self.noImage = "dtvnlimage.jpg"
            self.mainListUri = "https://media.wos.nl/retrospect/dtvnieuws/dtvnieuws-index.json"
            self.baseUrl = "https://media.wos.nl/retrospect/"
            self.recentUrl = "https://media.wos.nl/retrospect/dtvnieuws/dtvnieuws-latest.json"
            self.liveUrls = {
                "Dtv Oss & Bernheze": "https://rrr.sz.xlcdn.com/?account=dtvmaasland&file=dtv1&type=live&service=wowza&output=playlist.m3u8&format=jsonp",
                "Dtv Den Bosch": "https://rrr.sz.xlcdn.com/?account=dtvmaasland&file=dtv2&type=live&service=wowza&output=playlist.m3u8&format=jsonp",
                "Dtv Uden": "https://rrr.sz.xlcdn.com/?account=dtvmaasland&file=dtv2&type=live&service=wowza&output=playlist.m3u8&format=jsonp",
                "Mfm Radio": "https://rrr.sz.xlcdn.com/?account=dtvmaasland&file=mfm1&type=live&service=icecast&format=jsonp"
            }

        elif self.channelCode == "venlonl":
            self.noImage = "venlonlimage.jpg"
            self.mainListUri = "https://media.wos.nl/retrospect/omroepvenlo/omroepvenlo-index.json"
            self.baseUrl = "https://media.wos.nl/retrospect/"
            self.recentUrl = "https://media.wos.nl/retrospect/omroepvenlo/omroepvenlo-latest.json"

        elif self.channelCode == "horstnl":
            self.noImage = "horstnlimage.jpg"
            self.mainListUri = "https://media.wos.nl/retrospect/omroephorstaandemaas/omroephorstaandemaas-index.json"
            self.baseUrl = "https://media.wos.nl/retrospect/"
            self.recentUrl = "https://media.wos.nl/retrospect/omroephorstaandemaas/omroephorstaandemaas-latest.json"

        elif self.channelCode == "studio040":
            self.noImage = "studio040image.jpg"
            self.mainListUri = "https://media.wos.nl/retrospect/studio040/studio040-index.json"
            self.baseUrl = "https://media.wos.nl/retrospect/"
            self.recentUrl = "https://media.wos.nl/retrospect/studio040/studio040-latest.json"

        else:
            raise NotImplementedError("Channelcode '%s' not implemented" % (self.channelCode, ))

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, json=True,
                              name="Mainlist parser",
                              preprocessor=self.add_other_items, match_type=ParserData.MatchExact,
                              parser=[], creator=self.create_episode_item)

        self._add_data_parser("https://media.wos.nl/stream/wos/live.php", json=True,
                              name="Live stream parser",
                              parser=[], creator=self.create_live_item)

        self._add_data_parser("https://rrr.sz.xlcdn.com/?account=",
                              updater=self.update_live_item)

        self._add_data_parser("*", json=True,
                              parser=["items"], creator=self.create_video_item,
                              updater=self.update_video_item)
        return

    def add_other_items(self, data):
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

        if self.liveUrls:
            live_title = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
            live_item = MediaItem("\a{}".format(live_title), "")
            live_item.dontGroup = True
            items.append(live_item)

            for name, url in self.liveUrls.items():
                item = MediaItem(name, url)
                item.type = "video"
                item.isLive = True
                live_item.items.append(item)

        elif self.liveUrl:
            Logger.debug("Adding live item")
            live_title = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
            live_item = MediaItem("\a{}".format(live_title), self.liveUrl)
            live_item.dontGroup = True
            items.append(live_item)

        if self.recentUrl:
            Logger.debug("Adding recent item")
            recent_title = LanguageHelper.get_localized_string(LanguageHelper.Recent)
            recent_item = MediaItem("\a{}".format(recent_title), self.recentUrl)
            recent_item.dontGroup = True
            items.append(recent_item)

        return data, items

    def create_live_item(self, result_set):
        """ Creates a new MediaItem for an live item.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        title = result_set.get("title")
        link = result_set.get("streamurl")

        item = MediaItem(title, link)
        stream_type = result_set["type"]
        item.type = "video" if stream_type == "tv" else "audio"
        item.isLive = True
        item.thumb = result_set.get('screenshot')
        item.fanart = result_set.get('image')

        if "radio" in title.lower():
            item.type = "audio"
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

        Logger.trace(result_set)
        title = result_set.get("title")

        if not title:
            return None

        link = result_set.get("feedLink")
        if not link.startswith("http"):
            link = parse.urljoin(self.baseUrl, link)

        item = MediaItem(title, link)
        item.thumb = result_set.get("image")
        item.description = result_set.get("text")
        if item.description is not None:
            item.description = item.description.replace("<br>", "\n")
        item.complete = True

        timestamp = result_set.get("timestamp")
        if timestamp is not None:
            date_time = DateHelper.get_date_from_posix(result_set["timestamp"])
            item.set_date(date_time.year, date_time.month, date_time.day, date_time.hour,
                          date_time.minute,
                          date_time.second)

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

        title = result_set.get("title")
        media_link = result_set.get("video", result_set.get("ipadLink"))

        item = MediaItem(title, media_link)
        item.thumb = result_set.get("image", result_set.get("imageLink"))
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

        item.set_info_label("duration", result_set.get("duration", 0))
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

        if "icecast" in item.url:
            item.type = "audio"

        data = UriHandler.open(item.url)
        stream_info = JsonHelper(data)
        url = stream_info.get_value("data")
        item.url = url

        return self.update_video_item(item)

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

        if item.type == "audio":
            item.append_single_stream(item.url, 0)
            item.complete = True

        elif ".m3u8" in item.url:
            part = item.create_new_empty_media_part()
            item.complete = M3u8.update_part_with_m3u8_streams(
                part, item.url, channel=self, encrypted=False)

        elif item.url.endswith(".mp4"):
            item.append_single_stream(item.url, self.channelBitrate)
            item.complete = True

        return item
