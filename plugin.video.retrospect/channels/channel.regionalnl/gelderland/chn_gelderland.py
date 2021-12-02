# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class, mediatype, contenttype
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.parserdata import ParserData
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

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "omroepgelderlandimage.png"

        # setup the urls
        self.mainListUri = "https://api.regiogroei.cloud/page/tv/programs"
        self.httpHeaders = {
            "accept": "application/vnd.groei.gelderland+json;v=1.0",
            "x-groei-layout": "wide",
            "x-groei-platform": "web"
        }
        self.baseUrl = "https://api.regiogroei.cloud"
        # https://api.regiogroei.cloud/page/program/83?slug=4daagse-journaal&origin=83

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, name="Mainlist parser", json=True,
                              parser=["components", ("type", "program-list", 0), "items"],
                              preprocessor=self.add_live_streams,
                              creator=self.create_episode_item)

        self._add_data_parser("https://api.regiogroei.cloud/page/program/",
                              name="Show content", json=True,
                              parser=["components", ("type", "episode-list", 0), "items"],
                              creator=self.create_video_item)

        self._add_data_parser("https://api.regiogroei.cloud/page/program/",
                              name="Show content single video", json=True,
                              parser=["components", ("type", "tv-detail-header", 0)],
                              creator=self.create_video_item)

        self._add_data_parser("https://api.regiogroei.cloud/page/channel/",
                              name="Live stream parser", json=True,
                              updater=self.update_live_stream)

        self._add_data_parser("sourceid_string:", match_type=ParserData.MatchContains,
                              updater=self.update_video_item)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def add_live_streams(self, data):
        items = []

        live_title = LanguageHelper.get_localized_string(LanguageHelper.LiveTv)
        live_tv = MediaItem("\b.: {} :.".format(live_title), "https://api.regiogroei.cloud/page/channel/tv-gelderland?channel=tv-gelderland", media_type=mediatype.VIDEO)
        live_tv.dontGroup = True
        items.append(live_tv)

        return data, items

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        # https://api.regiogroei.cloud/page/program/83?slug=4daagse-journaal&origin=83
        url_info = result_set["_links"]["page"]
        url = "{}{}".format(self.baseUrl, url_info["href"])
        item = FolderItem(result_set["programTitle"], url, content_type=contenttype.EPISODES)

        synposis = result_set.get("synopsis")
        description = result_set.get("description")
        if synposis and description:
            item.description = "{}\n\n{}".format(synposis, description)
        elif synposis:
            item.description = synposis
        elif description:
            item.description = description

        # thumbnail=https://images.regiogroei.cloud/[format]/d169259e-0f0a-39b1-824d-a49f3ff7ce34.[ext]?ts=1632764016263
        item.thumb = result_set.get("thumbnail").replace("[format]", "552x310").replace("[ext]", "jpg")
        item.fanart = result_set.get("thumbnail").replace("[format]", "2456x1380").replace("[ext]", "jpg")
        # https://images.regiogroei.cloud/2456x1380/d169259e-0f0a-39b1-824d-a49f3ff7ce34.jpg?ts=1632764312802 2456w
        # https://images.regiogroei.cloud/1104x620/d169259e-0f0a-39b1-824d-a49f3ff7ce34.jpg?ts=1632764312802 1104w
        # https://images.regiogroei.cloud/552x310/d169259e-0f0a-39b1-824d-a49f3ff7ce34.jpg?ts=1632764312802 552w
        # https://images.regiogroei.cloud/264x148/d169259e-0f0a-39b1-824d-a49f3ff7ce34.jpg?ts=1632764312802 264w
        # https://images.regiogroei.cloud/112x64/d169259e-0f0a-39b1-824d-a49f3ff7ce34.jpg?ts=1632764312802 112w

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

        name = result_set["programTitle"]

        # sourceId=sourceid_string:SREGIOOG_96941
        source_id = result_set["sourceId"]
        if "sourceid_string:" in source_id:
            url = "https://omroepgelderland.bbvms.com/p/regiogroei_gelderland_web_videoplayer/c/{}.json".format(source_id)
        else:
            url = "https://omroepgelderland.bbvms.com/p/regiogroei_gelderland_web_videoplayer/c/sourceid_string:{}.json".format(source_id)

        item = MediaItem(name, url, media_type=mediatype.EPISODE)
        item.description = result_set.get("synopsis")
        item.thumb = result_set.get("thumbnail").replace("[format]", "552x310").replace("[ext]", "jpg")

        # id=3a13d646-fcbc-5882-be5b-55683aed1781
        # displayId=48178

        # scheduleStart=2020-07-24T15:20:00Z
        time_stamp = DateHelper.get_date_from_string(
            result_set["scheduleStart"], "%Y-%m-%dT%H:%M:%SZ")
        item.set_date(*time_stamp[0:6])
        return item

    def update_live_stream(self, item):
        """ Updates an live stream item

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

        data = UriHandler.open(item.url, additional_headers=self.httpHeaders)
        json_data = JsonHelper(data)
        live_stream_id = json_data.get_value("components", 0, "channel", "livestreamId")
        url = "https://omroepgelderland.bbvms.com/p/regiogroei_gelderland_web_videoplayer/c/{}.json".format(live_stream_id)
        item.url = url
        return self.update_video_item(item)

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

        data = UriHandler.open(item.url)
        json_data = JsonHelper(data)

        clip_data = json_data.get_value("clipData", "assets")
        server = json_data.get_value("publicationData", "defaultMediaAssetPath")
        for clip in clip_data:
            url = clip["src"]
            if not url.startswith("http"):
                url = "{}{}".format(server, clip["src"])
            item.add_stream(url, int(clip["bandwidth"] or 1))
            item.complete = True

        return item
