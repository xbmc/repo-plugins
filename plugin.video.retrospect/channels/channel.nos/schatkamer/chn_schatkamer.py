# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Dict, Union, List
from typing import Optional
from urllib.parse import parse_qs
from urllib.parse import urlparse

from resources.lib import chn_class, contenttype
from resources.lib import mediatype
from resources.lib.channelinfo import ChannelInfo
from resources.lib.chn_class import PreProcessorResult
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.reactrsc import NextJsParser
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.regexer import Regexer
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.mpd import Mpd
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info: ChannelInfo):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "de-schatkamer-image.jpg"

        self.mainListUri = "https://schatkamer.beeldengeluid.nl/"
        self.baseUrl = "https://schatkamer.beeldengeluid.nl/"

        # We need React Server Components
        self.httpHeaders["rsc"] = "1"

        self._add_data_parser(self.mainListUri, match_type="Exact", json=True,
                              preprocessor=self.main_list_preprocessor,
                              parser=["children", -1, "children"],
                              creator=self.create_carousel_item)

        self._add_data_parser("https://schatkamer.beeldengeluid.nl/verhaal/",
                              preprocessor=NextJsParser(key="modules", return_parent=True), json=True,
                              parser=["modules"], creator=self.create_swimlane_item,
                              updater=self.update_video_item, match_type="Regex")

        self._add_data_parsers(
            ["https://schatkamer.beeldengeluid.nl/serie/", "https://schatkamer.beeldengeluid.nl/omroep/", "https://schatkamer.beeldengeluid.nl/persoon/"],
            preprocessor=NextJsParser(key="total", return_parent=True), json=True,
            parser=["results"], creator=self.create_video_item)

        self._add_data_parser("https://schatkamer.beeldengeluid.nl/zoeken", json=True,
                              preprocessor=NextJsParser(key="total", return_parent=True),
                              parser=["results"], creator=self.create_video_item)

        self._add_data_parser("https://schatkamer.beeldengeluid.nl/serie/.+/aflevering",
                              updater=self.update_video_item, match_type="Regex")
        self._add_data_parser("https://schatkamer.beeldengeluid.nl/programma/",
                              updater=self.update_video_item)

    def main_list_preprocessor(self, data: str) -> PreProcessorResult:
        preprocessor = NextJsParser(key="data-gtm-ux-component", value="information-page-details")
        json_data, items = preprocessor(data)

        search = FolderItem(LanguageHelper.get_localized_string(LanguageHelper.Search), self.search_url,
                            content_type=contenttype.EPISODES)
        items.append(search)
        return json_data, items

    def create_carousel_item(self, result_set: Dict) -> Union[MediaItem, List[MediaItem], None]:
        result_set = result_set[-1]["children"]
        for result in result_set:
            if isinstance(result, list):
                # pyrefly: ignore [bad-assignment]
                result_set = result
                break
        result_set = result_set[-1]
        if "data" not in result_set:
            return None

        return self.create_swimlane_item(result_set["data"])

    def create_swimlane_item(self, result_set: Dict) -> Union[MediaItem, List[MediaItem], None]:
        if result_set["type"] not in ("swimlane",):
            return None

        title = result_set["title"].title()
        parent = FolderItem(title, "", content_type=contenttype.EPISODES)

        if "items" not in result_set:
            return parent

        for result in result_set["items"]:
            if "/verhaal/genre" in result["url"]:
                item = self.create_serie_item(result)
            elif "/verhaal/" in result["url"]:
                item = self.create_video_item(result)
            elif "/aflevering/" in result["url"] or "/programma/" in result["url"]:
                item = self.create_video_item(result)
            else:
                item = self.create_serie_item(result)
            if item:
                parent.items.append(item)
        return parent

    def create_serie_item(self, result_set: Dict) -> Union[MediaItem, None]:
        title = result_set["title"].title()
        url = result_set["url"]

        item = FolderItem(title, url, content_type=contenttype.EPISODES)

        if "image" in result_set and result_set["image"]:
            image = result_set["image"]["url"]
            item.set_artwork(poster=image)

        return item

    # pyrefly: ignore [bad-override]
    def create_video_item(self, result_set: Dict) -> MediaItem:
        title = result_set["title"]
        tvshow = result_set.get("seriesTitle")
        if tvshow:
            tvshow = tvshow.title()
            title = f"{tvshow} - {title}"
        else:
            title = title.title()
        url = result_set["url"]

        item = MediaItem(title, url, tv_show_title=tvshow, media_type=mediatype.EPISODE)
        item.HttpHeaders["rsc"] = "1"
        item.description = result_set.get("description", "")

        if "image" in result_set and result_set["image"]:
            image = result_set["image"]["url"]
            item.set_artwork(thumb=image)

        date_info: Optional[str] = result_set.get("date")
        if date_info and "-" in date_info:
            item.set_date(*date_info.split("-"))
        elif date_info and " " in date_info:
            day, month_name, year = date_info.split(" ")
            month = DateHelper.get_month_from_name(month_name, "nl")
            item.set_date(year, month, day)

        return item

    def search_site(self, url: Optional[str] = None, needle: Optional[str] = None) -> List[MediaItem]:
        """ Creates a list of items by searching the site.

        This method is called when and item with `self.search_url` is opened. The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with a URL encoded representation of the
        text to search for.

        :param url:     Url to use to search with an %s for the search parameters.
        :param needle:  The needle to search for.

        :return: A list with search results as MediaItems.

        """

        if not needle:
            raise ValueError("No needle present")

        url = f"https://schatkamer.beeldengeluid.nl/zoeken?q=%s&_rsc=1"
        return chn_class.Channel.search_site(self, url, needle)

    def update_video_item(self, item: MediaItem) -> MediaItem:
        data = UriHandler.open(item.url, additional_headers=item.HttpHeaders, no_cache=True)
        url = Regexer.do_regex(r"https:\/\/[^,]+\.(?:m3u8[^:]+\d{2}:|mp4)", data)[0]

        if url and url.endswith(".mp4"):
            item.add_stream(url, 0)
            item.complete = True
            return item

        # We need to pass the parameters to both the manifest, stream and update parameter as a cookie.
        url_info = urlparse(url)
        url_parameters = parse_qs(url_info.query)
        url = f"{url_info.scheme}://{url_info.netloc}{url_info.path}"
        cookie_value = ""
        for key in ("CloudFront-Key-Pair-Id", "CloudFront-Policy", "CloudFront-Signature"):
            cookie = url_parameters[key][0]
            if cookie:
                cookie_value = f"{cookie_value};{key}={cookie}"
        cookie_value = cookie_value.strip(";")

        stream = item.add_stream(url, 0)
        Mpd.set_input_stream_addon_input(
            stream,
            manifest_headers={
                "cookie": cookie_value
            },
            stream_headers={
                "cookie": cookie_value
            },
            manifest_upd_params={
                "cookie": cookie_value
            },
            # Take from the website JS file. Seems fixed.
            license_key=Mpd.get_license_key("https://widevine-dash.ezdrm.com/widevine-php/widevine-foreignkey.php?pX=E24145", "R"),
        )

        item.complete = True
        return item
