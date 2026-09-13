import threading
import time

import requests
import urllib.parse
import xbmc
import xbmcaddon

from resources.lib import oauth


REQUEST_TIMEOUT_SECONDS = 10
DEFAULT_BASE_URL = "https://api.mdblist.com"

# api.mdblist enforces a 5-minute sliding-window throttle (300 write / 1000
# read requests) independent of and much tighter than the daily quota. A
# bulk sync's chunked pushes used to fire back-to-back with nothing in
# between, so a large first sync could blow through the write budget in
# seconds. MAX_RATE_LIMIT_RETRIES/MAX_AUTO_RETRY_DELAY_SECONDS bound how a
# 429 is retried; _WRITE_PACER/_READ_PACER proactively space every request
# out so a bulk sync ideally never trips the throttle in the first place.
MAX_RATE_LIMIT_RETRIES = 3
# A 429's Retry-After is auto-retried only up to this wait -- enough to ride
# out the ~300s short-window throttle, but not the daily quota's "retry
# after midnight UTC" (which can be many hours).
MAX_AUTO_RETRY_DELAY_SECONDS = 310
# Fallback wait for a 429 that, unexpectedly, carries no Retry-After header.
DEFAULT_RETRY_AFTER_SECONDS = 5


class MDBListApiError(Exception):
    def __init__(self, message, status_code=None, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after

    @property
    def is_rate_limited(self):
        return self.status_code == 429


class _RequestPacer:
    """Spaces out requests to a fixed minimum interval, sleeping (on
    whatever thread calls it -- every caller of mdblist_api.request() here
    already runs off a background thread, never Kodi's main/UI thread) when
    a caller would otherwise send too soon. Shared across every thread in
    the process, since api.mdblist's rate-limit budget is per-account, not
    per-thread."""

    def __init__(self, min_interval_seconds):
        self._min_interval = min_interval_seconds
        self._lock = threading.Lock()
        self._next_slot = 0.0

    def wait(self):
        with self._lock:
            now = time.monotonic()
            slot = max(self._next_slot, now)
            delay = slot - now
            self._next_slot = slot + self._min_interval

        if delay > 0:
            time.sleep(delay)


# api.mdblist's write bucket allows 300 requests / 300s -- exactly 1/s
# sustained. Pacing writes a touch slower than that means a bulk push should
# never trip the throttle on its own.
_WRITE_PACER = _RequestPacer(1.1)
# api.mdblist's read bucket allows 1000 requests / 300s (~3.3/s).
_READ_PACER = _RequestPacer(0.32)


def _parse_retry_after(response):
    """api.mdblist always sends Retry-After as a plain integer second count
    on a 429 (never an HTTP-date), so that's the only form parsed."""
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        seconds = int(value)
    except ValueError:
        return None
    return seconds if seconds >= 0 else None


def _addon():
    return xbmcaddon.Addon()


def get_string_setting(setting_id: str, default: str = ""):
    try:
        value = _addon().getSettings().getString(setting_id)
        return value or default
    except Exception:
        return default


def base_url():
    return DEFAULT_BASE_URL


def auth_params():
    access_token = oauth.ensure_valid_token()
    apikey = "" if access_token else get_string_setting("apikey")

    if access_token:
        return {"headers": {"Authorization": "Bearer {}".format(access_token)}, "query": ""}
    if apikey:
        return {"headers": None, "query": urllib.parse.urlencode({"apikey": apikey})}

    raise MDBListApiError("Not authenticated. Open addon settings to connect.")


def request(method: str, endpoint: str, params=None, json_data=None):
    auth = auth_params()
    url = "{}{}".format(base_url(), endpoint)

    query = auth["query"]
    if params:
        filtered = {key: value for key, value in params.items() if value not in (None, "")}
        encoded = urllib.parse.urlencode(filtered)
        if encoded:
            query = "{}&{}".format(query, encoded) if query else encoded
    if query:
        url = "{}?{}".format(url, query)

    # GET is the only read verb this module ever issues -- everything else
    # (POST) draws from the write bucket, which api.mdblist polices far
    # tighter (300 vs 1000 per 5-minute window).
    pacer = _READ_PACER if method.upper() == "GET" else _WRITE_PACER

    attempt = 0
    while True:
        pacer.wait()

        try:
            response = requests.request(
                method,
                url,
                json=json_data,
                headers=auth["headers"],
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.exceptions.RequestException as exception:
            raise MDBListApiError(str(exception))

        if response.status_code == 429:
            retry_after = _parse_retry_after(response)
            if retry_after is None:
                retry_after = DEFAULT_RETRY_AFTER_SECONDS

            if attempt < MAX_RATE_LIMIT_RETRIES and retry_after <= MAX_AUTO_RETRY_DELAY_SECONDS:
                attempt += 1
                time.sleep(retry_after)
                continue

            xbmc.log(
                "MDBList Scrobbler: API error 429 on {} response={}".format(endpoint, response.text[:200]),
                level=xbmc.LOGERROR,
            )
            raise MDBListApiError(
                "API Error 429: {}".format(response.text[:80]),
                status_code=429,
                retry_after=retry_after,
            )

        if response.status_code >= 400:
            xbmc.log(
                "MDBList Scrobbler: API error {} on {} response={}".format(
                    response.status_code, endpoint, response.text[:200]
                ),
                level=xbmc.LOGERROR,
            )
            raise MDBListApiError(
                "API Error {}: {}".format(response.status_code, response.text[:80]),
                status_code=response.status_code,
            )

        break

    try:
        return response.json()
    except ValueError:
        # A 200 with an unparseable body is a real failure, not "no data" --
        # callers read the result with .get() and treat a missing key as
        # legitimately absent (no items, no server_time, etc.), so silently
        # returning {} here would be indistinguishable from a genuinely
        # empty-but-valid response.
        raise MDBListApiError("Invalid response from {}".format(endpoint))


def fetch_watchlist(mediatype=None, limit=100):
    endpoint = "/watchlist/items/{}".format(mediatype) if mediatype else "/watchlist/items"
    cursor = None
    movies = []
    shows = []

    while True:
        params = {"limit": limit, "append_to_response": "poster"}
        if cursor:
            params["cursor"] = cursor

        data = request("GET", endpoint, params=params)
        if isinstance(data, list):
            movies.extend([item for item in data if item.get("mediatype") == "movie"])
            shows.extend([item for item in data if item.get("mediatype") == "show"])
        else:
            movies.extend(data.get("movies") or [])
            shows.extend(data.get("shows") or [])

        pagination = data.get("pagination", {}) if isinstance(data, dict) else {}
        cursor = pagination.get("next_cursor")
        if not cursor:
            break

    return {"movies": movies, "shows": shows}


def modify_watchlist(action: str, mediatype: str, ids: dict):
    if mediatype == "movie":
        payload = {"movies": [ids]}
    elif mediatype == "show":
        payload = {"shows": [ids]}
    else:
        raise MDBListApiError("Unsupported watchlist type: {}".format(mediatype))

    return request("POST", "/watchlist/items/{}".format(action), json_data=payload)


def fetch_sync_items(endpoint: str, mediatype=None, since=None, extended="ids_only", limit=1000):
    """Cursor-paginate a /sync/* GET endpoint and merge every page's list-valued
    keys (movies/shows/seasons/episodes/...) into one dict, ignoring pagination."""
    params = {"limit": limit, "extended": extended}
    if mediatype:
        params["mediatype"] = mediatype
    if since:
        params["since"] = since

    cursor = None
    merged = {}

    while True:
        page_params = dict(params)
        if cursor:
            page_params["cursor"] = cursor

        data = request("GET", endpoint, params=page_params)
        if not isinstance(data, dict):
            break

        for key, value in data.items():
            if key == "pagination" or not isinstance(value, list):
                continue
            merged.setdefault(key, []).extend(value)

        cursor = (data.get("pagination") or {}).get("next_cursor")
        if not cursor:
            break

    return merged


def push_sync_items(endpoint: str, payload: dict):
    return request("POST", endpoint, json_data=payload)


def fetch_journal(since=None, limit=1000):
    """Page through /sync/journal starting from `since`. Returns
    {"requires_full_sync": True} if the caller's watermark is outside the
    30-day retention window, otherwise {"requires_full_sync": False,
    "entries": [...], "journal_oldest_at": ...}."""
    cursor = None
    entries = []
    journal_oldest_at = None

    while True:
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        elif since:
            params["since"] = since

        data = request("GET", "/sync/journal", params=params)
        if not isinstance(data, dict):
            break

        if data.get("requires_full_sync"):
            return {"requires_full_sync": True, "entries": []}

        entries.extend(data.get("journal") or [])
        journal_oldest_at = data.get("journal_oldest_at", journal_oldest_at)

        cursor = (data.get("pagination") or {}).get("next_cursor")
        if not cursor:
            break

    return {"requires_full_sync": False, "entries": entries, "journal_oldest_at": journal_oldest_at}


def fetch_last_activities():
    data = request("GET", "/sync/last_activities")
    # server_time is always present in a real response -- every caller uses
    # it as the next sync watermark, so a response that parsed but doesn't
    # have it (wrong shape, unexpected body) needs to abort the pull rather
    # than let watched_sync/ratings_sync silently fall back to the device's
    # own clock.
    if not isinstance(data, dict) or "server_time" not in data:
        raise MDBListApiError("Malformed response from /sync/last_activities")
    return data
