# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import time
import base64
from resources.lib import chn_class

from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.encodinghelper import EncodingHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
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

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "nosnlimage.png"

        # setup the urls
        # self.mainListUri = "http://nos.nl/"
        self.mainListUri = "#getcategories"

        # we need specific headers: APK:NosHttpClientHelper.java
        salt = int(time.time())
        # Some more work for keys that seemed required.
        # Logger.Trace("Found Salt: %s and Key: %s", salt, key)
        # key = "%sRM%%j%%l@g@w_A%%" % (salt,)
        # key = EncodingHelper.encode_md5(key, toUpper=False)
        # self.httpHeaders = {"X-NOS-App": "Google/x86;Android/4.4.4;nl.nos.app/3.1",
        #                     "X-NOS-Salt": salt,
        #                     "X-NOS-Key": key}

        user_agent = "%s;%d;%s/%s;Android/%s;nl.nos.app/%s" % ("nos", salt, "Google", "Nexus", "6.0", "5.1.1")
        string = ";UB}7Gaji==JPHtjX3@c%s" % (user_agent, )
        string = EncodingHelper.encode_md5(string, to_upper=False).zfill(32)
        xnos = string + base64.b64encode(user_agent)
        self.httpHeaders = {"X-Nos": xnos}

        self.baseUrl = "http://nos.nl"

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, preprocessor=self.get_categories)
        self._add_data_parser("*",
                              # No longer used: preprocessor=self.AddNextPage,
                              json=True,
                              parser=['items', ],
                              creator=self.create_json_video, updater=self.update_json_video)
        self._add_data_parser("*",
                              json=True,
                              parser=['links', ],
                              creator=self.create_page_item)

        #===============================================================================================================
        # non standard items
        # self.__ignore_cookie_law()
        self.__pageSize = 50

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def get_categories(self, data):
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

        Logger.info("Creating categories")
        items = []

        cats = {
            "Meest Bekeken": "https://api.nos.nl/mobile/videos/most-viewed/phone.json",
            "Nieuws": "https://api.nos.nl/nosapp/v3/items?mainCategories=nieuws&types=video&limit={0}".format(self.__pageSize),
            "Sport": "https://api.nos.nl/nosapp/v3/items?mainCategories=sport&types=video&limit={0}".format(self.__pageSize),
            "Alles": "https://api.nos.nl/nosapp/v3/items?types=video&limit={0}".format(self.__pageSize),
        }

        for cat in cats:
            item = MediaItem(cat, cats[cat])
            item.complete = True
            items.append(item)

        Logger.debug("Creating categories finished")
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

        items = []
        if 'next' in result_set:
            title = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
            url = result_set['next']
            item = MediaItem(title, url)
            items.append(item)

        return items

    def create_json_video(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param dict[str,any|None] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        video_id = result_set['id']

        # Categories to use
        # category = result_set["maincategory"].title()
        # subcategory = result_set["subcategory"].title()

        url = "https://api.nos.nl/mobile/video/%s/phone.json" % (video_id, )
        item = MediaItem(result_set['title'], url, type="video")
        if 'image' in result_set:
            images = result_set['image']["formats"]
            matched_image = images[-1]
            for image in images:
                if image["width"] >= 720:
                    matched_image = image
                    break
            item.thumb = matched_image["url"].values()[0]

        item.description = result_set["description"]
        item.complete = False
        item.isGeoLocked = result_set.get("geoprotection", False)

        # set the date and time
        date = result_set["published_at"]
        time_stamp = DateHelper.get_date_from_string(date, date_format="%Y-%m-%dT%H:%M:%S+{0}".format(date[-4:]))
        item.set_date(*time_stamp[0:6])
        return item

    def update_json_video(self, item):
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

        Logger.debug('Starting update_video_item: %s', item.name)

        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=self.httpHeaders)
        json_data = JsonHelper(data)
        streams = json_data.get_value("formats")
        if not streams:
            return item

        qualities = {"720p": 1600, "480p": 1200, "360p": 500, "other": 0}  # , "http-hls": 1500, "3gp-mob01": 300, "flv-web01": 500}
        part = item.create_new_empty_media_part()
        urls = []
        for stream in streams:
            url = stream["url"].values()[-1]
            if url in urls:
                # duplicate url, ignore
                continue

            urls.append(url)

            # actually process the url
            if ".m3u8" not in url:
                part.append_media_stream(
                    url=url,
                    bitrate=qualities.get(stream.get("name", "other"), 0)
                )
                item.complete = True
            # elif AddonSettings.use_adaptive_stream_add_on():
            #     content_type, url = UriHandler.header(url, self.proxy)
            #     stream = part.append_media_stream(url, 0)
            #     M3u8.SetInputStreamAddonInput(stream, self.proxy)
            #     item.complete = True
            else:
                M3u8.update_part_with_m3u8_streams(part, url, proxy=self.proxy, channel=self)
        return item

    def __ignore_cookie_law(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        # a second cookie seems to be required
        UriHandler.set_cookie(name='npo_cc', value='tmp', domain='.nos.nl')
        return
