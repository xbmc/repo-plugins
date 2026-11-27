"""The conditional download-quality decision.

With the transcode toggles off this module answers "original" without a
server round trip. With one on, the decision is the *server's*, through
PlaybackInfo with the download device profile
(:func:`kofin.core.deviceprofile.build_download`): an item within every
limit — bitrate cap, resolution cap, the device's codec lists, the allowed
HDR types — answers ``SupportsDirectPlay`` and downloads as the original;
anything else hands back a ``TranscodingUrl`` whose job stream-copies the
compliant tracks and re-encodes only the offending ones. A failed decision
raises rather than falling back to the original: silently downloading a
40 GB file the caps ruled out is worse than a retry.
"""

from typing import Any, NamedTuple

from kofin.core import deviceprofile, settings
from kofin.core.http import JellyfinError
from kofin.downloads import files, store
from kofin.core.log import Logger

LOG = Logger(__name__)

JsonDict = dict[str, Any]

# The store's row value is the vocabulary; aliased so the shared vocabulary
# is named once.
ORIGINAL = store.QUALITY_ORIGINAL
TRANSCODE = store.QUALITY_TRANSCODE

VIDEO_TYPES = ("Movie", "Episode")


class Decision(NamedTuple):
    kind: str
    url: str = ""  # transcode only: the absolute progressive stream URL
    container: str = ""  # transcode only: the on-disk container/extension
    play_session_id: str = ""  # transcode only: names the job for closing


def wanted(item_type: str) -> bool:
    """Whether the decision runs at all for this item type."""
    if item_type in VIDEO_TYPES:
        return settings.get_bool("downloadsTranscode")
    if item_type == "Audio":
        return settings.get_bool("downloadsMusicTranscode")
    return False


def _stream_rate(source: JsonDict, kind: str) -> int:
    """The source's own bitrate for its first stream of ``kind``, 0 unknown."""
    for stream in source.get("MediaStreams") or []:
        if stream.get("Type") == kind:
            return int(stream.get("BitRate") or 0)
    return 0


def cap_bitrates_to_source(url: str, source: JsonDict) -> str:
    """Splice the URL's target bitrates down to the source's own rates.

    The server sizes a transcode from the profile's budget, not from the
    source, so the target never exceeds the source stream's own rate.
    Lowering to *equal* is safe for a stream the server planned to copy: the
    copy gates on ``requested >= source``, which equality satisfies. Params
    are spliced textually, as ``play.rewrite_bitrates`` does, and a URL that
    names no bitrate is left alone.
    """
    base, _, query = url.partition("?")
    if not query:
        return url
    caps = {
        "VideoBitrate=": _stream_rate(source, "Video"),
        "AudioBitrate=": _stream_rate(source, "Audio"),
    }
    rewritten = []
    for param in query.split("&"):
        for prefix, source_rate in caps.items():
            if source_rate and param.startswith(prefix):
                value = param[len(prefix) :]
                if value.isdigit() and int(value) > source_rate:
                    param = "%s%d" % (prefix, source_rate)
                break
        rewritten.append(param)
    return "%s?%s" % (base, "&".join(rewritten))


def estimated_bytes(url: str, runtime_ticks: int) -> int:
    """A transcode's likely finished size, off the URL's own targets.

    The only total a progress bar can get — no Content-Length exists. The
    targets are capped to the source's own rates by
    :func:`cap_bitrates_to_source`. 0 when the URL names no bitrate or the
    runtime is unknown, which the bar reads as "count this item only when it
    finishes".
    """
    seconds = runtime_ticks / 10_000_000
    if seconds <= 0:
        return 0
    total_bps = 0
    for param in url.partition("?")[2].split("&"):
        for prefix in ("VideoBitrate=", "AudioBitrate="):
            if param.startswith(prefix):
                value = param[len(prefix) :]
                if value.isdigit():
                    total_bps += int(value)
    if total_bps <= 0:
        return 0
    return int(seconds * total_bps / 8)


def progressive(transcoding_url: str) -> str:
    """The progressive shape of a TranscodingUrl.

    An http-protocol profile is answered with a progressive URL already; the
    rewrite is the fallback for a server that hands back the HLS playlist
    shape anyway (Streamyfin's rewrite). The ``.mp4`` in the replacement is
    load-bearing: ``/Videos/{id}/stream`` reads its output container off the
    extension, and the HLS URL's own params carry no ``container=``.
    """
    for playlist in ("master.m3u8", "main.m3u8"):
        if playlist in transcoding_url:
            return transcoding_url.replace(playlist, "stream.mp4", 1)
    return transcoding_url


def decide(api: Any, item: JsonDict) -> Decision:
    """original | transcode(url) for one item; raises on an unusable answer."""
    item_id = str(item.get("Id") or "")
    item_type = str(item.get("Type") or "")
    if not wanted(item_type):
        return Decision(ORIGINAL)

    profile = deviceprofile.build_download(deviceprofile.ProfileConfig.for_downloads())
    info = api.playback_info(item_id, profile)
    sources = info.get("MediaSources") or []
    if not sources:
        raise JellyfinError("no media sources in the decision for %s" % item_id)
    source = sources[0]

    if source.get("SupportsDirectPlay") or source.get("SupportsDirectStream"):
        # Within every limit. DirectStream — all streams copied, container
        # remuxed — counts as original too: the profile states no container
        # constraint, and a local play through Kodi's demuxer never needs
        # one, so a remux would re-package bytes that are fine as they are.
        return Decision(ORIGINAL)

    transcoding_url = str(source.get("TranscodingUrl") or "")
    if not transcoding_url:
        raise JellyfinError(
            "no compliant stream and no transcode offered for %s" % item_id
        )
    url = cap_bitrates_to_source(progressive(transcoding_url), source)
    if url.startswith("/"):
        url = api.server + url
    container = files.extension(
        str(source.get("TranscodingContainer") or "").split(",")[0], ""
    )
    if not container:
        container = (
            (settings.get_str("downloadsMusicCodec") or "opus")
            if item_type == "Audio"
            else "mp4"
        )
    LOG.debug(
        "download decision for %s: transcode (%s)",
        item_id,
        source.get("TranscodeReasons") or "reasons unstated",
    )
    return Decision(TRANSCODE, url, container, str(info.get("PlaySessionId") or ""))
