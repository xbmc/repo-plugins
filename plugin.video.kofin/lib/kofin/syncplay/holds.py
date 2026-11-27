"""Local starts in a SyncPlay group: the hold that keeps a start paused until
the group adopts it, the proposal that offers it as the group's queue, and
the prompt that asks what a local stop meant (SYNCPLAY.md §5, §14)."""

import threading
import time
from typing import TYPE_CHECKING, Any, Optional

import xbmcgui

from kofin.core import settings
from kofin.core.log import Logger
from kofin.syncplay import utils
from kofin.syncplay.providers import JELLYFIN
from kofin.syncplay.utils import FOLLOWING, Phase

if TYPE_CHECKING:
    from kofin.syncplay.manager import SyncPlayManager

LOG = Logger(__name__)


def _start_of(info: Any) -> float:
    """Where a claimed start began, for its proposal to the group.

    0 for a live claim, whose player clock is session time, and for a song:
    the claim's position follows the player, whose clock can still read the
    previous track straight after a gapless advance.
    """
    if not info or utils.claim_is_live(info) or info.get("Type") == "Audio":
        return 0.0
    try:
        return max(0.0, float(info.get("CurrentPosition") or 0.0))
    except (TypeError, ValueError):
        return 0.0


class LocalStarts:
    """The hold-and-propose flow of the member's own starts and stops.

    Owns the hold in progress (the start waiting for the group to adopt it)
    and the stop whose prompt is unresolved.
    """

    def __init__(self, manager: "SyncPlayManager") -> None:
        self.manager = manager
        # The held local start: what it is, whether it was proposed yet,
        # and when it began.
        self._hold: Optional[dict[str, Any]] = None
        # The stop the prompt was started for, until it is resolved.
        self._stop_pending: Optional[dict[str, Any]] = None

    # -- the hold --------------------------------------------------------------

    def enter(self, transition: bool) -> None:
        """Hold a local start paused until the group adopts it: a native
        playlist advance (``transition``, which starts at 0) or a fresh
        user start, possibly at a resume point."""
        hold = {
            "transition": transition,
            "proposed": False,
            "item_id": None,
            "at": utils.local_ms(),
        }
        LOG.debug(
            "[ syncplay/hold ] entered (%s)",
            "transition" if hold["transition"] else "fresh start",
        )
        self._hold = hold
        self.manager.playback.ensure_paused()
        self._watch(hold)

    def _watch(self, hold: dict[str, Any]) -> None:
        """A held start that never gets adopted must not stay paused
        forever (e.g. the proposal failed): give playback back."""

        def check() -> None:
            if self._hold is not hold:
                return

            LOG.warning("Held start was never adopted; releasing the hold")
            self.release()

        utils.later(utils.HOLD_RELEASE_TIMEOUT, self.manager._post, check)

    def _done(self, reason: str) -> None:
        """How long a boundary hold lasted, and what ended it."""
        hold = self._hold
        if hold is None or not hold.get("at"):
            return
        LOG.debug(
            "[ syncplay/hold ] released after %.0f ms (%s)",
            utils.local_ms() - hold["at"],
            reason,
        )

    def ended(self, reason: str) -> None:
        """The hold is over without a release of the player: the group
        adopted the start, or the playback detached, stopped or ended."""
        self._done(reason)
        self._hold = None

    def release(self) -> None:
        if self._hold is None:
            return

        self._done("released")
        self._hold = None
        self.manager.playback.ensure_playing()

    def holding(self) -> bool:
        """Whether a local start is held — the player has moved off the
        group's item onto the one being proposed, so the group's item is no
        longer what is loaded."""
        return self._hold is not None

    # -- the proposal ----------------------------------------------------------

    def on_kodi_play(self, data: dict[str, Any]) -> None:
        """Player.OnPlay from the Kodi bus: carries the Kodi library id,
        the earliest identification of a local start (before the play
        pipeline claims the item). Called on the notification thread."""
        self.manager._post(self._identify, data)

    def forward(self, attempt: int = 0) -> None:
        """Propose the currently-playing item to the group as its queue."""
        manager = self.manager
        if not manager.player.isPlaying():
            # Nothing to propose — e.g. a group created before playback
            # starts. Stay idle and wait for the user to play something;
            # do not demote to spectator.
            return

        hold = self._hold

        if hold is not None and hold["proposed"]:
            return  # the fast identification path already proposed

        if hold is not None and hold["transition"]:
            # Mid-transition the playing-id window property can still name
            # the previous track; only trust the claimed play state, which
            # is keyed by the new file.
            info = manager._local_file_info()
            item_id = info.get("Id") if info else None
        else:
            item_id = manager._local_item_id()

        if (
            item_id
            and item_id == manager.current_item_id
            and manager.phase in FOLLOWING
        ):
            # Already the group's current item: a late-delivered start
            # event for a proposal whose echo was adopted meanwhile.
            return

        if not item_id:
            # The plugin play worker may still be resolving the item.
            if attempt >= utils.FORWARD_RETRY_LIMIT:
                self._give_back()
                return

            utils.later(
                utils.FORWARD_RETRY_INTERVAL,
                manager._post,
                self.forward,
                attempt + 1,
            )
            return

        info = manager._local_file_info() or {}
        provider = info.get("Provider") or JELLYFIN

        if hold is not None:
            hold["proposed"] = True
            hold["item_id"] = item_id

            if hold["transition"]:
                self.propose(item_id, position=_start_of(info), provider=provider)
                return

        position = None
        if (
            item_id != manager.current_item_id
            and info.get("CurrentPosition") is not None
            and not utils.claim_is_live(info)
        ):
            # A new item over the group, with kofin's own claim: proposed
            # where its play began (a resume, or 0). The player clock is not
            # read for it, since it can still show the item being replaced:
            # a group paused at 917 s had its next film proposed, and
            # started, at 917 s. A claim without a position (a provider's)
            # leaves the clock as the only reading.
            position = _start_of(info)
        if utils.claim_is_live(info):
            # A live claim (zero runtime): the player's position is session
            # time on this member's own stream, meaningless to the group.
            # With a live clock (LiveClock.source_offset_ms) the
            # group is anchored on that instead, a delay behind this
            # member's reading; without one it tunes together from its own
            # edge.
            anchor_ms = manager.playback.live_anchor_ms()
            position = anchor_ms / 1000.0 if anchor_ms is not None else 0.0
            LOG.debug(
                "[ syncplay/live ] proposing %s %s",
                item_id,
                (
                    "anchored on the source clock"
                    if anchor_ms is not None
                    else "without a source clock; tune-together only"
                ),
            )

        self.propose(item_id, position=position, provider=provider)

    def _identify(self, data: dict[str, Any]) -> None:
        """Identify a held playlist advance from the Player.OnPlay payload.

        The Kodi library id maps straight to a provider key (for Jellyfin,
        kofin.db), so a transition can be proposed within milliseconds of the
        boundary instead of waiting for the play pipeline's claim. Fresh
        starts keep waiting for the player: their start position (a resume
        point) is only trustworthy once A/V is up.
        """
        manager = self.manager
        manager.bus.drop_stale_claim()

        hold = self._hold

        if not manager.in_group() or hold is None or hold["proposed"]:
            return

        item = data.get("item") or {}
        kodi_id = item.get("id")
        media = item.get("type")

        if not kodi_id or kodi_id == -1 or not media:
            return

        try:
            mapped = manager.providers.resolve_kodi_id(kodi_id, media)
        except Exception as error:
            LOG.warning("SyncPlay kodi id lookup failed: %s", error)
            return

        if not mapped:
            if media in ("channel", "recording"):
                # A PVR play is never in the provider mapping, but its
                # owner may claim it over the public bus a moment after
                # OnPlay (pvr.kofin claims from onAVStarted). Leave
                # identification to the ordinary retry window.
                return
            # A Kodi library item with no provider mapping: the group
            # cannot follow it, and the play pipeline (same mapping) will
            # not identify it either. Let it play now rather than after
            # the retry window.
            self._give_back()
            return

        if not hold["transition"]:
            return

        if media != "song":
            # Kodi sends no stop when the user picks another video over the
            # synced one, so this start may be at a resume point, which only
            # its claim states: forward proposes it once A/V is up.
            return

        hold["proposed"] = True
        hold["item_id"] = mapped
        self.propose(mapped, position=0.0)

    def _give_back(self) -> None:
        """Playing something the group can't follow (a local file,
        another addon): give playback back and stop pretending to be
        synchronized. Quiet when already a spectator — repeat plays of
        unmanaged media must not re-toast on every start."""
        manager = self.manager
        self.release()
        manager._detach_playback()

        if manager.ignore_wait:
            return

        LOG.debug("Unmanaged playback while in a group, detaching")
        manager.ignore_wait = True
        manager._api("syncplay_set_ignore_wait", True)
        manager._toast(settings.localized(30569))

    def propose(
        self,
        item_id: str,
        position: Optional[float] = None,
        provider: str = JELLYFIN,
        content: Optional[dict[str, Any]] = None,
    ) -> None:
        """Propose a queue; a held transition proposes 0 and the player is
        aligned on it at adopt time (prepare_ready), not here.

        A foreign provider's item goes out as an external-content entry
        (SYNCPLAY.md §14.2) — descriptor built from ``content`` when the
        caller has one (the bus propose), from the claim otherwise — and
        only when the server negotiated the capability: refused loudly
        rather than sent as a key the server would reject for everyone.

        External players cannot reach this path: kofin has no play-with
        flow, and the SyncPlay root entry is hidden when a
        playercorefactory override is installed (plugin/browse.py).
        """
        manager = self.manager
        if position is None:
            try:
                position = manager.player.getTime()
            except Exception:
                position = 0.0

        if provider != JELLYFIN:
            if not manager.server_external_content:
                LOG.warning(
                    "Propose for provider %r needs the server's "
                    "ExternalContent capability; refused",
                    provider,
                )
                return

            if content is None:
                info = manager._local_file_info() or {}
                content = {
                    "Provider": provider,
                    "Key": item_id,
                    "Name": info.get("Name") or "",
                    "RunTimeTicks": int(info.get("RunTimeTicks") or 0),
                }

            LOG.debug(
                "[ syncplay/set queue ] %s:%s at %.1fs", provider, item_id, position
            )
            manager._api(
                "syncplay_set_new_queue_ex",
                [{"Content": content}],
                0,
                utils.seconds_to_ticks(position),
            )
            return

        LOG.debug("[ syncplay/set queue ] %s at %.1fs", item_id, position)
        manager._api(
            "syncplay_set_new_queue",
            [item_id],
            0,
            utils.seconds_to_ticks(position),
        )

    # -- the stop --------------------------------------------------------------

    def note_stop(self, playlist_item_id: Optional[str]) -> dict[str, Any]:
        """Mark the user's stop of the group's item, before the detach
        clears the item: the dispatcher can be handling a group command for
        it on its own thread right now."""
        pending = {"playlist_item_id": playlist_item_id}
        self._stop_pending = pending
        return pending

    def clear_stop(self) -> None:
        """Whatever starts here replaced the stop, or the group was left."""
        self._stop_pending = None

    def prompt_in_thread(self, pending: dict[str, Any]) -> None:
        thread = threading.Thread(target=self._prompt, args=(pending,))
        thread.daemon = True
        thread.start()

    def _superseded(self) -> bool:
        """Did another local start (or a group item) replace the stop?"""
        manager = self.manager
        return (
            self._hold is not None
            or manager.phase != Phase.IDLE
            or manager.player.isPlaying()
        )

    def stopped_here(self, playlist_item_id: Optional[str]) -> bool:
        """Is this the item the user stopped, with the stop prompt unresolved?"""
        pending = self._stop_pending

        return (
            pending is not None
            and playlist_item_id is not None
            and pending["playlist_item_id"] == playlist_item_id
        )

    def _prompt(self, pending: Optional[dict[str, Any]] = None) -> None:
        """Local stop while synced: sort out what it means for the group.

        ``pending`` is the stop this prompt was started for (on_stopped).
        Whichever way the prompt ends — superseded, answered, dismissed, the
        group left — that stop is resolved, and the group's updates about the
        item are followed again exactly as before it. A later stop's mark is
        not this prompt's to clear.
        """
        if pending is None:
            pending = self._stop_pending

        try:
            self._ask()
        finally:
            if self._stop_pending is pending:
                self._stop_pending = None

    def _ask(self) -> None:
        """A stop that is immediately followed by another local start is a
        replace-play (the user picked a new item), not a departure: give
        the new start a moment to appear and skip the prompt when it does.
        """
        manager = self.manager
        deadline = time.time() + utils.STOP_PROMPT_GRACE

        while time.time() < deadline:
            if not manager.in_group() or self._superseded():
                return

            time.sleep(utils.STOP_PROMPT_POLL)

        if not manager.in_group() or self._superseded():
            return

        selection = xbmcgui.Dialog().select(
            settings.localized(30568),
            [
                settings.localized(30584),
                settings.localized(30580),
                settings.localized(30562),
            ],
        )

        if selection == 2:
            manager.leave_group()
            return

        if not manager.in_group() or self._superseded():
            # Answered against a stale premise (something started while
            # the dialog was open): only an explicit leave still applies.
            return

        if selection == 0:
            # Stop playback for the whole group. Membership is kept, so
            # whatever is played next is proposed to everyone.
            manager._api("syncplay_stop")
        else:
            # Explicit spectator choice — or the dialog was dismissed:
            # never leave the group silently waiting on this member.
            manager.ignore_wait = True
            manager._api("syncplay_set_ignore_wait", True)
            manager._toast(settings.localized(30569))
