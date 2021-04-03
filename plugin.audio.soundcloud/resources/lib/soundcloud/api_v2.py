import hashlib
import json
import re
import requests
import urllib.parse
import xbmc

from resources.lib.models.playlist import Playlist
from resources.lib.models.track import Track
from resources.lib.models.selection import Selection
from resources.lib.models.user import User
from resources.lib.soundcloud.api_collection import ApiCollection
from resources.lib.soundcloud.api_interface import ApiInterface


class ApiV2(ApiInterface):
    """This class uses the unofficial API used by the SoundCloud website."""

    api_host = "https://api-v2.soundcloud.com"
    api_client_id_cache_duration = 1440  # 24 hours
    api_client_id_cache_key = "api-client-id"
    api_limit = 20
    api_limit_tracks = 50
    api_lang = "en"
    api_cache = {
        "discover": 120  # 2 hours
    }
    thumbnail_size = 500

    def __init__(self, settings, lang, cache):
        self.cache = cache
        self.settings = settings
        self.api_limit = int(self.settings.get("search.items.size"))

        if self.settings.get("apiv2.locale") == self.settings.APIV2_LOCALE["auto"]:
            self.api_lang = lang

    @property
    def api_client_id(self):
        # It is possible to set a custom client ID in the settings
        client_id_settings = self.settings.get("apiv2.client_id")
        if client_id_settings:
            xbmc.log("plugin.audio.soundcloud::ApiV2() Using custom client ID", xbmc.LOGDEBUG)
            return client_id_settings

        # Check if there is a cached client ID
        client_id_cached = self.cache.get(
            self.api_client_id_cache_key,
            self.api_client_id_cache_duration
        )
        if client_id_cached:
            xbmc.log("plugin.audio.soundcloud::ApiV2() Using cached client ID", xbmc.LOGDEBUG)
            return client_id_cached

        # Extract client ID from website and cache it
        client_id = self.fetch_client_id()
        self.cache.add(self.api_client_id_cache_key, str(client_id))
        xbmc.log("plugin.audio.soundcloud::ApiV2() Using new client ID", xbmc.LOGDEBUG)

        return client_id

    def search(self, query, kind="tracks"):
        res = self._do_request("/search/" + kind, {"q": query, "limit": self.api_limit})
        return self._map_json_to_collection(res)

    def discover(self, selection_id=None):
        res = self._do_request("/mixed-selections", {}, self.api_cache["discover"])

        if selection_id and "collection" in res:
            res = self._find_id_in_selection(res["collection"], selection_id)

        return self._map_json_to_collection(res)

    def charts(self, filters):
        res = self._do_request("/charts", filters)
        res = {"collection": [item["track"] for item in res["collection"]]}
        return self._map_json_to_collection(res)

    def call(self, url):
        url = urllib.parse.urlparse(url)
        res = self._do_request(url.path, urllib.parse.parse_qs(url.query))
        return self._map_json_to_collection(res)

    def resolve_id(self, id):
        res = self._do_request("/tracks", {"ids": id})
        return self._map_json_to_collection({"collection": res})

    def resolve_url(self, url):
        url = self._sanitize_url(url)
        res = self._do_request("/resolve", {"url": url})
        return self._map_json_to_collection(res)

    def resolve_media_url(self, url):
        url = urllib.parse.urlparse(url)
        res = self._do_request(url.path, urllib.parse.parse_qs(url.query))
        return res.get("url")

    def _do_request(self, path, payload, cache=0):
        payload["client_id"] = self.api_client_id
        payload["app_locale"] = self.api_lang
        headers = {"Accept-Encoding": "gzip"}
        path = self.api_host + path
        cache_key = hashlib.sha1((path + str(payload)).encode()).hexdigest()

        xbmc.log(
            "plugin.audio.soundcloud::ApiV2() Calling %s with header %s and payload %s" %
            (path, str(headers), str(payload)),
            xbmc.LOGDEBUG
        )

        # If caching is active, check for an existing cached file.
        if cache:
            cached_response = self.cache.get(cache_key, cache)
            if cached_response:
                return json.loads(cached_response)

        # Send the request.
        response = requests.get(path, headers=headers, params=payload).json()

        # If caching is active, cache the response.
        if cache:
            self.cache.add(cache_key, json.dumps(response))

        return response

    def _extract_media_url(self, transcodings):
        setting = self.settings.get("audio.format")
        for codec in transcodings:
            if self._is_preferred_codec(codec["format"], self.settings.AUDIO_FORMATS[setting]):
                return codec["url"]

        # Fallback
        return transcodings[0]["url"] if len(transcodings) else None

    def _find_id_in_selection(self, selection, selection_id):
        for category in selection:
            if category["id"] == selection_id:
                if "items" in category:
                    return category["items"]
                elif "tracks" in category:
                    return {"collection": category["tracks"]}
            elif "items" in category:
                res = self._find_id_in_selection(category["items"]["collection"], selection_id)
                if res:
                    return res

    def _map_json_to_collection(self, json_obj):
        collection = ApiCollection()
        collection.items = []  # Reset list in order to resolve problems in unit tests.
        collection.load = []
        collection.next_href = json_obj.get("next_href", None)

        if "kind" in json_obj and json_obj["kind"] == "track":
            # If we are dealing with a single track, pack it into a dict
            json_obj = {"collection": [json_obj]}

        if "collection" in json_obj:

            for item in json_obj["collection"]:
                kind = item.get("kind", None)

                if kind == "track":
                    if "title" not in item:
                        # Track not fully returned by API
                        collection.load.append(item["id"])
                        continue

                    track = self._build_track(item)
                    collection.items.append(track)

                elif kind == "user":
                    user = User(id=item["id"], label=item["username"])
                    user.label2 = item.get("full_name", "")
                    user.thumb = self._get_thumbnail(item, self.thumbnail_size)
                    user.info = {
                        "artist": item.get("description", None)
                    }
                    collection.items.append(user)

                elif kind == "playlist":
                    playlist = Playlist(id=item["id"], label=item.get("title"))
                    playlist.is_album = item.get("is_album", False)
                    playlist.label2 = item.get("label_name", "")
                    playlist.thumb = self._get_thumbnail(item, self.thumbnail_size)
                    playlist.info = {
                        "artist": item["user"]["username"]
                    }
                    collection.items.append(playlist)

                elif kind == "system-playlist":
                    # System playlists only appear inside selections
                    playlist = Selection(id=item["id"], label=item.get("title"))
                    playlist.thumb = self._get_thumbnail(item, self.thumbnail_size)
                    collection.items.append(playlist)

                elif kind == "selection":
                    selection = Selection(id=item["id"], label=item.get("title"))
                    selection.label2 = item.get("description", "")
                    collection.items.append(selection)

                else:
                    xbmc.log("plugin.audio.soundcloud::ApiV2() "
                             "Could not convert JSON kind to model...",
                             xbmc.LOGWARNING)

        elif "tracks" in json_obj:

            for item in json_obj["tracks"]:
                if "title" not in item:
                    # Track not fully returned by API
                    collection.load.append(item["id"])
                    continue

                track = self._build_track(item)
                track.label2 = json_obj["title"]
                collection.items.append(track)

        else:
            raise RuntimeError("ApiV2 JSON seems to be invalid")

        # Load unresolved tracks
        if collection.load:
            # The API only supports a max of 50 track IDs per request:
            for chunk in self._chunks(collection.load, self.api_limit_tracks):
                track_ids = ",".join(str(x) for x in chunk)
                loaded_tracks = self._do_request("/tracks", {"ids": track_ids})
                # Because returned tracks are not sorted, we have to manually match them
                for track_id in chunk:
                    loaded_track = [lt for lt in loaded_tracks if lt["id"] == track_id]
                    if len(loaded_track):  # Sometimes a track cannot be resolved
                        track = self._build_track(loaded_track[0])
                        collection.items.append(track)

        return collection

    def _build_track(self, item):
        if type(item.get("publisher_metadata")) is dict:
            artist = item["publisher_metadata"].get("artist", item["user"]["username"])
        else:
            artist = item["user"]["username"]

        track = Track(id=item["id"], label=item["title"])
        track.blocked = True if item.get("policy") == "BLOCK" else False
        track.preview = True if item.get("policy") == "SNIP" else False
        track.thumb = self._get_thumbnail(item, self.thumbnail_size)
        track.media = self._extract_media_url(item["media"]["transcodings"])
        track.info = {
            "artist": artist,
            "genre": item.get("genre", None),
            "date": item.get("display_date", None),
            "description": item.get("description", None),
            "duration": int(item["duration"]) / 1000
        }

        return track

    @staticmethod
    def fetch_client_id():
        headers = {"Accept-Encoding": "gzip"}

        # Get the HTML (includes a reference to the JS file we need)
        html = requests.get("https://soundcloud.com/", headers=headers).text

        # Extract the HREF to the JS file (which contains the API key)
        matches = re.findall(r"=\"(https://a-v2\.sndcdn\.com/assets/.*.js)\"", html)

        if matches:
            for match in matches:
                # Get the JS
                response = requests.get(match, headers=headers)
                response.encoding = "utf-8"  # This speeds up `response.text` by 3 seconds

                # Extract the API key
                key = re.search(r"exports={\"api-v2\".*client_id:\"(\w*)\"", response.text)

                if key:
                    return key.group(1)

            raise Exception("Failed to extract client key from js")
        else:
            raise Exception("Failed to extract js href from html")

    @staticmethod
    def _is_preferred_codec(codec, setting):
        return codec["mime_type"] == setting["mime_type"] and \
               codec["protocol"] == setting["protocol"]

    @staticmethod
    def _sanitize_url(url):
        return url.replace("m.soundcloud.com/", "soundcloud.com/")

    @staticmethod
    def _get_thumbnail(item, size):
        """
        availableSizes: [
          [ 20, 't20x20'],
          [ 50, 't50x50'],
          [120, 't120x120'],
          [200, 't200x200'],
          [500, 't500x500']
        ]
        """
        url = item.get(
            "artwork_url", item.get("avatar_url", item.get("calculated_artwork_url", False))
        )

        return re.sub(
            r"^(.*/)(\w+)-([-a-zA-Z0-9]+)-([a-z0-9]+)\.(jpg|png|gif).*$",
            r"\1\2-\3-t{x}x{y}.\5".format(x=size, y=size),
            url
        ) if url else None

    @staticmethod
    def _chunks(lst, size):
        for i in range(0, len(lst), size):
            yield lst[i:i + size]
