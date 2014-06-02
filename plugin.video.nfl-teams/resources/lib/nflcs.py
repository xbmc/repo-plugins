import urllib
import urllib2
import resources.lib.menu
from json import load
import xbmc
import xbmcaddon
import xbmcgui

class NFLCS(object):
    _short = str(None)
    _fanart = str(None)
    _cdaweb_url = str(None)
    _categories = list()
    _categories_strip_left = [
        "Pandora ",
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
        get_parameters = {"id": self._parameters["id"][0]}
        data = urllib.urlencode(get_parameters)
        request = urllib2.Request(self._cdaweb_url + "audio-video-content.htm", data)
        response = urllib2.urlopen(request)
        json = load(response, "iso-8859-1")
        title = json["headline"]
        thumbnail = json["imagePaths"]["xl"]

        remotehost = json["cdnData"]["streamingRemoteHost"]
        if "a.video.nfl.com" in remotehost:
            remotehost = remotehost.replace("a.video.nfl.com", "vod.hstream.video.nfl.com")

        max_bitrate = int(xbmcaddon.Addon(id="plugin.video.nfl-teams").getSetting("max_bitrate")) * 1000000 or 5000000
        bitrate = -1
        lowest_bitrate = None
        for path_entry in json["cdnData"]["bitrateInfo"]:
            if path_entry["rate"] > bitrate and path_entry["rate"] <= max_bitrate:
                path = path_entry["path"]
                bitrate = path_entry["rate"]
            if not lowest_bitrate or path_entry["rate"] < lowest_bitrate:
                lowest_path = path_entry["path"]
                lowest_bitrate = path_entry["rate"]

        if not path:
            path = lowest_path

        if not path.startswith("http://"):
            path = remotehost + path + "?r=&fp=&v=&g="

        listitem = xbmcgui.ListItem(title, thumbnailImage=thumbnail)
        listitem.setProperty("PlayPath", path)
        xbmc.Player().play(path, listitem)

    def list_videos(self):
        if self._parameters["category"][0] == "all":
            parameters = {"type": "VIDEO", "channelKey": ""}
        else:
            parameters = {"type": "VIDEO", "channelKey": self._parameters["category"][0]}

        data = urllib.urlencode(parameters)
        request = urllib2.Request(self._cdaweb_url + "audio-video-channel.htm", data)
        response = urllib2.urlopen(request)
        json = load(response, "iso-8859-1")

        menu = resources.lib.menu.Menu()
        menu.add_sort_method("date")
        menu.add_sort_method("alpha")
        for video in json["gallery"]["clips"]:
            menu.add_item(
                url_params={"team": self._short, "id": video["id"]},
                name=video["title"],
                folder=False,
                thumbnail=video["thumb"],
                raw_metadata=video
            )
        menu.end_directory()

    def list_categories(self):
        menu = resources.lib.menu.Menu()
        menu.add_sort_method("none")
        menu.add_item(
            url_params={"team": self._short, "category": "all"},
            name="All Videos",
            folder=True,
            thumbnail="resources/images/%s.png" % self._short
        )
        for category in self._categories:
            raw_category = category

            for strip_left in self._categories_strip_left:
                if category.startswith(strip_left):
                    category = category[(len(strip_left)):]

            menu.add_item(
                url_params={"team": self._short, "category": raw_category},
                name=category,
                folder=True,
                thumbnail="resources/images/%s.png" % self._short
            )
        menu.end_directory()
