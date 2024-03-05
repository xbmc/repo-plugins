# coding: utf-8
#
# Copyright © 2020 melmorabity
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from __future__ import unicode_literals

import logging
from os.path import dirname
from os.path import join
import re
import time

try:
    from itertools import zip_longest  # type: ignore
except ImportError:
    from itertools import izip_longest as zip_longest

try:
    from typing import Any
    from typing import Dict
    from typing import Generator
    from typing import List
    from typing import NamedTuple
    from typing import Optional
    from typing import Text
    from typing import Union

    Item = Dict[Text, Any]
    Collection = List[Item]

    Art = Dict[Text, Optional[Text]]  # pylint: disable=unsubscriptable-object
    Url = Dict[Text, Union[int, Text]]

    ParsedItem = NamedTuple(
        "ParsedItem",
        [
            ("label", Text),
            ("url", Url),
            ("info", Dict[Text, Any]),
            ("art", Art),
            ("properties", Dict[Text, Text]),
        ],
    )
except ImportError:
    from collections import namedtuple

    ParsedItem = namedtuple(  # type: ignore
        "ParsedItem", ["label", "url", "info", "art", "properties"]
    )

from requests import Response
from requests import Session
from requests.exceptions import HTTPError

from resources.lib.utils import capitalize
from resources.lib.utils import html_to_text
from resources.lib.utils import update_url_params


_LOGGER = logging.getLogger(__name__)

_IMAGE_TYPE_MAPPING = {
    "background_16x9": "fanart",
    "carre": "thumb",
    "vignette_16x9": "fanart",
    "vignette_3x4": "poster",
    "hero": "clearart",
    "hero_plein": "characterart",
    "logo": "clearlogo",
}  # type: Dict[Optional[Text], Text]

_MEDIA_DIR = join(dirname(__file__), "..", "media")

_CHANNEL_ICONS = {
    "france-2": join(_MEDIA_DIR, "france-2.png"),
    "france-3": join(_MEDIA_DIR, "france-3.png"),
    "france-4": join(_MEDIA_DIR, "france-4.png"),
    "france-5": join(_MEDIA_DIR, "france-5.png"),
    "france-o": join(_MEDIA_DIR, "france-o.png"),
    "la1ere": join(_MEDIA_DIR, "la1ere.png"),
    "franceinfo": join(_MEDIA_DIR, "franceinfo.png"),
    "slash": join(_MEDIA_DIR, "slash.png"),
    "okoo": join(_MEDIA_DIR, "okoo.png"),
    "culturebox": join(_MEDIA_DIR, "culturebox.png"),
    "serie": join(_MEDIA_DIR, "serie.png"),
}  # type: Dict[Optional[Text], Text]

_ALL_TV_SHOWS_ICON = join(_MEDIA_DIR, "all-tv-shows.png")
_ALL_VIDEOS_ICON = join(_MEDIA_DIR, "all-videos.png")
_NEXT_PAGE_ICON = join(_MEDIA_DIR, "next-page.png")


class FranceTVException(Exception):
    pass


class FranceTV:
    _API_URL = "https://api-mobile.yatta.francetv.fr"

    def __init__(self):
        self._session = Session()
        self._session.hooks = {"response": [self._requests_raise_status]}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self._session:
            self._session.close()

    @staticmethod
    def _requests_raise_status(response, *_args, **_kwargs):
        # type: (Response, Any, Any) -> None

        try:
            response.raise_for_status()
        except HTTPError as ex:
            try:
                raise FranceTVException(ex, ex.response.json().get("error"))
            except ValueError:
                raise ex

    def _query_api(self, path):
        # type: (Text) -> Union[Item, Collection]

        return self._session.get(
            "{}/{}".format(self._API_URL, path),
            params={"platform": "apps"},
        ).json()

    @staticmethod
    def _get_channel_id(item):
        # type: (Item) -> Optional[Text]

        if isinstance(item.get("channel"), dict):
            channel_id = item["channel"].get("channel_path")
        else:
            channel_id = (
                item.get("channel")
                or item.get("channel_path")
                or item.get("region_path")
            )

        if channel_id:
            return re.split("[_/]", channel_id)[0]

        return None

    @staticmethod
    def _is_live(item, parent_item):
        # type: (Item, Item) -> bool

        # "is_live" item key can be "false", even for "real" lives
        if parent_item.get("type") in [
            "live",
            "live_channel",
            "current_live",
        ]:
            return True

        return bool(item.get("is_live"))

    @staticmethod
    def _parse_item_art(item, parent_item):
        # type: (Item, Item) -> Art

        art = {}  # type: Art

        channel = FranceTV._get_channel_id(item)
        channel_icon = _CHANNEL_ICONS.get(channel)
        art.setdefault("icon", channel_icon)

        # Use channel logo as thumb for live videos
        if FranceTV._is_live(item, parent_item):
            art.setdefault("thumb", channel_icon)

        item_type = item.get("type")

        # Artwork provided by the france.tv API is really bad for
        # channels
        if item_type == "channel" and channel:
            return art

        for image in item.get("images") or []:
            image_type = _IMAGE_TYPE_MAPPING.get(image.get("type"))

            if not image_type or not image.get("urls"):
                continue

            # Category fanarts provided the france.tv API are low-resolution
            if item_type == "categorie" and image_type == "fanart":
                continue

            # Sort images by quality
            image_urls = sorted(
                list(image["urls"].items()),
                key=lambda i: int(i[0].split(":")[1]),
            )

            art.setdefault(image_type, image_urls[-1][1])

        # Complete missing artwork with item program
        if item.get("program"):
            program_art = FranceTV._parse_item_art(item["program"], {})
            art = dict(list(program_art.items()) + list(art.items()))

        return art

    @staticmethod
    # pylint: disable=too-many-branches
    def _get_item_url(
        item,  # type: Item
        path,  # type: Text
        level,  # type: Optional[int]
        parent_item,  # type: Item
    ):
        # type: (...) -> Optional[Url]

        video_id = None
        if FranceTV._is_live(item, parent_item):
            video_id = (item.get("channel") or {}).get("si_id")
        if not video_id:
            video_id = item.get("si_id")

        if video_id:
            return {
                "mode": "watch",
                "id": video_id,
            }

        url = {
            "mode": "collection",
        }  # type: Dict[Text, Any]

        item_type = item.get("type")

        if item.get("url_complete"):
            if item_type == "sous_categorie":
                url["path"] = "apps/sub-categories/{}".format(
                    item["url_complete"]
                )
            else:
                url["path"] = "apps/{}s/{}".format(
                    item_type, item["url_complete"]
                )
        elif item_type == "collection" and item.get("id"):
            url["path"] = "generic/collections/{}".format(item["id"])
        elif item.get("program_path"):
            url["path"] = "apps/program/{}".format(item["program_path"])
        elif item.get("link"):
            url["path"] = item["link"]
        elif item.get("region_path"):
            url["path"] = "/apps/regions/{}/{}".format(
                item["region_path"], path.split("/")[-1]
            )
        elif item.get("channel_path"):
            if item.get("channel_url") == "la1ere":
                url["path"] = "apps/regions/outre-mer"
            else:
                url["path"] = "apps/channels/{}".format(item["channel_path"])
        elif "items" in item:
            url["path"] = path
            url["level"] = level
        else:
            _LOGGER.warning("Item %s in path %s is unmanaged", item, path)
            return None

        # Ignore items based on user authentication
        if ":userId" in url["path"] or ":userUId" in url["path"]:
            return None

        return url

    @staticmethod
    # pylint: disable=too-many-branches,too-many-statements
    def _parse_item(
        item,  # type: Item
        path,  # type: Text
        level,  # type: Optional[int]
        parent_item,  # type: Item
    ):
        # type: (...) -> Optional[ParsedItem]

        url = FranceTV._get_item_url(item, path, level, parent_item)
        if not url:
            return None

        info = {}  # type: Dict[Text, Any]
        art = FranceTV._parse_item_art(item, parent_item)
        properties = {}  # type: Dict[Text, Text]

        item_type = item.get("type")

        title = capitalize(item.get("label") or item.get("title"))
        program = capitalize((item.get("program") or {}).get("label"))

        if not title:
            if item_type == "categories":
                title = "Catégories"
            elif (
                parent_item.get("type") == "program"
                and item_type == "playlist_program"
            ):
                title = "À regarder également"
            elif program:
                title = program
            else:
                _LOGGER.warning("No title in item %s in path %s", item, path)
                title = "Inconnu"

        if title == program and item.get("episode_title"):
            title = capitalize(item["episode_title"])

        label_parts = [program, title]
        label = " – ".join([i for i in label_parts if i])

        result = ParsedItem(label, url, info, art, properties)

        info["title"] = title
        info["plot"] = (
            html_to_text(item.get("description") or item.get("synopsis"))
            or title
        )

        # No need to parse more item metadata for folders
        if url["mode"] != "watch":
            return result

        info["genre"] = capitalize((item.get("category") or {}).get("label"))
        info["year"] = item.get("production_year") or item.get("year")

        if item.get("episode"):
            info["episode"] = item["episode"]

        if item.get("season"):
            info["season"] = item["season"]

        if FranceTV._is_live(item, parent_item):
            # Don't mark live streams as read once played
            info["playcount"] = 0

        if item.get("casting"):
            cast = item["casting"].split(", ")

            if item.get("characters"):
                info["cast"] = list(
                    zip_longest(
                        cast, item["characters"].replace("\n", "").split(", ")
                    )
                )
            else:
                info["cast"] = cast
        elif item.get("presenter"):
            info["cast"] = [
                (
                    p,
                    "Présentateur",
                )
                for p in item["presenter"]
                .replace("Présenté par ", "")
                .rstrip(".")
                .split(",")
            ]

        if item.get("director"):
            info["director"] = item["director"].split(", ")

        info["mpaa"] = item.get("rating_csa_code")
        info["plotoutline"] = item.get("headline_title") or item.get(
            "subtitle"
        )
        info["duration"] = item.get("duration")

        if program:
            info["tvshowtitle"] = program

        if not info["year"] and item.get("broadcast_begin_date"):
            info["aired"] = time.strftime(
                "%Y-%m-%d",  # type: ignore
                time.localtime(item["broadcast_begin_date"]),
            )

        if item.get("begin_date"):
            info["dateadded"] = time.strftime(
                "%Y-%m-%d %H:%M:%S",  # type: ignore
                time.localtime(item["begin_date"]),
            )

        if (
            info.get("tvshowtitle")
            or info.get("episode")
            or info.get("season")
        ):
            info["mediatype"] = "episode"
        else:
            info["mediatype"] = "movie"

        properties["isPlayable"] = "true"

        return result

    def get_collection(self, path, level=None):
        # type: (Text, Optional[int]) -> Generator[ParsedItem, None, None]

        data = self._query_api(path)

        if isinstance(data, dict):
            cursor = data.get("cursor")
            parent_item = data.get("item") or data
            collection = data.get("collections") or data.get("items") or []
        else:
            cursor = None
            parent_item = {}
            collection = data

        if level is not None and level < len(collection):
            cursor = None
            parent_item = collection[level]
            collection = collection[level].get("items") or []

        # Sub-category items only provides incomplete list of programs and
        # videos, use our own extra items insteads
        if parent_item.get("type") != "sous_categorie":
            for index, item in enumerate(collection):
                parsed_item = self._parse_item(item, path, index, parent_item)
                if parsed_item:
                    yield parsed_item

        if path == "generic/channels":
            # Add "virtual" Okoo/Culturebox channels in the channel collection,
            # as done on the france.tv website
            yield ParsedItem(
                "Okoo",
                {"mode": "collection", "path": "apps/categories/enfants"},
                {"plot": "Okoo"},
                {"icon": _CHANNEL_ICONS["okoo"]},
                {},
            )
            yield ParsedItem(
                "Culturebox",
                {
                    "mode": "collection",
                    "path": "apps/categories/spectacles-et-culture",
                },
                {"plot": "Culturebox"},
                {"icon": _CHANNEL_ICONS["culturebox"]},
                {},
            )

        # Extra items

        parent_item_type = parent_item.get("type")

        if parent_item_type in [
            "categorie",
            "channel",
            "program",
            "region",
            "sous_categorie",
        ]:
            collection_id = (
                parent_item.get("channel_path")
                or parent_item.get("program_path")
                or parent_item.get("region_path")
                or parent_item.get("url_complete")
            )

            # Add "all TV shows"/"all programs" item
            if parent_item_type != "program":
                yield ParsedItem(
                    "$LOCALIZE[30101]",
                    {
                        "mode": "collection",
                        "path": "apps/regions/{}/programs".format(
                            collection_id
                        ),
                    },
                    {"plot": ""},
                    {"icon": _ALL_TV_SHOWS_ICON},
                    {"SpecialSort": "bottom"},
                )

            yield ParsedItem(
                "$LOCALIZE[30102]",
                {
                    "mode": "collection",
                    "path": "generic/taxonomy/{}/contents".format(
                        collection_id
                    ),
                },
                {"plot": ""},
                {"icon": _ALL_VIDEOS_ICON},
                {"SpecialSort": "bottom"},
            )

        if (
            level is None
            and cursor
            and cursor.get("next")
            and cursor.get("last")
        ):
            # Add "next page" item
            label = "$LOCALIZE[30103] ({}/{})".format(
                cursor["next"] + 1, cursor["last"] + 1
            )
            yield ParsedItem(
                label,
                {
                    "mode": "collection",
                    "path": update_url_params(path, page=cursor["next"]),
                },
                {"plot": ""},
                {"icon": _NEXT_PAGE_ICON},
                {"SpecialSort": "bottom"},
            )
