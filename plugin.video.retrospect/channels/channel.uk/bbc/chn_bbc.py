# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.xmlhelper import XmlHelper
from resources.lib.helpers import subtitlehelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.streams.f4m import F4m
from resources.lib.logger import Logger
from resources.lib.parserdata import ParserData
from resources.lib.regexer import Regexer
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.mpd import Mpd
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.liveUrl = None

        # setup the urls
        self.baseUrl = "http://www.bbc.co.uk"
        self.swfUrl = "http://emp.bbci.co.uk/emp/SMPf/1.13.13/StandardMediaPlayerChromelessFlash.swf"

        self.noImage = "bbciplayerimage.png"
        self.mainListUri = "#mainlisting"

        # setup the main parsing data
        self.episodeItemRegex = '<a class="letter stat" href="(?<url>/iplayer/a-z/[^"]+)">(?<title>[^<]+)</a>'\
                                .replace("(?<", "(?P<")
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              preprocessor=self.add_live_channels_and_folders)

        # A-Z listing
        self._add_data_parser("#alphalisting", preprocessor=self.alpha_listing)
        self._add_data_parser("https://www.bbc.co.uk/iplayer/a-z/",
                              preprocessor=self.extract_json, json=True,
                              parser=["programmes"], creator=self.create_show_items)

        # Video item listing
        self._add_data_parser("*", preprocessor=self.redirect_to_main_show)
        # self._add_data_parser("*", json=True,
        #                       name="Parsing of the main video item of the listing.",
        #                       parser=[], creator=self.create_video_item)
        self._add_data_parser("*", json=True,
                              name="Parsing of the related video items.",
                              parser=["entities"], creator=self.create_video_item)

        # Standard items
        # self._add_data_parser("*", preprocessor=self.pre_process_folder_list)
        # self.folderItemRegex = r'<a href="(?<url>/iplayer/brand/[^"]+)"[^>]*>\W+<i[^>]+></i>\W+' \
        #                        r'<span[^>]+>(?<title>[^<]+)<'.replace("(?<", "(?P<")
        # self._add_data_parser("*", parser=self.folderItemRegex, creator=self.create_folder_item)
        # self.videoItemRegex = r'<a\W+href="/iplayer/episode/(?<url>[^/]+)[^>]+>\W+<div[^>]+>[^>]+' \
        #                       r'</div>\W+(?:<div[^>]+>[^>]+</div>\W+)?[\w\W]{0,500}?<source ' \
        #                       r'srcset="(?<thumburl>[^"]+)"[\w\W]{0,500}?<div class="secondary">' \
        #                       r'\W+<div[^>]+>(?<title>[^<]+)</div>\W+(?:<div[^>]+>(?<subtitle>' \
        #                       r'[^<]+)</div>\W+)?<p[^>]*>(?<description>[^<]*)</p>[\w\W]{0,1000}?' \
        #                       r'(?:<span class="release">\W+First shown: (?<day>\d+) (?<month>\w+) ' \
        #                       r'(?<year>\d+)|<div class="period")'
        # self.videoItemRegex = Regexer.from_expresso(self.videoItemRegex)
        # self._add_data_parser("*", parser=self.videoItemRegex, creator=self.create_video_item)

        # Live channels
        self._add_data_parser("http://vs-hds-uk-live.edgesuite.net/",
                              updater=self.update_live_item)
        self._add_data_parser("http://a.files.bbci.co.uk/media/live/manifesto/",
                              updater=self.update_live_item)

        # Generic updater
        self._add_data_parser("*", updater=self.update_video_item)

        # ===============================================================================================================
        # non standard items
        # if self.proxy:
        #     self.proxy.Filter = ["mediaselector"]

        self.searchUrl = "http://feeds.bbc.co.uk/iplayer/search/tv/?q=%s"
        self.programs = dict()

        # ===============================================================================================================
        # Test cases:
        # http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/pc/vpid/b04plqyv/atk/

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_episode_item(self, result_set, append_subtitle=True):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex
        :param bool append_subtitle:               Should we append a subtitle?

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        url = result_set['href']
        if not url.startswith("http"):
            url = "{}{}".format(self.baseUrl, url)

        title = result_set["title"]
        if title is None:
            title = self.parentItem.name
        elif append_subtitle and "subtitle" in result_set:
            title = "{} - {}".format(title, result_set["subtitle"])

        item = MediaItem(title, url)
        item.description = result_set.get('synopsis', item.description)

        image_template = result_set.get("imageTemplate")
        item.fanart = image_template.replace("{recipe}", "1920x1080")
        item.thumb = image_template.replace("{recipe}", "608x342")
        return item

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

        if "episode.json" in self.parentItem.url:
            Logger.debug("Fetching Carousel data")
            json = JsonHelper(data)
            data = json.get_value("carousel")

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_folder_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        item = chn_class.Channel.create_folder_item(self, result_set)
        brand = item.url[item.url.rindex("/") + 1:]

        # to match the first video regex: item.url = "http://www.bbc.co.uk/programmes/%s/episodes/player" % (brand, )
        item.url = "http://www.bbc.co.uk/iplayer/episodes/%s" % (brand,)
        item.isGeoLocked = True
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

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        item = self.create_episode_item(result_set["props"], append_subtitle=False)
        item.type = "video"
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

        data = UriHandler.open(item.url, proxy=self.proxy)
        json_data, _ = self.extract_json(data)
        video_id = json_data.get_value("versions", 0, "id")
        stream_data_url = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/{}".format(video_id)

        # this URL is one from the webbrowser but requires a security part. So NOT:
        # streamDataUrl = "http://open.live.bbc.co.uk/mediaselector/5/select/version
        # /2.0/mediaset/pc/vpid/%s" % (vid,)
        #
        # but:
        # streamDataUrl = "http://open.live.bbc.co.uk/mediaselector/5/select/version
        # /2.0/mediaset/pc/vpid/%s/atk/2214e42b5729dcdd012dfb61a3054d39309ccd31/asn/1/
        # And I don't know where that one comes from

        part = item.create_new_empty_media_part()

        stream_data = UriHandler.open(stream_data_url, proxy=self.proxy)
        # Reroute for debugging
        # from debug.router import Router
        # streamData = Router.get_via("uk", streamDataUrl, self.proxy)

        connection_datas = Regexer.do_regex(
            r'<media bitrate="(\d+)"[^>]+>\W*'
            r'(<connection[^>]+>\W*)'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?</media>', stream_data)

        for connection_data in connection_datas:
            # first the bitrate
            bitrate = int(connection_data[0])
            Logger.trace("Found Media: %s", connection_data)

            # go through the available connections
            for connection in connection_data[1:]:
                if not connection:
                    continue

                connection_xml = XmlHelper(connection)
                stream_bitrate = bitrate
                Logger.trace("Analyzing Connection: %s", connection)
                supplier = connection_xml.get_tag_attribute("connection", {"supplier": None})
                protocol = connection_xml.get_tag_attribute("connection", {"protocol": None})
                transfer_format = connection_xml.get_tag_attribute("connection", {"transferFormat": None})
                Logger.debug("Found connection information:\n"
                             "Protocol:       %s\n"
                             "TransferFormat: %s\n"
                             "Supplier:       %s\n"
                             "Bitrate:        %s",
                             protocol, transfer_format, supplier, bitrate)

                if protocol.startswith("http"):
                    if transfer_format != "hls":  # and transfer_format != "dash":
                        Logger.debug("Ignoring TransferFormat: %s", transfer_format)
                        continue
                    if "lime" in supplier or "mf_akamai_uk" in supplier:
                        # Prefer others
                        stream_bitrate -= 1
                        # Logger.debug("Ignoring Supplier: %s", supplier)
                        # continue
                    url = connection_xml.get_tag_attribute("connection", {"href": None})

                elif protocol.startswith("rtmp"):
                    Logger.warning("Ignoring RTMP for now")
                    continue
                else:
                    Logger.warning("Unknown protocol: %s", protocol)
                    continue

                if transfer_format == "hls":
                    item.complete = M3u8.update_part_with_m3u8_streams(part, url, proxy=self.proxy, bitrate=stream_bitrate)
                elif transfer_format == "dash":
                    strm = part.append_media_stream(url, bitrate)
                    Mpd.set_input_stream_addon_input(strm, self.proxy)

        # get the subtitle
        subtitles = Regexer.do_regex(
            '<connection href="(http://www.bbc.co.uk/iplayer/subtitles/[^"]+/)([^/]+.xml)"',
            stream_data)
        if len(subtitles) > 0:
            subtitle = subtitles[0]
            subtitle_url = "%s%s" % (subtitle[0], subtitle[1])
            part.Subtitle = subtitlehelper.SubtitleHelper.download_subtitle(
                subtitle_url, subtitle[1], "ttml", proxy=self.proxy)

        item.complete = True
        Logger.trace('finishing update_video_item: %s.', item)
        return item

    def add_live_channels_and_folders(self, data):
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

        Logger.info("Generating Live channels")
        items = []

        live_channels = [
            {"name": "BBC 1 HD", "code": "bbc_one_hd", "image": "bbc1large.png"},
            {"name": "BBC 2 HD", "code": "bbc_two_hd", "image": "bbc2large.png"},
            {"name": "BBC 3 HD", "code": "bbc_three_hd", "image": "bbc3large.png"},
            {"name": "BBC 4 HD", "code": "bbc_four_hd", "image": "bbc4large.png"},
            {"name": "CBBC", "code": "cbbc_hd", "image": "cbbclarge.png"},
            {"name": "CBeebies", "code": "cbeebies_hd", "image": "cbeebieslarge.png"},
            {"name": "BBC News Channel", "code": "bbc_news24", "image": "bbcnewslarge.png"},
            {"name": "BBC Parliament", "code": "bbc_parliament", "image": "bbcparliamentlarge.png"},
            {"name": "Alba", "code": "bbc_alba", "image": "bbcalbalarge.png"},

            {"name": "S4C", "code": "s4cpbs", "image": "bbchdlarge.png"},
            {"name": "BBC One London", "code": "bbc_one_london", "image": "bbchdlarge.png"},
            {"name": "BBC One Scotland", "code": "bbc_one_scotland_hd", "image": "bbchdlarge.png"},
            {"name": "BBC One Northern Ireland", "code": "bbc_one_northern_ireland_hd", "image": "bbchdlarge.png"},
            {"name": "BBC One Wales", "code": "bbc_one_wales_hd", "image": "bbchdlarge.png"},
            {"name": "BBC Two Scotland", "code": "bbc_two_scotland", "image": "bbchdlarge.png"},
            {"name": "BBC Two Northern Ireland", "code": "bbc_two_northern_ireland_digital", "image": "bbchdlarge.png"},
            {"name": "BBC Two Wales", "code": "bbc_two_wales_digital", "image": "bbchdlarge.png"},
        ]

        live = MediaItem("Live Channels", "")
        live.dontGroup = True
        live.type = "folder"
        items.append(live)

        for channel in live_channels:
            url = "http://a.files.bbci.co.uk/media/live/manifesto/audio_video/simulcast/hds/uk/pc/ak/%(code)s.f4m" % channel
            item = MediaItem(channel["name"], url)
            item.isGeoLocked = True
            item.isLive = True
            item.type = "video"
            item.complete = False
            item.thumb = self.get_image_location(channel["image"])
            live.items.append(item)

        extra = MediaItem("Shows (A-Z)", "#alphalisting")
        extra.complete = True
        extra.description = "Alphabetical show listing of BBC shows"
        extra.dontGroup = True
        items.append(extra)

        return data, items

    def alpha_listing(self, data):
        """ Creates a alpha listing with items pointing to the alpha listing on line.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Generating an Alpha list for BBC")

        items = []
        # https://www.bbc.co.uk/iplayer/a-z/a

        title_format = LanguageHelper.get_localized_string(LanguageHelper.StartWith)
        url_format = "https://www.bbc.co.uk/iplayer/a-z/%s"
        for char in "abcdefghijklmnopqrstuvwxyz0":
            if char == "0":
                char = "0-9"
            sub_item = MediaItem(title_format % (char.upper(),), url_format % (char,))
            sub_item.complete = True
            sub_item.dontGroup = True
            sub_item.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
            items.append(sub_item)
        return data, items

    def redirect_to_main_show(self, data):
        """ Determines the actual URL of a show and fetches it's videos

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[JsonHelper,list[MediaItem]]

        """

        json_data, items = self.extract_json(data)

        # 325	200	HTTPS	www.bbc.co.uk	/iplayer/episode/b0404c5j/absolute-genius-with-dick-and-dom-series-2-10-talbot	65.993	no-store, must-revalidate, max-age=0	text/html; charset=utf-8	kodi:14240
        # 326	200	HTTP	Tunnel to	www.bbc.co.uk:443	914			kodi:14240
        # 327	301	HTTPS	www.bbc.co.uk	/iplayer/episodes/b03srr0b	94	no-store, must-revalidate, max-age=0	text/plain; charset=utf-8	kodi:14240
        # 328	200	HTTPS	www.bbc.co.uk	/iplayer/episodes/b03srr0b/absolute-genius-with-dick-and-dom	60.571	no-store, must-revalidate, max-age=0	text/html; charset=utf-8	kodi:14240
        show_id = json_data.get_value("episode", "tleoId")
        url = "{}/iplayer/episodes/{}".format(self.baseUrl, show_id)
        data = UriHandler.open(url, proxy=self.proxy)
        json_data, items = self.extract_json(data)
        return json_data, items

    def extract_json(self, data):
        """ Extracts the JSON datda from a main list.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[JsonHelper,list[MediaItem]]

        """

        items = []
        json_regex = r'window.__IPLAYER_REDUX_STATE__ = (.*?);\s*</script>'
        json_data = Regexer.do_regex(json_regex, data)
        return JsonHelper(json_data[0]), items

    def create_show_items(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict[str,dict]] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        items = []
        for char, data in result_set.items():
            shows = data.get("entities")
            if not shows:
                continue

            for item_data in shows:
                item = self.create_episode_item(item_data["props"])
                if items is not None:
                    items.append(item)

        return items or None

    def update_live_item(self, item):
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

        Logger.debug('Starting update_live_item for %s (%s)', item.name, self.channelName)
        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=self.httpHeaders)
        stream_root = Regexer.do_regex(r'<media href="([^"]+\.isml)', data)[0]
        Logger.debug("Found Live stream root: %s", stream_root)

        part = item.create_new_empty_media_part()
        for s, b in F4m.get_streams_from_f4m(item.url, self.proxy):
            item.complete = True
            s = s.replace(".f4m", ".m3u8")
            part.append_media_stream(s, b)

        return item

    def __get_date(self, date):
        # actual_start=2014-12-07T10:03:56+0000
        date_part, time_part = date.split("T")
        year, month, day = date_part.split("-")
        hour, minute, ignore = time_part.split(":")
        # Logger.Trace((year, month, day, hour, minute, 0))
        return year, month, day, hour, minute, 0
