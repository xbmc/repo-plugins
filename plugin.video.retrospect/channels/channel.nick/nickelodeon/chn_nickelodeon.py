# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class
from resources.lib.helpers.datehelper import DateHelper

from resources.lib.mediaitem import MediaItem
from resources.lib.parserdata import ParserData
from resources.lib.regexer import Regexer
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
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
        # setup the main parsing data
        if self.channelCode == 'nickelodeon':
            self.noImage = "nickelodeonimage.png"
            self.mainListUri = "https://www.nickelodeon.nl/shows"
            self.baseUrl = "https://www.nickelodeon.nl"

        elif self.channelCode == "nickno":
            self.noImage = "nickelodeonimage.png"
            self.mainListUri = "https://www.nickelodeon.no/shows"
            self.baseUrl = "https://www.nickelodeon.no"

        else:
            raise NotImplementedError("Unknown channel code")

        self._add_data_parser(self.mainListUri, json=True, name="JSON extract mainlist",
                              match_type=ParserData.MatchExact,
                              preprocessor=self.extract_json_episodes,
                              parser=['items'], creator=self.create_json_episode_item)

        self._add_data_parser("https://www.nickelodeon.n[ol]/shows/",
                              name="JSON Retriever for videos",
                              match_type=ParserData.MatchRegex,
                              json=True, preprocessor=self.extract_json_video)

        self._add_data_parser("https://www.nickelodeon.n[ol]/shows/", name="JSON video creator",
                              match_type=ParserData.MatchRegex, json=True,
                              parser=["items"], creator=self.create_json_video_item)

        self._add_data_parser("https://www.nickelodeon.n[ol]/shows/", name="JSON season creator",
                              match_type=ParserData.MatchRegex,  json=True,
                              parser=["seasons"], creator=self.create_json_season_item)

        self._add_data_parser("/api/context/mgid%3Aarc%3Aseason%3A", name="JSON API Videos",
                              match_type=ParserData.MatchContains, json=True,
                              parser=["items"], creator=self.create_json_video_item)

        self._add_data_parser("*", name="Generic Updater", updater=self.update_video_item)

        #===============================================================================================================
        # Test cases:
        #  NO: Avator -> Other items
        #  SE: Hotel 13 -> Other items
        #  NL: Sam & Cat -> Other items

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def extract_json_video(self, data):
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

        data = Regexer.do_regex(r'window.__DATA__ = ([\w\W]+?});\s*window.__PUSH_STATE__', data)[0]
        json_data = JsonHelper(data)
        # Get the main content container
        main_container = [m for m in json_data.get_value("children") if m["type"] == "MainContainer"]

        # Extract seasons
        seasons = []
        if not self.parentItem.metaData.get("is_season", False):
            seasons = [
                lst["props"]["items"]
                for lst in main_container[0]["children"]
                if lst["type"] == "SeasonSelector"
            ]
            if seasons:
                seasons = [s for s in seasons[0] if s["url"]]
                # Inject them
                json_data.json["seasons"] = seasons

        # Find the actual
        line_lists = [lst for lst in main_container[0]["children"] if lst["type"] == "LineList"]
        for line_list in line_lists:
            if line_list.get("props", {}).get("type") == "video-guide":
                json_data.json = line_list["props"]

                # Get the actual full episode list
                all_episodes = json_data.get_value("filters", "items", 0, "url")
                url_all_episodes = "{}{}".format(self.baseUrl, all_episodes)
                data = UriHandler.open(url_all_episodes)
                json_data = JsonHelper(data)

                # And append seasons again
                if seasons:
                    json_data.json["seasons"] = seasons
                return json_data, items

        Logger.warning("Cannot extract video items")
        return json_data, items

    def extract_json_episodes(self, data):
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

        data = Regexer.do_regex(r'window.__DATA__ = ([\w\W]+?});\s*window.__PUSH_STATE__', data)[0]
        json_data = JsonHelper(data)
        main_container = [m for m in json_data.get_value("children") if m["type"] == "MainContainer"]
        line_list = [item for item in main_container[0]["children"] if item["type"] == "LineList"]
        line_list = line_list[0]["props"]
        json_data.json = line_list
        return json_data, items

    def create_json_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set:   The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        meta = result_set["meta"]
        name = meta["header"]["title"]
        url = "{}{}".format(self.baseUrl, result_set["url"])

        item = MediaItem(name, url)
        item.description = meta.get("description")
        item.isGeoLocked = True
        media_info = result_set.get("media")
        if media_info is not None:
            item.thumb = media_info.get("image", {}).get("url")
        return item

    def create_json_season_item(self, result_set):
        """ Creates a MediaItem of type 'folder' for a season using the result_set from the regex.

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

        url = "{}{}".format(self.baseUrl, result_set["url"])
        item = MediaItem(result_set["label"], url)
        item.metaData["is_season"] = True
        return item

    def create_json_video_item(self, result_set):
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
        meta = result_set["meta"]
        name = meta["header"]["title"]
        if isinstance(name, dict):
            name = name["text"]

        sub_heading = meta.get("subHeader")
        if sub_heading:
            name = "{} - {}".format(name, sub_heading)

        url = "{}{}".format(self.baseUrl, result_set["url"])
        item = MediaItem(name, url)
        item.type = "video"
        item.description = meta.get("description")
        item.thumb = result_set.get("media", {}).get("image", {}).get("url")
        item.isGeoLocked = True

        date_value = meta["date"]
        if "." in date_value:
            date = DateHelper.get_date_from_string(date_value, date_format="%d.%m.%Y")
        else:
            date = DateHelper.get_date_from_string(date_value, date_format="%d/%m/%Y")
        item.set_date(*date[0:6])

        return item

    def update_video_item(self, item):
        """Updates an existing MediaItem with more data.

        Arguments:
        item : MediaItem - the MediaItem that needs to be updated

        Returns:
        The original item with more data added to it's properties.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)
        from resources.lib.streams.m3u8 import M3u8

        data = UriHandler.open(item.url)
        video_id = Regexer.do_regex(r'{"video":{"config":{"uri":"([^"]+)', data)[0]
        url = "http://media.mtvnservices.com/pmt/e1/access/index.html?uri={}&configtype=edge".format(video_id)
        meta_data = UriHandler.open(url, referer=self.baseUrl)
        meta = JsonHelper(meta_data)
        stream_parts = meta.get_value("feed", "items")
        for stream_part in stream_parts:
            stream_url = stream_part["group"]["content"]
            stream_url = stream_url.replace("&device={device}", "")
            stream_url = "%s&format=json&acceptMethods=hls" % (stream_url,)
            stream_data = UriHandler.open(stream_url)
            stream = JsonHelper(stream_data)

            # subUrls = stream.get_value("package", "video", "item", 0, "transcript", 0, "typographic")  # NOSONAR
            part = item.create_new_empty_media_part()

            hls_streams = stream.get_value("package", "video", "item", 0, "rendition")
            for hls_stream in hls_streams:
                hls_url = hls_stream["src"]
                item.complete |= M3u8.update_part_with_m3u8_streams(part, hls_url)

        item.complete = True
        Logger.trace("Media url: %s", item)
        return item
