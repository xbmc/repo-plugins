# SPDX-License-Identifier: GPL-3.0-or-later
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.parserdata import ParserData

from resources.lib import chn_class, contenttype, mediatype
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.logger import Logger
from resources.lib.regexer import Regexer
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
        self.noImage = "channel9image.png"

        # setup the urls
        self.mainListUri = "#mainlist"
        self.baseUrl = "https://docs.microsoft.com"

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.fetch_pages,
                              parser=[], creator=self.create_episode_item)

        self._add_data_parser("https://docs.microsoft.com/api/hierarchy/shows/", json=True,
                              name="Video listings",
                              preprocessor=self.fetch_video_pages,
                              parser=["episodes"], creator=self.create_video_item)

        self._add_data_parser("https://docs.microsoft.com/api/video", updater=self.update_video_item)

        self.__episode_regex = r"^(.+) \[(\d+) of (\d+)\](?: (.+))?$"
        # =========================== Actual channel setup STOPS here ==============================
        return

    # noinspection PyUnusedLocal
    def fetch_pages(self, combined_data):
        """ Fetches the pages for the mainlist

        :param str combined_data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        combined_data = []
        max_items = 31
        skip = 30
        i = 0

        while i < max_items:
            url = "https://docs.microsoft.com/api/contentbrowser/search/shows?" \
                  "locale=en-us&" \
                  "facet=products&" \
                  "facet=type&" \
                  "%24orderBy=latest_episode_upload_at%20desc&" \
                  "%24skip={:d}&" \
                  "%24top=30".format(i)
            raw_data = UriHandler.open(url)
            json_data = JsonHelper(raw_data)
            combined_data += json_data.get_value("results", fallback=[])
            max_items = json_data.get_value("count")
            i += skip

        data = JsonHelper("[]")
        data.json = combined_data

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

        hidden = result_set["hidden"]
        if hidden:
            return None

        name = result_set["title"]
        # item_type = result_set["type"]
        # item_id = result_set["uid"]
        slug = result_set["url"]
        # https://docs.microsoft.com/api/hierarchy/shows/xamarinshow/episodes?page=0&locale=en-us&pageSize=30&orderBy=uploaddate%20desc
        url = "{}/api/hierarchy{}episodes?page=0&locale=en-us&pageSize=30&orderBy=uploaddate%20desc".format(self.baseUrl, slug)

        item = FolderItem(name, url, content_type=contenttype.EPISODES)

        thumb = result_set["image_url"]
        if thumb:
            # https://docs.microsoft.com/shows/vs-code-livestreams/media/vscodelivestream_383x215.png
            thumb = "{}{}{}".format(self.baseUrl, slug, thumb)
            item.thumb = thumb

        self.__set_date(result_set.get("latest_episode_upload_at"), item)
        return item

    def fetch_video_pages(self, data):
        """ Fetches the pages for the mainlist

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        data = JsonHelper(data)
        max_items = data.get_value("totalCount")
        items = data.get_value("episodes")
        if len(items) == max_items:
            return data, []

        page_number = 1

        # we limit at 5 pages of 30 items
        while len(items) < max_items and len(items) < 5 * 30:
            url = self.parentItem.url.replace("page=0", "page={}".format(page_number))
            raw_data = UriHandler.open(url)
            json_data = JsonHelper(raw_data)
            items += json_data.get_value("episodes", fallback=[])
            max_items = json_data.get_value("totalCount")
            page_number += 1

        return data, []

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
        title = result_set["title"]
        episode = None
        season = None
        if "[" in title:
            episode_info = Regexer.do_regex(self.__episode_regex, title)
            if episode_info:
                episode = int(episode_info[0][1])
                season = "1"  # int(episode_info[0][2])
                title = episode_info[0][0]
                if episode_info[0][3]:
                    title = "{} - {}".format(episode_info[0][0], episode_info[0][3])

                # title = "{:02d} of {:02d} - {}".format(episode, season, title)

        description = result_set["description"]
        date_value = result_set["uploadDate"]

        if "entryId" not in result_set:
            return None

        url = "{}/api/video/public/v1/entries/batch?ids={}".format(self.baseUrl, result_set["entryId"])
        # https://docs.microsoft.com/api/video/public/v1/entries/batch?ids=0998ca55-c69f-468e-831d-176cde7e8a78%2C5cb5e481-e64d-4400-bb2d-2f8a6284bd62%2Cc5ccb371-39a6-474c-a9d7-bb8b0fa7567c%2C8b11149d-acaa-4a4b-a50d-5eb010933e5d%2C9fb9f5ed-aca9-48b9-b5c6-298fbbce117b%2Cb1a2aa31-6157-486d-8a2c-73ff70272897%2C89ed8ecb-a660-4ec7-ab1a-f2338410edec%2Ce35cd0b1-d655-4777-a03e-924b3dcd10b1%2Ccdbbafc4-42ba-4261-b0b7-85ddc95cd8d8%2C18123cfb-5973-49aa-8b88-08ce1547f278%2Cd168a18c-9119-4531-a288-8675eea93da5%2C977bf1ce-8ba9-4e07-998d-f87c7d44ba47

        item = MediaItem(title, url, media_type=mediatype.EPISODE)
        item.description = description or ""
        if season and episode:
            item.set_season_info(season, episode)

        levels = result_set.get("levels")
        if levels:
            item.description = "Levels: {}[CR][CR]{}".format(", ".join(levels), item.description)

        self.__set_date(date_value, item)
        return item

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

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.open(item.url)
        json_data = JsonHelper(data)
        item_data = json_data.get_value(0, "entry")
        video_data = item_data["publicVideo"]
        hls = video_data.get("adaptiveVideoUrl")
        high = video_data.get("highQualityVideoUrl")
        medium = video_data.get("mediumQualityVideoUrl")
        low = video_data.get("lowQualityVideoUrl")
        if hls and False:
            pass
        else:
            if low:
                item.add_stream(low, bitrate=400)
            if medium:
                item.add_stream(medium, bitrate=1000)
            if high:
                item.add_stream(high, bitrate=1400)
        item.complete = item.has_streams()

        # Fix relative streams.
        for stream in item.streams:
            if not stream.Url.startswith("https://"):
                stream.Url = "{}{}".format(self.baseUrl, stream.Url)
        return item

    def __set_date(self, date_value, item):
        # # '2021-11-23T22:16:00Z'
        if date_value:
            date_value = date_value.rsplit(".", 1)[0]
            date_value = date_value.replace("Z", "")
            time_stamp = DateHelper.get_date_from_string(date_value, "%Y-%m-%dT%H:%M:%S")
            item.set_date(*time_stamp[0:6])
        pass
