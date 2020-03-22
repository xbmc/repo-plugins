# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.regexer import Regexer
from resources.lib.parserdata import ParserData
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
            self.mainListUri = "http://www.nickelodeon.nl/shows"
            self.baseUrl = "http://www.nickelodeon.nl"

        elif self.channelCode == "nickno":
            self.noImage = "nickelodeonimage.png"
            self.mainListUri = "http://www.nickelodeon.no/program/"
            self.baseUrl = "http://www.nickelodeon.no"

        else:
            raise NotImplementedError("Unknown channel code")

        episode_item_regex = r"""<a[^>]+href="(?<url>/[^"]+)"[^>]*>\W*<img[^>]+src='(?<thumburl>[^']+)'[^>]*>\W*<div class='info'>\W+<h2 class='title'>(?<title>[^<]+)</h2>\W+<p class='sub_title'>(?<description>[^<]+)</p>"""
        episode_item_regex = Regexer.from_expresso(episode_item_regex)
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              preprocessor=self.no_nick_jr,
                              parser=episode_item_regex, creator=self.create_episode_item)
        # <h2 class='row-title'>Nick Jr

        video_item_regex = r"""<li[^>]+data-item-id='\d+'>\W+<a href='(?<url>[^']+)'>\W+<img[^>]+src="(?<thumburl>[^"]+)"[^>]*>\W+<p class='title'>(?<title>[^<]+)</p>\W+<p[^>]+class='subtitle'[^>]*>(?<subtitle>[^>]+)</p>"""
        video_item_regex = Regexer.from_expresso(video_item_regex)
        self._add_data_parser("*",
                              preprocessor=self.pre_process_folder_list,
                              parser=video_item_regex, creator=self.create_video_item,
                              updater=self.update_video_item)

        self.pageNavigationRegex = r'href="(/video[^?"]+\?page_\d*=)(\d+)"'
        self.pageNavigationRegexIndex = 1
        self._add_data_parser("*", parser=self.pageNavigationRegex, creator=self.create_page_item)

        self.mediaUrlRegex = '<param name="src" value="([^"]+)" />'    # used for the update_video_item
        self.swfUrl = "http://origin-player.mtvnn.com/g2/g2player_2.1.7.swf"

        #===============================================================================================================
        # Test cases:
        #  NO: Avator -> Other items
        #  SE: Hotel 13 -> Other items
        #  NL: Sam & Cat -> Other items

        # ====================================== Actual channel setup STOPS here =======================================
        return

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

        item.isGeoLocked = True
        return item

    def no_nick_jr(self, data):
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

        end = data.find("<h2 class='row-title'>Nick Jr")

        Logger.debug("Pre-Processing finished")
        if end > 0:
            Logger.debug("Nick Jr content found starting at %d", end)
            return data[:end], items
        return data, items

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

        end = data.find('<li class="divider playlist-item">')
        if end < 0:
            end = data.find("<p>Liknande videos</p>")
        if end < 0:
            end = data.find("<p>Lignende videoer</p>")
        if end < 0:
            end = data.find("<p>Andere leuke video’s</p>")

        Logger.debug("Pre-Processing finished")
        if end > 0:
            return data[:end], items

        return data, items

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

        data = UriHandler.open(item.url, proxy=self.proxy)

        # get the playlist GUID
        playlist_guids = Regexer.do_regex("<div[^>]+data-playlist-id='([^']+)'[^>]+></div>", data)
        if not playlist_guids:
            # let's try the alternative then (for the new channels)
            playlist_guids = Regexer.do_regex('local_playlist[", -]+([a-f0-9]{20})"', data)
        playlist_guid = playlist_guids[0]
        play_list_url = "http://api.mtvnn.com/v2/nl/NL/local_playlists/{}.json?video_format=m3u8".format(playlist_guid)

        data = UriHandler.open(play_list_url, proxy=self.proxy)

        from resources.lib.helpers.jsonhelper import JsonHelper
        from resources.lib.streams.m3u8 import M3u8

        json_data = JsonHelper(data)
        m3u8_url = json_data.get_value("local_playlist_videos", 0, "url")
        part = item.create_new_empty_media_part()
        item.complete = M3u8.update_part_with_m3u8_streams(part, m3u8_url, proxy=self.proxy, channel=self, encrypted=True)
        return item
