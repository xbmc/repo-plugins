# -*- coding: utf-8 -*-
"""Small HTTP helpers (standard library only)."""
try:
    from urllib.parse import quote, unquote
    from urllib.request import Request, urlopen
except ImportError:  # pragma: no cover
    from urllib import quote, unquote
    from urllib2 import Request, urlopen

import time

USER_AGENT = "TVSPlayer-Kodi/1.1"

# ~80 KB that do not compress, from tvsplayer.app; Google as a second opinion (same rule as the apps)
SPEED_FILE = "https://tvsplayer.app/wp-content/plugins/tvs-player-core/seed/tvs-player-pro-feature.png"
PING = "https://connectivitycheck.gstatic.com/generate_204"


def _split_kodi_url(url):
    """'http://x/y|User-Agent=a&Referer=b' -> ('http://x/y', {'User-Agent': 'a', 'Referer': 'b'})."""
    address, _, options = url.partition("|")
    headers = {}
    for part in options.split("&"):
        key, _, value = part.partition("=")
        if key:
            headers[key] = unquote(value)
    return address, headers


def with_headers(url, headers):
    """Kodi's 'url|Header=value&...' syntax; values are URL-encoded (Kodi decodes them), so a
    '&', '|' or '+' inside a value (e.g. a Referer with a query string) stays intact."""
    if not headers or "|" in url:
        return url
    return url + "|" + "&".join("%s=%s" % (k, quote(v, safe="/:;,()=@")) for k, v in headers.items())


def decode_text(raw):
    """Playlist bytes -> text: UTF-8 (with or without BOM), else Latin-1."""
    if not isinstance(raw, bytes):
        return raw
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def get_text(url, timeout=20):
    address, headers = _split_kodi_url(url)
    headers.setdefault("User-Agent", USER_AGENT)
    response = urlopen(Request(address, headers=headers), timeout=timeout)
    try:
        return decode_text(response.read())
    finally:
        response.close()


def is_reachable(url, timeout=4):
    """Quick check that a stream answers, used to skip dead links before playing."""
    address, headers = _split_kodi_url(url)
    if not address.lower().startswith(("http://", "https://")):
        return True  # rtmp, udp…: cannot be checked cheaply, let Kodi try
    headers.setdefault("User-Agent", USER_AGENT)
    try:
        response = urlopen(Request(address, headers=headers), timeout=timeout)
        try:
            ok = response.getcode() < 400
            response.read(1)
        finally:
            response.close()
        return ok
    except Exception:
        return False


def is_poor_connection():
    """True when this device's internet is missing or too slow to judge a channel: the 80 KB need
    more than 1.5 s after the first byte (under ~0.4 Mbit/s) or more than 4 s in all. When the site
    does not answer, Google is asked. Same rule as the Android apps and tvsplayer.app."""
    t0 = time.time()
    try:
        response = urlopen(Request(SPEED_FILE + "?ping=%d" % int(t0 * 1000),
                                   headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}), timeout=3)
    except Exception:
        try:
            urlopen(Request(PING, headers={"User-Agent": USER_AGENT}), timeout=3).close()
            return False   # the site is down, the internet is not
        except Exception:
            return True
    try:
        first = None
        while True:
            chunk = response.read(16384)
            if not chunk:
                break
            if first is None:
                first = time.time()
            if time.time() - t0 > 4:
                return True
        end = time.time()
        return end - t0 > 4 or (first is not None and end - first > 1.5)
    except Exception:
        return True   # it started answering, then stalled: slow
    finally:
        response.close()
