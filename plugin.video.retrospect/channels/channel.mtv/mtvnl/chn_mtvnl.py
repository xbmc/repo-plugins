# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.parserdata import ParserData
from resources.lib.urihandler import UriHandler
from resources.lib.regexer import Regexer
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.datehelper import DateHelper


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

        # setup the urls
        self.__backgroundServiceEp = None
        self.__region = None
        if self.channelCode == "mtvnl":
            # self.mainListUri = "http://api.mtvnn.com/v2/site/m79obhheh2/nl/franchises.json?per=2147483647"
            # Configuration on: http://api.playplex.viacom.com/feeds/networkapp/intl/main/1.5?key=networkapp1.0&brand=mtv&platform=android&region=NL&version=2.2
            # Main screens: http://api.playplex.viacom.com/feeds/networkapp/intl/screen/1.5/mgid:arc:page:mtv.nl:aec18556-7dbb-4ac4-a1f7-90e17fa2e069?key=networkapp1.0&brand=mtv&platform=android&region=NL&version=2.2&region=NL&mvpd=
            self.mainListUri = "http://api.playplex.viacom.com/feeds/networkapp/intl/promolist/1.5/" \
                               "mgid:arc:promotion:mtv.nl:0b8e68bb-8477-4eee-940f-6caa86e01960?" \
                               "key=networkapp1.0&" \
                               "brand=mtv&" \
                               "platform=android&" \
                               "region=NL&" \
                               "version=2.2&" \
                               "mvpd="
            self.baseUrl = "http://www.mtv.nl"
            self.__backgroundServiceEp = "1b5b03c4"
            self.__region = "NL"

        elif self.channelCode == "mtvde":
            # self.mainListUri = "http://api.mtvnn.com/v2/site/va7rcfymx4/de/franchises.json?per=2147483647"
            # http://api.playplex.viacom.com/feeds/networkapp/intl/main/1.5?key=networkapp1.0&
            # brand=mtv&platform=android&region=DE&version=2.2
            self.mainListUri = "http://api.playplex.viacom.com/feeds/networkapp/intl/promolist/1.5/" \
                               "mgid:arc:promotion:mtv.de:0af488a0-6610-4e25-8483-25e3039b19d3?" \
                               "key=networkapp1.0&" \
                               "brand=mtv&" \
                               "platform=android&" \
                               "region=DE&" \
                               "version=2.2&" \
                               "mvpd="
            self.baseUrl = "http://www.mtv.de"
            self.__backgroundServiceEp = "e6bfc4ca"
            self.__region = "DE"

        self.swfUrl = "http://media.mtvnservices.com/player/prime/mediaplayerprime.2.11.4.swf"

        self._add_data_parser("http://api.playplex.viacom.com/feeds/networkapp/intl/promolist/1.5/",
                              name="Main show listing PlayPlay API", json=True,
                              parser=["data", "items"], creator=self.create_episode_item)

        self._add_data_parser("http://api.playplex.viacom.com/feeds/networkapp/intl/series/items",
                              name="Main video listing PlayPlay API", json=True,
                              parser=["data", "items"], creator=self.create_video_item)

        # Old API
        self._add_data_parser(r"http://api.mtvnn.com/v2/site/[^/]+/\w+/franchises.json",
                              match_type=ParserData.MatchRegex,
                              name="V2 API show listing", json=True,
                              parser=[], creator=self.create_episode_item_json)
        self._add_data_parser(r"http://api.mtvnn.com/v2/site/[^/]+/\w+/episodes.json",
                              match_type=ParserData.MatchRegex,
                              name="V2 API video listing", json=True,
                              parser=[], creator=self.create_video_item_json)

        self._add_data_parser("*", updater=self.update_video_item)

        # # setup the main parsing data
        # if "json" in self.mainListUri:
        #     Logger.Debug("Doing a JSON version of MTV")
        #     self.episodeItemJson = ()
        #     self.videoItemJson = ()
        #     self.create_episode_item = self.create_episode_item_json
        #     self.create_video_item = self.create_video_item_json
        # else:
        #     Logger.Debug("Doing a HTML version of MTV")
        #     self.episodeItemRegex = '<a href="/(shows/[^"]+)" title="([^"]+)"><img [^>]+src="([^"]+)"'  # used for the ParseMainList
        #     self.videoItemRegex = '<a href="([^"]+)" title="([^"]+)">(?:<span class=\Wepisode_number\W>(\d+)</span>){0,1}[\w\W]{0,100}?<img[^>]+src="([^"]+)"[^>]+\W+</a>'
        #     self.folderItemRegex = '<li>\W+<a href="/(seizoen/[^"]+)">([^<]+)</a>'

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        title = result_set["title"]
        # The id = result_set["id"]
        url = "http://api.playplex.viacom.com/feeds/networkapp/intl/series/items/1.5/%s" \
              "?key=networkapp1.0&brand=mtv&platform=android&region=%s&version=2.2" % \
              (result_set["id"], self.__region)
        item = MediaItem(title, url)
        item.description = result_set.get("description", None)
        item.complete = True

        images = result_set.get("images", [])
        if images:
            #  mgid:file:gsp:scenic:/international/mtv.nl/playplex/dutch-ridiculousness/Dutch_Ridiculousness_Landscape.png
            # http://playplex.mtvnimages.com/uri/mgid:file:gsp:scenic:/international/mtv.nl/playplex/dutch-ridiculousness/Dutch_Ridiculousness_Landscape.png
            for image in images:
                # noinspection PyTypeChecker
                if image["width"] > 500:
                    item.fanart = "http://playplex.mtvnimages.com/uri/%(url)s" % image
                else:
                    item.thumb = "http://playplex.mtvnimages.com/uri/%(url)s" % image

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

        :param dict[str,dict|None] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        title = result_set["title"]
        if "subTitle" in result_set:
            title = "%s - %s" % (title, result_set["subTitle"])
        mgid = result_set["id"].split(":")[-1]
        url = "http://feeds.mtvnservices.com/od/feed/intl-mrss-player-feed" \
              "?mgid=mgid:arc:episode:mtvplay.com:%s" \
              "&ep=%s" \
              "&episodeType=segmented" \
              "&imageEp=android.playplex.mtv.%s" \
              "&arcEp=android.playplex.mtv.%s" \
              % (mgid, self.__backgroundServiceEp, self.__region.lower(), self.__region.lower())

        item = MediaItem(title, url)
        item.type = "video"
        item.description = result_set.get("description", None)
        item.isGeoLocked = True
        images = result_set.get("images", [])
        if images:
            # mgid:file:gsp:scenic:/international/mtv.nl/playplex/dutch-ridiculousness/Dutch_Ridiculousness_Landscape.png
            # http://playplex.mtvnimages.com/uri/mgid:file:gsp:scenic:/international/mtv.nl/playplex/dutch-ridiculousness/Dutch_Ridiculousness_Landscape.png
            for image in images:
                if image["width"] > 500:
                    pass  # no fanart here
                else:
                    item.thumb = "http://playplex.mtvnimages.com/uri/%(url)s" % image

        date = result_set.get("originalAirDate", None)
        if not date:
            date = result_set.get("originalPublishDate", None)
        if date:
            time_stamp = date["timestamp"]
            date_time = DateHelper.get_date_from_posix(time_stamp)
            item.set_date(date_time.year, date_time.month, date_time.day, date_time.hour,
                          date_time.minute,
                          date_time.second)

        return item

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

        # add  { to make it valid Json again. if it would be in the regex it would
        # not find all items
        # data = JsonHelper("{%s" % (result_set,))

        # title
        local_title = result_set.get("local_title")
        original_title = result_set.get("original_name")
        if local_title == "" or local_title is None:
            title = original_title
        elif original_title != local_title:
            title = "%s (%s)" % (local_title, original_title)
        else:
            title = local_title

        # the URL
        serie_id = result_set["id"]
        url = "%sepisodes.json?per=2147483647&franchise_id=%s" % (self.mainListUri[0:43], serie_id)

        item = MediaItem(title, url)
        item.complete = True

        # thumbs
        if "image" in result_set and result_set["image"] is not None:
            # noinspection PyTypeChecker
            thumb = result_set["image"]["riptide_image_id"]
            thumb = "http://images.mtvnn.com/%s/original" % (thumb,)
            item.thumb = thumb

        # others
        item.description = result_set["local_long_description"]
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
        original_title = result_set.get("original_title")
        local_title = result_set.get("local_title")
        # Logger.Trace("%s - %s", originalTitle, localTitle)
        if original_title == "":
            title = local_title
        else:
            title = original_title

        # get the other meta data
        play_lists = result_set.get("local_playlists", [])
        video_mgid = None
        for play_list in play_lists:
            language = play_list["language_code"]
            if language == self.language:
                Logger.trace("Found '%s' playlist, using this one.", language)
                video_mgid = play_list["id"]
                break
            elif language == "en":
                Logger.trace("Found '%s' instead of '%s' playlist", language, self.language)
                video_mgid = play_list["id"]

        if video_mgid is None:
            Logger.error("No video MGID found for: %s", title)
            return None

        url = "http://api.mtvnn.com/v2/mrss.xml?uri=mgid:sensei:video:mtvnn.com:local_playlist-%s" % (video_mgid,)

        thumb = result_set.get("riptide_image_id")
        thumb = "http://images.mtvnn.com/%s/original" % (thumb,)

        description = result_set.get("local_long_description")

        date = result_set.get("published_from")
        date = date[0:10].split("-")

        item = MediaItem(title, url)
        item.thumb = thumb
        item.description = description
        item.type = 'video'
        item.set_date(date[0], date[1], date[2])
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

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        url = item.url
        data = UriHandler.open(url, proxy=self.proxy)

        renditions_url = Regexer.do_regex(r'<media:content[^>]+url=\W([^\'"]+)\W', data)[0]
        renditions_url = HtmlEntityHelper.strip_amp(renditions_url)
        rendition_data = UriHandler.open(renditions_url, proxy=self.proxy)
        video_items = Regexer.do_regex(r'<rendition[^>]+bitrate="(\d+)"[^>]*>\W+<src>([^<]+)<',
                                       rendition_data)

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()
        for video_item in video_items:
            media_url = self.get_verifiable_video_url(video_item[1].replace("rtmpe", "rtmp"))
            part.append_media_stream(media_url, video_item[0])

        item.complete = True
        return item
