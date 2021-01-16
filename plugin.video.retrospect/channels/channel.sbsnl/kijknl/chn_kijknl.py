# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import pytz

from resources.lib import chn_class, contenttype
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.subtitlehelper import SubtitleHelper

from resources.lib.mediaitem import MediaItem
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.mpd import Mpd
from resources.lib.regexer import Regexer
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.addonsettings import AddonSettings
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
        # setup the urls
        self.baseUrl = "https://www.kijk.nl"

        if self.channelCode is None:
            self.noImage = "kijkimage.jpg"
            self.poster = "kijkposter.jpg"
            self.mainListUri = self.__get_api_query_url(
                "programs(programTypes:[SERIES],limit:1000)",
                "{items{__typename,title,description,guid,updated,seriesTvSeasons{id},"
                "imageMedia{url,label}}}")

            self._add_data_parser("#recentgraphql", preprocessor=self.add_graphql_recents,
                                  name="GraphQL Recent listing")

            self._add_data_parser("https://graph.kijk.nl/graphql?query=query%7Bprograms%28programTypes",
                                  name="Main GraphQL Program parser", json=True,
                                  preprocessor=self.add_graphql_extras,
                                  parser=["data", "programs", "items"], creator=self.create_api_typed_item)

            self._add_data_parser("https://graph.kijk.nl/graphql?query=query%7Bprograms%28guid",
                                  name="Main GraphQL season overview parser", json=True,
                                  parser=["data", "programs", "items", 0, "seriesTvSeasons"],
                                  creator=self.create_api_tvseason_type)

            self._add_data_parser("https://graph.kijk.nl/graphql?query=query%7BprogramsByDate",
                                  name="Main GraphQL programs per date parser", json=True,
                                  parser=["data", "programsByDate", 0, "items"],
                                  creator=self.create_api_typed_item)

            self._add_data_parser("https://graph.kijk.nl/graphql?query=query%7BtrendingPrograms",
                                  name="GraphQL trending parser", json=True,
                                  parser=["data", "trendingPrograms"],
                                  creator=self.create_api_typed_item)

            self._add_data_parsers(["https://graph.kijk.nl/graphql?operationName=programs",
                                    "https://graph.kijk.nl/graphql?query=query%7Bprograms%28tvSeasonId"],
                                   name="GraphQL season video listing parsing", json=True,
                                   parser=["data", "programs", "items"],
                                   creator=self.create_api_typed_item)

            self._add_data_parser("https://graph.kijk.nl/graphql?query=query%7Bsearch",
                                  name="GraphQL search", json=True,
                                  parser=["data", "search", "items"], creator=self.create_api_typed_item)

            self._add_data_parser("https://graph.kijk.nl/graphql-video",
                                  updater=self.update_graphql_item)

            self._add_data_parser("https://graph.kijk.nl/graphql?operationName=programs",
                                  updater=self.update_graphql_item)

        else:
            raise ValueError("Channel with code '{}' not supported".format(self.channelCode))

        # setup the main parsing data
        self._add_data_parser("#lastweek",
                              name="Last week listing", json=True,
                              preprocessor=self.list_dates)

        self._add_data_parser("https://embed.kijk.nl/",
                              updater=self.update_json_video_item)

        #===============================================================================================================
        # non standard items
        self.__video_fields = \
            "{items{__typename,title,description,guid,updated,seriesTvSeasons{id}," \
            "imageMedia{url,label},type,sources{type,drm,file},series{title}," \
            "seasonNumber,tvSeasonEpisodeNumber,lastPubDate,duration,displayGenre,tracks{type,file}}}"
        self.__list_limit = 150
        self.__timezone = pytz.timezone("Europe/Amsterdam")
        self.__timezone_utc = pytz.timezone("UTC")

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        UriHandler.set_cookie(name="OPTOUTMULTI", value="0:0%7Cc5:0%7Cc1:0%7Cc4:0%7Cc3:0%7Cc2:0", domain=".kijk.nl")
        return

    # noinspection PyUnusedLocal
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

        url = self.__get_api_query_url(
            "search(searchParam:\"----\",programTypes:[SERIES,EPISODE],limit:50)",
            "{items{__typename,title,description,guid,updated,seriesTvSeasons{id},"
            "imageMedia{url,label},type,sources{type,file,drm},seasonNumber,"
            "tvSeasonEpisodeNumber,series{title},lastPubDate}}"
        ).replace("%", "%%").replace("----", "%s")
        return chn_class.Channel.search_site(self, url)

    def list_dates(self, data):
        """ Generates a list of the past week days.

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

        # https://api.kijk.nl/v2/templates/page/missed/all/20180201
        days = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        for i in range(0, 7):
            date = datetime.datetime.now() - datetime.timedelta(days=i)
            # https://api.kijk.nl/v2/templates/page/missed/all/20180626
            # url = "https://api.kijk.nl/v2/templates/page/missed/all/{0}{1:02d}{2:02d}".format(date.year, date.month, date.day)
            # https://api.kijk.nl/v1/default/sections/missed-all-20180619
            url = "https://api.kijk.nl/v1/default/sections/missed-all-{0}{1:02d}{2:02d}".format(date.year, date.month, date.day)
            if i == 0:
                title = LanguageHelper.get_localized_string(LanguageHelper.Today)
            elif i == 1:
                title = LanguageHelper.get_localized_string(LanguageHelper.Yesterday)
            elif i == 2:
                title = LanguageHelper.get_localized_string(LanguageHelper.DayBeforeYesterday)
            else:
                day_name = days[date.weekday()]
                title = day_name

            date_item = MediaItem(title, url)
            date_item.set_date(date.year, date.month, date.day)
            items.append(date_item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def update_json_video_item(self, item):
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

        headers = {"accept": "application/vnd.sbs.ovp+json; version=2.0"}
        data = UriHandler.open(item.url, additional_headers=headers)

        if UriHandler.instance().status.code == 404:
            Logger.warning("No normal stream found. Trying newer method")
            new_url = item.url.replace("https://embed.kijk.nl/api/", "https://embed.kijk.nl/")
            item.url = new_url[:new_url.index("?")]
            return self.__update_embedded_video(item)

        json = JsonHelper(data)
        embed_url = json.get_value("metadata", "embedURL")
        if embed_url:
            Logger.warning("Embed URL found. Using that to determine the streams.")
            item.url = embed_url
            try:
                return self.__update_embedded_video(item)
            except:
                Logger.warning("Failed to update embedded item:", exc_info=True)

        use_adaptive_with_encryption = AddonSettings.use_adaptive_stream_add_on(with_encryption=True, channel=self)
        mpd_info = json.get_value("entitlements", "play")

        # is there MPD information in the API response?
        if mpd_info is not None:
            return self.__update_video_from_mpd(item, mpd_info, use_adaptive_with_encryption)

        # Try the plain M3u8 streams
        part = item.create_new_empty_media_part()
        m3u8_url = json.get_value("playlist")
        use_adaptive = AddonSettings.use_adaptive_stream_add_on(channel=self)

        # with the Accept: application/vnd.sbs.ovp+json; version=2.0 header, the m3u8 streams that
        # are brightcove based have an url parameter instead of an empty m3u8 file
        Logger.debug("Trying standard M3u8 streams.")
        if m3u8_url != "https://embed.kijk.nl/api/playlist/.m3u8" \
                and "hostingervice=brightcove" not in m3u8_url:
            for s, b in M3u8.get_streams_from_m3u8(m3u8_url, append_query_string=True):
                if "_enc_" in s:
                    continue

                if use_adaptive:
                    # we have at least 1 none encrypted streams
                    Logger.info("Using HLS InputStreamAddon")
                    strm = part.append_media_stream(m3u8_url, 0)
                    M3u8.set_input_stream_addon_input(strm)
                    item.complete = True
                    return item

                part.append_media_stream(s, b)
                item.complete = True
            return item

        Logger.warning("No M3u8 data found. Falling back to BrightCove")
        video_id = json.get_value("vpakey")
        # videoId = json.get_value("videoId") -> Not all items have a videoId
        mpd_manifest_url = "https://embed.kijk.nl/video/%s?width=868&height=491" % (video_id,)
        referer = "https://embed.kijk.nl/video/%s" % (video_id,)

        data = UriHandler.open(mpd_manifest_url, referer=referer)
        # First try to find an M3u8
        m3u8_urls = Regexer.do_regex('https:[^"]+.m3u8', data)
        for m3u8_url in m3u8_urls:
            m3u8_url = m3u8_url.replace("\\", "")

            # We need the actual URI to make this work, so fetch it.
            m3u8_url = UriHandler.header(m3u8_url)[-1]
            Logger.debug("Found direct M3u8 in brightcove data.")
            if use_adaptive:
                # we have at least 1 none encrypted streams
                Logger.info("Using HLS InputStreamAddon")
                strm = part.append_media_stream(m3u8_url, 0)
                M3u8.set_input_stream_addon_input(strm)
                item.complete = True
                return item

            for s, b in M3u8.get_streams_from_m3u8(m3u8_url, append_query_string=True):
                item.complete = True
                part.append_media_stream(s, b)

            return item

        return self.__update_video_from_brightcove(item, data, use_adaptive_with_encryption)

    def __update_embedded_video(self, item):
        """ Updates video items that are encrypted. This could be the default for Krypton!

        :param MediaItem item: The item to update.

        :return: An updated item.
        :rtype: MediaItem

        """

        data = UriHandler.open(item.url)
        if UriHandler.instance().status.code == 404:
            title, message = Regexer.do_regex(r'<h1>([^<]+)</h1>\W+<p>([^<]+)<', data)[0]
            XbmcWrapper.show_dialog(title, message)
            return item

        start_needle = "var playerConfig ="
        start_data = data.index(start_needle) + len(start_needle)
        end_data = data.index("var talpaPlayer")
        data = data[start_data:end_data].strip().rstrip(";")

        json = JsonHelper(data)
        has_drm_only = True
        adaptive_available = AddonSettings.use_adaptive_stream_add_on(with_encryption=False, channel=self)
        adaptive_available_encrypted = AddonSettings.use_adaptive_stream_add_on(with_encryption=True, channel=self)

        for play_list_entry in json.get_value("playlist"):
            part = item.create_new_empty_media_part()
            for source in play_list_entry["sources"]:
                stream_type = source["type"]
                stream_url = source["file"]
                stream_drm = source.get("drm")

                if not stream_drm:
                    has_drm_only = False
                    if stream_type == "m3u8":
                        Logger.debug("Found non-encrypted M3u8 stream: %s", stream_url)
                        M3u8.update_part_with_m3u8_streams(part, stream_url, channel=self)
                        item.complete = True
                    elif stream_type == "dash" and adaptive_available:
                        Logger.debug("Found non-encrypted Dash stream: %s", stream_url)
                        stream = part.append_media_stream(stream_url, 1)
                        Mpd.set_input_stream_addon_input(stream)
                        item.complete = True
                    else:
                        Logger.debug("Unknown stream source: %s", source)

                else:
                    compatible_drm = "widevine"
                    if compatible_drm not in stream_drm or stream_type != "dash":
                        Logger.debug("Found encrypted %s stream: %s", stream_type, stream_url)
                        continue

                    Logger.debug("Found Widevine encrypted Dash stream: %s", stream_url)
                    license_url = stream_drm[compatible_drm]["url"]
                    pid = stream_drm[compatible_drm]["releasePid"]
                    encryption_json = '{"getRawWidevineLicense":' \
                                      '{"releasePid":"%s", "widevineChallenge":"b{SSM}"}' \
                                      '}' % (pid,)

                    headers = {
                        "Content-Type": "application/json",
                        "Origin": "https://embed.kijk.nl",
                        "Referer": stream_url
                    }

                    encryption_key = Mpd.get_license_key(
                        license_url, key_type=None, key_value=encryption_json, key_headers=headers)

                    stream = part.append_media_stream(stream_url, 0)
                    Mpd.set_input_stream_addon_input(
                        stream, license_key=encryption_key)
                    item.complete = True

            subs = [s['file'] for s in play_list_entry.get("tracks", []) if s.get('kind') == "captions"]
            if subs:
                subtitle = SubtitleHelper.download_subtitle(subs[0], format="webvtt")
                part.Subtitle = subtitle

        if has_drm_only and not adaptive_available_encrypted:
            XbmcWrapper.show_dialog(
                LanguageHelper.get_localized_string(LanguageHelper.DrmTitle),
                LanguageHelper.get_localized_string(LanguageHelper.WidevineLeiaRequired)
            )
        return item

    def __update_video_from_mpd(self, item, mpd_info, use_adaptive_with_encryption):
        """ Updates an existing MediaItem with more data based on an MPD stream.

        :param dict[str,str] mpd_info:              Stream info retrieved from the stream json.
        :param bool use_adaptive_with_encryption:   Do we use the Adaptive InputStream add-on?
        :param MediaItem item:                      The original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug("Updating streams using BrightCove data.")

        part = item.create_new_empty_media_part()
        mpd_manifest_url = "https:{0}".format(mpd_info["mediaLocator"])
        mpd_data = UriHandler.open(mpd_manifest_url)
        subtitles = Regexer.do_regex(r'<BaseURL>([^<]+\.vtt)</BaseURL>', mpd_data)

        if subtitles:
            Logger.debug("Found subtitle: %s", subtitles[0])
            subtitle = SubtitleHelper.download_subtitle(subtitles[0], format="webvtt")
            part.Subtitle = subtitle

        if use_adaptive_with_encryption:
            # We can use the adaptive add-on with encryption
            Logger.info("Using MPD InputStreamAddon")
            license_url = Regexer.do_regex('licenseUrl="([^"]+)"', mpd_data)[0]
            token = "Bearer {0}".format(mpd_info["playToken"])
            key_headers = {"Authorization": token}
            license_key = Mpd.get_license_key(license_url, key_headers=key_headers)

            stream = part.append_media_stream(mpd_manifest_url, 0)
            Mpd.set_input_stream_addon_input(stream, license_key=license_key)
            item.complete = True
        else:
            XbmcWrapper.show_dialog(
                LanguageHelper.get_localized_string(LanguageHelper.DrmTitle),
                LanguageHelper.get_localized_string(LanguageHelper.WidevineLeiaRequired)
            )

        return item

    def __update_video_from_brightcove(self, item, data, use_adaptive_with_encryption):
        """ Updates an existing MediaItem with more data based on an MPD stream.

        :param str data:                            Stream info retrieved from BrightCove.
        :param bool use_adaptive_with_encryption:   Do we use the Adaptive InputStream add-on?
        :param MediaItem item:                      The original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        part = item.create_new_empty_media_part()
        # Then try the new BrightCove JSON
        bright_cove_regex = '<video[^>]+data-video-id="(?<videoId>[^"]+)[^>]+data-account="(?<videoAccount>[^"]+)'
        bright_cove_data = Regexer.do_regex(Regexer.from_expresso(bright_cove_regex), data)
        if not bright_cove_data:
            Logger.warning("Error updating using BrightCove data: %s", item)
            return item

        Logger.info("Found new BrightCove JSON data")
        bright_cove_url = 'https://edge.api.brightcove.com/playback/v1/accounts/' \
                          '%(videoAccount)s/videos/%(videoId)s' % bright_cove_data[0]
        headers = {
            "Accept": "application/json;pk=BCpkADawqM3ve1c3k3HcmzaxBvD8lXCl89K7XEHiKutxZArg2c5RhwJHJANOwPwS_4o7UsC4RhIzXG8Y69mrwKCPlRkIxNgPQVY9qG78SJ1TJop4JoDDcgdsNrg"
        }

        bright_cove_data = UriHandler.open(bright_cove_url, additional_headers=headers)
        bright_cove_json = JsonHelper(bright_cove_data)
        streams = [d for d in bright_cove_json.get_value("sources") if d["container"] == "M2TS"]
        # Old filter
        # streams = filter(lambda d: d["container"] == "M2TS", bright_cove_json.get_value("sources"))
        if not streams:
            Logger.warning("Error extracting streams from BrightCove data: %s", item)
            return item

        # noinspection PyTypeChecker
        stream_url = streams[0]["src"]

        # these streams work better with the the InputStreamAddon because it removes the
        # "range" http header
        if use_adaptive_with_encryption:
            Logger.info("Using InputStreamAddon for playback of HLS stream")
            strm = part.append_media_stream(stream_url, 0)
            M3u8.set_input_stream_addon_input(strm)
            item.complete = True
            return item

        for s, b in M3u8.get_streams_from_m3u8(stream_url):
            item.complete = True
            part.append_media_stream(s, b)
        return item

    #region GraphQL data
    # noinspection SpellCheckingInspection
    def add_graphql_extras(self, data):
        """ Adds additional items to the main listings

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        if self.parentItem is not None:
            return data, items

        popular_url = self.__get_api_query_url(
            "trendingPrograms",
            "{__typename,title,description,guid,updated,seriesTvSeasons{id},imageMedia{url,label}}"
        )
        popular_title = LanguageHelper.get_localized_string(LanguageHelper.Popular)
        popular = MediaItem("\a.: {} :.".format(popular_title), popular_url)
        popular.dontGroup = True
        popular.content_type = contenttype.TVSHOWS
        items.append(popular)

        # https://graph.kijk.nl/graphql?operationName=programsByDate&variables={"date":"2020-04-19","numOfDays":7}&extensions={"persistedQuery":{"version":1,"sha256Hash":"1445cc0d283e10fa21fcdf95b127207d5f8c22834c1d0d17df1aacb8a9da7a8e"}}
        recent_url = "#recentgraphql"
        recent_title = LanguageHelper.get_localized_string(LanguageHelper.Recent)
        recent = MediaItem("\a.: {} :.".format(recent_title), recent_url)
        recent.dontGroup = True
        items.append(recent)

        search_title = LanguageHelper.get_localized_string(LanguageHelper.Search)
        search = MediaItem("\a.: {} :.".format(search_title), "#searchSite")
        search.dontGroup = True
        items.append(search)

        movie_url = self.__get_api_persisted_url(
            "programs", "b6f65688f7e1fbe22aae20816d24ca5dcea8c86c8e72d80b462a345b5b70fa41",
            variables={"programTypes": "MOVIE", "limit": 100}
        )
        movies_title = LanguageHelper.get_localized_string(LanguageHelper.Movies)
        movies = MediaItem("\a.: {} :.".format(movies_title), movie_url)
        movies.dontGroup = True
        movies.content_type = contenttype.MOVIES
        items.append(movies)

        return data, items

    def add_graphql_recents(self, data):
        items = []

        today = datetime.datetime.now()
        days = LanguageHelper.get_days_list()
        for i in range(0, 7, 1):
            air_date = today - datetime.timedelta(i)
            Logger.trace("Adding item for: %s", air_date)

            # Determine a nice display date
            day = days[air_date.weekday()]
            if i == 0:
                day = LanguageHelper.get_localized_string(LanguageHelper.Today)
            elif i == 1:
                day = LanguageHelper.get_localized_string(LanguageHelper.Yesterday)
            title = "%04d-%02d-%02d - %s" % (air_date.year, air_date.month, air_date.day, day)

            recent_url = self.__get_api_query_url(
                "programsByDate(date:\"{:04d}-{:02d}-{:02d}\",numOfDays:0)".format(
                    air_date.year, air_date.month, air_date.day),
                self.__video_fields
            )
            extra = MediaItem(title, recent_url)
            extra.complete = True
            extra.dontGroup = True
            extra.metaData["title_format"] = "{2} - s{0:02d}e{1:02d}"
            extra.set_date(air_date.year, air_date.month, air_date.day, text="")

            items.append(extra)

        return data, items

    # noinspection PyUnusedLocal
    def create_api_typed_item(self, result_set, add_parent_title=False):
        """ Creates a new MediaItem based on the __typename attribute.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex
        :param bool add_parent_title: Should the parent's title be included?

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        api_type = result_set["__typename"].lower()
        custom_type = result_set.get("type")
        Logger.trace("%s: %s", api_type, result_set)

        item = None
        if custom_type is not None:
            # Use the kijk.nl custom type
            if custom_type == "EPISODE":
                item = self.create_api_episode_type(result_set)
            elif custom_type == "SERIES":
                item = self.create_api_program_type(result_set)
            elif custom_type == "MOVIE":
                item = self.create_api_movie_type(result_set)
            else:
                Logger.warning("Missing type: %s", api_type)
                return None
            return item

        if api_type == "program":
            item = self.create_api_program_type(result_set)
        elif api_type == "tvseason":
            item = self.create_api_tvseason_type(result_set)
        else:
            Logger.warning("Missing type: %s", api_type)
            return None

        return item

    def create_api_program_type(self, result_set):
        """ Creates a new MediaItem for an program.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        title = result_set["title"]
        if title is None:
            return None

        seasons = result_set["seriesTvSeasons"]
        if len(seasons) == 0:
            return None

        if len(seasons) == 1:
            # List the videos in that season
            season_id = seasons[0]["id"].rsplit("/", 1)[-1]
            url = self.__get_api_query_url(
                query='programs(tvSeasonId:"{}",programTypes:EPISODE,skip:0,limit:{})'.format(season_id, self.__list_limit),
                fields=self.__video_fields)
        else:
            # Fetch the season information
            url = self.__get_api_query_url(
                query='programs(guid:"{}")'.format(result_set["guid"]),
                fields="{items{seriesTvSeasons{id,title,seasonNumber,__typename}}}"
            )

        item = MediaItem(result_set["title"], url)
        item.description = result_set.get("description")
        self.__get_artwork(item, result_set.get("imageMedia"))

        # In the main list we should set the fanart too
        if self.parentItem is None:
            item.fanart = item.thumb

        return item

    def create_api_movie_type(self, result_set):
        """ Creates a new MediaItem for an program.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        title = result_set["title"]
        if title is None:
            return None

        url = self.__get_api_persisted_url(
            "programs", "b6f65688f7e1fbe22aae20816d24ca5dcea8c86c8e72d80b462a345b5b70fa41",
            variables={"programTypes": "MOVIE", "guid": result_set["guid"]})

        item = MediaItem(result_set["title"], url)
        item.description = result_set.get("description")
        item.type = "video"
        item.set_info_label("duration", int(result_set.get("duration", 0) or 0))
        item.set_info_label("genre", result_set.get("displayGenre"))
        self.__get_artwork(item, result_set.get("imageMedia"))

        time_stamp = result_set["epgDate"] / 1000
        date_stamp = DateHelper.get_date_from_posix(time_stamp, tz=self.__timezone_utc)
        date_stamp = date_stamp.astimezone(self.__timezone)
        if date_stamp > datetime.datetime.now(tz=self.__timezone):
            available = LanguageHelper.get_localized_string(LanguageHelper.AvailableFrom)
            item.name = "{} - [COLOR=gold]{} {:%Y-%m-%d}[/COLOR]".format(
                title, available, date_stamp)
        item.set_date(date_stamp.year, date_stamp.month, date_stamp.day)

        # In the main list we should set the fanart too
        if self.parentItem is None:
            item.fanart = item.thumb

        sources = result_set.get("sources")
        item.metaData["sources"] = sources
        subs = result_set.get("tracks")
        item.metaData["subtitles"] = subs
        return item

    def create_api_tvseason_type(self, result_set):
        """ Creates a new MediaItem for an TV Season.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        season_number = result_set["seasonNumber"]
        title = LanguageHelper.get_localized_string(LanguageHelper.SeasonId)
        title = "{} {:02d}".format(title, season_number)

        season_id = result_set["id"].rsplit("/", 1)[-1]
        url = self.__get_api_query_url(
            query='programs(tvSeasonId:"{}",programTypes:EPISODE,skip:0,limit:{})'.format(season_id, self.__list_limit),
            fields=self.__video_fields)

        item = MediaItem(title, url)
        return item

    def create_api_episode_type(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        # This URL gives the URL that contains the show info with Season ID's
        url = "https://graph.kijk.nl/graphql-video"

        if not result_set.get("sources"):
            return None

        title = result_set["title"]
        season_number = result_set.get("seasonNumber")
        episode_number = result_set.get("tvSeasonEpisodeNumber")

        title_format = self.parentItem.metaData.get("title_format", "s{0:02d}e{1:02d} - {2}")
        if title is None:
            serie_title = result_set["series"]["title"]
            title = title_format.format(season_number, episode_number, serie_title)
        elif season_number is not None and episode_number is not None:
            title = title_format.format(season_number, episode_number, title)

        item = MediaItem(title, url, type="video")
        item.description = result_set.get("longDescription", result_set.get("description"))
        item.set_info_label("duration", int(result_set.get("duration", 0) or 0))
        item.set_info_label("genre", result_set.get("displayGenre"))
        self.__get_artwork(item, result_set.get("imageMedia"), mode="thumb")

        updated = result_set["lastPubDate"] / 1000
        date_time = DateHelper.get_date_from_posix(updated)
        item.set_date(date_time.year, date_time.month, date_time.day, date_time.hour,
                      date_time.minute,
                      date_time.second)

        # Find the media streams
        item.metaData["sources"] = result_set["sources"]
        item.metaData["subtitles"] = result_set.get("tracks", [])

        # DRM only
        no_drm_items = [src for src in result_set["sources"] if not src["drm"]]
        item.isDrmProtected = len(no_drm_items) == 0
        return item

    def update_graphql_item(self, item):
        """ Updates video items that are encrypted. This could be the default for Krypton!

        :param MediaItem item: The item to update.

        :return: An updated item.
        :rtype: MediaItem

        """

        sources = item.metaData["sources"]
        part = item.create_new_empty_media_part()
        hls_over_dash = self._get_setting("hls_over_dash") == "true"

        for src in sources:
            stream_type = src["type"]
            url = src["file"]
            drm = src["drm"]
            if "?filter=" in url:
                url = url[:url.index("?filter=")]

            if stream_type == "dash" and not drm:
                bitrate = 0 if hls_over_dash else 2
                stream = part.append_media_stream(url, bitrate)
                item.complete = Mpd.set_input_stream_addon_input(stream)

            elif stream_type == "dash" and drm and "widevine" in drm:
                bitrate = 0 if hls_over_dash else 1
                stream = part.append_media_stream(url, bitrate)

                # fetch the authentication token:
                # url = self.__get_api_persisted_url("drmToken", "634c83ae7588a877e2bb67d078dda618cfcfc70ac073aef5e134e622686c0bb6", variables={})
                url = self.__get_api_query_url("drmToken", "{token,expiration}")
                token_data = UriHandler.open(url, no_cache=True)
                token_json = JsonHelper(token_data)
                token = token_json.get_value("data", "drmToken", "token")

                # we need to POST to this url using this wrapper:
                key_url = drm["widevine"]["url"]
                release_pid = drm["widevine"]["releasePid"]
                encryption_json = '{{"getRawWidevineLicense":{{"releasePid":"{}","widevineChallenge":"b{{SSM}}"}}}}'.format(release_pid)
                encryption_key = Mpd.get_license_key(
                    key_url=key_url,
                    key_type="b",
                    key_value=encryption_json,
                    key_headers={"Content-Type": "application/json", "authorization": "Basic {}".format(token)}
                )
                Mpd.set_input_stream_addon_input(stream, license_key=encryption_key)
                item.complete = True

            elif stream_type == "m3u8" and not drm:
                bitrate = 2 if hls_over_dash else 0
                item.complete = M3u8.update_part_with_m3u8_streams(
                    part, url, channel=self, bitrate=bitrate)

            else:
                Logger.debug("Found incompatible stream: %s", src)

        subtitle = None
        for sub in item.metaData.get("subtitles", []):
            subtitle = sub["file"]
        part.Subtitle = subtitle

        # If we are here, we can playback.
        item.isDrmProtected = False
        return item

    # noinspection PyUnusedLocal
    def __get_artwork(self, item, image_data, mode=("thumb", "poster")):
        """ Generates a full thumbnail url based on the "id" and "changed" values in a thumbnail
        data object from the API.

        :param MediaItem item:                      The item to set the data to.
        :param list[dict[str, string]] image_data:  The data for the thumb

        """

        if not bool(image_data):
            return

        thumb_set = False
        for img in image_data:
            if "_landscape" in img["label"] and "thumb" in mode:
                url = "https://cldnr.talpa.network/talpa-network/image/fetch/" \
                      "ar_16:9,c_scale,f_auto,h_1080,w_auto/{}".format(img["url"])
                item.set_artwork(thumb=url)
                thumb_set = True
            elif "_portrait" in img["label"] and "poster" in mode:
                url = "https://cldnr.talpa.network/talpa-network/image/fetch/" \
                      "ar_2:3,c_scale,f_auto,h_750,w_auto/{}".format(img["url"])
                item.set_artwork(poster=url)

        # If it fails, return the first one.
        if not thumb_set:
            item.set_artwork(thumb=image_data[0].get("url"))

    def __get_api_query_url(self, query, fields):
        result = "query{%s%s}" % (query, fields)
        return "https://graph.kijk.nl/graphql?query={}".format(HtmlEntityHelper.url_encode(result))

    def __get_api_persisted_url(self, operation, hash_value, variables):  # NOSONAR
        """ Generates a GraphQL url

        :param str operation:   The operation to use
        :param str hash_value:  The hash of the Query
        :param dict variables:  Any variables to pass

        :return: A GraphQL string
        :rtype: str

        """

        extensions = {"persistedQuery": {"version": 1, "sha256Hash": hash_value}}
        extensions = HtmlEntityHelper.url_encode(JsonHelper.dump(extensions, pretty_print=False))

        variables = HtmlEntityHelper.url_encode(JsonHelper.dump(variables, pretty_print=False))

        url = "https://graph.kijk.nl/graphql?" \
              "operationName={}&" \
              "variables={}&" \
              "extensions={}".format(operation, variables, extensions)
        return url
    #endregion
