from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class OmdbRatings:
    """Ratings fetched from OMDb API."""

    imdb_rating: str       # e.g. "9.3"
    imdb_votes: str        # e.g. "2,700,000"
    rotten_tomatoes: str   # e.g. "91%" or "" if not available
    metacritic: str        # e.g. "82" or "" if not available
    awards: str = ""


def parse_rt_rating(raw: str, logger: Any = None) -> Optional[float]:
    """Parse Rotten Tomatoes rating: '91%' -> 91.0. Returns None on failure."""
    if not raw:
        return None
    try:
        cleaned = raw.strip().rstrip("%")
        value = float(cleaned)
        if logger:
            logger.debug(f"parse_rt_rating: '{raw}' -> {value}")
        return value
    except (ValueError, TypeError):
        if logger:
            logger.debug(f"parse_rt_rating: failed to parse '{raw}', skipping")
        return None


def parse_mc_rating(raw: str, logger: Any = None) -> Optional[float]:
    """Parse Metacritic rating: '82' -> 82.0. Returns None on failure."""
    if not raw:
        return None
    try:
        value = float(raw.strip())
        if logger:
            logger.debug(f"parse_mc_rating: '{raw}' -> {value}")
        return value
    except (ValueError, TypeError):
        if logger:
            logger.debug(f"parse_mc_rating: failed to parse '{raw}', skipping")
        return None


_AWARD_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"\bOscar", re.IGNORECASE),
        "Оскар",
        "Номинант Оскара",
    ),
    (
        re.compile(r"\bGolden Globe", re.IGNORECASE),
        "Золотой глобус",
        "Номинант Золотого глобуса",
    ),
    (
        re.compile(r"\b(?:Primetime )?Emmy", re.IGNORECASE),
        "Эмми",
        "Номинант Эмми",
    ),
    (
        re.compile(r"\bBAFTA", re.IGNORECASE),
        "BAFTA",
        "Номинант BAFTA",
    ),
    (
        re.compile(r"\b(?:Cannes|Palme d'Or)", re.IGNORECASE),
        "Канны",
        "Номинант Канн",
    ),
]


def parse_award_tags(awards_text: str, logger: Any = None) -> list[str]:
    """Parse OMDb Awards text and return list of Russian award tags.

    Detects major awards (Oscar, Golden Globe, Emmy, BAFTA, Cannes)
    and returns a tag indicating won vs nominated for each.

    Args:
        awards_text: Raw Awards string from OMDb (e.g. "Won 1 Oscar. 3 nominations.").
        logger: Optional logger instance.

    Returns:
        List of Russian award tag strings.
    """
    if not awards_text or awards_text.strip() == "N/A":
        if logger:
            logger.debug("parse_award_tags: empty or N/A awards text, returning []")
        return []

    tags: list[str] = []

    for pattern, tag_won, tag_nominated in _AWARD_PATTERNS:
        if not pattern.search(awards_text):
            continue

        won_match = re.search(
            r"\bWon\b[^.]*\b" + pattern.pattern.lstrip(r"\b"),
            awards_text,
            re.IGNORECASE,
        )
        if won_match:
            tags.append(tag_won)
            if logger:
                logger.debug(
                    f"parse_award_tags: found WON '{tag_won}' in '{awards_text}'"
                )
        else:
            tags.append(tag_nominated)
            if logger:
                logger.debug(
                    f"parse_award_tags: found NOMINATED '{tag_nominated}' "
                    f"in '{awards_text}'"
                )

    if logger:
        if tags:
            logger.info(f"parse_award_tags: awards='{awards_text}' -> tags={tags}")
        else:
            logger.info(f"parse_award_tags: awards='{awards_text}' -> no award tags")

    return tags


class OmdbClient:
    """Standalone OMDb API client for fetching IMDB and Rotten Tomatoes ratings.

    Uses short timeouts and minimal retries because OMDb is accessed via VPN
    which may be unstable. All failures are suppressed -- this is optional
    enrichment data, so callers should never see exceptions from this client.
    """

    TIMEOUT = 3   # seconds -- short due to VPN instability
    MAX_RETRIES = 1  # only 1 retry; if VPN is down, waiting won't help
    BASE_URL = "https://www.omdbapi.com/"

    def __init__(self, api_key: str, logger: Any = None) -> None:
        self._api_key = api_key
        self._logger = logger

    def get_ratings(self, imdb_id: str) -> Optional[OmdbRatings]:
        """Fetch ratings from OMDb by IMDB ID.

        Returns OmdbRatings on success, None on any failure.
        Never raises exceptions to callers.
        Backward compatible: delegates to fetch_ratings_raw + parse_ratings.

        Args:
            imdb_id: IMDB identifier (e.g. "tt0111161").

        Returns:
            OmdbRatings dataclass or None.
        """
        raw = self.fetch_ratings_raw(imdb_id)
        if raw is None:
            return None
        return self.parse_ratings(raw, imdb_id)

    def fetch_ratings_raw(self, imdb_id: str) -> Optional[dict]:
        """Fetch raw OMDb JSON response for ratings.

        Returns the parsed JSON dict on success, None on any failure.
        Never raises exceptions to callers.

        Args:
            imdb_id: IMDB identifier (e.g. "tt0111161").

        Returns:
            Raw OMDb response dict or None.
        """
        if not imdb_id or not imdb_id.strip():
            self._log_warning(
                "OmdbClient.fetch_ratings_raw: empty imdb_id, skipping"
            )
            return None

        self._log_info(
            f"OmdbClient.fetch_ratings_raw: looking up imdb_id={imdb_id}"
        )

        for attempt in range(1, self.MAX_RETRIES + 2):  # 1 initial + MAX_RETRIES retries
            try:
                data = self._fetch_json(imdb_id, attempt)
                return data  # may be None if Response != True
            except _RetryableError:
                if attempt <= self.MAX_RETRIES:
                    self._log_warning(
                        f"OmdbClient.fetch_ratings_raw: attempt {attempt} failed for "
                        f"imdb_id={imdb_id}, retrying"
                    )
                    continue
                self._log_warning(
                    f"OmdbClient.fetch_ratings_raw: all attempts exhausted for "
                    f"imdb_id={imdb_id}"
                )
                return None

        return None  # pragma: no cover -- defensive fallback

    def parse_ratings(self, data: dict, imdb_id: str) -> OmdbRatings:
        """Parse raw OMDb dict into OmdbRatings.

        Public API for cache integration. Delegates to internal _parse_ratings.

        Args:
            data: Raw OMDb response dict (must have Response=True).
            imdb_id: IMDB identifier for logging.

        Returns:
            OmdbRatings dataclass.
        """
        return self._parse_ratings(data, imdb_id)

    def _fetch_json(self, imdb_id: str, attempt: int) -> Optional[dict]:
        """Execute a single HTTP request to OMDb.

        Returns raw dict on success, None on API error (Response=False).
        Raises _RetryableError on network/timeout failures.
        """
        params = {
            "apikey": self._api_key,
            "i": imdb_id,
            "type": "movie",
        }
        url = self.BASE_URL + "?" + urllib.parse.urlencode(params)

        self._log_debug(
            f"OmdbClient._fetch_json: GET {self._sanitize_url(url)} "
            f"(attempt {attempt})"
        )

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            self._log_warning(
                f"OmdbClient._fetch_json: HTTP {exc.code} for imdb_id={imdb_id}"
            )
            raise _RetryableError() from exc
        except urllib.error.URLError as exc:
            self._log_warning(
                f"OmdbClient._fetch_json: URLError for imdb_id={imdb_id}: {exc.reason}"
            )
            raise _RetryableError() from exc
        except Exception as exc:
            self._log_warning(
                f"OmdbClient._fetch_json: unexpected error for imdb_id={imdb_id}: {exc}"
            )
            raise _RetryableError() from exc

        try:
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError) as exc:
            self._log_warning(
                f"OmdbClient._fetch_json: invalid JSON for imdb_id={imdb_id}: {exc}"
            )
            return None

        if data.get("Response") != "True":
            error_msg = data.get("Error", "Unknown error")
            self._log_warning(
                f"OmdbClient._fetch_json: OMDb error for imdb_id={imdb_id}: {error_msg}"
            )
            return None

        return data

    def _parse_ratings(self, data: dict, imdb_id: str) -> OmdbRatings:
        """Extract ratings from OMDb response data."""
        imdb_rating = data.get("imdbRating", "N/A") or "N/A"
        imdb_votes = data.get("imdbVotes", "N/A") or "N/A"

        rotten_tomatoes = ""
        metacritic = ""

        for rating_entry in data.get("Ratings", []):
            source = rating_entry.get("Source", "")
            value = rating_entry.get("Value", "")

            if source == "Rotten Tomatoes":
                rotten_tomatoes = value
            elif source == "Metacritic":
                # OMDb returns "82/100", extract just the number
                metacritic = value.split("/")[0] if "/" in value else value

        awards_raw = data.get("Awards", "") or ""
        if awards_raw == "N/A":
            awards_raw = ""

        result = OmdbRatings(
            imdb_rating=imdb_rating,
            imdb_votes=imdb_votes,
            rotten_tomatoes=rotten_tomatoes,
            metacritic=metacritic,
            awards=awards_raw,
        )

        self._log_info(
            f"OmdbClient.get_ratings: success for imdb_id={imdb_id} -- "
            f"IMDB={imdb_rating}, RT={rotten_tomatoes or 'N/A'}, "
            f"MC={metacritic or 'N/A'}, Awards={awards_raw or 'N/A'}"
        )
        return result

    def get_episode_rating(
        self, imdb_id: str, season: int, episode: int
    ) -> Optional[tuple[float, int]]:
        """Fetch individual episode rating from OMDb by IMDB ID, season, episode.

        Returns (rating, votes) tuple on success, None on any failure.
        Never raises exceptions to callers.

        Args:
            imdb_id: IMDB identifier of the series (e.g. "tt0903747").
            season: Season number (1-based).
            episode: Episode number (1-based).

        Returns:
            Episode rating and votes as tuple (e.g. (9.8, 1234)) or None.
        """
        if not imdb_id or not imdb_id.strip():
            self._log_warning(
                "OmdbClient.get_episode_rating: empty imdb_id, skipping"
            )
            return None

        self._log_info(
            f"OmdbClient.get_episode_rating: "
            f"imdb_id={imdb_id}, S{season:02d}E{episode:02d}"
        )

        for attempt in range(1, self.MAX_RETRIES + 2):
            try:
                result = self._fetch_episode(imdb_id, season, episode, attempt)
                return result
            except _RetryableError:
                if attempt <= self.MAX_RETRIES:
                    self._log_warning(
                        f"OmdbClient.get_episode_rating: attempt {attempt} "
                        f"failed, retrying"
                    )
                    continue
                self._log_warning(
                    f"OmdbClient.get_episode_rating: all attempts exhausted "
                    f"for {imdb_id} S{season:02d}E{episode:02d}"
                )
                return None

        return None  # pragma: no cover -- defensive fallback

    def _fetch_episode(
        self, imdb_id: str, season: int, episode: int, attempt: int
    ) -> Optional[tuple[float, int]]:
        """Execute a single HTTP request to OMDb for episode rating.

        Returns (rating, votes) tuple on success, None on API error
        (Response=False) or missing rating.
        Raises _RetryableError on network/timeout failures.
        """
        params = {
            "apikey": self._api_key,
            "i": imdb_id,
            "Season": str(season),
            "Episode": str(episode),
        }
        url = self.BASE_URL + "?" + urllib.parse.urlencode(params)

        self._log_debug(
            f"OmdbClient._fetch_episode: GET {self._sanitize_url(url)} "
            f"(attempt {attempt})"
        )

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            self._log_warning(
                f"OmdbClient._fetch_episode: HTTP {exc.code} for "
                f"{imdb_id} S{season:02d}E{episode:02d}"
            )
            raise _RetryableError() from exc
        except urllib.error.URLError as exc:
            self._log_warning(
                f"OmdbClient._fetch_episode: URLError for "
                f"{imdb_id} S{season:02d}E{episode:02d}: {exc.reason}"
            )
            raise _RetryableError() from exc
        except Exception as exc:
            self._log_warning(
                f"OmdbClient._fetch_episode: unexpected error for "
                f"{imdb_id} S{season:02d}E{episode:02d}: {exc}"
            )
            raise _RetryableError() from exc

        try:
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError) as exc:
            self._log_warning(
                f"OmdbClient._fetch_episode: invalid JSON for "
                f"{imdb_id} S{season:02d}E{episode:02d}: {exc}"
            )
            return None

        if data.get("Response") != "True":
            error_msg = data.get("Error", "Unknown error")
            self._log_warning(
                f"OmdbClient._fetch_episode: OMDb error for "
                f"{imdb_id} S{season:02d}E{episode:02d}: {error_msg}"
            )
            return None

        imdb_rating = data.get("imdbRating")
        if imdb_rating and imdb_rating != "N/A":
            try:
                rating = float(imdb_rating)
            except (ValueError, TypeError):
                self._log_info(
                    f"OmdbClient.get_episode_rating: non-numeric imdbRating "
                    f"'{imdb_rating}' for {imdb_id} S{season:02d}E{episode:02d}"
                )
                return None
            # Parse votes
            raw_votes = data.get("imdbVotes", "0") or "0"
            if raw_votes == "N/A":
                raw_votes = "0"
            try:
                votes = int(raw_votes.replace(",", ""))
            except (ValueError, TypeError):
                votes = 0
            self._log_info(
                f"OmdbClient.get_episode_rating: success for "
                f"{imdb_id} S{season:02d}E{episode:02d} -- rating={rating}, votes={votes}"
            )
            return (rating, votes)

        self._log_info(
            f"OmdbClient.get_episode_rating: no valid rating for "
            f"{imdb_id} S{season:02d}E{episode:02d}"
        )
        return None

    def _sanitize_url(self, url: str) -> str:
        """Replace API key in URL for safe logging."""
        return url.replace(self._api_key, "***") if self._api_key else url

    def _log_debug(self, message: str) -> None:
        if self._logger is not None:
            self._logger.debug(message)

    def _log_info(self, message: str) -> None:
        if self._logger is not None:
            self._logger.info(message)

    def _log_warning(self, message: str) -> None:
        if self._logger is not None:
            self._logger.warning(message)


class _RetryableError(Exception):
    """Internal signal that the request failed and may be retried."""
