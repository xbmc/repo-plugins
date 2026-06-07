# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class, mediatype
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem
from resources.lib.regexer import Regexer
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
        # setup the urls
        self.baseUrl = "https://www.bvn.tv"

        self.noImage = "bvntvimage.png"
        self.poster = "bvntvposter.png"
        self.mainListUri = "https://www.bvn.tv/programmas/"

        episode_regex = (r'<a[^>]*href="(?<url>[^"]+)[^>]*>\W*<figure class="media">\W*<img[^>]*'
                         r'data-src="(?<thumburl>[^"]+)"[\w\W]{0,500}?<h4[^>]+>\W+'
                         r'(?<title>[^<]+?)[\W]+<')
        episode_regex = Regexer.from_expresso(episode_regex)
        self._add_data_parser(self.mainListUri, name="Mainlist and live",
                              preprocessor=self.add_live_streams,
                              parser=episode_regex, creator=self.create_episode_item)

        video_regex = (r'<a[^>]+href="(?<url>[^"]+/(?<pow>[^"]+))"[^>]*>\W*<figure[^>]+>\W+'
                       r'<img[^>]+src="(?<thumburl>[^"]+)"[\w\W]{0,1000}?<h4[^>]*>\W+'
                       r'(?<title>[^<]+?)\W+</h4>\W*<p.+class="time">\W+\w+ (?<datetime>[^"]+?)'
                       r'\W+</p>')
        video_regex = Regexer.from_expresso(video_regex)
        self._add_data_parser("https://www.bvn.tv/programma/", name="Main video listings for shows",
                              preprocessor=self.extract_episode_section,
                              parser=video_regex, creator=self.create_video_item,
                              updater=self.update_video_item)
        return

    def extract_episode_section(self, data):
        """ Extracts the section with the available episodes.

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        data = data.split("<!-- episodes -->", 1)[1]
        data = data.split("<!-- footer -->", 1)[0]

        Logger.debug("Pre-Processing finished")
        return data, items

    def add_live_streams(self, data):
        """ Adds the live streams

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        #  Add live stream (the the actual URL, but it makes it use the standard updater).
        name = LanguageHelper.get_localized_string(LanguageHelper.LiveTv)
        item = MediaItem(
            name, "%s/programma/live/%s" % (self.baseUrl, "LI_BVN_4589107"), media_type=mediatype.VIDEO)
        item.isLive = True
        item.metaData["pow"] = "LI_BVN_4589107"
        items.append(item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_episode_item(self, result_set):
        item = chn_class.Channel.create_episode_item(self, result_set)
        if not item:
            return item

        if not item.url.endswith("/"):
            item.url = "{}/".format(item.url)

        thumb_url = result_set["thumburl"]
        if "://" not in thumb_url:
            item.thumb = "{}{}".format(self.baseUrl, thumb_url)

        item.fanart = item.thumb.replace("600/338", "1280/720")
        return item

    def create_video_item(self, result_set):
        item = chn_class.Channel.create_video_item(self, result_set)
        if not item:
            return item

        if not item.url.endswith("/"):
            item.url = "{}/".format(item.url)

        # date_value = result_set["datetime"]
        # date_time = DateHelper.get_date_from_string(date_value, "%  Y-%m-%d %H:%M:%S")
        # item.set_date(*date_time[0:6])

        thumb_url = result_set["thumburl"]
        if "://" not in thumb_url:
            item.thumb = "{}{}".format(self.baseUrl, thumb_url)

        item.metaData["pow"] = result_set["pow"]

        return item

    def update_video_item(self, item):
        pow_id = item.metaData.get("pow")
        if not pow_id:
            pow_id = item.url.rsplit("/", -1)

        from resources.lib.streams.npostream import NpoStream
        error = NpoStream.add_mpd_stream_from_npo(None, pow_id, item, live=item.isLive, use_post=True)
        if error:
            XbmcWrapper.show_dialog(LanguageHelper.ErrorId, error)
        else:
            item.complete = True
        return item


