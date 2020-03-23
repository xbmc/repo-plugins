# SPDX-License-Identifier: CC-BY-NC-SA-4.0
from resources.lib import chn_class


from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.regexer import Regexer
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData
from resources.lib.addonsettings import AddonSettings
from resources.lib.streams.m3u8 import M3u8


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        # The following data was taken from http://playapi.mtgx.tv/v3/channels
        self.channelIds = None
        self.mainListUri = None

        # The LV channels
        if self.channelCode == "tv3lv":
            self.noImage = "tv3lvimage.png"
            self.mainListUri = "https://tvplay.skaties.lv/seriali/"
            self.channelIds = (
                1482,  # TV3
                6400,  # LNT
                6401,  # TV6
                6402,  # TV5
                6403,  # Kanals2
                6404,  # TVPlay
                6405   # 3+
            )

        # EE channels
        elif self.channelCode == "tv3ee":
            self.mainListUri = "https://tvplay.tv3.ee/saated/tv3/"
            self.noImage = "tv3noimage.png"
            self.channelId = (1375, 6301, 6302)

        elif self.channelCode == "tv6ee":
            self.mainListUri = "https://tvplay.tv3.ee/saated/tv6/"
            self.noImage = "tv6seimage.png"
            self.channelId = (6300, )

        # Lithuanian channels
        elif self.channelCode == "tv3lt":
            self.mainListUri = "https://tvplay.tv3.lt/pramogines-laidos/tv3/"
            self.noImage = "tv3ltimage.png"
            self.channelId = (3000, 6503)

        elif self.channelCode == "tv6lt":
            self.mainListUri = "https://tvplay.tv3.lt/pramogines-laidos/tv6/"
            self.noImage = "tv6ltimage.png"
            self.channelId = (6501, )

        elif self.channelCode == "tv8lt":
            self.mainListUri = "https://tvplay.tv3.lt/pramogines-laidos/tv8/"
            self.noImage = "tv8seimage.png"
            self.channelId = (6502, )

        else:
            raise ValueError("Unknown channelcode {0}".format(self.channelCode))

        self.episodeItemRegex = r'<a[^>*]+href="(?<url>[^"]+)"[^>]*>\W+<img[^>]+data-srcset="[^"]*' \
                                r'(?<thumburl>http[^" ]+)[^"]+"[^>]+alt="(?<title>[^"]+)"'
        self.videoItemRegex = r'{0}[\w\W]{{0,1000}}?site-thumb-info[^>]+>(?<description>[^<]+)'. \
            format(self.episodeItemRegex)

        self.folderItemRegex = r'<option value="(?<url>[^"]+)"\W*>(?<title>[^<]+)</option>'

        self.episodeItemRegex = Regexer.from_expresso(self.episodeItemRegex)
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              preprocessor=self.add_search,
                              parser=self.episodeItemRegex, creator=self.create_episode_item)

        self.videoItemRegex = Regexer.from_expresso(self.videoItemRegex)
        self._add_data_parser("*", preprocessor=self.remove_clips,
                              parser=self.videoItemRegex, creator=self.create_video_item)

        self.folderItemRegex = Regexer.from_expresso(self.folderItemRegex)
        self._add_data_parser("*", parser=self.folderItemRegex, creator=self.create_folder_item)

        # Add an updater
        self._add_data_parser("*", updater=self.update_video_item)

        self.baseUrl = "{0}//{2}".format(*self.mainListUri.split("/", 3))
        self.searchInfo = {
            "se": ["sok", "S&ouml;k"],
            "ee": ["otsi", "Otsi"],
            "dk": ["sog", "S&oslash;g"],
            "no": ["sok", "S&oslash;k"],
            "lt": ["paieska", "Paie&scaron;ka"],
            "lv": ["meklet", "Mekl&#275;t"]
        }

    def remove_clips(self, data):
        """ Remove clip information from the data.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        clip_start = data.find('<div class="secondary-content">')
        if clip_start > 0:
            data = data[:clip_start]
        return data, []

    def add_search(self, data):
        """ Add a "search" item to the listing.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        title = "\a.: %s :." % (self.searchInfo.get(self.language, self.searchInfo["se"])[1], )
        Logger.trace("Adding search item: %s", title)
        search_item = MediaItem(title, "searchSite")
        search_item.dontGroup = True
        items.append(search_item)

        Logger.debug("Pre-Processing finished")
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

        item = self.create_episode_item(result_set)
        if item is None:
            return None

        alt_name = result_set["description"]
        item.name = "{0} - {1}".format(item.name, alt_name)
        item.description = alt_name
        item.type = "video"
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

        headers = {}
        if self.localIP:
            headers.update(self.localIP)

        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=headers)
        m3u8_url = Regexer.do_regex('data-file="([^"]+)"', data)[0]

        part = item.create_new_empty_media_part()
        if AddonSettings.use_adaptive_stream_add_on(with_encryption=False):
            stream = part.append_media_stream(m3u8_url, 0)
            M3u8.set_input_stream_addon_input(stream, proxy=self.proxy, headers=headers)
            item.complete = True
        else:
            for s, b, a in M3u8.get_streams_from_m3u8(m3u8_url, self.proxy,
                                                      headers=headers, map_audio=True):

                if a and "-audio" not in s:
                    video_part = s.rsplit("-", 1)[-1]
                    video_part = "-%s" % (video_part,)
                    s = a.replace(".m3u8", video_part)
                part.append_media_stream(s, b)
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

        # https://tvplay.tv3.lt/paieska/Lietuvos%20talentai%20/
        # https://tvplay.tv3.ee/otsi/test%20test%20/
        url = self.__get_search_url()
        url = "{0}/%s/".format(url)
        return chn_class.Channel.search_site(self, url)

    def __get_search_url(self):
        """ Generates a search url for the channel using the information for that channel.

        :return: a search url.
        :rtype: str

        """

        search_info = self.searchInfo.get(self.language, None)
        if search_info is None:
            search_info = self.searchInfo["se"]
        return "%s/%s" % (self.baseUrl, search_info[0])
