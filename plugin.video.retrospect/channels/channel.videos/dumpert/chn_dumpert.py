# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.streams.youtube import YouTube


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
        self._add_data_parser("*", json=True,
                              parser=["items"], creator=self.create_json_video_item)

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
        url_pattern = "https://api-live.dumpert.nl/mobile_api/json/video/%s/%s/"

        for page in range(0, 2):
            item = MediaItem("Toppertjes - Pagina %s" % (page + 1, ), url_pattern % ('toppers', page))
            items.append(item)

        for page in range(0, 10):
            item = MediaItem("Filmpjes - Pagina %s" % (page + 1, ), url_pattern % ('latest', page))
            items.append(item)

        item = MediaItem("Zoeken", "searchSite")
        items.append(item)

        return data, items

    def create_json_video_item(self, result_set):  # NOSONAR
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

        item = MediaItem(result_set["title"], "")
        item.type = "video"
        item.thumb = result_set["still"]
        item.description = result_set["description"]

        if "date" in result_set:
            # date=2019-10-02T08:30:13+02:00
            date_text = result_set["date"]
            date_tuple = date_text.split("T")[0].split("-")
            item.set_date(*[int(i) for i in date_tuple])

        if "media" in result_set and result_set["media"]:
            part = item.create_new_empty_media_part()
            for video_info in result_set["media"]:
                if video_info["mediatype"] == "FOTO":
                    Logger.trace("Ignoring foto: %s", item)
                    return None

                for info in video_info["variants"]:
                    video_type = info["version"]
                    uri = info["uri"]

                    if video_type == "flv":
                        part.append_media_stream(uri, 1000)
                    elif video_type == "720p":
                        part.append_media_stream(uri, 1200)
                    elif video_type == "1080p" or video_type == "original":
                        part.append_media_stream(uri, 1600)
                    elif video_type == "tablet":
                        part.append_media_stream(uri, 800)
                    elif video_type == "mobile":
                        part.append_media_stream(uri, 450)
                    elif video_type == "embed" and uri.startswith("youtube"):
                        embed_type, youtube_id = uri.split(":")
                        url = "https://www.youtube.com/watch?v=%s" % (youtube_id, )
                        for s, b in YouTube.get_streams_from_you_tube(url, self.proxy):
                            item.complete = True
                            part.append_media_stream(s, b)
                    else:
                        Logger.warning("Video type '%s' was not used", video_type)
            item.complete = True
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

        url = "https://api-live.dumpert.nl/mobile_api/json/search/%s/0/"
        return chn_class.Channel.search_site(self, url)

    def __ignore_cookie_law(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.dumpert.nl")

        # Set-Cookie: cpc=10; path=/; domain=www.dumpert.nl; expires=Thu, 11-Jun-2020 18:49:38 GMT
        UriHandler.set_cookie(name='cpc', value='10', domain='.www.dumpert.nl')
        UriHandler.set_cookie(name='cpc', value='10', domain='.legacy.dumpert.nl')
        return
