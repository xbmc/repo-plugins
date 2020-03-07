# coding:UTF-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import datetime

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.logger import Logger
from resources.lib.parserdata import ParserData
from resources.lib.urihandler import UriHandler
from resources.lib.regexer import Regexer
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

        if self.channelCode == "pathejson":
            # we need to add headers and stuff for the API
            # self.UriHandlerOpen = UriHandler.open
            # UriHandler.open = self.__JsonHandlerOpen

            self.baseUrl = "https://connect.pathe.nl/v1"
            # set the default headers
            self.httpHeaders = {"X-Client-Token": "2d1411a8ec9842988e2700a1e3180dd3",
                                "Accept": "application/json"}
            self.mainListUri = "https://connect.pathe.nl/v1/cinemas"

            self._add_data_parser("https://connect.pathe.nl/v1/cinemas", json=True,
                                  match_type=ParserData.MatchExact,
                                  parser=[], creator=self.create_cinema)
            self._add_data_parser("/movies/nowplaying", json=True, match_type=ParserData.MatchEnd,
                                  parser=[], creator=self.create_movie)
            self._add_data_parser("https://connect.pathe.nl/v1/movies/", json=True,
                                  parser=['trailers'], creator=self.create_trailer)
            self._add_data_parser("/schedules?date=", json=True,
                                  match_type=ParserData.MatchContains,
                                  preprocessor=self.get_schedule_data,
                                  parser=['movies'], creator=self.create_movie)

        elif self.channelCode == "pathe":
            self.mainListUri = "https://www.pathe.nl"
            self.baseUrl = "https://www.pathe.nl"
            # setup the main parsing data
            self.episodeItemRegex = '<li><a[^>]+href="(https://www.pathe.nl/bioscoop/[^"]+)"[^>]+>([^<]+)</a></li>'
            self.folderItemRegex = r'<li class="tab-item[^>]+>\W+<a[^>]+title="\w+ (\d+) (\w+) (\d+)"[^<]+' \
                                   r'href="([^#]+)#schedule[^>]*>(\w+)'
            self.videoItemRegex = r'<div class="schedule-movie">\W+<a[^>]+href="([^#]+)\#[^>]+"[^>]+' \
                                  r'title="([^"]+)"[^>]+>\W+<div[^>]+>\W+<img[^>]+src="([^"]+)"[^>]+>\W+</div>' \
                                  r'[\w\W]{0,1500}?<table class="table-schedule">([\w\W]{0,5000}?)</table>'
            self.mediaUrlRegex = 'file: "(http[^"]+)'
        else:
            raise NotImplementedError("Code %s is not implemented" % (self.channelCode,))

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "patheimage.png"
        self.scheduleData = None

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_cinema(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        cinema = MediaItem(result_set["name"], "")
        cinema.thumb = result_set["image"].replace("nocropthumb/[format]/", "")
        cinema.complete = True

        now_playing_url = "%s/cinemas/%s/movies/nowplaying" % (self.baseUrl, result_set["id"])
        now_playing = MediaItem("Trailers", now_playing_url)
        # https://www.pathe.nl/nocropthumb/[format]/gfx_content/bioscoop/foto/pathe.nl_380x218px_amersfoort.jpg
        now_playing.complete = True
        now_playing.HttpHeaders = self.httpHeaders
        cinema.items.append(now_playing)

        now = datetime.datetime.now()
        for i in range(0, 10):
            date = now + datetime.timedelta(days=i)
            title = "%s-%02d-%02d" % (date.year, date.month, date.day)
            schedule_url = "%s/cinemas/%s/schedules?date=%s" % (self.baseUrl, result_set["id"], title)
            schedule = MediaItem("Agenda: %s" % (title,), schedule_url)
            schedule.complete = True
            schedule.thumb = cinema.thumb
            schedule.HttpHeaders = self.httpHeaders
            cinema.items.append(schedule)
        return cinema

    def create_movie(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        movie_id = result_set['id']
        url = "%s/movies/%s" % (self.baseUrl, movie_id)
        item = MediaItem(result_set["name"], url)
        item.thumb = result_set["thumb"].replace("nocropthumb/[format]/", "")
        item.complete = True
        item.HttpHeaders = self.httpHeaders

        if self.scheduleData:
            Logger.debug("Adding schedule data")
            schedule_data = [s for s in self.scheduleData if s['movieId'] == movie_id]
            schedule = ""
            day = ""
            for s in schedule_data:
                start = s['start']
                day, start = start.split("T")
                hour, minute, ignore = start.split(":", 2)
                start = "%s:%s" % (hour, minute)

                end = s['end']
                ignore, end = end.split("T")
                hour, minute, ignore = end.split(":", 2)
                end = "%s:%s" % (hour, minute)

                schedule = "%s%s-%s, " % (schedule, start, end)
            item.description = "%s\n\n%s: %s" % (item.description, day, schedule.strip(', '))

        item.description = "%s\n\n%s" % (item.description, result_set.get('teaser', ""))
        if not item.description.endswith('.'):
            item.description = "%s." % (item.description, )

        if "releaseDate" in result_set:
            item.description = "%s\n\nRelease datum: %s" % (item.description, result_set["releaseDate"])

        # Dates?
        # date = result_set.get('releaseDate', None)
        # if date is not None:
        #     year, month, day = date.split("-")
        #     item.set_date(year, month, day)

        item.description = item.description.strip()
        return item

    def create_trailer(self, result_set):
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
        url = self.parentItem.url
        item = MediaItem(result_set["caption"], url, "video")
        item.thumb = result_set["still"].replace("nocropthumb/[format]/", "")
        item.fanart = item.thumb
        item.append_single_stream(result_set['filename'])
        item.complete = True
        item.HttpHeaders = self.httpHeaders
        return item

    def get_schedule_data(self, data):
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
        json = JsonHelper(data)
        self.scheduleData = json.get_value("schedules")
        Logger.debug("Pre-Processing finished")
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

        item = MediaItem(result_set[1], result_set[0])
        item.complete = True
        return item

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

        if self.parentItem.url.endswith(str(DateHelper.this_year())):
            return None

        url = "%s%s" % (self.baseUrl, result_set[3])
        name = result_set[4]

        item = MediaItem(name.title(), url)

        day = result_set[0]
        month = result_set[1]
        month = DateHelper.get_month_from_name(month, "nl", short=False)
        year = result_set[2]

        item.set_date(year, month, day)
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

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        if not self.parentItem.url[-1].isdigit():
            # only video on folders for day
            return None

        name = result_set[1]
        url = "%s%s" % (self.baseUrl, result_set[0])

        thumb_url = result_set[2]
        if not thumb_url.startswith("http"):
            thumb_url = "%s%s" % (self.baseUrl, thumb_url)
        # https://www.pathe.nl/gfx_content/posters/clubvansinterklaas3p1.jpg
        # https://www.pathe.nl/nocropthumb/180x254/gfx_content/posters/clubvansinterklaas3p1.jpg
        thumb_url = thumb_url.replace("nocropthumb/180x254/", "")

        item = MediaItem(name, url)
        item.thumb = thumb_url
        item.type = 'video'

        # more description stuff
        # description = "%s\n\n" % (result_set[4],)
        description = ""
        
        time_table = result_set[3]
        time_table_regex = \
            r'<ul>\W+<li><b>([^<]+)</b></li>\W+<li>\w+ (\d+:\d+)</li>\W+<li>\w+ (\d+:\d+)</li>'
        bios_set = False
        for time_table_entry in Regexer.do_regex(time_table_regex, time_table):
            Logger.trace(time_table_entry)

            bios = time_table_entry[0]
            if not bios_set:
                description = "%s%s: " % (description, bios)
                bios_set = True

            start_time = time_table_entry[1]
            end_time = time_table_entry[2]
            description = "%s%s-%s, " % (description, start_time, end_time)

        description = description.strip(', ')
        item.description = description.strip()
        
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
        
        data = UriHandler.open(item.url, proxy=self.proxy)
        videos = Regexer.do_regex(self.mediaUrlRegex, data)

        fanart = Regexer.do_regex(r'<div class="visual-image">\W+<img src="([^"]+)"', data)
        if fanart:
            item.fanart = fanart[0]

        for video in videos:
            Logger.trace(video)
            item.append_single_stream(video)
        
        item.complete = True
        return item
