from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ProfessionType(Enum):
    ACTOR = "ACTOR"
    DIRECTOR = "DIRECTOR"
    WRITER = "WRITER"
    PRODUCER = "PRODUCER"
    COMPOSER = "COMPOSER"
    OPERATOR = "OPERATOR"
    EDITOR = "EDITOR"
    DESIGN = "DESIGN"
    UNKNOWN = "UNKNOWN"


class ArtworkType(Enum):
    POSTER = "poster"
    FANART = "fanart"
    THUMB = "thumb"
    BANNER = "banner"
    LANDSCAPE = "landscape"
    CLEARLOGO = "clearlogo"
    CLEARART = "clearart"
    ACTOR_THUMB = "actor_thumb"


class DataSource(Enum):
    KINOPOISK = "kinopoisk"
    IMDB = "imdb"
    ROTTEN_TOMATOES = "rottentomatoes"
    METACRITIC = "metacritic"


@dataclass
class Rating:
    source: DataSource
    value: float
    votes: int = 0


@dataclass
class Person:
    name_ru: str
    name_en: str = ""
    role: str = ""
    profession: ProfessionType = ProfessionType.UNKNOWN
    photo_url: str = ""
    order: int = 0
    source_id: int = 0

    def display_name(self, lang: str = "ru") -> str:
        if lang == "en" and self.name_en:
            return self.name_en
        return self.name_ru


@dataclass
class Artwork:
    url: str
    preview_url: str = ""
    artwork_type: ArtworkType = ArtworkType.POSTER
    source: DataSource = DataSource.KINOPOISK
    language: str = ""
    width: int = 0
    height: int = 0


@dataclass
class MovieSearchResult:
    title_ru: str
    title_original: str = ""
    year: int = 0
    kinopoisk_id: int = 0
    imdb_id: str = ""
    poster_url: str = ""
    rating: float = 0.0
    source: DataSource = DataSource.KINOPOISK


@dataclass
class MovieDetails:
    kinopoisk_id: int = 0
    imdb_id: str = ""
    title_ru: str = ""
    title_original: str = ""
    tagline: str = ""
    year: int = 0
    plot: str = ""
    runtime: int = 0
    mpaa: str = ""
    genres: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    studios: list[str] = field(default_factory=list)
    ratings: list[Rating] = field(default_factory=list)
    directors: list[Person] = field(default_factory=list)
    writers: list[Person] = field(default_factory=list)
    cast: list[Person] = field(default_factory=list)
    artwork: list[Artwork] = field(default_factory=list)
    set_name: str = ""
    tags: list[str] = field(default_factory=list)
    trailer_url: str = ""
    premiere_date: str = ""
    plot_outline: str = ""
    original_language: str = ""


class ContentType(Enum):
    FILM = "FILM"
    TV_SERIES = "TV_SERIES"
    MINI_SERIES = "MINI_SERIES"
    TV_SHOW = "TV_SHOW"
    VIDEO = "VIDEO"
    UNKNOWN = "UNKNOWN"


@dataclass
class Episode:
    season_number: int = 0
    episode_number: int = 0
    title_ru: str = ""
    title_en: str = ""
    synopsis: str = ""
    release_date: str = ""
    rating: float = 0.0
    directors: list[str] = field(default_factory=list)
    writers: list[str] = field(default_factory=list)


@dataclass
class Season:
    number: int = 0
    episodes: list[Episode] = field(default_factory=list)


@dataclass
class SeasonArtInfo:
    number: int = 0
    name: str = ""
    poster_url: str = ""
    poster_preview_url: str = ""


@dataclass
class TVShowSearchResult:
    title_ru: str
    title_original: str = ""
    year: int = 0
    kinopoisk_id: int = 0
    imdb_id: str = ""
    poster_url: str = ""
    rating: float = 0.0
    content_type: ContentType = ContentType.TV_SERIES
    source: DataSource = DataSource.KINOPOISK


@dataclass
class TVShowDetails:
    kinopoisk_id: int = 0
    imdb_id: str = ""
    title_ru: str = ""
    title_original: str = ""
    tagline: str = ""
    year: int = 0
    plot: str = ""
    runtime: int = 0
    mpaa: str = ""
    genres: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    studios: list[str] = field(default_factory=list)
    ratings: list[Rating] = field(default_factory=list)
    directors: list[Person] = field(default_factory=list)
    writers: list[Person] = field(default_factory=list)
    cast: list[Person] = field(default_factory=list)
    artwork: list[Artwork] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    is_miniseries: bool = False
    status: str = ""
    trailer_url: str = ""
    premiere_date: str = ""
    plot_outline: str = ""
    original_language: str = ""
