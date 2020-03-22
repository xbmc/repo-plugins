# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.urihandler import UriHandler
from resources.lib.streams.npostream import NpoStream
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.datehelper import DateHelper


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
        self.noImage = "schooltvimage.jpg"
        self.baseUrl = "http://apps-api.uitzendinggemist.nl"
        self.mainListUri = "http://m.schooltv.nl/api/v1/programmas.json"

        # mainlist stuff
        self._add_data_parser("http://m.schooltv.nl/api/v1/programmas.json", json=True,
                              name="All Shows (API v1)",
                              preprocessor=self.add_categories,
                              parser=[], creator=self.create_episode_item)

        self._add_data_parser("http://m.schooltv.nl/api/v1/programmas/tips.json?size=100", json=True,
                              name="Tips (API v1)",
                              parser=[], creator=self.create_episode_item)

        self._add_data_parsers(["http://m.schooltv.nl/api/v1/programmas/",
                                "http://m.schooltv.nl/api/v1/categorieen/",
                                "http://m.schooltv.nl/api/v1/leeftijdscategorieen/"],
                               json=True,
                               name="Paged Video Items (API v1)",
                               preprocessor=self.add_page_items,
                               parser=['results', ], creator=self.create_video_item)

        self._add_data_parser("http://m.schooltv.nl/api/v1/categorieen.json?size=100", json=True,
                              name="Categories (API v1)",
                              parser=[], creator=self.create_category)

        self._add_data_parser("http://m.schooltv.nl/api/v1/afleveringen/", json=True,
                              name="Video Updater (API v1)",
                              updater=self.update_video_item)

        # ===============================================================================================================
        # non standard items
        self.__PageSize = 100

        # ===============================================================================================================
        # Test cases:
        # schooltv-weekjournaal: paging
        # Aarde & Ruimte: -> has both ODI+MP4 and ODI+M3U8
        # Wiskunden tweede fase: fylosofie en waarheid - waaronaan.resources.lib.-> ODI+M3u8

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param dict[str,str|dict] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        url = "http://m.schooltv.nl/api/v1/programmas/%s/afleveringen.json?size=%s&sort=Nieuwste" % (result_set['mid'], self.__PageSize)
        item = MediaItem(result_set['title'], url)
        item.thumb = result_set.get('image', self.noImage)
        item.description = result_set.get('description', None)
        age_groups = result_set.get('ageGroups', ['Onbekend'])
        item.description = "%s\n\nLeeftijden: %s" % (item.description, ", ".join(age_groups))
        return item

    def add_categories(self, data):
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

        cat = MediaItem("\b.: Categorie&euml;n :.",
                        "http://m.schooltv.nl/api/v1/categorieen.json?size=100")
        cat.complete = True
        cat.dontGroup = True
        items.append(cat)

        tips = MediaItem("\b.: Tips :.",
                         "http://m.schooltv.nl/api/v1/programmas/tips.json?size=100")
        tips.complete = True
        tips.dontGroup = True
        items.append(tips)

        data = JsonHelper(data)
        ages = MediaItem("\b.: Leeftijden :.", "")
        ages.complete = True
        ages.dontGroup = True
        for age in ("0-4", "5-6", "7-8", "9-12", "13-15", "16-18"):
            age_item = MediaItem(
                "%s Jaar" % (age,),
                "http://m.schooltv.nl/api/v1/leeftijdscategorieen/%s/afleveringen.json?"
                "size=%s&sort=Nieuwste" % (age, self.__PageSize))
            age_item.complete = True
            age_item.dontGroup = True
            ages.items.append(age_item)

            # We should list programs instead of videos, so just prefill them here.
            for program in data.get_value():
                if age in program['ageGroups']:
                    age_item.items.append(self.create_episode_item(program))
        items.append(ages)

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_category(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        title = HtmlEntityHelper.url_encode(result_set['title'])
        url = "http://m.schooltv.nl/api/v1/categorieen/%s/afleveringen.json?sort=Nieuwste&age_filter=&size=%s" % (title, self.__PageSize)
        item = MediaItem(result_set['title'], url)
        item.thumb = result_set.get('image', self.noImage)
        item.description = "Totaal %(count)s videos" % result_set
        return item

    def add_page_items(self, data):
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
        json = JsonHelper(data)
        total_results = json.get_value("totalResults")
        from_value = json.get_value("from")
        size_value = json.get_value("size")

        if from_value + size_value < total_results:
            more_pages = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
            url = self.parentItem.url.split('?')[0]
            url = "%s?size=%s&from=%s&sort=Nieuwste" % (url, size_value, from_value+size_value)
            Logger.debug("Adding next-page item from %s to %s", from_value + size_value, from_value + size_value + size_value)

            next_page = MediaItem(more_pages, url)
            next_page.dontGroup = True
            items.append(next_page)

        Logger.debug("Pre-Processing finished")
        return json, items

    def create_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict[str,str|dict] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        title = result_set["title"]
        if title is None:
            Logger.warning("Found item with all <null> items. Skipping")
            return None

        if "subtitle" in result_set and result_set['subtitle'].lower() not in title.lower():
            title = "%(title)s - %(subtitle)s" % result_set

        url = "http://m.schooltv.nl/api/v1/afleveringen/%(mid)s.json" % result_set
        item = MediaItem(title, url)
        item.description = result_set.get("description", "")
        age_groups = result_set.get('ageGroups', ['Onbekend'])
        item.description = "%s\n\nLeeftijden: %s" % (item.description, ", ".join(age_groups))

        item.thumb = result_set.get("image", "")
        item.type = 'video'
        item.complete = False
        item.set_info_label("duration", result_set['duration'])

        if "publicationDate" in result_set:
            broadcast_date = DateHelper.get_date_from_posix(int(result_set['publicationDate']))
            item.set_date(broadcast_date.year,
                          broadcast_date.month,
                          broadcast_date.day,
                          broadcast_date.hour,
                          broadcast_date.minute,
                          broadcast_date.second)
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

        part = item.create_new_empty_media_part()
        part.Subtitle = NpoStream.get_subtitle(json.get_value("mid"), proxy=self.proxy)

        for stream in json.get_value("videoStreams"):
            if not stream["url"].startswith("odi"):
                part.append_media_stream(stream["url"], stream["bitrate"] / 1000)
                item.complete = True

        if item.has_media_item_parts():
            return item

        for s, b in NpoStream.get_streams_from_npo(None, json.get_value("mid"), proxy=self.proxy):
            item.complete = True
            part.append_media_stream(s, b)

        return item
