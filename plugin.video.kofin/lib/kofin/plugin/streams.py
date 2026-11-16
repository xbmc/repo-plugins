"""Audio and subtitle selection for a playback already running.

Reached from the context menu on the played item, which the viewer gets back
to by pressing Back or Tab — fullscreen video itself has no context menu, but
leaving it does not stop playback, and the item stays focused with
``ListItem.IsPlaying`` true.

Three kinds of change, and the differences are the whole reason this module
exists. A subtitle Kodi already holds — anything embedded on a direct play,
anything attached as a file — switches in place, instantly. A text subtitle a
transcode did not attach is fetched from the server and added to the running
playback, which costs a wait but no gap: this module states the index and the
service does the waiting (:func:`_fetch_subtitle`). Only two things still
resolve a new stream, because only they cannot be answered any other way —
audio on a transcode, since Jellyfin bakes one track into the HLS output and
offers no alternates, and an image subtitle on a transcode, which can only
reach the screen burned into the video.

No API call happens here. Everything the menus show was resolved by the play
route's own PlaybackInfo and published when the service claimed the playback,
so the menu is complete before the first frame and opening it costs nothing.
"""

from typing import Any, NamedTuple, Optional, Union
from urllib.parse import parse_qsl, urlparse

import xbmc
import xbmcgui

from kofin.core import ipc, kodirpc, settings, state, streams, toast
from kofin.core.log import Logger
from kofin.core.urls import (
    PARAM_AUDIO_INDEX,
    PARAM_BITRATE,
    PARAM_BURN_SUBS,
    PARAM_MEDIA_SOURCE,
    PARAM_SUBTITLE_INDEX,
    PARAM_TRANSCODE,
    plugin_url,
)
from kofin.plugin.router import Request

LOG = Logger(__name__)

JsonDict = dict[str, Any]

# Kodi's own wording for the headings and for "no subtitle", so the menu reads
# like the player's rather than like an addon's.
STR_AUDIO_STREAM = 460
STR_SUBTITLES = 287
STR_NONE = 231


class Playing(NamedTuple):
    """What the picture is actually made of right now.

    Not what the playback was resolved with: Kodi's own menus move both tracks
    without kofin hearing of it, and a burned-in subtitle is not a track at all
    (see :func:`_playing`). Every menu marks its rows against this, and a
    restart reproduces it with one field replaced — which is what keeps a
    burned-in subtitle through an audio change, and the audio track through a
    burn-in.
    """

    audio: Optional[int]
    subtitle: Optional[int]
    burned: bool


def _playing(
    payload: JsonDict, media_streams: list[JsonDict], attached: list[int], method: str
) -> Playing:
    audio = payload.get("AudioStreamIndex")
    if streams.is_direct(method):
        # A transcode has one audio track by construction, so the resolved
        # index is the only answer there. Direct play is the opposite: Kodi
        # holds them all and its own menu can have moved.
        live = streams.audio_index_at(media_streams, kodirpc.current_audio())
        if live is not None:
            audio = live

    wanted = payload.get("SubtitleStreamIndex")
    if streams.burned_subtitle(media_streams, wanted, method):
        return Playing(audio, wanted, True)
    return Playing(
        audio, _current_subtitle_index(media_streams, attached, method), False
    )


def _row_of(index: Optional[int], rows: list[Optional[int]]) -> int:
    """Which row to put the cursor on, or -1 for none.

    Kodi's own stream dialogs open on the running track; marking it in the text
    and then opening on row 0 is half the job.
    """
    return rows.index(index) if index in rows else -1


def menu(request: Request) -> None:
    """``mode=streams``: the same menu, for anything driving it by URL."""
    context_menu()


def context_menu() -> None:
    """The context item: pick a stream for the running playback."""
    payload = state.playing_streams()
    if not payload:
        LOG.warning("stream menu invoked with no published playback")
        return

    media_streams: list[JsonDict] = payload.get("MediaStreams") or []
    attached: list[int] = payload.get("Attached") or []
    method = str(payload.get("PlayMethod") or "")

    audio = streams.of_type(media_streams, "Audio")
    subtitles = streams.selectable_subtitles(media_streams)
    offer = streams.menu_offer(media_streams)
    if offer == streams.OFFER_NONE:
        return

    # One kind on offer goes straight to its list — asking "audio or
    # subtitles?" when only one answer exists is a click for nothing. With both
    # on offer that question is worth asking, and it is the second popup the
    # single menu entry implies.
    if offer == streams.OFFER_BOTH:
        kind = xbmcgui.Dialog().contextmenu(
            [
                xbmc.getLocalizedString(STR_AUDIO_STREAM),
                xbmc.getLocalizedString(STR_SUBTITLES),
            ]
        )
        if kind < 0:
            return
        offer = streams.OFFER_AUDIO if kind == 0 else streams.OFFER_SUBTITLE

    playing = _playing(payload, media_streams, attached, method)

    if offer == streams.OFFER_AUDIO:
        _choose_audio(payload, audio, media_streams, method, playing)
    else:
        _choose_subtitle(payload, subtitles, media_streams, attached, method, playing)


# -- audio -------------------------------------------------------------------


def _choose_audio(
    payload: JsonDict,
    audio: list[JsonDict],
    media_streams: list[JsonDict],
    method: str,
    playing: Playing,
) -> None:
    labels: list[Union[str, xbmcgui.ListItem]] = [
        streams.label_for(stream, stream.get("Index") == playing.audio)
        for stream in audio
    ]
    index = xbmcgui.Dialog().select(
        xbmc.getLocalizedString(STR_AUDIO_STREAM),
        labels,
        preselect=_row_of(playing.audio, [stream.get("Index") for stream in audio]),
    )
    if index < 0:
        return
    chosen = audio[index]
    if chosen.get("Index") == playing.audio:
        return  # already playing; nothing worth a restart

    if streams.is_direct(method):
        # The tracks are all in the stream Kodi opened, so this is a switch,
        # not a new playback.
        ordinal = streams.audio_ordinal(media_streams, chosen.get("Index"))
        if ordinal is None:
            return
        xbmc.Player().setAudioStream(ordinal)
        LOG.debug("audio -> jellyfin %s (kodi %s)", chosen.get("Index"), ordinal)
        return

    _restart(payload, playing._replace(audio=chosen.get("Index")))


# -- subtitles ---------------------------------------------------------------


def _choose_subtitle(
    payload: JsonDict,
    subtitles: list[JsonDict],
    media_streams: list[JsonDict],
    attached: list[int],
    method: str,
    playing: Playing,
) -> None:
    if not subtitles:
        return
    rows: list[tuple[Optional[JsonDict], str]] = [
        (
            None,
            streams.label_for(
                {"DisplayTitle": xbmc.getLocalizedString(STR_NONE)},
                playing.subtitle is None,
            ),
        )
    ]
    for stream in subtitles:
        active = stream.get("Index") == playing.subtitle
        label = streams.label_for(stream, active)
        if not active:
            # Two kinds of row cost something on a transcode, and they are
            # labelled apart. An image subtitle can only reach the screen as
            # pixels in the video, so it costs a new stream. A text one that
            # was not attached (only the resolved track is — see
            # streams.attached_subtitles) costs a download and nothing else:
            # the service fetches it onto the running playback. The row already
            # on screen has nothing left to warn about either way.
            if streams.burns_in(stream, method):
                label = "%s (%s)" % (label, settings.localized(30617))
            elif streams.needs_fetch(stream, method, attached):
                label = "%s (%s)" % (label, settings.localized(30775))
        rows.append((stream, label))

    labels: list[Union[str, xbmcgui.ListItem]] = [label for _, label in rows]
    index = xbmcgui.Dialog().select(
        xbmc.getLocalizedString(STR_SUBTITLES),
        labels,
        preselect=_row_of(
            playing.subtitle,
            [None if stream is None else stream.get("Index") for stream, _ in rows],
        ),
    )
    if index < 0:
        return
    chosen = rows[index][0]

    if chosen is None:
        if playing.burned:
            # Nothing can turn this one off: it is in the picture, not in a
            # track. Only a stream without it is an answer.
            _restart(payload, playing._replace(subtitle=None, burned=False))
            return
        xbmc.Player().showSubtitles(False)
        LOG.debug("subtitles off")
        return
    if chosen.get("Index") == playing.subtitle:
        return  # already on screen; never pay anything to arrive where we are
    if streams.burns_in(chosen, method):
        # The only row left that costs a new stream. ``burned=True`` is what
        # puts ``burnsubs=1`` on the restart, and only an image subtitle wants
        # that.
        _restart(payload, playing._replace(subtitle=chosen.get("Index"), burned=True))
        return
    if streams.needs_fetch(chosen, method, attached):
        _fetch_subtitle(chosen)
        return
    ordinal = streams.subtitle_ordinal(
        media_streams, chosen.get("Index"), attached, method
    )
    if ordinal is None:
        return
    player = xbmc.Player()
    player.setSubtitleStream(ordinal)
    player.showSubtitles(True)
    LOG.debug("subtitle -> jellyfin %s (kodi %s)", chosen.get("Index"), ordinal)


def _current_subtitle_index(
    media_streams: list[JsonDict], attached: list[int], method: str
) -> Optional[int]:
    """The Jellyfin index of the subtitle Kodi is showing, or None.

    Asked of the player rather than remembered, because Kodi's own subtitle
    menu can change it behind this module's back.
    """
    current = kodirpc.current_subtitle()
    if current is None:
        return None
    for stream in streams.of_type(media_streams, "Subtitle"):
        if (
            streams.subtitle_ordinal(
                media_streams, stream.get("Index"), attached, method
            )
            == current
        ):
            return stream.get("Index")
    return None


def _fetch_subtitle(chosen: JsonDict) -> None:
    """Ask the service for a text track the transcode did not attach.

    Not done here: fetching it means waiting on an ffmpeg extraction the
    server runs on demand, which can take minutes, and this process is a
    plugin invocation that has to return. The service owns the running
    playback and can wait (``service/latesubs.py``), so this states the index
    and exits.
    """
    index = chosen.get("Index")
    if index is None:
        return
    LOG.debug("subtitle %s requested; asking the service to fetch it", index)
    toast.show(settings.localized(30776), time_ms=4000)
    ipc.notify(ipc.ATTACH_SUBTITLE, {"Index": int(index)})


# -- restart -----------------------------------------------------------------


def _restart(payload: JsonDict, playing: Playing) -> None:
    """Resolve a new stream that is ``playing``, and pick up where we were.

    Every field is stated, not just the one the viewer changed: the server
    resolves what it is not told from the user's profile.

    The position is stated in the params rather than left to PlayMedia's
    resume flag (context.play_with_transcode says why), and the originating
    request's own params are carried forward (play.play_state).
    """
    item_id = str(payload.get("Id") or "")
    if not item_id:
        return
    position = _current_position()
    request = payload.get("Request") or {}

    params: dict[str, str] = {"mode": "play", "id": item_id}
    for key in (PARAM_TRANSCODE, PARAM_BITRATE, "dbid", PARAM_MEDIA_SOURCE):
        value = request.get(key)
        if value:
            params[key] = str(value)
    if not params.get(PARAM_MEDIA_SOURCE) and payload.get("MediaSourceId"):
        params[PARAM_MEDIA_SOURCE] = str(payload["MediaSourceId"])
    if not params.get("dbid"):
        # Play Next builds its own URL and carries no dbid, so a restart of an
        # autoplayed episode would drop the library link. Kodi's own playing
        # path still has it.
        dbid = _playing_dbid()
        if dbid:
            params["dbid"] = dbid
    if playing.audio is not None:
        params[PARAM_AUDIO_INDEX] = str(playing.audio)
    # -1 is "no subtitle" (play._stream_index).
    params[PARAM_SUBTITLE_INDEX] = str(
        playing.subtitle if playing.subtitle is not None else -1
    )
    if playing.burned:
        params[PARAM_BURN_SUBS] = "1"
    if position > 0:
        params["startticks"] = str(int(position * 10_000_000))
    else:
        params["fromstart"] = "1"

    LOG.debug(
        "restarting %s at %.1fs (audio=%s subtitle=%s burn=%s)",
        item_id,
        position,
        playing.audio,
        playing.subtitle,
        playing.burned,
    )
    # Nothing here reports the stop: the restart replaces the playback, and the
    # player's own onPlayBackStopped finalize() posts the position and closes
    # the outgoing transcode session before the new one claims.
    toast.show(settings.localized(30616), time_ms=4000)
    xbmc.executebuiltin("PlayMedia(%s)" % plugin_url(params))


def _current_position() -> float:
    try:
        return max(float(xbmc.Player().getTime()), 0.0)
    except RuntimeError:  # playback ended between opening the menu and choosing
        return 0.0


def _playing_dbid() -> str:
    try:
        return dbid_from_path(xbmc.Player().getPlayingFile())
    except RuntimeError:
        return ""


def dbid_from_path(path: str) -> str:
    """The ``dbid`` a kofin play URL carries, or ''."""
    try:
        query = dict(parse_qsl(urlparse(path).query))
    except ValueError:
        return ""
    dbid = query.get("dbid", "")
    return dbid if dbid.isdigit() else ""
