from __future__ import annotations

import xbmcaddon
from models import DataSource


class SettingsManager:

    _RATING_MAP = {
        0: DataSource.KINOPOISK,
        1: DataSource.IMDB,
    }

    _GENRE_LANGUAGE_MAP = {
        0: "ru",
        1: "en",
    }

    def __init__(self, addon=None):
        self._addon = addon or xbmcaddon.Addon()

    @property
    def kinopoisk_api_key(self) -> str:
        return self._addon.getSetting("kinopoisk_api_key").strip()

    @property
    def omdb_api_key(self) -> str:
        return self._addon.getSetting("omdb_api_key").strip()

    @property
    def show_ratings_in_plot(self) -> bool:
        return self._addon.getSettingBool("show_ratings_in_plot")

    @property
    def use_tvmaze(self) -> bool:
        return self._addon.getSettingBool("use_tvmaze")

    @property
    def use_season_art(self) -> bool:
        return self._addon.getSettingBool("use_season_art")

    @property
    def preferred_rating_source(self) -> DataSource:
        value = self._addon.getSettingInt("preferred_rating")
        return self._RATING_MAP.get(value, DataSource.KINOPOISK)

    @property
    def fetch_actor_photos(self) -> bool:
        return self._addon.getSettingBool("fetch_actor_photos")

    @property
    def auto_select_exact_match(self) -> bool:
        return self._addon.getSettingBool("auto_select_exact_match")

    @property
    def enable_collections(self) -> bool:
        return self._addon.getSettingBool("enable_collections")

    @property
    def enable_dual_search(self) -> bool:
        return self._addon.getSettingBool("enable_dual_search")

    @property
    def enable_award_tags(self) -> bool:
        return self._addon.getSettingBool("enable_award_tags")

    @property
    def debug_logging(self) -> bool:
        return self._addon.getSettingBool("debug_logging")

    @property
    def genre_language(self) -> str:
        value = self._addon.getSettingInt("genre_language")
        return self._GENRE_LANGUAGE_MAP.get(value, "ru")

    @property
    def actor_name_language(self) -> str:
        value = self._addon.getSettingInt("actor_name_language")
        return self._GENRE_LANGUAGE_MAP.get(value, "ru")

    @property
    def clear_cache(self) -> bool:
        return self._addon.getSettingBool("clear_cache")

    def set_clear_cache(self, value: bool) -> None:
        self._addon.setSettingBool("clear_cache", value)

    @property
    def enable_nfo_export(self) -> bool:
        return self._addon.getSettingBool("enable_nfo_export")

    @property
    def nfo_overwrite(self) -> bool:
        return self._addon.getSettingBool("nfo_overwrite")

    @property
    def enable_duplicate_detection(self) -> bool:
        return self._addon.getSettingBool("enable_duplicate_detection")

    @property
    def enable_trailers(self) -> bool:
        return self._addon.getSettingBool("enable_trailers")

    @property
    def use_wikidata_fallback(self) -> bool:
        return self._addon.getSettingBool("use_wikidata_fallback")

    @property
    def use_fanart(self) -> bool:
        return self._addon.getSettingBool("use_fanart")

    @property
    def fanart_api_key(self) -> str:
        return self._addon.getSetting("fanart_api_key").strip()

    def validate(self) -> list[str]:
        errors = []
        if not self.kinopoisk_api_key:
            errors.append("Kinopoisk API key is not configured")
        return errors
