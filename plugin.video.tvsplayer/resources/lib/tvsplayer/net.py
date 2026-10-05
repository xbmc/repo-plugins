# -*- coding: utf-8 -*-
"""Small HTTP helpers (standard library only)."""
try:
    from urllib.parse import quote, unquote
    from urllib.request import Request, urlopen
except ImportError:  # pragma: no cover
    from urllib import quote, unquote
    from urllib2 import Request, urlopen

USER_AGENT = "TVSPlayer-Kodi/1.0"


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
