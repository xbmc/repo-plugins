import os
import pickle
from functools import wraps
from math import floor

import requests
import xbmc
import xbmcgui


class CSAuthFailed(Exception):
    def __init__(self, error_message):
        self.error_message = error_message


def _authenticate_and_retry_on_401(bound_method):
    @wraps(bound_method)
    def wrapper(instance, *args):
        try:
            return bound_method(instance, *args)
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                instance.authenticate(force=True)
                return bound_method(instance, *args)

    return wrapper


class CuriosityStream(object):
    """
    API reference:

    Error message in case of unauthorised access
    {
        "error": {
            "message": {
                "base": [
                    "Not authorized."
                ]
            },
            "status_code": 401
        }
    }

    Error message in case of unauthenticated access
    {
        "error": {
            "message": {
                "base": [
                    "Authentication required"
                ]
            }
        }
    }

    LOGIN
    POST https://api.curiositystream.com/v1/login/
    BODY:
        {
            "email": "your@email.com",
            "password": "YourPassword"
        }
    Error Response:
        {
            "error": {
                "message": {
                    "base": [
                        "The login credentials are incorrect. Please try again."
                    ]
                },
                "status_code": 401
            }
        }
    Success Response
        {
            "status": "success,
            "message": {
                "email": "your@email.com",
                ... user's data ...
                "auth_token": "authentication_token"
            }
        }

    """

    def __init__(self, username, password, profile_path, auth_context):
        self._username = username
        self._password = password
        self._profile_path = profile_path
        self._auth_context = auth_context
        self._authenticated = False
        self._base_url = "https://api.curiositystream.com/v1/"
        self._base_url2 = "https://api.curiositystream.com/v2/"
        self._session = requests.Session()
        self._session_file = os.path.join(self._profile_path, "session")
        self._load_session()

    def _save_session(self):
        with open(self._session_file, "w") as fd:
            pickle.dump(
                {
                    "headers": self._session.headers,
                    "cookies": requests.utils.dict_from_cookiejar(
                        self._session.cookies
                    ),
                },
                fd,
            )

    def _load_session(self):
        try:
            with open(self._session_file, "r") as f:
                session = pickle.load(f)
                print(session)
                self._session.cookies = requests.utils.cookiejar_from_dict(
                    session["cookies"]
                )
                self._session.headers.update(session["headers"])
        except IOError:
            # unable to read the file
            pass

    def authenticate(self, force=False):
        if (
            not force
            and "x-auth-token" in self._session.headers
            and "cs_session" in self._session.cookies
        ):
            # it should be still an authenticated session
            return
        with self._auth_context():
            if not self._username or not self._password:
                raise CSAuthFailed(
                    "Please provide username and password in the profile settings"
                )
            response = self._session.post(
                "{}login".format(self._base_url),
                json={"email": self._username, "password": self._password},
            )
            if not response.ok:
                raise CSAuthFailed("Login attempt failed")
            data = response.json()
            self._session.headers.update(
                {"x-auth-token": data["message"]["auth_token"]}
            )
            self._save_session()

    @_authenticate_and_retry_on_401
    def my_account(self):
        response = self._session.get("{}user".format(self._base_url))
        response.raise_for_status()
        return response.json()["data"]

    @_authenticate_and_retry_on_401
    def categories(self, parent=None):
        response = self._session.get("{}categories".format(self._base_url))
        response.raise_for_status()
        data = response.json()
        # No need to check paginator because categories are less than page limit
        return [
            {
                "name": cat["name"],
                "label": cat["label"],
                "art": {
                    "thumb": cat["image_url"],
                    "banner": cat["header_url"],
                    "fanart": cat["header_url"],
                    "landscape": cat["background_url"],
                },
            }
            for cat in (
                [
                    subcat
                    for cat in data["data"]
                    for subcat in cat["subcategories"]
                    if cat["name"] == parent
                ]
                if parent
                else data["data"]
            )
        ]

    def _get_collection_details(self, collection_id):
        resp = self._session.get(
            "{}collections/{}".format(self._base_url, collection_id)
        )
        return resp.json()["data"]

    def _extract_media_data(self, media_data):
        def title_with_episodes(m):
            if not m.get("is_collection", False):
                return u""
            # label returned by curiositystream media API seems to be always emtpy
            return u"{} ({} episodes)".format(m["title"], m["media_count"])

        def format_duration(m):
            duration = max(m.get("duration", 0), m.get("media_duration", 0))
            minutes = floor(duration / 60.0 % 60)
            hours = round((duration / 60.0 - minutes) / 60.0)
            return "{} {}m".format(
                "{}h".format(int(hours)) if hours > 0 else "", int(minutes)
            )

        def enhanced_description(m):
            return (
                u"{dur_epi}\n"
                u"Year {year}\n"
                u"Quality {quality}\n"
                u"{episode_number}\n"
                u"{description}\n"
                u"{producer}"
            ).format(
                description=m["description"],
                producer=m["producer"],
                year=m["year_produced"],
                dur_epi="{} episodes".format(m["media_count"])
                if m.get("is_collection", False)
                else "Duration {}".format(format_duration(m)),
                quality=m["quality"],
                episode_number="Episode {} of {}\n".format(
                    m["collection_order"] + 1,
                    self._get_collection_details(m["collection_id"])["title"],
                )
                if m.get("collection_id", 0) > 0
                else "\n",
            )

        return [
            {
                "id": media["id"],
                "label": title_with_episodes(media),
                "name": media["title"],
                "is_folder": media["obj_type"] == "collection",
                "art": {
                    "thumb": media["image_small"],
                    "banner": media["image_large"],
                    "fanart": media["image_show"]
                    if media["obj_type"] == "collection"
                    else media["image_movie"],
                    "landscape": media["image_medium"],
                },
                "video": {
                    "genre": media["type"],
                    "year": media["year_produced"],
                    "title": media["title"],
                    "plot": enhanced_description(media),
                    "plotoutline": media["description"],
                    "rating": float(media["rating_percentage"]) / 10.0,
                    "overlay": xbmcgui.ICON_OVERLAY_HD
                    if media["quality"] in ["HD", "4K"]
                    else xbmcgui.ICON_OVERLAY_NONE,
                },
            }
            for media in media_data
        ]

    @staticmethod
    def _extract_pagination(data):
        if "paginator" not in data:
            return False, False
        current_page = int(data["paginator"]["current_page"])
        total_pages = int(data["paginator"]["total_pages"])
        return (
            (current_page - 1) if current_page > 1 else False,
            (current_page + 1) if current_page < total_pages else False,
        )

    def _get_data(self, endpoint, params, page, use_version2=False):
        if page:
            params.update({"page": page})
        response = self._session.get(
            "{}{}".format(
                self._base_url2 if use_version2 else self._base_url, endpoint
            ),
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        prev_page, next_page = self._extract_pagination(data)
        return data, prev_page, next_page

    @_authenticate_and_retry_on_401
    def media(self, category=None, page=None):
        params = {"collections": True, "limit": 20}
        if category:
            params.update({"filterBy": "category", "term": category})
        data, prev_page, next_page = self._get_data("media", params, page)
        return (
            self._extract_media_data(data["data"]),
            prev_page,
            next_page,
        )

    @_authenticate_and_retry_on_401
    def history(self, page=None):
        params = {"filterBy": "history", "collections": True, "limit": 20}
        data, prev_page, next_page = self._get_data("media", params, page)
        return (
            self._extract_media_data(data["data"]),
            prev_page,
            next_page,
        )

    @_authenticate_and_retry_on_401
    def recently_added(self, page=None):
        params = {
            "filterBy": "recently_added",
            "term": "recently-added",
            "collections": True,
            "limit": 20,
        }
        data, prev_page, next_page = self._get_data("media", params, page)
        return (
            self._extract_media_data(data["data"]),
            prev_page,
            next_page,
        )

    @_authenticate_and_retry_on_401
    def collections_v1(self, parent=None, page=None):
        """
        CuriosityStream API has two collections endpoints.
        This one is used for listing the video inside a media collection.
        """
        params = {"limit": 20}
        data, prev_page, next_page = self._get_data(
            "collections/{}".format(parent if parent else ""), params, page
        )
        return (
            self._extract_media_data(data["data"]["media"] if parent else data["data"]),
            prev_page,
            next_page,
        )

    @_authenticate_and_retry_on_401
    def collections_v2(self, parent=None, page=None):
        """
        CuriosityStream API has two collections endpoints.
        This one groups media and collections in curated themes.
        """
        params = {"limit": 20}
        if parent is None:
            params.update({"excludeMedia": True})
        data, prev_page, next_page = self._get_data(
            "collections/{}".format(parent if parent else ""),
            params,
            page,
            use_version2=True,
        )
        if parent is None:
            return (
                [
                    {
                        "id": col["id"],
                        "name": col["title"],
                        "label": col["title"],
                        "is_folder": True,
                        "art": {
                            "thumb": col["image_url"],
                            "banner": col["hero_url"],
                            "fanart": col["hero_url"],
                            "landscape": col["background_url"],
                        },
                        "video": {
                            "title": col["title"],
                            "plot": col["description"],
                            "plotoutline": col["description"],
                        },
                    }
                    for col in data["data"]
                ],
                prev_page,
                next_page,
            )
        else:
            return (
                self._extract_media_data(data["data"]["media"]),
                prev_page,
                next_page,
            )

    @_authenticate_and_retry_on_401
    def watchlist(self, page):
        params = {"filterBy": "bookmarked", "collections": True, "limit": 20}
        data, prev_page, next_page = self._get_data("media", params, page)
        return (
            self._extract_media_data(data["data"]),
            prev_page,
            next_page,
        )

    @_authenticate_and_retry_on_401
    def popular(self, page):
        params = {"filterBy": "popular", "collections": True, "limit": 20}
        data, prev_page, next_page = self._get_data("media", params, page)
        return (
            self._extract_media_data(data["data"]),
            prev_page,
            next_page,
        )

    @_authenticate_and_retry_on_401
    def watching(self, page):
        params = {
            "filterBy": "watching",
            "term": "watching",
            "collections": True,
            "limit": 20,
        }
        data, prev_page, next_page = self._get_data("media", params, page)
        return (
            self._extract_media_data(data["data"]),
            prev_page,
            next_page,
        )

    @_authenticate_and_retry_on_401
    def recommended(self, page):
        params = {
            "filterBy": "user-recommended",
            "term": "user-recommended",
            "collections": True,
            "limit": 20,
        }
        data, prev_page, next_page = self._get_data("media", params, page)
        return (
            self._extract_media_data(data["data"]),
            prev_page,
            next_page,
        )

    def _get_media_details(self, media_id):
        resp = self._session.get("{}media/{}".format(self._base_url, media_id))
        return resp.json()["data"]

    @_authenticate_and_retry_on_401
    def featured(self, label="NEW THIS WEEK"):
        response = self._session.get("{}featured".format(self._base_url))
        response.raise_for_status()
        media = [
            self._get_media_details(media_id)
            for featured in response.json()
            for media_id in featured["media_ids"]
            if featured["label"] == label
        ]
        return (
            self._extract_media_data(media),
            False,
            False,
        )

    @_authenticate_and_retry_on_401
    def media_playlist_url(self, media):
        def get_media():
            response = self._session.get("{}media/{}".format(self._base_url, media))
            response.raise_for_status()
            return response.json()

        data = get_media()
        if data["data"]["status"] != "full_featured":
            self.authenticate(force=True)
        data = get_media()
        hd_encodings = [
            encoding
            for encoding in data["data"]["encodings"]
            if encoding["type"] == "hd"
        ]
        return hd_encodings[0]["master_playlist_url"]
