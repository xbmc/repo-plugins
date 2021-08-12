# SPDX-License-Identifier: GPL-3.0-or-later
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.parserdata import ParserData

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

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = "channel9image.png"

        # setup the urls
        self.mainListUri = "https://channel9.msdn.com/Browse"
        self.baseUrl = "https://channel9.msdn.com"

        # setup the main parsing data
        main_list_regex = r'<li>\W+<a href="([^"]+Browse[^"]+)">(\D[^<]+)</a>'  # used for the ParseMainList
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              parser=main_list_regex, creator=self.create_episode_item)

        folder_regex = r'<a[^>]+href="(?<url>[^"]+)"[^>]*>\W*<img[^>]+src="(?<thumburl>[^"]+)"[^>]*alt="(?<title>[^"]+)"[^>]*>\W*(?:<div[^>]*>\W*<time[^>]+datetime="(?<date>[^"]+)"[^>]*>[^>]+>\W*</div>)?\W*</a>\W*</article'
        folder_regex = Regexer.from_expresso(folder_regex)
        self._add_data_parser("*", parser=folder_regex, creator=self.create_folder_item)

        page_regex = r'<a href="([^"]+page=)(\d+)"'
        page_regex = Regexer.from_expresso(page_regex)
        self.pageNavigationRegexIndex = 1
        self._add_data_parser("*", parser=page_regex, creator=self.create_page_item)

        video_regex = r'<a[^>]+href="(?<url>[^"]+)"[^>]*>\W*<img[^>]+src="(?<thumburl>[^"]+)"[^>]*alt="(?<title>[^"]+)"[^>]*>\W*<tim'
        video_regex = Regexer.from_expresso(video_regex)
        self._add_data_parser("*", parser=video_regex, creator=self.create_video_item,
                              updater=self.update_video_item)

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

        url = "{}{}".format(self.baseUrl, HtmlEntityHelper.convert_html_entities(result_set[0]))
        name = result_set[1]

        if name == "Tags":
            return None
        if name == "Authors":
            return None
        if name == "Most Viewed":
            return None
        if name == "Top Rated":
            name = "Recent"
            url = "https://channel9.msdn.com/Feeds/RSS"
            item = MediaItem(name, url)
            item.complete = True
            return item

        items = []
        sorts = {
            "?sort=atoz": "A-Z",
            "?sort=recen": LanguageHelper.get_localized_string(LanguageHelper.Recent)
        }

        for sort, title in sorts.items():
            sort_url = "%s%s" % (url, sort)
            sort_name = "%s - %s" % (name, title)
            item = MediaItem(sort_name, sort_url)
            item.complete = True
            items.append(item)
        return items

    def create_folder_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        item = chn_class.Channel.create_folder_item(self, result_set)
        if not item:
            return item

        if "date" not in result_set or not result_set["date"]:
            return item

        data_time = result_set["date"]
        date_str = data_time.split(" ")[0]
        time_stamp = DateHelper.get_date_from_string(date_str, "%Y-%m-%d")
        item.set_date(*time_stamp[0:6])
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

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.open(item.url)

        urls = Regexer.do_regex(r'<a[^"]+href="([^"]+.(?:wmv|mp4))"[^>]*>\W*(High|Medium|Mid|Low|MP4)', data)
        for url in urls:
            if url[1].lower() == "high":
                bitrate = 2000
            elif url[1].lower() == "medium" or url[1].lower() == "mid":
                bitrate = 1200
            elif url[1].lower() == "low" or url[1].lower() == "mp4":
                bitrate = 200
            else:
                bitrate = 0
            item.add_stream(HtmlEntityHelper.convert_html_entities(url[0]), bitrate)

        item.complete = True
        return item
