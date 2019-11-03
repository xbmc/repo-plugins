# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import datetime

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.regexer import Regexer
from resources.lib.helpers import subtitlehelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.mpd import Mpd
from resources.lib.channelinfo import ChannelInfo
from resources.lib.addonsettings import AddonSettings

from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "svtimage.png"

        # Setup the urls
        self.mainListUri = "https://www.svtplay.se/api/all_titles_and_singles"
        self.baseUrl = "https://www.svtplay.se"
        self.swfUrl = "https://media.svt.se/swf/video/svtplayer-2016.01.swf"

        # In case we use the All Titles and Singles with the API
        self._add_data_parser("https://www.svtplay.se/api/all_titles_and_singles",
                              match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.add_live_items_and_genres,
                              parser=[], creator=self.create_json_episode_item)

        self._add_data_parser("https://www.svtplay.se/api/title?slug=",
                              json=True, name="JSON API Videos via Slug",
                              preprocessor=self.extract_article_id,
                              parser=[], creator=self.create_json_item)

        self._add_data_parser("https://www.svtplay.se/api/title_episodes_by_article_id?articleId=",
                              json=True, name="JSON API Videos via ArticleID",
                              parser=[], creator=self.create_json_item)

        self._add_data_parser("https://api.svt.se/videoplayer-api/video/",
                              updater=self.update_video_api_item)

        # Setup channel listing based on JSON data in the HTML
        self._add_data_parser("https://www.svtplay.se/kanaler", match_type=ParserData.MatchExact,
                              name="Live streams", json=True,
                              preprocessor=self.extract_live_channel_data,
                              parser=[], creator=self.create_channel_item)

        # Special pages (using JSON) using a generic pre-processor to extract the data
        # Could also be done with
        #   - https://www.svtplay.se/api/latest?page=1&excludedTagsString=lokalt
        #   - https://www.svtplay.se/api/last_chance?page=1&excludedTagsString=lokalt
        #   - https://www.svtplay.se/populara?sida=1
        #   - https://www.svtplay.se/api/live?page=1&excludedTagsString=lokalt
        special_json_pages = r"^https?://www.svtplay.se/(senaste|sista-chansen|populara|direkt)\?sida=\d+$"
        self._add_data_parser(special_json_pages,
                              match_type=ParserData.MatchRegex, preprocessor=self.extract_json_data)
        self._add_data_parser(special_json_pages,
                              match_type=ParserData.MatchRegex, json=True,
                              parser=["gridPage", "content"],
                              creator=self.create_json_item)
        self._add_data_parser(special_json_pages,
                              match_type=ParserData.MatchRegex, json=True,
                              parser=["gridPage", "pagination"],
                              creator=self.create_json_page_item)

        # Genres/tags (using JSON)
        self._add_data_parser("https://www.svtplay.se/api/clusters", json=True,
                              name="Genre/Tags parser",
                              parser=[], creator=self.create_json_tag_item)

        self._add_data_parser("https://www.svtplay.se/api/cluster_titles_and_episodes?cluster=", json=True,
                              name="Cluster List Generator",
                              parser=[], creator=self.create_json_episode_item)

        # Categories (SVT reverted the Apollo stuff (See #1080))
        self._add_data_parser("https://www.svtplay.se/genre/",
                              preprocessor=self.extract_apollo_json_data, json=True,
                              name="Video/Folder parsers for items in a Genre/Tag")

        # Searching
        self._add_data_parser("https://www.svtplay.se/api/search?q=", json=True,
                              parser=["videosAndTitles"],
                              creator=self.create_json_item_sok)

        # Update via HTML pages
        self._add_data_parser("https://www.svtplay.se/video/", updater=self.update_video_html_item)
        self._add_data_parser("https://www.svtplay.se/klipp/", updater=self.update_video_html_item)
        # Update via the new API urls
        self._add_data_parser("https://www.svt.se/videoplayer-api/", updater=self.update_video_api_item)

        # ===============================================================================================================
        # non standard items
        self.__apollo_data = None
        self.__expires_text = LanguageHelper.get_localized_string(LanguageHelper.ExpiresAt)

        # ===============================================================================================================
        # Test cases:
        #   Affaren Ramel: just 1 folder -> should only list videos

        # ====================================== Actual channel setup STOPS here =======================================
        return

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

        url = "https://www.svtplay.se/api/search?q=%s"
        return chn_class.Channel.search_site(self, url)

    def add_live_items_and_genres(self, data):
        """ Adds the Live items, Channels and Last Episodes to the listing.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        extra_items = {
            LanguageHelper.get_localized_string(LanguageHelper.LiveTv): "https://www.svtplay.se/kanaler",
            LanguageHelper.get_localized_string(LanguageHelper.CurrentlyPlayingEpisodes): "https://www.svtplay.se/direkt?sida=1",
            LanguageHelper.get_localized_string(LanguageHelper.Search): "searchSite",
            LanguageHelper.get_localized_string(LanguageHelper.Recent): "https://www.svtplay.se/senaste?sida=1",
            LanguageHelper.get_localized_string(LanguageHelper.LastChance): "https://www.svtplay.se/sista-chansen?sida=1",
            LanguageHelper.get_localized_string(LanguageHelper.MostViewedEpisodes): "https://www.svtplay.se/populara?sida=1",
        }

        for title, url in extra_items.items():
            new_item = MediaItem("\a.: %s :." % (title, ), url)
            new_item.complete = True
            new_item.thumb = self.noImage
            new_item.dontGroup = True
            items.append(new_item)

        # https://www.svtplay.se/ajax/dokumentar/titlar?filterAccessibility=&filterRights=
        category_items = {
            "Drama": (
                "https://www.svtplay.se/genre/drama",
                "https://www.svtstatic.se/play/play5/images/categories/posters/drama-d75cd2da2eecde36b3d60fad6b92ad42.jpg"
            ),
            "Dokumentär": (
                "https://www.svtplay.se/genre/dokumentar",
                "https://www.svtstatic.se/play/play5/images/categories/posters/dokumentar-00599af62aa8009dbc13577eff894b8e.jpg"
            ),
            "Humor": (
                "https://www.svtplay.se/genre/humor",
                "https://www.svtstatic.se/play/play5/images/categories/posters/humor-abc329317eedf789d2cca76151213188.jpg"
            ),
            "Livsstil": (
                "https://www.svtplay.se/genre/livsstil",
                "https://www.svtstatic.se/play/play5/images/categories/posters/livsstil-2d9cd77d86c086fb8908ce4905b488b7.jpg"
            ),
            "Underhållning": (
                "https://www.svtplay.se/genre/underhallning",
                "https://www.svtstatic.se/play/play5/images/categories/posters/underhallning-a60da5125e715d74500a200bd4416841.jpg"
            ),
            "Kultur": (
                "https://www.svtplay.se/genre/kultur",
                "https://www.svtstatic.se/play/play5/images/categories/posters/kultur-93dca50ed1d6f25d316ac1621393851a.jpg"
            ),
            "Samhälle & Fakta": (
                "https://www.svtplay.se/genre/samhalle-och-fakta",
                "https://www.svtstatic.se/play/play5/images/categories/posters/samhalle-och-fakta-3750657f72529a572f3698e01452f348.jpg"
            ),
            "Film": (
                "https://www.svtplay.se/genre/film",
                "https://www.svtstatic.se/image/medium/480/20888292/1548755428"
            ),
            "Barn": (
                "https://www.svtplay.se/genre/barn",
                "https://www.svtstatic.se/play/play5/images/categories/posters/barn-c17302a6f7a9a458e0043b58bbe8ab79.jpg"
            ),
            "Nyheter": (
                "https://www.svtplay.se/genre/nyheter",
                "https://www.svtstatic.se/play/play6/images/categories/posters/nyheter.e67ff1b5770152af4690ad188546f9e9.jpg"
            ),
            "Sport": (
                "https://www.svtplay.se/genre/sport",
                "https://www.svtstatic.se/play/play6/images/categories/posters/sport.98b65f6627e4addbc4177542035ea504.jpg"
            )
        }

        category_title = "\a.: {} :.".format(LanguageHelper.get_localized_string(LanguageHelper.Categories))
        new_item = MediaItem(category_title, "https://www.svtplay.se/genre")
        new_item.complete = True
        new_item.thumb = self.noImage
        new_item.dontGroup = True
        for title, (url, thumb) in category_items.items():
            cat_item = MediaItem(title, url)
            cat_item.complete = True
            cat_item.thumb = thumb or self.noImage
            cat_item.dontGroup = True
            new_item.items.append(cat_item)
        items.append(new_item)

        genre_tags = "\a.: {}/{} :.".format(
            LanguageHelper.get_localized_string(LanguageHelper.Genres),
            LanguageHelper.get_localized_string(LanguageHelper.Tags)
        )
        new_item = MediaItem(genre_tags, "https://www.svtplay.se/api/clusters")
        new_item.complete = True
        new_item.thumb = self.noImage
        new_item.dontGroup = True
        items.append(new_item)

        return data, items

    def extract_json_data(self, data):
        """ Extracts JSON data from the HTML for __svtplay and __reduxStore json data.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        return self.__extract_json_data(data, "(?:__svtplay|__reduxStore)")

    def extract_apollo_json_data(self, data):
        """ Extracts JSON data from the HTML for __svtplay_apollo json data.

        :param str|unicode data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        data, items = self.__extract_json_data(data, "(?:__svtplay_apollo)")
        self.__apollo_data = JsonHelper(data).json
        for k, v in self.__apollo_data.items():
            item = self.create_json_genre_item(v)
            if item:
                items.append(item)
        return data, items

    def extract_slug_data(self, data):
        """ Extracts the correct Slugged Data for tabbed items

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Extracting Slugged data during pre-processing")
        data, items = self.extract_json_data(data)

        json = JsonHelper(data)
        slugs = json.get_value("relatedVideoContent", "relatedVideosAccordion")
        for slug_data in slugs:
            tab_slug = "?tab=%s" % (slug_data["slug"], )
            if not self.parentItem.url.endswith(tab_slug):
                continue

            for item in slug_data["videos"]:
                i = self.create_json_item(item)
                if i:
                    items.append(i)

        return data, items

    def create_json_genre_item(self, result_set):
        """ Creates a MediaItem of type 'folder/video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        if "__typename" not in result_set:
            return None

        item_type = result_set["__typename"].lower()
        if item_type not in ("episode", "single", "clip", "tvseries") or "name" not in result_set:
            return None

        Logger.trace("%s->%s", item_type, result_set)
        title = result_set["name"]
        if item_type == 'episode' and "parent" in result_set:
            # noinspection PyTypeChecker
            parent_data = self.__apollo_data[result_set["parent"]["id"]]
            parent_title = parent_data["name"]
            title = "{} - {}".format(parent_title, title)

        if item_type == "clip":
            url = "https://www.svtplay.se/klipp/{}/".format(result_set["id"])

        elif "id" in result_set:
            url = "https://www.svtplay.se/api/title_episodes_by_article_id?articleId={}".format(result_set['id'])

        elif "urls" in result_set:
            # noinspection PyTypeChecker
            url_data = self.__apollo_data[result_set["urls"]["id"]]
            url = url_data["svtplay"]
            url = "{}{}".format(self.baseUrl, url)
        else:
            Logger.debug("No url found for: %s", title)
            return None

        item = MediaItem(title, url)
        item.description = result_set.get("longDescription")
        item.fanart = self.parentItem.fanart
        item.type = "video" if item_type != "tvseries" else "folder"

        if "image" in result_set:
            # noinspection PyTypeChecker
            image = result_set["image"]["id"]
            image_data = self.__apollo_data[image]
            image_url = "https://www.svtstatic.se/image/medium/520/{id}/{changed}".format(**image_data)
            item.thumb = image_url

        if "restrictions" in result_set:
            # noinspection PyTypeChecker
            restrictions = self.__apollo_data[result_set["restrictions"]["id"]]
            item.isGeoLocked = restrictions.get('onlyAvailableInSweden', False)

        duration = result_set.get("duration")
        if bool(duration):
            item.set_info_label("duration", duration)

        valid_to = result_set.get("validTo")
        if bool(valid_to):
            self.__set_expire_time(valid_to, item)

        return item

    # Used at the moment
    def extract_article_id(self, data):
        """ Extracts the correct article_id from the json and fetches the data for that id

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """
        items = []

        json = JsonHelper(data)
        article_id = json.get_value("articleId")
        if not article_id:
            return None, items

        url = "https://www.svtplay.se/api/title_episodes_by_article_id?articleId={}".format(article_id)
        data = UriHandler.open(url, proxy=self.proxy)
        return data, items

    # Used at the moment
    def create_json_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        if "titleArticleId" in result_set:
            return None

        url = result_set['contentUrl']
        url = "https://www.svtplay.se/api/title?slug={0}".format(url.strip("/"))
        if "video/" in url:
            return None

        item = MediaItem(result_set['programTitle'], url)
        item.icon = self.icon
        item.isGeoLocked = result_set.get('onlyAvailableInSweden', False)
        item.description = result_set.get('description')

        thumb = self.noImage
        if "poster" in result_set:
            thumb = result_set["poster"]
            thumb = self.__get_thumb(thumb or self.noImage)

        item.thumb = thumb
        return item

    def create_json_item_sok(self, result_set):
        """ Creates a new MediaItem for search results.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        content_type = result_set["contentType"].lower()

        if content_type == "titel":
            return self.create_json_episode_item(result_set)
        elif content_type == "videoepisod":
            return self.create_json_item(result_set)
        elif content_type == "singel":
            return self.create_json_item(result_set)
        elif content_type == "videoklipp":
            return self.create_json_item(result_set)
        else:
            Logger.warning("Missing contentType: %s", content_type)
            return None

    def create_json_page_item(self, result_set):
        """ Creates a MediaItem of type 'page' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'page'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        if "nextPageUrl" not in result_set:
            return None

        title = "\b.: %s :." % (LanguageHelper.get_localized_string(LanguageHelper.MorePages),)
        url = "%s%s" % (self.baseUrl, result_set["nextPageUrl"])
        item = MediaItem(title, url)
        item.icon = self.icon
        item.thumb = self.noImage
        item.complete = True
        return item

    def create_json_tag_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """
        Logger.trace(result_set)

        url = "https://www.svtplay.se/api/cluster_titles_and_episodes?cluster={}".format(result_set['slug'])

        genre = MediaItem(result_set['name'], url)
        genre.icon = self.icon
        genre.description = result_set.get('description')
        genre.fanart = result_set.get('backgroundImage') or self.parentItem.fanart
        genre.fanart = self.__get_thumb(genre.fanart, thumb_size="/extralarge/")
        genre.thumb = result_set.get('thumbnailImage') or self.noImage
        genre.thumb = self.__get_thumb(genre.thumb)
        return genre

    def create_json_genre(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        genres = []

        for cluster in result_set['clusters']:
            Logger.trace(cluster)
            url = "%s%s" % (self.baseUrl, cluster['contentUrl'])
            genre = MediaItem(cluster['name'], url)
            genre.icon = self.icon
            genre.description = cluster.get('description')
            genre.fanart = cluster.get('backgroundImage') or self.parentItem.fanart
            genre.fanart = self.__get_thumb(genre.fanart, thumb_size="/extralarge/")
            genre.thumb = cluster.get('thumbnailImage') or self.noImage
            genre.thumb = self.__get_thumb(genre.thumb)
            genres.append(genre)

        return genres

    def create_json_item(self, result_set):  # NOSONAR
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

        Logger.trace(result_set)

        # determine the title
        program_title = result_set.get("programTitle", "") or ""
        show_title = result_set.get("title", "") or ""
        if show_title == "" and program_title != "":
            title = program_title
        elif show_title != "" and program_title == "":
            title = show_title
        elif program_title == "" and show_title == "":
            Logger.warning("Could not find title for item: %s", result_set)
            return None
        elif show_title != "" and show_title != program_title:
            title = "%s - %s" % (program_title, show_title)
        else:
            # they are the same
            title = show_title  # NOSONAR

        if "live" in result_set and result_set["live"]:
            title = "%s (&middot;Live&middot;)" % (title, )

        item_type = result_set.get("contentType")
        if "contentUrl" in result_set:
            if "versions" in result_set and bool(result_set["versions"]):
                video_id = result_set["versions"][0]["id"]
            else:
                video_id = result_set["id"]
            url = "https://api.svt.se/videoplayer-api/video/{}".format(video_id)
        else:
            url = result_set["url"]
        broad_cast_date = result_set.get("broadcastDate", None)

        if item_type in ("videoEpisod", "videoKlipp", "singel"):
            if "/video/" not in url and "/klipp/" not in url:
                Logger.warning("Found video item without a /video/ or /klipp/ url.")
                return None
            item_type = "video"
            if "programVersionId" in result_set:
                url = "https://www.svt.se/videoplayer-api/video/%s" % (result_set["programVersionId"],)
            elif not url.startswith("http"):
                url = "%s%s" % (self.baseUrl, url)
        else:
            item_type = "folder"
            url = "%s%s" % (self.baseUrl, url)

        item = MediaItem(title, url)
        item.icon = self.icon
        item.type = item_type
        item.isGeoLocked = result_set.get("onlyAvailableInSweden", False)
        item.description = result_set.get("description", "")

        if "season" in result_set and "episodeNumber" in result_set and result_set["episodeNumber"]:
            season = int(result_set["season"])
            episode = int(result_set["episodeNumber"])
            if season > 0 and episode > 0:
                item.name = "s%02de%02d - %s" % (season, episode, item.name)
                item.set_season_info(season, episode)

        thumb = self.noImage
        if self.parentItem:
            thumb = self.parentItem.thumb

        for image_key in ("image", "imageMedium", "thumbnailMedium", "thumbnail", "poster"):
            if image_key in result_set and result_set[image_key] is not None:
                thumb = result_set[image_key]
                break

        item.thumb = self.__get_thumb(thumb or self.noImage)

        if broad_cast_date is not None:
            if "+" in broad_cast_date:
                broad_cast_date = broad_cast_date.rsplit("+")[0]
            time_stamp = DateHelper.get_date_from_string(broad_cast_date, "%Y-%m-%dT%H:%M:%S")
            item.set_date(*time_stamp[0:6])

        # Set the expire date
        expire_date = result_set.get("expireDate")
        if expire_date is not None:
            self.__set_expire_time(expire_date, item)

        length = result_set.get("materialLength", 0)
        if length > 0:
            item.set_info_label(MediaItem.LabelDuration, length)
        return item

    def create_category_item(self, result_set):
        """ Creates a MediaItem of type 'video/folder' using the result_set from the regex.

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

        url = result_set["Url"]
        if "http://" not in url and "https://" not in url:
            url = "%s%s" % (self.baseUrl, url)

        thumb = result_set["Thumb"]
        if thumb.startswith("//"):
            thumb = "https:%s" % (thumb,)

        item = MediaItem(result_set['Title'], url)
        item.icon = self.icon
        item.thumb = thumb
        item.isGeoLocked = result_set["Abroad"] == "false"

        if result_set["Date1"] is not None and result_set["Date1"].lower() != "imorgon":
            year, month, day, hour, minutes = self.__get_date(result_set["Date1"], result_set["Date2"], result_set["Date3"])
            item.set_date(year, month, day, hour, minutes, 0)

        if "/video/" in url:
            item.type = "video"
            video_id = url.split("/")[4]
            item.url = "https://www.svtplay.se/video/%s?type=embed&output=json" % (video_id,)
        # else:
        #     # make sure we get the right tab for displaying
        #     item.url = "%s?tab=program" % (item.url, )

        return item

    def extract_live_channel_data(self, data):
        """ Adds the channel items to the listing.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        json_string, _ = self.extract_json_data(data)
        json_data = JsonHelper(json_string)
        channels = json_data.get_value("channelsPage", "schedule")
        channel_list = []
        for channel_name, channel_data in channels.items():
            if "channel" not in channel_data:
                continue
            channel_list.append(channel_data)

        json_data.json = channel_list
        return json_data, []

    def create_channel_item(self, channel):
        """ Creates a MediaItem of type 'video' for a live channel using the result_set
        from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict channel: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(channel)

        title = channel["programmeTitle"]
        episode = channel.get("episodeTitle", None)
        thumb = self.noImage
        channel_title = channel["channelName"]
        description = channel.get("description")
        channel_id = channel["channel"].lower()
        if channel_id == "svtbarn":
            channel_id = "barnkanalen"

        date_format = "%Y-%m-%dT%H:%M:%S"
        start_time = DateHelper.get_date_from_string(channel["publishingTime"][:19], date_format)
        end_time = DateHelper.get_date_from_string(channel["publishingEndTime"][:19], date_format)

        if episode:
            title = "%s: %s - %s (%02d:%02d - %02d:%02d)" \
                    % (channel_title, title, episode,
                       start_time.tm_hour, start_time.tm_min, end_time.tm_hour, end_time.tm_min)
        else:
            title = "%s: %s (%02d:%02d - %02d:%02d)" \
                    % (channel_title, title,
                       start_time.tm_hour, start_time.tm_min, end_time.tm_hour, end_time.tm_min)
        channel_item = MediaItem(
            title,
            "https://www.svt.se/videoplayer-api/video/ch-%s" % (channel_id.lower(), )
        )
        channel_item.type = "video"
        channel_item.description = description
        channel_item.isLive = True
        channel_item.isGeoLocked = True

        channel_item.thumb = thumb
        if "titlePageThumbnailIds" in channel and channel["titlePageThumbnailIds"]:
            channel_item.thumb = "https://www.svtstatic.se/image/wide/650/%s.jpg" % (channel["titlePageThumbnailIds"][0], )
        return channel_item

    def update_video_html_item(self, item):
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

        data = UriHandler.open(item.url, proxy=self.proxy)
        # Logger.Trace(data)
        data = self.extract_json_data(data)[0]
        json = JsonHelper(data, logger=Logger.instance())

        # check for direct streams:
        streams = json.get_value("videoTitlePage", "video", "videoReferences")
        subtitles = json.get_value("videoTitlePage", "video", "subtitles")

        if streams:
            Logger.info("Found stream information within HTML data")
            return self.__update_item_from_video_references(item, streams, subtitles)

        video_id = json.get_value("videoPage", "video", "id")
        # in case that did not work, try the old version.
        if not video_id:
            video_id = json.get_value("videoPage", "video", "programVersionId")
        if video_id:
            item.url = "https://api.svt.se/videoplayer-api/video/%s" % (video_id, )
        return self.update_video_api_item(item)

    def update_video_api_item(self, item):
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

        Logger.debug('Starting UpdateChannelItem for %s (%s)', item.name, self.channelName)

        data = UriHandler.open(item.url, proxy=self.proxy)

        json = JsonHelper(data, logger=Logger.instance())
        videos = json.get_value("videoReferences")
        subtitles = json.get_value("subtitleReferences")
        Logger.trace(videos)
        return self.__update_item_from_video_references(item, videos, subtitles)

    def __update_item_from_video_references(self, item, videos, subtitles=None):  # NOSONAR
        """

        :param MediaItem item:      The original MediaItem that needs updating.
        :param list[any] videos:    Videos to add.
        :param dict subtitles:      Subtitle information.

        :return: Updated MediaItem
        :rtype: MediaItem

        """

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()
        if self.localIP:
            part.HttpHeaders.update(self.localIP)

        use_input_stream = AddonSettings.use_adaptive_stream_add_on(channel=self)

        for video in videos:
            video_format = video.get("format", "")
            if not video_format:
                video_format = video.get("playerType", "")
            video_format = video_format.lower()

            if ("dash" in video_format and not video_format == "dash") or "hds" in video_format:
                Logger.debug("Skipping video format: %s", video_format)
                continue
            Logger.debug("Found video item for format: %s", video_format)

            url = video['url']
            if any(filter(lambda s: s.Url == url, part.MediaStreams)):
                Logger.debug("Skippping duplicate Stream url: %s", url)
                continue

            if video_format == "dash" and use_input_stream:
                stream = part.append_media_stream(video['url'], 1)
                Mpd.set_input_stream_addon_input(stream, self.proxy)

            elif "m3u8" in url:
                alt_index = url.find("m3u8?")
                if alt_index > 0:
                    url = url[0:alt_index + 4]

                if "-fmp4.m3u8" in url or "-lowbw.m3u8" in url:
                    Logger.trace("Ignoring: %s", url)
                    continue

                M3u8.update_part_with_m3u8_streams(
                    part,
                    url,
                    encrypted=False,
                    proxy=self.proxy,
                    headers=part.HttpHeaders,
                    channel=self
                )

            elif video["url"].startswith("rtmp"):
                # just replace some data in the URL
                part.append_media_stream(self.get_verifiable_video_url(video["url"]).replace("_definst_", "?slist="), video[1])
            else:
                part.append_media_stream(url, 0)

        if subtitles:
            Logger.info("Found subtitles to play")
            for sub in subtitles:
                sub_format = sub["format"].lower()
                url = sub["url"]
                if sub_format == "websrt":
                    sub_url = url
                # elif subFormat == "webvtt":
                #     Logger.Info("Found M3u8 subtitle, replacing with WSRT")
                #     start, name, index = sub[-1].rsplit("/", 2)
                #     subUrl = "%s/%s/%s.wsrt" % (start, name, name)
                else:
                    # look for more
                    continue

                part.Subtitle = subtitlehelper.SubtitleHelper.download_subtitle(sub_url, format="srt", proxy=self.proxy)
                # stop when finding one
                break

        item.complete = True
        return item

    def __set_expire_time(self, expire_date, item):
        expire_date = expire_date.split("+")[0].replace("T", " ")
        year = expire_date.split("-")[0]
        if len(year) == 4 and int(year) < datetime.datetime.now().year + 50:
            item.description = \
                "{}\n\n{}: {}".format(item.description or "", self.__expires_text, expire_date)

    def __get_date(self, first, second, third):
        """ Tries to parse formats for dates like "Today 9:00" or "mon 9 jun" or "Tonight 9.00"

        :param str first:   First part.
        :param str second:  Second part.
        :param str third:   Third part.

        :return:  a tuple containing: year, month, day, hour, minutes
        :rtype: tuple[int,int,int,int,int]

        """

        Logger.trace("Determining date for: ('%s', '%s', '%s')", first, second, third)
        hour = minutes = 0

        year = DateHelper.this_year()
        if first.lower() == "idag" or first.lower() == "ikv&auml;ll":  # Today or Tonight
            date = datetime.datetime.now()
            month = date.month
            day = date.day
            hour = second
            minutes = third

        elif first.lower() == "ig&aring;r":  # Yesterday
            date = datetime.datetime.now() - datetime.timedelta(1)
            month = date.month
            day = date.day
            hour = second
            minutes = third

        elif second.isdigit():
            day = int(second)
            month = DateHelper.get_month_from_name(third, "se")
            year = DateHelper.this_year()

            # if the date was in the future, it must have been last year.
            result = datetime.datetime(year, month, day)
            if result > datetime.datetime.now() + datetime.timedelta(1):
                Logger.trace("Found future date, setting it to one year earlier.")
                year -= 1

        elif first.isdigit() and third.isdigit() and not second.isdigit():
            day = int(first)
            month = DateHelper.get_month_from_name(second, "se")
            year = int(third)

        else:
            Logger.warning("Unknonw date format: ('%s', '%s', '%s')", first, second, third)
            year = month = day = hour = minutes = 0

        return year, month, day, hour, minutes

    def __get_thumb(self, thumb, thumb_size="/large/"):
        """ Converts images into the correct url format

        :param str thumb:        The original URL.
        :param str thumb_size:   The size to make them.

        :return: the actual url.
        :rtype: str
        
        """

        if "<>" in thumb:
            thumb_parts = thumb.split("<>")
            thumb_index = int(thumb_parts[1])
            thumb_stores = ["https://www.svtstatic.se/image-cms-stage/svtse",
                            "//www.svtstatic.se/image-cms-stage/svtse",
                            "https://www.svtstatic.se/image-cms/svtse",
                            "//www.svtstatic.se/image-cms/svtse",
                            "https://www.svtstatic.se/image-cms-stage/barn",
                            "//www.svtstatic.se/image-cms-stage/barn",
                            "https://www.svtstatic.se/image-cms/barn",
                            "//www.svtstatic.se/image-cms/barn"]
            thumb = "%s%s" % (thumb_stores[thumb_index], thumb_parts[-1])

        if thumb.startswith("//"):
            thumb = "https:%s" % (thumb,)

        thumb = thumb.replace("/{format}/", thumb_size)\
            .replace("/medium/", thumb_size)\
            .replace("/small/", thumb_size)
        Logger.trace(thumb)
        return thumb

    def __extract_json_data(self, data, root):
        """ Performs pre-process actions for data processing

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Extracting JSON data during pre-processing")
        data = Regexer.do_regex(r'root\[[\'"]%s[\'"]\] = ([\w\W]+?);\W*root\[' % (root,), data)[-1]
        items = []
        Logger.trace("JSON data found: %s", data)
        return data, items
