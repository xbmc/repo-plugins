# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class, mediatype, contenttype

from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.parserdata import ParserData
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.streams.m3u8 import M3u8


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
        self.noImage = "tweedekamer.png"

        # setup the urls
        self.mainListUri = "#overview"

        self.baseUrl = "https://cdn.debatdirect.tweedekamer.nl"

        # setup the main parsing data
        self._add_data_parser(self.mainListUri,
                              preprocessor=self.create_main_index)

        # additional parsers
        # - list of locations and livestreams
        self._add_data_parser("https://cdn.debatdirect.tweedekamer.nl/api/app",
                              match_type=ParserData.MatchExact,
                              json=True,
                              parser=[],
                              creator=self.create_livestreams,
                              updater=self.update_livestream_item)
        # - livestream of a specific location
        self._add_data_parser(r"https://livestreaming.+.tweedekamer.nl/.+/.+/index.m3u8.+",
                              match_type=ParserData.MatchRegex,
                              updater=self.update_livestream_item)
        # - calendar index showing last few days
        self._add_data_parser("https://cdn.debatdirect.tweedekamer.nl/api/agenda",
                              match_type=ParserData.MatchExact,
                              json=True,
                              parser=["overview",],
                              creator=self.create_debate_archive)
        # - debate list for a specific date
        self._add_data_parser(r"^https://cdn.debatdirect.tweedekamer.nl/api/agenda/[-0-9]+",
                              match_type=ParserData.MatchRegex,
                              json=True,
                              parser=[],
                              creator=self.create_video_items,
                              updater=self.update_video_item)
        # - search results
        self._add_data_parser(r"^https://cdn.debatdirect.tweedekamer.nl/search",
                              match_type=ParserData.MatchRegex,
                              json=True,
                              parser=['hits'],
                              creator=self.create_video_items_from_search,
                              updater=self.update_video_item)

        #===============================================================================================================
        # non standard items
        self.__pageSize = 50

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_main_index(self, data):
        """ Creates the index listing (debates, live, search).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Creating main index")
        items = []

        cats = {
            "Debatten terugkijken": "https://cdn.debatdirect.tweedekamer.nl/api/agenda",
            "Livestreams": "https://cdn.debatdirect.tweedekamer.nl/api/app",
            LanguageHelper.get_localized_string(LanguageHelper.Search): 'searchSite',
        }

        for cat in cats:
            item = FolderItem(cat, cats[cat], content_type=contenttype.VIDEOS)
            item.thumb = "https://cdn.debatdirect.tweedekamer.nl/static/img/bg/plenaire-zaal.jpg"
            item.fanart = "https://cdn.debatdirect.tweedekamer.nl/static/img/bg/plenaire-zaal.jpg"
            item.complete = True
            items.append(item)

        Logger.debug("Creating main index finished")
        return data, items

    def create_livestreams(self, result_set):
        """ Creates a list of MediaItems for the livestreams.

        :param list[str]|dict[str,dict] result_set: The result_set of the self.episodeItemRegex

        :return: A list of new MediaItems of type 'video'.
        :rtype: list[MediaItem]

        """

        Logger.info("Creating livestreams")
        items = []

        # list the livestream for each location (plenaire zaal et cetera)
        for location in result_set["locations"]:
            url = location["streamUrl"].replace("{date}", "live")
            item = MediaItem(location["name"], url, media_type=mediatype.VIDEO)
            item.description = location["description"]
            item.complete = False
            item.isLive = True
            item.isGeoLocked = False
            item.thumb = location["imageUrl"]
            item.fanart = location["imageUrl"]
            items.append(item)

        Logger.debug("Creating livestreams finished")
        return items

    def update_livestream_item(self, item):
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

        Logger.info('Starting update_livestream_item: url = %s', item.url)

        # use Retrospect code to extract streams
        for s, b in M3u8.get_streams_from_m3u8(item.url):
            item.add_stream(s, b)
        item.complete = True

        Logger.debug('Finished update_livestream_item: url = %s', item.url)
        return item

    def create_debate_archive(self, result_set):
        """ Creates a list of MediaItems of type 'page' for the recent dates.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,dict] result_set: The result_set of the self.episodeItemRegex

        :return: A list of new MediaItems of type 'page'.
        :rtype: list[MediaItem]

        """

        Logger.info("Creating debate archive")

        items = []
        days = LanguageHelper.get_days_list()

        # generate one item for each day
        for day in result_set["days"].values():
            date = day["date"]
            debate_count = day["debateCount"]

            # only include days with at least one debate
            if debate_count > 0:
                date_stamp = DateHelper.get_datetime_from_string(date, date_format="%Y-%m-%d")
                day = days[date_stamp.weekday()]
                if debate_count == 1:
                    title = "%s - %s (%d debat)" % (date, day, debate_count)
                else:
                    title = "%s - %s (%d debatten)" % (date, day, debate_count)
                url = "https://cdn.debatdirect.tweedekamer.nl/api/agenda/%s" % date

                item = MediaItem(title, url)
                item.thumb = "https://cdn.debatdirect.tweedekamer.nl/static/img/bg/plenaire-zaal.jpg"
                item.fanart = "https://cdn.debatdirect.tweedekamer.nl/static/img/bg/plenaire-zaal.jpg"
                items.append(item)

        Logger.debug("Creating debate archive finished")
        return items

    def create_video_items(self, result_set):
        """ Creates a list of MediaItems for the debates on a specific date.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A list of new MediaItems of type 'video'.
        :rtype: list[MediaItem]

        """

        Logger.info("Creating video items")

        items = []
        for debate in result_set["debates"]:
            item = self.__create_video_item_for_debate(debate)
            items.append(item)

        Logger.debug("Creating video items finished")
        return items

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

        Logger.info('Starting update_video_item: %s', item.name)

        data = UriHandler.open(item.url)
        json_data = JsonHelper(data)

        introduction = json_data.get_value("introduction")
        if introduction:
            item.description += "\n" + introduction

        url = json_data.get_value("video", "vodUrl")

        url += '&start=%s&end=%s' % (HtmlEntityHelper.url_encode(json_data.get_value('startedAt')),
                                     HtmlEntityHelper.url_encode(json_data.get_value('endedAt')))

        Logger.info('Starting update_video_item: url = %s', url)

        item.thumb = json_data.get_value("video", "imageUrl")
        item.fanart = json_data.get_value("video", "imageUrl")

        duration = json_data.get_value("duration")
        if duration:
            duration = sum([int(d) * (60 ** i)
                            for i, d in enumerate(reversed(duration.split(":")))])
            item.set_info_label(MediaItem.LabelDuration, duration)

        # alternative: use inputstream adaptive
        # (currently does not work)
        # item.complete = M3u8.update_part_with_m3u8_streams(item, url, channel=self, encrypted=False, map_audio=True)

        # use Retrospect code to extract streams
        for s, b in M3u8.get_streams_from_m3u8(url):
            item.add_stream(s, b)
        item.complete = True

        Logger.debug('Finished update_video_item: %s', item.name)
        return item

    def search_site(self, url=None):  # @UnusedVariable
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

        url = "https://cdn.debatdirect.tweedekamer.nl/search?q=%s&status[0]=geweest&sortering=relevant&vanaf=0"
        return chn_class.Channel.search_site(self, url)

    def create_video_items_from_search(self, result_set):
        """ Creates a list of MediaItems for the debates in the search results.

        :param list[str]|dict[str,dict] result_set: The result_set of the self.episodeItemRegex

        :return: A list of new MediaItems of type 'video'.
        :rtype: list[MediaItem]

        """

        Logger.info("Creating video items")

        items = []
        for hit in result_set["hits"]:
            item = self.__create_video_item_for_debate(hit["_source"])
            items.append(item)

        return items

    def __create_video_item_for_debate(self, debate):
        # create a MediaItem for the debate, given the JSON metadata 

        # startsAt is the official starting time in the calendar
        # we ignore the time zone to always use the local Dutch time
        time_stamp = DateHelper.get_date_from_string(debate["startsAt"][:19],
                                                     date_format="%Y-%m-%dT%H:%M:%S")

        url = "https://cdn.debatdirect.tweedekamer.nl/api/agenda/%s/debates/%s" \
              % (debate["debateDate"], debate["id"])

        # title: HH:MM - title
        title = "%02d:%02d - %s" % (time_stamp[3], time_stamp[4], debate["name"])

        # add debate location, category, and perhaps the introduction text
        description = "%s / %s" % (debate["locationName"], debate["debateType"])
        if "categoryNames" in debate:
            description += "\n%s" % ", ".join(debate["categoryNames"])
        if "introduction" in debate:
            description += "\n\n%s" % debate["introduction"]

        # create the item for this debate
        item = MediaItem(title, url, media_type=mediatype.VIDEO)
        item.description = description
        item.set_date(*time_stamp[0:6])
        item.complete = False
        item.isGeoLocked = False

        # duration is not returned for search results
        if "duration" in debate:
            duration = debate["duration"]
            duration = sum([int(d) * (60 ** i)
                            for i, d in enumerate(reversed(duration.split(":")))])
            item.set_info_label(MediaItem.LabelDuration, duration)

        # use the location photo as the thumbnail
        locations = self.__get_location_data()
        if debate["locationId"] in locations:
            item.thumb = locations[debate["locationId"]]["imageUrl"]
            item.fanart = locations[debate["locationId"]]["imageUrl"]

        return item

    def __get_location_data(self):
        # load the locations from the API
        if hasattr(self, "__cache_locations"):
            return self.__cache_locations

        data = UriHandler.open("https://cdn.debatdirect.tweedekamer.nl/api/app")
        json_data = JsonHelper(data)

        locations = {}
        for location in json_data.get_value("locations"):
            locations[location["slug"]] = {
                    "name": location["name"],
                    "imageUrl": location["imageUrl"],
                }
        self.__cache_locations = locations
        return locations
