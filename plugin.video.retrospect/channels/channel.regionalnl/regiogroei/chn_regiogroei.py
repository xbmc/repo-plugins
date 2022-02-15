# SPDX-License-Identifier: GPL-3.0-or-later
import datetime

import pytz

from resources.lib import chn_class, mediatype, contenttype
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.parserdata import ParserData
from resources.lib.logger import Logger
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    THIS CHANNEL IS BASED ON THE PEPERZAKEN APPS FOR ANDROID
    """

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        self.liveUrl = None  # : the live url if present
        self.mainListUri = "https://api.regiogroei.cloud/page/tv/programs"
        self.baseUrl = "https://api.regiogroei.cloud"
        self.__timezone = pytz.timezone("Europe/Amsterdam")
        self.httpHeaders = {
            "x-groei-layout": "wide",
            "x-groei-platform": "web",
            # "accept": "application/vnd.groei.utrecht+json;v=2.0"
        }

        if self.channelCode == "rtvutrecht":
            self.mainListUri = "https://api.regiogroei.cloud/page/tv/programs?utrecht"
            self.noImage = "rtvutrechtimage.png"
            self.videoUrlFormat = "https://rtvutrecht.bbvms.com/p/regiogroei_utrecht_web_videoplayer/c/{}.json"
            self.recentSlug = "rtvutrecht"
            self.liveUrl = "https://api.regiogroei.cloud/page/channel/rtv-utrecht?channel=rtv-utrecht"
            self.httpHeaders["accept"] = "application/vnd.groei.utrecht+json;v=2.0"

        elif self.channelCode == "omroepzeeland":
            self.mainListUri = "https://api.regiogroei.cloud/page/tv/programs?zeeland"
            self.noImage = "omroepzeelandimage.png"
            self.videoUrlFormat = "https://omroepzeeland.bbvms.com/p/regiogroei_zeeland_web_videoplayer/c/{}.json"
            self.recentSlug = "omroep-zeeland-tv"
            self.liveUrl = "https://api.regiogroei.cloud/page/channel/omroep-zeeland-tv?channel=omroep-zeeland-tv"
            self.httpHeaders["accept"] = "application/vnd.groei.zeeland+json;v=2.0"

        elif self.channelCode == "rtvnoord":
            self.mainListUri = "https://api.regiogroei.cloud/page/tv/programs?noord"
            self.noImage = "rtvnoordimage.png"
            self.videoUrlFormat = "https://rtvnoord.bbvms.com/p/regiogroei_web_videoplayer/c/{}.json"
            self.recentSlug = "tv-noord"
            self.httpHeaders["accept"] = "application/vnd.groei.groningen+json;v=2.0"
            self.liveUrl = "https://api.regiogroei.cloud/page/channel/tv-noord?channel=tv-noord"

        elif self.channelCode == "rtvrijnmond":
            self.mainListUri = "https://api.regiogroei.cloud/page/tv/programs?rijnmond"
            self.noImage = "rtvrijnmondimage.png"
            self.videoUrlFormat = "https://rijnmond.bbvms.com/p/regiogroei_rijnmond_web_videoplayer/c/{}.json"
            self.recentSlug = "tv-rijnmond"
            self.httpHeaders["accept"] = "application/vnd.groei.zh-rijnmond+json;v=3.0"
            self.liveUrl = "https://api.regiogroei.cloud/page/channel/tv-rijnmond?channel=tv-rijnmond"

        elif self.channelCode == "omroepwest":
            self.mainListUri = "https://api.regiogroei.cloud/page/tv/programs"
            self.noImage = "omroepwestimage.png"
            self.videoUrlFormat = "https://omroepwest.bbvms.com/p/regiogroei_west_web_videoplayer/c/{}.json"
            self.recentSlug = "tv-west"
            self.httpHeaders["accept"] = "application/vnd.groei.zh-west+json;v=3.0"
            self.liveUrl = "https://api.regiogroei.cloud/page/channel/tv-west?channel=tv-west"

        elif self.channelCode == "omroepgelderland":
            self.mainListUri = "https://api.regiogroei.cloud/page/tv/programs?omroepgelderland"
            self.noImage = "omroepgelderlandimage.png"
            self.videoUrlFormat = "https://omroepgelderland.bbvms.com/p/regiogroei_gelderland_web_videoplayer/c/{}.json"
            self.recentSlug = "tv-gelderland"
            self.httpHeaders["accept"] = "application/vnd.groei.gelderland+json;v=3.0"
            self.liveUrl = "https://api.regiogroei.cloud/page/channel/tv-gelderland?channel=tv-gelderland"

        elif self.channelCode == "rtvoost":
            self.mainListUri = "https://api.regiogroei.cloud/page/tv/programs?rtvoost"
            self.noImage = "omroepgelderlandimage.png"
            self.videoUrlFormat = "https://rtvoost.bbvms.com/p/regiogroei_oost_web_videoplayer/c/{}.json"
            self.recentSlug = "tv-oost"
            self.httpHeaders["accept"] = "application/vnd.groei.overijssel+json;v=3.0"
            self.liveUrl = "https://api.regiogroei.cloud/page/channel/tv-oost?channel=tv-oost"

        else:
            raise NotImplementedError("Channelcode '%s' not implemented" % (self.channelCode,))

        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              name="Mainlist parser",
                              preprocessor=self.add_week_overview,
                              parser=["components", ("type", "program-list", 0), "items"],
                              creator=self.create_program_item)

        self._add_data_parser("#recent", name="Recent items list", preprocessor=self.add_recent_items)

        self._add_data_parser("https://api.regiogroei.cloud/page/program", json=True,
                              name="Videos for show parsers",
                              parser=["components", ("type", "episode-list", 0), "items"],
                              creator=self.create_video_item)

        self._add_data_parser("*", updater=self.update_video_item)

        self._add_data_parser("https://api.regiogroei.cloud/programs/.+?startDate", json=True,
                              match_type=ParserData.MatchRegex,
                              name="TV Guide parser",
                              parser=[], creator=self.create_epg_item)

        # ===============================================================================================================
        # non standard items

        # ===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def add_week_overview(self, data):
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
        title = "\a .: {} :.".format(LanguageHelper.get_localized_string(LanguageHelper.Recent))
        recent = FolderItem(
            title, "#recent",
            content_type=contenttype.EPISODES)
        recent.complete = True
        recent.dontGroup = True

        items.append(recent)
        return data, items

    def add_recent_items(self, data):
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
        today = datetime.datetime.now() - datetime.timedelta(hours=5)
        days = LanguageHelper.get_days_list()
        for i in range(0, 7, 1):
            air_date = today - datetime.timedelta(i)
            day_after = air_date + datetime.timedelta(days=1)
            Logger.trace("Adding item for: %s", air_date)

            # Determine a nice display date
            day = days[air_date.weekday()]
            if i == 0:
                day = LanguageHelper.get_localized_string(LanguageHelper.Today)
            elif i == 1:
                day = LanguageHelper.get_localized_string(LanguageHelper.Yesterday)
            # elif i == 2:
            #     day = LanguageHelper.get_localized_string(LanguageHelper.DayBeforeYesterday)
            title = "{:04d}-{:02d}-{:02d} - {}".format(air_date.year, air_date.month, air_date.day, day)

            url = "{}/programs/{}?startDate={:04d}-{:02d}-{:02d}&endDate={:04d}-{:02d}-{:02d}"\
                .format(
                    self.baseUrl,
                    self.recentSlug,
                    air_date.year, air_date.month, air_date.day,
                    day_after.year, day_after.month, day_after.day
                )

            extra = FolderItem(title, url, content_type=contenttype.EPISODES)
            extra.complete = True
            extra.dontGroup = True
            extra.set_date(air_date.year, air_date.month, air_date.day, text="")
            items.append(extra)

        # Live
        if self.liveUrl:
            title = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
            live = MediaItem(title, self.liveUrl, media_type=mediatype.VIDEO)
            live.HttpHeaders = self.httpHeaders
            live.isLive = True
            items.append(live)

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_program_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """
        Logger.trace(result_set)

        title = result_set["programTitle"]
        desc = result_set["description"]
        thumb = result_set.get("thumbnail")
        base = result_set["_links"]["page"]["href"]
        slug = result_set["_links"]["web"]["slug"]
        origin = result_set["_links"]["web"]["originId"]
        url = "{}{}?slug={}&origin={}".format(self.baseUrl, base, slug, origin)

        item = FolderItem(title, url, content_type=contenttype.EPISODES, media_type=mediatype.TVSHOW)
        item.description = desc
        item.thumb = self._get_thumb(thumb)
        # item.poster = thumb.replace("[format]", "1000x1500").replace("[ext]", "jpg")

        return item

    def create_epg_item(self, result_set):
        item = self.create_video_item(result_set, epg_item=True)
        return item

    def create_video_item(self, result_set, epg_item=False):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict result_set: The result_set of the self.episodeItemRegex
        :param bool epg_item: format as an EPG item.

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        availabe = result_set["available"]
        if not availabe:
            return None

        program_title = result_set["programTitle"]
        episode_title = result_set["episodeTitle"]
        url = "{}{}".format(self.baseUrl, result_set["_links"]["page"]["href"])

        item = MediaItem(episode_title or program_title, url, media_type=mediatype.EPISODE)
        item.description = result_set.get("synopsis")
        item.HttpHeaders = self.httpHeaders
        item.thumb = self._get_thumb(result_set["thumbnail"])

        # '2021-08-28T06:00:00Z'
        broadcasted = result_set["scheduleStart"]
        date_time = DateHelper.get_datetime_from_string(broadcasted, date_format="%Y-%m-%dT%H:%M:%SZ", time_zone="UTC")
        date_time = date_time.astimezone(self.__timezone)
        item.set_date(date_time.year, date_time.month, date_time.day,
                      date_time.hour, date_time.minute, date_time.second)
        if epg_item:
            if episode_title and program_title:
                item.name = "{:02d}:{:02d} - {} - {}".format(date_time.hour, date_time.minute,
                                                             program_title, episode_title)
            else:
                item.name = "{:02d}:{:02d} - {}".format(date_time.hour, date_time.minute,
                                                        item.title)

        item.complete = False
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

        # Just double check.
        if not item.HttpHeaders:
            item.HttpHeaders = self.httpHeaders

        data = UriHandler.open(item.url, additional_headers=item.HttpHeaders)
        # extract the source_id:
        json_data = JsonHelper(data)
        source_id = None
        for c in json_data.get_value("components"):
            if c["type"] == "tv-detail-header":
                source_id = c["sourceId"]
                break

        if not source_id:
            Logger.error("Unable to extract source_id")

        source_url = self.videoUrlFormat.format(source_id)
        data = UriHandler.open(source_url)
        json_data = JsonHelper(data)
        base_url = json_data.get_value("publicationData", "defaultMediaAssetPath")
        clip_data = json_data.get_value("clipData", "assets")

        for clip in clip_data:
            video_url = clip["src"]
            if not video_url.startswith("http"):
                video_url = "{}{}".format(base_url, video_url)

            bitrate = clip["bandwidth"] or "0"
            if bitrate.lower() == "auto":
                bitrate = 4000

            media_type = clip["mediatype"].lower()
            # Should we resolve the actual urls?
            # _, video_url = UriHandler.header(video_url)

            if "m3u8" in video_url:
                item.complete = M3u8.update_part_with_m3u8_streams(item, video_url, bitrate=bitrate)

            elif media_type.startswith("mp4_"):
                item.add_stream(video_url, bitrate=bitrate)
                item.complete = True

            else:
                Logger.error("Unsupported stream for %s from url: %s", item, video_url)

        item.isLive = json_data.get_value("clipData", "sourcetype") == "live"
        return item

    def _get_thumb(self, thumb):
        return thumb.replace("[format]", "1104x620").replace("[ext]", "jpg")
