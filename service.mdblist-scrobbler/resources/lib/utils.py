import datetime
import json

import xbmc


SUPPORTED_IDS = {
    "movie": {"imdb", "tmdb", "trakt", "kitsu", "mdblist"},
    "show": {"imdb", "tmdb", "trakt", "tvdb", "mdblist"},
    "episode": {"imdb", "tmdb", "trakt", "tvdb", "mdblist"},
}

ID_ALIASES = {
    "imdbnumber": "imdb",
    "imdb_id": "imdb",
    "themoviedb": "tmdb",
    "tmdb_id": "tmdb",
    "tvdb_id": "tvdb",
    "trakt_id": "trakt",
    "kitsu_id": "kitsu",
    "mdblist_id": "mdblist",
}


def _normalize_id_value(key: str, value):
    if key in ("tmdb", "tvdb", "trakt", "kitsu") and isinstance(value, str):
        cleaned = value.strip()
        if cleaned.isdigit():
            return int(cleaned)
        return cleaned

    return value


class JSONRPCError(Exception):
    pass


def jsonrpc_request(method: str, params=None):
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1
    }

    if params is not None:
        request["params"] = params

    request_json = json.dumps(request)

    xbmc.log("Sending JSON-RPC request: {}".format(request_json), level=xbmc.LOGDEBUG)
    response_json = xbmc.executeJSONRPC(request_json)
    xbmc.log("Response from JSON-RPC request: {}".format(response_json), level=xbmc.LOGDEBUG)

    response = json.loads(response_json)
    if "error" in response:
        # Raise rather than fall back to {} -- callers that build a library
        # snapshot for diff-based reconciliation treat an empty result as
        # authoritative, so a real query failure needs to abort the sync
        # run rather than look like "the library is empty".
        raise JSONRPCError("{} failed: {}".format(method, response["error"]))
    return response.get("result", {})


def _coerce_unknown_id(unique_id, media_type: str):
    if unique_id is None:
        return None, None

    if isinstance(unique_id, str):
        cleaned = unique_id.strip()
        if not cleaned:
            return None, None

        if cleaned.startswith("tt"):
            return "imdb", cleaned
        if cleaned.isdigit():
            return ("tvdb", cleaned) if media_type in ("episode", "show") else ("tmdb", cleaned)
        return None, None

    if isinstance(unique_id, int):
        return ("tvdb", unique_id) if media_type in ("episode", "show") else ("tmdb", unique_id)

    return None, None


def fix_unique_ids(unique_ids: dict, media_type: str):
    if not isinstance(unique_ids, dict):
        return {}

    canonical = {}

    for raw_key, raw_value in unique_ids.items():
        if raw_value in (None, ""):
            continue

        key = str(raw_key).strip().lower()
        key = ID_ALIASES.get(key, key)

        if key == "unknown":
            continue

        canonical[key] = _normalize_id_value(key, raw_value)

    # Backward-compatible fallback: map Kodi "unknown" id when no canonical ids exist.
    if not canonical and "unknown" in unique_ids:
        mapped_key, mapped_value = _coerce_unknown_id(unique_ids.get("unknown"), media_type)
        if mapped_key:
            canonical[mapped_key] = mapped_value

    allowed = SUPPORTED_IDS.get(media_type, set())
    filtered = {key: value for key, value in canonical.items() if key in allowed}

    return filtered


def _local_utc_offset():
    return datetime.datetime.now() - datetime.datetime.utcnow()


def local_time_to_utc_iso(value):
    """Kodi's lastplayed/dateadded are naive local-time strings
    ('YYYY-MM-DD HH:MM:SS', no timezone info), while every MDBList API
    timestamp is UTC. Comparing or sending the raw string as if it were
    already UTC is wrong by the device's UTC offset -- confirmed as the
    cause of a real bug: on a UTC+3 (EEST) system, a local lastplayed could
    look "newer" than a UTC removal timestamp that actually happened later,
    silently blocking a real remote unwatch from applying. Offset is
    computed from the current moment, so a value from months ago under a
    different DST offset can be off by up to an hour -- acceptable for sync
    conflict-resolution purposes, unlike being off by a fixed multi-hour
    offset on every single comparison.
    """
    if not value:
        return None
    try:
        local_dt = datetime.datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return (local_dt - _local_utc_offset()).strftime("%Y-%m-%dT%H:%M:%S")


def utc_iso_to_local_time(value):
    """Inverse of local_time_to_utc_iso -- convert a UTC timestamp from
    MDBList into a naive local-time string suitable for writing back to
    Kodi's lastplayed/dateadded fields."""
    if not value:
        return None
    cleaned = value.replace("Z", "").replace("T", " ")[:19]
    try:
        utc_dt = datetime.datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return (utc_dt + _local_utc_offset()).strftime("%Y-%m-%d %H:%M:%S")
