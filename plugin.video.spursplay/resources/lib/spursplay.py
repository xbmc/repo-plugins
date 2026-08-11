import base64
import hashlib
import json
import re
import secrets
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

    BROWSER_HEADERS = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-GB,en;q=0.5",
    }

    # Auth0 bot detection expects the headers a browser sends when navigating to a page.
    NAVIGATION_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    URL_ROOT = "https://dce-frontoffice.imggaming.com/api"

    # Thumbnail filenames embed the upload date, e.g. ".../original/p/2025/10/04/xxx.jpg",
    # which matches the video's publish date. The bucket listing has no date field of its
    # own, so this avoids an extra request per video just to show one.
    THUMBNAIL_DATE_RE = re.compile(r"/(\d{4})/(\d{2})/(\d{2})/")

    # SpursPlay moved its sign-in to Auth0 Universal Login, exchanging the resulting
    # Auth0 tokens for an IMG Gaming (dce) authorisation token via an OpenID exchange.
    AUTH0_DOMAIN = "auth.tottenhamhotspur.com"
    AUTH0_CLIENT_ID = "WpCY8WImmTjFslafikdhn5AbVOiJSrKt"
    AUTH0_AUDIENCE = "user-svc-api"
    AUTH0_REDIRECT_URI = "https://www.tottenhamhotspur.com/callback"
    AUTH0_SCOPE = "openid profile email offline_access"
    SSO_PROVIDER = "spurs_auth0_sso"

    def __init__(self, token=None):
        self.session = requests.Session()
        self.session.headers.update(self.BROWSER_HEADERS)
        self.refresh_token = None
        # Whether self.token belongs to a signed-in user, rather than the anonymous
        # token fetched below. Callers should set this after a successful login().
        self.signed_in = False

        if token is None:
            self.token = self._auth_token()
        else:
            self.token = token

    def login(self, user, password):
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )

        authorize = self.session.get(
            f"https://{self.AUTH0_DOMAIN}/authorize",
            params={
                "client_id": self.AUTH0_CLIENT_ID,
                "redirect_uri": self.AUTH0_REDIRECT_URI,
                "response_type": "code",
                "scope": self.AUTH0_SCOPE,
                "audience": self.AUTH0_AUDIENCE,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": secrets.token_urlsafe(16),
                "nonce": secrets.token_urlsafe(16),
            },
            headers=self.NAVIGATION_HEADERS,
        )
        state = dict(parse_qsl(urlparse(authorize.url).query)).get("state")
        if state is None:
            raise LoginError("Unexpected sign-in page from SPURSPLAY")

        response = self.session.post(
            f"https://{self.AUTH0_DOMAIN}/u/login",
            params={"state": state},
            data={"state": state, "username": user, "password": password},
            headers=self.NAVIGATION_HEADERS
            | {
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": f"https://{self.AUTH0_DOMAIN}",
                "Referer": authorize.url,
                "Sec-Fetch-Site": "same-origin",
            },
            allow_redirects=False,
        )

        code = self._follow_to_code(response)
        if code is None:
            if "data-captcha-sitekey" in response.text:
                raise LoginError("Sign-in blocked by a CAPTCHA. Try again later.")
            raise LoginError("Incorrect email or password")

        tokens = self.session.post(
            f"https://{self.AUTH0_DOMAIN}/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": self.AUTH0_CLIENT_ID,
                "code": code,
                "code_verifier": verifier,
                "redirect_uri": self.AUTH0_REDIRECT_URI,
            },
        ).json()

        return self._exchange(tokens["id_token"], tokens["access_token"])

    def _follow_to_code(self, response):
        redirects = 0
        while response.is_redirect and redirects < 10:
            redirects += 1
            location = response.headers["location"]
            if location.startswith("/"):
                location = f"https://{self.AUTH0_DOMAIN}{location}"
            if location.startswith(self.AUTH0_REDIRECT_URI):
                return dict(parse_qsl(urlparse(location).query)).get("code")
            response = self.session.get(
                location,
                headers=self.NAVIGATION_HEADERS | {"Sec-Fetch-Site": "same-origin"},
                allow_redirects=False,
            )

        return None

    def _exchange(self, id_token, access_token):
        subject_token = {
            "idToken": id_token,
            "accessToken": access_token,
            "refreshToken": None,
            "providerName": self.SSO_PROVIDER,
        }
        response = self.session.post(
            f"{self.URL_ROOT}/v2/openid/{self.SSO_PROVIDER}/exchange",
            headers=self.HEADERS | {"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token": json.dumps(subject_token),
                "subject_token_type": "idAccessRefresh",
            },
        ).json()

        self.token = response["access_token"]
        self.refresh_token = response["refresh_token"]
        return self.token, self.refresh_token

    def refresh(self, refresh_token):
        response = self.session.post(
            f"{self.URL_ROOT}/v1/token/refresh",
            headers=self._headers(),
            data=json.dumps({"refreshToken": refresh_token}),
        )
        if not response.ok:
            raise LoginError("Session refresh failed")

        data = response.json()
        self.token = data["authorisationToken"]
        self.refresh_token = data.get("refreshToken", refresh_token)
        return self.token, self.refresh_token

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
            return response.get("hlsUrl")
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

    def is_signed_in_only(self, bucket_id):
        """True if a bucket requires signing in but not a paid subscription, i.e. it
        would show nothing at all while browsing anonymously."""
        contents, _, _ = self._get_bucket_contents(bucket_id, None)
        levels = {video["accessLevel"] for video in contents}
        return levels == {"GRANTED_ON_SIGN_IN"}

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
                "date": self._thumbnail_date(video["thumbnailUrl"]),
            }
            for video in videos
            if video["accessLevel"] == "GRANTED"
        )

    def _thumbnail_date(self, thumbnail_url):
        match = self.THUMBNAIL_DATE_RE.search(thumbnail_url)
        return "-".join(match.groups()) if match else None

    def _auth_token(self):
        response = self.session.get(f"{self.URL_ROOT}/v1/init", headers=self.HEADERS)
        return response.json()["authentication"]["authorisationToken"]

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} | self.HEADERS

    def _categories(
        self, types=("VOD_PLAYLIST", "VOD_VIDEO", "PLAYLISTS"), section="First Team", num_pages=3
    ):
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
                    yield bucket["name"], bucket["exid"], bucket["type"]
                elif bucket["type"] == "SECTION_LINK":
                    section_number += 1
                    if section_number > 1:
                        break
