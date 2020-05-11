# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class
from resources.lib.mediaitem import MediaItem
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.subtitlehelper import SubtitleHelper
from resources.lib.parserdata import ParserData
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger


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
        self.noImage = "nrknoimage.png"

        # setup the urls
        self.mainListUri = "#mainlist"
        self.baseUrl = "https://psapi.nrk.no"

        self._add_data_parser(self.mainListUri, preprocessor=self.create_main_list)

        # See https://stsnapshottestwe.blob.core.windows.net/apidocumentation/documentation.html for
        # the url definitions
        self._add_data_parser("https://psapi.nrk.no/medium/tv/letters?", json=True,
                              name="Alfa Listing",
                              parser=[], creator=self.create_alpha_item)

        self._add_data_parser("https://psapi.nrk.no/medium/tv/letters/", json=True,
                              name="Programs from AlphaListing",
                              parser=[], creator=self.create_episode_item)

        self._add_data_parser("https://psapi.nrk.no/programs/", json=True,
                              name="Main program json video updater",
                              updater=self.update_json_video_item)

        self._add_data_parsers(
            ["https://psapi.nrk.no/medium/tv/recommendedprograms",
             "https://psapi.nrk.no/medium/tv/popularprograms",
             "https://psapi.nrk.no/medium/tv/recentlysentprograms"],
            json=True, parser=[], creator=self.create_video_item)

        self._add_data_parsers(["https://psapi.nrk.no/tv/live", "https://psapi.nrk.no/radio/live"],
                               json=True, name="Live items",
                               parser=[], creator=self.create_live_channel_item)
        self._add_data_parser("https://psapi.nrk.no/playback/manifest/channel/",
                              updater=self.update_live_channel)

        self._add_data_parser("https://psapi.nrk.no/medium/tv/categories", json=True,
                              name="Category listing",
                              parser=[], creator=self.create_category_item)
        self._add_data_parser("https://psapi.nrk.no/medium/tv/categories/", json=True,
                              name="Category Items",
                              parser=[], creator=self.create_category_episode_item)

        # The new Series/Instalments API (https://psapi-catalog-prod-we.azurewebsites.net/swagger/index.html)
        self._add_data_parser("https://psapi.nrk.no/tv/catalog/series/",
                              json=True, name="Main Series parser",
                              parser=["_links", "seasons"], creator=self.create_instalment_season_item)

        self._add_data_parser("https://psapi.nrk.no/tv/catalog/series/[^/]+/seasons/", json=True,
                              match_type=ParserData.MatchRegex,
                              name="Videos for Serie parser - instalments",
                              parser=["_embedded", "instalments"],
                              creator=self.create_instalment_video_item)
        self._add_data_parser("https://psapi.nrk.no/tv/catalog/series/[^/]+/seasons/", json=True,
                              match_type=ParserData.MatchRegex,
                              name="Videos for Serie parser - episodes",
                              parser=["_embedded", "episodes"],
                              creator=self.create_instalment_video_item)

        self._add_data_parser("https://psapi-ne.nrk.no/autocomplete?q=", json=True,
                              name="Search regex item",
                              parser=["result", ],
                              creator=self.create_search_item)

        # The old Series API (http://nrkpswebapi2ne.cloudapp.net/swagger/ui/index#/)
        self._add_data_parser("https://psapi.nrk.no/series/", json=True,
                              name="Main Series parser",
                              parser=["seasons", ], creator=self.create_series_season_item)

        self._add_data_parser("https://psapi.nrk.no/series/[^/]+/seasons/", json=True,
                              match_type=ParserData.MatchRegex,
                              name="Videos for Serie parser",
                              parser=[], creator=self.create_series_video_item)

        self._add_data_parser("*", updater=self.update_video_item)

        # ==============================================================================================================
        # non standard items
        self.__meta_data_index_category = "category_id"
        self.__api_key = "d1381d92278a47c09066460f2522a67d"
        self.__category_thumbs = {
            "dokumentar": "https://gfx.nrk.no/i3DzcJ0XTcemgMb_ZyOlFwI-03NRFfBl9pUtzwTRQpTA",
            "drama-serier": "https://gfx.nrk.no/2HMvppp-47PO0xSWBHM2ZwHm5xp6n_07t54E76ccl5eA",
            "barn": "https://gfx.nrk.no/xwGsglO0bd4p2bYkTYGOIAE9UCgZSuiEgvFsQEJ3QSFA",
            "kultur": "https://gfx.nrk.no/RtXpUdc9ChV4XFUuimLh9gLNN4-MmklT0Lvo83bzhI2Q",
            "humor": "https://gfx.nrk.no/O1oNdMAAjFZkI3ees23gnAL8rZVCiB5eRJOZmkA-A3dg",
            "underholdning": "https://gfx.nrk.no/ECDmornhSJq6RzV13BOgZwTZjdR4WIaWM2p5n8V6y6Jg",
            "familie": "https://gfx.nrk.no/aRTqJveqSlE5XZooe6aqzABrNAShEei7kb3uWlxoJ0Zg",
            "livsstil": "https://gfx.nrk.no/Uox8RfJvIbTXkZeSgrBf9QKLeW2mAsey4nIEwrKkIjsQ",
            "natur": "https://gfx.nrk.no/0FeIb5ab4eTG-1AYqnZwoQiBwG4GdWUX7yNN2v5jcZvw",
            "vitenskap": "https://gfx.nrk.no/rTUeAtQs-pqAmCI-gxrBFwVnXefxSaXv1BfsOpXskaCw",
            "nyheter": "https://gfx.nrk.no/9MpRHSUAmv5G5bi9qdFw3gFHct6todw8sGE_n-KzU6kA",
            "sport": "https://gfx.nrk.no/YGxIhtvVJQl777nAGEz94gjdA3nvQdwVMVHb5zMg22Vg",
            "nrk-arkivet": "https://gfx.nrk.no/oWNng0oqTjx-SxPYaCrtZAxlBscGGu3-fV_7w-l6nDfg",
            "samisk": "https://gfx.nrk.no/OaSWHWFVweeRJ1EigD7iMw_85pz4MH6OuJ1HyN3Wf5Yg",
            "tegnspraak": "https://gfx.nrk.no/9u2UYEA2-VKZj4U9qT6njQelUZ2FFGE-oOy8f4ZlRP8g",
            "synstolk": "https://gfx.nrk.no/LtU-m90topVMltAfXaFNqgKPNQ7wQioJTSZOhq-ltiDQ",
        }

        # ==============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_main_list(self, data):
        """ Performs pre-process actions for data processing and creates the main menu list

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

        live = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
        live_tv = "{} - TV".format(live)
        live_radio = "{} - Radio".format(live)

        links = {
            live_tv: "https://psapi.nrk.no/tv/live?apiKey={}".format(self.__api_key),
            live_radio: "https://psapi.nrk.no/radio/live?apiKey={}".format(self.__api_key),
            "Recommended": "https://psapi.nrk.no/medium/tv/recommendedprograms?maxnumber=100&startRow=0&apiKey={}".format(self.__api_key),
            "Popular": "https://psapi.nrk.no/medium/tv/popularprograms/week?maxnumber=100&startRow=0&apiKey={}".format(self.__api_key),
            "Recent": "https://psapi.nrk.no/medium/tv/recentlysentprograms?maxnumber=100&startRow=0&apiKey={}".format(self.__api_key),
            "Categories": "https://psapi.nrk.no/medium/tv/categories?apiKey={}".format(self.__api_key),
            "A - Å": "https://psapi.nrk.no/medium/tv/letters?apiKey={}".format(self.__api_key),
            "S&oslash;k": "#searchSite"
        }
        for name, url in links.items():
            item = MediaItem(name, url)
            item.complete = True
            item.HttpHeaders = self.httpHeaders
            items.append(item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def search_site(self, url=None):
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

        url = "https://psapi-ne.nrk.no/autocomplete?q=%s&apiKey={}".format(self.__api_key)
        return chn_class.Channel.search_site(self, url)

    def create_alpha_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the Alpha chars available. It uses
        the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        program_count = result_set.get("availableInternationally", 0)
        if program_count <= 0:
            return None

        title = result_set["title"]
        url_part = title.lower()
        if url_part == "0-9":
            url_part = "$"
        url = "https://psapi.nrk.no/medium/tv/letters/{}/indexelements?onlyOnDemandRights=false&" \
              "apiKey={}".format(url_part, self.__api_key)

        title = LanguageHelper.get_localized_string(LanguageHelper.StartWith) % (title, )
        item = MediaItem(title, url)
        item.type = 'folder'
        return item

    def create_category_item(self, result_set):
        """ Creates a MediaItem of type 'folder' for a category using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        title = result_set["displayValue"]
        category_id = result_set["id"]
        url = "https://psapi.nrk.no/medium/tv/categories/{}/indexelements?apiKey={}"\
            .format(category_id, self.__api_key)
        item = MediaItem(title, url)
        item.type = 'folder'
        item.thumb = self.__category_thumbs.get(category_id.lower(), self.noImage)
        return item

    def create_category_episode_item(self, result_set):
        """ Creates a MediaItem of type 'folder' for a category list item
        using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        title = result_set["title"]

        program_type = result_set.get("type", "???").lower()
        if program_type != "series":
            Logger.debug("Item '%s' has type '%s'. Ignoring", title, program_type)
            return None

        return self.create_generic_item(result_set, program_type)

    def create_episode_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        title = result_set["title"]

        program_type = result_set.get("type", "???").lower()
        if program_type not in ("programme", "series"):
            Logger.debug("Item '%s' has type '%s'. Ignoring", title, program_type)
            return None

        return self.create_generic_item(result_set, program_type)

    def create_search_item(self, result_set):
        """ Creates a MediaItem of type 'folder' for a search result using the result_set
        from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        if "_source" not in result_set:
            return None

        return self.create_generic_item(result_set["_source"], "series")

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

        return self.create_generic_item(result_set, "programme")

    def create_generic_item(self, result_set, program_type):
        """ Creates a MediaItem of type 'video' or 'folder' using the result_set from the regex and
        a basic set of values.

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

        title = result_set["title"]

        if not result_set.get("hasOndemandRights", True):
            Logger.debug("Item '%s' has no on-demand rights", title)
            return None

        item_id = result_set["id"]
        if program_type == "programme":
            url = "https://psapi.nrk.no/programs/{}?apiKey={}".format(item_id, self.__api_key)
            item = MediaItem(title, url)
            item.type = 'video'
        else:
            use_old_series_api = False
            if use_old_series_api:
                url = "https://psapi.nrk.no/series/{}?apiKey={}".format(item_id, self.__api_key)
            else:
                url = "https://psapi.nrk.no/tv/catalog/series/{}?apiKey={}".format(item_id, self.__api_key)

            item = MediaItem(title, url)
            item.type = 'folder'

        item.isGeoLocked = result_set.get("isGeoBlocked", result_set.get("usageRights", {}).get("isGeoBlocked", False))

        description = result_set.get("description")
        if description and description.lower() != "no description":
            item.description = description

        if "image" not in result_set or "webImages" not in result_set["image"]:
            return item

        # noinspection PyTypeChecker
        item.thumb = self.__get_image(result_set["image"]["webImages"], "pixelWidth", "imageUrl")

        # see if there is a date?
        self.__set_date(result_set, item)
        return item

    def create_series_season_item(self, result_set):
        """ Creates a MediaItem of type 'folder' for a season using the result_set from the regex.

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

        title = "Sesong {}".format(result_set["name"])
        season_id = result_set["id"]
        if not result_set.get("hasOnDemandRightsEpisodes", True):
            return None

        parent_url, qs = self.parentItem.url.split("?", 1)
        url = "{}/seasons/{}/episodes?apiKey={}".format(parent_url, season_id, self.__api_key)
        item = MediaItem(title, url)
        item.type = 'folder'
        return item

    def create_series_video_item(self, result_set):
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

        title = result_set["title"]
        sub_title = result_set.get("episodeTitle", None)
        if sub_title:
            title = "{} - {}".format(title, sub_title)

        if not result_set["usageRights"].get("hasRightsNow", True):
            Logger.debug("Found '%s' without 'usageRights'", title)
            return None

        url = "https://psapi.nrk.no/programs/{}?apiKey={}".format(result_set["id"], self.__api_key)
        item = MediaItem(title, url)
        item.type = 'video'

        # noinspection PyTypeChecker
        item.thumb = self.__get_image(result_set["image"]["webImages"], "pixelWidth", "imageUrl")
        item.description = result_set.get("longDescription", "")
        if not item.description:
            item.description = result_set.get("shortDescription", "")

        item.isGeoLocked = result_set.get("usageRights", {}).get("isGeoBlocked", False)
        self.__set_date(result_set, item)
        return item

    def create_instalment_season_item(self, result_set):
        """ Creates a MediaItem of type 'folder' for a season using the result_set from the regex.

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

        title = result_set["title"]
        season_id = result_set["name"]
        if title != season_id:
            title = "{} - {}".format(season_id, title)

        url = "{}{}?apiKey={}".format(self.baseUrl, result_set["href"], self.__api_key)

        item = MediaItem(title, url)
        item.type = 'folder'
        return item

    def create_instalment_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict[str,str|dict] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        title = result_set["titles"]["title"]
        sub_title = result_set["titles"]["subtitle"]

        # noinspection PyTypeChecker
        if result_set.get("availability", {}).get("status", "available") != "available":
            Logger.debug("Found '%s' with a non-available status", title)
            return None

        url = "https://psapi.nrk.no/programs/{}?apiKey={}".format(result_set["prfId"], self.__api_key)
        item = MediaItem(title, url)
        item.type = 'video'
        item.thumb = self.__get_image(result_set["image"], "width", "url")

        # noinspection PyTypeChecker
        item.isGeoLocked = result_set.get("usageRights", {}).get("geoBlock", {}).get("isGeoBlocked", False)
        if sub_title and sub_title.strip():
            item.description = sub_title

        if "firstTransmissionDateDisplayValue" in result_set:
            Logger.trace("Using 'firstTransmissionDateDisplayValue' for date")
            day, month, year = result_set["firstTransmissionDateDisplayValue"].split(".")
            item.set_date(year, month, day)
        elif "usageRights" in result_set and "from" in result_set["usageRights"] and result_set["usageRights"]["from"] is not None:
            Logger.trace("Using 'usageRights.from.date' for date")
            # noinspection PyTypeChecker
            date_value = result_set["usageRights"]["from"]["date"].split("+")[0]
            time_stamp = DateHelper.get_date_from_string(date_value, date_format="%Y-%m-%dT%H:%M:%S")
            item.set_date(*time_stamp[0:6])

        return item

    def create_live_channel_item(self, result_set):
        """ Creates a MediaItem of type 'video' for live video using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict[str,dict|str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        # noinspection PyTypeChecker
        url = "{}{}?apiKey={}".format(self.baseUrl, result_set["_links"]["manifest"]["href"], self.__api_key)

        live_data = result_set["_embedded"]["playback"]  # type: dict
        item = MediaItem(live_data["title"], url)
        item.type = "video"
        item.isLive = True
        item.isGeoLocked = live_data.get("isGeoBlocked")

        # noinspection PyTypeChecker
        self.__get_image(live_data["posters"][0]["image"]["items"], "pixelWidth", "url")
        return item

    def update_live_channel(self, item):
        """ Updates an existing live stream MediaItem with more data.

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

        headers = {}
        if self.localIP:
            headers.update(self.localIP)

        data = UriHandler.open(item.url, proxy=self.proxy, no_cache=True, additional_headers=headers)
        manifest = JsonHelper(data)
        if "nonPlayable" in manifest.json and manifest.json["nonPlayable"]:
            Logger.error("Cannot update Live: %s", item)
            return item

        source = manifest.get_value("sourceMedium")
        if source == "audio":
            return self.__update_live_audio(item, manifest, headers)
        else:
            return self.__update_live_video(item, manifest, headers)

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

        headers = {}
        if self.localIP:
            headers.update(self.localIP)

        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=headers)
        video_data = JsonHelper(data)
        stream_data = video_data.get_value("mediaAssetsOnDemand")
        if not stream_data:
            return item

        use_adaptive = AddonSettings.use_adaptive_stream_add_on()
        stream_data = stream_data[0]
        part = item.create_new_empty_media_part()
        if "hlsUrl" in stream_data:
            hls_url = stream_data["hlsUrl"]
            if use_adaptive:
                stream = part.append_media_stream(hls_url, 0)
                M3u8.set_input_stream_addon_input(stream, self.proxy, headers=headers)
                item.complete = True
            else:
                for s, b in M3u8.get_streams_from_m3u8(hls_url, self.proxy, headers=headers):
                    item.complete = True
                    part.append_media_stream(s, b)

        if "timedTextSubtitlesUrl" in stream_data and stream_data["timedTextSubtitlesUrl"]:
            sub_url = stream_data["timedTextSubtitlesUrl"].replace(".ttml", ".vtt")
            sub_url = HtmlEntityHelper.url_decode(sub_url)
            part.Subtitle = SubtitleHelper.download_subtitle(sub_url, format="webvtt")
        return item

    def __update_live_audio(self, item, manifest, headers):
        video_info = manifest.get_value("playable", "assets", 0)
        url = video_info["url"]
        # Is it encrypted? encrypted = video_info["encrypted"]
        part = item.create_new_empty_media_part()

        # Adaptive add-on does not work with audio only
        for s, b in M3u8.get_streams_from_m3u8(url, self.proxy, headers=headers):
            item.complete = True
            part.append_media_stream(s, b)

        return item

    def __update_live_video(self, item, manifest, headers):
        video_info = manifest.get_value("playable", "assets", 0)
        url = video_info["url"]
        encrypted = video_info["encrypted"]
        part = item.create_new_empty_media_part()

        if encrypted:
            use_adaptive = AddonSettings.use_adaptive_stream_add_on(with_encryption=True)
            if not use_adaptive:
                Logger.error("Cannot playback encrypted item without inputstream.adaptive with encryption support")
                return item
            stream = part.append_media_stream(url, 0)
            key = M3u8.get_license_key("", key_headers=headers, key_type="R")
            M3u8.set_input_stream_addon_input(stream, proxy=self.proxy, headers=headers, license_key=key)
            item.complete = True
        else:
            use_adaptive = AddonSettings.use_adaptive_stream_add_on(with_encryption=False)
            if use_adaptive:
                stream = part.append_media_stream(url, 0)
                M3u8.set_input_stream_addon_input(stream, self.proxy, headers=headers)
                item.complete = True
            else:
                for s, b in M3u8.get_streams_from_m3u8(url, self.proxy, headers=headers):
                    item.complete = True
                    part.append_media_stream(s, b)

        return item

    def __set_date(self, result_set, item):
        if "usageRights" in result_set and "availableFrom" in result_set["usageRights"] \
                and result_set["usageRights"]["availableFrom"] is not None:
            Logger.trace("Using 'usageRights.availableFrom' for date")
            # availableFrom=/Date(1540612800000+0200)/
            epoch_stamp = result_set["usageRights"]["availableFrom"][6:16]
            available_from = DateHelper.get_date_from_posix(int(epoch_stamp))
            item.set_date(available_from.year, available_from.month, available_from.day)

        elif "episodeNumberOrDate" in result_set and result_set["episodeNumberOrDate"] is not None:
            Logger.trace("Using 'episodeNumberOrDate' for date")
            date_parts = result_set["episodeNumberOrDate"].split(".")
            if len(date_parts) == 3:
                item.set_date(date_parts[2], date_parts[1], date_parts[0])

        elif "programUrlMetadata" in result_set and result_set["programUrlMetadata"] is not None:
            Logger.trace("Using 'programUrlMetadata' for date")
            date_parts = result_set["programUrlMetadata"].split("-")
            if len(date_parts) == 3:
                item.set_date(date_parts[2], date_parts[1], date_parts[0])
        return

    def __get_image(self, images, width_attribute, url_attribute):
        max_width = 0
        thumb = None
        for image_data in images:
            src = image_data[url_attribute]
            width = image_data[width_attribute]
            # No Fanart for now
            # if  width > max_width:
            #     item.fanart = src
            if max_width < width < 521:
                thumb = src

        return thumb
