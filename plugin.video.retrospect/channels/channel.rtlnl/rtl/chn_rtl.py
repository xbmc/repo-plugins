# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
from typing import Dict, Union, Any, Optional, List

from resources.lib import chn_class
from resources.lib import contenttype
from resources.lib import mediatype
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import FolderItem
from resources.lib.mediaitem import MediaItem
from resources.lib.parserdata import ParserData
from resources.lib.urihandler import UriHandler
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
        self.noImage = "rtlimage.png"
        self.poster = "rtlposter.png"

        # setup the urls
        self.mainListUri = "https://api.rtl.nl/rtlxl/missed/api/missed?dayOffset=1"

        self.baseUrl = "http://www.rtl.nl"

        # Set up the main parsing data
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.add_recent_items,
                              parser=["items"], creator=self.create_episode_item)

        self._add_data_parser("*", json=True,
                              parser=["items"], creator=self.create_api_typed_item)

        self._add_data_parser("*", updater=self.update_video_item, requires_logon=True)

        #===============================================================================================================
        # non standard items
        self.largeIconSet = dict()

        for channel in ["rtl4", "rtl5", "rtl7", "rtl8"]:
            self.largeIconSet[channel] = self.get_image_location("%slarge.png" % (channel,))

        self.__ignore_cookie_law()
        self.__authenticator = None

        #===============================================================================================================
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

        from resources.lib.authentication.rtlxlhandler import RtlXlHandler
        from resources.lib.authentication.authenticator import Authenticator
        handler = RtlXlHandler("rtlxl.nl", "3_R0XjstXd4MpkuqdK3kKxX20icLSE3FB27yQKl4zQVjVpqmgSyRCPKKLGdn5kjoKq")
        self.__authenticator = Authenticator(handler)

        # Always try to log on. If the username was changed to empty, we should clear the current
        # log in.
        username = self._get_setting("rtlxl_username", value_for_none=None)
        result = self.__authenticator.log_on(username=username, channel_guid=self.guid, setting_id="rtlxl_password")

        if not username:
            Logger.info("No username for RTL specified. Not logging in.")
            # Return True to prevent unwanted messages
            return False

        return result.logged_on

    def add_recent_items(self, data):
        """ Builds the "Recent" folder for this channel.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        recent = FolderItem("\a .: Recent :.", "", content_type=contenttype.VIDEOS)
        recent.complete = True
        recent.dontGroup = True
        items.append(recent)

        today = datetime.datetime.now()
        days = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        for offset in range(0, 7, 1):
            air_date = today - datetime.timedelta(offset)
            Logger.trace("Adding item for: %s", air_date)

            # Determine a nice display date
            day = days[air_date.weekday()]
            if offset == 0:
                day = "Vandaag"
            elif offset == 1:
                day = "Gisteren"
            elif offset == 2:
                day = "Eergisteren"
            title = "%04d-%02d-%02d - %s" % (air_date.year, air_date.month, air_date.day, day)

            url = "https://api.rtl.nl/rtlxl/missed/api/missed?dayOffset={}".format(offset)
            extra = FolderItem(title, url, content_type=contenttype.EPISODES)
            extra.complete = True
            extra.dontGroup = True
            extra.set_date(air_date.year, air_date.month, air_date.day, text="")

            recent.items.append(extra)

        news = FolderItem("\a .: Zoeken :.", "#searchSite", content_type=contenttype.NONE)
        news.complete = True
        news.dontGroup = True
        items.append(news)
        return data, items


    def create_api_typed_item(self, result_set):
        item_type = result_set["type"].lower()
        recent = "missed/api/missed" in self.parentItem.url

        if item_type == "episode" and not recent:
            return self.create_video_item(result_set)
        elif item_type == "episode" and recent:
            return self.create_video_item(result_set, include_serie_title=True)
        elif item_type == "series":
            return self.create_series_item(result_set)

        Logger.error("Missing API type: %s", item_type)
        return None

    def create_episode_item(self, result_set: Dict[str, Union[str, Dict]]):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        serie_info = result_set["series"]
        title = serie_info["title"]
        serie_id = serie_info["id"]

        url = "https://api.rtl.nl/rtlxl/related/api/related/{}".format(serie_id)
        item = FolderItem(title, url, content_type=contenttype.EPISODES)
        item.complete = True

        if "season"in result_set:
            description = result_set["season"].get("synopsis", "")
            item.description = description

        asset: Dict[str, str]
        for asset in result_set["assets"]:
            if asset["type"] == "Cover":
                item.poster = asset["url"]
            elif asset["type"] == "Poster":
                item.thumb = asset["url"]
                item.fanart = item.thumb

        return item

    def create_series_item(self, result_set: Dict[str, Union[str, Dict]]):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        title = result_set["title"]
        serie_id = result_set["id"]
        description = result_set["synopsis"]
        url = "https://api.rtl.nl/rtlxl/related/api/related/{}".format(serie_id)

        item = FolderItem(title, url, content_type=contenttype.EPISODES)
        item.complete = True
        item.description = description

        asset: Dict[str, str]
        for asset in result_set["assets"]:
            if asset["type"] == "Cover":
                item.poster = asset["url"]
            elif asset["type"] == "Poster":
                item.thumb = asset["url"]

        return item

    def create_video_item(self, result_set: Dict[str, Any], include_serie_title: bool = False) -> MediaItem:
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param result_set: The result_set of the self.episodeItemRegex.
        :param include_serie_title: Include the serie's title.

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).

        """

        Logger.trace(result_set)
        title = result_set["title"]
        if include_serie_title:
            title = "{} - {}".format(result_set["series"]["title"], title)

        uuid = result_set["id"]
        url = "https://api.rtl.nl/watch/play/api/play/xl/{}?device=web&drm=widevine&format=dash".format(uuid)
        description = result_set.get("synopsis", "")

        item = MediaItem(title, url, media_type=mediatype.EPISODE)
        item.description = description
        item.isGeoLocked = result_set["rights"].get("audience") == "ALLEEN_NL"
        item.isDrmProtected = result_set["rights"].get("audience") == "DRM"

        asset: Dict[str, str]
        for asset in result_set["assets"]:
            if asset["type"] == "Cover":
                item.poster = asset["url"]
            elif asset["type"] == "Poster":
                item.thumb = asset["url"]
            elif asset["type"] == "Still":
                item.thumb = asset["url"]

        duration = result_set.get("duration", 0)
        if duration > 0:
            item.set_info_label(MediaItem.LabelDuration, duration)

        # 2023-06-02
        date = result_set["scheduleDate"]
        year, month, day = date.split("-")
        item.set_date(year, month, day)

        return item

    def search_site(self, url: Optional[str]=None) -> List[MediaItem]:
        """ Creates an list of items by searching the site.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with an URL encoded representation of the
        text to search for.

        :param url:     Url to use to search with a %s for the search parameters.

        :return: A list with search results as MediaItems.
        :rtype: list[MediaItem]

        """

        url = "https://api.rtl.nl/rtlxl/search/api/search?query=%s"
        return chn_class.Channel.search_site(self, url)

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

        # Get the authentication part right.
        token = self.__authenticator.get_authentication_token()
        headers = {
            "Authorization": "Bearer {}".format(token)
        }
        video_data = UriHandler.open(item.url, additional_headers=headers)
        video_json = JsonHelper(video_data)
        error = video_json.get_value("error")
        if error:
            XbmcWrapper.show_notification(LanguageHelper.ErrorId, error["description"])
            return item

        license_url = video_json.get_value("licenseUrl")
        video_manifest = video_json.get_value("manifest")
        token = video_json.get_value("token")
        key_headers = {
            "Authorization": "Bearer {0}".format(token),
            "content-type": "application/octet-stream"
        }

        stream = item.add_stream(video_manifest, 0)

        from resources.lib.streams.mpd import Mpd
        license_key = Mpd.get_license_key(license_url, key_headers=key_headers, key_type="A")
        Mpd.set_input_stream_addon_input(stream, license_key=license_key)
        item.complete = True
        item.isDrmProtected = False
        return item

    def __ignore_cookie_law(self):
        """ Accepts the cookies from RTL channel in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        # the rfc2109 parameters is not valid in Python 2.4 (Xbox), so we ommit it.
        UriHandler.set_cookie(name='rtlcookieconsent', value='yes', domain='.www.rtl.nl')
        return
