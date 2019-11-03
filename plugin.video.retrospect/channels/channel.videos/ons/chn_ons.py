# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import chn_class
from resources.lib.regexer import Regexer
from resources.lib.mediaitem import MediaItem


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
        self.baseUrl = "https://www.kijkbijons.nl"
        self.mainListUri = "https://www.kijkbijons.nl/programmas"

        # Setup textures
        self.noImage = "onsimage.png"

        # Define parsers
        episode_regex = r'<a class="clipItem"[^>]*href="(?<url>[^"]+)[^>]*>\s*<span class="clipItemImage">\s*<img[^>]*src="(?<thumburl>[^"]+)"[^>]+alt="(?<title>[^"]+)"[^>]*>'
        self._add_data_parser(self.mainListUri, name="Main Programlist", 
                              parser=Regexer.from_expresso(episode_regex),
                              creator=self.create_episode_item)

        video_regex = r'<a class="clipItem"\s+href="(?<url>[^"]+item\?(?<id>[^"]+))"[^>]+>\s+<[^>]+>\s*<img src="(?<thumb>[^"]+)[^>]*>\s*(?:[^>]+>\s*){4}(?<title>[^\n\r<]+)'
        self._add_data_parser("*", name="Main Video parsers",
                              parser=Regexer.from_expresso(video_regex),
                              creator=self.create_video_item,
                              updater=self.update_video_item)

        #===============================================================================================================
        # non standard items

        return

    def create_video_item(self, result_set):
        item = chn_class.Channel.create_video_item(self, result_set)
        if item is None:
            return None

        item.url = "https://api.ibbroadcast.nl/clips.ashx?" \
                   "key=hU6YJdwThYkjsb1Z4qRDQ795UduP2CYRYm1An2amlxk=&" \
                   "mode=getclip&" \
                   "output=jsonp&" \
                   "id={}".format(result_set["id"])
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

        from resources.lib.helpers.jsonhelper import JsonHelper
        from resources.lib.urihandler import UriHandler

        data = UriHandler.open(item.url, proxy=self.proxy)
        json_data = JsonHelper(data)
        streams = json_data.get_value("clip", "previews")
        part = item.create_new_empty_media_part()
        for stream_info in streams:
            name = stream_info["name"]
            # for now we only take the numbers as bitrate:
            bitrate = int(''.join([x for x in name if x.isdigit()]))
            url = stream_info["source"]
            part.append_media_stream(url, bitrate)
            item.complete = True

        return item
