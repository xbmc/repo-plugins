"""Kodi streamdetails -> the Trakt media values MDBList's POST /sync/collection
takes (resolution, hdr, audio, audio_channels, 3d) -- the Kodi counterpart of
the Jellyfin/Emby plugins' MediaInfoMapper. Each Kodi library entry is one
file; collection_sync sends one copy per entry (several when a title is in the
library more than once).

No xbmc imports: pure functions over the JSON-RPC "streamdetails" dict."""

MEDIA_FIELDS = ("resolution", "hdr", "audio", "audio_channels", "3d")

_CHANNELS = {1: "1.0", 2: "2.0", 3: "2.1", 4: "4.0", 5: "5.0", 6: "5.1", 7: "6.1", 8: "7.1"}
_SIMPLE_AUDIO = {
    "aac": "aac", "mp3": "mp3", "mp2": "mp2", "flac": "flac",
    "opus": "ogg_opus", "vorbis": "ogg", "wmav2": "wma", "wmapro": "wma",
}


def resolution(width, height):
    """Trakt resolution from a video stream's size. Width decides first, so a
    cropped widescreen 1920x800 file still counts as 1080p. Kodi doesn't
    report interlacing, so the progressive values are used."""
    w, h = width or 0, height or 0
    if w <= 0 and h <= 0:
        return None
    if w >= 3200 or h >= 1800:
        return "uhd_4k"
    if w >= 1800 or h >= 1000:
        return "hd_1080p"
    if w >= 1200 or h >= 700:
        return "hd_720p"
    if h >= 540:
        return "sd_576p"
    return "sd_480p"


def hdr(hdrtype):
    """Trakt HDR value from Kodi's hdrtype ("dolbyvision", "hdr10", "hlg", and
    "hdr10plus" on builds that report it); empty means SDR."""
    value = (hdrtype or "").lower().replace("_", "").replace("+", "plus")
    if "dolbyvision" in value or value.startswith("dovi"):
        return "dolby_vision"
    if "hdr10plus" in value:
        return "hdr10_plus"
    if "hdr10" in value:
        return "hdr10"
    if "hlg" in value:
        return "hlg"
    return None


def audio(codec):
    """Trakt audio value from Kodi's audio codec name. Besides ffmpeg's names
    (truehd, eac3, dca, ...) Kodi reports DTS profiles as dtshd_ma/dtshd_hra
    and, on newer builds, Atmos/DTS:X variants such as truehd_atmos,
    eac3_ddp_atmos and dtshd_ma_x."""
    c = (codec or "").lower()
    if c.startswith("truehd"):
        return "dolby_atmos" if "atmos" in c else "dolby_truehd"
    if c.startswith("eac3") or c.startswith("ddp"):
        return "dolby_digital_plus_atmos" if "atmos" in c else "dolby_digital_plus"
    if c == "ac3":
        return "dolby_digital"
    if c.startswith("dts") or c == "dca":
        if c in ("dtsx", "dts_x") or c.startswith("dtshd_ma_x"):
            return "dts_x"
        if c.startswith("dtshd_ma"):
            return "dts_ma"
        if c.startswith("dtshd_hra"):
            return "dts_hr"
        return "dts"
    if c.startswith("pcm"):
        return "lpcm"
    return _SIMPLE_AUDIO.get(c)


def channels(count):
    try:
        return _CHANNELS.get(int(count or 0))
    except (TypeError, ValueError):
        return None


def from_streamdetails(streamdetails):
    """The media fields of one Kodi library entry, leaving out unknown values;
    an empty dict when nothing is known (the entry then sends no copy)."""
    streamdetails = streamdetails or {}
    video = (streamdetails.get("video") or [{}])[0] or {}
    sound = (streamdetails.get("audio") or [{}])[0] or {}
    fields = {
        "resolution": resolution(video.get("width"), video.get("height")),
        "hdr": hdr(video.get("hdrtype")),
        "audio": audio(sound.get("codec")),
        "audio_channels": channels(sound.get("channels")),
        # Kodi reports "mono" for files explicitly tagged 2D.
        "3d": True if video.get("stereomode") not in (None, "", "mono") else None,
    }
    return {key: value for key, value in fields.items() if value is not None}
