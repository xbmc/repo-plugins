import time
from collections import namedtuple

import requests
import xbmc
import xbmcaddon
import xbmcgui

VideoListItem = namedtuple("VideoSearchResult",
    [
        "type",
        "id",
        "thumbnail_url",
        "heading",
        "author",
        "description",
        "view_count",
        "published",
        "duration",
    ]
)

ChannelListItem = namedtuple("ChannelSearchResult",
    [
        "type",
        "id",
        "thumbnail_url",
        "heading",
        "description",
        "verified",
        "sub_count",
     ]
)

PlaylistListItem = namedtuple("PlaylistSearchResult",
    [
        "type",
        "id",
        "thumbnail_url",
        "heading",
        "channel",
        "channel_id",
        "verified",
        "video_count",
    ]
)


class InvidiousAPIClient:
    def __init__(self, instance_url):
        self.instance_url = instance_url.rstrip("/")
        self.addon = xbmcaddon.Addon()

    def make_get_request(self, *path, **params):
        base_url = self.instance_url + "/api/v1/"

        url_path = "/".join(path)

        while "//" in url_path:
            url_path = url_path.replace("//", "/")

        assembled_url = base_url + url_path

        xbmc.log(f"invidious ========== request {assembled_url} with {params} started ==========", xbmc.LOGDEBUG)
        start = time.time()
        response = requests.get(assembled_url, params=params, timeout=5)
        end = time.time()
        xbmc.log(f"invidious ========== request finished in {end - start}s ==========", xbmc.LOGDEBUG)

        if response.status_code > 300:
            xbmc.log(f'invidious API request {assembled_url} with {params} failed with HTTP status {response.status_code}: {response.reason}.', xbmc.LOGWARNING)
            return None

        return response

    def parse_response(self, response):
        if not response:
            return None
        data = response.json()

        # If a channel or playlist is opened, the videos are packaged
        # in a dict entry "videos".
        if "videos" in data:
            data = data["videos"]

        for item in data:
            # Playlist videos do not have the 'type' attribute
            if not "type" in item or item["type"] in ["video", "shortVideo"]:
                # Skip videos with no or negative duration.
                if not item["lengthSeconds"] > 0:
                    continue
                for thumb in item["videoThumbnails"]:

                    # high appears to be ~480x360, which is a
                    # reasonable trade-off works well on 1080p.
                    if thumb["quality"] == "high":
                        thumbnail_url = thumb["url"]
                        break

                # as a fallback, we just use the last one in the list
                # (which is usually the lowest quality).
                else:
                    thumbnail_url = item["videoThumbnails"][-1]["url"]

                yield VideoListItem(
                    "video",
                    item["videoId"],
                    thumbnail_url,
                    item["title"],
                    item["author"],
                    item.get("description", self.addon.getLocalizedString(30000)),
                    item.get("viewCount", -1), # Missing for playlists.
                    item.get("published", 0), # Missing for playlists.
                    item["lengthSeconds"],
                )
            elif item["type"] == "channel":
                # Grab the highest resolution avatar image
                # Usually isn't more than 512x512
                thumbnail = sorted(item["authorThumbnails"], key=lambda thumb: thumb["height"], reverse=True)[0]

                yield ChannelListItem(
                    "channel",
                    item["authorId"],
                    "https:" + thumbnail["url"],
                    item["author"],
                    item["description"],
                    item["authorVerified"],
                    item["subCount"],
                )
            elif item["type"] == 'playlist':
                yield PlaylistListItem(
                    "playlist",
                    item["playlistId"],
                    item["playlistThumbnail"],
                    item["title"],
                    item["author"],
                    item["authorId"],
                    item["authorVerified"],
                    item["videoCount"],
                )
            else:
                xbmc.log(f'invidious received search result item with unknown response type {item["type"]}.', xbmc.LOGWARNING)

    def search(self, *terms):
        params = {
            "q": " ".join(terms),
            "sort_by": "upload_date",
        }

        response = self.make_get_request("search", **params)

        return self.parse_response(response)

    def fetch_video_information(self, video_id):
        response = self.make_get_request("videos/", video_id)
        if not response:
            return None
        return response.json()

    def fetch_channel_list(self, channel_id):
        response = self.make_get_request(f"channels/videos/{channel_id}")

        return self.parse_response(response)

    def fetch_playlist_list(self, playlist_id):
        response = self.make_get_request(f"playlists/{playlist_id}")

        return self.parse_response(response)

    def fetch_special_list(self, special_list_name):
        response = self.make_get_request(special_list_name)

        return self.parse_response(response)
