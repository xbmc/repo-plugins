# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Union, List

from resources.lib import chn_class, contenttype, mediatype
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, FolderItem


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

        # https://api.ibbroadcast.nl/IB_API.pdf
        self.baseUrl = "https://www.kijkbijons.nl"
        self.api_key = "hU6YJdwThYkjsb1Z4qRDQ795UduP2CYRYm1An2amlxk="
        self.mainListUri = f"https://api.ibbroadcast.nl/clips.ashx?key={self.api_key}" \
                           "&output=json&mode=searchClips&sort=lasttransmissiontime" \
                           "&cliptype=1&sortdirection=DESC&amount=200&page=1"

        # Setup textures
        self.noImage = "onsimage.jpg"

        # Define parsers
        self._add_data_parser("https://api.ibbroadcast.nl/clips.ashx", json=True,
                              name="Main Programlist",
                              parser=[],
                              creator=self.create_episode_item)

        self._add_data_parser("https://api.ibbroadcast.nl/clips.ashx", json=True,
                              name="Parser that filters the folders", label="folder",
                              parser=[],
                              creator=self.create_video_item)

        self._add_data_parser("*", updater=self.update_video_item)

        #===============================================================================================================
        # non standard items

        return

    def create_episode_item(self, result_set: dict) -> Union[MediaItem, List[MediaItem], None]:
        folder_id = result_set["folder"]["id"]
        folder_name = result_set["folder"]["name"]
        url = self.mainListUri
        item = FolderItem(folder_name, url, content_type=contenttype.EPISODES)
        item.metaData["folder_id"] = folder_id
        item.metaData["retrospect:parser"] = "folder"
        return item

    def create_video_item(self, result_set: dict):
        folder_id = result_set["folder"]["id"]
        if folder_id != self.parentItem.metaData["folder_id"]:
            return None

        clip_id = result_set["id"]
        name = result_set["name"]
        url = f"http://api.ibbroadcast.nl/clips.ashx?key={self.api_key}&mode=getclip&id={clip_id}&output=json"
        item = MediaItem(name, url, media_type=mediatype.EPISODE)
        item.description = result_set["description"]
        item.set_artwork(thumb=result_set["screenshot"])

        # date: '01-02-2024 11:15:09'
        changed = result_set.get("changedate")
        if changed:
            time_stamp = DateHelper.get_date_from_string(changed, "%d-%m-%Y %H:%M:%S")
            item.set_date(*time_stamp[0:6])

        # duration=00:25:16.4800000
        durations = result_set.get("duration", "0:0:0")
        Logger.debug(durations)
        duration_parts = durations.split(":")
        duration = 60 * 60 * int(duration_parts[0]) + 60 * int(duration_parts[1]) + int(duration_parts[2][0:2])
        Logger.trace(f"Duration: {durations} -> {duration}")
        item.set_info_label(MediaItem.LabelDuration, duration)

        params = result_set.get("parameters") or []
        episode = 0
        season = 0
        for param in params:
            if not param["name"]:
                continue
            if param["name"].lower() == "episode":
                episode = param["values"][0]["name"]
            elif param["name"].lower() == "season":
                season = param["values"][0]["name"]

        if episode and season:
            item.set_season_info(season, episode)

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

        from resources.lib.helpers.jsonhelper import JsonHelper
        from resources.lib.urihandler import UriHandler

        data = UriHandler.open(item.url)
        json_data = JsonHelper(data)
        streams = json_data.get_value("previews")
        for stream_info in streams:
            name = stream_info["name"]
            # for now we only take the numbers as bitrate:
            bitrate = int(''.join([x for x in name if x.isdigit()]))
            url = stream_info["source"]
            item.add_stream(url, bitrate)
            item.complete = True

        return item
