import json
import time
from datetime import datetime
from os import path

import requests
import xbmc
import xbmcgui
from bs4 import BeautifulSoup
from resources.lib.menu import Menu

try:
    from StorageServer import StorageServer
except ImportError:
    from resources.lib.storageserverdummy import StorageServer


class NFL2018(object):
    short = str()
    hostname = str()
    parameters = dict()
    cache = StorageServer("plugin.video.nfl-teams", timeout=1)

    def __init__(self):
        if "video" in self.parameters:
            self.play_video()
        elif "category" in self.parameters:
            self.list_videos()
        else:
            self.list_categories()

    def request(self, url, params=None):
        return self.cache.cacheFunction(do_request, url, params)

    def get_thumbnail(self, video_tag):
        image_tag = video_tag.find("img")
        if image_tag:
            for i in ["src", "data-src"]:
                if image_tag.get(i):
                    return image_tag.get(i).replace("/t_lazy/", "/")

            xbmc.log("Image URL not found in tag: " + str(image_tag), xbmc.LOGWARNING)

        return path.join("resources", "images", "{0}.png".format(self.short))

    def list_categories(self):
        response = self.request("https://{}/video/".format(self.hostname))
        soup = BeautifulSoup(response, "html.parser")
        category_links = soup.find(
            "nav", attrs={"class": "d3-o-nav--secondary"}
        ).find_all("a")

        with Menu(["alpha"]) as menu:
            for category in category_links:
                if category["href"] == "/video/index":
                    # Skip the link to the video page itself
                    continue

                if not category["href"].startswith("/video/"):
                    # Skip links which aren't internal to the website
                    continue

                menu.add_item(
                    {
                        "url_params": {
                            "team": self.short,
                            "category": category["href"],
                        },
                        "name": category["title"],
                        "folder": True,
                        "thumbnail": path.join(
                            "resources", "images", "{0}.png".format(self.short)
                        ),
                    }
                )

    def list_videos(self):
        response = self.request(
            "https://{}{}".format(self.hostname, self.parameters["category"])
        )
        soup = BeautifulSoup(response, "html.parser")
        video_tags = soup.find_all("a", attrs={"class": "d3-o-media-object"})

        with Menu(["none"]) as menu:
            for video_tag in video_tags:
                if not video_tag["href"].startswith("/video/"):
                    # Skip links which aren't for videos
                    continue

                description = video_tag.find(
                    attrs={"class": "d3-o-media-object__summary"}
                )

                video = {
                    "url_params": {"team": self.short, "video": video_tag["href"]},
                    "name": video_tag["title"],
                    "folder": False,
                    "thumbnail": self.get_thumbnail(video_tag),
                    "info": {
                        "plot": description.text.strip()
                        if description
                        else "No description provided.",
                    },
                }
                date = get_date(video_tag)
                if date:
                    video["info"]["date"] = date
                menu.add_item(video)

    def play_video(self):
        response = self.request(
            "https://{}{}".format(self.hostname, self.parameters["video"])
        )
        soup = BeautifulSoup(response, "html.parser")
        video_tag = soup.find("div", attrs={"class": "nfl-o-media-player__video"})
        video_data = json.loads(video_tag["data-json"])["initialVideo"]

        summary = soup.find(
            "div", attrs={"class": "d3-o-media-object__summary"}
        ).text.strip()

        listitem = xbmcgui.ListItem(
            video_data["title"].strip(), thumbnailImage=video_data["posterImage"]
        )
        listitem.setThumbnailImage(video_data["posterImage"])
        listitem.setInfo("video", {"plot": summary})
        listitem.setProperty("PlayPath", video_data["url"])
        xbmc.Player().play(video_data["url"], listitem)


def do_request(url, params):
    if not params:
        params = {}
    return requests.get(url, params=params).content


def get_date(video_tag):
    date_tag = video_tag.find(attrs={"class": "d3-o-media-object__date"})
    if not date_tag:
        return None

    try:
        date = datetime.strptime(date_tag.text.strip(), "%b %d, %Y")
    except TypeError:
        # Workaround for bug in Kodi: https://forum.kodi.tv/showthread.php?tid=112916
        date = datetime.fromtimestamp(
            time.mktime(time.strptime(date_tag.text.strip(), "%b %d, %Y"))
        )
    return date.strftime("%d.%m.%Y")
