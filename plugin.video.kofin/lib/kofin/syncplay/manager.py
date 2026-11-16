"""SyncPlay group membership and state mirror."""

import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from queue import Queue
from typing import TYPE_CHECKING, Any, Optional, Union, cast

import xbmc

from kofin.core import contract, settings, state, toast
from kofin.core.http import JellyfinError, Unauthorized
from kofin.core.log import Logger
from kofin.syncplay import utils
from kofin.syncplay.utils import FOLLOWING, HELD, STARTABLE, Phase
from kofin.syncplay.bus import ProviderBus
from kofin.syncplay.holds import LocalStarts
from kofin.syncplay.playback import PlaybackController
from kofin.syncplay.ports import Claim, SyncPlayApi
from kofin.syncplay.providers import (
    JELLYFIN,
    ProviderRegistry,
    jellyfin_registry,
)
from kofin.syncplay.tempo import TempoSession
from kofin.syncplay.timesync import TimeSync

if TYPE_CHECKING:
    from kofin.service.player import Player

LOG = Logger(__name__)

# What the dispatcher is handed: a callable with its arguments, a Kodi
# notification with its data, or None to stop.
Posted = Optional[tuple[Union[Callable[..., Any], str], Any]]


class SyncPlayManager:
    """SyncPlay group membership and state mirror (SYNCPLAY.md §5, §6, §9).

    Runs in the service process. WebSocket traffic arrives through
    service/remote.py and is processed sequentially on a dispatcher thread
    so message ordering is preserved and the websocket thread is never
    blocked.
    """

    def __init__(
        self,
        api: Optional[SyncPlayApi],
        player: "Player",
        providers: Optional[ProviderRegistry] = None,
    ) -> None:
        self.api = api
        self.player = player
        # The provider seam: how a queue item id becomes a playing stream,
        # and how a Kodi library id maps back to one. The service injects the
        # registry.
        self.providers = providers if providers is not None else jellyfin_registry(api)
        # A play kofin's own pipeline did not resolve, identified from
        # outside over the public bus (SyncProvider.Claim). kofin's claim
        # always wins over it.
        self.playback = PlaybackController(self, player)
        self.bus = ProviderBus(self)
        self.timesync: Optional[TimeSync] = None
        # Fine sync through Kodi's own tempo (syncplay/tempo.py): armed at
        # group join when the setting allows, disarmed at leave.
        self.tempo_session = TempoSession()
        self._rate_mismatch_told = False

        self.group: Optional[dict[str, Any]] = None  # {"GroupId", "GroupName"}
        self.group_state: Optional[str] = None
        self.members: list[Any] = []
        self.protocol_version = 1
        self.state_version = 0
        # Dedicated time-sync socket path from the server's Hello (plugin
        # binding); None = HTTP time sync only.
        self.timesync_ws_path: Optional[str] = None
        self.ignore_wait = False

        # [(key, PlaylistItemId, provider)] mirror of the group queue
        self.queue: list[tuple[str, str, str]] = []
        self.queue_last_update: Optional[float] = None
        self.current_item_id: Optional[str] = None
        self.current_playlist_item_id: Optional[str] = None
        # Which provider owns the current queue item (SYNCPLAY.md §14.3):
        # jellyfin for plain entries, the descriptor's Provider otherwise.
        self.current_provider = JELLYFIN
        # Whether the server negotiated the ExternalContent capability
        # (§14.1); learned from Hello, server-scoped rather than group-scoped.
        self.server_external_content = False

        self.phase = Phase.IDLE

        self.join_local_ms = 0.0
        self.last_group_id: Optional[str] = None
        # A group handed over by the last generation, to rejoin on connect.
        self._rejoin_owed = False
        self.last_snapshot_at = 0.0
        self._last_rejoin = 0.0
        self._last_snapshot_request = 0.0
        # How long this device's loads take, smoothed; None until one is timed.
        self._load_ms: Optional[float] = None
        self._load_started_ms: Optional[float] = None
        # Bumped by every load so an earlier load's watchdog can tell that it
        # has been superseded; see _start_item.
        self._load_generation = 0
        self._last_ping_report = 0.0
        self._join_pending_since = 0.0
        self._pending_local_queue = False

        # A user-initiated start paused at its first instant, awaiting the
        # group echo: {"transition", "proposed", "item_id"}. "transition"
        # marks a native playlist advance (starts at 0); otherwise the
        # start position is read from the player once it settles.
        self.holds = LocalStarts(self)

        self._prog_depth = 0
        self._prog_release = 0.0
        self._prog_lock = threading.Lock()

        self._inbox: Queue[Posted] = Queue()
        self._running = True
        self._dispatcher = threading.Thread(
            target=self._dispatch_loop, name="kofin-syncplay-dispatch"
        )
        self._dispatcher.daemon = True
        self._dispatcher.start()

    # ------------------------------------------------------------------
    # Plumbing
    # ------------------------------------------------------------------

    def stop(self, leave: bool = True) -> None:
        # The leave is a courtesy to the group, not something teardown waits
        # on: this runs inside Service.stop, which Kodi gives five seconds.
        # Skipped when the service knows the server is away, and when the
        # service is restarted in place; otherwise sent on the short budget
        # syncplay_leave carries. The group is handed to the next generation
        # either way (state.PROP_SYNCPLAY_GROUP): an add-on disabled and
        # enabled again, or updated, stops like a Kodi quit and starts again
        # seconds later, and the property dies with Kodi's process, so only
        # a generation of the same process ever reads it.
        kept = ""
        if self.in_group():
            kept = str((self.group or {}).get("GroupId") or self.last_group_id or "")
            if leave and not state.is_offline():
                try:
                    self._api_raw("syncplay_leave")
                except Exception:
                    pass

        self._running = False
        self._inbox.put(None)
        self._leave_locally()
        if kept:
            LOG.debug("SyncPlay group %s handed to the next service generation", kept)
            state.publish_syncplay_group(kept)
        else:
            state.clear_syncplay_group()
        self._dispatcher.join(timeout=5)
        if self._dispatcher.is_alive():  # pragma: no cover - watchdog only
            LOG.warning("syncplay dispatcher did not stop within deadline")

    def adopt_group(self, group_id: str) -> None:
        """The group the previous service generation was in: rejoined on the
        first websocket connect (_on_ws_connected), where the group's answer
        can reach this member. A group the generation left as a courtesy is
        joined again, which the server allows."""
        if not group_id:
            return
        LOG.debug(
            "SyncPlay group %s adopted from the last service generation", group_id
        )
        self.last_group_id = group_id
        self._rejoin_owed = True

    def on_notification(self, method: str, data: dict[str, Any]) -> None:
        """Entry point from the websocket routing; returns immediately."""
        self._inbox.put((method, data))

    def _post(self, func: Callable[..., Any], *args: Any) -> None:
        """Run a callable on the dispatcher thread."""
        self._inbox.put((func, args))

    def _dispatch_loop(self) -> None:
        LOG.debug("--->[ syncplay dispatcher ]")

        while self._running:
            entry = self._inbox.get()

            if entry is None:
                break

            try:
                method, data = entry

                if callable(method):
                    method(*data)
                elif method == "SyncPlayCommand":
                    self._handle_command(data)
                elif method == "SyncPlayGroupUpdate":
                    self._handle_group_update(data)
                elif method == "WebSocketConnected":
                    self._on_ws_connected()
            except Exception as error:
                LOG.exception("SyncPlay dispatch error: %s", error)

        LOG.debug("---<[ syncplay dispatcher ]")

    def get_api(self) -> Optional[SyncPlayApi]:
        return self.api

    def _api(self, name: str, *args: Any) -> Any:
        """SyncPlay REST with the §9 reaction to a lost session (401/403 on
        kofin's transport): one rate-limited automatic re-join before
        giving up."""
        api_client = self.get_api()

        if api_client is None:
            return None

        try:
            return getattr(api_client, name)(*args)
        except Unauthorized:
            if self.in_group():
                LOG.debug("SyncPlay %s unauthorized, attempting rejoin", name)
                self._post(self._attempt_rejoin)
            else:
                LOG.warning("SyncPlay %s unauthorized", name)
        except Exception as error:
            LOG.warning("SyncPlay %s failed: %s", name, error)

        return None

    def _api_raw(self, name: str, *args: Any) -> Any:
        """SyncPlay REST that surfaces HTTP errors to the caller."""
        api_client = self.get_api()

        if api_client is None:
            return None

        return getattr(api_client, name)(*args)

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def in_group(self) -> bool:
        return self.group is not None

    def enabled(self) -> bool:
        return settings.get_bool("syncPlayEnabled")

    def offset_ms(self) -> float:
        return self.timesync.offset_ms if self.timesync else 0.0

    def server_now_ms(self) -> float:
        return utils.local_ms() + self.offset_ms()

    def server_now_iso(self) -> str:
        return utils.to_iso(self.server_now_ms())

    def join_server_ms(self) -> float:
        """Join instant on the server clock; tracks time sync refinement."""
        return self.join_local_ms + self.offset_ms()

    def get_utc_time(self) -> Any:
        try:
            return self._api_raw("get_utc_time")
        except Exception as error:
            LOG.debug("GetUtcTime failed: %s", error)
            return None

    def can_ws_timesync(self) -> bool:
        return self.in_group() and bool(self.timesync_ws_path)

    def timesync_ws_target(self) -> Optional[tuple[str, str]]:
        """(url, authorization) for the dedicated time-sync socket, or None."""
        if not self.timesync_ws_path:
            return None

        api_client = self.get_api()

        if api_client is None:
            return None

        return (
            api_client.websocket_url(self.timesync_ws_path),
            api_client.authorization(),
        )

    def on_timesync_update(self) -> None:
        """Report our ping after accepted measurements (SYNCPLAY.md §3)."""
        if not self.in_group() or self.timesync is None:
            return

        now = time.time()

        if now - self._last_ping_report < utils.TIMESYNC_INTERVAL - 5:
            return

        if self.timesync.ping_ms is not None:
            self._last_ping_report = now
            self._api("syncplay_ping", int(self.timesync.ping_ms))

    @contextmanager
    def programmatic(self) -> Iterator[None]:
        """Marks player actions we cause, so their Kodi callbacks are not
        forwarded to the group as user requests."""
        with self._prog_lock:
            self._prog_depth += 1

        try:
            yield
        finally:
            with self._prog_lock:
                self._prog_depth -= 1
                self._prog_release = time.time()

    def is_programmatic(self) -> bool:
        with self._prog_lock:
            if self._prog_depth > 0:
                return True

            return (time.time() - self._prog_release) < utils.PROGRAMMATIC_ECHO_GRACE

    def _local_file_info(self) -> Optional[Claim]:
        """The claimed play state of the current playback: kofin's own claim,
        else the foreign claim, or None."""
        try:
            if not self.player.isPlaying():
                return None

            # The play state the plugin pushed, read back from JSON
            # (core/state): here it takes the shape SyncPlay names.
            claim = cast(Optional[Claim], self.player.current_item())
            if claim:
                return claim

            # Not a kofin play: the foreign claim (public bus) is the
            # identity, when one was published.
            return self.bus.foreign_claim
        except Exception as error:
            LOG.debug("current item unreadable: %s", error)

        return None

    def _local_item_id(self) -> Optional[str]:
        info = self._local_file_info()

        if info:
            return info.get("Id")

        return state.get_playing_id() or None

    def watching_own_media(self) -> bool:
        """A spectator whose player is showing something that is not the
        group's item.

        ``ignore_wait`` alone cannot answer this: an idle spectator still
        follows the group's queue (``_apply_play_queue``) and transport
        commands, so what is playing is compared with the group's item.
        """
        if not self.ignore_wait or not self.player.isPlaying():
            return False

        local = self._local_item_id()
        own = bool(local) and local != self.current_item_id

        if not own:
            LOG.debug(
                "Spectator follows the group: playing %s, group item %s",
                local,
                self.current_item_id,
            )

        return own

    def is_transcoding(self) -> bool:
        info = self._local_file_info()
        return info is not None and info.get("PlayMethod") == "Transcode"

    def current_claim(self) -> Optional[Claim]:
        """The claimed play state of the current playback, or None: what the
        fine-sync scheduler arms on, one play session at a time."""
        return self._local_file_info()

    def fine_sync_active(self) -> bool:
        """Whether this group membership has fine sync (the setting, at join)."""
        return self.tempo_session.active

    def refresh_tempo_session(self) -> None:
        """The fine-sync setting changed: arm or disarm for the current group.
        Outside a group there is nothing to do — join arms it."""
        if not self.in_group():
            return

        if settings.get_bool("syncPlayTempo"):
            self.tempo_session.begin()
        else:
            self.tempo_session.end()
            # A pulse running now must not outlive the setting.
            self.playback.tempo.reset()

    def notify_rate_mismatch(self) -> None:
        """The scheduler gave up on a residual that keeps regrowing: tell the
        user once per group, because the cause is on their side."""
        if self._rate_mismatch_told:
            return

        self._rate_mismatch_told = True
        self._toast(settings.localized(30592), warning=True)

    def reload_current_item(self) -> None:
        """Restart the current item at the group position.

        The seek path uses this on a transcode (``PlaybackController._do_seek``).
        The start position comes from the group position reference, which the
        Seek command has just set, so no position needs threading through.
        """
        if not self.in_group() or self.current_item_id is None:
            return

        self._start_item(
            self.current_item_id, self.current_playlist_item_id, self.current_provider
        )

    def _load_allowance_ms(self) -> float:
        """How far ahead of the group to aim a load that is about to start.

        A playing group moves on during a load, so the load aims ahead by the
        last load's duration. It is measured, not predicted, because whether
        the server transcodes is decided by the PlaybackInfo negotiation
        *inside* the load.

        Zero unless the group is playing. Aiming ahead of a paused group would
        land the member past a position that is not going to move.
        """
        if self._load_ms is None or not self.playback.reference_is_playing():
            return 0.0

        return min(self._load_ms, utils.LOAD_ALLOWANCE_MAX_MS)

    def _note_load_completed(self) -> None:
        """Fold the load that just finished into the allowance."""
        started = self._load_started_ms
        self._load_started_ms = None

        if started is None:
            return

        elapsed = utils.local_ms() - started

        if (
            elapsed < utils.LOAD_ALLOWANCE_MIN_MS
            or elapsed > utils.LOAD_ALLOWANCE_MAX_MS
        ):
            # Too quick to be worth aiming off for, or so slow that something
            # other than loading happened (a dialog, a stall) and it would
            # poison the estimate.
            return

        if self._load_ms is None:
            self._load_ms = elapsed
        else:
            weight = utils.LOAD_ALLOWANCE_SMOOTHING
            self._load_ms = weight * elapsed + (1.0 - weight) * self._load_ms

        LOG.debug(
            "[ syncplay/load ] took %.1fs; aiming %.1fs ahead next time",
            elapsed / 1000.0,
            self._load_ms / 1000.0,
        )

    def post_report(self, kind: str, position_s: Optional[float] = None) -> None:
        """Ready/Buffering report with our actual position (SYNCPLAY.md §4).

        position_s overrides the live clock for reports that promise a
        position we are committed to landing on (a deferred audio seek).
        """
        if not self.in_group() or self.current_playlist_item_id is None:
            return

        position = position_s

        if position is None:
            try:
                position = self.playback.reported_position_s()
            except Exception:
                position = 0.0

        is_playing = self.player.isPlaying() and not xbmc.getCondVisibility(
            "Player.Paused"
        )
        self._api(
            kind,
            self.server_now_iso(),
            utils.seconds_to_ticks(position),
            bool(is_playing),
            self.current_playlist_item_id,
        )

    def _text(self, string_id: int, value: Any = None) -> str:
        """localized() returns '' for unknown ids; never let formatting
        break a message handler."""
        template = settings.localized(string_id)

        if value is None:
            return template

        try:
            text: str = template % value
        except (TypeError, ValueError):
            return "%s %s" % (template, value)
        return text

    def _toast(self, message: str, error: bool = False, warning: bool = False) -> None:
        if not settings.get_bool("syncPlayNotifications") and not (error or warning):
            return

        level = toast.ERROR if error else toast.WARNING if warning else toast.INFO
        toast.show(message, level, heading="SyncPlay", time_ms=3000)

    # ------------------------------------------------------------------
    # Group membership (menu-facing)
    # ------------------------------------------------------------------

    def list_groups(self) -> Optional[list[dict[str, Any]]]:
        try:
            return self._api_raw("syncplay_list") or []
        except Exception as error:
            LOG.warning("SyncPlay list failed: %s", error)
            return None

    def refresh_group_info(self) -> None:
        """Refresh the member list for the menu."""
        if not self.in_group():
            return

        assert self.group is not None  # in_group() above
        for group in self.list_groups() or []:
            if group.get("GroupId") == self.group["GroupId"]:
                self.members = (
                    group.get("Members") or group.get("Participants") or self.members
                )
                self.group["GroupName"] = (
                    group.get("GroupName") or self.group["GroupName"]
                )

    def join_group(self, group_id: str) -> bool:
        self._join_pending_since = time.time()
        # Only a group this member creates takes its playback as the queue.
        self._pending_local_queue = False

        try:
            # Request v2 unconditionally: older servers ignore unknown
            # fields and we detect the version from GroupJoined (§2).
            self._api_raw("syncplay_join", group_id, 2)
        except JellyfinError as error:
            LOG.warning("SyncPlay join failed: %s", error)
            self._toast(settings.localized(30578), error=True)
            return False
        except Exception as error:
            LOG.warning("SyncPlay join failed: %s", error)
            self._toast(settings.localized(30578), error=True)
            return False

        self._watch_join_feedback()
        return True

    def new_group(self, group_name: str) -> bool:
        self._join_pending_since = time.time()
        self._pending_local_queue = True

        try:
            self._api_raw("syncplay_new", group_name, 2)
        except Exception as error:
            LOG.warning("SyncPlay new group failed: %s", error)
            self._pending_local_queue = False
            self._toast(settings.localized(30578), error=True)
            return False

        self._watch_join_feedback()
        return True

    def leave_group(self) -> None:
        try:
            self._api_raw("syncplay_leave")
        except Exception as error:
            LOG.warning("SyncPlay leave failed: %s", error)

        self._leave_locally()
        self._toast(settings.localized(30564))

    def toggle_spectator(self) -> None:
        self.ignore_wait = not self.ignore_wait
        self._api("syncplay_set_ignore_wait", self.ignore_wait)
        self._toast(
            settings.localized(30569) if self.ignore_wait else settings.localized(30583)
        )

        if not self.ignore_wait:
            # Coming back from spectator mode: re-attach so the server
            # pushes the group state again now, instead of us only
            # catching up at the group's next queue change.
            self._attempt_rejoin(force=True)

    def request_resync(self) -> None:
        """Menu 'resync': snapshot on v2, re-join on v1 (§4, §9)."""
        if not self.in_group():
            return

        if self.protocol_version >= 2:
            self._request_snapshot(force=True)
        else:
            self._attempt_rejoin(force=True)

    def _watch_join_feedback(self) -> None:
        """The feedback plane is mandatory: joining without a working
        WebSocket would mean never receiving a single command (§1)."""

        def check() -> None:
            if self.in_group() or not self._join_pending_since:
                return

            LOG.warning("No GroupJoined update within 10s of joining")
            self._join_pending_since = 0.0
            self._pending_local_queue = False
            self._toast(settings.localized(30570), error=True)

            try:
                self._api_raw("syncplay_leave")
            except Exception:
                pass

        utils.later(10, self._post, check)

    # ------------------------------------------------------------------
    # WebSocket message handling (dispatcher thread)
    # ------------------------------------------------------------------

    # Group updates by type, in three tables that keep the dispatch's guard
    # order: what is handled whether or not we are in a group, what is handled
    # in-group before the state version moves, and what is versioned and
    # dropped when stale.
    _GROUP_UPDATES_ANY_STATE = {
        "GroupJoined": "_on_group_joined",
        "NotInGroup": "_on_not_in_group",
        "GroupDoesNotExist": "_on_group_does_not_exist",
        "LibraryAccessDenied": "_on_library_access_denied",
    }
    _GROUP_UPDATES_UNVERSIONED = {
        "GroupLeft": "_on_group_left",
        "UserJoined": "_on_user_joined",
        "UserLeft": "_on_user_left",
    }
    _GROUP_UPDATES_VERSIONED = {
        "StateUpdate": "_on_state_update",
        "PlayQueue": "_on_play_queue",
        "StateSnapshot": "_on_state_snapshot",
        "PositionBeacon": "_on_beacon",
    }

    def _handle_group_update(self, data: dict[str, Any]) -> None:
        gtype = str(data.get("Type") or "")
        payload = data.get("Data")
        version = data.get("StateVersion")

        handler = self._GROUP_UPDATES_ANY_STATE.get(gtype)
        if handler is not None:
            getattr(self, handler)(payload or {}, version)
            return

        if not self.in_group():
            return
        assert self.group is not None  # in_group() above
        if data.get("GroupId") and data["GroupId"] != self.group["GroupId"]:
            return

        if gtype == "GroupLeft":
            # Before the version bookkeeping: a left group has no version.
            self._on_group_left(payload or {})
            return

        previous_version = self.state_version
        if version is not None:
            self.state_version = max(previous_version, version)

        handler = self._GROUP_UPDATES_UNVERSIONED.get(gtype)
        if handler is not None:
            getattr(self, handler)(payload or {})
            return

        if utils.is_stale_version(version, previous_version):
            LOG.debug("Ignoring stale %s (v%s < v%s)", gtype, version, previous_version)
            return

        handler = self._GROUP_UPDATES_VERSIONED.get(gtype)
        if handler is None:
            LOG.debug("Unhandled group update type: %s", gtype)
            return
        getattr(self, handler)(payload or {}, version, previous_version)

    def _on_not_in_group(self, payload: Any, version: Optional[int]) -> None:
        if self.in_group():
            self._attempt_rejoin()

    def _on_group_does_not_exist(self, payload: Any, version: Optional[int]) -> None:
        """The server sends this to a Join of a group that is gone, and to
        nothing else: in a group it is the rejoin failing, and before
        GroupJoined it is the join refused."""
        if self.in_group():
            LOG.debug("SyncPlay group %s no longer exists", self.last_group_id)
            self._leave_locally()
            self._toast(settings.localized(30571), warning=True)
        elif self._join_pending_since:
            self._join_refused(30578)

    def _on_library_access_denied(self, payload: Any, version: Optional[int]) -> None:
        if self._join_pending_since and not self.in_group():
            self._join_refused(30579)
        else:
            self._toast(settings.localized(30579), error=True)

    def _join_refused(self, message: int) -> None:
        """A join the server refused: the check waiting for GroupJoined has
        its answer, and nothing local is proposed to a group."""
        self._join_pending_since = 0.0
        self._pending_local_queue = False
        self._toast(settings.localized(message), error=True)

    def _on_group_left(self, payload: Any) -> None:
        self._leave_locally()
        self._toast(settings.localized(30564))

    def _on_user_joined(self, payload: Any) -> None:
        self._toast(self._text(30565, payload))

    def _on_user_left(self, payload: Any) -> None:
        self._toast(self._text(30566, payload))

    def _on_state_update(
        self,
        payload: dict[str, Any],
        version: Optional[int],
        previous_version: Optional[int],
    ) -> None:
        previous = self.group_state
        self.group_state = payload.get("State")
        LOG.debug(
            "[ syncplay/state ] %s (%s)",
            self.group_state,
            payload.get("Reason"),
        )
        if self.group_state == "Waiting" and previous == "Playing":
            # A member dropped out or started buffering: the whole
            # group holds. Surface why playback froze.
            self._toast(settings.localized(30585))

    def _on_play_queue(
        self,
        payload: dict[str, Any],
        version: Optional[int],
        previous_version: Optional[int],
    ) -> None:
        self._apply_play_queue(payload)

    def _on_state_snapshot(
        self,
        payload: dict[str, Any],
        version: Optional[int],
        previous_version: Optional[int],
    ) -> None:
        self._apply_snapshot(payload)

    def _handle_command(self, command: dict[str, Any]) -> None:
        """SyncPlayCommand gating per SYNCPLAY.md §5.1."""
        if not self.in_group():
            return

        assert self.group is not None  # in_group() above
        if command.get("GroupId") and command["GroupId"] != self.group["GroupId"]:
            LOG.debug("Discarding command for another group")
            return

        previous_version = self.state_version
        version = command.get("StateVersion")

        if version is not None:
            self.state_version = max(previous_version, version)

        if utils.is_stale_version(version, previous_version):
            LOG.debug("Ignoring stale command (v%s < v%s)", version, previous_version)
            return

        emitted = utils.parse_iso_ms(command.get("EmittedAt"))

        if emitted is not None and emitted < self.join_server_ms() - 2000:
            LOG.debug("Discarding command emitted before our join")
            return

        if self.watching_own_media():
            # A spectator's own playback follows no transport command, as it
            # follows no group queue (_apply_play_queue).
            LOG.debug("Spectator playing own media; not following transport")
            return

        if command.get("Command") != "Stop" and self.holds.stopped_here(
            command.get("PlaylistItemId")
        ):
            # Not a missed queue update, so nothing to reconcile: the item is
            # known, and the user stopped it.
            LOG.debug("Command for the item stopped here; waiting on the stop prompt")
            return

        if (
            command.get("Command") != "Stop"
            and command.get("PlaylistItemId")
            and command["PlaylistItemId"] != self.current_playlist_item_id
        ):
            LOG.debug(
                "Command for another queue item (%s != %s)",
                command.get("PlaylistItemId"),
                self.current_playlist_item_id,
            )

            if self.protocol_version >= 2:
                # A command for an item we don't have means we missed a
                # queue update: reconcile instead of staying split (§6).
                self._request_snapshot()

            return

        if self.holds.holding() and command.get("Command") in (
            "Unpause",
            "Pause",
            "Seek",
        ):
            # A local start is held, and this command is for the current
            # item -- a command for any other item was reconciled just above.
            # The player has swapped off that item onto the one being
            # proposed, which still carries this PlaylistItemId (the queue has
            # not moved), so the command would seek or pause the held file to
            # the item being replaced. The held file's position reaches the
            # group with the proposal (holds.forward). The counterpart to
            # on_seek's hold guard: a scrub of a held file is not the group's,
            # and a group command for the item being replaced is not the held
            # file's. After the mismatch check above, so a missed queue update
            # still reconciles.
            LOG.debug(
                "[ syncplay/%s ] not applied: a local start is held",
                command.get("Command"),
            )
            return

        self.playback.schedule(command)

    def _on_group_joined(self, info: dict[str, Any], version: Optional[int]) -> None:
        if not self.enabled():
            LOG.debug("SyncPlay is disabled in settings, ignoring GroupJoined")
            return

        group = self.group  # in_group() is exactly this None test
        rejoined = group is not None and group["GroupId"] == info.get("GroupId")

        self.group = {
            "GroupId": info.get("GroupId"),
            "GroupName": info.get("GroupName") or "",
        }
        self.last_group_id = info.get("GroupId")
        self.group_state = info.get("State")
        # Members (with per-member state) is a v2 field; stock v1 servers
        # only send Participants name strings.
        self.members = info.get("Members") or info.get("Participants") or []
        server_version = info.get("ProtocolVersion") or 1
        self.protocol_version = 2 if server_version >= 2 else 1
        self.state_version = version or 0
        self.queue_last_update = None
        self.join_local_ms = utils.local_ms()
        self._join_pending_since = 0.0

        if not rejoined:
            # Spectator state is client-local — the wire's Members carry no
            # session identity, so there is nothing to read it back from — and
            # a GroupJoined for the group we are already in would otherwise
            # silently undo the user's choice.
            self.ignore_wait = False

        # While True, Play Next and the cinema/near-end prompts are withheld:
        # the group queue is authoritative.
        self.player.syncplay_group_active = True

        if self.timesync is None:
            self.timesync = TimeSync(self, user_agent=settings.user_agent())
            self.timesync.start()
        else:
            self.timesync.force_update()

        self.playback.start_loop()

        if not rejoined:
            self._rate_mismatch_told = False
            self.tempo_session.begin()

        LOG.debug(
            "--->[ syncplay group/%s ] protocol v%s",
            self.group["GroupId"],
            self.protocol_version,
        )

        if self.protocol_version >= 2 and self.timesync_ws_path is None:
            # Learn the time-sync transport (plugin binding); integrated v2
            # servers have no Hello and stay on HTTP time sync.
            self._hello()

        if not rejoined:
            self._toast(self._text(30563, self.group["GroupName"] or "?"))

        if self._pending_local_queue:
            self._pending_local_queue = False
            self._post(self.holds.forward)

        self.publish_session_state(announce=True)

    def _leave_locally(self) -> None:
        if not self.in_group() and self.phase == Phase.IDLE:
            return

        self.playback.stop_loop()
        self.tempo_session.end()

        if self.timesync is not None:
            self.timesync.stop()
            self.timesync = None

        self.group = None
        self.group_state = None
        self.members = []
        self.protocol_version = 1
        self.state_version = 0
        self.queue = []
        self.queue_last_update = None
        self.current_item_id = None
        self.current_playlist_item_id = None
        self.current_provider = JELLYFIN
        self.phase = Phase.IDLE
        self.ignore_wait = False
        self.holds.clear_stop()
        self._join_pending_since = 0.0
        self.player.syncplay_group_active = False
        self.holds.release()
        self.publish_session_state(announce=True)
        LOG.debug("---<[ syncplay group ]")

    def _attempt_rejoin(self, force: bool = False) -> None:
        """§9: one automatic re-join before surfacing an error."""
        if not self.last_group_id:
            self._leave_locally()
            return

        now = time.time()

        if not force and now - self._last_rejoin < utils.AUTO_REJOIN_INTERVAL:
            return

        self._last_rejoin = now
        LOG.debug("Attempting SyncPlay rejoin of %s", self.last_group_id)
        self._pending_local_queue = False

        try:
            self._api_raw("syncplay_join", self.last_group_id, 2)
        except Exception as error:
            LOG.warning("SyncPlay rejoin failed: %s", error)
            self._leave_locally()
            self._toast(settings.localized(30571), warning=True)

    def _request_snapshot(self, force: bool = False) -> None:
        """§6: reconcile via a pushed StateSnapshot, rate-limited."""
        if self.protocol_version < 2:
            return

        now = time.time()

        if (
            not force
            and now - self._last_snapshot_request < utils.SNAPSHOT_REQUEST_INTERVAL
        ):
            return

        self._last_snapshot_request = now
        self._api("syncplay_snapshot")

    def _hello(self) -> None:
        """Capability probe (plugin binding): learns the dedicated time-sync
        socket path and registers our protocol version for this device.
        Stock and integrated servers 404 — HTTP time sync stays in place and
        nothing else changes."""
        try:
            # Declared because the engine honours it: a descriptor entry is
            # resolved through the provider registry, and one no provider
            # answers is a graceful load failure, exactly as §14.4 requires.
            info = self._api_raw("syncplay_hello", 2, ["ExternalContent"]) or {}
        except Unauthorized:
            return
        except JellyfinError as error:
            LOG.debug("SyncPlay hello unavailable: %s", error)
            self.timesync_ws_path = None
            return
        except Exception as error:
            LOG.debug("SyncPlay hello failed: %s", error)
            return

        self.timesync_ws_path = (info.get("TimeSync") or {}).get("WebSocketPath")
        self.server_external_content = "ExternalContent" in (
            info.get("Capabilities") or []
        )

        if self.server_external_content:
            LOG.debug("SyncPlay server accepts external content")

        if self.timesync_ws_path:
            LOG.debug("SyncPlay time-sync socket at %s", self.timesync_ws_path)

    def _on_ws_connected(self) -> None:
        """Reconnect contract (§9): a v2 server re-attaches the member and
        pushes a StateSnapshot on its own; verify and pull one if it never
        arrives. v1 servers end the session on any socket close: probe
        GET /SyncPlay/List and re-join, or stop pretending."""
        if not self.in_group():
            if self._rejoin_owed:
                # The group the last generation stayed in: join it again,
                # or hear that it is gone.
                self._rejoin_owed = False
                self._kicked_probe()
            return

        if self.timesync is not None:
            self.timesync.force_update()

        if self.protocol_version >= 2:
            connected_at = time.time()

            def check() -> None:
                if self.in_group() and self.last_snapshot_at < connected_at:
                    LOG.debug("No snapshot pushed after reconnect, requesting one")
                    self._request_snapshot()

            utils.later(5, self._post, check)
        else:
            self._kicked_probe()

    def _kicked_probe(self) -> None:
        groups = self.list_groups()

        if groups is None:
            # Server unreachable right now; the next reconnect re-probes.
            LOG.debug("kicked-probe skipped: group list unavailable")
            return

        group = self.group  # in_group() is exactly this None test
        group_id = group["GroupId"] if group is not None else self.last_group_id

        if any(group.get("GroupId") == group_id for group in groups):
            self._attempt_rejoin(force=True)
            return

        LOG.debug("Group %s no longer exists after reconnect", group_id)
        self._leave_locally()
        self._toast(settings.localized(30571), warning=True)

    # ------------------------------------------------------------------
    # Snapshots and beacons (v2)
    # ------------------------------------------------------------------

    def _apply_snapshot(self, snapshot: dict[str, Any]) -> None:
        """§5.4: equivalent to GroupJoined + PlayQueue + a synthetic command."""
        self.last_snapshot_at = time.time()

        if snapshot.get("GroupName"):
            assert self.group is not None  # snapshots only arrive in-group
            self.group["GroupName"] = snapshot["GroupName"]

        self.group_state = snapshot.get("State")
        self.members = snapshot.get("Members") or self.members

        self._apply_play_queue(snapshot.get("PlayQueue") or {})

        if self.phase == Phase.LOADING:
            # The queue application is (re)loading the item; the ready
            # flow will converge on the snapshot position by itself.
            return

        if self.holds._stop_pending is not None:
            # The stop prompt is open and the queue started nothing (it
            # named the item stopped here): there is no playback for a
            # synthetic command to act on, and none may be recorded as
            # applied.
            return

        state = snapshot.get("State")

        if snapshot.get("IsPlaying"):
            command = "Unpause"
        elif state == "Idle":
            command = "Stop"
        else:
            command = "Pause"

        self._handle_command(
            {
                "Command": command,
                "When": snapshot.get("When"),
                "EmittedAt": snapshot.get("When"),
                "PositionTicks": snapshot.get("PositionTicks") or 0,
                "PlaylistItemId": self.current_playlist_item_id,
                "StateVersion": None,
            }
        )

    def _on_beacon(
        self,
        beacon: dict[str, Any],
        version: Optional[int],
        previous_version: Optional[int],
    ) -> None:
        """§11: advisory position data; §6: version gap detection."""
        if version is not None and previous_version and version > previous_version:
            LOG.debug(
                "Beacon v%s ahead of last update v%s, requesting snapshot",
                version,
                previous_version,
            )
            self._request_snapshot()

        if (
            beacon.get("PlaylistItemId")
            and beacon["PlaylistItemId"] == self.current_playlist_item_id
        ):
            when_ms = utils.parse_iso_ms(beacon.get("When"))

            if when_ms is not None:
                self.playback.set_reference(
                    beacon.get("PositionTicks") or 0, when_ms, True
                )

    # ------------------------------------------------------------------
    # Queue mirror (SYNCPLAY.md §5.3)
    # ------------------------------------------------------------------

    def _apply_play_queue(self, data: dict[str, Any]) -> None:
        last_update = utils.parse_iso_ms(data.get("LastUpdate"))

        # LastUpdate timestamps queue contents, not the playing item.
        if (
            last_update is not None
            and self.queue_last_update is not None
            and last_update < self.queue_last_update
        ):
            LOG.debug("Ignoring play queue not newer than the applied one")
            return

        self.queue_last_update = last_update
        playlist = data.get("Playlist") or []
        self.queue = [self._queue_entry(entry) for entry in playlist]
        index = data.get("PlayingItemIndex", -1)
        is_playing = bool(data.get("IsPlaying"))
        start_ticks = data.get("StartPositionTicks") or 0

        LOG.debug(
            "[ syncplay/queue ] %s items, playing %s (%s)",
            len(self.queue),
            index,
            data.get("Reason"),
        )

        if index is None or index < 0 or index >= len(self.queue):
            self._detach_playback(stop_media=True)
            return

        item_id, playlist_item_id, provider = self.queue[index]

        if (
            playlist_item_id == self.current_playlist_item_id
            and self.phase != Phase.IDLE
        ):
            return  # tail-only change; drift reference stays authoritative

        if self.holds.stopped_here(playlist_item_id):
            # A re-sent queue or a snapshot, not a new selection: the group
            # is still on the item the user just stopped. A different item
            # falls through and starts — the group really moved on, which is
            # what LocalStarts._superseded expects.
            LOG.debug(
                "[ syncplay/queue ] still the item stopped here; "
                "waiting on the stop prompt"
            )
            return

        # Position reference: StartPositionTicks is extrapolated to *send* time
        # by the server (Group.cs::GetPlayQueueUpdate adds the elapsed since
        # LastActivity), so the instant it describes is now — not LastUpdate,
        # which timestamps the *queue's* last change and, on a group that has
        # been playing a while, is arbitrarily far in the past.
        reference_ms = self.server_now_ms()
        self.playback.set_reference(start_ticks, reference_ms, is_playing)

        held = self.holds._hold
        held_match = held is not None and held.get("item_id") == item_id

        if (
            item_id
            and self.player.isPlaying()
            and (item_id == self._local_item_id() or held_match)
        ):
            # We are already playing this exact item (e.g. the queue we
            # just proposed with SetNewQueue came back with a fresh
            # PlaylistItemId): adopt it. Never tear down and reload media
            # that is already on screen, regardless of phase. A held start
            # matches on the id we proposed, since the play pipeline may
            # not have claimed the new item yet.
            LOG.debug("Adopting queue identity for the playing item")
            self.holds.ended("adopted")
            self.current_item_id = item_id
            self.current_playlist_item_id = playlist_item_id
            self.current_provider = provider
            self.phase = Phase.WAITING_READY
            self.playback.ensure_paused()
            self._post(self.playback.prepare_ready)
            self.publish_session_state()
            return

        if self.ignore_wait and self.player.isPlaying():
            # A spectator watching their own thing: the group's queue
            # must not tear it down. They re-attach via the menu (or
            # automatically once their player is idle again).
            LOG.debug("Spectator playing own media; not following the queue")
            return

        self._start_item(item_id, playlist_item_id, provider)

    @staticmethod
    def _queue_entry(entry: dict[str, Any]) -> tuple[Any, Any, Any]:
        """(key, PlaylistItemId, provider) for one wire playlist entry.

        A descriptor entry (SYNCPLAY.md §14.3) is identified by its
        Provider:Key; the ItemId beside it is a server-side sentinel and
        never a client-side identity — claims carry the key, so every
        comparison against _local_item_id keeps working unchanged.
        """
        content = entry.get("Content")

        if isinstance(content, dict) and content.get("Key"):
            return (
                content["Key"],
                entry.get("PlaylistItemId"),
                content.get("Provider") or JELLYFIN,
            )

        return (entry.get("ItemId"), entry.get("PlaylistItemId"), JELLYFIN)

    def _start_item(
        self, item_id: str, playlist_item_id: Optional[str], provider: str = JELLYFIN
    ) -> None:
        if not self.in_group():  # left while this update was in flight
            return

        self.phase = Phase.LOADING
        self.current_item_id = item_id
        self.current_playlist_item_id = playlist_item_id
        self.current_provider = provider
        # Whatever starts here replaced the stop (_apply_play_queue never
        # brings the stopped item itself this far while the prompt is open).
        self.holds.clear_stop()
        # A leftover zap Unpause must not resume the next item. last_command
        # stays: a transcode Seek reload is the same event, and clearing it
        # here would re-apply the Seek.
        self.playback._deferred_unpause = None

        estimate_ms = self.playback.estimate_position_ms() or 0
        allowance_ms = self._load_allowance_ms()
        estimate_ms += allowance_ms
        self._load_started_ms = utils.local_ms()

        LOG.debug(
            "[ syncplay/play ] %s (%s) at %.1fs%s",
            item_id,
            playlist_item_id,
            estimate_ms / 1000.0,
            (
                " (+%.1fs load allowance)" % (allowance_ms / 1000.0)
                if allowance_ms
                else ""
            ),
        )

        if self.providers.is_delegated(provider):
            # A delegated start (the provider contract): the content is
            # tuned, not fetched, so the provider's own service executes
            # the start and this member's playback arrives like any other
            # local play — on_avstarted completes the load, and the load
            # watchdog below covers a start nobody executes.
            contract.publish_start(provider, item_id, utils.ms_to_ticks(estimate_ms))
        else:
            try:
                target = self.providers.play_target(
                    item_id, utils.ms_to_ticks(estimate_ms), provider=provider
                )
            except Exception as error:
                LOG.warning("SyncPlay item lookup failed: %s", error)
                self._load_failed("item lookup failed")
                return

            runtime_ms = utils.ticks_to_ms(target.get("runtime_ticks"))

            if runtime_ms and estimate_ms >= runtime_ms:
                # The group's clock has run off the end of the item. A load
                # aimed there ends at once on direct play and starts over from
                # 0:00 on a transcode, so nothing is loaded. The item stays
                # ours, and a queue or snapshot that puts the group back inside
                # it starts it then.
                LOG.debug(
                    "[ syncplay/play ] not started: %.1fs is at or past the "
                    "item's end (%.1fs)",
                    estimate_ms / 1000.0,
                    runtime_ms / 1000.0,
                )
                self.phase = Phase.IDLE
                self._load_started_ms = None
                self.publish_session_state()
                return

            try:
                self.playback.play_item(target)
            except Exception as error:
                LOG.exception("SyncPlay playback start failed: %s", error)
                self._load_failed(error)
                return

        # Identify the load, not the item: a transcode seek reloads the *same*
        # playlist item, so an earlier load's watchdog would fire into a
        # healthy reload and leave the group.
        self._load_generation += 1
        generation = self._load_generation

        def check() -> None:
            if self.phase == Phase.LOADING and self._load_generation == generation:
                self._load_failed("no playback within 45s")

        utils.later(45, self._post, check)
        self.publish_session_state()

    def _load_failed(self, reason: Union[str, Exception]) -> None:
        LOG.warning("SyncPlay could not start playback: %s", reason)
        self._toast(settings.localized(30576), error=True)

        try:
            self._api_raw("syncplay_leave")
        except Exception:
            pass

        self._leave_locally()

    def _detach_playback(self, stop_media: bool = False) -> None:
        was_active = self.phase != Phase.IDLE
        self.holds.ended("detached")
        self.current_item_id = None
        self.current_playlist_item_id = None
        self.phase = Phase.IDLE
        self.playback.cancel_pending()
        self.playback.last_command = None
        self.playback._deferred_unpause = None

        # Only kill media that SyncPlay itself is driving: joining an
        # idle group must not stop whatever the user was watching.
        if stop_media and was_active:
            self.playback.stop_media()

        self.publish_session_state()

    def on_group_stopped(self) -> None:
        """A Stop command was executed."""
        self.current_item_id = None
        self.current_playlist_item_id = None
        self.phase = Phase.IDLE
        self.publish_session_state()

    def on_local_unpaused(self) -> None:
        """An Unpause command was executed against loaded media."""
        if self.phase in HELD:
            self.phase = Phase.SYNCED
            self.publish_session_state()

    # ------------------------------------------------------------------
    # Player events (called from service/player.py hooks)
    # ------------------------------------------------------------------

    def on_playback_started(self) -> None:
        """Earliest signal of a local item start, before A/V rolls.

        Runs on the player callback thread the instant playback begins
        (including a native playlist advance), so a start that must wait
        for the group is paused before it plays audibly rather than a few
        seconds in when the round trip completes.
        """
        if not self.in_group():
            return

        if self.phase == Phase.LOADING:
            # Our own play_item(): try to hold before the first frame;
            # on_avstarted re-ensures once the player is fully up.
            self.playback.ensure_paused()
            return

        # No is_programmatic() test: play_item() is the only start kofin
        # makes, and the echo grace after our own pause or seek must not
        # swallow the start of a file the viewer opened.

        if self.ignore_wait:
            # A spectator's own plays stay local: nothing is proposed to
            # the group, so there is nothing to hold (or demote) either.
            return

        if self.phase in STARTABLE:
            # Phase "synced" means no stop intervened since the synced item:
            # a native playlist advance, or a video the user picked in its
            # place (Kodi's player opens it in place, with no stop). Phase
            # "idle" is a fresh user start (possibly at a resume point).
            self.holds.enter(transition=self.phase == Phase.SYNCED)

    def on_kodi_play(self, data: dict[str, Any]) -> None:
        """Player.OnPlay from the Kodi bus: carries the Kodi library id,
        the earliest identification of a local start (before the play
        pipeline claims the item). Called on the notification thread."""
        self.holds.on_kodi_play(data)

    def on_avstarted(self) -> None:
        if not self.in_group():
            return

        # A seamless PVR zap emits no OnPlay and no stop — this is the one
        # event every new stream reliably fires, so the stale-claim drop
        # anchors here as well as on OnPlay.
        self.bus.drop_stale_claim()
        self.playback.note_live_origin()

        if self.phase == Phase.LOADING:
            # Hold the first frame; the group start is choreographed by
            # the server once every member reports Ready.
            self._note_load_completed()
            self.playback.ensure_paused()
            self.phase = Phase.WAITING_READY
            self._post(self.playback.prepare_ready)
            return

        if self.ignore_wait:
            return  # a spectator's own plays are not forwarded

        hold = self.holds._hold

        if hold is not None and not hold["proposed"]:
            # The early pause is best-effort while the player is still
            # opening; with A/V up it always lands. Our own pause above
            # must not swallow the forward via the programmatic grace.
            self.playback.ensure_paused()
            self._post(self.holds.forward)
            return

        if not self.is_programmatic() and self.phase in STARTABLE:
            self._post(self.holds.forward)

    def on_paused(self) -> None:
        if not self.in_group() or self.is_programmatic():
            return

        if self.phase == Phase.SYNCED:
            LOG.debug("[ syncplay/user pause ]")
            self._post(self._api, "syncplay_pause")

    def on_resumed(self) -> None:
        # First, in a group or not: a pulse cut while paused left its 1.0
        # owed.
        self.playback.tempo.settle_owed()

        if not self.in_group() or self.is_programmatic():
            return

        claim = self.player.current_item()
        if claim and not claim.get("Paused"):
            # Nothing was paused. Kodi sets speed 1 before it opens a file,
            # and VideoPlayer reports that as a resume even while playing,
            # ahead of the file's start. The service records a pause or a
            # resume on its claim only after forwarding it here.
            return

        if self.phase in FOLLOWING:
            LOG.debug("[ syncplay/user unpause ]")
            # The group start time is the server's call: hold position
            # and ask for a group unpause instead of running ahead.
            self.playback.ensure_paused()
            self._post(self._api, "syncplay_unpause")

    def on_seek(self, seconds: float) -> None:
        if not self.in_group() or self.is_programmatic():
            return

        if self.holds._hold is not None:
            # The held file is not the group's item yet: its position goes
            # to the group with the proposal, from the claim.
            return

        if self.phase in FOLLOWING:
            LOG.debug("[ syncplay/user seek ] %.1fs", seconds)
            self._post(self._api, "syncplay_seek", utils.seconds_to_ticks(seconds))

    def on_stopped(self) -> None:
        self.bus.foreign_claim = None  # claims are playback-scoped
        self.holds.ended("stopped")

        if not self.in_group() or self.is_programmatic():
            return

        if self.phase == Phase.LOADING:
            return  # load-failure timer handles it

        if self.phase in FOLLOWING:
            # Marked before the detach clears the item: the dispatcher can be
            # handling a group command for it on its own thread right now.
            pending = self.holds.note_stop(self.current_playlist_item_id)
            self._detach_playback()
            self.holds.prompt_in_thread(pending)

    def on_ended(self) -> None:
        self.bus.foreign_claim = None  # claims are playback-scoped
        self.holds.ended("ended")

        if not self.in_group() or self.is_programmatic():
            return

        if self.phase != Phase.SYNCED:
            return

        playlist_item_id = self.current_playlist_item_id
        self.phase = Phase.IDLE

        if playlist_item_id:
            LOG.debug("[ syncplay/next item ]")
            self._post(self._api, "syncplay_next_item", playlist_item_id)

    def on_error(self) -> None:
        if not self.in_group():
            return

        LOG.warning("Playback error while in a SyncPlay group")
        self._detach_playback()
        self.ignore_wait = True
        self._post(self._api, "syncplay_set_ignore_wait", True)
        self._toast(settings.localized(30576), error=True)

    # ------------------------------------------------------------------
    # The public provider contract
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Lifecycle from the service
    # ------------------------------------------------------------------

    # -- the provider bus (bus.py) ---------------------------------------------

    def on_foreign_claim(self, claim: Claim) -> None:
        self.bus.on_foreign_claim(claim)

    def on_provider_register(self, sender: str, payload: dict[str, Any]) -> None:
        self.bus.on_provider_register(sender, payload)

    def on_propose(self, payload: dict[str, Any]) -> None:
        self.bus.on_propose(payload)

    def publish_session_state(self, announce: bool = False) -> None:
        self.bus.publish_session_state(announce)

    def on_sleep(self) -> None:
        self.playback.cancel_pending()

    def on_wake(self) -> None:
        """Screensaver deactivate / system wake: never trust a stale clock
        offset, and reconcile the group — after a sleep the socket may be a
        zombie. A v2 snapshot request also re-attaches the membership
        server-side; v1 keeps the kicked-probe."""
        if self.timesync is not None:
            self.timesync.force_update(reset=True)

        if not self.in_group():
            return

        if self.protocol_version >= 2:
            self._post(self._request_snapshot, True)
        else:
            self._post(self._kicked_probe)
