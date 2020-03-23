# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper


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
        self.noImage = "eenimage.png"

        # setup the urls
        self.mainListUri = "https://www.een.be/programmas"
        self.baseUrl = "http://www.een.be"

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, preprocessor=self.extract_json, json=True,
                              parser=["data", ], creator=self.create_show_item)

        video_parser = r'<a class="card-teaser"[^>][^>]*href="(?<url>[^"]+)"[^>]*>\W+<div[^>]+' \
                       r'style="background-image: url\(\'(?<thumburl>[^\']+/(?<year>\d{4})/' \
                       r'(?<month>\d{2})/(?<day>\d{2})/[^\']+)\'[^>]*>\W+<div[^>]+_play[\w\W+]' \
                       r'{0,2000}?<div[^>]*>(?<_title>[^>]*)</div>\W*<h3[^>]*>(?<title>[^<]+)' \
                       r'</h3>\W+<div[^>]*>\W+(?:<span[^>]*>[^<]*</span>)?(?<description>[^<]+)'
        video_parser = Regexer.from_expresso(video_parser)
        self._add_data_parser("*", name="Links to teasers of videos (Card teaser)",
                              parser=video_parser, creator=self.create_video_item,
                              updater=self.update_video_item)

        video_parser = r'<a[^>]*class="[^"]+-teaser"[^>]*background-image: url\(\'(?<thumburl>' \
                       r'[^\']+/(?<year>\d{4})/(?<month>\d{2})/(?<day>\d{2})/[^\']+)\'[^>]*href="' \
                       r'(?<url>[^"]+)"[^>]*>\W+<div[^>]+_play[\w\W+]{0,2000}?<div[^>]*>' \
                       r'(?<_title>[^>]*)</div>\W*<h3[^>]*>(?<title>[^<]+)</h3>\W+<div[^>]*>\W+' \
                       r'(?:<span[^>]*>[^<]*</span>)?(?<description>[^<]+)'
        video_parser = Regexer.from_expresso(video_parser)
        self._add_data_parser("*", name="Links to teasers of videos (Image Teaser)",
                              parser=video_parser, creator=self.create_video_item,
                              updater=self.update_video_item)

        single_video_parser = r'>(?<title>[^<]+)</h1>[\w\W]{0,2000}?(?:<h2>?<description>[^<]+)?' \
                              r'[\w\W]{0,1000}?data-video="(?<url>[^"]+)"[\w\W]{0,500}data-analytics' \
                              r'=\'{&quot;date&quot;:&quot;(?<year>\d+)-(?<month>\d+)-(?<day>\d+)'
        single_video_parser = Regexer.from_expresso(single_video_parser)
        self._add_data_parser("*", name="Pages that contain only a single video",
                              parser=single_video_parser, creator=self.create_video_item)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def extract_json(self, data):
        """ Extracts JSON data from pages

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        recent = MediaItem("\a .: Recent :.", "https://www.een.be/deze-week")
        recent.type = "folder"
        recent.complete = True
        recent.dontGroup = True
        items.append(recent)

        data = Regexer.do_regex(r'epgAZ\W+({"data"[\w\W]+?);<', data)[0]
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

        if not result_set["url"].startswith("http"):
            result_set["url"] = "https://mediazone.vrt.be/api/v1/een/assets/%(url)s" % result_set

        item = chn_class.Channel.create_video_item(self, result_set)
        if "year" in result_set and result_set["year"]:
            item.set_date(result_set["year"], result_set["month"], result_set["day"])
        return item

    def create_show_item(self, result_set):
        """ Creates a MediaItem of type 'folder' for a show using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        exclude = {
            11: "Dagelijkse Kost",
            388: "Het journaal",
            400: "Karakters",
            413: "Het weer"
        }
        if result_set["id"] in exclude.keys():
            return None

        # # dummy class
        # url = "http://www.een.be/mediatheek/tag/%s"
        item = MediaItem(result_set["title"], result_set["url"])
        item.type = "folder"
        item.complete = True

        if "image" in result_set and "data" in result_set["image"]:
            # noinspection PyTypeChecker
            item.thumb = result_set["image"]["data"]["url"]
            # noinspection PyTypeChecker
            item.fanart = result_set["image"]["data"]["url"]
        return item

    def update_video_item(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        # rtmpt://vrt.flash.streampower.be/een//2011/07/1000_110723_getipt_neefs_wiels_Website_EEN.flv
        # http://www.een.be/sites/een.be/modules/custom/vrt_video/player/player_4.3.swf

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.open(item.url, proxy=self.proxy)

        part = item.create_new_empty_media_part()
        if "mediazone.vrt.be" not in item.url:
            # Extract actual media data
            video_id = Regexer.do_regex('data-video=[\'"]([^"\']+)[\'"]', data)[0]
            url = "https://mediazone.vrt.be/api/v1/een/assets/%s" % (video_id, )
            data = UriHandler.open(url, proxy=self.proxy)

        json = JsonHelper(data)
        urls = json.get_value("targetUrls")

        for url_info in urls:
            Logger.trace(url_info)
            if url_info["type"].lower() != "hls":
                continue

            hls_url = url_info["url"]
            for s, b in M3u8.get_streams_from_m3u8(hls_url, self.proxy):
                part.append_media_stream(s, b)

        item.complete = True
        return item
