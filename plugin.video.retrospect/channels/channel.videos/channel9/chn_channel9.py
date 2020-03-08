# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.backtothefuture import PY2
if PY2:
    # noinspection PyUnresolvedReferences
    import urlparse as parse
else:
    # noinspection PyUnresolvedReferences
    import urllib.parse as parse

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.htmlhelper import HtmlHelper
from resources.lib.helpers.xmlhelper import XmlHelper


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
        self.noImage = "channel9image.png"

        # setup the urls
        self.mainListUri = "http://channel9.msdn.com/Browse"
        self.baseUrl = "http://channel9.msdn.com"

        # setup the main parsing data
        self.episodeItemRegex = r'<li>\W+<a href="([^"]+Browse[^"]+)">(\D[^<]+)</a>'  # used for the ParseMainList
        self.videoItemRegex = r'<item>([\W\w]+?)</item>'
        self.folderItemRegex = r'<a href="([^"]+)" class="title">([^<]+)</a>([\w\W]{0,600})</li>'
        self.folderItemRegex = "(?:%s|%s)" % (self.folderItemRegex, r'<li>\W+<a href="(/Browse[^"]+)">(\D[^<]+)')
        self.pageNavigationRegex = r'<a href="([^"]+page[^"]+)">(\d+)</a>'  # self.pageNavigationIndicationRegex
        self.pageNavigationRegexIndex = 1

        # =========================== Actual channel setup STOPS here ==============================
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

        url = parse.urljoin(self.baseUrl, HtmlEntityHelper.convert_html_entities(result_set[0]))
        name = result_set[1]

        if name == "Tags":
            return None
        if name == "Authors":
            return None
        if name == "Most Viewed":
            return None
        if name == "Top Rated":
            name = "Recent"
            url = "http://channel9.msdn.com/Feeds/RSS"
        else:
            url = "%s?sort=atoz" % (url,)

        item = MediaItem(name, url)
        item.complete = True
        return item

    def pre_process_folder_list(self, data):
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
        data = data.replace("&#160;", " ")

        page_nav = data.find('<div class="pageNav">')
        if page_nav > 0:
            data = data[0:page_nav]

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_page_item(self, result_set):
        """ Creates a MediaItem of type 'page' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'page'.
        :rtype: MediaItem|None

        """

        url = parse.urljoin(self.baseUrl, HtmlEntityHelper.convert_html_entities(result_set[0]))
        item = MediaItem(result_set[self.pageNavigationRegexIndex], url)
        item.type = "page"
        item.complete = True

        Logger.trace("Created '%s' for url %s", item.name, item.url)
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

        if len(result_set) > 3 and result_set[3] != "":
            Logger.debug("Sub category folder found.")
            url = parse.urljoin(self.baseUrl, HtmlEntityHelper.convert_html_entities(result_set[3]))
            name = "\a.: %s :." % (result_set[4],)
            item = MediaItem(name, url)
            item.complete = True
            item.type = "folder"
            return item

        url = parse.urljoin(self.baseUrl, HtmlEntityHelper.convert_html_entities(result_set[0]))
        name = HtmlEntityHelper.convert_html_entities(result_set[1])

        helper = HtmlHelper(result_set[2])
        description = helper.get_tag_content("div", {'class': 'description'})

        item = MediaItem(name, "%s/RSS" % (url,))
        item.type = 'folder'
        item.description = description.strip()

        date = helper.get_tag_content("div", {'class': 'date'})
        if date == "":
            date = helper.get_tag_content("span", {'class': 'lastPublishedDate'})

        if not date == "":
            date_parts = Regexer.do_regex(r"(\w+) (\d+)[^<]+, (\d+)", date)
            if len(date_parts) > 0:
                date_parts = date_parts[0]
                month_part = date_parts[0].lower()
                day_part = date_parts[1]
                year_part = date_parts[2]

                try:
                    month = DateHelper.get_month_from_name(month_part, "en")
                    item.set_date(year_part, month, day_part)
                except:
                    Logger.error("Error matching month: %s", month_part, exc_info=True)

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

        # Logger.Trace(result_set)

        xml_data = XmlHelper(result_set)
        title = xml_data.get_single_node_content("title")
        url = xml_data.get_single_node_content("link")
        description = xml_data.get_single_node_content("description")
        description = description.replace("<![CDATA[ ", "").replace("]]>", "").replace("<p>", "").replace("</p>", "\n")

        item = MediaItem(title, url)
        item.type = 'video'
        item.complete = False
        item.description = description

        date = xml_data.get_single_node_content("pubDate")
        date_result = Regexer.do_regex(r"\w+, (\d+) (\w+) (\d+)", date)[-1]
        day = date_result[0]
        month_part = date_result[1].lower()
        year = date_result[2]

        try:
            month_lookup = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
            month = month_lookup.index(month_part) + 1
            item.set_date(year, month, day)
        except:
            Logger.error("Error matching month: %s", result_set[4].lower(), exc_info=True)

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

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.open(item.url)

        urls = Regexer.do_regex('<a href="([^"]+.(?:wmv|mp4))">(High|Medium|Mid|Low|MP4)', data)
        media_part = item.create_new_empty_media_part()
        for url in urls:
            if url[1].lower() == "high":
                bitrate = 2000
            elif url[1].lower() == "medium" or url[1].lower() == "mid":
                bitrate = 1200
            elif url[1].lower() == "low" or url[1].lower() == "mp4":
                bitrate = 200
            else:
                bitrate = 0
            media_part.append_media_stream(HtmlEntityHelper.convert_html_entities(url[0]), bitrate)

        item.complete = True
        return item
