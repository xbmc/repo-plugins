"""Playback resolve: PlaybackInfo -> stream URL -> setResolvedUrl.

The device profile decides how an item is served. The one question this path
asks is which version to play, of an item Kodi has no versions of
(plugin/versions.py). The resolved play's state is queued for the service-side
player to claim and report (state.push_play_item).
"""

import os
import threading
import time
from collections.abc import Callable
from typing import Any, Optional
from uuid import uuid4

import xbmc
import xbmcgui
import xbmcplugin

from kofin.core import deviceprofile, kodirpc, settings, state, streams, toast
from kofin.core.api import LEAVE_TIMEOUT, Api
from kofin.core.http import Abandoned, JellyfinError
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.core.urls import (
    PARAM_AUDIO_INDEX,
    PARAM_BITRATE,
    PARAM_BURN_SUBS,
    PARAM_MEDIA_SOURCE,
    PARAM_SUBTITLE_INDEX,
    PARAM_TRANSCODE,
    PARAM_UNATTENDED,
    STREAM_REQUEST_PARAMS,
)
from kofin.plugin import listitems, subtitles, versions
from kofin.plugin.listitems import AUDIO_TYPES
from kofin.sync import private
from kofin.plugin.router import Request

LOG = Logger(__name__)

# Jellyfin types with a native row, and Kodi's name for it.
NATIVE_MEDIA = {
    "Movie": "movie",
    "Episode": "episode",
    "MusicVideo": "musicvideo",
    "Audio": "song",
}

JsonDict = dict[str, Any]

MIME_BY_CONTAINER = {
    "mp4": "video/mp4",
    "m4v": "video/mp4",
    "mkv": "video/x-matroska",
    "webm": "video/webm",
    "avi": "video/avi",
    "ts": "video/mp2t",
    "mpegts": "video/mp2t",
    "mov": "video/quicktime",
    "flac": "audio/flac",
    "mp3": "audio/mpeg",
    "aac": "audio/aac",
    "m4a": "audio/mp4",
    "ogg": "audio/ogg",
    "opus": "audio/ogg",
    "wav": "audio/wav",
}
HLS_MIME = "application/x-mpegURL"

# Kodi's STREAM_PROPERTY_ISREALTIMESTREAM, which every input stream reads
# (CDVDInputStream): the source is live, as a PVR client marks live TV.
REALTIME_PROPERTY = "isrealtimestream"

# Chapter images: the chapters dialog draws small tiles, and the server
# resizes before it sends.
CHAPTER_IMAGE_WIDTH = 640
CHAPTER_METHODS = frozenset({"DirectPlay", "DirectStream"})
CHAPTER_TYPES = frozenset({"Movie", "Episode", "MusicVideo", "Video"})


def chapter_art(
    api: Api, item: JsonDict, source: JsonDict, method: str
) -> dict[str, str]:
    """The server's chapter images as the resolved item's ``chapter<n>``
    art, which a Kodi that reads ``chapter<n>`` art shows in its chapters
    dialog in place of the frames it would extract; the extractor refuses an
    http source.

    A direct play only, since a transcode's stream carries no chapters, and
    the item's own file only: the server extracts chapter images from the
    item's primary source, and a version's chapters need not match them."""
    if method not in CHAPTER_METHODS or item.get("Type") not in CHAPTER_TYPES:
        return {}
    if source.get("Id") not in (None, "", item.get("Id")):
        return {}
    art: dict[str, str] = {}
    for index, chapter in enumerate(item.get("Chapters") or []):
        tag = chapter.get("ImageTag") if isinstance(chapter, dict) else None
        if tag:
            art["chapter%d" % (index + 1)] = api.chapter_image_url(
                item["Id"], index, tag, CHAPTER_IMAGE_WIDTH
            )
    return art


# Scrub previews: the dialog shows a thumbnail of about this size, and the
# server keeps a trickplay set per configured width (320 by default).
SCRUB_PREVIEW_MAX_WIDTH = 480

ScrubPreviews = tuple[int, int, int, int, int, list[str], int]


def scrub_previews(
    api: Api, item: JsonDict, source: JsonDict, method: str
) -> Optional[ScrubPreviews]:
    """The server's trickplay tiles for the source played, as the arguments
    of ``InfoTagVideo.setScrubPreviews()``: interval ms, thumbnail width and
    height, columns and rows to a tile, the tile URLs in order, and the
    thumbnail count, since the last tile is part filled.

    ``Trickplay`` on the item is keyed by media source id, then by width.
    A direct play or stream of the source only: a transcode's timeline is the
    source's, but its stream is not what the server extracted from. The
    sharpest set that fits the dialog's preview, else the smallest."""
    if method not in CHAPTER_METHODS:
        return None
    by_source = item.get("Trickplay")
    if not isinstance(by_source, dict):
        return None
    source_id = source.get("Id") or item.get("Id") or ""
    by_width = by_source.get(source_id)
    if not isinstance(by_width, dict) or not by_width:
        return None
    widths = sorted(int(w) for w in by_width if str(w).isdigit())
    if not widths:
        return None
    fitting = [w for w in widths if w <= SCRUB_PREVIEW_MAX_WIDTH]
    width = max(fitting) if fitting else widths[0]
    info = by_width.get(str(width)) or by_width.get(width) or {}
    try:
        interval = int(info["Interval"])
        height = int(info["Height"])
        columns = int(info["TileWidth"])
        rows = int(info["TileHeight"])
        count = int(info["ThumbnailCount"])
    except (KeyError, TypeError, ValueError):
        return None
    if min(interval, width, height, columns, rows, count) <= 0:
        return None
    tiles = -(-count // (columns * rows))
    return (
        interval,
        width,
        height,
        columns,
        rows,
        [
            api.trickplay_tile_url(item["Id"], source_id, width, index)
            for index in range(tiles)
        ],
        count,
    )


def hand_over_scrub_previews(li: xbmcgui.ListItem, previews: ScrubPreviews) -> None:
    """Give a video's previews to Kodi, whose scrub dialog (kontell/xbmc
    video/scrub-previews) reads them off the tag. Never for a song: Kodi
    creates the video tag on first use and classifies an item with one as
    video ahead of its music tag, so a song would go to VideoPlayer. A set
    Kodi refuses costs the previews, not the play."""
    tag = li.getVideoInfoTag()
    if not hasattr(tag, "setScrubPreviews"):
        return
    try:
        tag.setScrubPreviews(*previews)
    except TypeError as error:
        LOG.warning("scrub previews refused: %s", error)


def pick_media_source(
    sources: list[JsonDict], mediasource_id: Optional[str] = None
) -> JsonDict:
    """Select a MediaSource for playback.

    Library version rows pass ``mediasourceid`` so the alternate file is used;
    primary movie URLs omit it and take the first source. A missing id falls
    back to the first source (server may have reorganized sources).
    """
    if not sources:
        raise JellyfinError("no media sources")
    wanted = (mediasource_id or "").strip()
    if wanted:
        for source in sources:
            if source.get("Id") == wanted:
                return source
        LOG.warning("mediasourceid %s not in PlaybackInfo; using first source", wanted)
    return sources[0]


def stream_url(
    server: str,
    item: JsonDict,
    source: JsonDict,
    device_id: str,
    play_session_id: str,
) -> tuple[str, str]:
    """(url, play method) for a MediaSource; raises on unplayable.

    Every stream served off the transcoding endpoint reports as Transcode,
    remux included — the same call pvr.kofin and jellyfin-kodi make. The
    dashboard's remux-vs-transcode wording comes from the server's own
    TranscodingInfo (IsVideoDirect/IsAudioDirect), not from this value, so
    reporting a stream copy as DirectStream here buys nothing and costs the
    session-close and drift-correction paths their signal.
    """
    # A live source never takes the static branch, whatever it claims to
    # support: /stream?static=true of an infinite stream hands Kodi's demuxer
    # a download that never begins. The session's live.m3u8 is the stream
    # that plays (AutoOpenLiveStream is in every PlaybackInfo this module
    # makes): an EVENT playlist, which Kodi's own demuxer pauses and seeks.
    live = bool(source.get("IsInfiniteStream")) or item.get("Type") == "TvChannel"
    if not live and (
        source.get("SupportsDirectPlay") or source.get("SupportsDirectStream")
    ):
        kind = "Audio" if item.get("Type") in AUDIO_TYPES else "Videos"
        container = (source.get("Container") or "").split(",")[0]
        suffix = ".%s" % container if container else ""
        url = (
            "%s/%s/%s/stream%s?static=true&mediaSourceId=%s&deviceId=%s&playSessionId=%s"
            % (
                server,
                kind,
                item.get("Id", ""),
                suffix,
                source.get("Id", ""),
                device_id,
                play_session_id,
            )
        )
        return url, "DirectStream"
    transcoding_url = source.get("TranscodingUrl")
    if transcoding_url:
        return server + transcoding_url, "Transcode"
    raise JellyfinError(
        "no playable stream for %s (%s)" % (item.get("Id"), source.get("Id"))
    )


def mime_for(source: JsonDict, play_method: str) -> str:
    """The MIME type to hand Kodi for the resolved stream.

    A transcode is only HLS when the server says so. The music transcoding
    profile is plain http (``TranscodingSubProtocol: "http"``), and labelling
    that stream as an HLS playlist makes Kodi try to parse the audio as m3u8;
    it gets the transcoded container's type instead.
    """
    if play_method == "Transcode":
        if (source.get("TranscodingSubProtocol") or "hls").lower() == "hls":
            return HLS_MIME
        container = source.get("TranscodingContainer") or ""
    else:
        container = (source.get("Container") or "").split(",")[0]
    return MIME_BY_CONTAINER.get(container.lower(), "")


def rewrite_bitrates(url: str, budget_bps: int, audio_cap_kbps: int) -> str:
    """Replace the server's bitrates with our split of ``budget_bps``.

    Params are spliced textually rather than re-encoded, as pvr.kofin does:
    the transcoding URL carries opaque values (PlaySessionId, api_key) that a
    parse/re-encode round trip has no business touching.
    """
    base, _, query = url.partition("?")
    if not query:
        return url
    kept = [
        param
        for param in query.split("&")
        if not param.startswith(("VideoBitrate=", "AudioBitrate="))
    ]
    audio = deviceprofile.audio_bitrate_bps(audio_cap_kbps, budget_bps)
    kept.append("VideoBitrate=%d" % max(budget_bps - audio, 0))
    kept.append("AudioBitrate=%d" % audio)
    return "%s?%s" % (base, "&".join(kept))


def deny_video_stream_copy(url: str) -> str:
    """Take the video stream copy off the table for a forced transcode.

    No bitrate can do this. Jellyfin allows the copy whenever the requested
    VideoBitrate is at or above the source's, so a budget high enough to be
    worth asking for is a budget that permits a copy -- and any budget low
    enough to forbid one is a quality choice the user did not make.
    ``allowVideoStreamCopy=false`` makes ``CanStreamCopyVideo`` answer no
    whatever the bitrates say.
    """
    return _deny_stream_copy(url, "allowVideoStreamCopy")


def deny_audio_stream_copy(url: str) -> str:
    """Take the audio stream copy off the table for a forced transcode.

    Same pin as video: if E-AC3 is on the TranscodingProfile and the URL then
    asks for an AudioBitrate below the source, StreamBuilder has already
    collapsed AudioCodec to eac3 and 10.11 cannot encode it. Force transcode
    names the preferred encode target on the profile *and* denies the copy
    here. Music PlaybackInfo never reaches this — see the play path.
    """
    return _deny_stream_copy(url, "allowAudioStreamCopy")


def _deny_stream_copy(url: str, flag: str) -> str:
    base, _, query = url.partition("?")
    if not query:
        return url
    prefix = flag + "="
    kept = [param for param in query.split("&") if not param.startswith(prefix)]
    kept.append(flag + "=false")
    return "%s?%s" % (base, "&".join(kept))


def play_state(
    item: JsonDict,
    source: JsonDict,
    url: str,
    play_method: str,
    play_session_id: str,
    device_id: str,
    start_seconds: float,
    attached: Optional[list[int]] = None,
    deferred: Optional[list[streams.Attachment]] = None,
    fetchable: Optional[list[streams.Attachment]] = None,
    request_params: Optional[dict[str, str]] = None,
    streams_menu: bool = True,
) -> JsonDict:
    """The play state the service claims: what the resolved playback is,
    how it is served, and (unless ``streams_menu`` is off — a downloaded
    play, whose one file has only the tracks it was made with) everything
    the stream menu needs, resolved while the PlaybackInfo is fresh."""
    play_item = {
        "Id": item.get("Id", ""),
        "Type": item.get("Type", ""),
        # Carried so the service can name the item in a dialog after playback
        # ends, without a round trip for something it already had.
        "Name": item.get("Name", ""),
        # Same reason, and it has to travel: the dialog in question is the
        # delete offer, and the queue entry is all the service gets. The
        # server answers this per account on the fetch above, with no Fields
        # request needed.
        "CanDelete": bool(item.get("CanDelete")),
        "SeriesId": item.get("SeriesId", ""),
        "Path": url,
        "PlayMethod": play_method,
        "PlaySessionId": play_session_id,
        "MediaSourceId": source.get("Id", ""),
        # The version Play Next has the next episode follow.
        "MediaSourceName": source.get("Name", ""),
        "DeviceId": device_id,
        "Runtime": int(source.get("RunTimeTicks") or item.get("RunTimeTicks") or 0),
        "AudioStreamIndex": source.get("DefaultAudioStreamIndex"),
        "SubtitleStreamIndex": source.get("DefaultSubtitleStreamIndex"),
        "CurrentPosition": start_seconds,
    }
    if source.get("LiveStreamId"):
        # The live stream the server opened for this play: the service's
        # session reports name it (service/player.py).
        play_item["LiveStreamId"] = source["LiveStreamId"]
    if streams_menu:
        # Everything the stream menu needs. The service moves this to a window
        # property when it claims the playback, since by then the queue entry
        # is gone and the context item runs in a third process.
        play_item["Streams"] = {
            "MediaStreams": streams.summarize(source),
            "Attached": list(attached or []),
            # Every embedded text track the server can hand over as a file,
            # whether or not this play asked for one. Whole attachments rather
            # than indices, because the service fetches them by URL and names
            # the files exactly as the play path would have
            # (plugin/subtitles.py) — this is what lets a subtitle picked from
            # the menu arrive without resolving a new stream.
            "Fetchable": [item._asdict() for item in fetchable or []],
            # Of those, the one this play resolved with and did not get inside
            # its budget: chased automatically as soon as the service claims.
            "Deferred": [item.stream_index for item in deferred or []],
            # A restart has to reproduce *this* play method, and a context
            # transcode's bitrate lives nowhere else — the settings would
            # resolve it back to direct play.
            "Request": dict(request_params or {}),
        }
    return play_item


def prefetch_segments(
    api: Api, item: JsonDict, source_id: str = ""
) -> Optional[list[JsonDict]]:
    """Warm the media-segments fetch on the play path: the parsed
    segments ride the play-state queue so the service-side checker is armed
    before the first frame, killing the t≈0 Intro race. None on failure —
    the service then falls back to its own bounded-retry fetch.

    The segments are those of the source that plays: Jellyfin keeps a
    version's segments under its own item id, which is its source id."""
    if item.get("Type") not in ("Movie", "Episode"):
        return []
    if not settings.get_bool("mediaSegmentsEnabled"):
        return []
    from kofin.core.segments import parse_segments

    try:
        return parse_segments(api.media_segments(source_id or item.get("Id", "")))
    except Exception as error:
        LOG.debug("segments prefetch failed for %s: %s", item.get("Id"), error)
        return None


def resume_start_ticks(item: JsonDict, dbid: str) -> int:
    """Where a resume actually starts, in ticks.

    For a library row, whose ``dbid`` the caller passes, that is the bookmark
    in Kodi's own database, taken verbatim. Kodi seeks a library item to that
    bookmark and ignores what the resolved item says, so any other answer is a
    number nothing acts on. It is also the time Kodi's resume prompt just
    quoted at the user.

    Everything else — a plugin listing, synced item or not, a row kofin cannot
    read — is not seeked to a Kodi bookmark. There the resolved item's resume
    point is the only one in play, so the server's position with the offset
    applied, which is the point a listing advertises, is both the answer and
    what Kodi will act on.

    A readable row whose bookmark is 0 answers 0: Kodi will start at the
    beginning whatever the server thinks, and saying so is the honest report.
    """
    media = listitems.MEDIATYPE.get(item.get("Type", ""), "")
    if dbid.isdigit() and media in kodirpc.RESUME_QUERY:
        kodi_resume = kodirpc.resume_seconds(int(dbid), media)
        if kodi_resume is not None:
            return int(kodi_resume * 10_000_000)
    position = float((item.get("UserData") or {}).get("PlaybackPositionTicks") or 0)
    return int(settings.adjusted_resume(position / 10_000_000) * 10_000_000)


def _stream_index(raw: Optional[str]) -> Optional[int]:
    """A stream-index play param, or None when absent or junk.

    ``-1`` is meaningful and passes through: it is how Jellyfin is told "no
    subtitle", as distinct from omitting the parameter and letting the user's
    profile choose one.
    """
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def catalogue_item(item_id: str) -> Optional[JsonDict]:
    """The item as the catalogue last published it, or None: for an item of
    a synced library this is the DTO a download's play is built and claimed
    with, and it needs no server."""
    try:
        from kofin.sync.backends.api.identity import current_store

        return current_store().item(item_id)
    except Exception as error:
        LOG.debug("catalogue has no copy of %s: %s", item_id, error)
        return None


def download_start_ticks(request: Request, item: JsonDict, from_library: bool) -> int:
    """Where a download's play starts: as a streamed play, the bookmark for
    a library row or the item's own position, an explicit start winning."""
    from_start = request.params.get("fromstart") == "1"
    dbid = request.params.get("dbid", "")
    start_ticks = 0
    if request.resume and not from_start:
        start_ticks = resume_start_ticks(item, dbid if from_library else "")
    try:
        return int(request.params.get("startticks") or start_ticks)
    except ValueError:
        return start_ticks


def download_item(item_id: str) -> JsonDict:
    """What the download row knows of its item, as a DTO: enough to play
    the file and claim the play, with the title Kodi's row carries."""
    from kofin.downloads import store

    row = store.get(item_id)
    media = getattr(row, "media_type", "") if row is not None else ""
    item_type = next((t for t, m in NATIVE_MEDIA.items() if m == media), "Video")
    return {
        "Id": item_id,
        "Type": item_type,
        "Name": "",
        "MediaSources": [{"Id": item_id}],
    }


def downloaded_file(item_id: str) -> Optional[str]:
    """The absolute path of this item's completed download, or None.

    None covers every reason there is nothing to play locally, and they are
    not distinguished because none of them changes the answer: no row at
    all, a download still running or failed, a row that never recorded a
    target, and a row whose file has since gone from under it.
    """
    from kofin.downloads import downloads_root, files, store

    row = store.get(item_id)
    if row is None or row.state != store.DONE or not row.rel_path:
        return None

    path = files.path_in(downloads_root(), row.rel_path)
    return path if path is not None and os.path.exists(path) else None


def stream_requested(request: Request) -> bool:
    """Whether this request names a stream or quality the server must serve.

    A download is one file with the tracks it was made with, so a request
    that asks for a particular media source, audio or subtitle track, or a
    transcode at a stated bitrate is asking for something only the server
    can answer — it streams even when a download exists. This is also what
    keeps the stream menu's restart (plugin/streams.py) resolving back to
    the server it was picked from. The names live in core/urls.py beside
    the builder.
    """
    return any(request.params.get(name) for name in STREAM_REQUEST_PARAMS)


def _resolve_to(request: Request, listitem: xbmcgui.ListItem, path: str) -> None:
    """Hand the resolved item back — to the directory handle that asked, or,
    when there is none (a RunPlugin play, a SyncPlay group start), to the
    player directly. The one tail every resolve ends in."""
    if request.handle >= 0:
        xbmcplugin.setResolvedUrl(request.handle, True, listitem)
    else:
        xbmc.Player().play(path, listitem)


def offline_answer(request: Request, item_id: str, from_library: bool = False) -> bool:
    """Handle the play entirely locally when the server is unreachable.

    A downloaded item plays its file however it is reached: a library row,
    a kofin listing (Continue watching, a widget) or a SyncPlay group start.
    Anything not downloaded is answered at once instead of after the
    transport's budget.

    Online the same preference is applied further down, once the item DTO is
    in hand to claim the playback with — see :func:`resolve_downloaded`.

    True means the request is finished.
    """
    if not state.is_offline():
        return False

    path = downloaded_file(item_id)
    if path:
        LOG.debug("offline: resolving %s to its download", item_id)
        item = catalogue_item(item_id)
        if item is not None:
            # Claimed as an online play of the download is, from the
            # catalogue's copy: the service reports it, and the stop it
            # cannot send is parked for the reconnect.
            creds = Credentials.load()
            dbid = request.params.get("dbid", "")
            resolve_downloaded(
                request,
                item,
                path,
                creds.server_address,
                creds.device_id,
                download_start_ticks(request, item, from_library),
                dbid,
                None,
            )
            return True
        listitem = xbmcgui.ListItem(path=path)
        listitem.setContentLookup(False)
        dbid = request.params.get("dbid", "")
        if dbid.isdigit():
            listitem.getVideoInfoTag().setDbId(int(dbid))
            from_start = request.params.get("fromstart") == "1"
            if request.resume and not from_start:
                # Offline the server has no position. Stamp Kodi's bookmark
                # only when the user asked to resume and the point is
                # actually resumable — a resolved item must never carry a
                # zero point (listitems.build).
                from kofin.downloads import store

                row = store.get(item_id)
                media = getattr(row, "media_type", "") if row is not None else ""
                if media in kodirpc.RESUME_QUERY:
                    point = kodirpc.resume_point(int(dbid), media)
                    if point is not None and point[0] > 0 and point[1] > 0:
                        listitem.getVideoInfoTag().setResumePoint(point[0], point[1])
        _resolve_to(request, listitem, path)
        return True

    LOG.debug("offline: %s is not downloaded", item_id)
    _fail(request, 30720)
    return True


def _joined_segments(
    thread: Optional[threading.Thread],
    box: list[Optional[list[JsonDict]]],
) -> Optional[list[JsonDict]]:
    """The prefetched media segments, waiting only as long as they are worth.

    Bounded: the interactive Api budget caps the fetch, so a hung join here
    can only mean the bound itself failed — fall back rather than wait. None
    means the service falls back to its own bounded-retry fetch.
    """
    if thread is not None:
        thread.join(timeout=15.0)
    return box[0] if box else None


def resolve_downloaded(
    request: Request,
    item: JsonDict,
    path: str,
    server: str,
    device_id: str,
    start_ticks: int,
    dbid: str,
    segments: Optional[list[JsonDict]],
) -> None:
    """Resolve a play to the item's own download while the server is up.

    Everything that plays by id — a library row, a kofin listing, a widget,
    a SyncPlay group start — resolves to the download here.

    No stream menu travels with it. The download is one file whose tracks are
    its own (a transcode has exactly the ones it was made with), so the
    server's MediaStreams would describe something else.
    """
    li = listitems.build(item, server, resume_seconds=start_ticks / 10_000_000)
    if dbid.isdigit() and item.get("Type") in ("Movie", "Episode", "MusicVideo"):
        li.getVideoInfoTag().setDbId(int(dbid))
    elif dbid.isdigit() and item.get("Type") in AUDIO_TYPES:
        li.getMusicInfoTag().setDbId(int(dbid), "song")
    li.setPath(path)
    li.setContentLookup(False)

    LOG.debug("play %s via Download", item.get("Id", ""))
    sources = item.get("MediaSources") or [{}]
    # The claim shape the streamed play pushes: DirectPlay, since Kodi opens
    # the file. The "source" is the downloaded one's id and the name Play
    # Next follows, nothing else, so the runtime is the item's and no
    # server-side default track index rides along; a download is always of
    # the item's first source.
    play_item = play_state(
        item,
        {
            "Id": sources[0].get("Id") or item.get("Id", ""),
            "Name": sources[0].get("Name", ""),
        },
        path,
        "DirectPlay",
        uuid4().hex,
        device_id,
        start_ticks / 10_000_000,
        streams_menu=False,
    )
    if segments is not None:
        play_item["Segments"] = segments
    state.push_play_item(play_item)

    _resolve_to(request, li, path)


def play(request: Request) -> None:
    stop = request.stop or _stop_check()
    if stop():
        # Cancelled while the interpreter was still importing: nothing has
        # been asked of anyone yet.
        _unresolved(request)
        return
    # One connection to kofin.db for the life of this interpreter, as the
    # provider keeps.
    private.pool_connections(True)
    item_id = request.params.get("id", "")
    creds = Credentials.load()
    if not creds.is_logged_in:
        _fail(request, 30026)
        return
    if not item_id:
        _fail(request)
        return

    from kofin.sync.backends.api.paths import key_from_url
    from kofin.sync.backends.api.store import namespace

    key = key_from_url(request.base_url)
    if key and key != namespace(creds.server_id, creds.user_id):
        _fail(request)
        return
    # Play Next's hint is spent by this play whichever way it goes, so a
    # later play of the item asks.
    followed = state.followed_version(item_id)
    # A play from a library row: its URL is the provider's, or names the row
    # outright. Only such a play resumes at Kodi's bookmark
    # (resume_start_ticks); the native id found below is stamped on every
    # synced item's resolved tag, a listing's included.
    from_library = bool(key) or request.params.get("dbid", "").isdigit()

    # Before any transport is built: offline, everything below is a wait
    # with a known answer.
    if offline_answer(request, item_id, from_library):
        return

    # A download the viewer already has beats the network, and a synced
    # item's catalogue copy is DTO enough to claim it with: no request is
    # made for a play that needs none, so a server that has stopped
    # answering, unnoticed yet, costs the play nothing.
    local_path = None if stream_requested(request) else downloaded_file(item_id)
    if local_path:
        item = catalogue_item(item_id)
        if item is not None:
            resolve_downloaded(
                request,
                item,
                local_path,
                creds.server_address,
                creds.device_id,
                download_start_ticks(request, item, from_library),
                request.params.get("dbid", "") if from_library else "",
                None,
            )
            return

    transcode = request.params.get(PARAM_TRANSCODE) == "1"
    try:
        bitrate_mbps = float(request.params.get(PARAM_BITRATE, "0"))
    except ValueError:
        bitrate_mbps = 0.0

    api = Api.for_plugin(creds, abort=stop)
    http = api.http
    # The media-segments prefetch shares nothing with PlaybackInfo or the
    # subtitle fetches, so it runs beside them instead of after them and its
    # round trip leaves the resolve's critical path. The
    # item fetch stays ahead of PlaybackInfo on the main thread: StartTimeTicks
    # needs the resume position, which in the server-resume case only the item
    # DTO knows. prefetch_segments catches its own failures (None), so the
    # join can only yield segments or the service-side fallback. Daemon and
    # bounded (interactive Api budget), so an abandoned fail path leaks
    # nothing but a finishing request.
    segments_box: list[Optional[list[JsonDict]]] = []
    segments_thread: Optional[threading.Thread] = None
    opened_live_stream = ""
    try:
        try:
            item = api.item(item_id)
        except Abandoned:
            # A fetch the stop cut short is no outage to play around: the
            # play ends here, below.
            raise
        except JellyfinError as error:
            if not local_path:
                raise
            # The download is on disk and the server is not answering: the
            # play goes ahead on what the download row knows.
            LOG.debug(
                "item fetch failed (%s); playing the download of %s", error, item_id
            )
            item = download_item(item_id)
        if item.get("Type") in NATIVE_MEDIA:
            from kofin.sync.backends.api.identity import native_id_for

            try:
                native_id = native_id_for(item_id, NATIVE_MEDIA[item["Type"]])
            except Exception:
                LOG.warning(
                    "native identity unavailable; resolving by Jellyfin identity"
                )
                native_id = None
            if native_id is not None:
                request.params["dbid"] = str(native_id)
            else:
                request.params.pop("dbid", None)
        if not local_path and not request.params.get(PARAM_MEDIA_SOURCE):
            chosen = versions.choose(
                item, request.params.get(PARAM_UNATTENDED) == "1", followed
            )
            if chosen is None:
                LOG.debug("no version chosen for %s", item_id)
                _unresolved(request)
                return
            if chosen:
                request.params[PARAM_MEDIA_SOURCE] = chosen
        source_id = request.params.get(PARAM_MEDIA_SOURCE) or item_id
        segments_thread = threading.Thread(
            target=lambda: segments_box.append(prefetch_segments(api, item, source_id)),
            name="kofin-segments-prefetch",
            daemon=True,
        )
        segments_thread.start()
        from_start = request.params.get("fromstart") == "1"
        dbid = request.params.get("dbid", "")
        start_ticks = 0
        if request.resume and not from_start:
            start_ticks = resume_start_ticks(item, dbid if from_library else "")
        # An explicit start position wins over resume/fromstart: SyncPlay
        # group starts say exactly where the group timeline is.
        try:
            start_ticks = int(request.params.get("startticks") or start_ticks)
        except ValueError:
            pass
        channel = item.get("Type") == "TvChannel"
        if channel:
            # Live has no position to start at: the opened live stream
            # begins at its edge, and a group position on a live item is a
            # live-clock anchor, never a stream offset.
            start_ticks = 0

        # A download of an item the catalogue does not hold: the claim needs
        # the item DTO, so it is resolved here, with the start position.
        if local_path:
            segments = _joined_segments(segments_thread, segments_box)
            # The download is handed on without the checks further down, so
            # it takes the last look here, after the last wait.
            if stop():
                _abandon(
                    request,
                    creds,
                    opened_live_stream,
                    item_id,
                    "stopped before the download was handed on",
                )
                return
            resolve_downloaded(
                request,
                item,
                local_path,
                api.server,
                creds.device_id,
                start_ticks,
                dbid,
                segments,
            )
            return

        config = deviceprofile.ProfileConfig.from_settings()
        profile = deviceprofile.build(
            config,
            bitrate_override_mbps=bitrate_mbps,
            force_transcode=transcode,
            burn_subtitles=request.params.get(PARAM_BURN_SUBS) == "1",
        )
        # The stream indices only bind when MediaSourceId travels with them;
        # without it the server silently answers its own default. The first
        # call cannot name a source it has not seen yet, so a request that
        # selects streams states which source it is selecting them on.
        wanted_source = request.params.get(PARAM_MEDIA_SOURCE) or ""
        audio_index = _stream_index(request.params.get(PARAM_AUDIO_INDEX))
        subtitle_index = _stream_index(request.params.get(PARAM_SUBTITLE_INDEX))
        info = api.playback_info(
            item_id,
            profile,
            start_ticks=start_ticks,
            audio_index=audio_index,
            subtitle_index=subtitle_index,
            media_source_id=wanted_source or None,
            # Direct play would hand Kodi a channel's provider stream, a TS
            # stream or a sliding playlist its demuxer cannot seek.
            enable_direct_play=not channel,
        )
        sources = info.get("MediaSources") or []
        if not sources:
            raise JellyfinError("no media sources for %s" % item_id)
        source = pick_media_source(sources, wanted_source)
        opened_live_stream = source.get("LiveStreamId") or ""
        play_session_id = info.get("PlaySessionId", "")
        url, method = stream_url(
            api.server, item, source, creds.device_id, play_session_id
        )
        is_audio = item.get("Type") in AUDIO_TYPES
        is_live = channel or bool(source.get("IsInfiniteStream"))
        if method == "Transcode" and not is_audio and not is_live:
            # The bitrate the user asked for is the budget, whether it came from
            # the context item or the setting: the server reserves its own audio
            # share off that cap, so the split is recomputed to keep audio
            # proportional to the budget rather than to the source. Nothing caps
            # this against the source bitrate.
            #
            # Music is exempt: its transcode is already sized by
            # MusicStreamingTranscodingBitrate, and the video audio share would
            # otherwise overwrite that with an unrelated number.
            #
            # Force remux is codec-copy: do not rewrite the bitrates (that is
            # what refuses an E-AC3 copy) and do not deny copy. Transcode
            # wins when both are set.
            force_xcode = transcode or config.force_transcode
            remux_copy = config.force_remux and not force_xcode
            budget = int(profile["MaxStreamingBitrate"])
            if not remux_copy and budget < deviceprofile.UNLIMITED_BITRATE:
                url = rewrite_bitrates(url, budget, config.audio_bitrate_kbps)
            if force_xcode:
                url = deny_video_stream_copy(url)
                url = deny_audio_stream_copy(url)
    except Abandoned as error:
        _abandon(request, creds, opened_live_stream, item_id, str(error))
        return
    except JellyfinError as error:
        LOG.warning("play resolve failed for %s: %s", item_id, error)
        _close_live_stream(api, opened_live_stream)
        _fail(request)
        return

    try:
        LOG.debug("play %s via %s%s", item_id, method, " (live)" if is_live else "")
        # A resume point on the *resolved* item overrides the choice the user made
        # at Kodi's resume prompt: Kodi treats a resolved item that carries one as
        # a resume regardless of the resume:true|false it just passed us, and then
        # seeks — to the item's own point, or, when that point has no time on it,
        # to the bookmark in Kodi's database. Nor can the point be cleared once
        # stamped, so the play route states its start position up front and 0
        # means the item is built without one.
        li = listitems.build(item, api.server, resume_seconds=start_ticks / 10_000_000)
        # Library-item paths carry the Kodi database id;
        # stamping it on the tag links the playback to the library row for
        # widgets invoked outside a library window.
        if dbid.isdigit() and item.get("Type") in ("Movie", "Episode", "MusicVideo"):
            li.getVideoInfoTag().setDbId(int(dbid))
        elif dbid.isdigit() and is_audio:
            # setResolvedUrl replaces the library item's music tag wholesale, so
            # the song's database id has to be restated or the link back to the
            # Kodi row is lost for anything reading the tag.
            li.getMusicInfoTag().setDbId(int(dbid), "song")
        chapters = chapter_art(api, item, source, method)
        if chapters:
            li.setArt(chapters)
        if not is_audio:
            previews = scrub_previews(api, item, source, method)
            if previews:
                hand_over_scrub_previews(li, previews)
        li.setPath(url)
        mime = mime_for(source, method)
        if mime:
            li.setMimeType(mime)
        li.setContentLookup(False)
        if is_live:
            li.setProperty(REALTIME_PROPERTY, "true")
        # On a transcode this is the *only* way any subtitle reaches the screen —
        # the transcoded stream carries none. The attached order is what the
        # stream menu's ordinals map through (subtitles.localize).
        attached = streams.attached_subtitles(
            api.server, source, method, kodirpc.preferred_subtitle_language()
        )
        localized = (
            subtitles.localize(http, attached)
            if attached
            else subtitles.Localized([], [])
        )
        if localized.files:
            li.setSubtitles([path for _attachment, path in localized.files])

        play_item = play_state(
            item,
            source,
            url,
            method,
            play_session_id,
            creds.device_id,
            start_ticks / 10_000_000,
            attached=[attachment.stream_index for attachment, _path in localized.files],
            deferred=localized.deferred,
            fetchable=streams.fetchable_subtitles(api.server, source),
            request_params=request.params,
        )
        if channel:
            # The engine's spelling of live for kofin's own claim
            # (syncplay/utils.py::claim_is_live): what makes the group position
            # a source-clock anchor rather than a stream offset. A recording
            # still being written is not live: its playlist starts where the
            # recording does, so the player's time is a position in it, as
            # pvr.kofin claims it.
            play_item["Live"] = True
        segments = _joined_segments(segments_thread, segments_box)
        if segments is not None:
            play_item["Segments"] = segments
        # Last look before anything is handed on: a subtitle fetch the stop
        # cuts short ends without an error, so nothing above has noticed it,
        # and a play queued or resolved now is one nobody will watch.
        if stop():
            _abandon(
                request, creds, opened_live_stream, item_id, "stopped after the fetches"
            )
            return
        state.push_play_item(play_item)
    except Exception:
        # Nothing will play or report what PlaybackInfo opened.
        _close_live_stream(api, opened_live_stream)
        raise

    _resolve_to(request, li, url)


def _stop_check() -> Callable[[], bool]:
    """Whether Kodi has asked this resolve to stop: the viewer cancelled its
    busy dialog, or Kodi is going down. For a play reached without the check
    default.py makes before its imports.

    Kodi's GUI thread waits up to five seconds for a script it stops, and for
    every thread that script started, so each step the resolve takes after
    the stop is a step of frozen GUI. Kodi raises the flag only on the
    Monitors alive when it stops the script
    (``XBPython::NotifyScriptAborting``): one made after a cancel never hears
    it, which is why default.py makes a play's first.
    """
    return xbmc.Monitor().abortRequested


# How long a stopped play's live-stream close may take, start to finish. Kodi's
# GUI is waiting for the thread that sends it, so it is a deadline rather than
# a connect and a read budget, which a server can stretch by answering slowly.
# A server that answers at all answers a close in a round trip.
CLOSE_DEADLINE_SECONDS = 2.0


def _abandon(
    request: Request,
    creds: Credentials,
    live_stream_id: str,
    item_id: str,
    reason: str,
) -> None:
    """A resolve Kodi stopped: the handle answered with nothing, a live stream
    PlaybackInfo opened closed, and no toast — the viewer asked for this.
    ``reason`` says where the stop caught it: the request cut short or not
    sent, or the last look before the hand-off."""
    LOG.debug("play %s abandoned (%s)", item_id, reason)
    if live_stream_id:
        # On a transport of its own: the route's sends nothing once the stop
        # is raised, and this has to reach the server to free the tuner. Its
        # own stop check is the deadline, so the watcher that cuts a stopped
        # request cuts this one when the deadline passes; a close that fails
        # is only logged.
        deadline = time.monotonic() + CLOSE_DEADLINE_SECONDS
        closer = Api.for_plugin(creds, abort=lambda: time.monotonic() > deadline)
        _close_live_stream(closer, live_stream_id, LEAVE_TIMEOUT)
    _unresolved(request)


def _close_live_stream(
    api: Api, live_stream_id: str, timeout: Optional[tuple[float, float]] = None
) -> None:
    """Close a live stream PlaybackInfo opened for a play that will not
    happen: the server keeps it, and the tuner behind it, until a session
    report names it or it is closed."""
    if not live_stream_id:
        return
    try:
        api.close_live_stream(live_stream_id, timeout=timeout)
    except Exception as error:
        LOG.warning("live stream close failed: %s", error)


def _unresolved(request: Request) -> None:
    """Answer the handle, when there is one, with nothing to play."""
    if request.handle >= 0:
        xbmcplugin.setResolvedUrl(request.handle, False, xbmcgui.ListItem())


def _fail(request: Request, message_id: int = 30018) -> None:
    """A failed resolve: the handle answered with nothing, and a toast that
    says why — the server, or (30720) an offline play with no download."""
    _unresolved(request)
    toast.show(settings.localized(message_id), toast.ERROR, time_ms=4000)
