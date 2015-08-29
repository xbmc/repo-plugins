from HTMLParser import HTMLParser
from os import path

import requests
import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.menu import Menu


class NFLC(object):
    _short = str(None)
    _categories = dict()
    _website_url = str(None)
    _parameters = list()

    def go(self):
        if "id" in self._parameters:
            self.play_video()
        elif "category" in self._parameters:
            self.list_videos()
        else:
            self.list_categories()

    def play_video(self):
        parameters = {"id": self._parameters["id"]}
        response = requests.get("{0}/media/nflc-content.json".format(self._website_url), params=parameters)
        data = response.json()

        title = data["headline"]
        thumbnail = data["imagePaths"]["l"]
        remotehost = data["cdnData"]["streamingRemoteHost"]
        video_path = self._get_path_to_video(data["cdnData"]["bitrateInfo"])

        if not video_path.startswith("http://"):
            video_path = "{0}{1}?r=&fp=&v=&g=".format(remotehost, video_path)

        listitem = xbmcgui.ListItem(title, thumbnailImage=thumbnail)
        listitem.setProperty("PlayPath", video_path)
        xbmc.Player().play(video_path, listitem)

    @classmethod
    def _get_path_to_video(cls, videos):
        max_bitrate = int(xbmcaddon.Addon("plugin.video.nfl-teams").getSetting("max_bitrate")) * 1000000 or 5000000
        bitrate = -1
        lowest_bitrate = None

        for video in videos:
            if video["rate"] > bitrate and video["rate"] <= max_bitrate:
                best_video = video["path"]
                bitrate = video["rate"]
            if not lowest_bitrate or video["rate"] < lowest_bitrate:
                lowest_video = video["path"]
                lowest_bitrate = video["rate"]

        return best_video or lowest_video

    def list_videos(self):
        parameters = {"type": "VIDEO", "channelKey": self._parameters["category"]}

        response = requests.get("{0}/media/nflc-playlist-video.json".format(self._website_url))
        data = response.json()
        html_parser = HTMLParser()

        with Menu(["none"]) as menu:
            for video in data[str(self._parameters["category"])]["data"]:
                menu.add_item({
                    "url_params": {"team": self._short, "id": video["video_id"]},
                    "name": html_parser.unescape(video["title"]),
                    "folder": False,
                    "thumbnail": "{0}{1}".format(self._website_url, video["thumbnail"]),
                })

    def list_categories(self):
        with Menu(["none"]) as menu:
            for category_id, category_name in self._categories:
                menu.add_item({
                    "url_params": {"team": self._short, "category": category_id},
                    "name": category_name,
                    "folder": True,
                    "thumbnail": path.join("resources", "images", "{0}.png".format(self._short)),
                })
