# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.datehelper import DateHelper
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
        self.useAtom = False  # : The atom feeds just do not give all videos
        self.noImage = "srfimage.png"

        # setup the urls
        self.mainListUri = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/tv/assetGroup/editorialPlayerAlphabetical.json"
        self.baseUrl = "http://www.srf.ch"

        # setup the intial listing
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              parser=["AssetGroups", "Show"], creator=self.create_episode_item_new)

        # self._add_data_parser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
        #                     preprocessor=self.get_live_items)

        self._add_data_parser("http://il.srgssr.ch/integrationlayer/1.0/ue/srf/video/play",
                              updater=self.update_live_item)

        self._add_data_parser("http://il.srgssr.ch/integrationlayer/1.0/ue/srf/assetSet/listByAssetGroup", json=True,
                              parser=['AssetSets', 'AssetSet'],
                              creator=self.create_video_item_new)

        # TODO: folders
        self._add_data_parser("http://www.srf.ch/player/webservice/videodetail/", updater=self.update_video_item)

        # ===============================================================================================================
        # Test cases:
        #
        # ====================================== Actual channel setup STOPS here =======================================
        return

    def get_live_items(self, data):
        """ Adds live stream items.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Fetching episode items")
        items = []

        live_items = MediaItem("\a.: Live TV :.", "")
        items.append(live_items)

        live_base = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/video/play/%s.json"
        live_channels = {"SRF 1 live": ("c4927fcf-e1a0-0001-7edd-1ef01d441651", "srf1.png"),
                         "SRF zwei live": ("c49c1d64-9f60-0001-1c36-43c288c01a10", "srf2.png"),
                         "SRF info live": ("c49c1d73-2f70-0001-138a-15e0c4ccd3d0", "srfinfo.png")}
        for live_item in live_channels.keys():
            item = MediaItem(live_item, live_base % (live_channels[live_item][0],))
            item.thumb = self.get_image_location(live_channels[live_item][1])
            item.isGeoLocked = True
            item.type = "video"
            live_items.items.append(item)

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

        Logger.trace(result_set)

        url = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/assetSet/listByAssetGroup/%s.json" % (result_set["id"],)
        item = MediaItem(result_set["title"], url)
        item.description = result_set.get("description", "")
        item.httpHeaders = self.httpHeaders

        # the 0005 seems to be a quality thing: 0001, 0003, 0004, 0005
        # http://www.srf.ch/webservice/picture/videogroup/c60026b7-2ed0-0001-b4b1-1f801a6355d0/0005
        # http://www.srfcdn.ch/piccache/vis/videogroup/c6/00/c60026b7-2ed0-0001-b4b1-1f801a6355d0_0005_w_h_m.jpg
        # item.thumb = "http://www.srf.ch/webservice/picture/videogroup/%s/0005" % (resultSet["id"],)
        item.thumb = "http://www.srfcdn.ch/piccache/vis/videogroup/%s/%s/%s_0005_w_h_m.jpg" \
                     % (result_set["id"][0:2], result_set["id"][2:4], result_set["id"],)

        # item.thumb = resultSet.get("thumbUrl", None)
        # item.thumb = "%s/scale/width/288" % (item.thumb, )  # apparently only the 144 return the correct HEAD info
        # item.fanart = resultSet.get("imageUrl", None)  $# the HEAD will not return a size, so Kodi can't handle it
        item.complete = True
        return item

    def create_episode_item_new(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        url = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/assetSet/listByAssetGroup/%s.json?pageSize=100" % (result_set["id"],)
        item = MediaItem(result_set["title"], url)
        item.description = result_set.get("description", "")
        item.httpHeaders = self.httpHeaders
        item.thumb = self.__get_nested_value(result_set, "Image", "ImageRepresentations", "ImageRepresentation", 0, "url")
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

        :param result_set: The result_set of the self.episodeItemRegex
        :type result_set: list[str]|dict[str,dict[str,dict]]

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        if "fullengthSegment" in result_set and "segment" in result_set["fullengthSegment"]:
            video_id = result_set["fullengthSegment"]["segment"]["id"]
            geo_location = result_set["fullengthSegment"]["segment"]["geolocation"]
            geo_block = False
            if "flags" in result_set["fullengthSegment"]["segment"]:
                geo_block = result_set["fullengthSegment"]["segment"]["flags"].get("geoblock", None)
            Logger.trace("Found geoLocation/geoBlock: %s/%s", geo_location, geo_block)
        else:
            Logger.warning("No video information found.")
            return None

        url = "http://www.srf.ch/player/webservice/videodetail/index?id=%s" % (video_id,)
        item = MediaItem(result_set["titleFull"], url)
        item.type = "video"

        # noinspection PyTypeChecker
        item.thumb = result_set.get("segmentThumbUrl", None)
        # apparently only the 144 return the correct HEAD info
        # item.thumb = "%s/scale/width/288" % (item.thumb, )
        # the HEAD will not return a size, so Kodi can't handle it
        # item.fanart = resultSet.get("imageUrl", None)
        item.description = result_set.get("description", "")

        date_value = str(result_set["time_published"])
        # 2015-01-20 22:17:59"
        date_time = DateHelper.get_date_from_string(date_value, "%Y-%m-%d %H:%M:%S")
        item.set_date(*date_time[0:6])
        item.httpHeaders = self.httpHeaders
        item.complete = False
        return item

    def create_video_item_new(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param result_set: The result_set of the self.episodeItemRegex
        :type result_set: list[str]|dict[str,str]

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        videos = self.__get_nested_value(result_set, "Assets", "Video")
        if not videos:
            Logger.warning("No video information found.")
            return None

        video_infos = [vi for vi in videos if vi["fullLength"]]
        if len(video_infos) > 0:
            video_info = video_infos[0]
        else:
            Logger.warning("No full length video found.")
            return None
        # noinspection PyTypeChecker
        video_id = video_info["id"]

        url = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/video/play/%s.json" % (video_id,)
        item = MediaItem(result_set["title"], url)
        item.type = "video"

        item.thumb = self.__get_nested_value(video_info, "Image", "ImageRepresentations", "ImageRepresentation", 0, "url")
        item.description = self.__get_nested_value(video_info, "AssetMetadatas", "AssetMetadata", 0, "description")

        date_value = str(result_set["publishedDate"])
        date_value = date_value[0:-6]
        # 2015-01-20T22:17:59"
        date_time = DateHelper.get_date_from_string(date_value, "%Y-%m-%dT%H:%M:%S")
        item.set_date(*date_time[0:6])
        item.httpHeaders = self.httpHeaders
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

        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=item.HttpHeaders)
        json = JsonHelper(data)
        video_info = json.get_value("content", "videoInfos")

        part = item.create_new_empty_media_part()
        if "HLSurlHD" in video_info:
            # HLSurlHD=http://srfvodhd-vh.akamaihd.net/i/vod/potzmusig/2015/03/
            # potzmusig_20150307_184438_v_webcast_h264_,q10,q20,q30,q40,q50,q60,.mp4.csmil/master.m3u8
            for s, b in M3u8.get_streams_from_m3u8(video_info["HLSurlHD"], self.proxy):
                item.complete = True
                part.append_media_stream(s, b)
        elif "HLSurl" in video_info:
            # HLSurl=http://srfvodhd-vh.akamaihd.net/i/vod/potzmusig/2015/03/
            # potzmusig_20150307_184438_v_webcast_h264_,q10,q20,q30,q40,.mp4.csmil/master.m3u8
            for s, b in M3u8.get_streams_from_m3u8(video_info["HLSurl"], self.proxy):
                item.complete = True
                part.append_media_stream(s, b)

        if "downloadLink" in video_info:
            # downloadLink=http://podcastsource.sf.tv/nps/podcast/10vor10/2015/03/
            # 10vor10_20150304_215030_v_podcast_h264_q10.mp4
            part.append_media_stream(video_info["downloadLink"], 1000)

        return item

    def update_live_item(self, item):
        """ Updates an existing Live stream MediaItem with more data.

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

        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=item.HttpHeaders)
        json = JsonHelper(data)
        video_play_lists = json.get_value("Video", "Playlists", "Playlist")

        part = item.create_new_empty_media_part()
        for play_list in video_play_lists:
            streams = play_list["url"]
            Logger.trace("Found %s streams", len(streams))
            for stream in streams:
                stream_url = stream["text"]
                if ".m3u8" in stream_url:
                    for s, b in M3u8.get_streams_from_m3u8(stream_url, self.proxy):
                        item.complete = True
                        part.append_media_stream(s, b)
                else:
                    Logger.debug("Cannot use stream url: %s", stream_url)

        # Unused at the moment
        # videoInfo = json.get_value("content", "videoInfos")
        #
        # part = item.create_new_empty_media_part()
        # if "HLSurlHD" in videoInfo:
        #     # HLSurlHD=http://srfvodhd-vh.akamaihd.net/i/vod/potzmusig/2015/03/potzmusig_20150307_184438_v_webcast_h264_,q10,q20,q30,q40,q50,q60,.mp4.csmil/master.m3u8
        #     for s, b in M3u8.get_streams_from_m3u8(videoInfo["HLSurlHD"], self.proxy):
        #         item.complete = True
        #         # s = self.get_verifiable_video_url(s)
        #         part.append_media_stream(s, b)
        # elif "HLSurl" in videoInfo:
        #     # HLSurl=http://srfvodhd-vh.akamaihd.net/i/vod/potzmusig/2015/03/potzmusig_20150307_184438_v_webcast_h264_,q10,q20,q30,q40,.mp4.csmil/master.m3u8
        #     for s, b in M3u8.get_streams_from_m3u8(videoInfo["HLSurl"], self.proxy):
        #         item.complete = True
        #         # s = self.get_verifiable_video_url(s)
        #         part.append_media_stream(s, b)
        #
        # if "downloadLink" in videoInfo:
        #     # downloadLink=http://podcastsource.sf.tv/nps/podcast/10vor10/2015/03/10vor10_20150304_215030_v_podcast_h264_q10.mp4
        #     part.append_media_stream(videoInfo["downloadLink"], 1000)

        return item

    def __get_nested_value(self, dic, *args, **kwargs):
        current_node = dic
        for a in args:
            try:
                current_node = current_node[a]
            except:
                Logger.debug("Value '%s' is not found in '%s'", a, current_node)
                if "fallback" in kwargs:
                    return kwargs["fallback"]
                else:
                    return None
        return current_node
