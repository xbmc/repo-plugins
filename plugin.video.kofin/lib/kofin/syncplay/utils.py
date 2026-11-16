"""Pure helpers for SyncPlay: time conversions and protocol constants.

Kept free of Kodi imports so the protocol math is unit-testable.
"""

import threading
import time
from collections.abc import Callable, Mapping
from datetime import datetime
from enum import Enum
from typing import Any, Optional

TICKS_PER_SECOND = 10000000


class Phase(str, Enum):
    """The manager's playback phase.

    ``idle`` → ``loading`` (we asked Kodi to play the group's item) →
    ``waiting_ready`` (first frame held, Ready reported) → ``synced`` (the
    group unpaused us). ``str``-valued so every log line, comparison and
    property keeps the plain spelling.
    """

    IDLE = "idle"
    LOADING = "loading"
    WAITING_READY = "waiting_ready"
    SYNCED = "synced"

    def __str__(self) -> str:
        return str(self.value)

    def __format__(self, spec: str) -> str:
        return format(str(self.value), spec)


# The phases in which this member follows the group's timeline — a user
# pause, seek or resume is forwarded, a stop detaches.
FOLLOWING = frozenset({Phase.WAITING_READY, Phase.SYNCED})
# The phases from which a local start is the member proposing an item.
STARTABLE = frozenset({Phase.IDLE, Phase.SYNCED})
# Media loaded for the group but not yet released by it: an Unpause here is
# the group start.
HELD = frozenset({Phase.WAITING_READY, Phase.LOADING})
TICKS_PER_MS = 10000

# Client-side constants from the protocol specification (SYNCPLAY.md §12)
TIMESYNC_WINDOW = 8  # sliding measurement window, use min-RTT sample
TIMESYNC_GREEDY_COUNT = 4  # exchanges at ~1s on group join
TIMESYNC_GREEDY_INTERVAL = 1.0
TIMESYNC_INTERVAL = 30.0  # spec minimum is 60s
# A group Unpause on audio resumes first and aligns while running; if the
# resume lands this far from the group position, seek (video aligns tightly
# via UNPAUSE_ALIGN_MS instead).
AUDIO_UNPAUSE_ALIGN_MS = 1500.0
AUTO_REJOIN_INTERVAL = 30.0  # min seconds between automatic re-Join attempts
SNAPSHOT_REQUEST_INTERVAL = 5.0  # min seconds between snapshot requests
# A scheduled Unpause names the exact group position; starting from anywhere
# else (the pause-time spread after a barrier, the load position on a hot join)
# is an audible offset. Align by seeking at arm time whenever the start position
# is off by more than this.
UNPAUSE_ALIGN_MS = 100.0
BUFFERING_DEBOUNCE = 2.5  # Player.Caching must persist this long before reporting
# A local start that must be proposed to the group is paused ("held") the
# instant it begins, so any waiting happens before playback instead of a few
# seconds into it. The hold is released by the group's Unpause; these bound
# how long we identify the item and how long an unanswered hold may last.
FORWARD_RETRY_INTERVAL = 0.5  # poll cadence while identifying a local start
FORWARD_RETRY_LIMIT = 10  # give up identifying after this many polls
# A foreign claim older than this when a new local play starts belongs to
# the previous playback (a seamless zap emits no stop to clear it).
STALE_CLAIM_SECS = 2.0
HOLD_RELEASE_TIMEOUT = 10.0  # a held start nobody adopted resumes after this
STOP_PROMPT_GRACE = 1.0  # window for a replace-play to supersede a local stop
STOP_PROMPT_POLL = 0.1  # supersession poll cadence within that window
# A seek can resume a paused player (see playback._seek_and_settle), so every
# seek that expects to stay paused re-pauses; audio's resume can land after the
# seek settles, so audio is watched this long.
SEEK_REPAUSE_WINDOW_MS = 600.0
# A PAPlayer paused around a gapless boundary is unreliable: state reads
# (isPlaying/getTime/Player.Paused) intermittently report no media, and a
# single pause toggle can be swallowed. The group Unpause is the one command
# that must not be lost, so on audio it retries -- nudge, then verify the
# clock actually advances -- until it demonstrably took effect.
UNPAUSE_RETRY_WINDOW_MS = 4000.0  # keep trying this long before giving up
UNPAUSE_NUDGE_INTERVAL_MS = 600.0  # min gap between pause-toggle nudges
UNPAUSE_VERIFY_STEP_MS = 300  # clock sample spacing (xbmc.sleep, int ms)
SEEK_SETTLE_TIMEOUT = 3.0  # give up waiting for a seek to land after this
# A group Unpause asks for playing explicitly and then confirms the clock
# moved, because the failure to start is silent otherwise: the member simply
# sits still while the group plays on, and nothing revisits it.
RESUME_VERIFY_S = 1.5  # keep asking for playing this long
# Poll cadence, separate from RESUME_REASK_MS: each check's wait is added
# lateness.
RESUME_VERIFY_STEP_MS = 50  # clock sample spacing (xbmc.sleep, int ms)
# The re-ask undoes the pre-resume align's re-pause, which can land after the
# resume, so the interval is the recovery time.
RESUME_REASK_MS = 600  # how often to re-issue the play request while waiting
# Correcting *after* the picture is moving costs a visible jump, so only a gap
# larger than the spread two devices show anyway is closed.
POST_RESUME_ALIGN_MS = 250.0
PROGRAMMATIC_ECHO_GRACE = 1.0  # player events within this window of our own actions
STOP_WAIT_SECONDS = 3.0  # bound on waiting for a requested stop to take effect

# A load aims ahead by this device's last load time.
LOAD_ALLOWANCE_SMOOTHING = 0.5  # weight of the newest measurement in the EMA
LOAD_ALLOWANCE_MIN_MS = 250.0  # below this, not worth aiming off for
LOAD_ALLOWANCE_MAX_MS = 15000.0  # a pathological load must not fling the target

# Live position convergence. The group position of a live item is defined on
# the source's own clock — the broadcast's PTS, which every member's stream
# carries whatever moment it opened — never on a member's session time. A
# proposer anchors the group LIVE_DELAY_S behind its own reading: the headroom
# for a member whose stream lands later than the proposer's did. The clock is
# an MPEG-TS PTS and wraps every LIVE_PTS_PERIOD_S, so positions are compared
# on that circle; and a position on it is offset by LIVE_PTS_EPOCH_S on the
# wire, which is what tells a source-clock anchor apart from the session-time
# zero a member without the clock proposes (a group would need ten days on
# session time to reach it). A member that cannot read the clock, or whose
# group is anchored on session time, converges on commands only.
LIVE_PTS_PERIOD_S = 2**33 / 90000.0  # 33-bit PTS at 90 kHz: 26 h 30 m
LIVE_PTS_EPOCH_S = 10 * 86400.0
LIVE_DELAY_S = 5.0
# A live member that lands ahead of the group by more than this pauses for
# the excess — its timeshift buffer keeps the picture — rather than playing
# it off at the rate ceiling. Bounded, so a broken reading cannot freeze a
# member indefinitely.
LIVE_HOLD_MIN_MS = 2500.0
LIVE_HOLD_MAX_S = 60.0
# Kodi puts a live stream playing faster than its source back to 1.0 at its
# live edge. This many forward pulses ended that way in a row end fine sync for
# the item — it can only wait for the feed.
LIVE_EDGE_PULSES = 2
# A source clock that starts below this is a job-relative one, not a
# broadcast's: Jellyfin's transcode jobs restamp every session from about
# ten seconds, so two members on two jobs read two clocks. A broadcast's own
# PTS is never this young except in the first minute after an encoder restart.
LIVE_CLOCK_MIN_START_S = 60.0


def local_ms() -> float:
    """Local wall clock in unix milliseconds."""
    return time.time() * 1000.0


def ticks_to_ms(ticks: Optional[int]) -> float:
    return (ticks or 0) / TICKS_PER_MS


def ms_to_ticks(ms: float) -> int:
    return int(ms * TICKS_PER_MS)


def seconds_to_ticks(seconds: float) -> int:
    return int(seconds * TICKS_PER_SECOND)


def ticks_to_seconds(ticks: Optional[int]) -> float:
    return (ticks or 0) / TICKS_PER_SECOND


def claim_is_live(claim: Optional[Mapping[str, Any]]) -> bool:
    """Whether a claim names a live stream.

    kofin's own claim says so outright (``Live``, stamped by the play route
    on a channel); a public-bus
    claim — the ones that carry a ``Provider`` — spells it as no runtime,
    per the provider contract. Anything else is not live: an item whose
    runtime the server does not know still seeks.
    """
    if not claim:
        return False

    if "Live" in claim:
        return bool(claim["Live"])

    if claim.get("Provider"):
        return not claim.get("RunTimeTicks")

    return False


def time_object_ms(value: Any) -> Optional[float]:
    """A JSON-RPC ``Global.Time`` object in milliseconds, or None."""
    if not isinstance(value, dict):
        return None

    try:
        return float(
            (
                (int(value["hours"]) * 60 + int(value["minutes"])) * 60
                + int(value["seconds"])
            )
            * 1000
            + int(value["milliseconds"])
        )
    except (KeyError, TypeError, ValueError):
        return None


def presentation_offset_ms(props: Any) -> Optional[float]:
    """What to add to the player clock to read the stream's own clock, from
    one ``Player.GetProperties`` answer carrying ``time`` and
    ``presentationtime``; None when Kodi cannot tell.

    ``presentationtime`` is ``null`` for PAPlayer, a PVR-demuxed stream and an
    inputstream that does not report it (ffmpegdirect without kontell's
    presentation-offset change). The offset is the stream's timestamp at this
    player's time zero, and it holds across a tempo, since Kodi's time is
    content time.
    """
    if not isinstance(props, dict):
        return None

    presentation = time_object_ms(props.get("presentationtime"))
    played = time_object_ms(props.get("time"))

    if presentation is None or played is None:
        return None

    offset = presentation - played

    if offset < LIVE_CLOCK_MIN_START_S * 1000.0:
        return None

    return offset


def live_anchor_ms(source_ms: float) -> float:
    """The group position a proposer anchors for its own source-clock
    reading: LIVE_DELAY_S behind it, on the wire's epoch."""
    period = LIVE_PTS_PERIOD_S * 1000.0
    behind = (source_ms - LIVE_DELAY_S * 1000.0) % period
    return LIVE_PTS_EPOCH_S * 1000.0 + behind


def live_anchored(position_ms: Optional[float]) -> bool:
    """Whether a group position is on the source clock (see LIVE_PTS_EPOCH_S)."""
    return position_ms is not None and position_ms >= LIVE_PTS_EPOCH_S * 1000.0 / 2


def unwrap_live_ms(source_ms: float, reference_ms: Optional[float]) -> float:
    """A source-clock reading as the wire position nearest ``reference_ms``.

    The clock wraps, and a member may have opened on the far side of a wrap
    from the proposer, so the reading is placed on the reference's cycle:
    the representative whose difference from the reference is smallest.
    Without a reference it sits on the epoch.
    """
    period = LIVE_PTS_PERIOD_S * 1000.0
    position = LIVE_PTS_EPOCH_S * 1000.0 + (source_ms % period)

    if reference_ms is None:
        return position

    return position + round((reference_ms - position) / period) * period


def to_iso(unix_ms: float) -> str:
    """Unix milliseconds -> ISO 8601 UTC string the server parses."""
    seconds, ms = divmod(int(round(unix_ms)), 1000)
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(seconds)) + ".%03dZ" % ms


def parse_iso_ms(value: Optional[str]) -> Optional[float]:
    """ISO 8601 UTC string -> unix milliseconds (float).

    Handles .NET's 7-digit fractional seconds and both 'Z' and '+00:00'
    style offsets; naive timestamps are treated as UTC.
    """
    if not value:
        return None

    text = value.strip().replace("Z", "+00:00")
    head, sep, offset = text.partition("+")

    if "." in head:
        base, fraction = head.split(".")
        head = "%s.%s" % (base, (fraction + "000000")[:6])

    if not sep:  # no timezone: treat as UTC
        head += "+00:00"
        offset = ""

    try:
        parsed = datetime.fromisoformat(head + (("+" + offset) if offset else ""))
    except ValueError:
        return None

    return parsed.timestamp() * 1000.0


def ntp_sample(t0: float, t1: float, t2: float, t3: float) -> tuple[float, float]:
    """Standard NTP offset/rtt from the four timestamps (all unix ms).

    offset = server_clock - local_clock.
    """
    rtt = (t3 - t0) - (t2 - t1)
    offset = ((t1 - t0) + (t2 - t3)) / 2.0
    return offset, rtt


def command_position_ms(
    command_ticks: Optional[int], command_when_ms: float, server_now_ms: float
) -> float:
    """Extrapolated group position for a command, in ms of media time."""
    elapsed = max(0.0, server_now_ms - command_when_ms)
    return ticks_to_ms(command_ticks) + elapsed


def is_stale_version(version: Optional[int], highest_seen: Optional[int]) -> bool:
    """StateVersion gating (SYNCPLAY.md §6). None (v1) is never stale."""
    if version is None or highest_seen is None:
        return False

    return version < highest_seen


def later(seconds: float, func: Callable[..., Any], *args: Any) -> threading.Timer:
    """A fire-and-forget daemon Timer — the one spelling of the
    schedule-and-move-on blocks. Returns the timer for the one caller that
    stores it (the command scheduler)."""
    timer = threading.Timer(seconds, func, args=args)
    timer.daemon = True
    timer.start()
    return timer
