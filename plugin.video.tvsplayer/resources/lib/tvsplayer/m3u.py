# -*- coding: utf-8 -*-
"""M3U / M3U8 playlist parser (no Kodi dependencies, unit-testable).

Understands the usual IPTV-style format:
    #EXTM3U
    #EXTINF:-1 tvg-logo="http://.../logo.png" group-title="News" radio="false",Channel name
    #EXTVLCOPT:http-user-agent=Mozilla/5.0
    http://stream-address
Lines that are just an address (no #EXTINF) are accepted too.
"""
import re

from . import net

TV = "tv"
RADIO = "radio"

# How the channels of a playlist are sorted into the TV / Radio menus
TYPE_AUTO = "auto"
TYPE_TV = "tv"
TYPE_RADIO = "radio"

_ATTRIBUTE = re.compile(r'([\w-]+)="([^"]*)"')
_ATTRIBUTE_SPAN = re.compile(r'[\w-]+="[^"]*"')
_AUDIO_EXTENSIONS = (".mp3", ".aac", ".ogg", ".opus", ".m4a", ".pls", ".flac", ".wav")


def parse(text, default_group, type_mode=TYPE_AUTO):
    """Returns a list of entries: dict(name, logo, group, url, type)."""
    entries = []
    name = None
    attrs = {}
    group_line = None
    headers = {}

    for raw in text.splitlines():
        line = raw.strip().lstrip("﻿")
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("#EXTINF"):
            header = line.split(":", 1)[1] if ":" in line else ""
            attrs = {k.lower(): v for k, v in _ATTRIBUTE.findall(header)}
            name = _display_name(header)
        elif upper.startswith("#EXTGRP:"):
            group_line = line.split(":", 1)[1].strip()
        elif upper.startswith("#EXTVLCOPT:"):
            # Stream headers some providers need (converted to Kodi's "url|Header=value" syntax)
            option = line.split(":", 1)[1]
            key, _, value = option.partition("=")
            key = key.strip().lower()
            if key == "http-user-agent":
                headers["User-Agent"] = value.strip()
            elif key == "http-referrer":
                headers["Referer"] = value.strip()
        elif line.startswith("#"):
            continue  # #EXTM3U, comments, unknown tags
        else:
            url = line
            title = (name or "").strip() or attrs.get("tvg-name", "").strip() or \
                url.split("?")[0].rstrip("/").rsplit("/", 1)[-1] or url
            group = attrs.get("group-title", "").strip() or (group_line or "").strip() or default_group
            url = net.with_headers(url, headers)
            entries.append({
                "name": title,
                "logo": attrs.get("tvg-logo", "").strip(),
                "group": group,
                "url": url,
                "type": _type_of(type_mode, attrs, group, url),
            })
            name, attrs, group_line, headers = None, {}, None, {}
    return entries


def _display_name(header):
    """Name of an #EXTINF line: '-1 tvg-name="a,b",Name' -> 'Name'.

    The name starts after the last key="value" attribute, at the first comma outside quotes and
    brackets: works with user-agent=Mozilla/5.0 (KHTML, like Gecko) Chrome/... without quotes or
    with only one (same rule as tvsplayer.app, Android and Samsung).
    """
    start = 0
    for m in _ATTRIBUTE_SPAN.finditer(header):
        start = m.end()
    in_quotes, depth, first = False, 0, -1
    for i in range(start, len(header)):
        c = header[i]
        if c == '"':
            in_quotes = not in_quotes
        elif in_quotes:
            continue
        elif c == "(":
            depth += 1
        elif c == ")":
            depth = max(0, depth - 1)
        elif c == ",":
            if depth == 0:
                return header[i + 1:].strip()
            if first < 0:
                first = i
    return header[first + 1:].strip() if first >= 0 else ""   # bracket never closed


def is_hls_stream(text):
    """The address is a single HLS stream (one channel), not a playlist of channels."""
    return re.search(r"#EXT-X-(STREAM-INF|TARGETDURATION|MEDIA-SEQUENCE)", text[:8192], re.I) is not None


def single(url, group):
    """An HLS stream as a one-channel playlist, named after the file or, if generic, the site."""
    file = url.split("?")[0].split("#")[0].rstrip("/").rsplit("/", 1)[-1]
    try:
        from urllib.parse import unquote
        file = unquote(file)
    except Exception:
        pass
    file = re.sub(r"[_+]+", " ", re.sub(r"\.(m3u8?|ts|mp4)$", "", file, flags=re.I)).strip()
    host = re.match(r"^https?://([^/:?#]+)", url, re.I)
    host = re.sub(r"^www\.", "", host.group(1), flags=re.I) if host else url
    generic = re.match(r"^(index|master|playlist|chunklist|stream|live|main|mono|manifest|video|hls)", file, re.I)
    name = host if not file or generic else file
    return [{"name": name, "logo": "", "group": group, "url": url, "type": TV}]


def _type_of(type_mode, attrs, group, url):
    if type_mode == TYPE_TV:
        return TV
    if type_mode == TYPE_RADIO:
        return RADIO
    path = url.split("|")[0].split("?")[0].lower()
    radio = attrs.get("radio", "").lower() == "true" or \
        attrs.get("tvg-type", "").lower() == "radio" or \
        "radio" in group.lower() or \
        path.endswith(_AUDIO_EXTENSIONS)
    return RADIO if radio else TV
