"""
Brightcove video resolver.

Resolves a Brightcove video ID to a playable HLS/MP4 stream URL
using the Brightcove Playback API (edge.api.brightcove.com).
"""

import json

try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import Request, urlopen, HTTPError

from . import rainfocus

# Brightcove Playback API
PLAYBACK_API = (
    "https://edge.api.brightcove.com/playback/v1/accounts/{account}/videos/{video_id}"
)

_POLICY_KEY = None


def _fetch_policy_key():
    """
    Fetch the Brightcove policy key from the player config.json endpoint.
    The key lives at video_cloud.policy_key in the player configuration.
    Response may be gzip-encoded.
    """
    global _POLICY_KEY
    if _POLICY_KEY:
        return _POLICY_KEY

    import gzip

    config_url = (
        "https://players.brightcove.net/{account}/{player}_default/config.json"
    ).format(account=rainfocus.BRIGHTCOVE_ACCOUNT, player=rainfocus.BRIGHTCOVE_PLAYER)
    try:
        req = Request(config_url, headers={"Accept-Encoding": "gzip"})
        resp = urlopen(req, timeout=15)
        raw = resp.read()
        try:
            data = gzip.decompress(raw)
        except (OSError, IOError):
            data = raw  # Response wasn't gzip-encoded despite header
        config = json.loads(data)
        pk = config.get("video_cloud", {}).get("policy_key")
        if pk:
            _POLICY_KEY = pk
            return _POLICY_KEY
    except Exception:
        pass

    # Fallback: try parsing the player JS for policyKey
    import re
    js_url = (
        "https://players.brightcove.net/{account}/{player}_default/index.min.js"
    ).format(account=rainfocus.BRIGHTCOVE_ACCOUNT, player=rainfocus.BRIGHTCOVE_PLAYER)
    try:
        req = Request(js_url, headers={"Accept-Encoding": "gzip"})
        resp = urlopen(req, timeout=15)
        raw = resp.read()
        try:
            js = gzip.decompress(raw).decode("utf-8", errors="replace")
        except (OSError, IOError):
            js = raw.decode("utf-8", errors="replace")
        m = re.search(r'policyKey\s*:\s*["\']([^"\']+)', js)
        if m:
            _POLICY_KEY = m.group(1)
            return _POLICY_KEY
    except Exception:
        pass

    return None


def resolve(video_id):
    """
    Resolve a Brightcove video ID to stream info.

    Returns:
        dict with keys:
            - streams: list of {url, width, height, bitrate, codec} sorted by bitrate desc
            - thumbnail: str (poster image URL)
            - title: str
            - duration: float (seconds)
        or None if resolution fails
    """
    policy_key = _fetch_policy_key()
    if not policy_key:
        return None

    url = PLAYBACK_API.format(
        account=rainfocus.BRIGHTCOVE_ACCOUNT, video_id=video_id
    )
    headers = {
        "Accept": "application/json;pk={}".format(policy_key),
    }
    req = Request(url, headers=headers)
    try:
        resp = urlopen(req, timeout=15)
        data = json.loads(resp.read().decode("utf-8"))
    except HTTPError:
        return None

    streams = []
    for source in data.get("sources", []):
        src_url = source.get("src", "")
        src_type = source.get("type", "").lower()
        if not src_url:
            continue
        # HLS: type contains mpegurl or m3u8, or URL ends with .m3u8
        if "mpegurl" in src_type or "m3u8" in src_type or ".m3u8" in src_url:
            streams.append({
                "url": src_url,
                "type": "hls",
                "width": source.get("width", 0),
                "height": source.get("height", 0),
                "bitrate": source.get("avg_bitrate", 0),
                "codec": source.get("codec", ""),
            })
        # DASH: type contains dash+xml
        elif "dash" in src_type:
            streams.append({
                "url": src_url,
                "type": "dash",
                "width": source.get("width", 0),
                "height": source.get("height", 0),
                "bitrate": source.get("avg_bitrate", 0),
                "codec": source.get("codec", ""),
            })
        # MP4: type contains mp4, or URL contains /pmp4/ or ends with .mp4
        elif "mp4" in src_type or "/pmp4/" in src_url or src_url.endswith(".mp4"):
            streams.append({
                "url": src_url,
                "type": "mp4",
                "width": source.get("width", 0),
                "height": source.get("height", 0),
                "bitrate": source.get("avg_bitrate", 0),
                "codec": source.get("codec", ""),
            })

    # Sort by bitrate descending (highest quality first)
    streams.sort(key=lambda s: s.get("bitrate", 0), reverse=True)

    poster = data.get("poster", "")
    thumbnail = data.get("thumbnail", poster)

    return {
        "streams": streams,
        "thumbnail": poster or thumbnail,
        "title": data.get("name", ""),
        "duration": data.get("duration", 0) / 1000.0,  # ms to seconds
    }


def best_stream(video_id, prefer_hls=True):
    """
    Get the best playable stream URL for a video.

    Args:
        video_id: Brightcove video ID
        prefer_hls: If True, prefer HLS over MP4 (Kodi handles HLS natively)

    Returns:
        tuple of (url, mime_type) or (None, None)
    """
    info = resolve(video_id)
    if not info or not info["streams"]:
        return None, None

    def prefer_https(stream_list):
        """Sort streams to prefer HTTPS over HTTP."""
        return sorted(stream_list, key=lambda s: (0 if s["url"].startswith("https") else 1))

    if prefer_hls:
        hls = prefer_https([s for s in info["streams"] if s["type"] == "hls"])
        if hls:
            return hls[0]["url"], "application/vnd.apple.mpegurl"

    mp4 = prefer_https([s for s in info["streams"] if s["type"] == "mp4"])
    if mp4:
        return mp4[0]["url"], "video/mp4"

    # DASH fallback
    dash = prefer_https([s for s in info["streams"] if s["type"] == "dash"])
    if dash:
        return dash[0]["url"], "application/dash+xml"

    # Last resort: first available
    s = info["streams"][0]
    type_map = {"hls": "application/vnd.apple.mpegurl", "mp4": "video/mp4", "dash": "application/dash+xml"}
    return s["url"], type_map.get(s["type"], "video/mp4")
