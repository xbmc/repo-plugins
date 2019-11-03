# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.logger import Logger
from resources.lib.regexer import Regexer
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData
from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.datehelper import DateHelper
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

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = "rtbfimage.png"

        # setup the urls
        self.mainListUri = "https://www.rtbf.be/auvio/emissions"
        self.baseUrl = "https://www.rtbf.be"

        # setup the main parsing data
        episode_regex = r'<article[^>]+data-id="(?<id>(?<url>\d+))"[^>]*>\W+<figure[^>]+>\W+' \
                        r'<figcaption[^>]+>(?<title>[^{][^<]+)</figcaption>\W*<div[^>]*>\W*' \
                        r'<img[^>]*(?<thumburl>http[^"]+) \d+w"'
        episode_regex = Regexer.from_expresso(episode_regex)
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              preprocessor=self.add_category_and_live_items,
                              parser=episode_regex,
                              creator=self.create_episode_item)

        self._add_data_parser("http://www.rtbf.be/news/api/menu?site=media", json=True,
                              match_type=ParserData.MatchExact,
                              parser=["item", 3, "item"], creator=self.create_category)

        live_regex = r'<img[^>]*(?<thumburl>http[^"]+) \d+w"[^>]*>[\w\W]{0,1000}Maintenant' \
                     r'</span> (?:sur )?(?<channel>[^>]+)</div>\W*<h3[^>]*>\W*<a[^>]+href="' \
                     r'(?<url>[^"]+=(?<liveId>\d+))"[^>]+title="(?<title>[^"]+)'
        live_regex = Regexer.from_expresso(live_regex)
        self._add_data_parser("https://www.rtbf.be/auvio/direct/",
                              parser=live_regex,
                              creator=self.create_video_item)

        self._add_data_parser("https://www.rtbf.be/auvio/embed/direct",
                              updater=self.update_live_item)

        video_regex = r'<img[^>]*alt="(?<title>[^"]+)"[^>]*(?<thumburl>http[^"]+) \d+w"[^>]*>' \
                      r'[\w\W]{0,1000}?<h4[^>]+>\W+<a[^>]+href="(?<url>[^<"]+=(?<videoId>\d+))"' \
                      r'[^>]*>[^<]*</a>\W*</h4>\W*(?:<h5[^>]+>(?<description>[^<]*)</h5>|<div)' \
                      r'[\w\W]{0,1000}?<time[^>]+datetime="(?<date>[^"]+)"'
        video_regex = Regexer.from_expresso(video_regex)
        self._add_data_parser("*", parser=video_regex, creator=self.create_video_item,
                              updater=self.update_video_item)

        self.pageNavigationRegexIndex = 1
        page_regex = r'<li class="(?:|[^a][^"]+)">\W+<a class="rtbf-pagination__link" ' \
                     r'href="([^"]+&p=)(\d+)"'
        self._add_data_parser("*", parser=page_regex, creator=self.create_page_item)

        self.swfUrl = "http://www.static.rtbf.be/rtbf/embed/js/vendor/jwplayer/jwplayer.flash.swf"
        # ==========================================================================================
        # Test cases:
        # 5@7

        # ====================================== Actual channel setup STOPS here ===================
        return

    def add_category_and_live_items(self, data):
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

        sub_items = {
            "\a.: Direct :.": "%s/auvio/direct/" % (self.baseUrl, ),
            "\a.: Cat&eacute;gories :.": "http://www.rtbf.be/news/api/menu?site=media"
        }

        for k, v in sub_items.items():
            item = MediaItem(k, v)
            item.complete = True
            item.dontGroup = True
            items.append(item)
            item.isLive = v.endswith('/direct/')

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

        item = chn_class.Channel.create_episode_item(self, result_set)
        if item is None:
            return item

        item.url = "%s/auvio/archives?pid=%s&contentType=complete" % (self.baseUrl, result_set["id"])
        return item

    def create_category(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set[str,any]: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        result_set = result_set["@attributes"]
        Logger.trace(result_set)
        # http://www.rtbf.be/auvio/archives?caid=29&contentType=complete,extract,bonus
        # {
        # u'url': u'http://www.rtbf.be/auvio/categorie/sport/football?id=11',
        # u'expandorder': u'6', u'aliases': u'football', u'id': u'category-11',
        # u'name': u'Football'
        # }
        cid = result_set["id"].split("-")[-1]
        url = "%s/auvio/archives?caid=%s&contentType=complete,extract,bonus" % (self.baseUrl, cid)
        item = MediaItem(result_set["name"], url)
        item.complete = True
        return item

    # Not used for now:
    # def create_live_channel_item(self, result_set):
    #     item = chn_class.Channel.create_episode_item(self, result_set)
    #     if item is None:
    #         return item
    #
    #     item.url = "%s/auvio/archives?pid=%s&contentType=complete" % (self.baseUrl, result_set["id"])
    #     return item

    def create_page_item(self, result_set):
        """ Creates a MediaItem of type 'page' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'page'.
        :rtype: MediaItem|None

        """

        item = chn_class.Channel.create_page_item(self, result_set)
        url = "%s/auvio/archives%s%s" % (self.baseUrl, HtmlEntityHelper.url_decode(result_set[0]), result_set[1])
        item.url = url
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

        item = chn_class.Channel.create_video_item(self, result_set)
        if item is None:
            return item

        # http://www.rtbf.be/auvio/embed/media?id=2101078&autoplay=1
        if "videoId" in result_set:
            item.url = "%s/auvio/embed/media?id=%s" % (self.baseUrl, result_set["videoId"])
        elif "liveId" in result_set:
            item.name = "%s - %s" % (result_set["channel"].strip(), item.name)
            item.url = "%s/auvio/embed/direct?id=%s" % (self.baseUrl, result_set["liveId"])
            item.isLive = True

        if "date" in result_set:
            # 2016-05-14T20:00:00+02:00 -> strip the hours
            time_stamp = DateHelper.get_date_from_string(
                result_set["date"].rsplit("+")[0], "%Y-%m-%dT%H:%M:%S")
            item.set_date(*time_stamp[0:6])

        return item

    def update_video_item(self, item):
        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=item.HttpHeaders)
        media_regex = 'data-media="([^"]+)"'
        media_info = Regexer.do_regex(media_regex, data)[0]
        media_info = HtmlEntityHelper.convert_html_entities(media_info)
        media_info = JsonHelper(media_info)
        Logger.trace(media_info)

        # sources
        part = item.create_new_empty_media_part()
        # high, web, mobile, url
        media_sources = media_info.json.get("sources", {})
        for quality in media_sources:
            url = media_sources[quality]
            if quality == "high":
                bitrate = 2000
            elif quality == "web":
                bitrate = 800
            elif quality == "mobile":
                bitrate = 400
            else:
                bitrate = 0
            part.append_media_stream(url, bitrate)

        # geoLocRestriction
        item.isGeoLocked = not media_info.get_value("geoLocRestriction", fallback="world") == "world"
        item.complete = True
        return item

    def update_live_item(self, item):
        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=item.HttpHeaders)
        media_regex = 'data-media="([^"]+)"'
        media_info = Regexer.do_regex(media_regex, data)[0]
        media_info = HtmlEntityHelper.convert_html_entities(media_info)
        media_info = JsonHelper(media_info)
        Logger.trace(media_info)
        part = item.create_new_empty_media_part()

        hls_url = media_info.get_value("streamUrl")
        if hls_url is not None and "m3u8" in hls_url:
            Logger.debug("Found HLS url for %s: %s", media_info.json["streamName"], hls_url)

            for s, b in M3u8.get_streams_from_m3u8(hls_url, self.proxy):
                part.append_media_stream(s, b)
                item.complete = True
        else:
            Logger.debug("No HLS url found for %s. Fetching RTMP Token.", media_info.json["streamName"])
            # fetch the token:
            token_url = "%s/api/media/streaming?streamname=%s" \
                        % (self.baseUrl, media_info.json["streamName"])

            token_data = UriHandler.open(token_url, proxy=self.proxy,
                                         additional_headers=item.HttpHeaders, no_cache=True)

            token_data = JsonHelper(token_data)
            token = token_data.get_value("token")
            Logger.debug("Found token '%s' for '%s'", token, media_info.json["streamName"])

            rtmp_url = "rtmp://rtmp.rtbf.be/livecast/%s?%s pageUrl=%s tcUrl=rtmp://rtmp.rtbf.be/livecast" \
                       % (media_info.json["streamName"], token, self.baseUrl)
            rtmp_url = self.get_verifiable_video_url(rtmp_url)
            part.append_media_stream(rtmp_url, 0)
            item.complete = True

        item.isGeoLocked = not media_info.get_value("geoLocRestriction", fallback="world") == "world"
        return item
