from future import standard_library
standard_library.install_aliases()  # noqa: E402

import os
import re
import requests
import urllib.parse

from .client import VimeoClient
from .api_collection import ApiCollection
from resources.lib.models.channel import Channel
from resources.lib.models.group import Group
from resources.lib.models.user import User
from resources.lib.models.video import Video


class Api:
    """This class uses the official Vimeo API."""

    api_player = "https://player.vimeo.com"
    api_client = None
    api_access_token = "d284acb5ed7c011ec0d79f79e3479f8c"
    api_client_id = ""
    api_client_secret = ""
    api_limit = 10
    video_stream = ""
    video_hls_file_name = "hls.playlist.master.m3u8"

    def __init__(self, settings, lang, vfs):
        self.settings = settings
        self.lang = lang
        self.vfs = vfs

        self.api_limit = int(self.settings.get("search.items.size"))
        self.video_stream = self.settings.get("video.format")

        if self.settings.get("api.accesstoken"):
            self.api_access_token = self.settings.get("api.accesstoken")

        self.api_client = VimeoClient(
            token=self.api_access_token,
            key=self.api_client_id,
            secret=self.api_client_secret
        )

    def call(self, url):
        params = self._get_default_params()
        res = self._do_api_request(url, params)
        return self._map_json_to_collection(res)

    def search(self, query, kind):
        params = self._get_default_params()
        params["query"] = query
        res = self._do_api_request("/{kind}".format(kind=kind), params)
        return self._map_json_to_collection(res)

    def channel(self, channel):
        params = self._get_default_params()
        params["sort"] = "added"
        channel_id = urllib.parse.quote(channel)
        res = self._do_api_request("/channels/{id}/videos".format(id=channel_id), params)
        return self._map_json_to_collection(res)

    def resolve_media_url(self, uri):
        uri = uri.replace("/videos/", "/video/")
        res = self._do_player_request(uri)

        return self._extract_url_from_video_config(res)

    def resolve_id(self, video_id):
        params = self._get_default_params()
        res = self._do_api_request("/videos/{video_id}".format(video_id=video_id), params)
        return self._map_json_to_collection(res)

    def _do_api_request(self, path, params):
        return self.api_client.get(path, params=params).json()

    def _do_player_request(self, uri):
        headers = {"Accept-Encoding": "gzip"}
        return requests.get(self.api_player + uri + "/config", headers=headers).json()

    def _map_json_to_collection(self, json_obj):
        collection = ApiCollection()
        collection.items = []  # Reset list in order to resolve problems in unit tests.
        collection.next_href = json_obj.get("paging", {"next": None})["next"]

        if "type" in json_obj and json_obj["type"] == "video":
            # If we are dealing with a single video, pack it into a dict
            json_obj = {"data": [json_obj]}

        if "data" in json_obj:

            for item in json_obj["data"]:
                kind = item.get("type", None)
                is_channel = "/channels/" in item.get("uri", "")
                is_group = "/groups/" in item.get("uri", "")
                is_user = item.get("account", False)

                if kind == "video":
                    video = Video(id=item["resource_key"], label=item["name"])
                    # TODO Improve image extraction
                    video.thumb = item["pictures"]["sizes"][1]["link"]
                    video.uri = item["uri"]
                    video.info = {
                        "playcount": item["stats"].get("plays", 0),
                        "date": item["release_time"],
                        "duration": item["duration"],
                        "description": item["description"],
                        "user": item["user"]["name"]
                    }
                    collection.items.append(video)

                elif is_channel:
                    channel = Channel(id=item["resource_key"], label=item["name"])
                    # TODO Improve image extraction
                    channel.thumb = item["pictures"]["sizes"][3]["link"]
                    channel.uri = item["metadata"]["connections"]["videos"]["uri"]
                    channel.info = {
                        "date": item["created_time"],
                        "description": item.get("description", "")
                    }
                    collection.items.append(channel)

                elif is_group:
                    group = Group(id=item["resource_key"], label=item["name"])
                    # TODO Improve image extraction
                    group.thumb = item["pictures"]["sizes"][3]["link"]
                    group.uri = item["metadata"]["connections"]["videos"]["uri"]
                    group.info = {
                        "date": item["created_time"],
                        "description": item.get("description", "")
                    }
                    collection.items.append(group)

                elif is_user:
                    user = User(id=item["resource_key"], label=item["name"])
                    # TODO Improve image extraction
                    user.thumb = item["pictures"]["sizes"][3]["link"]
                    user.uri = item["metadata"]["connections"]["videos"]["uri"]
                    user.info = {
                        "country": item.get("location", ""),
                        "date": item["created_time"],
                        "description": item["bio"]
                    }
                    collection.items.append(user)

                else:
                    raise RuntimeError("Could not convert JSON kind to model...")

        else:
            raise RuntimeError("Api JSON seems to be invalid")

        return collection

    def _get_default_params(self):
        return {
            "per_page": self.api_limit,
            "total": self.api_limit,
            # Avoid rate limiting:
            # https://developer.vimeo.com/guidelines/rate-limiting#avoid-rate-limiting
            "fields": "uri,resource_key,name,description,type,duration,created_time,location,"
                      "bio,stats,user,account,release_time,pictures,metadata"
        }

    def _extract_url_from_video_config(self, video_config):
        video_files = video_config["request"]["files"]
        video_format = self.settings.VIDEO_FORMAT[self.video_stream]
        video_format = video_format.split(":")
        video_type = video_format[0]
        video_type_setting = video_format[1]
        video_has_av1_codec = len(video_config["request"]["file_codecs"]["av1"])

        if video_type == "hls" or video_has_av1_codec:
            hls_default_cdn = video_files["hls"]["default_cdn"]
            hls_playlist = video_files["hls"]["cdns"][hls_default_cdn]["url"]
            return self._hls_playlist_master_remove_av1_streams(hls_playlist)

        elif video_type == "progressive":
            for video_file in video_files["progressive"]:
                if video_file["quality"] == video_type_setting:
                    return video_file["url"]

            # Fallback if no matching quality was found.
            return video_files["progressive"][0]["url"]

        else:
            raise RuntimeError("Could not extract video URL")

    def _hls_playlist_master_remove_av1_streams(self, playlist):
        """
        Kodi doesn't support AV1 yet: https://forum.kodi.tv/showthread.php?tid=346272
        That's why we have to remove those streams until there is support in Kodi.
        Also the Vimeo HLS streaming servers don't seem to support the AV1 codec yet:
        > code=404, message=Could not chop_open: AV1 in MPEG-TS is unsupported.
        """
        # Download the playlist
        headers = {"Accept-Encoding": "gzip"}
        response = requests.get(playlist, headers=headers)
        response.encoding = "utf-8"
        hls_master_playlist = response.text
        hls_master_playlist_without_av1 = ""

        # Strip AV1 codec streams and create a new playlist
        remove_line = False
        for line in hls_master_playlist.splitlines():
            av1 = re.search(r"CODECS=\"av01", line)
            url = re.search(r"\.\./", line)
            if remove_line:
                remove_line = False
                continue
            elif not av1:
                if url:
                    hls_master_playlist_without_av1 += urllib.parse.urljoin(playlist, line)
                else:
                    hls_master_playlist_without_av1 += line

                hls_master_playlist_without_av1 += os.linesep
                remove_line = False
            else:
                remove_line = True

        # Write the playlist and return the path
        return self.vfs.write(self.video_hls_file_name, str(hls_master_playlist_without_av1))
