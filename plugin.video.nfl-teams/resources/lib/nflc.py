import json
from hashlib import sha1
from HTMLParser import HTMLParser
from os import path

import requests
import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.menu import Menu

try:
    from StorageServer import StorageServer
except:
    from resources.lib.storageserverdummy import StorageServer


class NFLC(object):
    _short = str(None)
    _categories = dict()
    _website_url = str(None)
    _parameters = list()
    _cache = StorageServer("plugin.video.nfl-teams", timeout=1)

    def go(self):
        if "id" in self._parameters:
            self.play_video()
        elif "category" in self._parameters:
            self.list_videos()
        else:
            self.list_categories()

    def _get_cached_response(self, url, parameters={}):
        cache_key = sha1(url + repr(parameters)).hexdigest()

        cache_response = self._cache.get(cache_key)
        if cache_response:
            return json.loads(cache_response)
        else:
            response = requests.get(url, params=parameters)
            self._cache.set(cache_key, response.text.encode("utf-8"))
            return response.json()

    def play_video(self):
        parameters = {"id": self._parameters["id"]}
        data = self._get_cached_response("{0}/media/nflc-content.json".format(self._website_url), parameters)

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
        data = self._get_cached_response("{0}/media/nflc-playlist-video.json".format(self._website_url))
        html_parser = HTMLParser()

        videos = list()
        if self._parameters["category"] == "all":
            for category in data.itervalues():
                videos.extend(category["data"])
        else:
            videos = data[str(self._parameters["category"])]["data"]

        with Menu(["none"]) as menu:
            for video in videos:
                menu.add_item({
                    "url_params": {"team": self._short, "id": video["video_id"]},
                    "name": html_parser.unescape(video["title"]),
                    "folder": False,
                    "thumbnail": "{0}{1}".format(self._website_url, video["thumbnail"]),
                    "raw_metadata": video
                })

    def list_categories(self):
        with Menu(["none"]) as menu:
            menu.add_item({
                "url_params": {"team": self._short, "category": "all"},
                "name": "[B]All Videos[/B]",
                "folder": True,
                "thumbnail": path.join("resources", "images", "{0}.png".format(self._short))
            })
            for category_id, category_name in self._categories:
                menu.add_item({
                    "url_params": {"team": self._short, "category": category_id},
                    "name": category_name,
                    "folder": True,
                    "thumbnail": path.join("resources", "images", "{0}.png".format(self._short)),
                })
