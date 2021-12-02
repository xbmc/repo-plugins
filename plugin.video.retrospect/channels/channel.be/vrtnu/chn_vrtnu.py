# SPDX-License-Identifier: GPL-3.0-or-later

import datetime

from resources.lib import chn_class
from resources.lib import contenttype
from resources.lib import mediatype
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.htmlhelper import HtmlHelper
from resources.lib.regexer import Regexer
from resources.lib.parserdata import ParserData
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.vault import Vault
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.textures import TextureHandler


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
        self.noImage = "vrtnuimage.png"
        self.mainListUri = "https://www.vrt.be/vrtnu/a-z/"
        self.baseUrl = "https://www.vrt.be"

        # first regex is a bit tighter than the second one.
        episode_regex = r'<nui-tile href="(?<url>/vrtnu[^"]+)/"[^>]*>\s*<h3[^>]*>\s*<a[^>]+>' \
                        r'(?<title>[^<]+)</a>\s*</h3>\s*<div[^>]+>(?:\s*<p>)?(?<description>' \
                        r'[\w\W]{0,2000}?)(?:</p>)?\W*</div>\s*(?:<p[^>]*' \
                        r'data-brand="(?<channel>[^"]+)"[^>]*>[^<]+</p>)?\s*(?:<img[\w\W]{0,100}?' \
                        r'data-responsive-image="(?<thumburl>//[^" ]+)")?'
        episode_regex = Regexer.from_expresso(episode_regex)
        self._add_data_parser(self.mainListUri, name="Main A-Z listing",
                              preprocessor=self.add_categories,
                              match_type=ParserData.MatchExact,
                              parser=episode_regex, creator=self.create_episode_item)

        self._add_data_parser("#channels", name="Main channel name listing",
                              preprocessor=self.list_channels)

        self._add_data_parser("https://search.vrt.be/suggest?facets[categories]",
                              name="JSON Show Parser", json=True,
                              parser=[], creator=self.create_show_item)

        self._add_data_parser("https://services.vrt.be/videoplayer/r/live.json", json=True,
                              name="Live streams parser",
                              parser=[], creator=self.create_live_stream)
        self._add_data_parsers(["http://live.stream.vrt.be/", "https://live-vrt.akamaized.net"],
                               name="Live streams updater",
                               updater=self.update_live_video)
        self._add_data_parser(r"https://live-[^/]+\.vrtcdn\.be",
                              match_type=ParserData.MatchRegex,
                              name="Live streams updater",
                              updater=self.update_live_video)

        self._add_data_parser("https://www.vrt.be/vrtnu/categorieen.model.json", name="Category parser",
                              json=True,
                              match_type=ParserData.MatchExact,
                              parser=[":items", "par", ":items", "categories", "items"],
                              creator=self.create_category)

        folder_regex = r'<option value="#([^"]+)[^>]*>([^<]+)</option>'
        folder_regex = Regexer.from_expresso(folder_regex)
        self._add_data_parser("*", name="Folder/Season parser",
                              preprocessor=self.extract_lazy_url,
                              parser=folder_regex, creator=self.create_folder_item)

        video_regex = r'vrtnu-tile[^>]+link="(?<url>[^"]+)[^>]+>\W*<vrtnu-image[^>]+src=' \
                      r'"(?<thumburl>[^"]+/(?<year>\d{4})/(?<month>\d+)/(?<day>\d+)[^"]+)"' \
                      r'[\w\W]{100,2000}?<h3[^>]*>(?<title>[^<]+)<[^<]+(?:<div[^>]+>(?<description>[^<]+))?'

        # No need for a subtitle for now as it only includes the textual date
        video_regex = Regexer.from_expresso(video_regex)
        self._add_data_parser("*", name="Video item parser",
                              parser=video_regex, creator=self.create_video_item)

        # needs to be after the standard video item regex
        single_video_regex = r'<script type="application/ld\+json">\W+({[\w\W]+?})\s*</script'
        single_video_regex = Regexer.from_expresso(single_video_regex)
        # noinspection PyTypeChecker
        self._add_data_parser("*", name="Single video item parser",
                              parser=single_video_regex, creator=self.create_single_video_item)

        self._add_data_parser("*", updater=self.update_video_item, requires_logon=True)

        # ===============================================================================================================
        # non standard items
        self.__hasAlreadyVideoItems = False
        self.__currentChannel = None

        # The key is the channel live stream key
        self.__channelData = {
            "vualto_mnm": {
                "title": "MNM",
                "metaCode": "mnm",
                "fanart": TextureHandler.instance().get_texture_uri(self, "mnmfanart.jpg"),
                "thumb": TextureHandler.instance().get_texture_uri(self, "mnmimage.jpg"),
                "icon": TextureHandler.instance().get_texture_uri(self, "mnmicon.png")
            },
            "vualto_stubru": {
                "title": "Studio Brussel",
                "metaCode": "stubru",
                "fanart": TextureHandler.instance().get_texture_uri(self, "stubrufanart.jpg"),
                "thumb": TextureHandler.instance().get_texture_uri(self, "stubruimage.jpg"),
                "icon": TextureHandler.instance().get_texture_uri(self, "stubruicon.png")
            },
            "vualto_een_geo": {
                "title": "E&eacute;n",
                "metaCode": "een",
                "fanart": TextureHandler.instance().get_texture_uri(self, "eenfanart.jpg"),
                "thumb": TextureHandler.instance().get_texture_uri(self, "eenimage.png"),
                "icon": TextureHandler.instance().get_texture_uri(self, "eenlarge.png"),
                # "url": "https://live-vrt.akamaized.net/groupc/live/8edf3bdf-7db3-41c3-a318-72cb7f82de66/live_aes.isml/.m3u8"
            },
            "vualto_canvas_geo": {
                "title": "Canvas",
                "metaCode": "canvas",
                "fanart": TextureHandler.instance().get_texture_uri(self, "canvasfanart.png"),
                "thumb": TextureHandler.instance().get_texture_uri(self, "canvasimage.png"),
                "icon": TextureHandler.instance().get_texture_uri(self, "canvaslarge.png"),
                # "url": "https://live-vrt.akamaized.net/groupc/live/14a2c0f6-3043-4850-88a5-7fb062fe7f05/live_aes.isml/.m3u8"
            },
            "vualto_ketnet_geo": {
                "title": "KetNet",
                "metaCode": "ketnet",
                "fanart": TextureHandler.instance().get_texture_uri(self, "ketnetfanart.jpg"),
                "thumb": TextureHandler.instance().get_texture_uri(self, "ketnetimage.jpg"),
                "icon": TextureHandler.instance().get_texture_uri(self, "ketnetlarge.png"),
                # "url": "https://live-vrt.akamaized.net/groupc/live/f132f1b8-d04d-404e-90e0-6da1abb4f4fc/live_aes.isml/.m3u8"
            },
            "vualto_sporza_geo": {  # not in the channel filter maps, so no metaCode
                "title": "Sporza",
                "fanart": TextureHandler.instance().get_texture_uri(self, "sporzafanart.jpg"),
                "thumb": TextureHandler.instance().get_texture_uri(self, "sporzaimage.jpg"),
                "icon": TextureHandler.instance().get_texture_uri(self, "sporzalarge.png"),
                # "url": "https://live-vrt.akamaized.net/groupa/live/7d5f0e4a-3429-4861-91d4-aa3229d7ad7b/live_aes.isml/.m3u8"
            },
            "ketnet-jr": {  # Not in the live channels
                "title": "KetNet Junior",
                "metaCode": "ketnet-jr",
                "fanart": TextureHandler.instance().get_texture_uri(self, "ketnetfanart.jpg"),
                "thumb": TextureHandler.instance().get_texture_uri(self, "ketnetimage.jpg"),
                "icon": TextureHandler.instance().get_texture_uri(self, "ketnetlarge.png")
            }
        }

        # To get the tokens:
        # POST
        # Content-Type:application/json
        # https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/tokens

        self.__folder_map = {}

        # ===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def log_on(self):
        """ Logs on to a website, using an url.

        First checks if the channel requires log on. If so and it's not already
        logged on, it should handle the log on. That part should be implemented
        by the specific channel.

        More arguments can be passed on, but must be handled by custom code.

        After a successful log on the self.loggedOn property is set to True and
        True is returned.

        :return: indication if the login was successful.
        :rtype: bool

        """

        api_key = "3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG"

        # Do we still have a valid short living token (1 hour)? If so, we have an active session.
        short_login_cookie = UriHandler.get_cookie("X-VRT-Token", ".vrt.be")
        if short_login_cookie is not None:
            # The old X-VRT-Token expired after 1 year. We don't want that old cookie
            short_login_cookie_can_live_too_long = \
                DateHelper.get_date_from_posix(short_login_cookie.expires) > datetime.datetime.now() + datetime.timedelta(hours=4)
            if not short_login_cookie_can_live_too_long:
                Logger.debug("Using existing VRT.be session.")
                return True

        # Do we still have a valid long living token? If so, try to extend the session. We need the
        # original UIDSignature value for that. The 'vrtlogin-rt' and all other related cookies
        # are valid for a same period (1 year).
        long_login_cookie = UriHandler.get_cookie("vrtlogin-rt", ".vrt.be")
        if long_login_cookie is not None:
            # if we stored a valid user signature, we can use it, together with the 'gmid' and
            # 'ucid' cookies to extend the session and get new token data
            data = UriHandler.open("https://token.vrt.be/refreshtoken", no_cache=True)
            if "vrtnutoken" in data:
                Logger.debug("Refreshed the VRT.be session.")
                return True

        Logger.warning("Failed to extend the VRT.be session.")
        username = self._get_setting("username")
        if not username:
            Logger.warning("No username configured for VRT.nu")
            return None

        v = Vault()
        password = v.get_channel_setting(self.guid, "password")
        if not password:
            Logger.warning("Found empty password for VRT user")

        # Get a 'gmid' and 'ucid' cookie by logging in. Valid for 10 years
        Logger.debug("Using: %s / %s", username, "*" * len(password))
        url = "https://accounts.vrt.be/accounts.login"
        data = {
            "loginID": username,
            "password": password,
            "sessionExpiration": "-1",
            "targetEnv": "jssdk",
            "include": "profile,data,emails,subscriptions,preferences,",
            "includeUserInfo": "true",
            "loginMode": "standard",
            "lang": "nl-inf",
            "APIKey": api_key,
            "source": "showScreenSet",
            "sdk": "js_latest",
            "authMode": "cookie",
            "format": "json"
        }
        logon_data = UriHandler.open(url, data=data, no_cache=True)
        user_id, signature, signature_time_stamp = self.__extract_session_data(logon_data)
        if user_id is None or signature is None or signature_time_stamp is None:
            return False

        # We need to initialize the token retrieval which will redirect to the actual token
        UriHandler.open("https://token.vrt.be/vrtnuinitlogin?provider=site&destination=https://www.vrt.be/vrtnu/",
                        no_cache=True)

        # Now get the actual VRT tokens (X-VRT-Token....). Valid for 1 hour. So we call the actual
        # perform_login url which will redirect and get cookies.
        csrf = UriHandler.get_cookie("OIDCXSRF", "login.vrt.be")
        if csrf is None:
            csrf = UriHandler.get_cookie("XSRF-TOKEN", "login.vrt.be")

        token_data = {
            "UID": user_id,
            "UIDSignature": signature,
            "signatureTimestamp": signature_time_stamp,
            "client_id": "vrtnu-site",
            "submit": "submit",
            "_csrf": csrf.value
        }
        UriHandler.open("https://login.vrt.be/perform_login", data=token_data, no_cache=True)
        return True

    def add_categories(self, data):
        """ Adds categories to the main listings.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        if self.parentItem and "code" in self.parentItem.metaData:
            self.__currentChannel = self.parentItem.metaData["code"]
            Logger.info("Only showing items for channel: '%s'", self.__currentChannel)
            return data, items

        cat = FolderItem("\a.: Categori&euml;n :.", "https://www.vrt.be/vrtnu/categorieen.model.json",
                         content_type=contenttype.FILES)
        cat.dontGroup = True
        items.append(cat)

        live = FolderItem("\a.: Live Streams :.", "https://services.vrt.be/videoplayer/r/live.json",
                          content_type=contenttype.VIDEOS)
        live.dontGroup = True
        live.isLive = True
        items.append(live)

        channel_text = LanguageHelper.get_localized_string(30010)
        channels = FolderItem("\a.: %s :." % (channel_text, ), "#channels",
                              content_type=contenttype.FILES)
        channels.dontGroup = True
        items.append(channels)

        Logger.debug("Pre-Processing finished")
        return data, items

    def extract_lazy_url(self, data):
        """ Extract the lazy load URL from a TV Show page.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        lazy_urls = Regexer.do_regex(r'data-lazy-src="([^"]+)"[^>]+id="([^"]+)', data)
        for folder_url in lazy_urls:
            self.__folder_map[folder_url[1]] = folder_url[0]

        return data, items

    def list_channels(self, data):
        """ Lists all the available channels.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        for name, meta in self.__channelData.items():
            if "metaCode" not in meta:
                continue

            channel = FolderItem(meta["title"], self.mainListUri, content_type=contenttype.TVSHOWS)
            # noinspection PyArgumentList
            channel.fanart = meta.get("fanart", self.fanart)
            # noinspection PyArgumentList
            channel.thumb = meta.get("icon", self.icon)
            # noinspection PyArgumentList
            channel.icon = meta.get("icon", self.icon)
            channel.dontGroup = True
            channel.metaData["code"] = meta["metaCode"]
            items.append(channel)
        return data, items

    def create_category(self, result_set):
        """ Creates a new MediaItem for an category folder.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        # https://search.vrt.be/suggest?facets[categories]=met-audiodescriptie
        url = "https://search.vrt.be/suggest?facets[categories]=%(name)s" % result_set
        title = result_set["title"]
        thumb = result_set["imageStoreUrl"]
        if thumb.startswith("//"):
            thumb = "https:{}".format(thumb)

        item = FolderItem(title, url, content_type=contenttype.EPISODES)
        item.description = title
        item.thumb = thumb
        item.HttpHeaders = self.httpHeaders
        item.complete = True
        return item

    def create_live_stream(self, result_set):
        """ Creates a MediaItem of type 'video' for a live stream using the
        result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        items = []
        for key_value, stream_value in result_set.items():
            Logger.trace(stream_value)
            # noinspection PyArgumentList
            channel_data = self.__channelData.get(key_value, None)
            if not channel_data:
                continue

            url = channel_data["url"] if "url" in channel_data else stream_value["mpd"]
            live_item = MediaItem(channel_data["title"], url, media_type=mediatype.VIDEO)
            live_item.isLive = True
            live_item.fanart = channel_data.get("fanart", self.fanart)
            live_item.thumb = channel_data.get("icon", self.icon)
            live_item.icon = channel_data.get("icon", self.icon)
            live_item.metaData["channel_key"] = key_value
            items.append(live_item)
        return items

    def create_show_item(self, result_set):
        """ Creates a new MediaItem for an show.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        if result_set["targetUrl"].startswith("//"):
            result_set["url"] = "https:%(targetUrl)s" % result_set
        else:
            result_set["url"] = result_set["targetUrl"]
        result_set["thumburl"] = result_set["thumbnail"]

        return chn_class.Channel.create_episode_item(self, result_set)

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        if self.__currentChannel is not None and result_set["channel"] != self.__currentChannel:
            Logger.debug("Skipping items due to channel mismatch: %s", result_set)
            return None

        item = chn_class.Channel.create_episode_item(self, result_set)
        if item is None:
            return None

        item.url = "{}/".format(item.url)
        item.description = HtmlHelper.to_text(item.description)

        # update artswork
        if item.thumb and item.thumb.startswith("//"):
            item.thumb = "https:%s" % (item.thumb, )

        # API url's
        # item.url = "https://vrtnu-api.vrt.be/search?i=video&facets[programUrl]={}&size=300".format(
        #     item.url.replace("https:", "").replace(".relevant", ""))

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

        folder_id = result_set[0]
        folder_url = self.__folder_map.get(folder_id)
        if not folder_url:
            return None

        folder_url = "{}{}".format(self.baseUrl, folder_url)
        item = FolderItem(result_set[1], folder_url, content_type=contenttype.EPISODES)
        item.name = item.name.title()
        return item

    def create_single_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param str result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        if self.__hasAlreadyVideoItems:
            # we already have items, so don't show this one, it will be a duplicate
            return None

        result_set = result_set.replace('\\x27', "'")

        json_data = JsonHelper(result_set)
        url = self.parentItem.url
        title = json_data.get_value("name")
        description = HtmlHelper.to_text(json_data.get_value("description"))

        item = MediaItem(title, url,  media_type=mediatype.EPISODE)
        item.description = description
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

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        if "title" not in result_set or result_set["title"] is None:
            result_set["title"] = result_set.pop("subtitle")

        result_set["title"] = result_set["title"].strip()
        item = chn_class.Channel.create_video_item(self, result_set)
        item.media_type = mediatype.EPISODE
        if item is None:
            return None

        item.description = result_set.get("subtitle", None)
        if "day" in result_set and result_set["day"]:
            if len(result_set.get("year", "")) < 4:
                result_set["year"] = None
            item.set_date(result_set["year"] or DateHelper.this_year(), result_set["month"], result_set["day"])

        if item.thumb.startswith("//"):
            item.thumb = "https:%s" % (item.thumb, )

        self.__hasAlreadyVideoItems = True
        return item

    def update_live_video(self, item):
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

        mzid = item.metaData["channel_key"]
        return self.update_video_for_mzid(item, mzid, live=True)

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

        # Get the MZID
        data = UriHandler.open(item.url, additional_headers=item.HttpHeaders)
        json_data = Regexer.do_regex(r'<script type="application/ld\+json">(.*?)</script>', data)
        json_info = JsonHelper(json_data[-1])
        video_id = json_info.get_value("video", "@id")
        publication_id = json_info.get_value("publication", -1, "@id")

        mzid = "{}${}".format(publication_id, video_id)
        return self.update_video_for_mzid(item, mzid)

    def update_video_for_mzid(self, item, mzid, live=False):  # NOSONAR
        """ Updates a video item based on the MZID

        :param MediaItem item: the parent item
        :param str mzid:       the MZID

        """

        hls_over_dash = self._get_setting("hls_over_dash", 'false') == 'true'

        from resources.lib.streams.vualto import Vualto
        v = Vualto(self, "vrtvideo")
        item = v.get_stream_info(item, mzid, live=live, hls_over_dash=hls_over_dash)
        return item

    def __extract_session_data(self, logon_data):
        logon_json = JsonHelper(logon_data)
        result_code = logon_json.get_value("statusCode")
        if result_code != 200:
            Logger.error("Error loging in: %s - %s", logon_json.get_value("errorMessage"),
                         logon_json.get_value("errorDetails"))
            return None, None, None

        return logon_json.get_value("UID"), \
            logon_json.get_value("UIDSignature"), \
            logon_json.get_value("signatureTimestamp")
