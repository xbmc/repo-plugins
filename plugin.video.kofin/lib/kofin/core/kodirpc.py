"""JSON-RPC calls into Kodi, shared by both processes."""

import json
from typing import Any, Optional
from collections.abc import Sequence

import xbmc

from kofin.core.log import Logger

LOG = Logger(__name__)

STOP_POLL_SECONDS = 0.05


class _Failed:
    """The type of ``FAILED``; nothing else is ever this."""

    def __repr__(self) -> str:  # pragma: no cover - repr only
        return "<kodirpc.FAILED>"


# What ``call`` answers when Kodi could not be asked at all — the call
# raised, or the reply would not parse. Distinct from a method-level error
# reply (Kodi answered, refusing), which ``call`` maps to None.
FAILED: Any = _Failed()

# Kodi media type -> (JSON-RPC method, id parameter, result key). The three
# video types kofin syncs; songs carry no resume point.
RESUME_QUERY = {
    "movie": ("VideoLibrary.GetMovieDetails", "movieid", "moviedetails"),
    "episode": ("VideoLibrary.GetEpisodeDetails", "episodeid", "episodedetails"),
    "musicvideo": (
        "VideoLibrary.GetMusicVideoDetails",
        "musicvideoid",
        "musicvideodetails",
    ),
}


def player_properties(
    properties: list[str], playerid: Optional[int] = None
) -> Optional[dict[str, Any]]:
    """Properties of player ``playerid``, or of whichever player is active;
    None when Kodi did not answer them."""
    if playerid is None:
        active = active_players()
        if not isinstance(active, list) or not active:
            return None
        playerid = active[0]["playerid"]
    result = call(
        "Player.GetProperties",
        {"playerid": playerid, "properties": properties},
    )
    return result if isinstance(result, dict) else None


def current_subtitle() -> Optional[int]:
    """Kodi's number for the subtitle on screen, or None when none is.

    Read over JSON-RPC rather than through ``Player.getSubtitles()``, which
    answers with the track's *name*: every subtitle kofin attaches as a file is
    named "Stream (External)" — Jellyfin's delivery route has a fixed filename
    — so looking a name up in the available list finds whichever came first.
    Only the index distinguishes them.
    """
    try:
        result = player_properties(["currentsubtitle", "subtitleenabled"])
        if result is None or not result.get("subtitleenabled"):
            return None
        index = result.get("currentsubtitle", {}).get("index")
        return int(index) if index is not None else None
    except Exception as error:
        LOG.debug("current subtitle read failed: %s", error)
        return None


def current_audio() -> Optional[int]:
    """Kodi's number for the audio track being heard, or None.

    Asked for the same reason as the subtitle above: on a direct play Kodi's
    own audio menu switches tracks without kofin hearing of it, so the index
    the playback was resolved with is not necessarily the one playing, and a
    menu that marks it as current would be marking the wrong row.
    """
    try:
        result = player_properties(["currentaudiostream"])
        if result is None:
            return None
        index = (result.get("currentaudiostream") or {}).get("index")
        return int(index) if index is not None else None
    except Exception as error:
        LOG.debug("current audio read failed: %s", error)
        return None


def stop_player(wait_seconds: float = 0.0) -> bool:
    """Stop whatever is playing, without holding Python's GIL while Kodi does it.

    **Never call ``xbmc.Player.stop()``.** Kodi's binding for it is
    ``SendMsg(TMSG_MEDIA_STOP)`` with no ``DelayedCallGuard``, so the calling
    thread blocks on the app thread *holding the GIL* — unlike ``playnext``,
    ``playprevious`` and ``play``, which all wrap the same send in the guard.
    The app thread's stop path ends in ``~CVideoPlayer()``, which spins until
    its outbound job queue drains, and the two jobs ahead of ``OnPlayBackStopped``
    both write MyVideos. Kodi's SQLite busy handler sleeps and retries forever,
    so if any kofin thread is holding the MyVideos write lock it can never be
    released — that thread needs the GIL this one is sitting on. Kodi is then
    wedged on a blank screen with only a force-stop to get out.

    ``executeJSONRPC`` carries the guard Kodi forgot on ``stop()``, and
    ``Player.Stop`` is a ``PostMsg`` on Kodi's side, so this returns in
    microseconds and no other Python thread ever stalls behind it.

    Being asynchronous is the one behaviour change: playback is *requested* to
    stop, not stopped. Anything Kodi sequences for us needs no wait — the app
    thread runs its messages in order, so a ``player.play()`` issued afterwards
    is handled after the stop. ``wait_seconds`` is for callers that must not
    race the teardown from the Python side. Note it can only ever be a
    courtesy: ``Player.GetActivePlayers`` goes empty while ``~CVideoPlayer()``
    is still running, so an empty answer means "Kodi has let go of the
    player", not "the teardown has finished".

    Returns True when a stop was asked for.
    """
    active = active_players()
    if not isinstance(active, list):
        LOG.warning("could not read the active players to stop them: %r", active)
        return False

    if not active:
        return False

    # Every active player by id, rather than a hardcoded 1: SyncPlay drives
    # music as well as video, and Player.Stop answers FailedToExecute for a
    # playerid that is not playing.
    for player in active:
        try:
            player_id = int(player["playerid"])
        except Exception as error:
            LOG.warning("stop failed for player %r: %s", player, error)
            continue
        if call("Player.Stop", {"playerid": player_id}) is FAILED:
            LOG.warning("stop failed for player %r", player)

    if wait_seconds > 0:
        monitor = xbmc.Monitor()
        waited = 0.0
        while waited < wait_seconds:
            if monitor.waitForAbort(STOP_POLL_SECONDS):
                break
            waited += STOP_POLL_SECONDS
            still = active_players()
            if not isinstance(still, list):
                LOG.debug("player poll failed while waiting for the stop: %r", still)
                break
            if not still:
                break

    return True


def resume_player() -> bool:
    """Set every active player *playing*, by intent rather than by toggling.

    ``xbmc.Player.pause()`` is a toggle and it lands asynchronously, so
    "toggle it if it reads paused" is two races stacked: the read can predate a
    pause still in flight, and the toggle then arrives while the player is
    already moving the other way. ``Player.PlayPause`` takes an explicit
    ``play`` flag, which has no state to race: asking for playing while
    already playing is a no-op.

    This only *asks*. Confirming is the caller's job and cannot be done from
    ``speed``, which reads 1 for a player that is not advancing — the position
    sampled twice is the only proof. The SyncPlay controller's
    ``_resume_and_verify`` does that, and re-asks, because the failure being
    guarded is another thread's pause landing after this call.

    Returns True when the request went out (or no player was active).
    """
    return _set_playing(True)


def pause_player() -> bool:
    """Set every active player *paused*, by intent as :func:`resume_player`
    sets it playing: asking for paused while already paused is a no-op, where
    ``xbmc.Player.pause()`` would resume it.

    Returns True when the request went out (or no player was active).
    """
    return _set_playing(False)


def _set_playing(play: bool) -> bool:
    verb = "resume" if play else "pause"
    active = active_players()
    if not isinstance(active, list):
        LOG.warning("could not read the active players to %s them: %r", verb, active)
        return False

    if not active:
        return True

    for player in active:
        try:
            player_id = int(player["playerid"])
        except Exception as error:
            LOG.warning("%s failed for player %r: %s", verb, player, error)
            continue
        if call("Player.PlayPause", {"playerid": player_id, "play": play}) is FAILED:
            LOG.warning("%s failed for player %r", verb, player)

    return True


def resume_point(kodi_id: int, media: str) -> Optional[tuple[float, float]]:
    """Kodi's stored ``(position, total)`` for a library row, or None.

    Position 0.0 is an answer, not a failure — the row has no bookmark.
    None only when the row cannot be read at all. Total is 0.0 when the
    payload omits it, so a resolved item still refuses to stamp.
    """
    query = RESUME_QUERY.get(media)
    if query is None:
        return None
    method, id_field, result_field = query
    result = call(method, {id_field: kodi_id, "properties": ["resume"]})
    try:
        resume = result[result_field]["resume"]
        return float(resume["position"]), float(resume.get("total") or 0)
    except Exception as error:
        LOG.debug("resume read failed for %s/%s: %s", media, kodi_id, error)
        return None


def resume_seconds(kodi_id: int, media: str) -> Optional[float]:
    """Kodi's stored resume position for a library row: :func:`resume_point`'s
    position alone."""
    point = resume_point(kodi_id, media)
    return None if point is None else point[0]


def preferred_subtitle_language() -> str:
    """Kodi's configured subtitle language as an ISO 639-2 code, or ''.

    The setting holds a display name ("English"), or one of Kodi's own words:
    ``original`` and ``default`` defer to the media or the UI language, and
    ``none``/``forced_only`` mean the viewer does not want a subtitle chosen
    for them — all of which answer '' here, since none of them names a track
    to prefer.
    """
    result = call("Settings.GetSettingValue", {"setting": "locale.subtitlelanguage"})
    if not isinstance(result, dict) or "value" not in result:
        LOG.debug("subtitle language unavailable: %r", result)
        return ""
    value = str(result["value"])
    if value.lower() in ("", "none", "forced_only", "original"):
        return ""
    if value.lower() == "default":
        return str(xbmc.getLanguage(xbmc.ISO_639_2) or "")
    return str(xbmc.convertLanguage(value, xbmc.ISO_639_2) or "")


def call(method: str, params: Optional[dict[str, Any]] = None) -> Any:
    """One JSON-RPC call's ``result`` — whatever shape the method answers
    with (``Settings.SetSettingValue`` answers a bare ``true``); None for a
    method-level error reply (Kodi answered, refusing); ``FAILED`` when Kodi
    could not be asked at all or answered unparseably."""
    request: dict[str, Any] = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    except Exception:
        return FAILED
    if not isinstance(response, dict):
        return FAILED
    if "error" in response:
        return None
    return response.get("result")


def batch(requests: Sequence[tuple[str, Optional[dict[str, Any]]]]) -> list[Any]:
    """Several calls in one ``executeJSONRPC``, answered in request order.

    Each entry is that call's ``result``, None for a method-level error reply
    and ``FAILED`` when Kodi could not be asked at all -- the same three
    answers as :func:`call`. Kodi's dispatcher runs the requests one by one
    and does not wrap them in a transaction, so a mixed batch is partly
    applied and the caller reads every entry.
    """
    if not requests:
        return []
    body: list[dict[str, Any]] = []
    for index, (method, params) in enumerate(requests):
        request: dict[str, Any] = {"jsonrpc": "2.0", "id": index + 1, "method": method}
        if params is not None:
            request["params"] = params
        body.append(request)
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(body)))
    except Exception:
        return [FAILED] * len(requests)
    if not isinstance(response, list):
        return [FAILED] * len(requests)
    by_id = {reply.get("id"): reply for reply in response if isinstance(reply, dict)}
    results: list[Any] = []
    for index in range(len(requests)):
        reply = by_id.get(index + 1)
        if reply is None:
            results.append(FAILED)
        elif "error" in reply:
            results.append(None)
        else:
            results.append(reply.get("result"))
    return results


def active_players() -> Any:
    """``Player.GetActivePlayers``'s list, or whatever ``call`` answered."""
    return call("Player.GetActivePlayers")


def kodi_setting(setting_id: str) -> Any:
    """The value of one of Kodi's own settings; None where this Kodi lacks
    the setting; ``FAILED`` when Kodi could not be asked."""
    result = call("Settings.GetSettingValue", {"setting": setting_id})
    if result is FAILED:
        return FAILED
    return result.get("value") if isinstance(result, dict) else None


def clear_resume_bookmark(path: str) -> bool:
    """Delete the resume bookmark Kodi keeps for a plugin path.

    Kodi saves a bookmark for every video it stops, keyed on the listing
    row's own path (``original_listitem_url`` for a plugin item), and reads
    it back for any row whose tag carries no resume point of its own
    (VideoUtils.cpp ``GetNonFolderItemResumeInformation``). So zeroing the
    server's position is only half of a reset: the half Kodi holds has to go
    too, or the row advertises the stale local time the moment kofin stops
    stamping the server's.

    ``Files.SetFileDetails`` is the one JSON-RPC write that reaches a plugin
    path. It insists the file exists, and ``CPluginFile::Exists`` answers
    true for any ``plugin://``; a zero position makes it clear the bookmark
    rather than write one (VideoLibrary.cpp ``UpdateResumePoint``). It adds a
    ``files`` row when none exists, which is what Kodi does after any plugin
    play, so nothing new is left behind.

    False when Kodi refused or could not be reached; the caller has nothing
    to undo either way.
    """
    result = call(
        "Files.SetFileDetails",
        {"file": path, "media": "video", "resume": {"position": 0}},
    )
    if result is FAILED:
        LOG.debug("bookmark clear failed for %s", path)
        return False
    if result is None:
        LOG.debug("bookmark clear refused for %s", path)
        return False
    return True
