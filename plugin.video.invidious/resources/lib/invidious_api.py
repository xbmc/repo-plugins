import time
from collections import namedtuple
from typing import Iterator, Union, Optional

import requests
import xbmc
import xbmcaddon

VideoSearchResult = namedtuple(
    "VideoSearchResult",
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
    ],
)

ChannelSearchResult = namedtuple(
    "ChannelSearchResult",
    [
        "type",
        "id",
        "thumbnail_url",
        "heading",
        "description",
        "verified",
        "sub_count",
    ],
)

PlaylistSearchResult = namedtuple(
    "PlaylistSearchResult",
    [
        "type",
        "id",
        "thumbnail_url",
        "heading",
        "channel",
        "channel_id",
        "verified",
        "video_count",
    ],
)

InvidiousApiResponseType = Union[
    VideoSearchResult, ChannelSearchResult, PlaylistSearchResult
]


class InvidiousAPIClient:
    instance_url: str
    session: requests.Session
    addon: xbmcaddon.Addon
    authenticated: bool
    username: Optional[str]
    password: Optional[str]

    def __init__(self, instance_url: str, auth: Optional[dict[str, str]] = None):
        self.instance_url = instance_url.rstrip("/")
        self.session = requests.Session()
        self.authenticated = False
        self.username, self.password = None, None
        if auth:
            self.username = auth["username"]
            self.password = auth["password"]
        self.addon = xbmcaddon.Addon()
        self.local = ("true" == self.addon.getSetting("local"))

    @property
    def base_url(self) -> str:
        return self.instance_url + "/api/v1/"

    def _login(self) -> None:
        if not self.username:
            raise
        login_response = self.session.post(
            self.instance_url + "/login",
            data={
                "email": self.username,
                "password": self.password,
                "action": "signin",
            },
        )

        login_response.raise_for_status()

        if login_response.ok:
            self.authenticated = True

    def _make_get_request(
        self, path: str, params: Optional[dict[str, str]] = None
    ) -> requests.Response:
        assembled_url = self.base_url + path

        xbmc.log(
            f"invidious ========== request {assembled_url} with {params} started ==========",
            xbmc.LOGDEBUG,
        )
        if self.local:
            params["local"] = "true"

        start = time.time()
        response = self.session.get(assembled_url, params=params, timeout=5)
        end = time.time()
        xbmc.log(
            f"invidious ========== request finished in {end - start}s ==========",
            xbmc.LOGDEBUG,
        )

        if response.status_code > 300:
            xbmc.log(
                f"invidious API request {assembled_url} with {params} failed with HTTP status {response.status_code}: {response.reason}.",
                xbmc.LOGWARNING,
            )
        response.raise_for_status()

        return response

    def _parse_list_response(
        self, response: requests.models.Response
    ) -> Iterator[InvidiousApiResponseType]:
        if not response or not response.content:
            raise StopIteration()
        data = response.json()

        # If a channel or playlist is opened, the videos are packaged
        # in a dict entry "videos".
        if "videos" in data:
            data = data["videos"]

        for item in data:
            # Playlist videos do not have the 'type' attribute
            if "type" not in item or item["type"] in ["video", "shortVideo"]:
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
                yield VideoSearchResult(
                    "video",
                    item["videoId"],
                    thumbnail_url,
                    item["title"],
                    item["author"],
                    item.get("description", self.addon.getLocalizedString(30000)),
                    item.get("viewCount", -1),  # Missing for playlists.
                    item.get("published", 0),  # Missing for playlists.
                    item["lengthSeconds"],
                )
            elif item["type"] == "channel":
                # Grab the highest resolution avatar image
                # Usually isn't more than 512x512
                thumbnail = sorted(
                    item["authorThumbnails"],
                    key=lambda thumb: thumb["height"],
                    reverse=True,
                )[0]

                yield ChannelSearchResult(
                    "channel",
                    item["authorId"],
                    "https:" + thumbnail["url"],
                    item["author"],
                    item["description"],
                    item["authorVerified"],
                    item["subCount"],
                )
            elif item["type"] == "playlist":
                yield PlaylistSearchResult(
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
                xbmc.log(
                    f'invidious received search result item with unknown response type {item["type"]}.',
                    xbmc.LOGWARNING,
                )

    def search(self, *terms):
        params = {
            "q": " ".join(terms),
            "sort_by": "upload_date",
        }

        response = self._make_get_request("search", params)

        return self._parse_list_response(response)

    def fetch_video_information(self, video_id):
        response = self._make_get_request(f"videos/{video_id}")

        return response.json()

    def fetch_channel_list(self, channel_id):
        response = self._make_get_request(f"channels/{channel_id}/videos")

        return self._parse_list_response(response)

    def fetch_playlist_list(self, playlist_id):
        response = self._make_get_request(f"playlists/{playlist_id}")

        return self._parse_list_response(response)

    def fetch_special_list(self, special_list_name: str):
        response = self._make_get_request(special_list_name)

        return self._parse_list_response(response)

    def fetch_feed(self) -> Iterator[VideoSearchResult]:
        if not self.authenticated:
            self._login()
        response = self._make_get_request("auth/feed")

        for result in self._parse_list_response(response):
            if isinstance(result, VideoSearchResult):
                yield result

    def fetch_subscribed_channels(self) -> Iterator[ChannelSearchResult]:
        if not self.authenticated:
            self._login()
        subscriptions_response = self._make_get_request("auth/subscriptions")

        data = subscriptions_response.json()
        for author in data:
            yield self.fetch_channel_info(author["authorId"])

    def fetch_channel_info(self, channel_id: str) -> ChannelSearchResult:
        response = self._make_get_request(f"channels/{channel_id}")

        data = response.json()
        thumbnail = sorted(
            data["authorThumbnails"],
            key=lambda thumb: thumb["height"],
            reverse=True,
        )[0]

        return ChannelSearchResult(
            "channel",
            data["authorId"],
            thumbnail["url"],
            data["author"],
            data["description"],
            data["authorVerified"],
            data["subCount"],
        )

    def subscribe(self, channel_id: str) -> None:
        if not self.authenticated:
            self._login()
        reponse = self.session.post(f"{self.base_url}auth/subscriptions/{channel_id}")
        if reponse.ok:
            return None
        raise

    def unsubscribe(self, channel_id: str) -> None:
        if not self.authenticated:
            self._login()
        response = self.session.delete(
            f"{self.base_url}auth/subscriptions/{channel_id}"
        )
        if response.ok:
            return None
        raise

    def mark_watched(self, video_id: str) -> None:
        if not self.authenticated:
            self._login()
        reponse = self.session.post(f"{self.base_url}auth/history/{video_id}")
        if reponse.ok:
            return None
        raise
