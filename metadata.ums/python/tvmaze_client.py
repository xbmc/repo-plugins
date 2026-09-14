from __future__ import annotations

import re
import threading
from typing import Any, Optional

from http_client import HttpClient, HttpError, RateLimiter
from models import SeasonArtInfo


_tvmaze_limiter = RateLimiter(2.0)

_show_cache: dict[str, int] = {}
_episodes_cache: dict[int, list[dict]] = {}
_tvmaze_cache_lock = threading.Lock()
_TVMAZE_CACHE_MAX_SHOWS = 20
_TVMAZE_CACHE_MAX_EPISODES = 10
_seasons_cache: dict[int, list[SeasonArtInfo]] = {}
_TVMAZE_CACHE_MAX_SEASONS = 10
_crew_cache: dict[int, list[dict]] = {}
_TVMAZE_CACHE_MAX_CREW = 50
_tvdb_cache: dict[str, Optional[int]] = {}
_TVMAZE_CACHE_MAX_TVDB = 20
_status_cache: dict[str, str] = {}
_TVMAZE_CACHE_MAX_STATUS = 20
_show_data_cache: dict[str, dict] = {}
_TVMAZE_CACHE_MAX_SHOW_DATA = 20

# Circuit breaker state (protected by _tvmaze_cache_lock)
_circuit_failures: int = 0
_circuit_open: bool = False
_CIRCUIT_BREAKER_THRESHOLD = 2

# Status codes that count as real failures for the circuit breaker
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

_TVMAZE_STATUS_MAP: dict[str, str] = {
    "Running": "Returning Series",
    "Ended": "Ended",
    "To Be Determined": "Returning Series",
    "In Development": "In Production",
}


class TvmazeClient:

    BASE_URL = "https://api.tvmaze.com"
    TIMEOUT = 5
    _HTML_TAG_RE = re.compile(r"<[^>]+>")

    def __init__(self, logger: Any = None) -> None:
        self._logger = logger
        self._http = HttpClient(
            base_url=self.BASE_URL,
            headers={"Accept": "application/json"},
            rate_limiter=_tvmaze_limiter,
            timeout=self.TIMEOUT,
            logger=logger,
        )

    # ------------------------------------------------------------------
    # Circuit breaker
    # ------------------------------------------------------------------

    def _is_circuit_open(self) -> bool:
        """Check if the circuit breaker is open (TVMaze calls disabled)."""
        global _circuit_open
        with _tvmaze_cache_lock:
            if _circuit_open:
                self._log_debug(
                    "TvmazeClient: circuit breaker is open, skipping TVMaze call"
                )
                return True
        return False

    def _record_failure(self) -> None:
        """Record a TVMaze HTTP failure; trip the breaker at threshold."""
        global _circuit_failures, _circuit_open
        with _tvmaze_cache_lock:
            _circuit_failures += 1
            if _circuit_failures >= _CIRCUIT_BREAKER_THRESHOLD and not _circuit_open:
                _circuit_open = True
                self._log_warning(
                    f"TvmazeClient: circuit breaker tripped after "
                    f"{_circuit_failures} consecutive failures, "
                    f"disabling TVMaze for this session"
                )

    def _record_success(self) -> None:
        """Reset the circuit breaker on a successful response."""
        global _circuit_failures, _circuit_open
        with _tvmaze_cache_lock:
            _circuit_failures = 0
            _circuit_open = False

    def _is_retryable_error(self, exc: Exception) -> bool:
        """Return True if the exception represents a real API failure.

        HttpError with 404 means the API is healthy but the resource
        was not found -- that is NOT a failure.  Only timeouts,
        connection errors, and retryable HTTP status codes count.
        """
        if isinstance(exc, HttpError):
            return exc.status_code in _RETRYABLE_STATUS_CODES
        # URLError, timeout, etc.
        return True

    # ------------------------------------------------------------------
    # Unified show-data accessor (T-02)
    # ------------------------------------------------------------------

    def _get_show_data(
        self, imdb_id: str, title_original: str = ""
    ) -> Optional[dict]:
        """Return full TVMaze show JSON, using _show_data_cache.

        Delegates to lookup_show / search_show which populate
        _show_data_cache as a side-effect.
        """
        # 1. Check cache by imdb_id
        if imdb_id:
            with _tvmaze_cache_lock:
                if imdb_id in _show_data_cache:
                    self._log_debug(
                        f"TvmazeClient._get_show_data: cache hit for imdb_id={imdb_id}"
                    )
                    return _show_data_cache[imdb_id]

        # 2. Check cache by title_original
        if title_original:
            with _tvmaze_cache_lock:
                if title_original in _show_data_cache:
                    self._log_debug(
                        f"TvmazeClient._get_show_data: cache hit for "
                        f"title='{title_original}'"
                    )
                    return _show_data_cache[title_original]

        # 3. Try IMDB lookup (populates _show_data_cache as side-effect)
        if imdb_id:
            self.lookup_show(imdb_id)
            with _tvmaze_cache_lock:
                if imdb_id in _show_data_cache:
                    return _show_data_cache[imdb_id]

        # 4. Fallback to title search
        if title_original:
            self.search_show(title_original)
            with _tvmaze_cache_lock:
                if title_original in _show_data_cache:
                    return _show_data_cache[title_original]

        return None

    def get_episode_plot(
        self,
        imdb_id: str,
        season: int,
        episode: int,
        title_original: str = "",
    ) -> Optional[str]:
        if not imdb_id and not title_original:
            self._log_debug(
                "TvmazeClient.get_episode_plot: no imdb_id or title_original, skipping"
            )
            return None

        self._log_info(
            f"TvmazeClient.get_episode_plot: "
            f"imdb_id={imdb_id}, S{season:02d}E{episode:02d}, "
            f"title_original='{title_original}'"
        )

        # Try IMDB lookup first, then name search as fallback
        show_id = None
        if imdb_id:
            show_id = self.lookup_show(imdb_id)
        if show_id is None and title_original:
            show_id = self.search_show(title_original)
        if show_id is None:
            return None

        episodes = self.get_episodes(show_id)
        if episodes is None:
            return None

        for ep in episodes:
            if ep.get("season") == season and ep.get("number") == episode:
                summary = ep.get("summary") or ""
                plot = self._strip_html(summary)
                if plot:
                    return plot
                self._log_debug(
                    f"TvmazeClient.get_episode_plot: empty summary for "
                    f"imdb_id={imdb_id}, S{season:02d}E{episode:02d}"
                )
                return None

        self._log_debug(
            f"TvmazeClient.get_episode_plot: episode not found for "
            f"imdb_id={imdb_id}, S{season:02d}E{episode:02d}"
        )
        return None

    def lookup_show(self, imdb_id: str) -> Optional[int]:
        with _tvmaze_cache_lock:
            if imdb_id in _show_cache:
                self._log_debug(
                    f"TvmazeClient.lookup_show: cache hit for imdb_id={imdb_id}"
                )
                return _show_cache[imdb_id]

        if self._is_circuit_open():
            return None

        self._log_info(
            f"TvmazeClient.lookup_show: looking up imdb_id={imdb_id}"
        )

        try:
            data = self._http.get_json("/lookup/shows", {"imdb": imdb_id})
        except HttpError as exc:
            if exc.status_code == 404:
                self._log_debug(
                    f"TvmazeClient.lookup_show: show not found for "
                    f"imdb_id={imdb_id}"
                )
                self._record_success()
                return None
            self._log_warning(
                f"TvmazeClient.lookup_show: HTTP error for "
                f"imdb_id={imdb_id}: {exc}"
            )
            if self._is_retryable_error(exc):
                self._record_failure()
            return None
        except Exception as exc:
            self._log_warning(
                f"TvmazeClient.lookup_show: unexpected error for "
                f"imdb_id={imdb_id}: {exc}"
            )
            self._record_failure()
            return None

        self._record_success()

        raw_id = data.get("id")
        if not raw_id:
            self._log_warning(
                f"TvmazeClient.lookup_show: no 'id' in response for "
                f"imdb_id={imdb_id}"
            )
            return None
        show_id = int(raw_id)

        with _tvmaze_cache_lock:
            if len(_show_cache) >= _TVMAZE_CACHE_MAX_SHOWS:
                oldest_key = next(iter(_show_cache))
                del _show_cache[oldest_key]
            _show_cache[imdb_id] = show_id
            # Cache full response for _get_show_data
            if len(_show_data_cache) >= _TVMAZE_CACHE_MAX_SHOW_DATA:
                oldest_key = next(iter(_show_data_cache))
                del _show_data_cache[oldest_key]
            _show_data_cache[imdb_id] = data

        self._log_info(
            f"TvmazeClient.lookup_show: success imdb_id={imdb_id} -> "
            f"show_id={show_id}"
        )
        return show_id

    def search_show(self, name: str) -> Optional[int]:
        """Find TVMaze show ID by name using singlesearch.

        Fallback when IMDB ID is not available from Kinopoisk.
        API: GET /singlesearch/shows?q={name}
        """
        with _tvmaze_cache_lock:
            if name in _show_cache:
                self._log_debug(
                    f"TvmazeClient.search_show: cache hit for name='{name}'"
                )
                return _show_cache[name]

        if self._is_circuit_open():
            return None

        self._log_info(
            f"TvmazeClient.search_show: searching for name='{name}'"
        )

        try:
            data = self._http.get_json("/singlesearch/shows", {"q": name})
        except HttpError as exc:
            if exc.status_code == 404:
                self._log_debug(
                    f"TvmazeClient.search_show: show not found for "
                    f"name='{name}'"
                )
                self._record_success()
                return None
            self._log_warning(
                f"TvmazeClient.search_show: HTTP error for "
                f"name='{name}': {exc}"
            )
            if self._is_retryable_error(exc):
                self._record_failure()
            return None
        except Exception as exc:
            self._log_warning(
                f"TvmazeClient.search_show: unexpected error for "
                f"name='{name}': {exc}"
            )
            self._record_failure()
            return None

        self._record_success()

        raw_id = data.get("id")
        if not raw_id:
            self._log_warning(
                f"TvmazeClient.search_show: no 'id' in response for "
                f"name='{name}'"
            )
            return None
        show_id = int(raw_id)

        with _tvmaze_cache_lock:
            if len(_show_cache) >= _TVMAZE_CACHE_MAX_SHOWS:
                oldest_key = next(iter(_show_cache))
                del _show_cache[oldest_key]
            _show_cache[name] = show_id
            # Cache full response for _get_show_data
            if len(_show_data_cache) >= _TVMAZE_CACHE_MAX_SHOW_DATA:
                oldest_key = next(iter(_show_data_cache))
                del _show_data_cache[oldest_key]
            _show_data_cache[name] = data

        self._log_info(
            f"TvmazeClient.search_show: success name='{name}' -> "
            f"show_id={show_id}"
        )
        return show_id

    def search_imdb_id(self, name: str) -> Optional[str]:
        if not name:
            return None

        if self._is_circuit_open():
            return None

        self._log_info(
            f"TvmazeClient.search_imdb_id: searching for name='{name}'"
        )

        try:
            data = self._http.get_json("/singlesearch/shows", {"q": name})
        except HttpError as exc:
            if exc.status_code == 404:
                self._log_debug(
                    f"TvmazeClient.search_imdb_id: show not found for "
                    f"name='{name}'"
                )
                self._record_success()
                return None
            self._log_warning(
                f"TvmazeClient.search_imdb_id: HTTP error for "
                f"name='{name}': {exc}"
            )
            if self._is_retryable_error(exc):
                self._record_failure()
            return None
        except Exception as exc:
            self._log_warning(
                f"TvmazeClient.search_imdb_id: unexpected error for "
                f"name='{name}': {exc}"
            )
            self._record_failure()
            return None

        self._record_success()

        externals = data.get("externals") or {}
        imdb_id = externals.get("imdb") or ""
        if not imdb_id:
            self._log_debug(
                f"TvmazeClient.search_imdb_id: no IMDB ID in response for "
                f"name='{name}'"
            )
            return None

        self._log_info(
            f"TvmazeClient.search_imdb_id: success name='{name}' -> "
            f"imdb_id={imdb_id}"
        )
        return imdb_id

    def get_show_status(self, imdb_id: str, title_original: str = "") -> str:
        """Resolve TV show status via TVMaze API.

        Returns Kodi-compatible status string or "" if not available.
        Uses _get_show_data to avoid duplicate HTTP calls.
        """
        if not imdb_id and not title_original:
            self._log_debug(
                "TvmazeClient.get_show_status: no imdb_id or title_original, skipping"
            )
            return ""

        cache_key = imdb_id if imdb_id else title_original

        with _tvmaze_cache_lock:
            if cache_key in _status_cache:
                cached = _status_cache[cache_key]
                self._log_debug(
                    f"TvmazeClient.get_show_status: cache hit for '{cache_key}': '{cached}'"
                )
                return cached

        self._log_info(
            f"TvmazeClient.get_show_status: resolving status for "
            f"imdb_id='{imdb_id}', title='{title_original}'"
        )

        data = self._get_show_data(imdb_id, title_original)

        if data is None:
            self._log_debug(
                f"TvmazeClient.get_show_status: show not found for "
                f"imdb_id='{imdb_id}', title='{title_original}'"
            )
            with _tvmaze_cache_lock:
                if len(_status_cache) >= _TVMAZE_CACHE_MAX_STATUS:
                    oldest_key = next(iter(_status_cache))
                    del _status_cache[oldest_key]
                _status_cache[cache_key] = ""
            return ""

        raw_status = data.get("status", "")
        if not raw_status:
            self._log_debug(
                "TvmazeClient.get_show_status: no status field in response"
            )
            result = ""
        elif raw_status in _TVMAZE_STATUS_MAP:
            result = _TVMAZE_STATUS_MAP[raw_status]
            self._log_info(
                f"TvmazeClient.get_show_status: '{raw_status}' -> '{result}'"
            )
        else:
            self._log_warning(
                f"TvmazeClient.get_show_status: unknown status '{raw_status}'"
            )
            result = ""

        with _tvmaze_cache_lock:
            if len(_status_cache) >= _TVMAZE_CACHE_MAX_STATUS:
                oldest_key = next(iter(_status_cache))
                del _status_cache[oldest_key]
            _status_cache[cache_key] = result

        return result

    def get_tvdb_id(self, imdb_id: str, title_original: str = "") -> Optional[int]:
        """Resolve TVDB ID via TVMaze lookup by IMDB ID, with title fallback.

        Uses _get_show_data to avoid duplicate HTTP calls.
        """
        if not imdb_id and not title_original:
            self._log_debug(
                "TvmazeClient.get_tvdb_id: no imdb_id or title_original, skipping"
            )
            return None

        cache_key = imdb_id if imdb_id else title_original

        with _tvmaze_cache_lock:
            if cache_key in _tvdb_cache:
                self._log_debug(
                    f"TvmazeClient.get_tvdb_id: cache hit for key='{cache_key}'"
                )
                return _tvdb_cache[cache_key]

        self._log_info(
            f"TvmazeClient.get_tvdb_id: resolving tvdb_id for imdb_id={imdb_id}"
        )

        data = self._get_show_data(imdb_id, title_original)

        tvdb_id: Optional[int] = None
        if data is not None:
            raw = data.get("externals", {}).get("thetvdb")
            if raw is not None:
                tvdb_id = int(raw)

        self._save_tvdb_cache(cache_key, tvdb_id)

        if tvdb_id is not None:
            self._log_info(
                f"TvmazeClient.get_tvdb_id: success imdb_id={imdb_id} -> tvdb_id={tvdb_id}"
            )
        else:
            self._log_info(
                f"TvmazeClient.get_tvdb_id: no TVDB ID found for imdb_id={imdb_id}"
            )

        return tvdb_id

    def _save_tvdb_cache(self, cache_key: str, tvdb_id: Optional[int]) -> None:
        with _tvmaze_cache_lock:
            if len(_tvdb_cache) >= _TVMAZE_CACHE_MAX_TVDB:
                oldest_key = next(iter(_tvdb_cache))
                del _tvdb_cache[oldest_key]
            _tvdb_cache[cache_key] = tvdb_id

    def get_episodes(self, show_id: int) -> Optional[list[dict]]:
        with _tvmaze_cache_lock:
            if show_id in _episodes_cache:
                self._log_debug(
                    f"TvmazeClient.get_episodes: cache hit for "
                    f"show_id={show_id}"
                )
                return _episodes_cache[show_id]

        if self._is_circuit_open():
            return None

        self._log_info(
            f"TvmazeClient.get_episodes: fetching episodes for "
            f"show_id={show_id}"
        )

        try:
            data = self._http.get_json(f"/shows/{show_id}/episodes")
        except HttpError as exc:
            self._log_warning(
                f"TvmazeClient.get_episodes: HTTP error for "
                f"show_id={show_id}: {exc}"
            )
            if self._is_retryable_error(exc):
                self._record_failure()
            else:
                self._record_success()
            return None
        except Exception as exc:
            self._log_warning(
                f"TvmazeClient.get_episodes: unexpected error for "
                f"show_id={show_id}: {exc}"
            )
            self._record_failure()
            return None

        self._record_success()

        if not isinstance(data, list):
            self._log_warning(
                f"TvmazeClient.get_episodes: unexpected response type "
                f"for show_id={show_id}: {type(data).__name__}"
            )
            return None

        with _tvmaze_cache_lock:
            if len(_episodes_cache) >= _TVMAZE_CACHE_MAX_EPISODES:
                oldest_key = next(iter(_episodes_cache))
                del _episodes_cache[oldest_key]
            _episodes_cache[show_id] = data

        self._log_info(
            f"TvmazeClient.get_episodes: success for show_id={show_id}, "
            f"{len(data)} episodes"
        )
        return data

    def get_seasons(self, show_id: int) -> Optional[list[SeasonArtInfo]]:
        with _tvmaze_cache_lock:
            if show_id in _seasons_cache:
                self._log_debug(
                    f"TvmazeClient.get_seasons: cache hit for show_id={show_id}"
                )
                return _seasons_cache[show_id]

        if self._is_circuit_open():
            return None

        self._log_info(
            f"TvmazeClient.get_seasons: fetching seasons for show_id={show_id}"
        )

        try:
            data = self._http.get_json(f"/shows/{show_id}/seasons")
        except HttpError as exc:
            self._log_warning(
                f"TvmazeClient.get_seasons: HTTP error for show_id={show_id}: {exc}"
            )
            if self._is_retryable_error(exc):
                self._record_failure()
            else:
                self._record_success()
            return None
        except Exception as exc:
            self._log_warning(
                f"TvmazeClient.get_seasons: unexpected error for show_id={show_id}: {exc}"
            )
            self._record_failure()
            return None

        self._record_success()

        if not isinstance(data, list):
            self._log_warning(
                f"TvmazeClient.get_seasons: unexpected response type "
                f"for show_id={show_id}: {type(data).__name__}"
            )
            return None

        result: list[SeasonArtInfo] = []
        for item in data:
            num = item.get("number")
            if num is None:
                self._log_warning(
                    f"TvmazeClient.get_seasons: skipping season with "
                    f"number=None in show_id={show_id}"
                )
                continue
            image = item.get("image") or {}
            result.append(SeasonArtInfo(
                number=int(num),
                name=item.get("name") or "",
                poster_url=image.get("original", ""),
                poster_preview_url=image.get("medium", ""),
            ))

        with _tvmaze_cache_lock:
            if len(_seasons_cache) >= _TVMAZE_CACHE_MAX_SEASONS:
                oldest_key = next(iter(_seasons_cache))
                del _seasons_cache[oldest_key]
            _seasons_cache[show_id] = result

        self._log_info(
            f"TvmazeClient.get_seasons: success for show_id={show_id}, "
            f"{len(result)} seasons"
        )
        return result

    def get_episode_crew(
        self,
        imdb_id: str,
        season: int,
        episode: int,
        title_original: str = "",
    ) -> tuple[list[str], list[str]]:
        if not imdb_id and not title_original:
            self._log_debug(
                "TvmazeClient.get_episode_crew: no imdb_id or title_original, skipping"
            )
            return ([], [])

        self._log_info(
            f"TvmazeClient.get_episode_crew: "
            f"imdb_id={imdb_id}, S{season:02d}E{episode:02d}, "
            f"title_original='{title_original}'"
        )

        show_id = None
        if imdb_id:
            show_id = self.lookup_show(imdb_id)
        if show_id is None and title_original:
            show_id = self.search_show(title_original)
        if show_id is None:
            return ([], [])

        episodes = self.get_episodes(show_id)
        if episodes is None:
            return ([], [])

        episode_id = None
        for ep in episodes:
            if ep.get("season") == season and ep.get("number") == episode:
                episode_id = ep.get("id")
                break

        if episode_id is None:
            self._log_debug(
                f"TvmazeClient.get_episode_crew: episode not found for "
                f"S{season:02d}E{episode:02d}"
            )
            return ([], [])

        with _tvmaze_cache_lock:
            if episode_id in _crew_cache:
                self._log_debug(
                    f"TvmazeClient.get_episode_crew: cache hit for episode_id={episode_id}"
                )
                crew_data = _crew_cache[episode_id]
                return self._parse_crew(crew_data, season, episode)

        if self._is_circuit_open():
            return ([], [])

        try:
            crew_data = self._http.get_json(f"/episodes/{episode_id}/guestcrew")
        except HttpError as exc:
            if exc.status_code == 404:
                self._log_debug(
                    f"TvmazeClient.get_episode_crew: no crew for episode_id={episode_id}"
                )
                self._record_success()
            else:
                self._log_warning(
                    f"TvmazeClient.get_episode_crew: HTTP error for "
                    f"episode_id={episode_id}: {exc}"
                )
                if self._is_retryable_error(exc):
                    self._record_failure()
            return ([], [])
        except Exception as exc:
            self._log_warning(
                f"TvmazeClient.get_episode_crew: unexpected error for "
                f"episode_id={episode_id}: {exc}"
            )
            self._record_failure()
            return ([], [])

        self._record_success()

        if not isinstance(crew_data, list):
            self._log_warning(
                f"TvmazeClient.get_episode_crew: unexpected response type "
                f"for episode_id={episode_id}: {type(crew_data).__name__}"
            )
            return ([], [])

        with _tvmaze_cache_lock:
            if len(_crew_cache) >= _TVMAZE_CACHE_MAX_CREW:
                oldest_key = next(iter(_crew_cache))
                del _crew_cache[oldest_key]
            _crew_cache[episode_id] = crew_data

        return self._parse_crew(crew_data, season, episode)

    def _parse_crew(
        self, crew_data: list[dict], season: int, episode: int
    ) -> tuple[list[str], list[str]]:
        directors: list[str] = []
        writers: list[str] = []
        for entry in crew_data:
            crew_type = entry.get("guestCrewType") or entry.get("type", "")
            person = entry.get("person") or {}
            name = person.get("name", "")
            if not name:
                self._log_warning(
                    f"TvmazeClient.get_episode_crew: crew entry without person.name "
                    f"for S{season:02d}E{episode:02d}, type={crew_type}"
                )
                continue
            if crew_type == "Director":
                directors.append(name)
            elif crew_type == "Writer":
                writers.append(name)

        if not directors and not writers:
            self._log_info(
                f"TvmazeClient.get_episode_crew: no crew data for "
                f"S{season:02d}E{episode:02d}"
            )
        else:
            self._log_info(
                f"TvmazeClient.get_episode_crew: S{season:02d}E{episode:02d} "
                f"directors={len(directors)}, writers={len(writers)}"
            )
        return (directors, writers)

    def get_episode_image(
        self,
        imdb_id: str,
        season: int,
        episode: int,
        title_original: str = "",
    ) -> tuple[str, str]:
        """Return (original_url, medium_url) for episode thumbnail.

        Uses _episodes_cache — no extra HTTP if episodes were already fetched
        via get_episode_plot or get_episode_crew.
        Returns ("", "") if image is unavailable.
        """
        if not imdb_id and not title_original:
            self._log_debug(
                "TvmazeClient.get_episode_image: no imdb_id or title_original, skipping"
            )
            return ("", "")

        self._log_info(
            f"TvmazeClient.get_episode_image: "
            f"imdb_id={imdb_id}, S{season:02d}E{episode:02d}"
        )

        show_id = None
        if imdb_id:
            show_id = self.lookup_show(imdb_id)
        if show_id is None and title_original:
            show_id = self.search_show(title_original)
        if show_id is None:
            return ("", "")

        episodes = self.get_episodes(show_id)
        if episodes is None:
            return ("", "")

        for ep in episodes:
            if ep.get("season") == season and ep.get("number") == episode:
                image = ep.get("image")
                if not image:
                    self._log_debug(
                        f"TvmazeClient.get_episode_image: image=null for "
                        f"S{season:02d}E{episode:02d}"
                    )
                    return ("", "")
                original = image.get("original", "")
                medium = image.get("medium", "")
                original = original or medium
                medium = medium or original
                self._log_info(
                    f"TvmazeClient.get_episode_image: found image for "
                    f"S{season:02d}E{episode:02d}"
                )
                return (original, medium)

        self._log_debug(
            f"TvmazeClient.get_episode_image: episode not found for "
            f"S{season:02d}E{episode:02d}"
        )
        return ("", "")

    def _strip_html(self, html: str) -> str:
        if not html:
            return ""
        text = self._HTML_TAG_RE.sub("", html)
        text = " ".join(text.split())
        return text

    def _log_debug(self, message: str) -> None:
        if self._logger is not None:
            self._logger.debug(message)

    def _log_info(self, message: str) -> None:
        if self._logger is not None:
            self._logger.info(message)

    def _log_warning(self, message: str) -> None:
        if self._logger is not None:
            self._logger.warning(message)
