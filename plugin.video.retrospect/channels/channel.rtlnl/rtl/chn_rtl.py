# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import datetime

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.streams.m3u8 import M3u8
from resources.lib.parserdata import ParserData
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.xbmcwrapper import XbmcWrapper


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "rtlimage.png"

        # setup the urls
        self.mainListUri = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/fun=az/fmt=smooth"
        self.mainListUri = "https://xlapi.rtl.nl/version=1/fun=az/model=svod/"
        self.baseUrl = "http://www.rtl.nl"

        # setup the main parsing data
        self.episodeItemJson = ["abstracts", ]
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.add_live_streams_and_recent,
                              parser=self.episodeItemJson, creator=self.create_episode_item)

        self._add_data_parser("https://xlapi.rtl.nl/version=1/fun=gemist/model=svod/bcdate=",
                              json=True,
                              parser=["material", ], creator=self.create_recent_video_item)

        self._add_data_parser("https://search.rtl.nl/?typeRestriction=tvabstract", json=True,
                              name="Search JSON matching shows",
                              parser=["Abstracts", ], creator=self.create_search_program_item)
        self._add_data_parser("https://search.rtl.nl/?typeRestriction=videoobject", json=True,
                              name="Search JSON matching videos",
                              parser=["Videos", ], creator=self.create_search_program_item)

        self.videoItemJson = ["material", ]
        self.folderItemJson = ["seasons", ]
        self._add_data_parser("*", preprocessor=self.pre_process_folder_list)
        self._add_data_parser("*", json=True,
                              parser=self.videoItemJson, creator=self.create_video_item, updater=self.update_video_item)
        self._add_data_parser("*", parser=self.folderItemJson, creator=self.create_folder_item, json=True)

        #===============================================================================================================
        # non standard items
        self.largeIconSet = dict()

        for channel in ["rtl4", "rtl5", "rtl7", "rtl8"]:
            self.largeIconSet[channel] = self.get_image_location("%slarge.png" % (channel,))

        self.__ignore_cookie_law()

        # setup some props for later use
        self.currentJson = None
        self.abstracts = None
        self.episodes = None
        self.posterBase = None
        self.thumbBase = None

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def add_live_streams_and_recent(self, data):
        """ Adds the live streams for RTL-Z.

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

        # let's add the RTL-Z live stream
        rtlz_live = MediaItem("RTL Z Live Stream", "")
        rtlz_live.complete = True
        rtlz_live.isLive = True
        rtlz_live.dontGroup = True

        stream_item = MediaItem("RTL Z: Live Stream", "http://www.rtl.nl/(config=RTLXLV2,channel=rtlxl,progid=rtlz,zone=inlineplayer.rtl.nl/rtlz,ord=0)/system/video/wvx/components/financien/rtlz/miMedia/livestream/rtlz_livestream.xml/1500.wvx")
        stream_item.complete = True
        stream_item.type = "video"
        stream_item.dontGroup = True
        stream_item.append_single_stream("http://mss6.rtl7.nl/rtlzbroad", 1200)
        stream_item.append_single_stream("http://mss26.rtl7.nl/rtlzbroad", 1200)
        stream_item.append_single_stream("http://mss4.rtl7.nl/rtlzbroad", 1200)
        stream_item.append_single_stream("http://mss5.rtl7.nl/rtlzbroad", 1200)
        stream_item.append_single_stream("http://mss3.rtl7.nl/rtlzbroad", 1200)

        rtlz_live.items.append(stream_item)
        items.append(rtlz_live)

        # Add recent items
        data, recent_items = self.add_recent_items(data)
        return data, recent_items

    def add_recent_items(self, data):
        """ Builds the "Recent" folder for this channel.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        recent = MediaItem("\a .: Recent :.", "")
        recent.type = "folder"
        recent.complete = True
        recent.dontGroup = True
        items.append(recent)

        today = datetime.datetime.now()
        days = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        for i in range(0, 7, 1):
            air_date = today - datetime.timedelta(i)
            Logger.trace("Adding item for: %s", air_date)

            # Determine a nice display date
            day = days[air_date.weekday()]
            if i == 0:
                day = "Vandaag"
            elif i == 1:
                day = "Gisteren"
            elif i == 2:
                day = "Eergisteren"
            title = "%04d-%02d-%02d - %s" % (air_date.year, air_date.month, air_date.day, day)

            # url = "https://www.npostart.nl/media/series?page=1&dateFrom=%04d-%02d-%02d&tileMapping=normal&tileType=teaser&pageType=catalogue" % \
            url = "https://xlapi.rtl.nl/version=1/fun=gemist/model=svod/bcdate=" \
                  "{0:04d}{1:02d}{2:02d}/".format(air_date.year, air_date.month, air_date.day)
            extra = MediaItem(title, url)
            extra.complete = True
            extra.dontGroup = True
            extra.set_date(air_date.year, air_date.month, air_date.day, text="")

            recent.items.append(extra)

        news = MediaItem("\a .: Zoeken :.", "#searchSite")
        news.type = "folder"
        news.complete = True
        news.dontGroup = True
        items.append(news)
        return data, items

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict[str,str|None] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        title = result_set["name"]
        key = result_set.get("key", result_set["abstract_key"])
        url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/fun=getseasons/ak=%s" % (key,)
        item = MediaItem(title, url)
        item.complete = True

        desc = result_set.get("synopsis", "")
        item.description = desc

        # sometimes the `"station": False` instead of a string
        channel = str(result_set.get("station", "folder")).lower()
        if channel in self.largeIconSet:
            item.icon = self.largeIconSet[channel]
            item.thumb = self.largeIconSet[channel]

        prog_logo = result_set.get("proglogo", None)
        if prog_logo:
            item.thumb = "http://data.rtl.nl/service/programma_logos/%s" % (prog_logo,)

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

        items = []

        # We need to keep the JSON data, in order to refer to it from the create methods.
        self.currentJson = JsonHelper(data, Logger.instance())

        # Extract season (called abstracts) information
        self.abstracts = dict()  # : the season
        Logger.debug("Storing abstract information")
        for abstract in self.currentJson.get_value("abstracts"):
            self.abstracts[abstract["key"]] = abstract

        # If we have episodes available, list them
        self.episodes = dict()
        if "episodes" in self.currentJson.get_value():
            Logger.debug("Storing episode information")
            for episode in self.currentJson.get_value("episodes"):
                self.episodes[episode["key"]] = episode

        # extract some meta data
        self.posterBase = self.currentJson.get_value("meta", "poster_base_url")
        self.thumbBase = self.currentJson.get_value("meta", "thumb_base_url")

        # And create page items
        items_on_page = int(self.currentJson.get_value("meta", "nr_of_videos_onpage"))
        total_items = int(self.currentJson.get_value("meta", "nr_of_videos_total"))
        current_page = self.currentJson.get_value("meta", "pg")
        if current_page == "all":
            current_page = 1
        else:
            current_page = int(current_page)
        Logger.debug("Found a total of %s items (%s items per page), we are on page %s", total_items, items_on_page, current_page)

        # But don't show them if not episodes were found
        if self.episodes:
            if items_on_page < 50:
                Logger.debug("No more pages to show.")
            else:
                next_page = current_page + 1
                url = self.parentItem.url[:self.parentItem.url.rindex("=")]
                url = "%s=%s" % (url, next_page)
                Logger.trace(url)
                page_item = MediaItem(str(next_page), url)
                page_item.type = "page"
                page_item.complete = True
                items.append(page_item)

        return data, items

    def create_folder_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """
        Logger.trace(result_set)

        if "/sk=" in self.parentItem.url:
            return None

        abstract_key = result_set["abstract_key"]
        abstract_data = self.abstracts.get(abstract_key, None)
        if not abstract_data:
            Logger.warning("Could not find abstract data for key: %s", abstract_key)
            return None

        Logger.debug("Found Abstract Data: %s", abstract_data)

        abstract_name = abstract_data.get("name", "")
        title = result_set["name"]
        if abstract_name:
            title = "%s - %s" % (abstract_name, title)

        description = result_set.get("synopsis", None)
        key_value = result_set["key"]
        url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/ak=%s/sk=%s/pg=1" % (abstract_key, key_value)

        item = MediaItem(title.title(), url)
        item.description = description
        item.thumb = "%s/%s.png" % (self.posterBase, key_value,)
        item.complete = True
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

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        episode_key = result_set["episode_key"]
        if episode_key:
            episode_data = self.episodes.get(episode_key, None)
            if not episode_data:
                Logger.warning("Could not find episodes data for key: %s", episode_key)
                return None
            Logger.debug("Found Episode Data: %s", episode_data)
        else:
            Logger.debug("No Episode Data Found")
            episode_data = None

        title = result_set["title"]
        description = None
        if episode_data:
            if title:
                title = "%s - %s" % (episode_data["name"], title)
            else:
                title = episode_data["name"]
            description = episode_data.get("synopsis", None)

        # tarifs have datetimes
        # noinspection PyStatementEffect
        # """
        #             "ddr_timeframes": [{
        #                     "start": 1382119200,
        #                     "stop": 1382378399,
        #                     "tariff": 149
        #                 },
        #                 {
        #                     "start": 1382378400,
        #                     "tariff": 0
        #                 }],
        #
        #         """

        tariffs = result_set.get("ddr_timeframes")
        premium_item = False
        if tariffs:
            Logger.trace(tariffs)
            for tariff in tariffs:  # type: dict
                if tariff["tariff"] > 0:
                    start = tariff.get("start", 0)
                    end = tariff.get("stop", 2147483647)
                    start = DateHelper.get_date_from_posix(start)
                    end = DateHelper.get_date_from_posix(end)
                    now = datetime.datetime.now()
                    if start < now < end:
                        premium_item = True
                        Logger.debug("Found a tariff for this episode: %s - %s: %s", start, end, tariff["tariff"])
                        break

        uuid = result_set["uuid"]
        url = "http://www.rtl.nl/system/s4m/xldata/ux/%s?context=rtlxl&d=pc&fmt=adaptive&version=3" % (uuid,)
        # The JSON urls do not yet work
        # url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/fun=abstract/uuid=%s/fmt=smooth" % (uuid,)

        item = MediaItem(title.title(), url)
        item.type = "video"
        item.isPaid = premium_item
        item.description = description
        item.thumb = "%s%s" % (self.posterBase, uuid,)

        station = result_set.get("station", None)
        if station:
            icon = self.largeIconSet.get(station.lower(), None)
            if icon:
                Logger.trace("Setting icon to: %s", icon)
                item.icon = icon

        date_time = result_set.get("display_date", None)
        if date_time:
            date_time = DateHelper.get_date_from_posix(int(date_time))
            item.set_date(date_time.year, date_time.month, date_time.day,
                          date_time.hour, date_time.minute, date_time.second)

        return item

    def search_site(self, url=None):
        """ Creates an list of items by searching the site.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with an URL encoded representation of the
        text to search for.

        :param str url:     Url to use to search with a %s for the search parameters.

        :return: A list with search results as MediaItems.
        :rtype: list[MediaItem]

        """

        items = []
        needle = XbmcWrapper.show_key_board()
        if not needle:
            return []

        Logger.debug("Searching for '%s'", needle)
        # convert to HTML
        needle = HtmlEntityHelper.url_encode(needle)

        # Search Programma's
        url = "https://search.rtl.nl/?typeRestriction=tvabstract&search={}&page=1&pageSize=99"
        search_url = url.format(needle)
        temp = MediaItem("Search", search_url)
        items += self.process_folder_list(temp) or []

        # Search Afleveringen -> no dates given, so this makes little sense
        # url = "https://search.rtl.nl/?typeRestriction=videoobject&uitzending=true&search={}&page=1&pageSize=99"
        # search_url = url.format(needle)
        # temp = MediaItem("Search", search_url)
        # items += self.process_folder_list(temp) or []

        return items

    def create_search_program_item(self, result_set):
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

        title = result_set["Title"]
        # Not used: uuid = result_set["Uuid"]
        abstract_key = result_set["AbstractKey"]
        url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/fun=getseasons/ak={}".format(abstract_key)
        item = MediaItem(title, url)

        time_stamp = result_set["LastBroadcastDate"]  # =1546268400000
        date_time = DateHelper.get_date_from_posix(int(time_stamp)/1000)
        item.set_date(date_time.year, date_time.month, date_time.day,
                      date_time.hour, date_time.minute, date_time.second)

        return item

    def create_recent_video_item(self, result_set):
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

        show_title = result_set["abstract_name"]
        episode_title = result_set["title"]
        title = "{} - {}".format(show_title, episode_title)
        description = result_set.get("synopsis")

        uuid = result_set["uuid"]
        url = "http://www.rtl.nl/system/s4m/xldata/ux/%s?context=rtlxl&" \
              "d=pc&fmt=adaptive&version=3" % (uuid, )
        # The JSON urls do not yet work
        # url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/" \
        #       "fun=abstract/uuid=%s/fmt=smooth" % (uuid,)

        item = MediaItem(title.title(), url)
        item.type = "video"
        item.description = description
        item.thumb = "%s%s" % (self.posterBase, uuid,)

        audience = result_set.get("audience")
        Logger.debug("Found audience: %s", audience)
        item.isGeoLocked = audience == "ALLEEN_NL"
        # We can play the DRM stuff
        # item.isDrmProtected = audience == "DRM"

        station = result_set.get("station", None)
        if station:
            item.name = "{} ({})".format(item.name, station)
            icon = self.largeIconSet.get(station.lower(), None)
            if icon:
                Logger.trace("Setting icon to: %s", icon)
                item.icon = icon

        # 2018-12-05T19:30:00.000Z
        date_time = result_set.get("dateTime", None)
        if date_time:
            date_time = DateHelper.get_date_from_string(date_time[:-5], "%Y-%m-%dT%H:%M:%S")
            # The time is in UTC, and the show as at UTC+1
            date_time = datetime.datetime(*date_time[:6]) + datetime.timedelta(hours=1)
            item.name = "{:02d}:{:02d}: {}".format(date_time.hour, date_time.minute, item.name)
            item.set_date(date_time.year, date_time.month, date_time.day,
                          date_time.hour, date_time.minute, date_time.second)
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

        xml_data = UriHandler.open(item.url, proxy=self.proxy)
        # <ref type='adaptive' device='pc' host='http://manifest.us.rtl.nl' href='/rtlxl/network/pc/adaptive/components/videorecorder/27/278629/278630/d009c025-6e8c-3d11-8aba-dc8579373134.ssm/d009c025-6e8c-3d11-8aba-dc8579373134.m3u8' />
        m3u8_urls = Regexer.do_regex("<ref type='adaptive' device='pc' host='([^']+)' href='/([^']+)' />", xml_data)
        if not m3u8_urls:
            Logger.warning("No m3u8 data found for: %s", item)
            return item
        m3u8_url = "%s/%s" % (m3u8_urls[0][0], m3u8_urls[0][1])

        part = item.create_new_empty_media_part()
        # prevent the "418 I'm a teapot" error
        part.HttpHeaders["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0"

        # Remove the Range header to make all streams start at the beginning.
        # Logger.debug("Setting an empty 'Range' http header to force playback at the start of a stream")
        # part.HttpHeaders["Range"] = ''

        item.complete = M3u8.update_part_with_m3u8_streams(part, m3u8_url,
                                                           proxy=self.proxy,
                                                           headers=part.HttpHeaders,
                                                           channel=self)
        return item

    def __ignore_cookie_law(self):
        """ Accepts the cookies from RTL channel in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        # the rfc2109 parameters is not valid in Python 2.4 (Xbox), so we ommit it.
        UriHandler.set_cookie(name='rtlcookieconsent', value='yes', domain='.www.rtl.nl')
        return
