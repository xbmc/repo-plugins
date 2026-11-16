"""Command execution against the Kodi player.

``play_item`` plays **kofin plugin URLs** (``plugin://…?mode=play&id=…``) for
Jellyfin items, so SyncPlay says *which id at what position* and kofin's normal
play path decides *how*.
"""

import threading
from typing import TYPE_CHECKING, Any, Optional

import xbmc

from kofin.core import kodirpc
from kofin.core.log import Logger
from kofin.syncplay import utils
from kofin.syncplay.utils import FOLLOWING, Phase
from kofin.syncplay.liveclock import LiveClock
from kofin.syncplay.tempo import PulseScheduler, SEEK_LAG_DEFAULT_MS

if TYPE_CHECKING:
    from kofin.syncplay.manager import SyncPlayManager
    from kofin.syncplay.ports import Claim
    from kofin.syncplay.providers import PlayTarget


LOG = Logger(__name__)

# Kodi's presentationtime is read at most this often once it has answered: the
# offset it gives holds across a tempo and a pause, and moves only where the
# stream's own timestamps jump.
# Until it has answered, it is asked again this soon: one controller tick, so
# the stream's clock is taken up as soon as it exists, while a stream that never
# has one (a server remux) costs a read a tick and no more.


class PlaybackController:
    """Executes group commands against the Kodi player and converges local
    playback on the group timeline at each command (SYNCPLAY.md §5.1).

    There is deliberately **no continuous drift controller**: stock Kodi
    plays a tempo only while "sync playback to display" is on, which imposes
    a fixed rate error wherever the display rate is not a whole multiple of
    the frame rate.

    Position is converged where the group tells us to converge it — on
    Unpause, Pause, Seek and item load. Between commands, an item Kodi can
    play at a tempo is kept on the group position by the
    :class:`~kofin.syncplay.tempo.PulseScheduler`: bounded, confirmed rate
    pulses through Kodi's own tempo, which with the ``tempo`` feature works
    with the display clock *off*, with a quiet window after each one — not a
    loop. Anything else is left alone. All privileged player operations run
    inside the manager's programmatic() guard so they are not echoed back to
    the group as user actions.
    """

    def __init__(self, manager: "SyncPlayManager", player: xbmc.Player) -> None:
        self.manager = manager
        self.player = player

        # The pending scheduled command.
        self._timer: Optional[threading.Timer] = None
        self._timer_lock = threading.Lock()
        self.last_command: Optional[dict[str, Any]] = None
        # An Unpause that arrived while LOADING.
        self._deferred_unpause: Optional[dict[str, Any]] = None

        # (media_ms, server_when_ms, playing) group position reference
        self._reference: Optional[tuple[float, Optional[float], bool]] = None

        self._loop_thread: Optional[threading.Thread] = None
        self._loop_stop = threading.Event()

        # schedule() pre-aligns on the dispatcher with the fire-time timer
        # armed; an align that overruns the scheduling lead would meet the
        # timer on the player, so the two take this lock in turn.
        self._player_lock = threading.RLock()

        self._caching_since: Optional[float] = None
        self._buffering_reported = False

        # Fine sync between commands (syncplay/tempo.py), and what a seek
        # aimed at the group's current position leaves behind on this device
        # — its restart time plus its landing error — so a corrective seek can
        # aim ahead of a moving group by exactly that. Learned from every
        # playing seek (see _seek_and_settle).
        self.tempo = PulseScheduler(self)
        self.seek_lag_ms = SEEK_LAG_DEFAULT_MS
        self._live_seek_logged = False
        self.live = LiveClock(self)

    # ------------------------------------------------------------------
    # Command scheduling (SYNCPLAY.md §5.1)
    # ------------------------------------------------------------------

    def schedule(self, command: dict[str, Any]) -> None:
        """Schedule a SyncPlayCommand for its server-clock instant."""
        when_ms = utils.parse_iso_ms(command.get("When"))

        if when_ms is None:
            LOG.warning("Command without a usable When: %s", command)
            return

        if self._is_repeat(command):
            LOG.debug(
                "[ syncplay/%s ] at %s already applied, ignoring the repeat",
                command.get("Command"),
                command.get("When"),
            )
            return

        fire_local_ms = when_ms - self.manager.offset_ms()
        delay = (fire_local_ms - utils.local_ms()) / 1000.0

        self.cancel_pending()
        LOG.debug(
            "[ syncplay/%s ] at %s (%+.0fms)",
            command.get("Command"),
            command.get("When"),
            delay * 1000,
        )

        if delay <= 0:
            self._execute(command)
            return

        with self._timer_lock:
            self._timer = utils.later(delay, self._execute, command)

        # With the timer armed, use the scheduling lead to line the player up
        # on the start position, so the fire instant starts from exactly the
        # group position (initial-start tightness for barrier restarts and
        # hot joins alike). Blocking here is fine: this runs on the dispatcher
        # like any REST round trip.
        if command.get("Command") == "Unpause":
            self._prealign_unpause(command)

    def _prealign_unpause(self, command: dict[str, Any]) -> None:
        """Seek to a scheduled Unpause's position at arm time.

        While paused, the position at the start instant IS the command's
        PositionTicks — no extrapolation. Audio is excluded: a paused
        PAPlayer is never seeked.
        """
        if self._is_audio() or self.manager.phase not in FOLLOWING:
            return

        if self.manager.is_transcoding():
            # A transcode seek snaps to a segment and its restart costs more
            # than the scheduling lead, so pre-aligning makes the start both
            # later and further out. Resume where we are instead.
            LOG.debug("[ syncplay/align ] skipped: transcoding")
            return

        target_ms = utils.ticks_to_ms(command.get("PositionTicks") or 0)

        try:
            offset_ms = target_ms - self._position_ms()
        except Exception:
            return

        if abs(offset_ms) <= utils.UNPAUSE_ALIGN_MS:
            return

        if self._leave_to_fine_sync(offset_ms, "to the start position"):
            return

        LOG.debug("[ syncplay/align ] %+.0fms to the start position", offset_ms)

        with self._player_lock, self.manager.programmatic():
            self._seek_and_settle(target_ms)

    def _leave_to_fine_sync(self, offset_ms: float, where: str) -> bool:
        """Whether an unpause offset is better closed by a rate pulse than a cut.

        Only in the ``synced`` phase. A ``waiting_ready`` start -- a barrier
        restart or a hot join -- is the one chance to begin exactly on the group
        position, and keeps the seek.

        ``can_close`` answers False for an item Kodi cannot play at a tempo now
        (``Player.TempoEnabled``) and for one whose pulse was not confirmed, so
        exactly when nothing can be nudged.
        """
        if self.manager.phase != Phase.SYNCED:
            return False

        if not self.tempo.can_close(offset_ms):
            return False

        LOG.debug("[ syncplay/align ] %+.0fms %s: left to fine sync", offset_ms, where)
        return True

    @staticmethod
    def _identity(command: dict[str, Any]) -> tuple[Any, Any, Any]:
        """What makes two commands the same group event."""
        return (
            command.get("Command"),
            command.get("When"),
            command.get("PositionTicks") or 0,
        )

    def _is_repeat(self, command: dict[str, Any]) -> bool:
        """Has this exact command already been carried out?

        The server re-issues the transport command when the last member
        reports ready out of a Waiting state, so a member that reloaded to
        serve a Seek is handed that same Seek again as it comes back, with an
        identical ``When``. Re-applying is invisible on a direct stream (a seek
        to where it already is) and a second full stop and restart on a
        transcoded one.

        ``When`` is the server's own instant for the event, so equality here
        means the same event and not a second one that happens to match.
        ``last_command`` is cleared whenever the group's playback ends or the
        member detaches, which is exactly when the same command could
        legitimately arrive again.
        """
        if self.last_command is None:
            return False

        return self._identity(self.last_command) == self._identity(command)

    def cancel_pending(self) -> None:
        with self._timer_lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

    def _execute(self, command: dict[str, Any]) -> None:
        try:
            name = str(command.get("Command") or "")
            when_ms = utils.parse_iso_ms(command.get("When"))
            ticks = command.get("PositionTicks") or 0

            # No pulse runs across a command: the command converges position
            # itself, and a seek under a running rate lands early.
            self.tempo.cancel(name)

            if name == "Unpause":
                if not self.live.keeps_source_clock(ticks):
                    self._reference = (utils.ticks_to_ms(ticks), when_ms, True)
                if self.manager.phase == Phase.LOADING:
                    # Do not set last_command: this Unpause has not run, and
                    # the Ready re-issue carries the same When.
                    self._deferred_unpause = command
                    LOG.debug("Unpause while still loading, deferring to ready flow")
                    return
                self._deferred_unpause = None
                if when_ms is None:
                    # An Unpause is placed in time by its When.
                    raise ValueError("Unpause command without When")
                self._do_unpause(
                    ticks,
                    when_ms,
                    rebind_origin=command.get("_rebind_origin", True),
                )
            elif name == "Pause":
                if not self.live.keeps_source_clock(ticks):
                    self._reference = (utils.ticks_to_ms(ticks), when_ms, False)
                self._do_pause(ticks)
            elif name == "Seek":
                if not self.live.keeps_source_clock(ticks):
                    self._reference = (
                        utils.ticks_to_ms(ticks),
                        when_ms,
                        False,
                    )
                self._do_seek(ticks)
            elif name == "Stop":
                self._reference = None
                self._do_stop()
            else:
                LOG.debug("Unknown SyncPlay command: %s", name)
                return
            self.last_command = command
        except Exception as error:
            LOG.exception("SyncPlay command failed: %s", error)

    def _do_unpause(
        self, ticks: int, when_ms: float, rebind_origin: bool = True
    ) -> None:
        # Gate on our own phase, not on player state reads: around a held
        # music boundary isPlaying/getTime intermittently report no media
        # for media that is right there, paused.
        phase = self.manager.phase

        if phase == Phase.LOADING:
            LOG.debug("Unpause while still loading, deferring to ready flow")
            return

        if phase not in FOLLOWING:
            LOG.debug("Unpause with nothing followed, ignoring")
            return

        # Shared-start Unpause fires at When. A zap / late Unpause carries a
        # When the group already played through; rebinding then maps a newer
        # picture onto that position and pulses will not close it.
        late_ms = self.manager.server_now_ms() - (when_ms or 0)
        if rebind_origin and late_ms <= 1000.0 and self.live.seek_refused():
            self.live.bind_origin_to_group()

        # Late command (When already past): jump to the extrapolated live
        # position instead of starting behind the group. Session-time ticks
        # on a source-clock group are not a live position — align to the
        # group clock we kept.
        if self.live.keeps_source_clock(ticks):
            target_ms = self.estimate_position_ms()
            if target_ms is None:
                target_ms = self._position_ms()
        else:
            target_ms = utils.command_position_ms(
                ticks, when_ms, self.manager.server_now_ms()
            )

        with self._player_lock, self.manager.programmatic():
            if self._is_audio():
                # Resume first: a paused PAPlayer must never be seeked
                # (seeks and even the pause toggle queue up until user
                # input on some builds, self-resume on others). All audio
                # alignment happens while running, and the resume itself is
                # retried until the clock moves.
                resumed = self._resume_with_retries()

                if not resumed:
                    LOG.warning("Unpause did not take effect; leaving it to a resync")
                    return

                behind_ms = target_ms - self._position_ms()

                if self.tempo.armed():
                    # Fine sync takes what the music budget allows, without
                    # the audible skip a seek is; past it, the seek is the
                    # cheaper sound (syncplay/tempo.py, MUSIC_BUDGET_MS).
                    if self.tempo.can_close(behind_ms):
                        LOG.debug(
                            "[ syncplay/align ] %+.0fms at the resume: "
                            "left to fine sync",
                            behind_ms,
                        )
                        # Measure once PAPlayer is off the pause, as the
                        # video branch does after its resume.
                        self.tempo.note_settle()
                    else:
                        self._seek_and_settle(target_ms)
                elif abs(behind_ms) > utils.AUDIO_UNPAUSE_ALIGN_MS:
                    self._seek_and_settle(target_ms)
            else:
                behind_ms = target_ms - self._position_ms()

                # Catch-all for starts that were not pre-aligned at arm time
                # (late commands execute immediately): the same tight band.
                # stay_paused=False because a resume follows immediately: the
                # settle's re-pause would fight it, and the pause it queues
                # lands after the resume decision is taken. Never on a
                # transcode (see _prealign_unpause).
                if abs(behind_ms) > utils.UNPAUSE_ALIGN_MS:
                    if self.manager.is_transcoding():
                        LOG.debug(
                            "[ syncplay/align ] %+.0fms carried: transcoding",
                            behind_ms,
                        )
                    elif not self._leave_to_fine_sync(behind_ms, "at the resume"):
                        self._seek_and_settle(target_ms, stay_paused=False)

                if self._resume_and_verify():
                    self._align_after_resume()
                    self.tempo.note_settle()

        self.manager.on_local_unpaused()

    def _align_after_resume(self) -> None:
        """Close what the resume itself opened up, once the picture is moving.

        The alignment above happens *before* the resume, and the resume lands
        up to about a second after it is asked, so whatever was aligned is
        stale by the time anything is on screen. Here the clock has started, so
        the reading is real and the group estimate is comparable to it. Not on
        a transcode (see ``_prealign_unpause``), and not on audio, whose resume
        choreography aligns itself.
        """
        if self._is_audio() or self.manager.is_transcoding():
            return

        target_ms = self.estimate_position_ms()

        if target_ms is None:
            return

        behind_ms = target_ms - self._position_ms()

        # Logged whether or not it acts: the residual is what the threshold is
        # chosen from.
        LOG.debug(
            "[ syncplay/resumed ] residual %+.0fms (threshold %.0fms)",
            behind_ms,
            utils.POST_RESUME_ALIGN_MS,
        )

        if abs(behind_ms) <= utils.POST_RESUME_ALIGN_MS:
            return

        if self.live.claim() is not None:
            # A live member has no seek: ahead by more than LIVE_HOLD_MIN_MS
            # it holds, otherwise fine sync.
            if behind_ms < -utils.LIVE_HOLD_MIN_MS and self.live_on_source_clock():
                self.live.hold(-behind_ms)
            else:
                LOG.debug(
                    "[ syncplay/align ] %+.0fms after the resume: left to fine sync",
                    behind_ms,
                )
            return

        if self.tempo.can_close(behind_ms):
            # A skip is for gross errors: a residual fine sync can close is
            # left to it — a few seconds at a raised rate instead of a visible
            # cut; the scheduler measures again once the resume has played
            # through the queue.
            LOG.debug(
                "[ syncplay/align ] %+.0fms after the resume: left to fine sync",
                behind_ms,
            )
            return

        LOG.debug("[ syncplay/align ] %+.0fms after the resume landed", behind_ms)
        # Aimed ahead by seek_lag_ms: the group moves on while the seek lands.
        self._seek_and_settle(target_ms + self.seek_lag_ms, stay_paused=False)

    def _resume_with_retries(self) -> bool:
        """Resume paused audio and verify it, nudging until it sticks.

        Around a held gapless boundary the player's state reads are not
        trustworthy and a single toggle can be swallowed, so the only
        acceptable success signal is the clock demonstrably advancing.
        Toggling with no media loaded is ignored by Kodi, so a nudge is
        safe even when the reads claim there is nothing playing.
        """
        started = utils.local_ms()
        deadline = started + utils.UNPAUSE_RETRY_WINDOW_MS
        nudges = 0
        last_nudge = 0.0
        last_pos = None
        frozen_reads = 0

        while utils.local_ms() < deadline:
            try:
                pos = self.player.getTime()
            except Exception:
                pos = None

            if pos is not None and last_pos is not None and pos > last_pos + 0.1:
                LOG.debug(
                    "[ syncplay/unpause ] resumed after %d nudge(s), %.0f ms",
                    nudges,
                    utils.local_ms() - started,
                )
                return True  # the clock is moving: playing

            if pos is not None and last_pos is not None and not self._is_paused():
                # Claims to be playing but the clock is frozen: jammed.
                frozen_reads += 1

            last_pos = pos
            now = utils.local_ms()

            if now - last_nudge > utils.UNPAUSE_NUDGE_INTERVAL_MS and (
                pos is None or self._is_paused() or frozen_reads >= 2
            ):
                LOG.debug("[ syncplay/unpause ] nudging the player")
                self.player.pause()
                nudges += 1
                last_nudge = now
                frozen_reads = 0

            xbmc.sleep(utils.UNPAUSE_VERIFY_STEP_MS)

        LOG.warning(
            "[ syncplay/unpause ] gave up after %d nudge(s), %.0f ms",
            nudges,
            utils.local_ms() - started,
        )
        return False

    def _resume_and_verify(self) -> bool:
        """Ask for playing, and keep asking until the clock actually moves.

        ``speed`` is not proof: Kodi reports speed 1 for a player that is not
        advancing, so the only signal is the position sampled twice. Re-asking
        matters as much as checking — the failure this exists for is another
        thread's pause landing *after* our resume, and a second explicit play
        is what undoes that.
        """
        deadline = utils.local_ms() + utils.RESUME_VERIFY_S * 1000
        started = utils.local_ms()
        asked_at = None
        attempts = 0

        while utils.local_ms() < deadline:
            now = utils.local_ms()

            if asked_at is None or now - asked_at >= utils.RESUME_REASK_MS:
                kodirpc.resume_player()
                asked_at = now
                attempts += 1

            before = self._position_ms()
            xbmc.sleep(utils.RESUME_VERIFY_STEP_MS)

            if self._position_ms() > before + 20:
                LOG.debug(
                    "[ syncplay/unpause ] playing after %.0fms (%s ask%s)",
                    utils.local_ms() - started,
                    attempts,
                    "" if attempts == 1 else "s",
                )

                return True

        LOG.warning("Unpause did not start playback; leaving it to a resync")
        return False

    def _do_pause(self, ticks: int) -> None:
        if not self._has_media():
            return

        with self._player_lock, self.manager.programmatic():
            if not self._is_paused():
                self.player.pause()

            # Land everyone on the same frame when we drifted visibly. Video
            # only: a paused PAPlayer is never seeked.
            diff_ms = utils.ticks_to_ms(ticks) - self._position_ms()

            if abs(diff_ms) > 250 and not self._is_audio():
                self._seek_and_settle(utils.ticks_to_ms(ticks))

    def _do_seek(self, ticks: int) -> None:
        if not self._has_media():
            return

        if self._is_audio():
            # Never seek a paused PAPlayer: pause, promise the target in the
            # ready report, and let the Unpause that follows a group Seek at
            # the same position land it.
            with self._player_lock, self.manager.programmatic():
                if not self._is_paused():
                    self.player.pause()

            self.manager.post_report(
                "syncplay_ready", position_s=utils.ticks_to_seconds(ticks)
            )
            return

        if self.live.seek_refused():
            # Live before Transcode: Jellyfin labels a live HLS remux
            # Transcode, and the reload path below would Player.Open the
            # same channel. Kodi does not restart it, OnAVStarted never
            # fires, and the 45s load watchdog leaves the group.
            LOG.debug("[ syncplay/seek ] skipped: live item, pulses only")
            self.report_ready()
            return

        if self.manager.is_transcoding():
            # Reload rather than seek: a transcode seek restarts the encode,
            # so the position does not move within _seek_and_settle's
            # SEEK_SETTLE_TIMEOUT and the settle would read the position
            # before the seek. The reload reports Ready through the normal
            # load flow, so nothing is reported here.
            LOG.debug("[ syncplay/seek ] transcoding: reloading at the target")
            self.manager.reload_current_item()
            return

        with self._player_lock, self.manager.programmatic():
            if not self._is_paused():
                self.player.pause()

            self._seek_and_settle(utils.ticks_to_ms(ticks))

        self.report_ready()

    def _do_stop(self) -> None:
        # Read before on_group_stopped() resets it: only media SyncPlay
        # is actually driving is stopped — a group Stop must not kill a
        # detached spectator's own playback.
        was_following = self.manager.phase != Phase.IDLE

        self.cancel_pending()
        self.manager.on_group_stopped()

        if was_following and self._has_media():
            with self.manager.programmatic():
                # Not player.stop() (see kodirpc.stop_player). Landing
                # asynchronously is safe: on_group_stopped() has already left
                # the phase behind, so the late callback finds nothing to
                # forward, and it is inside PROGRAMMATIC_ECHO_GRACE either way.
                kodirpc.stop_player()

    # ------------------------------------------------------------------
    # Item loading (queue application handoff)
    # ------------------------------------------------------------------

    def play_item(self, target: "PlayTarget") -> None:
        """Start a provider play target paused-on-arrival; the ready flow
        reports in.

        The playlist entry is whatever URL the owning provider resolved
        (``syncplay/providers.py``) — for Jellyfin, a kofin plugin URL, so the
        plugin process resolves it (device profile, direct-play vs
        transcode, PlaybackInfo at ``startticks``) and pushes the play state
        for the service player to claim — exactly the path a user-initiated
        play takes, except that its URL says it is unattended, so the play
        route asks nothing.
        """
        playlist_type = xbmc.PLAYLIST_MUSIC if target["audio"] else xbmc.PLAYLIST_VIDEO
        playlist = xbmc.PlayList(playlist_type)

        with self.manager.programmatic():
            if self.player.isPlaying():
                # Stopped through kodirpc and waited on, so the playlist
                # rewrite below follows the outgoing playback; Kodi orders the
                # play itself, since playPlaylist reaches the app thread behind
                # the stop message.
                kodirpc.stop_player(wait_seconds=utils.STOP_WAIT_SECONDS)

            playlist.clear()
            playlist.add(target["url"])
            self.player.play(playlist, startpos=0)

    def prepare_ready(self) -> None:
        """After onAVStarted: settle on the group position and report Ready.

        The server compares our reported position against the group and
        answers with a private Seek if we are out of tolerance (§7).
        """
        self.live.new_stream()
        self.note_live_origin()
        self._live_seek_logged = False
        target_ms = self.estimate_position_ms()

        if target_ms is not None:
            landed_ms = self._position_ms()
            diff = target_ms - landed_ms

            # Where a load lands: a transcode can begin away from the
            # requested start, since the server is still writing its playlist.
            LOG.debug(
                "[ syncplay/landed ] %.1fs, wanted %.1fs (%+.0fms)%s",
                landed_ms / 1000.0,
                target_ms / 1000.0,
                -diff,
                " transcoding" if self.manager.is_transcoding() else "",
            )

            # A paused PAPlayer is never seeked.
            if abs(diff) > 500 and not (self._is_audio() and self._is_paused()):
                with self.manager.programmatic():
                    self._seek_and_settle(target_ms)

        self.tempo.note_settle()
        self.report_ready()

        deferred = self._deferred_unpause
        self._deferred_unpause = None
        if deferred is not None:
            # Group already Playing: the Unpause arrived during load and
            # was not applied. The server re-issues it on Ready; run it
            # here too so a dropped re-issue cannot leave us paused.
            # No rebind: see LiveClock.bind_origin_to_group.
            deferred = dict(deferred)
            deferred["_rebind_origin"] = False
            self.schedule(deferred)

    def ensure_paused(self) -> None:
        # Gate on isPlaying alone: during a gapless stream swap getTime()
        # can misbehave, and this is exactly the window a start hold must
        # be able to pause in.
        if self._player_active() and not self._is_paused():
            with self.manager.programmatic():
                self.player.pause()

    def ensure_playing(self) -> None:
        if self._player_active() and self._is_paused():
            with self.manager.programmatic():
                self.player.pause()  # toggles back to playing

    def stop_media(self) -> None:
        if self._has_media():
            with self.manager.programmatic():
                kodirpc.stop_player()  # not player.stop(): see kodirpc.stop_player

    # ------------------------------------------------------------------
    # Reports (SYNCPLAY.md §4)
    # ------------------------------------------------------------------

    def report_ready(self) -> None:
        self.manager.post_report(
            "syncplay_ready", position_s=self.reported_position_s()
        )

    def report_buffering(self) -> None:
        self.manager.post_report(
            "syncplay_buffering", position_s=self.reported_position_s(promise=False)
        )

    # ------------------------------------------------------------------
    # Group position reference (SYNCPLAY.md §11)
    # ------------------------------------------------------------------

    def set_reference(
        self, ticks: int, server_when_ms: Optional[float], playing: bool
    ) -> None:
        self._reference = (utils.ticks_to_ms(ticks), server_when_ms, playing)

    def reference_is_playing(self) -> bool:
        """Whether the group's last known state was playing.

        Distinct from estimate_position_ms(), which returns a position either
        way: a caller that wants to aim ahead of a moving group needs to know
        the group is actually moving.
        """
        if self._reference is None:
            return False

        return bool(self._reference[2])

    def estimate_position_ms(self) -> Optional[float]:
        """Estimated group position now, from the last command/beacon."""
        if self._reference is None:
            return None

        media_ms, when_ms, playing = self._reference

        if when_ms is None:
            return media_ms

        if not playing:
            return media_ms

        now: float = self.manager.server_now_ms()
        return media_ms + max(0.0, now - when_ms)

    # ------------------------------------------------------------------
    # Sync loop: the buffering watch
    # ------------------------------------------------------------------

    def start_loop(self) -> None:
        if self._loop_thread is not None and self._loop_thread.is_alive():
            return

        self._loop_stop.clear()
        self._loop_thread = threading.Thread(
            target=self._loop, name="kofin-syncplay-loop"
        )
        self._loop_thread.daemon = True
        self._loop_thread.start()

    def stop_loop(self) -> None:
        self._loop_stop.set()
        self.cancel_pending()
        self.tempo.reset()
        self._caching_since = None
        self._buffering_reported = False
        self.last_command = None
        self._deferred_unpause = None
        self._reference = None
        self.live.reset()

    def _loop(self) -> None:
        LOG.debug("--->[ syncplay loop ]")

        while not self._loop_stop.wait(0.25):
            try:
                if not self.manager.in_group() or not self._has_media():
                    self._caching_since = None
                    continue

                if self.manager.phase not in FOLLOWING:
                    continue

                self._watch_buffering()

                if self.manager.watching_own_media():
                    # A spectator on its own media is still in phase "synced",
                    # so fine sync is cancelled rather than measured against
                    # the group. cancel() is quiet when no pulse is in flight.
                    self.tempo.cancel("spectator playing own media")
                    continue

                if self.manager.phase == Phase.SYNCED and self._expecting_playback():
                    self.tempo.tick()
            except Exception as error:
                LOG.exception("SyncPlay loop error: %s", error)

        LOG.debug("---<[ syncplay loop ]")

    def _watch_buffering(self) -> None:
        """Debounced Player.Caching -> Buffering/Ready reports (§7)."""
        caching = bool(xbmc.getCondVisibility("Player.Caching"))

        if self._buffering_reported:
            # A recovery Ready must go out even if the group paused us in
            # the meantime, or the server keeps waiting on this member.
            if not caching:
                LOG.debug("[ syncplay/recovered ]")
                self._buffering_reported = False
                self._caching_since = None
                self.report_ready()

            return

        if not self._expecting_playback():
            self._caching_since = None
            return

        now = utils.local_ms() / 1000.0

        if caching:
            if self._caching_since is None:
                self._caching_since = now

            if now - self._caching_since > utils.BUFFERING_DEBOUNCE:
                LOG.debug("[ syncplay/buffering ]")
                self._buffering_reported = True
                self.report_buffering()
        else:
            self._caching_since = None

    def _expecting_playback(self) -> bool:
        return (
            self.last_command is not None
            and self.last_command.get("Command") == "Unpause"
        )

    # ------------------------------------------------------------------
    # Player plumbing
    # ------------------------------------------------------------------

    def _has_media(self) -> bool:
        try:
            return self.player.isPlaying() and self.player.getTime() >= 0
        except Exception:
            return False

    def _player_active(self) -> bool:
        try:
            return self.player.isPlaying()
        except Exception:
            return False

    def _is_audio(self) -> bool:
        try:
            return self.player.isPlayingAudio()
        except Exception:
            return False

    def _is_paused(self) -> bool:
        return bool(xbmc.getCondVisibility("Player.Paused"))

    def remaining_ms(self) -> Optional[float]:
        """What is left of the playing item, or None when its length is not
        known (a live stream, a source with no duration)."""
        try:
            total = self.player.getTotalTime()
            played = self.player.getTime()
        except Exception:
            return None

        if not total or total <= 0:
            return None

        return max(0.0, (total - played) * 1000.0)

    def _position_ms(self) -> float:
        """The playing position on the group's clock: the player clock, or
        for a live item the live clock (``LiveClock.source_offset_ms``) placed
        on the group reference's cycle of it."""
        try:
            player_ms = self.player.getTime() * 1000.0
        except Exception:
            return 0.0

        offset = self.live.source_offset_ms()

        if offset is None:
            return player_ms

        return utils.unwrap_live_ms(player_ms + offset, self.estimate_position_ms())

    # ------------------------------------------------------------------
    # Live items: the source clock
    # ------------------------------------------------------------------

    def _current_claim(self) -> Optional["Claim"]:
        current = getattr(self.manager, "current_claim", None)
        return current() if current is not None else None

    # -- the live clock (liveclock.py) -----------------------------------------

    def note_live_origin(self) -> None:
        self.live.note_origin()

    def live_on_source_clock(self) -> bool:
        return self.live.on_source_clock()

    def live_anchor_ms(self) -> Optional[float]:
        return self.live.anchor_ms()

    def reported_position_s(self, promise: bool = True) -> float:
        """The position a report carries. With ``promise``, a live member
        reports the group's own position: it converges by pulses and holds
        of its own, a private Seek in answer would be refused here anyway,
        and a Ready that reports the real reading — the proposer's, a
        delay ahead of its anchor — is one the server's ready barrier does
        not release on. Without it, the real reading: what a Buffering report
        must say, since the group pauses there."""
        if promise and self.live.claim() is not None:
            estimate = self.estimate_position_ms()

            if estimate is not None:
                return estimate / 1000.0

        return self._position_ms() / 1000.0

    def correct_position(self) -> None:
        """The fine-sync scheduler found a residual beyond what a pulse can
        close: seek to where the group will be once the seek has landed."""
        target_ms = self.estimate_position_ms()

        if target_ms is None:
            return

        with self._player_lock, self.manager.programmatic():
            self._seek_and_settle(target_ms + self.seek_lag_ms, stay_paused=False)

    def _clock_restart(
        self, target_ms: float, polls: int = 30
    ) -> Optional[tuple[float, float]]:
        """(local ms, position ms) at which the clock started advancing again
        after a seek, or None when no hold was seen (a correction too small to
        tell from playback, or a player that stayed paused).

        Kodi reports the target as soon as the seek is accepted and holds
        there while the pipeline refills; where the clock then restarts from
        is where the seek really landed. Bounded by polls, not by the wall
        clock: a test may freeze the clock.
        """
        held = None
        previous = None

        for _ in range(polls):
            position = self._position_ms()
            now = utils.local_ms()

            if previous is not None:
                if held is None:
                    if (
                        abs(position - previous) < 15
                        and abs(position - target_ms) < 1500
                    ):
                        held = position
                elif abs(position - held) > 30:
                    return now, position

            previous = position
            xbmc.sleep(50)

        return None

    def _seek_and_settle(self, target_ms: float, stay_paused: bool = True) -> None:
        """Seek and wait for the position to land.

        Aligning on a server command (Unpause/Seek), a fresh item, or a
        residual beyond the pulse budget is what seeks; a residual inside it
        is closed by a tempo pulse instead, and anything under the deadband is
        left alone.

        ``stay_paused`` is the caller's intent for afterwards. It matters
        because a seek can resume a paused player by itself — PAPlayer always
        does, and Android's VideoPlayer does too — so a caller that wants to
        stay paused has to undo that, and a caller about to resume must *not*,
        or the two fight and the player can end up stopped.
        """
        if self.live.seek_refused():
            if not self._live_seek_logged:
                self._live_seek_logged = True
                LOG.debug("[ syncplay/align ] skipped: live item, pulses only")

            return

        was_paused = self._is_paused()
        target_s = max(0.0, target_ms / 1000.0)
        self.tempo.before_seek()
        started = utils.local_ms()
        self.player.seekTime(target_s)

        # Give the async seek a beat before polling, or a nearby
        # pre-seek position would satisfy the check immediately.
        xbmc.sleep(150)
        deadline = started + utils.SEEK_SETTLE_TIMEOUT * 1000

        landed = False

        while utils.local_ms() < deadline:
            if abs(self._position_ms() - target_ms) < 2000:
                landed = True
                break

            xbmc.sleep(100)

        if landed and not was_paused:
            # Only a seek issued while playing is measured: a paused player's
            # clock never restarts. The residual a seek leaves is restart time
            # minus landing offset (see _clock_restart); smoothed, it is what
            # the next seek aims ahead by.
            restarted = self._clock_restart(target_ms)

            if restarted is not None:
                restart_ms, restart_pos = restarted
                lag = (restart_ms - started) - (restart_pos - target_ms)
                self.seek_lag_ms = 0.5 * self.seek_lag_ms + 0.5 * lag

        self.tempo.note_settle()

        if was_paused and stay_paused:
            # Audio's resume can land after the settle loop, so it is watched
            # for SEEK_REPAUSE_WINDOW_MS before the state is trusted.
            watch_until = utils.local_ms() + (
                utils.SEEK_REPAUSE_WINDOW_MS if self._is_audio() else 0
            )

            while True:
                if not self._is_paused():
                    LOG.debug("[ syncplay/seek ] re-pausing after the seek")
                    self.player.pause()
                    break

                if utils.local_ms() >= watch_until:
                    break

                xbmc.sleep(50)
