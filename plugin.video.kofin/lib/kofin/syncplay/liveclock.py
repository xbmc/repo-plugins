"""A live item's clock in a SyncPlay group: the stream's own clock or the join
origin, the position the group shares on it, the ticks that must not replace
it, and the hold a member ahead of the group takes (docs/syncplay-fine-sync.md)."""

from typing import TYPE_CHECKING, Optional

from kofin.core import kodirpc
from kofin.core.log import Logger
from kofin.syncplay import utils
from kofin.syncplay.tempo import VIDEO_PLAYER

if TYPE_CHECKING:
    from kofin.syncplay.playback import PlaybackController
    from kofin.syncplay.ports import Claim

LOG = Logger(__name__)

# How long a read of Kodi's presentationtime stands for, and how soon a miss
# is asked again.
PRESENTATION_READ_MS = 1000.0
PRESENTATION_RETRY_MS = 250.0


class LiveClock:
    """The clock a live item plays on, kept for the playback controller.

    Owns the join origin (this stream's player t=0 on the server clock), the
    last reading of the stream's own clock, and the hold in progress.
    """

    def __init__(self, controller: "PlaybackController") -> None:
        self.controller = controller
        # A hold in progress: how long it was for.
        self._hold_ms: Optional[float] = None
        # Which hold; a superseded hold's timer resumes nothing.
        self._hold_seq = 0
        # Server-clock instant of this stream's player t=0: the live clock of
        # a stream whose own timestamps no other member shares (a remux
        # restamps from zero), since the edge a member opened at is the same
        # moment of the broadcast for every member.
        self._origin_server_ms: Optional[float] = None
        # (read at, offset) of Kodi's presentationtime, the stream's own clock.
        self._presentation: Optional[tuple[float, Optional[float]]] = None

    def new_stream(self) -> None:
        """A new stream brings its own clock."""
        self._presentation = None

    def reset(self) -> None:
        """Nothing plays: no origin, no reading."""
        self._origin_server_ms = None
        self._presentation = None

    def claim(self) -> Optional["Claim"]:
        """The current claim when it names a live stream, else None."""
        claim = self.controller._current_claim()
        return claim if utils.claim_is_live(claim) else None

    def seek_refused(self) -> bool:
        """Whether this playback must not be seeked.

        A live item is never seeked: ffmpeg's HLS demuxer refuses a seek
        on a live playlist, and a source-clock position is not a stream
        offset. Fine sync closes what it can.

        Before the claim, a delegated start (pvr.kofin) is treated as live,
        since a seek would send a live channel to 0. Once a claim exists,
        claim_is_live is the only signal: catchup is also pvr.kofin and must
        seek.
        """
        if self.claim() is not None:
            return True

        if self.controller._current_claim() is not None:
            return False

        manager = self.controller.manager
        provider = getattr(manager, "current_provider", None)
        providers = getattr(manager, "providers", None)
        is_delegated = getattr(providers, "is_delegated", None)
        return bool(provider) and callable(is_delegated) and is_delegated(provider)

    def keeps_source_clock(self, ticks: int) -> bool:
        """Whether command ticks must not replace a live-anchored group clock.

        A live Seek is refused, then Unpause (and Pause) arrive at the same
        PositionTicks — Kodi Player.Time on PVR, EPG-relative session time.
        Adopting those ticks knocks PTS members off the broadcast clock.
        """
        if not self.seek_refused():
            return False

        if not utils.live_anchored(self.controller.estimate_position_ms()):
            return False

        return not utils.live_anchored(utils.ticks_to_ms(ticks))

    def _player_ms(self) -> float:
        try:
            return self.controller.player.getTime() * 1000.0
        except Exception:
            return 0.0

    def note_origin(self) -> None:
        """Stamp this stream's player t=0 on the server clock.

        A remux that restamped from ~10 s has no broadcast PTS; t=0 is
        the live edge at this member's open.
        """
        player_ms = self._player_ms()
        self._origin_server_ms = self.controller.manager.server_now_ms() - player_ms

    def bind_origin_to_group(self) -> None:
        """Map this member's player t onto the group position.

        Origin is a raw offset: ``_position_ms`` unwraps player+origin onto
        the epoch. Storing the already-unwrapped group position here
        double-applies the epoch.

        Call only for a shared-start Unpause. A later open's gap is the
        picture offset; zeroing it leaves pictures apart with residual ~0.
        """
        player_ms = self._player_ms()
        group_ms = self.controller.estimate_position_ms()

        if group_ms is None:
            return

        raw_ms = group_ms - utils.LIVE_PTS_EPOCH_S * 1000.0
        self._origin_server_ms = raw_ms - player_ms
        LOG.debug(
            "[ syncplay/live ] join clock rebound to the group (player %.1fs)",
            player_ms / 1000.0,
        )

    def source_offset_ms(self) -> Optional[float]:
        """player clock → live clock; None for anything but a live item.

        The live clock is the stream's own when Kodi reports it
        (``presentationtime``: a broadcast's PTS, one clock for every member's
        stream whatever moment it opened), and otherwise the join origin:
        player t=0 plus the server time at open, which is the live edge this
        member started on.
        """
        if self.claim() is None:
            return None

        offset = self._presentation_offset_ms()

        if offset is not None:
            return offset

        return self._origin_server_ms

    def _presentation_offset_ms(self) -> Optional[float]:
        """The stream's own clock against the player clock, or None until Kodi
        has reported it.

        Only a reading is kept. A miss (a timeshift buffer with no timestamp
        yet, a failed read) keeps the last offset, and with none yet is asked
        again a tick later rather than held: None means the join origin,
        another clock, and held for a read interval it would put the group's
        anchor and the window on it.
        """
        now = utils.local_ms()
        known = None

        if self._presentation is not None:
            asked_at, known = self._presentation
            interval = (
                PRESENTATION_READ_MS if known is not None else PRESENTATION_RETRY_MS
            )

            if 0 <= now - asked_at < interval:
                return known

        offset = utils.presentation_offset_ms(
            kodirpc.player_properties(["time", "presentationtime"], VIDEO_PLAYER)
        )

        if offset is not None:
            known = offset

        self._presentation = (now, known)
        return known

    def on_source_clock(self) -> bool:
        """Whether this member and the group share the source clock: the
        member can read its own, and the group's position is anchored on
        it rather than on a proposer's session time."""
        if self.source_offset_ms() is None:
            return False

        return utils.live_anchored(self.controller.estimate_position_ms())

    def anchor_ms(self) -> Optional[float]:
        """The group position to propose for the live item playing here:
        LIVE_DELAY_S behind this member's own source-clock reading, or None
        when it has no such reading (the proposal then tunes together from
        zero)."""
        offset = self.source_offset_ms()

        if offset is None:
            return None

        try:
            player_ms = self.controller.player.getTime() * 1000.0
        except Exception:
            return None

        return utils.live_anchor_ms(player_ms + offset)

    def hold(self, hold_ms: float) -> None:
        """Pause for ``hold_ms`` so the group catches this member up, then
        resume through the dispatcher. The timeshift buffer keeps the
        stream; fine sync trims what the pause and resume leave."""
        controller = self.controller
        hold_ms = min(hold_ms, utils.LIVE_HOLD_MAX_S * 1000.0)
        self._hold_ms = hold_ms
        self._hold_seq += 1
        controller.tempo.cancel("hold")
        LOG.debug(
            "[ syncplay/live ] %.1fs ahead of the group: holding for it",
            hold_ms / 1000.0,
        )
        controller.ensure_paused()
        utils.later(
            hold_ms / 1000.0,
            controller.manager._post,
            self._resume,
            self._hold_seq,
        )

    def _resume(self, seq: int) -> None:
        if seq != self._hold_seq:
            return

        held = self._hold_ms
        self._hold_ms = None

        controller = self.controller
        if held is None or not controller.reference_is_playing():
            # The group paused meanwhile: its own Unpause resumes us, and
            # the residual it leaves is fine sync's.
            return

        controller.ensure_playing()
        controller.tempo.note_settle()
        LOG.debug("[ syncplay/live ] held %.1fs; playing on", held / 1000.0)
