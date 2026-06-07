# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class, contenttype, mediatype
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.parserdata import ParserData
from resources.lib.logger import Logger
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    THIS CHANNEL IS BASED ON THE PEPERZAKEN APPS FOR ANDROID
    """

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============

        # configure login stuff
        # setup the urls
        self.channelBitrate = 850  # : the default bitrate
        self.liveUrl = None        # : the live url if present

        if self.channelCode == "omroepbrabant":
            self.noImage = "omroepbrabantimage.png"
            self.mainListUri = "#alphalisting"
            self.baseUrl = "http://www.omroepbrabant.nl"
            self.liveUrl = "http://feed.omroepbrabant.nl/s520/tv.json"
            self.channelBitrate = 1500

        else:
            raise NotImplementedError("Channelcode '%s' not implemented" % (self.channelCode, ))

        self._add_data_parser(self.mainListUri,
                              preprocessor=self.create_alpha_listing,
                              match_type=ParserData.MatchExact)

        self._add_data_parser("https://api.omroepbrabant.nl/api/media/tv/series", json=True,
                              name="Alpha sublisting",
                              parser=["series"], creator=self.create_episode_item)

        self._add_data_parser("https://api.omroepbrabant.nl/api/media/series/v2/", json=True,
                              name="Show parsers",
                              preprocessor=self.add_seasons,
                              parser=["article", "children"], creator=self.create_video_item)

        self._add_data_parser("sourceid_string:", match_type=ParserData.MatchContains,
                              updater=self.update_video_item)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_alpha_listing(self, data):
        """ Performs pre-process actions for data processing and adds an alpha listing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        base_url = "https://api.omroepbrabant.nl/api/media/tv/series"
        title_format = "\a{}".format(LanguageHelper.get_localized_string(LanguageHelper.StartWith))

        items = []
        for char in " ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if char == " ":
                url = base_url
                title = "\a{}".format(LanguageHelper.get_localized_string(LanguageHelper.OtherChars))
            else:
                url = "{}/{}".format(base_url, char)
                title = title_format % (char, )

            item = FolderItem(title, url, content_type=contenttype.TVSHOWS)
            item.dontGroup = True
            items.append(item)

        if self.liveUrl:
            Logger.debug("Adding live item")
            live_item = MediaItem("\aLive TV", self.liveUrl)
            live_item.dontGroup = True
            items.append(live_item)

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

        Logger.trace(result_set)
        title = result_set["title"]
        episode_id = result_set["id"]
        url = "https://api.omroepbrabant.nl/api/media/series/v2/{}".format(episode_id)

        item = FolderItem(title, url, content_type=contenttype.TVSHOWS)
        item.thumb = self.__create_image_url(result_set["imageUrl"], "thumb")
        item.fanart = self.__create_image_url(result_set["imageUrl"], "fanart")
        item.poster = self.__create_image_url(result_set["imageUrl"], "poster")
        item.description = result_set["description"]

        return item

    def add_seasons(self, data):
        """ Performs pre-process actions for data processing and checks for additional seasons

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

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        title = result_set["title"]
        image = result_set["image"]["url"]
        thumb = self.__create_image_url(image, "thumb")
        poster = self.__create_image_url(image, "poster")
        # url = "https://api.omroepbrabant.nl/api/media/program/{}".format(result_set["externalId"])
        url = "https://omroepbrabant.bbvms.com/p/default/q/sourceid_string:{}.json".format(result_set["externalId"])

        item = MediaItem(title, url, media_type=mediatype.EPISODE)
        item.thumb = thumb
        item.poster = poster
        item.description = result_set.get("text")

        date_value = result_set["created"]
        # date_value = result_set["updated"]
        date_time = DateHelper.get_date_from_posix(date_value)
        # TODO: Fixed times
        item.set_date(date_time.year, date_time.month, date_time.day, date_time.hour,
                      date_time.minute,
                      date_time.second)

        if result_set["seriesId"] == "1":
            item.name = "{} - {:02d}:{:02d}".format(item.title, date_time.hour, date_time.minute)

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

        data = UriHandler.open(item.url)
        json_data = JsonHelper(data)

        clip_data = json_data.get_value("clipData", "assets")
        server = json_data.get_value("publicationData", "defaultMediaAssetPath")
        for clip in clip_data:
            url = clip["src"]
            if not url.startswith("http"):
                url = "{}{}".format(server, clip["src"])
            item.add_stream(url, int(clip["bandwidth"]))
            item.complete = True

        return item

    def __create_image_url(self, image, type_art):
        if type_art == "fanart":
            return image.replace("$width$", "1920").replace("$height$", "1080")
        if type_art == "thumb":
            return image.replace("$width$", "1280").replace("$height$", "720")
        if type_art == "poster":
            return image.replace("$width$", "1280").replace("$height$", "1920")
        return None
