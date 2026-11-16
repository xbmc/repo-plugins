"""Fine position sync for SyncPlay: tempo pulses through Kodi's own tempo.

Stock Kodi plays a tempo only while "Sync playback to display" is on, and that
setting slaves the media clock to the panel. With the ``tempo`` feature
(kontell/xbmc #14 and #16) Kodi plays the tempo in the audio itself (a resample
ratio the engine keeps) and lets the audio be the clock, so the tempo works
with the display clock **off**. #37 keeps a tempo beyond the atempo threshold
from drawing a clock correction. #15 gives PAPlayer the same tempo, so music
takes pulses too, within limits of its own (``music_profile``).

Three parts here:

* :class:`KodiTempo` — the actuator: ``Player.SetTempo`` and the ``tempo``
  property over JSON-RPC, since Python's ``xbmc.Player`` has no tempo call,
  and ``Player.TempoEnabled`` as the test of whether the playing item can
  take one at all.
* :class:`TempoSession` — whether this group membership has fine sync: the
  setting, read at join and whenever it changes.
* :class:`PulseScheduler` — between group commands, measure the residual
  against the group estimate and close it with a *pulse*: a rate ``r`` held
  for ``T`` seconds displaces the position by ``(r − 1) × T``. One pulse,
  confirmed by reading the tempo back, then a quiet window before the
  residual is trusted again.

The planner is Kodi-free so the arithmetic is unit testable; the scheduler
takes its player reads through the controller.
"""

import math
import statistics
import threading
import time
from typing import TYPE_CHECKING, Any, Optional

import xbmc

from kofin.core import kodirpc, settings, state
from kofin.core.log import Logger
from kofin.sync.backends.api import capabilities
from kofin.syncplay import utils

if TYPE_CHECKING:
    from kofin.syncplay.playback import PlaybackController
    from kofin.syncplay.ports import Claim


LOG = Logger(__name__)

VIDEO_PLAYER = 1  # JSON-RPC's playerids
MUSIC_PLAYER = 0

# Kodi's tempo has three decimals: both players round to them, so a pulse is
# planned on that grid and its length worked out from the rate Kodi will
# really play.
RATE_STEP = 0.001
# A read within this of a rate is that rate: half a step, since a music pulse
# can be one step from 1.0. Kodi reads a tempo back as a float, 1.03 as
# 1.0299999713897705, far inside it.
RATE_MATCH = 0.0005

# Pulse planning. A pulse aims to last PULSE_AIM_S, so the rate scales with the
# residual between RATE_MIN and the user's ceiling (syncPlayMaxRate, default
# 25 %), and the duration stretches only once the rate is capped. Rates above
# RAMP_STEP are ramped in and out in RAMP_STEP increments every RAMP_DT — not
# seamless, just less of a jolt; the viewer may well notice the fast-forward.
RATE_MIN = 0.005
RATE_MAX_DEFAULT = 0.25
RATE_MAX_CEILING = 0.25
PULSE_AIM_S = 5.0
PULSE_MAX_S = 40.0
# A pulse squeezed shorter than this by the end of its item is not worth one.
PULSE_MIN_S = 1.0
RAMP_STEP = 0.05
RAMP_DT = 0.25
# Below this the residual is left alone: above the position reads' jitter,
# about a frame (42 ms at 24 fps) on Android.
DEADBAND_MS = 75.0
# Above the budget (syncPlayPulseBudget, default 5 s) a seek closes the
# residual instead; a skip is for gross errors only, because it is both jarring
# and, on Android, inaccurate. At 25 % a 5 s residual is a 20 s pulse, a 10 s
# residual (the slider max) is a 40 s pulse — one pulse closes the budget.
BUDGET_DEFAULT_MS = 5000.0
SEEK_BLACKOUT_S = 30.0
# What a seek aimed at the group's current position leaves behind before it
# has been measured on a device: restart time plus landing error.
SEEK_LAG_DEFAULT_MS = 500.0
# Residual samples the decision is taken over, at the loop's 250 ms: 3 s.
WINDOW_SAMPLES = 12
# After a pulse ends (or any seek or resume): this long before measuring. A
# tempo change reaches the clock once the audio already queued in the engine
# and the sink has played out at the old rate (VideoPlayer times its clock
# change by that delay), a few hundred milliseconds.
SETTLE_S = 1.0
# A pulse ends, settle included, at least this long before its item does: the
# item after it must start at 1.0.
END_MARGIN_S = 2.0
# A live item logs its reading on the source clock this often (debug).
LIVE_LOG_INTERVAL_S = 30.0
# How long the player gets to report a tempo kofin asked for. VideoPlayer
# takes it on its player thread within milliseconds; three seconds is a
# player that is not taking it.
APPLY_TIMEOUT_S = 3.0
# Pulses an item may refuse, or take and not play, before it is written off.
# One can be the moment: a demuxer read the speed message waited behind.
APPLY_MISSES = 2
# A read that disagrees with the last ask this soon after it is the player
# thread catching up, not someone else's change.
CONFIRM_GRACE_S = 1.0
# A tempo kofin did not ask for — the OSD's play speed — is put back to 1.0
# once it has held this long. Long enough that a test can step a member's
# position through Player.SetTempo, short enough that a viewer's speed costs a
# group a second or two to undo.
FOREIGN_GRACE_S = 2.0
# Give up when this many consecutive pulses went the same way and the residual
# regrew between them at a steady rate above GIVEUP_PPM: a rate mismatch, not
# jitter. A regrowth above GIVEUP_PPM_CEILING is not a rate at all but a step —
# a stall, a seek, an injection — and the rates of a real mismatch agree with
# each other within GIVEUP_SPREAD.
GIVEUP_PULSES = 3
GIVEUP_PPM = 3000.0
GIVEUP_PPM_CEILING = 60000.0
GIVEUP_SPREAD = 3.0


class Profile:
    """What a pulse may do on one player: the limits the planner and the
    scheduler read, so nothing else in them depends on the player."""

    def __init__(
        self,
        name: str,
        deadband_ms: float,
        rate_min: float,
        rate_max: float,
        aim_s: float,
        budget_ms: float,
        settle_s: float = SETTLE_S,
        end_margin_s: float = END_MARGIN_S,
    ) -> None:
        self.name = name
        self.deadband_ms = deadband_ms
        self.rate_min = rate_min
        # On Kodi's grid, so a rounded rate never lands above the ceiling.
        self.rate_max = max(
            RATE_STEP, math.floor(rate_max / RATE_STEP + 1e-6) * RATE_STEP
        )
        self.aim_s = aim_s
        self.budget_ms = budget_ms
        self.settle_s = settle_s
        self.end_margin_s = end_margin_s


VIDEO_DEFAULT = Profile(
    "video", DEADBAND_MS, RATE_MIN, RATE_MAX_DEFAULT, PULSE_AIM_S, BUDGET_DEFAULT_MS
)


# Music's limits (Profile), fixed rather than the sliders, which are video's.
# Members free-run about 200 ppm apart (12 ms a minute) and two sources of one
# song heard together fuse below about 30 ms, so the deadband sits there and
# the corrections are slight: from Kodi's 0.1 % step to 1 %, always within the
# atempo threshold, where the engine resamples rather than stretches — the
# pitch moves at most 17 cents and none of atempo's smearing reaches music. A
# 25 ms drift is a 0.2 % pulse for about 13 s. Beyond the budget a seek while
# playing is the cheaper sound.
MUSIC_DEADBAND_MS = 25.0
MUSIC_RATE_MAX = 0.01
MUSIC_PULSE_AIM_S = 15.0
MUSIC_BUDGET_MS = 500.0
ATEMPO_SETTING = "audiooutput.atempothreshold"  # percent
CROSSFADE_SETTING = "musicplayer.crossfade"  # seconds


def music_profile(
    atempo_threshold: Optional[float] = None, crossfade: Optional[float] = None
) -> Profile:
    """Music's limits on a Kodi whose atempo threshold (percent) and
    crossfade (seconds) are as given; an unreadable setting counts as
    Kodi's default."""
    rate_max = MUSIC_RATE_MAX

    if isinstance(atempo_threshold, (int, float)) and atempo_threshold > 0:
        rate_max = min(rate_max, atempo_threshold / 100.0 - RATE_STEP)

    fade = crossfade if isinstance(crossfade, (int, float)) and crossfade > 0 else 0

    return Profile(
        "music",
        MUSIC_DEADBAND_MS,
        RATE_STEP,
        rate_max,
        MUSIC_PULSE_AIM_S,
        MUSIC_BUDGET_MS,
        # A track queued behind the playing one is made at the tempo in force,
        # and a crossfade starts it that much before this one ends.
        end_margin_s=END_MARGIN_S + fade,
    )


def video_profile() -> Profile:
    """Video's limits, with the user's budget and speed ceiling."""
    budget_ms = float(settings.get_int("syncPlayPulseBudget") or BUDGET_DEFAULT_MS)
    rate_max = (settings.get_int("syncPlayMaxRate") or RATE_MAX_DEFAULT * 100) / 100.0
    return Profile(
        "video",
        DEADBAND_MS,
        RATE_MIN,
        min(RATE_MAX_CEILING, max(RATE_MIN, rate_max)),
        PULSE_AIM_S,
        budget_ms,
    )


def plan_pulse(
    residual_ms: float, profile: Profile = VIDEO_DEFAULT
) -> Optional[tuple[float, float]]:
    """The (rate, seconds) pulse that closes ``residual_ms``, or None.

    Positive residual means this member is behind the group, so the rate is
    above 1. None inside the deadband. The caller checks the budget first;
    here a residual past it simply saturates at the profile's ceiling for
    PULSE_MAX_S. The rate is on Kodi's three-decimal grid and the length is
    worked out from it, so the plan moves what it says.
    """
    magnitude = abs(residual_ms)

    if magnitude <= profile.deadband_ms:
        return None

    step = min(
        profile.rate_max,
        max(profile.rate_min, magnitude / (profile.aim_s * 1000.0)),
    )
    step = max(RATE_STEP, round(step / RATE_STEP) * RATE_STEP)
    seconds = min(PULSE_MAX_S, magnitude / (step * 1000.0))
    rate = 1.0 + step if residual_ms > 0 else 1.0 - step
    return round(rate, 3), seconds


def _ramp(rate: float) -> tuple[list[float], float]:
    """The steps a pulse to ``rate`` ramps through between 1.0 and the rate,
    and what its two ramps move together, in seconds of content."""
    step = rate - 1.0
    sign = 1.0 if step > 0 else -1.0
    steps = int(math.ceil(abs(step) / RAMP_STEP - 1e-9))
    intermediate = [round(1.0 + sign * RAMP_STEP * k, 3) for k in range(1, steps)]
    return intermediate, 2.0 * sum((value - 1.0) * RAMP_DT for value in intermediate)


def pulse_schedule(rate: float, seconds: float) -> list[tuple[float, float]]:
    """The tempo writes that make up one pulse: (offset_s, rate) pairs,
    the last of them (…, 1.0).

    A rate within RAMP_STEP of 1.0 is one write and one return. Beyond that it
    is ramped: RAMP_STEP increments every RAMP_DT up to the rate, held, then
    stepped back down — and the hold is shortened by what the ramps already
    displace, so the whole schedule still moves (rate − 1) × seconds.
    """
    intermediate, displacement = _ramp(rate)

    if not intermediate:
        return [(0.0, rate), (seconds, 1.0)]

    hold = max(2.0 * RAMP_DT, seconds - displacement / (rate - 1.0))

    schedule = []
    offset = 0.0

    for value in intermediate:
        schedule.append((offset, value))
        offset += RAMP_DT

    schedule.append((offset, rate))
    offset += hold

    for value in reversed(intermediate):
        schedule.append((offset, value))
        offset += RAMP_DT

    schedule.append((offset, 1.0))
    return schedule


def fit_pulse(rate: float, seconds: float, room: float) -> Optional[float]:
    """``seconds`` shortened until the pulse's whole schedule, ramps included,
    ends within ``room`` seconds; None when there is no room for a pulse at
    this rate. Only the hold shortens, so a fitted pulse still moves
    (rate − 1) × the seconds returned."""
    intermediate, displacement = _ramp(rate)

    if not intermediate:
        if seconds <= room:
            return seconds

        return room if room >= PULSE_MIN_S else None

    ramps = 2.0 * len(intermediate) * RAMP_DT
    lead = displacement / (rate - 1.0)  # seconds the ramps stand in for

    if ramps + max(2.0 * RAMP_DT, seconds - lead) <= room:
        return seconds

    hold = room - ramps
    return hold + lead if hold >= 2.0 * RAMP_DT else None


def regrowth_ppm(residual_ms: float, elapsed_s: float) -> float:
    """How fast the residual came back, as a rate error in ppm."""
    if elapsed_s <= 0:
        return 0.0

    return residual_ms / elapsed_s * 1000.0


def takes_correction() -> bool:
    """Whether Kodi's ``Player.SetTempo`` takes ``correction`` (kontell/xbmc
    #38): a tempo the player plays as any other while the GUI shows none of
    it. Kodi refuses a parameter its schema does not name, so the schema is
    read rather than the call tried."""
    schema = kodirpc.call(
        "JSONRPC.Introspect",
        {
            "getdescriptions": False,
            "filter": {"id": "Player.SetTempo", "type": "method"},
        },
    )

    try:
        params = schema["methods"]["Player.SetTempo"]["params"]
    except (KeyError, TypeError):
        return False

    return any(
        isinstance(param, dict) and param.get("name") == "correction"
        for param in params
    )


class KodiTempo:
    """Kodi's own tempo on one player.

    Python's ``xbmc.Player`` has no tempo call, so the actuator is JSON-RPC:
    ``Player.SetTempo``, and the ``tempo`` property, which reads what the
    player has taken. Kodi refuses a tempo while paused and keeps the one in
    force across a pause, and refuses one for an item that cannot take it — a
    realtime stream with no time range, a bitstream track — which is what
    ``Player.TempoEnabled`` answers for the playing item.

    Every rate goes as a correction where Kodi takes the flag: no seek bar
    for the change or its end, and the OSD reads normal speed throughout,
    while the ``tempo`` property still reads the rate. Without it each change
    puts the seek bar up for three seconds, labelled with the rate.
    """

    def __init__(self, playerid: int, correction: Optional[bool] = None) -> None:
        self.playerid = playerid
        # Kodi's schema does not change in a process: a caller that holds the
        # answer passes it, and only a caller without one asks.
        self.correction = takes_correction() if correction is None else correction

    def set(self, rate: float) -> bool:
        """Ask for ``rate``; True when Kodi took the call."""
        # Always a float: Kodi reads the parameter as a double, and a JSON
        # integer would be refused as invalid.
        params = {"playerid": self.playerid, "tempo": float(rate)}

        if self.correction:
            params["correction"] = True

        return isinstance(kodirpc.call("Player.SetTempo", params), dict)

    def read(self) -> Optional[float]:
        """The tempo the player is taking, or None when it cannot be read."""
        result = kodirpc.player_properties(["tempo"], self.playerid)

        if result is None:
            return None

        try:
            return float(result["tempo"])
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def enabled() -> bool:
        """Whether the playing item can take a tempo now."""
        return bool(xbmc.getCondVisibility("Player.TempoEnabled"))


def _player_active(playerid: int) -> Optional[bool]:
    """True or False when Kodi answered; None when it could not be asked."""
    active = kodirpc.active_players()

    if not isinstance(active, list):
        return None

    return any(
        isinstance(player, dict) and player.get("playerid") == playerid
        for player in active
    )


def settle_left_rate(reason: str = "", correction: Optional[bool] = None) -> bool:
    """Put 1.0 back where a kofin pulse left its rate in force; True once
    nothing is left owed.

    The record (``state.syncplay_pulse``) is written when a pulse asks for a
    rate and dropped when a read shows Kodi took 1.0 back, not when the call
    is accepted. It outlives a refusal — a pulse cut while paused — and a
    service generation that ended mid-pulse, which would otherwise leave the
    item playing fast or slow to its end. It is dropped unasked when the
    player is already at 1.0 (a new item starts there) or not playing.
    """
    record = state.syncplay_pulse()

    if not record:
        return True

    playerid = record.get("player")

    if not isinstance(playerid, int):
        state.clear_syncplay_pulse()
        return True

    actuator = KodiTempo(playerid, correction)
    current = actuator.read()

    if current is None:
        if _player_active(playerid) is False:
            state.clear_syncplay_pulse()
            return True

        return False

    if abs(current - 1.0) < RATE_MATCH:
        state.clear_syncplay_pulse()
        return True

    if not actuator.set(1.0):
        return False  # still paused: the next resume tries again

    taken = actuator.read()

    if taken is None or abs(taken - 1.0) >= RATE_MATCH:
        return False  # still owed: the next resume, tick or start tries again

    state.clear_syncplay_pulse()
    LOG.debug("[ syncplay/pulse ] %.3fx left in force%s; back to 1.0x", current, reason)
    return True


class PulseScheduler:
    """Closes the residual between commands with confirmed tempo pulses.

    Driven by the controller's 250 ms loop through :meth:`tick`; told about
    every command and seek so a pulse is never left running across one.

    Nothing here waits under ``_lock``: a write is one JSON-RPC call, and its
    confirmation is a later tick finding the tempo read back, not a sleep.
    ``cancel()`` and ``before_seek()`` take the same lock on the command
    thread, and a scheduled Pause must not wait on the actuator. The one
    corrective seek goes through the controller with the lock dropped
    (:meth:`tick`).

    **A pulse never outlives a pause.** A pulse cut while paused — by a
    viewer's pause, or a command arriving on a paused player — leaves its 1.0
    owed: the next playing tick, and every resume
    (``SyncPlayManager.on_resumed``), put it back (:meth:`settle_owed`).
    """

    def __init__(self, controller: "PlaybackController") -> None:
        self.controller = controller
        # The playing item's limits once it is armed.
        self.profile: Optional[Profile] = None
        self.actuator: Optional[KodiTempo] = None
        # PlaySessionId the scheduler is armed for.
        self._session_id: Optional[str] = None
        self._window: list[float] = []
        # The running pulse: its remaining writes.
        self._pulse: Optional[dict[str, Any]] = None
        # A write waiting to be read back.
        self._awaiting: Optional[dict[str, Any]] = None
        # An ended pulse, moved measured after the settle.
        self._measure: Optional[dict[str, Any]] = None
        self._asked = 1.0  # the last tempo asked for
        self._asked_at = 0.0
        self._marked = False  # the left-rate record is ours to clear
        # Whether Player.SetTempo takes `correction`.
        self._correction: Optional[bool] = None
        self._misses = 0  # pulses this item refused or did not play
        self._settle_until = 0.0
        self._seek_blackout_until = 0.0
        # Per finished pulse: its direction, timing and regrowth.
        self._history: list[dict[str, Any]] = []
        self._gave_up = False
        self._unarmed_logged = False
        self._disabled_logged = False
        self._end_logged = False
        self._foreign_logged = False
        # When a tempo kofin did not ask for was seen.
        self._foreign_since: Optional[float] = None
        self._session_time_logged = False
        # A live item (utils.claim_is_live): never seeked, and a forward
        # pulse Kodi ends at the live edge ends fine sync (LIVE_EDGE_PULSES).
        self._live = False
        self._edge_pulses = 0
        self._live_logged_at = 0.0
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Arming
    # ------------------------------------------------------------------

    def _session_active(self) -> bool:
        active = getattr(self.controller.manager, "fine_sync_active", None)
        return bool(active()) if active is not None else False

    def _arm_for_current(self) -> Optional["Claim"]:
        """Arm for the playing item if it is not the one armed. Under the
        lock; returns the claim, or None outside a fine-sync session."""
        claim: Optional[Claim] = self.controller.manager.current_claim()

        if not claim or not self._session_active():
            return None

        if claim.get("PlaySessionId") != self._session_id:
            self._arm(claim)

        return claim

    def _arm(self, claim: "Claim") -> None:
        """Bind to the playing item, or note that it has no fine sync."""
        self._session_id = claim.get("PlaySessionId")
        self._window = []
        self._pulse = None
        self._awaiting = None
        self._measure = None
        self._history = []
        self._gave_up = False
        self._live = utils.claim_is_live(claim)
        self._edge_pulses = 0
        self._misses = 0
        self._disabled_logged = False
        self._end_logged = False
        self._foreign_logged = False
        self._foreign_since = None

        audio = self.controller._is_audio()

        if audio and self._live:
            # A radio stream through PAPlayer has no time range to move in.
            self.profile = None
            self.actuator = None

            if not self._unarmed_logged:
                self._unarmed_logged = True
                LOG.debug(
                    "[ syncplay/tempo ] %s is live audio; command-only sync",
                    claim.get("Id"),
                )

            return

        self._unarmed_logged = False

        if audio:
            self.profile = music_profile(
                kodirpc.kodi_setting(ATEMPO_SETTING),
                kodirpc.kodi_setting(CROSSFADE_SETTING),
            )
            self.actuator = KodiTempo(MUSIC_PLAYER, self._takes_correction())
        else:
            self.profile = video_profile()
            self.actuator = KodiTempo(VIDEO_PLAYER, self._takes_correction())

        LOG.debug(
            "[ syncplay/tempo ] fine sync armed for %s "
            "(%s: budget %.0fms, up to %.1f%%%s%s)",
            claim.get("Id"),
            self.profile.name,
            self.profile.budget_ms,
            self.profile.rate_max * 100.0,
            ", live: on the source clock, pulses only" if self._live else "",
            "" if self.actuator.correction else ", shown on the OSD",
        )

    def _takes_correction(self) -> bool:
        """``takes_correction()``, asked of Kodi once per scheduler."""
        if self._correction is None:
            self._correction = takes_correction()

        return bool(self._correction)

    def armed(self) -> bool:
        """Whether the playing item takes pulses now: armed, not given up,
        and able to take a tempo (``Player.TempoEnabled``)."""
        with self._lock:
            self._arm_for_current()

            if self.profile is None or self._gave_up:
                return False

        return KodiTempo.enabled()

    def _write_off(self, why: str) -> None:
        """This item takes no pulses after all: command-only until the next."""
        LOG.warning("[ syncplay/pulse ] %s; command-only sync for this item", why)
        self.profile = None

    def _missed(self, why: str, now: float) -> None:
        """A pulse Kodi refused, or took and did not play. A first miss waits
        out a settle and tries again; a second one, or an item that now cannot
        take a tempo at all, writes the item off."""
        self._misses += 1

        if self._misses >= APPLY_MISSES or not KodiTempo.enabled():
            self._write_off(why)
            return

        LOG.warning("[ syncplay/pulse ] %s; trying again after a settle", why)
        self._settle(None, now, measured=False)

    def can_close(self, residual_ms: float) -> bool:
        """Whether fine sync will take this residual, so a seek is not needed.

        A live item has no seek to fall back on, so every residual is fine
        sync's — saturated pulses close a large one over time. An item that
        cannot take a tempo now (``Player.TempoEnabled``) leaves it to a seek.
        """
        with self._lock:
            self._arm_for_current()  # a command can ask before the first tick

            if self.profile is None or self._gave_up:
                return False

            live = self._live
            budget_ms = self.profile.budget_ms

        if not KodiTempo.enabled():
            return False

        return live or abs(residual_ms) <= budget_ms

    def reset(self) -> None:
        with self._lock:
            self.cancel("stop")

            if self._marked:
                # The last look this scheduler gets: read the 1.0 back now (a
                # stopped player clears the record too) rather than leave it.
                self._settle_left(time.time())

            self.profile = None
            self.actuator = None
            self._session_id = None
            self._window = []
            self._history = []
            self._gave_up = False
            self._session_time_logged = False

    # ------------------------------------------------------------------
    # The actuator
    # ------------------------------------------------------------------

    def _set(self, rate: float, now: float) -> bool:
        """Ask for ``rate``; False when Kodi refused it."""
        actuator = self.actuator

        if actuator is None or not actuator.set(rate):
            return False

        self._asked = rate
        self._asked_at = now

        if abs(rate - 1.0) >= RATE_MATCH and not self._marked:
            state.publish_syncplay_pulse({"player": actuator.playerid})
            self._marked = True

        return True

    def _return_to_one(self, now: float) -> bool:
        """Ask for 1.0, which stays owed when Kodi refuses it. The left-rate
        record stays until a read shows 1.0 (``_back_at_one``)."""
        if self.actuator is None or not self.actuator.set(1.0):
            return False

        self._asked = 1.0
        self._asked_at = now
        return True

    def settle_owed(self) -> None:
        """Put back a rate a cut pulse left in force, when nothing of ours is
        running: on a resume, in a group or not, and on the playing tick."""
        with self._lock:
            if self._pulse is not None or self._awaiting is not None:
                return

            if not self._marked and not state.syncplay_pulse():
                return

            self._settle_left(time.time())

    def _settle_left(self, now: float) -> None:
        if settle_left_rate(" after a pause", self._correction):
            self._marked = False
            self._asked = 1.0
            self._asked_at = now

    def _back_at_one(self, now: float) -> None:
        """A read shows 1.0: the end of a pulse confirmed, a new item (which
        starts there), or an owed 1.0 put back from a resume. Only here does
        the left-rate record go."""
        self._asked = 1.0
        self._asked_at = now

        if self._marked:
            state.clear_syncplay_pulse()
            self._marked = False

    # ------------------------------------------------------------------
    # The loop
    # ------------------------------------------------------------------

    def tick(self) -> None:
        with self._lock:
            seek = self._tick()

        if seek is not None:
            # Outside the lock: the controller takes the player lock, and the
            # command path takes that one first before asking for ours.
            self.controller.correct_position()
            self.note_settle()

    def _tick(self) -> Optional[float]:
        """One scheduling step under the lock. Returns the residual to seek
        away, or None."""
        if self._arm_for_current() is None or self.profile is None:
            return None

        controller = self.controller
        now = time.time()

        if controller._is_paused():
            if self._pulse is not None or self._awaiting is not None:
                self._cut("pause", now)

            self._window = []
            return None

        if self._marked and self._pulse is None and self._awaiting is None:
            # A rate of ours in force with no pulse running is one a pause
            # refused to take back: owed, and the player is playing again.
            self._settle_left(now)

        current = self.actuator.read() if self.actuator is not None else None

        if self._awaiting is not None:
            self._check_awaiting(current, now)
            return None

        if self._pulse is not None:
            self._advance_pulse(current, now)
            return None

        if current is not None and self._changed_elsewhere(current, now):
            if abs(current - 1.0) < RATE_MATCH:
                self._back_at_one(now)
            else:
                # Someone else's tempo: measure nothing while it holds, and put
                # 1.0 back once it has held FOREIGN_GRACE_S.
                self._window = []

                if self._foreign_since is None:
                    self._foreign_since = now
                elif now - self._foreign_since >= FOREIGN_GRACE_S:
                    self._foreign(current, now)

                return None
        elif self._foreign_since is not None:
            # It was taken back by whoever set it: let the clock catch up.
            self._foreign_since = None
            self._settle_until = max(self._settle_until, now + self.profile.settle_s)

        if self._gave_up or not controller.reference_is_playing():
            self._window = []
            return None

        if now < self._settle_until:
            return None

        if self._measure is not None:
            self._report_moved(now)

        estimate = controller.estimate_position_ms()

        if estimate is None:
            return None

        if self._live and not controller.live_on_source_clock():
            # The group is anchored on session time (a proposer without
            # the clock) or this member cannot read its own: nothing to
            # converge on — the commands keep it tuned together.
            if not self._session_time_logged:
                self._session_time_logged = True
                LOG.debug(
                    "[ syncplay/tempo ] live group is on session time; "
                    "no pulses until a source clock is shared"
                )
            self._window = []
            return None

        position = controller._position_ms()
        self._window.append(estimate - position)

        if self._live and now - self._live_logged_at >= LIVE_LOG_INTERVAL_S:
            # Every member's reading on the one clock, against the group, at a
            # cadence a log can be read at.
            self._live_logged_at = now
            LOG.debug(
                "[ syncplay/live ] %.1fs on the source clock, %+.0fms off the group",
                (position - utils.LIVE_PTS_EPOCH_S * 1000.0) / 1000.0,
                estimate - position,
            )

        del self._window[:-WINDOW_SAMPLES]

        if len(self._window) < WINDOW_SAMPLES:
            return None

        residual = statistics.median(self._window)
        # The window's spread is this member's own read noise between pulses,
        # which is what a deadband has to sit above.
        LOG.debug(
            "[ syncplay/window ] %+.0fms, spread %.0fms",
            residual,
            max(self._window) - min(self._window),
        )

        # Beyond the budget a seek is the tool — once, for gross errors, and
        # only when every sample in the window agrees. Otherwise — the seek's
        # blackout holds, or the residual straddles the budget — pulses close
        # it after all, saturated at the rate ceiling for PULSE_MAX_S. A live
        # stream has no seek, so a live residual beyond the budget takes the
        # saturated pulses instead, as many as it needs.
        budget_ms = self.profile.budget_ms

        if (
            abs(residual) > budget_ms
            and not self._live
            and now >= self._seek_blackout_until
            and all(abs(sample) > budget_ms for sample in self._window)
        ):
            self._seek_blackout_until = now + SEEK_BLACKOUT_S
            self._window = []
            LOG.debug(
                "[ syncplay/align ] %+.0fms is beyond the pulse budget: seeking",
                residual,
            )
            return residual

        plan = plan_pulse(residual, self.profile)

        if plan is None:
            return None

        if self._losing(residual, now):
            self._give_up()
            return None

        self._start_pulse(plan[0], plan[1], residual, now)
        return None

    # ------------------------------------------------------------------
    # Pulses
    # ------------------------------------------------------------------

    def _fit_to_item(self, rate: float, seconds: float) -> Optional[float]:
        """The pulse's seconds once the end of its item is allowed for, or None
        when there is no room for one (``fit_pulse``: its ramps have to fit
        too). A live stream has no end."""
        if self._live:
            return seconds

        remaining_ms = self.controller.remaining_ms()

        if remaining_ms is None:
            return seconds

        profile = self.profile
        assert profile is not None  # only called armed (_start_pulse)
        room = remaining_ms / 1000.0 - profile.settle_s - profile.end_margin_s
        return fit_pulse(rate, seconds, room)

    def _start_pulse(
        self, rate: float, seconds: float, residual: float, now: float
    ) -> None:
        self._window = []

        if not KodiTempo.enabled():
            if not self._disabled_logged:
                self._disabled_logged = True
                LOG.debug(
                    "[ syncplay/pulse ] %+.0fms left: the item cannot take a tempo now",
                    residual,
                )
            return

        fitted = self._fit_to_item(rate, seconds)

        if fitted is None:
            if not self._end_logged:
                self._end_logged = True
                LOG.debug(
                    "[ syncplay/pulse ] %+.0fms left: too close to the end for a pulse",
                    residual,
                )
            return

        schedule = pulse_schedule(rate, fitted)
        first = schedule[0][1]

        if not self._set(first, now):
            # Paused since the tick looked: the pause is the cut, not the item.
            if not self.controller._is_paused():
                self._missed("%.3fx refused" % first, now)
            return

        self._awaiting = {
            "kind": "start",
            "rate": first,
            "asked": now,
            "deadline": now + APPLY_TIMEOUT_S,
            "plan": (rate, fitted, residual, schedule),
        }

    def _check_awaiting(self, current: Optional[float], now: float) -> None:
        """A write is out: has the player taken it yet?"""
        waiting = self._awaiting
        assert waiting is not None  # only called awaiting (_tick)
        confirmed = current is not None and abs(current - waiting["rate"]) < RATE_MATCH

        if not confirmed and now < waiting["deadline"]:
            return

        self._awaiting = None

        if waiting["kind"] == "start":
            self._pulse_started(waiting, confirmed, now)
        else:
            self._pulse_ended(waiting, confirmed, now)

    def _pulse_started(
        self, waiting: dict[str, Any], confirmed: bool, now: float
    ) -> None:
        rate, seconds, residual, schedule = waiting["plan"]

        if not confirmed:
            # The player took the call and never played the rate: do not leave
            # it asked for.
            self._return_to_one(now)
            self._missed(
                "%.3fx not applied within %.0fs" % (waiting["rate"], APPLY_TIMEOUT_S),
                now,
            )
            return

        LOG.debug(
            "[ syncplay/pulse ] %+.0fms: %.3fx for %.1fs%s (applied after %.0fms)",
            residual,
            rate,
            seconds,
            " ramped" if len(schedule) > 2 else "",
            (now - waiting["asked"]) * 1000.0,
        )
        self._pulse = {
            "rate": rate,
            "seconds": seconds,
            "residual": residual,
            "decided_at": waiting["asked"],
            # Where the player clock stood when the rate took: what the pulse
            # moved is read against it once the pulse has played out.
            "start": (now, self.controller._position_ms()),
            # The remaining writes, at absolute times; the last one is 1.0.
            "writes": [(now + offset, value) for offset, value in schedule[1:]],
        }

    def _changed_elsewhere(self, current: float, now: float) -> bool:
        """Whether the tempo read is not the one kofin last asked for, and the
        player has had time to take the ask."""
        return (
            abs(current - self._asked) >= RATE_MATCH
            and now - self._asked_at >= CONFIRM_GRACE_S
        )

    def _advance_pulse(self, current: Optional[float], now: float) -> None:
        """Write whatever the schedule has due. Several overdue at once — a
        late tick — collapse to the latest; the final 1.0 ends the pulse."""
        pulse = self._pulse
        assert pulse is not None  # only called pulsing (_tick)

        if current is not None and self._changed_elsewhere(current, now):
            if abs(current - 1.0) < RATE_MATCH:
                self._ended_by_kodi(pulse, now)
            else:
                self._foreign(current, now)
            return

        writes = pulse["writes"]
        due = None

        while writes and now >= writes[0][0]:
            due = writes.pop(0)

        if due is None:
            return

        if not writes:
            self._end_pulse(now)
        elif not self._set(due[1], now):
            self._cut("a refused step", now)

    def _end_pulse(self, now: float) -> None:
        pulse = self._pulse
        self._pulse = None

        if not self._return_to_one(now):
            LOG.warning("[ syncplay/pulse ] return to 1.0x refused; owed")
            self._settle(pulse, now, measured=False)
            return

        self._awaiting = {
            "kind": "end",
            "rate": 1.0,
            "asked": now,
            "deadline": now + APPLY_TIMEOUT_S,
            "pulse": pulse,
        }

    def _pulse_ended(
        self, waiting: dict[str, Any], confirmed: bool, now: float
    ) -> None:
        pulse = waiting["pulse"]

        if confirmed:
            self._back_at_one(now)
        else:
            LOG.warning("[ syncplay/pulse ] return to 1.0x not confirmed; owed")

        if self._live and pulse["rate"] > 1.0:
            self._edge_pulses = 0  # fed to the end: not the edge

        self._settle(pulse, now, measured=confirmed)

    def _ended_by_kodi(self, pulse: dict[str, Any], now: float) -> None:
        """Kodi put the tempo back to 1.0 during the pulse. On a live stream
        playing faster than its source that is the live edge."""
        self._pulse = None
        self._back_at_one(now)

        if self._live and pulse["rate"] > 1.0:
            self._edge_pulses += 1
            LOG.debug(
                "[ syncplay/pulse ] Kodi returned to 1.0x at the live edge (%d of %d)",
                self._edge_pulses,
                utils.LIVE_EDGE_PULSES,
            )

            if self._edge_pulses >= utils.LIVE_EDGE_PULSES:
                self._give_up_edge()
        else:
            LOG.debug("[ syncplay/pulse ] Kodi returned to 1.0x; pulse over")

        self._settle(pulse, now, measured=False)

    def _foreign(self, current: float, now: float) -> None:
        """A tempo kofin did not ask for — a viewer's play speed in the OSD.
        A group's speed is 1.0: put it back."""
        if not self._foreign_logged:
            self._foreign_logged = True
            LOG.debug(
                "[ syncplay/tempo ] %.3fx set outside fine sync; back to 1.0x", current
            )

        pulse = self._pulse
        self._pulse = None
        self._awaiting = None
        self._foreign_since = None
        self._return_to_one(now)
        self._settle(pulse, now, measured=False)

    def _settle(
        self, pulse: Optional[dict[str, Any]], now: float, measured: bool
    ) -> None:
        """A pulse is over: a quiet window before measuring again, and its
        outcome read once the window has passed."""
        profile = self.profile
        self._settle_until = now + (profile.settle_s if profile else SETTLE_S)
        self._window = []
        self._measure = pulse if measured else None

        if pulse is not None:
            self._remember(pulse, now)

    def _report_moved(self, now: float) -> None:
        """What the pulse moved, read off the player clock: the change in
        position less the time that passed. Logged against what it was asked
        to move, which is the actuator's accuracy."""
        pulse = self._measure
        assert pulse is not None  # only called measuring (_tick)
        self._measure = None
        started, start_ms = pulse["start"]
        moved = (self.controller._position_ms() - start_ms) - (now - started) * 1000.0
        LOG.debug(
            "[ syncplay/pulse ] moved %+.0fms (wanted %+.0fms)",
            moved,
            (pulse["rate"] - 1.0) * pulse["seconds"] * 1000.0,
        )

    def _give_up_edge(self) -> None:
        self._gave_up = True
        LOG.debug(
            "[ syncplay/pulse ] giving up: at the live edge — Kodi ended %d forward "
            "pulses in a row; this member follows the feed",
            self._edge_pulses,
        )

    def _cut(self, reason: str, now: float) -> bool:
        """Under the lock: no pulse runs on. Returns whether one was."""
        pulse = self._pulse
        waiting = self._awaiting
        self._pulse = None
        self._awaiting = None
        self._measure = None

        if pulse is None and waiting is None:
            return False

        self._return_to_one(now)
        LOG.debug("[ syncplay/pulse ] cut by %s", reason)
        profile = self.profile
        self._settle_until = now + (profile.settle_s if profile else SETTLE_S)

        if pulse is not None:
            self._remember(pulse, now)

        return True

    def cancel(self, reason: str) -> None:
        """A command or seek is about to act: no pulse may run across it.

        Returns at once — it asks for 1.0 and waits for nothing; while paused,
        the 1.0 is owed to the resume. It is also a fresh start for the
        give-up test (that is about the residual regrowing between pulses on
        its own, and a command moves the position by hand) and for a member
        that had given up: a real rate mismatch will earn the verdict again
        within three pulses, and the user is told only once per group either
        way.
        """
        with self._lock:
            self._window = []
            self._history = []
            self._gave_up = False
            self._cut(reason, time.time())

    def before_seek(self) -> None:
        """Back to 1.0 before a seek lands: no pulse runs across a seek. Kodi
        keeps a tempo across one, and the speed message and the seek take the
        player's one queue in order, so nothing has to be waited for."""
        self.cancel("seek")

    def note_settle(self) -> None:
        """A seek or resume just landed: measure again only once it has played
        out — and, as with a command, regrowth is counted from here, not
        across the seek."""
        with self._lock:
            self._window = []
            self._history = []
            self._measure = None
            profile = self.profile
            self._settle_until = max(
                self._settle_until,
                time.time() + (profile.settle_s if profile else SETTLE_S),
            )

    # ------------------------------------------------------------------
    # Giving up
    # ------------------------------------------------------------------

    def _remember(self, pulse: dict[str, Any], ended_at: float) -> None:
        """Fold a finished pulse into the give-up history."""
        direction = 1 if pulse["rate"] > 1.0 else -1
        previous = self._history[-1] if self._history else None
        elapsed = (
            pulse["decided_at"] - previous["ended_at"] if previous is not None else 0.0
        )
        self._history.append(
            {
                "direction": direction,
                "ppm": regrowth_ppm(pulse["residual"], elapsed) if previous else 0.0,
                "ended_at": ended_at,
            }
        )
        del self._history[:-GIVEUP_PULSES]

    def _losing(self, residual: float, now: float) -> bool:
        """Whether the residual is a rate mismatch pulses cannot keep up with.

        True once GIVEUP_PULSES pulses have gone the same way and every one of
        them, this candidate included, found the residual regrown at a
        steady, plausible rate above GIVEUP_PPM since the previous pulse
        ended.
        """
        if len(self._history) < GIVEUP_PULSES:
            return False

        direction = 1 if residual > 0 else -1
        last = self._history[-1]
        rates = [entry["ppm"] for entry in self._history[1:]] + [
            regrowth_ppm(residual, now - last["ended_at"])
        ]

        if not all(entry["direction"] == direction for entry in self._history):
            return False

        magnitudes = [abs(rate) for rate in rates]

        return (
            all((rate > 0) == (direction > 0) for rate in rates)
            and min(magnitudes) > GIVEUP_PPM
            and max(magnitudes) < GIVEUP_PPM_CEILING
            and max(magnitudes) <= GIVEUP_SPREAD * min(magnitudes)
        )

    def _give_up(self) -> None:
        self._gave_up = True
        LOG.warning(
            "[ syncplay/pulse ] giving up: the residual regrows faster than "
            "%.0f ppm across %s pulses — a rate mismatch, not drift. Is "
            "'Sync playback to display' on?",
            GIVEUP_PPM,
            GIVEUP_PULSES,
        )
        self.controller.manager.notify_rate_mismatch()


class TempoSession:
    """Whether this group membership has fine sync: the setting, read at join
    and again when it changes.

    The actuator is the player's own, and an item that cannot take a tempo
    says so through ``Player.TempoEnabled`` when it plays
    (:class:`PulseScheduler`).
    """

    def __init__(self) -> None:
        self.active = False

    def begin(self) -> None:
        """Arm fine sync for the group just joined, when the setting allows."""
        if self.active:
            return

        if not settings.get_bool("syncPlayTempo"):
            LOG.debug("[ syncplay/tempo ] fine sync is off in settings")
            return

        # Without the tempo feature this member keeps to the group's commands.
        if not capabilities.has("tempo"):
            LOG.debug(
                "[ syncplay/tempo ] fine sync needs Kodi's tempo set; this Kodi "
                "plays on the group's commands"
            )
            return

        self.active = True
        LOG.debug("[ syncplay/tempo ] fine sync armed (Kodi's tempo)")

    def end(self) -> None:
        if not self.active:
            return

        self.active = False
        LOG.debug("[ syncplay/tempo ] fine sync disarmed")
