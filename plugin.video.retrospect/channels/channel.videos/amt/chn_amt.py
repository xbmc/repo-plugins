# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class
from resources.lib.mediaitem import MediaItem
from resources.lib.helpers import datehelper
from resources.lib.regexer import Regexer

from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler


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

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = "amtimage.png"

        # setup the urls
        self.baseUrl = "http://trailers.apple.com"
        self.mainListUri = "http://trailers.apple.com/trailers/home/feeds/just_added.json"

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, parser=[], json=True,
                              creator=self.create_episode_item)
        self._add_data_parser("*", json=True, preprocessor=self.get_movie_id,
                              parser=["clips", ], creator=self.create_video_item)

        # ========================= Actual channel setup STOPS here ================================
        return

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict[str,Any] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        title = result_set["title"]
        date = result_set["trailers"][0]["postdate"]
        url = result_set["trailers"][0]["url"]
        thumb_url = result_set["poster"]
        if "http:" not in thumb_url:
            thumb_url = "%s%s" % (self.baseUrl, thumb_url)
        fanart = thumb_url.replace("poster.jpg", "background.jpg")

        # get the url that shows all trailers/clips. Because the json
        # only shows the most recent one.
        url = "%s%s" % (self.baseUrl, url)

        # Logger.Trace(date)
        dates = date.split(" ")
        # Logger.Trace(dates)
        day = dates[1]
        month = datehelper.DateHelper.get_month_from_name(dates[2], "en")
        year = dates[3]

        # dummy class
        item = MediaItem(title, url)
        item.thumb = thumb_url.replace("poster.jpg", "poster-xlarge.jpg")
        item.fanart = fanart
        item.set_date(year, month, day)
        item.complete = True

        # Set some info labels
        studio = result_set["studio"]
        item.set_info_label("studio", studio)
        directors = result_set["directors"]
        item.set_info_label("Director", directors)
        actors_data = result_set["actors"][:]
        item.set_info_label("cast", actors_data)
        genre_data = result_set["genre"][:]
        item.set_info_label("genre", genre_data)

        return item

    def get_movie_id(self, data):
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

        movie_id = Regexer.do_regex(r"movietrailers://movie/detail/(\d+)", data)[-1]
        Logger.debug("Found Movie ID: %s", movie_id)
        url = "%s/trailers/feeds/data/%s.json" % (self.baseUrl, movie_id)
        data = UriHandler.open(url, proxy=self.proxy)

        # set it for logging purposes
        self.parentItem.url = url

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

        :param dict[str,Any] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        title = result_set["title"]
        title = "%s - %s" % (self.parentItem.name, title)

        thumb = result_set["thumb"]
        year, month, day = result_set["posted"].split("-")
        item = MediaItem(title, self.parentItem.url)
        item.description = self.parentItem.description
        item.type = 'video'
        item.thumb = thumb
        item.set_date(year, month, day)

        runtime = result_set.get("runtime").split(":")
        if runtime:
            duration = (int(runtime[0]) * 60) + int(runtime[1])
            item.set_info_label("duration", duration)

        part = item.create_new_empty_media_part()
        part.HttpHeaders["User-Agent"] = "QuickTime/7.6 (qtver=7.6;os=Windows NT 6.0Service Pack 2)"

        if "versions" in result_set and "enus" in result_set["versions"] and "sizes" in result_set["versions"]["enus"]:
            streams = result_set["versions"]["enus"]["sizes"]
            stream_types = ("src", "srcAlt")
            bitrates = {"hd1080": 8300, "hd720": 5300, "sd": 1200}
            for s in streams:
                bitrate = bitrates.get(s, 0)
                stream_data = streams[s]

                # find all possible stream stream types
                for t in stream_types:
                    if t in stream_data:
                        stream_url = stream_data[t]
                        if stream_url.endswith(".mov"):
                            # movs need to have a 'h' before the quality
                            parts = stream_url.rsplit("_", 1)
                            if len(parts) == 2:
                                Logger.trace(parts)
                                stream_url = "%s_h%s" % (parts[0], parts[1])
                            part.append_media_stream(stream_url, bitrate)
                        else:
                            part.append_media_stream(stream_url, bitrate)
                        item.complete = True

        return item
