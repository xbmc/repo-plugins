# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper


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

        # setup the urls
        self.swfUrl = "http://media.mtvnservices.com/player/prime/mediaplayerprime.1.12.5.swf"
        if self.channelCode == "southpark.se":
            self.noImage = "southparkimage.png"
            self.mainListUri = "http://www.southparkstudios.se/full-episodes/"
            self.baseUrl = "http://www.southparkstudios.se"
            self.promotionId = None
        else:
            self.noImage = "southparkimage.png"
            self.mainListUri = "http://www.southpark.nl/episodes/"
            self.baseUrl = "http://www.southpark.nl"

        # setup the main parsing data
        self.episodeItemRegex = r'(?:data-promoId="([^"]+)"|<li[^>]*>\W*<a[^>]+href="([^"]+episodes/season[^"]+)">(\d+)</a>)'  # used for the ParseMainList
        self.videoItemRegex = r'(\{[^}]+)'

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        if not result_set[0] == "":
            self.promotionId = result_set[0]
            Logger.debug("Setting PromotionId to: %s", result_set[0])
            return None

        # <li><a href="(/guide/season/[^"]+)">(\d+)</a></li>
        # if (self.channelCode == "southpark"):
        #    url = "%s/ajax/seasonepisode/%s" % (self.baseUrl, result_set[2])
        #    url = http://www.southpark.nl/feeds/full-episode/carousel/14/424b7b57-e459-4c9c-83ca-9b924350e94d
        # else:
        url = "%s/feeds/full-episode/carousel/%s/%s" % (self.baseUrl, result_set[2], self.promotionId)

        item = MediaItem("Season %02d" % int(result_set[2]), url)
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

        # Logger.Debug(result_set)

        # data = result_set.replace('" : "', '":"').replace("\\'", "'")
        # helper = jsonhelper.JsonHelper(data)
        #
        # episodeNumber = helper.GetNamedValue("episodenumber")
        # episodeId = helper.GetNamedValue("id")
        #
        # # http://www.southpark.nl/feeds/video-player/mrss/mgid%3Aarc%3Aepisode%3Asouthpark.nl%3Abcc6a626-c98d-4390-9d7c-1d1233d4df1f?lang={lang}
        # interPart = "feeds/video-player/mrss/mgid%3Aarc%3Aepisode%3Asouthpark.nl%3A"
        # url = "%s/%s%s?lang={lang}" % (self.baseUrl, interPart, episodeId)
        #
        # title = "%s (%s)" % (helper.GetNamedValue("title"), episodeNumber)
        #
        # item = MediaItem(title, url)
        # item.thumb = helper.GetNamedValue("thumbnail_190")
        # item.description = helper.GetNamedValue("description")
        # item.type = 'video'
        # item.complete = False
        #
        # date = helper.GetNamedValue("airdate")
        # Logger.Trace(date)
        # year = int(date[6:8])
        # if year > 80:
        #     year = "19%s" % (year,)
        # else:
        #     year = "20%s" % (year,)
        # day = date[0:2]
        # month = date[3:5]
        # item.set_date(year, month, day)
        #
        # return item

        # json that comes here, sucks!
        return None

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

        # 1 - get the overal config file
        guid_regex = 'http://[^:]+/mgid:[^"]+:([0-9a-f-]+)"'
        rtmp_regex = r'type="video/([^"]+)" bitrate="(\d+)">\W+<src>([^<]+)</src>'

        data = UriHandler.open(item.url, proxy=self.proxy)
        guids = Regexer.do_regex(guid_regex, data)

        item.MediaItemParts = []
        for guid in guids:
            # get the info for this part
            Logger.debug("Processing part with GUID: %s", guid)

            # reset stuff
            part = None

            # http://www.southpark.nl/feeds/video-player/mediagen?uri=mgid%3Aarc%3Aepisode%3Acomedycentral.com%3Aeb2a53f7-e370-4049-a6a9-57c195367a92&suppressRegisterBeacon=true
            guid = HtmlEntityHelper.url_encode("mgid:arc:episode:comedycentral.com:%s" % (guid,))
            info_url = "%s/feeds/video-player/mediagen?uri=%s&suppressRegisterBeacon=true" % (self.baseUrl, guid)

            # 2- Get the GUIDS for the different ACTS
            info_data = UriHandler.open(info_url, proxy=self.proxy)
            rtmp_streams = Regexer.do_regex(rtmp_regex, info_data)

            for rtmp_stream in rtmp_streams:
                # if this is the first stream for the part, create an new part
                if part is None:
                    part = item.create_new_empty_media_part()

                part.append_media_stream(self.get_verifiable_video_url(rtmp_stream[2]), rtmp_stream[1])

        item.complete = True
        Logger.trace("Media item updated: %s", item)
        return item
