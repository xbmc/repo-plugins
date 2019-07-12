import chn_class

from mediaitem import MediaItem
from helpers import datehelper
from regexer import Regexer
from logger import Logger
from urihandler import UriHandler
from xbmcwrapper import XbmcWrapper
from helpers.encodinghelper import EncodingHelper
from helpers.jsonhelper import JsonHelper
from streams.youtube import YouTube


class Channel(chn_class.Channel):

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # === Actual channel setup STARTS here and should be overwritten from derived classes ======
        self.noImage = "dumpertimage.png"

        # setup the urls
        self.baseUrl = "http://www.dumpert.nl/mediabase/flv/%s_YTDL_1.flv.flv"

        # setup the main parsing data
        self.mainListUri = "#mainlist"
        self._add_data_parser(self.mainListUri, preprocessor=self.get_main_list_items)
        self.videoItemRegex = r'<a[^>]+href="([^"]+)"[^>]*>\W+<img src="([^"]+)[\W\w]{0,400}' \
                              r'<h\d>([^<]+)</h\d>\W+<[^>]*date"{0,1}>(\d+) (\w+) (\d+) (\d+):(\d+)'
        self._add_data_parser("*",
                              parser=self.videoItemRegex, creator=self.create_video_item,
                              updater=self.update_video_item)

        # ============================ Actual channel setup STOPS here =============================
        self.__ignore_cookie_law()
        return

    def get_main_list_items(self, data):
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
        url_pattern = "http://www.dumpert.nl/%s/%s/"

        for page in range(1, 3):
            item = MediaItem("Toppertjes - Pagina %s" % (page, ), url_pattern % ('toppers', page))
            item.icon = self.icon
            items.append(item)

        for page in range(1, 11):
            item = MediaItem("Filmpjes - Pagina %s" % (page, ), url_pattern % ('filmpjes', page))
            item.icon = self.icon
            items.append(item)

        item = MediaItem("Zoeken", "searchSite")
        item.icon = self.icon
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

        #                         0              1             2                             3
        #<a class="item" href="([^"]+)"[^=]+="([^"]+)" alt="([^"]+)[^:]+<div class="date">([^<]+)

        item = MediaItem(result_set[2], result_set[0], type='video')
        item.icon = self.icon
        item.description = result_set[2]
        item.thumb = result_set[1]

        try:
            month = datehelper.DateHelper.get_month_from_name(result_set[4], "nl")
            item.set_date(result_set[5], month, result_set[3], result_set[6], result_set[7], 0)
        except:
            Logger.error("Error matching month: %s", result_set[4].lower(), exc_info=True)

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

        data = UriHandler.open(item.url, proxy=self.proxy)
        item.MediaItemParts = []
        part = item.create_new_empty_media_part()

        base_encode = Regexer.do_regex('data-files="([^"]+)', data)
        if base_encode:
            Logger.debug("Loading video from BASE64 encoded JSON data")
            base_encode = base_encode[-1]
            json_data = EncodingHelper.decode_base64(base_encode)
            json = JsonHelper(json_data, logger=Logger.instance())
            Logger.trace(json)

            # "flv": "http://media.dumpert.nl/flv/e2a926ff_10307954_804223649588516_151552487_n.mp4.flv",
            # "tablet": "http://media.dumpert.nl/tablet/e2a926ff_10307954_804223649588516_151552487_n.mp4.mp4",
            # "mobile": "http://media.dumpert.nl/mobile/e2a926ff_10307954_804223649588516_151552487_n.mp4.mp4",

            streams = json.get_value()
            for key in streams:
                if key == "flv":
                    part.append_media_stream(streams[key], 1000)
                elif key == "720p":
                    part.append_media_stream(streams[key], 1200)
                elif key == "1080p":
                    part.append_media_stream(streams[key], 1600)
                elif key == "tablet":
                    part.append_media_stream(streams[key], 800)
                elif key == "mobile":
                    part.append_media_stream(streams[key], 450)
                elif key == "embed" and streams[key].startswith("youtube"):
                    embed_type, youtube_id = streams[key].split(":")
                    url = "https://www.youtube.com/watch?v=%s" % (youtube_id, )
                    for s, b in YouTube.get_streams_from_you_tube(url, self.proxy):
                        item.complete = True
                        part.append_media_stream(s, b)
                else:
                    Logger.debug("Key '%s' was not used", key)
            item.complete = True
            Logger.trace("VideoItem updated: %s", item)
            return item

        youtube_id = Regexer.do_regex("class='yt-iframe'[^>]+src='https://www.youtube.com/embed/([^?]+)", data)
        if youtube_id:
            youtube_id = youtube_id[-1]
            url = "https://www.youtube.com/watch?v=%s" % (youtube_id,)
            for s, b in YouTube.get_streams_from_you_tube(url, self.proxy):
                item.complete = True
                part.append_media_stream(s, b)
        return item

    def search_site(self, url=None):
        """ Creates an list of items by searching the site.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with an URL encoded representation of the
        text to search for.

        :param str|None url:     Url to use to search with a %s for the search parameters.

        :return: A list with search results as MediaItems.
        :rtype: list[MediaItem]

        """

        items = []

        needle = XbmcWrapper.show_key_board()
        if needle:
            #convert to HTML
            needle = needle.replace(" ", "%20")
            search_url = "http://www.dumpert.nl/search/V/%s/ " % (needle, )
            temp = MediaItem("Search", search_url)
            return self.process_folder_list(temp)

        return items

    def __ignore_cookie_law(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.dumpert.nl")

        # Set-Cookie: cpc=10; path=/; domain=www.dumpert.nl; expires=Thu, 11-Jun-2020 18:49:38 GMT
        UriHandler.set_cookie(name='cpc', value='10', domain='.www.dumpert.nl')
        return
