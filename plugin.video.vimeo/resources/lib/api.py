import json
import requests
import urllib.parse
import xbmc

from .api_collection import ApiCollection
from .utils import m3u8_fix_audio, m3u8_without_av1, webvtt_to_srt
from resources.lib.models.category import Category
from resources.lib.models.channel import Channel
from resources.lib.models.group import Group
from resources.lib.models.user import User
from resources.lib.models.video import Video
from resources.lib.vimeo.auth import GrantFailed
from resources.lib.vimeo.client import VimeoClient


class Api:
    """This class uses the official Vimeo API."""

    api_player = "https://player.vimeo.com"
    api_limit = 10
    api_sort = None
    api_fallback = False
    api_fallback_params = ["filter"]
    api_oauth_scope = "public,private,interact"
    api_user_cache_key = "user.json"

    # Extracted from public Vimeo Android App
    # This is a special client ID which will return playable URLs
    api_client_id = "74fa89b811a1cbb750d8528d163f48af28a2dbe1"
    api_client_secret = "VJjDTzlnL6Vm/GbUDuwCwcc1mrdFUa9XFlg4ZoMQ4xX2UWuzbBomapujUcGKLNrt" \
                        "wdtIIvy0paa7kFN0asWp2ooNSdqaEdwVkBLqau7MJFe0tSWez7HOakg/8BKtYzDe"

    # Access token of registered API app
    # Is used for specific routes and as a fallback if the client login request fails
    api_access_token_default = "d284acb5ed7c011ec0d79f79e3479f8c"
    api_access_token_cache_duration = 720  # 12 hours
    api_access_token_cache_key = "api-access-token"

    video_stream = ""
    video_hls_file_name = "hls.playlist.master.m3u8"

    def __init__(self, settings, lang, vfs, cache):
        self.settings = settings
        self.lang = lang
        self.vfs = vfs[0]
        self.vfs_cache = vfs[1]
        self.cache = cache

        self.api_limit = int(self.settings.get("search.items.size"))
        self.api_sort = self.settings.SORT.get(self.settings.get("search.sort"), {})
        self.video_stream = self.settings.get("video.format")
        self.video_av1 = True if self.settings.get("video.codec.av1") == "true" else False

    @property
    def api_client(self):
        self.api_fallback = False

        # It is possible to set a custom access token by logging in or adding it in the settings
        access_token_settings = self.settings.get("api.accesstoken")
        if access_token_settings:
            xbmc.log("plugin.video.vimeo::Api() Using custom access token", xbmc.LOGDEBUG)
            return VimeoClient(token=access_token_settings)

        # Check if there is a cached access token
        access_token_cached = self.cache.get(
            self.api_access_token_cache_key,
            self.api_access_token_cache_duration
        )
        if access_token_cached:
            xbmc.log("plugin.video.vimeo::Api() Using cached access token", xbmc.LOGDEBUG)
            return VimeoClient(token=access_token_cached)

        # Request an access token and cache it
        try:
            client = VimeoClient(
                key=self.api_client_id,
                secret=self.api_client_secret
            )
            access_token = client.load_client_credentials(["public"])
            self.cache.add(self.api_access_token_cache_key, str(access_token))
            xbmc.log("plugin.video.vimeo::Api() Using new access token", xbmc.LOGDEBUG)
            return client
        except GrantFailed:
            xbmc.log("plugin.video.vimeo::Api() Grant failed, using fallback", xbmc.LOGDEBUG)
            pass

        # Fallback
        return self.api_client_fallback

    @property
    def api_client_fallback(self):
        self.api_fallback = True
        return VimeoClient(token=self.api_access_token_default)

    @property
    def search_template(self):
        search_template = self.settings.get("search.template")

        if "{}" in search_template:
            return search_template

        return "{}"

    def oauth_device(self):
        return self.api_client.load_device_code(self.api_oauth_scope)

    def oauth_device_authorize(self, user_code, device_code):
        token, user, scope = self.api_client.device_code_authorize(user_code, device_code)
        self.settings.set("api.accesstoken", token)
        self.vfs.write(self.api_user_cache_key, json.dumps(user))

        return user["name"]

    def call(self, url):
        params = self._get_default_params()
        res = self._do_api_request(url, params)
        return self._map_json_to_collection(res)

    def search(self, query, kind):
        params = self._get_default_params()
        params.update(self.api_sort)
        params["query"] = self.search_template.format(query)
        res = self._do_api_request("/{kind}".format(kind=kind), params)
        return self._map_json_to_collection(res)

    def user(self, uri):
        params = self._get_default_params()
        return self._do_api_request(uri, params)

    def channel(self, channel):
        params = self._get_default_params()
        params["sort"] = "added"
        channel_id = urllib.parse.quote(channel)
        res = self._do_api_request("/channels/{id}/videos".format(id=channel_id), params)
        return self._map_json_to_collection(res)

    def categories(self):
        params = {"fields": "uri,resource_key,name,pictures,metadata,subcategories"}
        res = self._do_api_request("/categories", params)
        return self._map_json_to_collection(res)

    def trending(self):
        params = self._get_default_params()
        params["filter"] = "trending"
        params["direction"] = "desc"
        res = self._do_api_request("/videos", params)
        return self._map_json_to_collection(res)

    def resolve_texttracks(self, uri):
        res = self._do_api_request(uri, {})
        subtitles = res.get("data")
        for subtitle in subtitles:
            subtitle["srt"] = webvtt_to_srt(self._do_request(subtitle["link"]))
        return subtitles

    def resolve_media_url(self, uri, password=None):
        # If we have a on-demand URL, we need to fetch the trailer and return the uri
        if uri.startswith("/ondemand/"):
            xbmc.log("plugin.video.vimeo::Api() Resolving on-demand", xbmc.LOGDEBUG)
            media_url = self._get_on_demand_trailer(uri)

        # Fallback (if official API client ID doesn't work)
        elif self.api_fallback:
            xbmc.log("plugin.video.vimeo::Api() Resolving fallback", xbmc.LOGDEBUG)
            uri = uri.replace("/videos/", "/video/")
            res = self._do_player_request(uri)
            media_url = self._extract_url_from_video_config(res)

        # Fetch media URL
        else:
            xbmc.log("plugin.video.vimeo::Api() Resolving video uri", xbmc.LOGDEBUG)
            params = self._get_default_params()
            params["password"] = password
            res = self._do_api_request(uri, params)
            media_url = self._extract_url_from_search_response(res["play"])

        xbmc.log("plugin.video.vimeo::Api() Resolved video uri to " + media_url, xbmc.LOGDEBUG)

        return self._append_user_agent(media_url)

    def resolve_id(self, video_id, password=None):
        params = self._get_default_params()
        params["password"] = password
        res = self._do_api_request("/videos/{video_id}".format(video_id=video_id), params)
        return self._map_json_to_collection(res)

    def _do_api_request(self, path, params):
        xbmc.log("plugin.video.vimeo::Api() Requesting '{}'".format(path), xbmc.LOGDEBUG)

        if self._request_requires_fallback(path, params):
            return self.api_client_fallback.get(path, params=params).json()

        return self.api_client.get(path, params=params).json()

    def _do_player_request(self, uri):
        headers = {"Accept-Encoding": "gzip"}
        return requests.get(self.api_player + uri + "/config", headers=headers).json()

    def _do_request(self, uri):
        return requests.get(uri).text

    def _map_json_to_collection(self, json_obj):
        collection = ApiCollection()
        collection.items = []  # Reset list in order to resolve problems in unit tests
        collection.next_href = json_obj.get("paging", {"next": None})["next"]

        if self._request_was_bad(json_obj) == 2223:
            raise PasswordRequiredException()

        if self._request_was_bad(json_obj) == 2222:
            raise WrongPasswordException()

        if "type" in json_obj and json_obj["type"] in ("video", "live"):
            # If we are dealing with a single video, pack it into a dict
            json_obj = {"data": [json_obj]}

        if "data" in json_obj:

            for item in json_obj["data"]:
                if "play" in item and item.get("play").get("status", "") == "unavailable":
                    # Don't show unavailable items (like scheduled live streams)
                    continue

                kind = item.get("type", None)
                is_video = kind == "video"
                is_live = kind == "live"
                is_category = "/categories/" in item.get("uri", "")
                is_channel = "/channels/" in item.get("uri", "")
                is_group = "/groups/" in item.get("uri", "")
                is_user = item.get("account", False)

                # On-demand videos don't contain playable video links:
                purchase_required = item.get("play", {}).get("status", "") == "purchase_required"

                if is_video or is_live:
                    if purchase_required:
                        video_url = item["metadata"]["connections"]["trailer"]["uri"]
                    else:
                        video_url = item["uri"]

                    video = Video(id=item["resource_key"], label=item["name"])
                    video.thumb = self._get_picture(item["pictures"])
                    video.uri = video_url
                    video.hasSubtitles = item["metadata"]["connections"]["texttracks"]["total"] > 0
                    video.info = {
                        "date": item["release_time"],
                        "description": item["description"],
                        "duration": item["duration"],
                        "picture": self._get_picture(item["pictures"], 4),
                        "user": item["user"]["name"],
                        "userThumb": self._get_picture(item["user"]["pictures"], 3),
                        "onDemand": purchase_required,
                        "live": is_live,
                    }
                    collection.items.append(video)

                elif is_category:
                    category = Category(id=item["resource_key"], label=item["name"])
                    category.thumb = self._get_picture(item["pictures"], 3)
                    category.uri = item["metadata"]["connections"]["videos"]["uri"]
                    collection.items.append(category)

                elif is_channel:
                    channel = Channel(id=item["resource_key"], label=item["name"])
                    channel.thumb = self._get_picture(item["pictures"], 3)
                    channel.uri = item["metadata"]["connections"]["videos"]["uri"]
                    channel.info = {
                        "date": item["created_time"],
                        "description": item.get("description", ""),
                    }
                    collection.items.append(channel)

                elif is_group:
                    group = Group(id=item["resource_key"], label=item["name"])
                    group.thumb = self._get_picture(item["pictures"], 3)
                    group.uri = item["metadata"]["connections"]["videos"]["uri"]
                    group.info = {
                        "date": item["created_time"],
                        "description": item.get("description", ""),
                    }
                    collection.items.append(group)

                elif is_user:
                    user = User(id=item["resource_key"], label=item["name"])
                    user.data = item
                    collection.items.append(user)

                else:
                    raise RuntimeError("Could not convert JSON kind to model...")

        else:
            raise RuntimeError("Api JSON seems to be invalid")

        return collection

    def _get_on_demand_trailer(self, uri):
        res = self._do_api_request(uri, {"fields": "uri,type,play"})
        return self._extract_url_from_search_response(res["play"])

    def _video_matches(self, video, video_format):
        video_height = video_format[1].replace("p", "")
        return str(video["height"]) == video_height and video["codec"] == self._get_video_codec()

    def _extract_url_from_search_response(self, video_files):
        video_format = self.settings.VIDEO_FORMAT[self.video_stream]
        video_format = video_format.split(":")
        video_type = video_format[0]

        if video_type == "hls" and video_files.get("hls") is not None:
            return self._hls_playlist_without_av1_streams(video_files["hls"]["link"])

        elif video_files.get("progressive") is None:
            # We are probably dealing with a live stream, so we can't use the progressive format
            return self._hls_playlist_without_av1_streams(video_files["hls"]["link"])

        elif video_type == "progressive" or video_files.get("hls") is None:
            for video_file in video_files["progressive"]:
                if self._video_matches(video_file, video_format):
                    return video_file["link"]

            # Fallback if no matching quality was found
            for video_file in video_files["progressive"]:
                if video_file["codec"] == self._get_video_codec():
                    return video_file["link"]

            # Fallback if fallback failed
            return video_files["progressive"][0]["link"]

        else:
            raise RuntimeError("Could not extract video URL")

    def _extract_url_from_video_config(self, video_config):
        video_files = video_config["request"]["files"]
        video_format = self.settings.VIDEO_FORMAT[self.video_stream]
        video_format = video_format.split(":")
        video_type = video_format[0]
        video_type_setting = video_format[1]
        video_has_av1_codec = len(video_config["request"]["file_codecs"]["av1"]) > 0

        if video_type == "hls" or (video_has_av1_codec and not self.video_av1):
            hls_default_cdn = video_files["hls"]["default_cdn"]
            if self.video_av1:
                return video_files["hls"]["cdns"][hls_default_cdn]["av1_url"]
            else:
                return video_files["hls"]["cdns"][hls_default_cdn]["avc_url"]

        elif video_type == "progressive":
            for video_file in video_files["progressive"]:
                if video_file["quality"] == video_type_setting:
                    return video_file["url"]

            # Fallback if no matching quality was found
            return video_files["progressive"][0]["url"]

        else:
            raise RuntimeError("Could not extract video URL")

    def _get_video_codec(self):
        return self.settings.VIDEO_CODEC["AV1"] if self.video_av1 else \
            self.settings.VIDEO_CODEC["H.264"]

    def _get_default_params(self):
        return {
            "per_page": self.api_limit,
            "total": self.api_limit,
            # Avoid rate limiting:
            # https://developer.vimeo.com/guidelines/rate-limiting#avoid-rate-limiting
            "fields": "uri,resource_key,name,description,type,duration,created_time,location,"
                      "bio,short_bio,stats,user,account,release_time,pictures,metadata,play,"
                      "live.status,websites"
        }

    def _request_requires_fallback(self, path, params):
        url = urllib.parse.urlparse(path)
        for param in self.api_fallback_params:
            if param in params or param in urllib.parse.parse_qs(url.query):
                return True

        return False

    def _hls_playlist_without_av1_streams(self, playlist):
        """
        Kodi <= 18 doesn't support AV1 yet: https://forum.kodi.tv/showthread.php?tid=346272
        That's why we have to remove those streams for older Kodi versions.
        Also the Vimeo HLS streaming servers don't seem to support the AV1 codec yet:
        > code=404, message=Could not chop_open: AV1 in MPEG-TS is unsupported.
        """
        # Don't remove AV1 streams if AV1 is enabled
        if self.video_av1:
            return playlist

        # Download the playlist and strip AV1 streams
        headers = {"Accept-Encoding": "gzip"}
        response = requests.get(playlist, headers=headers)
        response.encoding = "utf-8"
        hls_master_playlist = response.text
        hls_master_playlist_without_av1 = m3u8_without_av1(hls_master_playlist, response.url)
        hls_master_playlist_without_av1 = m3u8_fix_audio(hls_master_playlist_without_av1)

        # Return original playlist if playlist hasn't changed
        if hls_master_playlist.count("\n") == hls_master_playlist_without_av1.count("\n"):
            return playlist

        xbmc.log("plugin.video.vimeo::Api() Stripped AV1 streams from HLS playlist", xbmc.LOGDEBUG)

        # Write the playlist and return the path
        return self.vfs_cache.write(self.video_hls_file_name, hls_master_playlist_without_av1)

    @staticmethod
    def _request_was_bad(json_obj):
        if "invalid_parameters" in json_obj and isinstance(json_obj["invalid_parameters"], list):
            invalid_params = json_obj["invalid_parameters"]
            if len(invalid_params) > 0 and "error_code" in invalid_params[0]:
                return invalid_params[0]["error_code"]

        return False

    @staticmethod
    def _append_user_agent(url):
        """
        Kodi automatically uses a operating system based User-Agent for HTTP requests.
        This causes an issue with the Vimeo API endpoint when a request is made from macOS,
        because the Vimeo endpoint then thinks it can deliver the DASH format to an iOS device.
        By appending a custom User-Agent at the end of the URL, the User-Agent can be overwritten.
        """
        if "Mac OS X" in xbmc.getUserAgent():
            return "{}|User-Agent={}".format(url, urllib.parse.quote(VimeoClient.USER_AGENT))

        return url

    @staticmethod
    def _get_picture(data, size=1):
        try:
            return data["sizes"][size]["link"]
        except IndexError:
            return data["sizes"][0]["link"]


class PasswordRequiredException(Exception):
    pass


class WrongPasswordException(Exception):
    pass
