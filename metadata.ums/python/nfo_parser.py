from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

from models import (
    Artwork,
    ArtworkType,
    DataSource,
    MovieDetails,
    Person,
    Rating,
    TVShowDetails,
)


@dataclass
class NfoParseResult:
    kinopoisk_id: int = 0
    imdb_id: str = ""


class NfoParser:

    _PATTERNS = [
        (
            "kinopoisk_url",
            re.compile(r"kinopoisk\.ru/(?:film|series)/(\d+)", re.IGNORECASE),
            "kinopoisk_id",
        ),
        (
            "kinopoisk_uniqueid",
            re.compile(
                r'<uniqueid\b[^>]*type=["\']kinopoisk["\'][^>]*>(\d+)</uniqueid>',
                re.IGNORECASE,
            ),
            "kinopoisk_id",
        ),
        (
            "imdb_url",
            re.compile(r"(tt\d{7,8})", re.IGNORECASE),
            "imdb_id",
        ),
        (
            "imdb_uniqueid",
            re.compile(
                r'<uniqueid\b[^>]*type=["\']imdb["\'][^>]*>(tt\d{7,8})</uniqueid>',
                re.IGNORECASE,
            ),
            "imdb_id",
        ),
    ]

    def __init__(self, logger):
        self._logger = logger

    def parse(self, nfo_content: str) -> NfoParseResult:
        self._logger.info("NfoParser.parse: parsing NFO content")
        result = NfoParseResult()

        for name, pattern, field_name in self._PATTERNS:
            match = pattern.search(nfo_content)
            if match:
                value = match.group(1)
                self._logger.debug(f"NfoParser.parse: matched {name} = {value}")

                if field_name == "kinopoisk_id" and not result.kinopoisk_id:
                    result.kinopoisk_id = int(value)
                elif field_name == "imdb_id" and not result.imdb_id:
                    result.imdb_id = value

        self._logger.info(
            f"NfoParser.parse: result kp={result.kinopoisk_id}, "
            f"imdb={result.imdb_id}"
        )
        return result

    # ------------------------------------------------------------------
    # Full NFO XML parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _text(root: ET.Element, tag: str) -> str:
        elem = root.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
        return ""

    @staticmethod
    def _int(root: ET.Element, tag: str) -> int:
        elem = root.find(tag)
        if elem is not None and elem.text:
            try:
                return int(elem.text.strip())
            except ValueError:
                return 0
        return 0

    @staticmethod
    def _text_list(root: ET.Element, tag: str) -> list:
        result = []
        for elem in root.findall(tag):
            if elem.text and elem.text.strip():
                result.append(elem.text.strip())
        return result

    def _parse_ratings(self, root: ET.Element) -> list:
        ratings = []
        ratings_elem = root.find("ratings")
        if ratings_elem is None:
            return ratings

        source_map = {
            "kinopoisk": DataSource.KINOPOISK,
            "imdb": DataSource.IMDB,
            "rottentomatoes": DataSource.ROTTEN_TOMATOES,
            "metacritic": DataSource.METACRITIC,
        }

        for rating_elem in ratings_elem.findall("rating"):
            name = (rating_elem.get("name") or "").lower()
            source = source_map.get(name)
            if source is None:
                continue

            value_elem = rating_elem.find("value")
            votes_elem = rating_elem.find("votes")

            try:
                value = float(value_elem.text.strip()) if value_elem is not None and value_elem.text else 0.0
            except ValueError:
                value = 0.0

            try:
                votes = int(votes_elem.text.strip()) if votes_elem is not None and votes_elem.text else 0
            except ValueError:
                votes = 0

            if value > 0:
                ratings.append(Rating(source=source, value=value, votes=votes))

        self._logger.debug(f"NfoParser._parse_ratings: parsed {len(ratings)} ratings")
        return ratings

    def _parse_actors(self, root: ET.Element) -> list:
        cast = []
        for actor_elem in root.findall("actor"):
            name_elem = actor_elem.find("name")
            if name_elem is None or not name_elem.text:
                continue

            role_elem = actor_elem.find("role")
            thumb_elem = actor_elem.find("thumb")
            order_elem = actor_elem.find("order")

            try:
                order = int(order_elem.text.strip()) if order_elem is not None and order_elem.text else len(cast)
            except ValueError:
                order = len(cast)

            person = Person(
                name_ru=name_elem.text.strip(),
                role=(role_elem.text.strip() if role_elem is not None and role_elem.text else ""),
                photo_url=(thumb_elem.text.strip() if thumb_elem is not None and thumb_elem.text else ""),
                order=order,
            )
            cast.append(person)

        self._logger.debug(f"NfoParser._parse_actors: parsed {len(cast)} actors")
        return cast

    def _parse_artwork(self, root: ET.Element) -> list:
        artworks = []
        for thumb_elem in root.findall("thumb"):
            url = (thumb_elem.text or "").strip()
            if not url:
                continue
            aspect = (thumb_elem.get("aspect") or "").lower()
            if aspect == "poster":
                art_type = ArtworkType.POSTER
            elif aspect == "fanart":
                art_type = ArtworkType.FANART
            else:
                art_type = ArtworkType.POSTER

            artworks.append(Artwork(url=url, artwork_type=art_type))

        self._logger.debug(f"NfoParser._parse_artwork: parsed {len(artworks)} artworks")
        return artworks

    def _parse_uniqueids(self, root: ET.Element, details):
        for uid in root.findall("uniqueid"):
            uid_type = (uid.get("type") or "").lower()
            uid_text = (uid.text or "").strip()
            if uid_type == "kinopoisk" and uid_text.isdigit():
                details.kinopoisk_id = int(uid_text)
            elif uid_type == "imdb" and uid_text.startswith("tt"):
                details.imdb_id = uid_text

    def _parse_directors(self, root: ET.Element) -> list:
        directors = []
        for elem in root.findall("director"):
            name = (elem.text or "").strip()
            if name:
                directors.append(Person(name_ru=name))
        return directors

    def _parse_writers(self, root: ET.Element) -> list:
        writers = []
        for elem in root.findall("credits"):
            name = (elem.text or "").strip()
            if name:
                writers.append(Person(name_ru=name))
        return writers

    def parse_full_movie(self, nfo_content: str) -> Optional[MovieDetails]:
        self._logger.info("NfoParser.parse_full_movie: parsing full movie NFO")
        try:
            root = ET.fromstring(nfo_content)
        except ET.ParseError as e:
            self._logger.warning(f"NfoParser.parse_full_movie: XML parse error: {e}")
            return None

        title = self._text(root, "title")
        if not title:
            self._logger.warning("NfoParser.parse_full_movie: <title> missing")
            return None

        details = MovieDetails(
            title_ru=title,
            title_original=self._text(root, "originaltitle"),
            year=self._int(root, "year"),
            plot=self._text(root, "plot"),
            tagline=self._text(root, "tagline"),
            runtime=self._int(root, "runtime"),
            mpaa=self._text(root, "mpaa"),
            genres=self._text_list(root, "genre"),
            countries=self._text_list(root, "country"),
            studios=self._text_list(root, "studio"),
            tags=self._text_list(root, "tag"),
        )

        plot_outline = self._text(root, "outline")
        if plot_outline:
            details.plot_outline = plot_outline
            self._logger.info("NfoParser.parse_full_movie: found <outline>")

        premiere_date = self._text(root, "premiered")
        if premiere_date:
            details.premiere_date = premiere_date
            self._logger.info(f"NfoParser.parse_full_movie: found <premiered>={premiere_date}")

        self._parse_uniqueids(root, details)
        details.ratings = self._parse_ratings(root)
        details.directors = self._parse_directors(root)
        details.writers = self._parse_writers(root)
        details.cast = self._parse_actors(root)
        details.artwork = self._parse_artwork(root)

        set_elem = root.find("set")
        if set_elem is not None:
            set_name_elem = set_elem.find("name")
            if set_name_elem is not None and set_name_elem.text:
                details.set_name = set_name_elem.text.strip()

        trailer_text = self._text(root, "trailer")
        if trailer_text:
            details.trailer_url = trailer_text
            self._logger.debug(f"NfoParser.parse_full_movie: trailer_url='{trailer_text}'")

        original_language = self._text(root, "language")
        if original_language:
            details.original_language = original_language
            self._logger.info(f"NfoParser.parse_full_movie: found <language>={original_language}")

        self._logger.info(
            f"NfoParser.parse_full_movie: success title='{details.title_ru}', "
            f"kp_id={details.kinopoisk_id}, year={details.year}, "
            f"{len(details.ratings)} ratings, {len(details.cast)} cast"
        )
        return details

    def parse_full_tvshow(self, nfo_content: str) -> Optional[TVShowDetails]:
        self._logger.info("NfoParser.parse_full_tvshow: parsing full tvshow NFO")
        try:
            root = ET.fromstring(nfo_content)
        except ET.ParseError as e:
            self._logger.warning(f"NfoParser.parse_full_tvshow: XML parse error: {e}")
            return None

        title = self._text(root, "title")
        if not title:
            self._logger.warning("NfoParser.parse_full_tvshow: <title> missing")
            return None

        details = TVShowDetails(
            title_ru=title,
            title_original=self._text(root, "originaltitle"),
            year=self._int(root, "year"),
            plot=self._text(root, "plot"),
            tagline=self._text(root, "tagline"),
            runtime=self._int(root, "runtime"),
            mpaa=self._text(root, "mpaa"),
            genres=self._text_list(root, "genre"),
            countries=self._text_list(root, "country"),
            studios=self._text_list(root, "studio"),
            tags=self._text_list(root, "tag"),
        )

        plot_outline = self._text(root, "outline")
        if plot_outline:
            details.plot_outline = plot_outline
            self._logger.info("NfoParser.parse_full_tvshow: found <outline>")

        premiere_date = self._text(root, "premiered")
        if premiere_date:
            details.premiere_date = premiere_date
            self._logger.info(f"NfoParser.parse_full_tvshow: found <premiered>={premiere_date}")

        self._parse_uniqueids(root, details)
        details.ratings = self._parse_ratings(root)
        details.directors = self._parse_directors(root)
        details.writers = self._parse_writers(root)
        details.cast = self._parse_actors(root)
        details.artwork = self._parse_artwork(root)

        trailer_text = self._text(root, "trailer")
        if trailer_text:
            details.trailer_url = trailer_text
            self._logger.debug(f"NfoParser.parse_full_tvshow: trailer_url='{trailer_text}'")

        original_language = self._text(root, "language")
        if original_language:
            details.original_language = original_language
            self._logger.info(f"NfoParser.parse_full_tvshow: found <language>={original_language}")

        status = self._text(root, "status")
        if status:
            details.status = status
            self._logger.info(f"NfoParser.parse_full_tvshow: found <status>={status}")

        self._logger.info(
            f"NfoParser.parse_full_tvshow: success title='{details.title_ru}', "
            f"kp_id={details.kinopoisk_id}, year={details.year}, "
            f"{len(details.ratings)} ratings, {len(details.cast)} cast"
        )
        return details
