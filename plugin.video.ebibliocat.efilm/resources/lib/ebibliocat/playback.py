"""Normalize provider responses and configure supported Kodi stream properties."""

import json
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit

import xbmc
import xbmcgui

from resources.lib.ebibliocat.errors import EfilmError


@dataclass
class Stream:
    url: str
    manifest: str = ""
    mime: str = ""
    drm: str = ""
    license_url: str = ""
    manifest_headers: dict = None
    stream_headers: dict = None
    license_headers: dict = None


def _object(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            value = {"src": value}
    if not isinstance(value, dict):
        raise EfilmError("unsupported_stream")
    return value


def _url(value):
    if not isinstance(value, str) or any(c in value for c in ("\r", "\n", "|")):
        return ""
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in ("https", "http") and parsed.hostname and not parsed.username else ""
    except ValueError:
        return ""


def _headers(value):
    if value is None:
        return {}
    if not isinstance(value, dict) or not all(
        isinstance(k, str) and isinstance(v, str) and not any(c in k + v for c in ("\r", "\n"))
        for k, v in value.items()
    ):
        raise EfilmError("invalid_response")
    return value


def parse_stream(playback):
    if isinstance(playback, list):
        playback = playback[0] if playback else {}
    playback = _object(playback)
    playback = _object(playback.get("data", playback))
    player = _object(playback.get("player", playback))
    source = _object(player.get("source", player))
    streaming = source.get("data_streaming") or {}
    if isinstance(streaming, list):
        streaming = streaming[0] if streaming else {}
    streaming = _object(streaming)
    url, key = "", ""
    for key in ("src", "url", "file", "DASHURL", "HLSURL", "FLVURL"):
        url = _url(source.get(key)) or _url(streaming.get(key))
        if url:
            break
    if not url:
        raise EfilmError("unsupported_stream")
    kind = str(streaming.get("manifest_type") or streaming.get("type") or source.get("type") or key).lower()
    path = urlsplit(url).path.lower()
    if path.endswith(".mpd") or "dash" in kind:
        manifest, mime = "mpd", "application/dash+xml"
    elif path.endswith(".m3u8") or any(k in kind for k in ("hls", "mpegurl", "flvurl")):
        manifest, mime = "hls", "application/vnd.apple.mpegurl"
    elif path.endswith((".mp4", ".m4v")) or "mp4" in kind:
        manifest, mime = "", "video/mp4"
    else:
        # A web player/iframe URL is not a Kodi-compatible stream.
        raise EfilmError("unsupported_stream")
    license_value = (
        streaming.get("license_url")
        or streaming.get("licenseUrl")
        or source.get("license_url")
        or source.get("licenseUrl")
        or ""
    )
    license_url = _url(license_value)
    drm_value = (
        streaming.get("license_type")
        or streaming.get("drm_type")
        or source.get("license_type")
        or source.get("drm_type")
        or ""
    )
    drm_name = str(drm_value).lower()
    if drm_name in ("widevine", "com.widevine.alpha"):
        drm = "com.widevine.alpha"
    elif drm_name in ("playready", "com.microsoft.playready"):
        drm = "com.microsoft.playready"
    elif drm_name or license_value:
        raise EfilmError("unsupported_drm")
    else:
        drm = ""
    if drm and (not manifest or not license_url):
        raise EfilmError("unsupported_drm")
    common = _headers(streaming.get("headers") or source.get("headers"))
    return Stream(
        url,
        manifest,
        mime,
        drm,
        license_url,
        _headers(streaming.get("manifest_headers") or source.get("manifest_headers") or common),
        _headers(streaming.get("stream_headers") or source.get("stream_headers") or common),
        _headers(streaming.get("license_headers") or source.get("license_headers")),
    )


def kodi_major():
    try:
        return int(xbmc.getInfoLabel("System.BuildVersion").split(".", 1)[0])
    except (ValueError, AttributeError):
        raise EfilmError("unsupported_stream") from None


def check_dependencies(protocol="mpd", drm=None):
    if drm and drm != "com.widevine.alpha":
        if (
            drm != "com.microsoft.playready"
            or kodi_major() < 21
            or not xbmc.getCondVisibility("System.Platform.Android")
        ):
            raise EfilmError("unsupported_drm")
    try:
        import inputstreamhelper
    except ImportError:
        raise EfilmError("helper_missing") from None
    try:
        # PlayReady is native to supported Android ISA builds; Helper installs Widevine only.
        helper = inputstreamhelper.Helper(protocol, drm=drm if drm == "com.widevine.alpha" else None)
        ready = helper.check_inputstream()
    except (OSError, ValueError, RuntimeError):
        raise EfilmError("drm_missing" if drm else "inputstream_missing") from None
    if not ready:
        raise EfilmError("drm_missing" if drm else "inputstream_missing")


def make_item(stream, title):
    item = xbmcgui.ListItem(path=stream.url)
    item.setMimeType(stream.mime)
    item.setContentLookup(False)
    item.setProperty("IsPlayable", "true")
    if kodi_major() >= 20:
        item.getVideoInfoTag().setTitle(title)
    else:
        item.setInfo("video", {"title": title})
    if not stream.manifest:
        if stream.stream_headers:
            # Direct MP4 headers use Kodi's URL header syntax, not ISA properties.
            item.setPath(stream.url + "|" + urlencode(stream.stream_headers))
        return item
    check_dependencies(stream.manifest, stream.drm or None)
    item.setProperty("inputstream", "inputstream.adaptive")
    version = kodi_major()
    if version < 21:
        item.setProperty("inputstream.adaptive.manifest_type", stream.manifest)
    for name, value in (
        ("manifest_headers", stream.manifest_headers),
        ("stream_headers", stream.stream_headers),
    ):
        if value:
            item.setProperty("inputstream.adaptive." + name, urlencode(value))
    if stream.drm:
        headers = urlencode(stream.license_headers)
        if version >= 22:
            config = {stream.drm: {"license": {"server_url": stream.license_url, "req_headers": headers}}}
            item.setProperty("inputstream.adaptive.drm", json.dumps(config))
        elif version >= 21:
            item.setProperty(
                "inputstream.adaptive.drm_legacy", "|".join((stream.drm, stream.license_url, headers))
            )
        else:
            item.setProperty("inputstream.adaptive.license_type", stream.drm)
            item.setProperty(
                "inputstream.adaptive.license_key", "{}|{}|R{{SSM}}|".format(stream.license_url, headers)
            )
    return item
