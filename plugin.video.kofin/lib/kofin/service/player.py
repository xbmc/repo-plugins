"""Playback reporting for kofin's own plays.

The player owns its progress ticker (10s cadence), so the service loop does no
playback polling. Foreign playback (anything not in the play queue) is ignored.
"""

from __future__ import annotations

import queue
import threading
from contextlib import AbstractContextManager
import time
from typing import TYPE_CHECKING, Any, Callable

import xbmc
import xbmcgui

from kofin.core import lyrics as lyrics_render
from kofin.core import ipc, kodirpc, settings, state, streams, toast
from kofin.core.api import Api
from kofin.downloads import auto as downloads_auto
from kofin.core.http import JellyfinError
from kofin.core.log import Logger
from kofin.service import latesubs
from kofin.service.libraryclaim import (
    downloaded_path,
    path_item_id,
    playing_jellyfin_id,
)
from kofin.service.segments import SegmentEngine
from kofin.service.ports import forward, spawn_once, no_modal

if TYPE_CHECKING:
    from kofin.syncplay.manager import SyncPlayManager

LOG = Logger(__name__)

JsonDict = dict[str, Any]

PROGRESS_INTERVAL_SECONDS = 10.0
PLUGIN_URL = "plugin://plugin.video.kofin/"
CLAIM_TIMEOUT_SECONDS = 10.0
# How often the service closes the live streams of plays Kodi never started
# (state.close_stale_live_streams).
LIVE_SWEEP_SECONDS = 15.0
# How long _claim waits for an audio or downloaded-video claim to be queued
# before calling the playback foreign.
BACKFILL_GRACE_SECONDS = 3.0

# How far into an item counts as having watched it, for the
# ``deleteAfterWatching`` offer. Jellyfin's own played threshold.
WATCHED_FRACTION = 0.9

# Item types the finished-watching delete offer applies to. A song or a music
# video reaching its end is not an invitation to delete anything.
DELETABLE_TYPES = ("Movie", "Episode")


def watched_to_end(item: JsonDict) -> bool:
    """True when this playback got close enough to the end to call it watched.

    Not "did Kodi fire onPlayBackEnded": Play Next autoplay hands over about a
    second before natural EOF, so the episode the viewer just finished ends as
    a *stopped* playback. A share of the runtime catches both, and matches the
    threshold the server itself uses to mark an item played. The last progress
    tick can be up to ``PROGRESS_INTERVAL_SECONDS`` stale, which at this
    threshold only matters for items under ~100 s.
    """
    runtime = float(item.get("Runtime") or 0) / 10_000_000
    if runtime <= 0:
        return False
    return float(item.get("CurrentPosition") or 0) >= runtime * WATCHED_FRACTION


KOFIN_LYRICS_ADDON = "script.kofin.lyrics"


def kofin_lyrics_installed() -> bool:
    """Whether script.kofin.lyrics is present to consume published lyrics."""
    return bool(xbmc.getCondVisibility("System.HasAddon(%s)" % KOFIN_LYRICS_ADDON))


def name_live_stream(data: JsonDict, item: JsonDict) -> None:
    """Name the play's live stream in a session report. Jellyfin closes a
    live stream, and frees the tuner behind it, at stop or when the session
    ends only when a report names it."""
    if item.get("LiveStreamId"):
        data["LiveStreamId"] = item["LiveStreamId"]


class _Reporter(threading.Thread):
    """One FIFO worker for every server-bound playback report.

    Kodi delivers player callbacks on its announcement thread, which every
    addon shares: a network call there stalls player and monitor callbacks
    for all of them, for the transport's whole budget, whenever the server is
    away. So callbacks capture their payload at event time — position and
    volume are read when the event happens, not when the network gets to it
    — and enqueue here, and this thread posts strictly in order: the server
    reads playing/progress/stopped as one session's story, and the single
    pipe is what keeps a stop from overtaking its start.
    """

    def __init__(self) -> None:
        super().__init__(name="kofin-reporter", daemon=True)
        self._jobs: queue.Queue[Callable[[], None] | None] = queue.Queue()

    def submit(self, job: Callable[[], None]) -> None:
        self._jobs.put(job)

    def flush(self, timeout: float = 5.0) -> bool:
        """True once everything queued before this call has run (tests)."""
        done = threading.Event()
        self._jobs.put(lambda: done.set())
        return done.wait(timeout)

    def stop(self, timeout: float = 5.0) -> None:
        self._jobs.put(None)
        if self.is_alive():
            self.join(timeout=timeout)
            if self.is_alive():  # pragma: no cover - watchdog logging only
                LOG.warning("reporter did not drain within its deadline")

    def run(self) -> None:
        while True:
            job = self._jobs.get()
            if job is None:
                break
            try:
                job()
            except Exception as error:
                LOG.warning("playback report failed: %s", error)


class Player(xbmc.Player):
    def __init__(
        self,
        api: Api,
        modal: Callable[[str], AbstractContextManager[None]] = no_modal,
    ) -> None:
        super().__init__()
        # The service's record of the dialogs it has open, closed at shutdown.
        self._modal = modal
        self.api = api
        self._item: JsonDict | None = None
        self._ticker: _Ticker | None = None
        self._lock = threading.Lock()
        # Driven by SyncPlay; while True, Play Next is withheld — the group
        # queue is authoritative.
        self._syncplay_group_active = False
        # The SyncPlay manager, attached by the service when built.
        self.syncplay: SyncPlayManager | None = None
        # One per player, reset per playback (service/segments.py).
        self.segments = SegmentEngine(self, api)
        # The auto-next one-shot: the item id whose trigger crossing already
        # fired, latched before the lookup so a failed resolve never retries.
        self._auto_next_latch = ""
        self._late_subs: latesubs.LateSubtitles | None = None
        self._reporter = _Reporter()
        self._reporter.start()
        self._last_live_sweep = 0.0
        # Raised by stop_threads, and every Kodi callback is ignored from then
        # on. Kodi calls a Player until the object is freed, and a stopped
        # generation outlives its run (Service.onNotification says why).
        self._stopped = False

    # A property so joining or leaving a group also withdraws or restores the
    # stream menu, without the SyncPlay manager having to know the menu exists:
    # it writes this attribute and nothing else. Changing audio means
    # restarting playback, which in a group would desync everyone else, so the
    # entry disappears.
    @property
    def syncplay_group_active(self) -> bool:
        return self._syncplay_group_active

    @syncplay_group_active.setter
    def syncplay_group_active(self, active: bool) -> None:
        self._syncplay_group_active = active
        item = self.current_item()
        if item is not None:
            self._publish_streams(item)

    # -- syncplay forwarding ---------------------------------------------------

    def _syncplay_event(self, name: str, *args: Any) -> None:
        """Forward a player callback to SyncPlay without ever letting it
        break regular playback reporting."""
        forward(self.syncplay, name, *args)

    def current_item(self) -> JsonDict | None:
        """The claimed play state of the current kofin playback (SyncPlay's
        identity source), or None for idle/foreign playback."""
        with self._lock:
            return self._item

    # -- lyrics ---------------------------------------------------------------

    def start_lyrics(self) -> None:
        """Publish the playing song's Jellyfin lyrics for script.kofin.lyrics.

        Never raises. Does nothing when that add-on is not installed — there
        is no other consumer. Kodi's music database has no lyrics column, so
        lyrics cannot be synced into the library the way everything else is;
        they exist only on the playback that is running, and only while it
        runs.

        The fetch runs synchronously at the top of playback start, ahead of
        the claim, and forfeits rather than stalls (see Api.lyrics).
        """
        if not kofin_lyrics_installed():
            return
        try:
            self._start_lyrics()
        except JellyfinError as error:
            LOG.debug("lyrics unavailable: %s", error)
        except Exception:
            LOG.exception("lyrics start failed")

    def _start_lyrics(self) -> None:
        if not self.isPlayingAudio():
            return

        jellyfin_id = playing_jellyfin_id(self.getPlayingItem(), self.getPlayingFile())
        if jellyfin_id is None:
            return

        self._publish_lyrics(self.api.lyrics(jellyfin_id), jellyfin_id)

    def _publish_lyrics(self, payload: JsonDict, jellyfin_id: str) -> None:
        """Publish the lyrics and stop. Rendering them, and following the
        clock, belongs to script.kofin.lyrics -- kofin only ever knows how to
        fetch them at the right instant."""
        lines = lyrics_render.to_lines(payload)
        if not lines:
            return
        state.publish_lyrics([[start, text] for start, text in lines], jellyfin_id)
        LOG.debug("--> lyrics %s (%d lines)", jellyfin_id, len(lines))

    def _reset_lyrics(self) -> None:
        """Release the overlay. Called from finalize, so lyrics never outlive
        the playback that fetched them — including the error and stale-play
        paths, which are the ones that would otherwise leave them stranded."""
        state.clear_lyrics()

    # -- kodi callbacks ------------------------------------------------------

    def onPlayBackStarted(self) -> None:
        if self._stopped:
            return
        # Before anything that can block this callback thread: a start that
        # must wait for a SyncPlay group is paused at its first instant, not
        # seconds later when the claim and round trip complete.
        self._syncplay_event("on_playback_started")
        self.finalize()  # a previous kofin play that never got its stop event
        # After finalize only because that is what releases the previous
        # song's lyrics — it is a no-op on the normal path, where the last
        # playback stopped cleanly. See start_lyrics.
        self.start_lyrics()
        claimed = self._claim()
        if claimed is None:
            return
        # From the player: a pause made before the claim existed (a SyncPlay
        # hold pauses before _claim, whose wait runs the callback) found no
        # item to mark.
        claimed["Paused"] = bool(xbmc.getCondVisibility("Player.Paused"))
        with self._lock:
            self._item = claimed
        state.set_playing_id(claimed["Id"])
        self._publish_streams(claimed)
        LOG.debug("--> play %s (%s)", claimed["Id"], claimed["PlayMethod"])
        self._report(self.api.session_playing, event=None)
        self._start_ticker()
        self._start_segment_engine(claimed)
        self._start_late_subtitles(claimed)

    def onAVStarted(self) -> None:
        """First frame rendered: the SyncPlay Ready trigger, and the earliest
        moment Kodi's stream lists are populated enough to pick from."""
        if self._stopped:
            return
        self._syncplay_event("on_avstarted")
        self.apply_default_tracks()

    def onPlayBackPaused(self) -> None:
        if self._stopped:
            return
        self._syncplay_event("on_paused")
        self._set_paused(True)

    def onPlayBackResumed(self) -> None:
        if self._stopped:
            return
        if self.syncplay is None:
            self._settle_left_tempo()
        self._syncplay_event("on_resumed")
        self._set_paused(False)

    def _settle_left_tempo(self) -> None:
        """Put back a 1.0 a SyncPlay pulse left owed, when no manager is here
        to: the service before its connect, or SyncPlay off. Kodi refused it
        while paused, and the service start tried it only once."""
        if not state.syncplay_pulse():
            return
        try:
            from kofin.syncplay import tempo

            tempo.settle_left_rate(" at a resume")
        except Exception:
            LOG.exception("left tempo settle failed")

    def onPlayBackSeek(self, time: int, seekOffset: int) -> None:
        if self._stopped:
            return
        self._syncplay_event("on_seek", time / 1000.0)
        if self._item is not None:
            self._update_position(time / 1000.0)
            self._report(self.api.session_progress, event="timeupdate")
            self.segments.note_seek(time / 1000.0)

    def onPlayBackStopped(self) -> None:
        if self._stopped:
            return
        self._syncplay_event("on_stopped")
        self._finish()

    def onPlayBackEnded(self) -> None:
        if self._stopped:
            return
        self._syncplay_event("on_ended")
        self._finish()

    def onPlayBackError(self) -> None:
        if self._stopped:
            return
        self._syncplay_event("on_error")
        self.finalize()

    # -- reporting -----------------------------------------------------------

    def report_progress(self) -> None:
        """Ticker callback: refresh position and post progress."""
        if self._item is None:
            return
        try:
            self._update_position(self.getTime())
        except RuntimeError:  # nothing playing (race with stop)
            return
        self._report(self.api.session_progress, event="timeupdate")
        self._maybe_auto_next()

    def _maybe_auto_next(self) -> None:
        """A downloaded episode crossing the trigger queues the next
        keep-ahead. Runs on the ticker thread — the lookup is one bounded
        listing, and the ticker's next beat is ten seconds out anyway."""
        item = self._item
        if item is None or item.get("Type") != "Episode":
            return
        item_id = str(item.get("Id") or "")
        if not item_id or self._auto_next_latch == item_id:
            return
        runtime = float(item.get("Runtime") or 0) / 10_000_000
        position = float(item.get("CurrentPosition") or 0)
        if runtime <= 0 or position < runtime * downloads_auto.NEXT_TRIGGER_RATIO:
            return
        self._auto_next_latch = item_id
        try:
            downloads_auto.trigger_next(self.api, item)
        except Exception:  # pragma: no cover - never break the ticker
            LOG.exception("auto-next trigger failed for %s", item_id)

    def _finish(self) -> None:
        """A playback the viewer ended: report the stop, then make any
        finished-watching offer against what was playing.

        ``finalize`` clears ``_item``, so the item is captured first. Only the
        stop/end callbacks come through here — ``finalize``'s other caller
        (a stale play discovered at the next start) is cleanup, not a
        playback the viewer just finished.
        """
        item = self.current_item()
        self.finalize()
        if item is not None:
            if not self.offer_delete(item):
                # Never two stacked dialogs about one just-finished item:
                # the local-remove offer stands down when the server-delete
                # prompt ran.
                self.offer_remove_download(item)

    def finalize(self) -> None:
        """Report the stop and release all playback state."""
        self.segments.reset()
        self._stop_ticker()
        self._stop_late_subtitles()
        self._reset_lyrics()
        self._auto_next_latch = ""
        with self._lock:
            item = self._item
            self._item = None
        if item is None:
            return
        LOG.debug("<-- stop %s", item["Id"])
        stop_data = {
            "ItemId": item["Id"],
            "MediaSourceId": item["MediaSourceId"],
            "PlaySessionId": item["PlaySessionId"],
            "PositionTicks": int(item["CurrentPosition"] * 10_000_000),
        }
        name_live_stream(stop_data, item)
        live_stream_id = item.get("LiveStreamId")
        close_encoding = item.get("PlayMethod") == "Transcode"
        device_id = item.get("DeviceId", "")
        play_session_id = item["PlaySessionId"]

        def post_stop() -> None:
            try:
                self.api.session_stopped(stop_data)
            except Exception as error:
                LOG.warning("stop report failed: %s", error)
                # The position is the user's viewing progress and this was
                # its only route to the server; park it for the next connect
                # rather than lose it, as the server's own stop rule would
                # have read it: a play that reached the watched share is
                # Played with no resume point, since a position that far in
                # is what puts a finished item in Continue Watching.
                # Contained: a parking failure must not skip the transcode
                # close below.
                try:
                    from kofin.downloads import pending

                    if watched_to_end(item):
                        pending.enqueue(
                            str(item["Id"]),
                            str(item.get("Type") or ""),
                            played=True,
                            position_ticks=0,
                            snapshot=item.get("ServerUserData") or {},
                        )
                    else:
                        pending.enqueue(
                            str(item["Id"]),
                            str(item.get("Type") or ""),
                            position_ticks=int(stop_data["PositionTicks"]),
                            snapshot=item.get("ServerUserData") or {},
                        )
                except Exception:  # pragma: no cover - defensive
                    LOG.exception("could not park the stop position")
                if live_stream_id:
                    # The parked stop carries the position alone, and the
                    # report that named the stream was what would have closed
                    # it on the server.
                    try:
                        self.api.close_live_stream(live_stream_id)
                    except Exception as close_error:
                        LOG.warning("live stream close failed: %s", close_error)
            if close_encoding:
                try:
                    self.api.close_transcode(device_id, play_session_id)
                except Exception as error:
                    LOG.debug("close transcode failed: %s", error)

        self._reporter.submit(post_stop)
        state.clear_playing_id()
        state.clear_playing_streams()

    def sweep_live_streams(self) -> None:
        """Close the live streams of plays Kodi never started, at most every
        LIVE_SWEEP_SECONDS and on the reporter's thread: no claim will report
        them (state.close_stale_live_streams)."""
        now = time.monotonic()
        if now - self._last_live_sweep < LIVE_SWEEP_SECONDS:
            return
        self._last_live_sweep = now
        self._reporter.submit(self._close_stale_live_streams)

    def _close_stale_live_streams(self) -> None:
        closed = state.close_stale_live_streams(self.api.close_live_stream)
        if closed:
            LOG.debug("closed the live streams of unclaimed plays: %s", closed)

    def stop_threads(self) -> None:
        """Service shutdown: stop the ticker and checker without reporting.

        A play still claimed goes on in Kodi, so its claim is handed to the
        next generation (``adopt``), once the last report queued here has
        gone. A claim handed over earlier and never taken is of a play that
        ended before this one's began, and is retired before this one
        replaces it."""
        self._stopped = True
        self.segments.reset()
        self._stop_ticker()
        self._stop_late_subtitles()
        item = self.current_item()
        if item is not None:
            superseded = self._take_handed_over()
            if superseded is not None:
                LOG.debug(
                    "handed-over play of %s dropped: another play followed it",
                    superseded["Id"],
                )
                self._retire(superseded)
        self._reporter.stop()
        if item is not None:
            state.hand_over_play(
                {"Claim": item, "Server": self.api.server, "UserId": self.api.user_id}
            )

    def _take_handed_over(self) -> JsonDict | None:
        """The claim a stopped generation handed over, when it is this
        login's; taken from the file either way."""
        handed = state.take_handed_over_play()
        claim = handed.get("Claim")
        if not isinstance(claim, dict) or not claim.get("Id"):
            return None
        if (
            handed.get("Server") != self.api.server
            or handed.get("UserId") != self.api.user_id
        ):
            LOG.debug("handed-over play of %s dropped: another login's", claim["Id"])
            return None
        return claim

    def _retire(self, claim: JsonDict) -> None:
        """Close what the server holds open for a play nothing reports any
        more, as its stop would have: the live stream, whose tuner only a
        report naming it or a close frees, and a transcode's encoding."""
        live_stream_id = claim.get("LiveStreamId")
        if live_stream_id:
            self._reporter.submit(lambda: self.api.close_live_stream(live_stream_id))
        if claim.get("PlayMethod") == "Transcode":
            self._reporter.submit(
                lambda: self.api.close_transcode(
                    claim.get("DeviceId", ""), claim["PlaySessionId"]
                )
            )

    def adopt(self) -> None:
        """Report the play a stopped generation handed over, when it is this
        login's and Kodi is still playing its file; drop it otherwise.

        Reported on from where Kodi is, with a progress report and never a
        start: the server counts a play when it starts. A play that ended
        between the generations goes unreported, since how long ago is
        unknown and a stop that late could overwrite a resume point set
        since; it is only retired."""
        if self._stopped or self.current_item() is not None:
            return
        claim = self._take_handed_over()
        if claim is None:
            return
        playing, position = "", 0.0
        try:
            if self.isPlaying():
                playing = self.getPlayingFile()
                position = max(float(self.getTime()), 0.0)
        except RuntimeError:  # it stopped meanwhile
            playing = ""
        if not playing or not state.same_file(playing, str(claim.get("Path") or "")):
            LOG.debug("handed-over play of %s dropped: it has ended", claim["Id"])
            self._retire(claim)
            return
        claim["CurrentPosition"] = position
        claim["Paused"] = bool(xbmc.getCondVisibility("Player.Paused"))
        with self._lock:
            self._item = claim
        state.set_playing_id(claim["Id"])
        self._publish_streams(claim)
        LOG.debug("--> adopted %s (%s)", claim["Id"], claim.get("PlayMethod"))
        self._report(self.api.session_progress, event="timeupdate")
        self._start_ticker()
        self._start_segment_engine(claim)
        self._start_late_subtitles(claim)

    # -- delete after watching -------------------------------------------------

    def offer_delete(self, item: JsonDict) -> bool:
        """Ask whether to delete an item the viewer just finished.

        Returns whether the prompt was raised. Both settings must be on: the
        Advanced tab's delete opt-in owns whether kofin deletes anything at
        all, and this is a sub-option of it.
        """
        if item.get("Type") not in DELETABLE_TYPES or not item.get("Id"):
            return False
        if not settings.get_bool("enableDelete"):
            return False
        if not settings.get_bool("deleteAfterWatching"):
            return False
        if not watched_to_end(item):
            return False
        if not item.get("CanDelete"):
            # The server's own answer for this account.
            return False
        # Off the Kodi callback thread: this dialog waits on a person, and
        # blocking that thread stalls the player callbacks behind it (Play
        # Next's handoff to the following episode arrives on it). Daemon, so a
        # prompt left open cannot hold up service shutdown.
        spawn_once(None, self._delete_prompt, "kofin-delete-prompt", item)
        return True

    def offer_remove_download(self, item: JsonDict) -> bool:
        """The local sibling of ``offer_delete`` — a download watched to the
        end has its local copy removed, silently or after a prompt, whoever
        queued it.

        The retention sweep covers what this path cannot see — something
        watched while the service was down, or outside kofin's player — and
        acts only in the silent mode.

        Video only, on ``DELETABLE_TYPES``. The test is the *item's* Jellyfin
        type rather than the row's ``media_type``, which can be ``""``.
        """
        if item.get("Type") not in DELETABLE_TYPES:
            return False
        try:
            if not settings.get_bool("downloadsDeleteAfterWatching"):
                return False
        except TypeError:
            # A profile whose settings have no downloads section.
            return False
        if not settings.get_bool("downloadsEnabled"):
            return False
        item_id = str(item.get("Id") or "")
        if not item_id or not watched_to_end(item):
            return False
        from kofin.downloads import store as downloads_store

        row = downloads_store.get(item_id)
        if row is None or row.state != downloads_store.DONE:
            return False
        if settings.get_bool("downloadsDeleteAutomatically"):
            LOG.debug("removing watched download %s (automatic)", item_id)
            ipc.notify(ipc.DOWNLOAD_REMOVE, {"Ids": [item_id]})
            return True
        # Off the callback thread, as the delete prompt.
        spawn_once(
            None,
            self._remove_download_prompt,
            "kofin-remove-download-prompt",
            item_id,
            str(item.get("Name") or ""),
        )
        return True

    def _remove_download_prompt(self, item_id: str, name: str) -> None:
        with self._modal("yesnodialog"):
            answer = xbmcgui.Dialog().yesno(
                settings.localized(30710),  # Remove download
                settings.localized(30714) % name,
            )
        if not answer:
            return
        ipc.notify(ipc.DOWNLOAD_REMOVE, {"Ids": [item_id]})

    def _delete_prompt(self, item: JsonDict) -> None:
        name = item.get("Name") or ""
        with self._modal("yesnodialog"):
            answer = xbmcgui.Dialog().yesno(
                xbmc.getLocalizedString(117),  # Delete
                settings.localized(30506) % name,
            )
        if not answer:
            return
        try:
            self.api.delete_item(str(item["Id"]))
        except Exception as error:
            LOG.warning("delete after watching failed: %s", error)
            self._notify(settings.localized(30507), toast.ERROR)
            return
        # No refresh from here: the server's own library-changed event drives
        # the removal out of the Kodi database through the normal sync path.
        LOG.debug("deleted %s after watching", item["Id"])

    # -- stream selection ------------------------------------------------------

    def _publish_streams(self, item: JsonDict) -> None:
        """Hand the claimed playback's streams to the context item.

        The play route resolved them; this moves them somewhere a later plugin
        invocation can read, and states in one word what the menu should
        offer so addon.xml can pick a label (see core/state.py). Never raises:
        a menu that fails to appear must not take the playback with it.
        """
        try:
            payload = dict(item.get("Streams") or {})
            if not payload:
                state.clear_playing_streams()
                return
            media_streams = payload.get("MediaStreams") or []
            method = str(item.get("PlayMethod") or "")
            payload["PlayMethod"] = method
            payload["Id"] = item.get("Id", "")
            payload["MediaSourceId"] = item.get("MediaSourceId", "")
            payload["AudioStreamIndex"] = item.get("AudioStreamIndex")
            # Both indices, not just audio: a burned-in subtitle is not a Kodi
            # track, so this is the only thing that tells the menu which row is
            # the one in the picture (core/streams.burned_subtitle).
            payload["SubtitleStreamIndex"] = item.get("SubtitleStreamIndex")
            offer = streams.menu_offer(media_streams)
            if self._syncplay_group_active:
                offer = streams.OFFER_NONE
            state.publish_playing_streams(payload, offer)
        except Exception:
            LOG.exception("publishing playing streams failed")

    def republish_streams(self, item: JsonDict) -> None:
        """Re-publish a claimed item's streams after they changed under it.

        The late-subtitle chase extends the attached list mid-playback, and
        the context menu reads its copy off a window property — so without
        this the menu goes on mapping indices against the list the playback
        started with."""
        self._publish_streams(item)

    def apply_default_tracks(self) -> None:
        """Start on the tracks the Jellyfin *user profile* nominates.

        Kodi otherwise picks from its own language settings. The server has
        already resolved both against that account and returns them on every
        MediaSource.

        Runs at first frame rather than at claim because Kodi's stream lists
        do not exist until then — and because running here cannot delay the
        picture, only follow it. Never raises.
        """
        if not settings.get_bool("honourJellyfinDefaultTracks"):
            return
        item = self.current_item()
        if item is None:
            return
        try:
            self._apply_default_tracks(item)
        except Exception:
            LOG.exception("applying Jellyfin default tracks failed")

    def _apply_default_tracks(self, item: JsonDict) -> None:
        payload = item.get("Streams")
        if not payload:
            # A downloaded play: the server's defaults index the tracks of a
            # source, not of the file playing, so Kodi's own choice stands.
            return
        media_streams = payload.get("MediaStreams") or []
        attached = payload.get("Attached") or []
        method = str(item.get("PlayMethod") or "")

        # Audio only on a direct play: a transcode carries the single track the
        # server already encoded to our request, so there is nothing to choose
        # and Kodi's only index is 0.
        if streams.is_direct(method):
            ordinal = streams.audio_ordinal(media_streams, item.get("AudioStreamIndex"))
            if ordinal is not None:
                # setAudioStream seeks the demuxer even for a no-op. On an HTTP
                # Matroska that seek can miss and land at EOF, so do not
                # re-select a track Kodi is already playing.
                if kodirpc.current_audio() == ordinal:
                    LOG.debug("audio track %s already current", ordinal)
                else:
                    self.setAudioStream(ordinal)
                    LOG.debug("--> audio track %s (Jellyfin default)", ordinal)

        wanted = item.get("SubtitleStreamIndex")
        if wanted is None or int(wanted) < 0:
            # The profile asks for no subtitle. Say so rather than leaving
            # whatever Kodi auto-selected running.
            self.showSubtitles(False)
            return
        if streams.burned_subtitle(media_streams, wanted, method):
            # It is already in the picture. Anything Kodi shows on top of it is
            # a second subtitle over the first, which is what an auto-selected
            # attached track would be here.
            self.showSubtitles(False)
            LOG.debug("--> subtitle %s is burned in; Kodi's own left off", wanted)
            return
        ordinal = streams.subtitle_ordinal(media_streams, wanted, attached, method)
        if ordinal is None:
            return
        if kodirpc.current_subtitle() == ordinal:
            LOG.debug("subtitle track %s already current", ordinal)
            return
        self.setSubtitleStream(ordinal)
        self.showSubtitles(True)
        LOG.debug("--> subtitle track %s (Jellyfin default)", ordinal)

    # -- segment engine: lifecycle -------------------------------------------

    def _start_segment_engine(self, item: JsonDict) -> None:
        self.segments.start(item)

    def _notify(self, message: str, level: str = toast.INFO) -> None:
        toast.show(message, level, time_ms=3000)

    def _claim(self) -> JsonDict | None:
        """The claim for the playback that just started, or None.

        Runs inside onPlayBackStarted, i.e. on the service's own thread
        (Kodi delivers Python player and monitor callbacks on the thread
        that created the object, from inside its Kodi API calls), so every
        beat waited here delays onAVStarted — the SyncPlay Ready trigger and
        apply_default_tracks.
        """
        monitor = xbmc.Monitor()
        waited = 0.0
        outcome = "timed out"
        kind = "none"
        claimed: JsonDict | None = None
        while waited < CLAIM_TIMEOUT_SECONDS:
            try:
                current_file = self.getPlayingFile()
            except RuntimeError:
                current_file = ""
            if current_file:
                if self.isPlayingAudio():
                    kind = "audio"
                elif downloaded_path(current_file):
                    kind = "downloaded"
                else:
                    kind = "video"
                claimed = state.claim_play_item(current_file)
                if claimed is None and current_file.startswith(PLUGIN_URL):
                    # A track Kodi queued ahead is named by the plugin URL
                    # it was listed under; its entry is found by the item.
                    queued = path_item_id(current_file)
                    if queued:
                        claimed = state.claim_play_item_of(queued)
                if claimed is not None:
                    outcome = "claimed"
                    break
                if (
                    kind != "video"
                    and waited < BACKFILL_GRACE_SECONDS
                    and not monitor.waitForAbort(0.25)
                ):
                    waited += 0.25
                    continue
                # A file is playing but nothing is queued: foreign playback.
                outcome = "foreign" if kind == "video" else "backfill missed"
                break
            if monitor.waitForAbort(0.5):
                outcome = "aborted"
                break
            waited += 0.5
        LOG.debug("claim %s after %.2fs (%s)", outcome, waited, kind)
        return claimed

    def _set_paused(self, paused: bool) -> None:
        if self._item is None:
            return
        self._item["Paused"] = paused
        self._report(self.api.session_progress, event="pause" if paused else "unpause")

    def _update_position(self, seconds: float) -> None:
        if self._item is not None and seconds >= 0:
            self._item["CurrentPosition"] = seconds

    def _report(self, poster: Any, event: str | None) -> None:
        item = self._item
        if item is None:
            return
        if state.is_offline():
            # Offline claims exist for the local machinery; a session post
            # every ten seconds would ride the ladder to nowhere for a session
            # the server cannot see. The stop report is not gated — its
            # failure path parks the position for the replay.
            return
        volume, muted = _volume_state()
        data: JsonDict = {
            "QueueableMediaTypes": "Video,Audio",
            "CanSeek": True,
            "ItemId": item["Id"],
            "MediaSourceId": item["MediaSourceId"],
            "PlayMethod": item["PlayMethod"],
            "PlaySessionId": item["PlaySessionId"],
            "PositionTicks": int(item["CurrentPosition"] * 10_000_000),
            "IsPaused": bool(item.get("Paused")),
            "IsMuted": muted,
            "VolumeLevel": volume,
            "AudioStreamIndex": item.get("AudioStreamIndex"),
            "SubtitleStreamIndex": item.get("SubtitleStreamIndex"),
        }
        name_live_stream(data, item)
        if event:
            data["EventName"] = event
        # Payload is complete; the post itself must not run on this thread —
        # for callbacks it is Kodi's announcement thread (see _Reporter).
        self._reporter.submit(lambda: poster(data))

    def _start_ticker(self) -> None:
        self._stop_ticker()
        self._ticker = _Ticker(self)
        self._ticker.start()

    def _stop_ticker(self) -> None:
        if self._ticker is not None:
            self._ticker.stop()
            self._ticker = None

    def _start_late_subtitles(self, item: JsonDict) -> None:
        """Chase any subtitle the server had not finished extracting.

        Nothing to do on the normal path: a track the play route fetched is
        already attached, and this only exists for the cold-extraction case
        (service/latesubs.py)."""
        self._stop_late_subtitles()  # belt: no chase leaks across claims
        deferred = latesubs.deferred_of(item)
        if not deferred:
            return
        self._late_subs = latesubs.LateSubtitles(self.api.http, self, item, deferred)
        self._late_subs.start()

    def _stop_late_subtitles(self) -> None:
        if self._late_subs is not None:
            self._late_subs.stop()
            self._late_subs = None

    def fetch_subtitle(self, index: int) -> None:
        """AttachSubtitle IPC: the stream menu picked a track the transcode
        did not attach.

        Runs on Kodi's notification thread, so it must only start the chase —
        the fetch itself is an ffmpeg extraction on the server and takes tens
        of seconds (service/latesubs.py). Supersedes any chase in flight: a
        viewer who picks a second subtitle has changed their mind about the
        first, and only one of them can be on screen anyway."""
        item = self.current_item()
        if item is None:
            LOG.warning("subtitle %s requested with nothing playing", index)
            return
        attachment = latesubs.fetchable_of(item).get(index)
        if attachment is None:
            LOG.warning("subtitle %s is not one this playback can be handed", index)
            return
        self._stop_late_subtitles()
        self._late_subs = latesubs.LateSubtitles(
            self.api.http, self, item, [attachment], requested=True
        )
        self._late_subs.start()


class _Ticker(threading.Thread):
    def __init__(self, player: Player) -> None:
        super().__init__(name="kofin-progress")
        self._player = player
        self._halt = threading.Event()

    def stop(self) -> None:
        self._halt.set()
        if self.is_alive():
            self.join(timeout=5)

    def run(self) -> None:
        while not self._halt.wait(PROGRESS_INTERVAL_SECONDS):
            try:
                self._player.report_progress()
            except Exception as error:  # pragma: no cover - defensive
                LOG.warning("progress tick failed: %s", error)


def _volume_state() -> tuple[int, bool]:
    result = kodirpc.call(
        "Application.GetProperties", {"properties": ["volume", "muted"]}
    )
    try:
        return int(result.get("volume", 100)), bool(result.get("muted", False))
    except Exception:
        return 100, False
