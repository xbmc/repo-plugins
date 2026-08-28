from __future__ import annotations

import threading
from typing import Any, Optional

from http_client import HttpClient, RateLimiter


_fanart_limiter = RateLimiter(1.0)
_fanart_cache: dict[str, Any] = {}
_fanart_cache_lock = threading.Lock()
_FANART_CACHE_MAX = 20

_MOVIE_MAPPING: list[tuple[str, str, list[str]]] = [
    ("clearlogo", "hdmovielogo", ["movielogo"]),
    ("clearart", "hdmovieclearart", ["movieart"]),
    ("banner", "moviebanner", []),
    ("landscape", "moviethumb", []),
    ("discart", "moviedisc", []),
]

_TV_SHOW_MAPPING: list[tuple[str, str, list[str]]] = [
    ("clearlogo", "hdtvlogo", ["clearlogo"]),
    ("clearart", "hdclearart", ["clearart"]),
    ("banner", "tvbanner", []),
    ("landscape", "tvthumb", []),
    ("characterart", "characterart", []),
]

_TV_SEASON_MAPPING: list[tuple[str, str]] = [
    ("banner", "seasonbanner"),
    ("landscape", "seasonthumb"),
]


class FanartClient:
    """FanArt.tv API v3 client for fetching additional artwork (clearlogo, clearart, etc.).

    Provides movie and TV show artwork that complements KP posters/fanart.
    All errors are silenced -- this is optional enrichment data.
    """

    BASE_URL = "https://webservice.fanart.tv"
    TIMEOUT = 5

    def __init__(self, api_key: str, logger: Any = None) -> None:
        self._api_key = api_key
        self._logger = logger

        self._http = HttpClient(
            base_url=self.BASE_URL,
            rate_limiter=_fanart_limiter,
            timeout=self.TIMEOUT,
            logger=logger,
        )

    def get_movie_art(self, imdb_id: str) -> dict[str, str]:
        """Fetch movie artwork from FanArt.tv by IMDb ID.

        Returns a dict mapping Kodi art types to URLs (e.g. {"clearlogo": "https://..."}).
        Never raises exceptions -- returns empty dict on any failure.

        Args:
            imdb_id: IMDb identifier (e.g. "tt0120737").

        Returns:
            Dict of kodi_type -> artwork URL.
        """
        if not imdb_id:
            self._log_debug("FanartClient.get_movie_art: empty imdb_id, skipping")
            return {}

        path = f"/v3/movies/{imdb_id}"

        try:
            data = self._get_cached_or_fetch(path)
        except Exception as e:
            self._log_warning(f"FanartClient.get_movie_art: error for imdb_id={imdb_id}: {e}")
            return {}

        if data is None:
            return {}

        result: dict[str, str] = {}

        for kodi_type, primary_key, fallback_keys in _MOVIE_MAPPING:
            url = self._resolve_art(data, primary_key, fallback_keys)
            if url:
                result[kodi_type] = url

        self._log_info(
            f"FanartClient.get_movie_art: {len(result)} art types for imdb_id={imdb_id}"
        )
        return result

    def get_tv_art(
        self, tvdb_id: int
    ) -> tuple[dict[str, str], dict[int, dict[str, str]]]:
        """Fetch TV show and season artwork from FanArt.tv by TVDB ID.

        Returns a tuple of (show_art, season_art) where:
        - show_art: dict of kodi_type -> URL for the show level
        - season_art: dict of season_number -> {kodi_type: URL} for per-season art

        Never raises exceptions -- returns empty structures on any failure.

        Args:
            tvdb_id: TVDB identifier (e.g. 121361).

        Returns:
            Tuple of (show_art dict, season_art dict).
        """
        if not tvdb_id:
            self._log_debug("FanartClient.get_tv_art: empty tvdb_id, skipping")
            return {}, {}

        path = f"/v3/tv/{tvdb_id}"

        try:
            data = self._get_cached_or_fetch(path)
        except Exception as e:
            self._log_warning(f"FanartClient.get_tv_art: error for tvdb_id={tvdb_id}: {e}")
            return {}, {}

        if data is None:
            return {}, {}

        # Show-level artwork
        show_art: dict[str, str] = {}

        for kodi_type, primary_key, fallback_keys in _TV_SHOW_MAPPING:
            url = self._resolve_art(data, primary_key, fallback_keys)
            if url:
                show_art[kodi_type] = url

        # Season-level artwork
        season_art: dict[int, dict[str, str]] = {}

        for kodi_type, fanart_key in _TV_SEASON_MAPPING:
            items = data.get(fanart_key, [])
            if not items:
                continue

            # Group items by season number
            by_season: dict[int, list[dict]] = {}
            for item in items:
                season_raw = item.get("season", "")
                if season_raw == "all" or season_raw == "":
                    continue
                try:
                    season_num = int(season_raw)
                except (ValueError, TypeError):
                    continue
                by_season.setdefault(season_num, []).append(item)

            for season_num, season_items in by_season.items():
                url = self._pick_best(season_items)
                if url:
                    if season_num not in season_art:
                        season_art[season_num] = {}
                    season_art[season_num][kodi_type] = url

        self._log_info(
            f"FanartClient.get_tv_art: {len(show_art)} show types + "
            f"{len(season_art)} seasons for tvdb_id={tvdb_id}"
        )
        return show_art, season_art

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_cached_or_fetch(self, path: str) -> Optional[dict]:
        """Check cache for raw API response, fetch from HTTP if missing.

        Stores raw API response in cache for reuse. FIFO eviction when
        cache exceeds _FANART_CACHE_MAX entries.

        Args:
            path: API path (e.g. "/v3/movies/tt0120737").

        Returns:
            Raw API response dict or None on failure.

        Raises:
            Exception: On HTTP or unexpected errors (caught by callers).
        """
        with _fanart_cache_lock:
            if path in _fanart_cache:
                self._log_debug(f"FanartClient._get_cached_or_fetch: cache hit for path={path}")
                return _fanart_cache[path]

        data = self._http.get_json(path, {"api_key": self._api_key})

        with _fanart_cache_lock:
            if len(_fanart_cache) >= _FANART_CACHE_MAX:
                oldest_key = next(iter(_fanart_cache))
                del _fanart_cache[oldest_key]
            _fanart_cache[path] = data

        return data

    def _resolve_art(
        self, data: dict, primary_key: str, fallback_keys: list[str]
    ) -> Optional[str]:
        """Try primary key, then fallback keys, return best URL or None."""
        items = data.get(primary_key, [])
        if items:
            url = self._pick_best(items)
            if url:
                return url

        for key in fallback_keys:
            items = data.get(key, [])
            if items:
                url = self._pick_best(items)
                if url:
                    return url

        return None

    def _pick_best(self, items: list[dict]) -> Optional[str]:
        """Pick the best artwork URL from a list of FanArt.tv items.

        Priority: items with "en" language first, then empty language,
        then any other. Within each language group, sort by likes descending.

        Args:
            items: List of FanArt.tv artwork items (each has "url", "lang", "likes").

        Returns:
            URL string of the best item, or None if no valid items.
        """
        if not items:
            return None

        valid = [item for item in items if item.get("url")]
        if not valid:
            return None

        def _sort_key(item: dict) -> tuple[int, int]:
            lang = item.get("lang", "")
            if lang == "en":
                lang_priority = 0
            elif lang == "":
                lang_priority = 1
            else:
                lang_priority = 2

            try:
                likes = int(item.get("likes", "0"))
            except (ValueError, TypeError):
                likes = 0

            return (lang_priority, -likes)

        valid.sort(key=_sort_key)
        return valid[0]["url"]

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def _log_info(self, message: str) -> None:
        if self._logger is not None:
            self._logger.info(message)

    def _log_debug(self, message: str) -> None:
        if self._logger is not None:
            self._logger.debug(message)

    def _log_warning(self, message: str) -> None:
        if self._logger is not None:
            self._logger.warning(message)
