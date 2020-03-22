# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData


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
        self.noImage = ""

        # setup the urls
        self.noImage = "24classicsimage.png"
        self.mainListUri = "https://www.24classics.com/app/core/server_load.php?" \
                           "r=default&page=luister&serial=&subserial=&hook="
        self.baseUrl = "https://www.24classics.com"

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              json=True, preprocessor=self.make_episode_dictionary_array,
                              parser=["items", ], creator=self.create_episode_item)

        self._add_data_parser("*", json=True,
                              parser=["items", "tracklist"], creator=self.create_music_item,
                              updater=self.update_music_item)

        #===========================================================================================
        # non standard items

        #===========================================================================================
        # Test cases:

        # =========================== Actual channel setup STOPS here ==============================
        return

    def make_episode_dictionary_array(self, data):
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
        json_data = JsonHelper(data)
        dict_items = json_data.get_value("items", fallback=[])
        for item in dict_items:
            if item == "banners" or item == "curators":
                continue
            items.append(self.create_episode_item(dict_items[item]))

        Logger.debug("Pre-Processing finished")
        data = ""
        return data, items

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        title = result_set["title"]
        description = result_set.get("description", "")
        description_nl = result_set.get("introduction_lan1", "")
        thumb = result_set["image_full"]
        url = "https://www.24classics.com/app/core/server_load.php?" \
              "r=default&page=luister&serial=&subserial=&hook=%s" % (result_set["hook"],)

        item = MediaItem(title, url)
        item.thumb = thumb
        item.description = "%s\n\n%s" % (description_nl, description)
        item.description = item.description.strip()
        item.complete = True
        return item

    def create_music_item(self, result_set):
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
        title = "%(composers)s - %(title)s" % result_set
        url = "https://www.24classics.com/app/ajax/auth.php?serial=%(serial)s" % result_set

        item = MediaItem(title, url)
        item.type = "video"
        # seems to not really work well with track numbers (not showing)
        # item.type = "audio"
        item.complete = False
        item.description = "Composers: %(composers)s\nPerformers: %(performers)s" % result_set
        item.set_info_label("TrackNumber", result_set["order"])
        item.set_info_label("AlbumArtist", result_set["composers"].split(","))
        item.set_info_label("Artist", result_set["performers"].split(","))
        return item

    def update_music_item(self, item):
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

        Logger.debug('Starting update_music_item for %s (%s)', item.name, self.channelName)
        url, data = item.url.split("?")

        data = UriHandler.open(url, proxy=self.proxy, params=data, additional_headers=item.HttpHeaders)
        Logger.trace(data)
        json_data = JsonHelper(data)
        url = json_data.get_value("url", fallback=None)

        if url:
            item.append_single_stream(url)
            item.Complete = True
        return item
