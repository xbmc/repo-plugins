# SPDX-License-Identifier: GPL-3.0-or-later
import pytz

from resources.lib import chn_class, mediatype
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper

from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.parserdata import ParserData
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.xbmcwrapper import XbmcWrapper


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
        self.noImage = "mtvnlimage.png"
        self.__country_id = None
        self.__clip_list_id = None
        self.__show_list_id = None
        self.__timezone = pytz.timezone("Europe/Amsterdam")
        self.__timezone_utc = pytz.timezone("UTC")

        # setup the urls
        if self.channelCode == "mtvde":
            self.mainListUri = "http://www.mtv.de/feeds/intl_m150/V8_0_0/" \
                               "9f78da03-d56a-4946-be43-41ed06a1b005"
            self.baseUrl = "https://www.mtv.de"
            self.__country_id = "mtv.de"
            self.__clip_list_id = "442813c0-9344-48d6-9674-f94c359fe9fb"
            self.__show_list_id = "62701278-3c80-4ef6-a801-1df8ffca7c78"
            self.__season_list_id = "bb3b48c4-178c-4cad-82c4-67ba76207020"

        self.swfUrl = "http://media.mtvnservices.com/player/prime/mediaplayerprime.2.11.4.swf"

        self._add_data_parser(r"https?://www.mtv.\w+/feeds/intl_m150/",
                              match_type=ParserData.MatchRegex,
                              name="Alpha list MTV", json=True,
                              parser=["result", "shows"], creator=self.create_program_items)

        self._add_data_parser(r"^https?://www.mtv.\w*/feeds/intl_m112/",
                              match_type=ParserData.MatchRegex,
                              name="Version 8 JSON Shows", json=True,
                              preprocessor=self.add_clips,
                              parser=["result", "data", "items"],
                              creator=self.create_video_item_json,
                              postprocessor=self.add_seasons)

        self._add_data_parser(r"^https?://www.mtv.\w+/feeds/intl_m300/",
                              match_type=ParserData.MatchRegex,
                              name="Version 8 JSON Clips", json=True,
                              parser=["result", "data", "items"],
                              creator=self.create_clip_item_json)

        self._add_data_parser("*", updater=self.update_video_item)

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_program_items(self, result_set):
        """ Creates a new list of MediaItems for a alpha char listing.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: list[MediaItem]|MediaItem|None

        """

        Logger.trace(result_set)

        items = []
        for result in result_set["value"]:
            title = result["title"]
            item_id = result["itemId"]

            url = "{}/feeds/intl_m112/V8_0_0/{}/{}" \
                .format(self.baseUrl, self.__show_list_id, item_id)

            item = MediaItem(title, url)
            item.description = result.get("description", None)
            item.metaData["guid"] = item_id
            item.complete = True
            item.thumb = "http://mtv-intl.mtvnimages.com/uri/mgid:arc:content:{}:{}?" \
                         "ep={}&stage=live&format=jpg&quality=0.8&quality=0.85" \
                         "&width=590&height=332&crop=true"\
                .format(self.__country_id, item_id, self.__country_id)
            item.fanart = "http://mtv-intl.mtvnimages.com/uri/mgid:arc:content:{}:{}?" \
                          "ep={}&stage=live&format=jpg&quality=0.8&quality=0.85" \
                          "&width=1280&height=720&crop=true"\
                .format(self.__country_id, item_id, self.__country_id)
            item.poster = "http://mtv-intl.mtvnimages.com/uri/mgid:arc:content:{}:{}?" \
                          "ep={}&stage=live&format=jpg&quality=0.8&quality=0.85" \
                          "&width=500&height=750&crop=true"\
                .format(self.__country_id, item_id, self.__country_id)
            items.append(item)
        return items

    # noinspection PyUnusedLocal
    def add_seasons(self, data, items):
        """ Performs post-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str|JsonHelper data:     The retrieve data that was loaded for the
                                         current item and URL.
        :param list[MediaItem] items:   The currently available items

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: list[MediaItem]

        """

        Logger.info("Performing Post-Processing")

        if not self.parentItem or "guid" not in self.parentItem.metaData:
            return items

        existing_seasons = set([i.metaData.get("season_id") for i in items])
        if not existing_seasons:
            return items

        item_id = self.parentItem.metaData["guid"]
        season_info_url = "http://www.mtv.de/feeds/intl_m308/V8_0_0/{0}/{1}/{1}".\
            format(self.__season_list_id, item_id)
        season_data = UriHandler.open(season_info_url)
        season_info = JsonHelper(season_data)

        for season in season_info.get_value("result", "data", "seasons", fallback=[]):
            Logger.trace("Found season: %s", season)
            season_id = season["id"]
            if season_id in existing_seasons:
                Logger.trace("Season is current season")
                continue

            url = "{}/feeds/intl_m112/V8_0_0/{}/{}/{}"\
                .format(self.baseUrl, self.__show_list_id, item_id, season_id)
            season_item = MediaItem(season["eTitle"], url)
            items.append(season_item)

        Logger.debug("Post-Processing finished")
        return items

    def add_clips(self, data):
        """ Adds a clip folder to items.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []
        if not self.parentItem or "guid" not in self.parentItem.metaData:
            return data, items

        clip_title = LanguageHelper.get_localized_string(LanguageHelper.Clips)
        item_id = self.parentItem.metaData["guid"]
        url = "{}/feeds/intl_m300/V8_0_0/{}/{}"\
            .format(self.baseUrl, self.__clip_list_id, item_id)

        clips = MediaItem("\a.: %s :." % (clip_title,), url)
        items.append(clips)

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_clip_item_json(self, result_set):
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

        # get the title
        title = result_set["title"]
        mgid = result_set["id"]

        url = "https://media-utils.mtvnservices.com/services/MediaGenerator/" \
              "mgid:arc:video:{}:{}" \
              "?arcStage=live&format=json&acceptMethods=hls&clang=nl" \
              "&https=true".format(self.__country_id, mgid)

        item = MediaItem(title, url)
        item.media_type = mediatype.EPISODE

        if "images" in result_set:
            item.thumb = result_set["images"]["url"]

        if "airDate" not in result_set:
            return item

        air_date = int(result_set["airDate"])
        date_stamp = DateHelper.get_date_from_posix(air_date, self.__timezone_utc)
        item.set_date(date_stamp.year, date_stamp.month, date_stamp.day)

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

        # get the title
        title = result_set["title"]
        mgid = result_set["id"]

        url = "http://media.mtvnservices.com/pmt/e1/access/index.html" \
              "?uri=mgid:arc:video:{}:{}&configtype=edge".format(self.__country_id, mgid)

        item = MediaItem(title, url)
        item.media_type = mediatype.EPISODE
        item.description = result_set["description"]

        if "images" in result_set:
            item.thumb = result_set["images"]["url"]

        air_date = int(result_set["publishDate"])
        date_stamp = DateHelper.get_date_from_posix(air_date, self.__timezone_utc)
        item.set_date(date_stamp.year, date_stamp.month, date_stamp.day)

        episode = result_set.get("episode")
        season = result_set.get("season")
        if season and episode:
            try:
                item.set_season_info(season, episode)
            except:
                Logger.debug("Error setting season and episode")

        duration = result_set.get("duration", "0:00")
        duration = duration.split(":")
        duration = int(duration[1]) + 60 * int(duration[0])
        item.set_info_label("duration", duration)

        # store season info
        item.metaData["season_id"] = result_set.get("seasonId")
        item.isGeoLocked = True
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

        if "index.html" in item.url:
            data = UriHandler.open(
                item.url,
                additional_headers={"Referer": "http://www.{}/".format(self.__country_id)}
            )
            json_data = JsonHelper(data)
            guid = json_data.get_value("feed", "items", 0, "guid")
            url = "https://media-utils.mtvnservices.com/services/MediaGenerator/" \
                  "{}?arcStage=live&format=json&acceptMethods=hls&clang=nl" \
                  "&https=true".format(guid)
        else:
            url = item.url

        data = UriHandler.open(url)
        json_data = JsonHelper(data)
        url = json_data.get_value("package", "video", "item", 0, "rendition", 0, "src")
        if not url:
            error = json_data.get_value("package", "video", "item", 0, "text")
            Logger.error("Error resolving url: %s", error)
            XbmcWrapper.show_dialog(LanguageHelper.ErrorId, error)
            return item

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()
        part.append_media_stream(url, 0)
        item.complete = True
        return item
