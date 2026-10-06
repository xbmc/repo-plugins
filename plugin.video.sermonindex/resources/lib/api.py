"""
SermonIndex API v2 client.

The API is pre-generated static JSON on a CDN: no key, no rate limit, and every
response is cacheable. That shapes this module far more than any design taste —
see the note on sizes below, which is the single most important fact here.

    https://api.sermonindex.net/v2

WHAT WE MAY AND MAY NOT FETCH
-----------------------------
    /v2/sermons        149 MB   NEVER. Not on a Raspberry Pi, not anywhere.
    /v2/topics          37 MB   NEVER — it carries a prose description per topic.
    /v2/speakers       1.6 MB   fine, once, cached.
    /v2/scripture       tiny    fine.
    /v2/random          tiny    fine.
    /v2/speakers/<slug>  small  the per-speaker file, WITH its sermons.
    /v2/scripture/<BOOK>[/<ch>] small.

So browsing is built entirely from the small per-entity files. The two big index
files are treated as if they did not exist. This is why there is no Topics menu
and no full-text search: both would need an index that does not exist in a size
we can load. A slim topics index (slug, name, sermonCount — no descriptions)
would be roughly 1 MB and would unlock topic browsing immediately.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.sermonindex.net/v2"
TIMEOUT = 20
UA = "Kodi plugin.video.sermonindex/1.0.0 (+https://www.sermonindex.net/)"

# A small in-process cache. Kodi starts a fresh Python interpreter per navigation
# step, so this only helps within one directory build — which is exactly where it
# matters (the speaker index is read once per page of the A-Z).
_CACHE = {}
_CACHE_TTL = 300


class ApiError(Exception):
    pass


def _get(path):
    """GET a path under /v2 and parse it as JSON."""
    url = path if path.startswith("http") else "{}/{}".format(BASE, path.lstrip("/"))
    hit = _CACHE.get(url)
    if hit and (time.time() - hit[0]) < _CACHE_TTL:
        return hit[1]
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError, OSError) as exc:
        raise ApiError(str(exc))
    _CACHE[url] = (time.time(), data)
    return data


# ── Browse ──────────────────────────────────────────────────────────────────

def speakers():
    """All 2,188 speakers. 1.6 MB — the largest thing this addon ever fetches."""
    return _get("speakers").get("speakers", [])


def speaker(slug):
    """One speaker, including the full sermon records for everything they have."""
    return _get("speakers/{}".format(urllib.parse.quote(slug)))


def books():
    """The 66 books of the Bible, each with a sermon count."""
    return _get("scripture").get("books", [])


def book(book_id):
    return _get("scripture/{}".format(urllib.parse.quote(book_id)))


def chapter(book_id, ch):
    return _get("scripture/{}/{}".format(urllib.parse.quote(book_id), int(ch)))


def random_sermons():
    data = _get("random")
    if isinstance(data, dict):
        return data.get("sermons") or data.get("results") or []
    return data if isinstance(data, list) else []


# ── Media selection ─────────────────────────────────────────────────────────
#
# Every sermon carries up to four media URLs. The plain `mp3Url`/`mp4Url` fields
# are ALREADY the Internet Archive; the `cdn*` fields are the SermonIndex CDN.
#
#   archive audio  33,711      cdn audio  36,363
#   archive video   8,894      cdn video   9,939
#
# Archive-first is deliberate: the Archive hosts this free, so a popular addon
# costs the project nothing. But 2,708 sermons exist ONLY on the CDN, so a
# strict Archive-only rule would silently make them unplayable — hence the
# fallback, which is the same dual-source idea the desktop app uses, reversed.

def pick_media(sermon, source="archive", prefer_video=True):
    """
    Choose what to play. Returns (url, is_video) or (None, False).

    `source` is the PREFERENCE, never a restriction: if the preferred host does
    not have this sermon, the other one is used rather than failing.
    """
    a_arch = sermon.get("archiveAudioUrl") or sermon.get("mp3Url")
    a_cdn = sermon.get("cdnMp3Url")
    v_arch = sermon.get("archiveVideoUrl") or sermon.get("mp4Url")
    v_cdn = sermon.get("cdnMp4Url")

    def order(primary, secondary):
        return [u for u in (primary, secondary) if u]

    if source == "cdn":
        video, audio = order(v_cdn, v_arch), order(a_cdn, a_arch)
    else:
        video, audio = order(v_arch, v_cdn), order(a_arch, a_cdn)

    if prefer_video and video:
        return video[0], True
    if audio:
        return audio[0], False
    if video:
        return video[0], True
    return None, False


def playable(sermon):
    """
    Is there anything here Kodi can play?

    42% of the catalogue (27,169 of 64,227) is mediaType TEXT — transcripts and
    articles with no audio or video at all. They are perfectly good content on
    the website and completely useless in a media centre, so they never enter a
    listing. A directory full of items that do nothing when clicked is worse
    than a shorter directory.
    """
    return bool(
        sermon.get("archiveAudioUrl") or sermon.get("cdnMp3Url") or sermon.get("mp3Url")
        or sermon.get("archiveVideoUrl") or sermon.get("cdnMp4Url") or sermon.get("mp4Url")
    )


def subtitles(sermon):
    """SRT/VTT if this sermon has them — about 36,400 do."""
    return [u for u in (sermon.get("vttUrl"), sermon.get("srtUrl")) if u]


def duration_seconds(sermon):
    """'58:01' or '1:02:58' -> seconds. Kodi wants an int; bad values mean 0."""
    raw = (sermon.get("duration") or "").strip()
    if not raw:
        return 0
    try:
        parts = [int(p) for p in raw.split(":")]
    except ValueError:
        return 0
    secs = 0
    for p in parts:
        secs = secs * 60 + p
    return secs
