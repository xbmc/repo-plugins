from os import path

import requests
import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.menu import Menu


class NFLCS(object):
    _short = str(None)
    _cdaweb_url = str(None)
    _categories = list()
    _categories_strip_left = [
        "Ravens Productions - ",
        "Video - ",
        "Videos - ",
    ]
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
        response = requests.get("{0}audio-video-content.htm".format(self._cdaweb_url), params=parameters)
        data = response.json()

        title = data["headline"]
        thumbnail = data["imagePaths"]["xl"]
        remotehost = data["cdnData"]["streamingRemoteHost"].replace("a.video.nfl.com", "vod.hstream.video.nfl.com")
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
        if self._parameters["category"] == "all":
            parameters = {"type": "VIDEO", "channelKey": ""}
        else:
            parameters = {"type": "VIDEO", "channelKey": self._parameters["category"]}

        response = requests.get("{0}audio-video-channel.htm".format(self._cdaweb_url), params=parameters)
        data = response.json()

        with Menu(["date", "alpha"]) as menu:
            for video in data["gallery"]["clips"]:
                menu.add_item({
                    "url_params": {"team": self._short, "id": video["id"]},
                    "name": video["title"],
                    "folder": False,
                    "thumbnail": video["thumb"],
                    "raw_metadata": video
                })

    def list_categories(self):
        with Menu(["none"]) as menu:
            menu.add_item({
                "url_params": {"team": self._short, "category": "all"},
                "name": "All Videos",
                "folder": True,
                "thumbnail": path.join("resources", "images", "{0}.png".format(self._short))
            })
            for category in self._categories:
                raw_category = category

                for strip_left in self._categories_strip_left:
                    if category.startswith(strip_left):
                        category = category[(len(strip_left)):]

                menu.add_item({
                    "url_params": {"team": self._short, "category": raw_category},
                    "name": category,
                    "folder": True,
                    "thumbnail": path.join("resources", "images", "{0}.png".format(self._short))
                })
