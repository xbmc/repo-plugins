# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class

from resources.lib.mediaitem import MediaItem
from resources.lib.logger import Logger
from resources.lib.addonsettings import AddonSettings
from resources.lib.streams.mpd import Mpd
from resources.lib.regexer import Regexer
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.xbmcwrapper import XbmcWrapper


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
        self.videoType = None
        self.noImage = "eredivisieimage.jpg"

        # setup the urls
        self.baseUrl = "https://www.foxsports.nl"
        self.mainListUri = "https://www.foxsports.nl/videos/"
        self.swfUrl = "https://static.eredivisielive.nl/static/swf/edPlayer-1.6.2.plus.swf"

        # setup the main parsing data
        # self.episodeItemRegex = '<option[^>]+value="([^"]+)"[^=>]+(?:data-season="([^"]+)")?[^=>]*>([^<]+)</option>'
        # self.videoItemJson = ("item",)
        self._add_data_parser(
            self.mainListUri,
            parser=Regexer.from_expresso('<a [hd][^>]*ata-(?<Type>area|sport)="(?<Url>[^"]+)[^>]*>'
                                         '(?<Title>[^<]+)</a>'),
            creator=self.create_folder_item
        )

        self._add_data_parser(
            self.mainListUri,
            parser=Regexer.from_expresso(r'<a[^>]+href="/video/(?<Type>filter|meest_bekeken)/?'
                                         r'(?<Url>[^"]*)">[^<]*</a>\W+<h1[^>]*>(?<Title>[^<;]+)'
                                         r'(?:&#39;s){0,1}</h1>'),
            creator=self.create_folder_item
        )

        self._add_data_parser(
            "https://www.foxsports.nl/video/filter/fragments/",
            preprocessor=self.add_pages,
            parser=Regexer.from_expresso(r'<img[^>]+src=\'(?<Thumb>[^\']+)\'[^>]*>\W+</picture>\W+'
                                         r'<span class="[^"]+play[\w\W]{0,500}?<h1[^>]*>\W+<a href="'
                                         r'(?<Url>[^"]+)"[^>]*>(?<Title>[^<]+)</a>\W+</h1>\W+<span'
                                         r'[^>]*>(?<Date>[^>]+)</span>'),
            creator=self.create_video_item
        )

        self._add_data_parser("*", updater=self.update_video_item)

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def add_pages(self, data):
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

        Logger.info("Adding pages")

        # extract the current page from:
        # http://www.foxsports.nl/video/filter/fragments/1/alle/tennis/
        current_pages = Regexer.do_regex(r'(.+filter/fragments)/(\d+)/(.+)', self.parentItem.url)
        if not current_pages:
            return data, []

        current_page = current_pages[0]
        items = []

        url = "%s/%s/%s" % (current_page[0], int(current_page[1]) + 1, current_page[2])
        page_item = MediaItem(LanguageHelper.get_localized_string(LanguageHelper.MorePages), url)
        page_item.dontGroup = True
        items.append(page_item)

        return data, items

    def create_folder_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        if result_set["Type"] == "sport":
            # http://www.foxsports.nl/video/filter/alle/tennis/
            url = "%s/video/filter/fragments/1/alle/%s/" % (self.baseUrl, result_set["Url"])
        elif result_set["Type"] == "meest_bekeken":
            url = "%s/video/filter/fragments/1/meer" % (self.baseUrl, )
        else:
            # http://www.foxsports.nl/video/filter/samenvattingen/
            url = "%s/video/filter/fragments/1/%s/" % (self.baseUrl, result_set["Url"])

        title = result_set["Title"]
        if not title[0].isupper():
            title = "%s%s" % (title[0].upper(), title[1:])
        item = MediaItem(title, url)
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

        Logger.trace(result_set)

        url = "%s%s" % (self.baseUrl, result_set["Url"])
        item = MediaItem(result_set["Title"], url)
        item.type = "video"
        item.thumb = result_set["Thumb"]
        item.complete = False
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

        if not AddonSettings.use_adaptive_stream_add_on(with_encryption=False):
            Logger.error("Cannot playback video without adaptive stream addon")
            return item

        # https://www.foxsports.nl/api/video/videodata/2945190
        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=item.HttpHeaders)
        video_id = Regexer.do_regex(r'data-videoid="(\d+)" ', data)[-1]
        data = UriHandler.open("https://www.foxsports.nl/api/video/videodata/%s" % (video_id,),
                               proxy=self.proxy, additional_headers=item.HttpHeaders, no_cache=True)
        stream_id = Regexer.do_regex('<uri>([^>]+)</uri>', data)[-1]

        # POST https://d3api.foxsports.nl/api/V2/entitlement/tokenize
        post_data = {
          "Type": 1,
          "User": "",
          "VideoId": "{0}".format(video_id),
          "VideoSource": "{0}".format(stream_id),
          "VideoKind": "vod",
          "AssetState": "3",
          "PlayerType": "HTML5",
          "VideoSourceFormat": "DASH",
          "VideoSourceName": "DASH",
          # "VideoSourceFormat": "HLS",
          # "VideoSourceName": "HLS",
          "DRMType": "widevine",
          "AuthType": "Token",
          "ContentKeyData": "",
          "Other__": "playerName=HTML5-Web-vod|ae755267-8482-455b-9055-529b643ece1d|"
                     "undefined|undefined|undefined|2945541|HTML5|web|diva.MajorVersion=4|"
                     "diva.MinorVersion=2|diva.PatchVersion=13"
        }

        data = UriHandler.open("https://d3api.foxsports.nl/api/V2/entitlement/tokenize",
                               json=post_data, no_cache=True, proxy=self.proxy)
        stream_info = JsonHelper(data)
        stream_url = stream_info.get_value("ContentUrl")
        if not stream_url:
            message = "Protected stream: {0}".format(stream_info.get_value("Message"))
            XbmcWrapper.show_notification(None, message,
                                          notification_type=XbmcWrapper.Error, display_time=5000)

        license_url = stream_info.get_value("LicenseURL")
        part = item.create_new_empty_media_part()
        stream = part.append_media_stream(stream_url, 0)
        license_key = Mpd.get_license_key(license_url)
        Mpd.set_input_stream_addon_input(stream, proxy=self.proxy, license_key=license_key)
        return item
