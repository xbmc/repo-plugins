import json
from urllib.parse import urlparse, parse_qsl

import requests


class LoginError(Exception):
    pass


class Api:
    HEADERS = {
        "x-api-key": "857a1e5d-e35e-4fdf-805b-a87b6f8364bf",
        "Origin": "https://play.tottenhamhotspur.com",
        "Referer": "https://play.tottenhamhotspur.com/",
        "Content-Type": "application/json",
        "Realm": "dce.spurs",
    }

    USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0"

    URL_ROOT = "https://dce-frontoffice.imggaming.com/api"

    def __init__(self, token=None):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

        if token is None:
            self.token = self._auth_token()
        else:
            self.token = token

    def login(self, user=None, password=None):
        response = self.session.post(
            "https://login.tottenhamhotspur.com/Identity/login",
            params={
                "response_type": "code",
                "redirect_uri": "https://play.tottenhamhotspur.com",
                "client_id": "EnKfF3qxkBD90uR",
                "scope": "openid email",
                "tenantId": "SPURS",
                "email": user,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            data=f"email={user}&password={password}",
        )

        if response.status_code == 401:
            raise LoginError(response.json()["message"])

        url = response.json()["redirect"]
        code = dict(parse_qsl(urlparse(url).query))["code"]

        self.token = self.session.post(
            f"{self.URL_ROOT}/v2/openid/enactor_sso/token",
            headers=self.HEADERS,
            data=json.dumps({"authorisationCode": code}),
        ).json()["authorisationToken"]

        return self.token

    def buckets(self, section, num_pages=3):
        return self._categories(section=section, num_pages=num_pages)

    def playlists(self):
        return self._categories(types=["PLAYLISTS"])

    def get_live_events(self):
        events = self.session.get(f"{self.URL_ROOT}/v2/event/live", headers=self._headers()).json()

        return self._videos(events["events"])

    def get_playlist_videos(self, playlist, page):
        page = page or 1
        params = {"rpp": 25, "p": page}

        videos = self.session.get(
            f"{self.URL_ROOT}/v2/vod/playlist/{playlist}",
            params=params,
            headers=self._headers(),
        ).json()["videos"]

        total_pages = videos["totalPages"]
        return self._videos(videos["vods"]), int(page) < total_pages

    def get_bucket_videos(self, bucket, last_seen):
        contents, last_seen, more_available = self._get_bucket_contents(bucket, last_seen)

        return self._videos(contents), last_seen, more_available

    def get_bucket_playlists(self, bucket, last_seen):
        contents, last_seen, more_available = self._get_bucket_contents(bucket, last_seen)

        playlists = (
            {
                "title": playlist["title"],
                "id": playlist["id"],
                "thumbnail": playlist["smallCoverUrl"],
            }
            for playlist in contents
        )

        return playlists, last_seen, more_available

    def get_video_url(self, video_id, live=False):
        endpoint = "event" if live else "vod"
        response = self.session.get(
            f"{self.URL_ROOT}/v4/{endpoint}/{video_id}",
            params={"includePlaybackDetails": "URL"},
            headers=self._headers(),
        )
        player_url = response.json()["playerUrlCallback"]

        response = self.session.get(player_url).json()
        if live:
            return response["hlsUrl"]
        return response["hls"][0]["url"]

    def _get_bucket_contents(self, bucket, last_seen):
        params = {"rpp": 25}
        if last_seen is not None:
            params["lastSeen"] = last_seen

        bucket = self.session.get(
            f"{self.URL_ROOT}/v4/content/bucket/{bucket}",
            params=params,
            headers=self._headers(),
        ).json()

        last_seen = bucket["paging"]["lastSeen"]
        more_available = bucket["paging"]["moreDataAvailable"]

        return bucket["contentList"], last_seen, more_available

    def _videos(self, videos):
        return (
            {
                "title": video["title"],
                "id": video["id"],
                "duration": video.get("duration"),
                "description": video.get("description"),
                "thumbnail": video["thumbnailUrl"],
                "poster": video.get("posterUrl"),
                "cover": video.get("coverUrl"),
            }
            for video in videos
            if video["accessLevel"] == "GRANTED"
        )

    def _auth_token(self):
        response = self.session.get(f"{self.URL_ROOT}/v1/init", headers=self.HEADERS)
        return response.json()["authentication"]["authorisationToken"]

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} | self.HEADERS

    def _categories(self, types=("VOD_PLAYLIST", "VOD_VIDEO"), section="First Team", num_pages=3):
        more_available = True
        last_seen = None
        page = 0
        section_number = 0

        while more_available and page < num_pages:
            page += 1
            params = {"bpp": 10}
            if last_seen:
                params["lastSeen"] = last_seen

            categories = self.session.get(
                f"{self.URL_ROOT}/v4/content/{section}",
                params=params,
                headers=self._headers(),
            ).json()

            more_available = categories["paging"]["moreDataAvailable"]
            last_seen = categories["paging"]["lastSeen"]

            for bucket in categories["buckets"]:
                if bucket["type"] in types:
                    yield bucket["name"], bucket["exid"]
                elif bucket["type"] == "SECTION_LINK":
                    section_number += 1
                    if section_number > 1:
                        break
