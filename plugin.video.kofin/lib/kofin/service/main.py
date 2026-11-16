"""Service lifecycle: build, run, and rebuild on soft restart.

The outer loop owns restarts — a restart tears the Service object down and
builds a fresh one. Nothing may survive a cycle at module level; all state
lives on the objects rebuilt each pass.
"""

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
import time
from typing import Any, Optional

import xbmc

from kofin.core import (
    auth,
    contract,
    diag,
    ipc,
    kodirpc,
    log,
    settings,
    state,
    toast,
)
from kofin.core.api import Api
from kofin.core.http import Http, HttpError, JellyfinError
from kofin.core.log import Logger
from kofin.core.settings import Credentials, addon_version
from kofin.core.ws import WSClient
from kofin.service import backdrop
from kofin.service.kodiuserdata import KodiUserData
from kofin.service.player import Player
from kofin.service.remote import RemoteHandler
from kofin.service.settings_apply import SettingsApplier
from kofin.service.ports import (
    DownloadsPort,
    LibraryPort,
    SyncPlayPort,
    forward,
    spawn_once,
)

LOG = Logger(__name__)

LIBRARY_COMMANDS = frozenset(
    {
        ipc.REMOVE_LIBRARY,
        ipc.REPAIR_LIBRARY,
        ipc.UPDATE_LIBRARY,
        ipc.SYNC_PLAYLISTS,
    }
)


# Seconds the service ignores settings changes after start, covering Kodi's
# startup settings-load transients. A user cannot open the settings dialog and
# edit within this window; a real change always lands well after it.
SETTINGS_READY_DELAY = 5.0

# How long the teardown waits for the library thread on a soft restart (kofin's
# own restart IPC), where nothing else bounds the wait. On an add-on bounce Kodi
# raises abortRequested and the join gives up on its first tick. Kodi will not
# finalise a script while a thread it started is still alive, so only the
# thread returning sooner shortens a stop (core/http.Http, ``abort``).
LIBRARY_JOIN_SECONDS = 30.0

# Server lifecycle websocket messages -> the string announcing them. These are
# the server telling us it is about to go away; the websocket drop that
# follows is then explained rather than mysterious.
SERVER_LIFECYCLE_MESSAGES = {
    "ServerRestarting": 30417,
    "ServerShuttingDown": 30418,
}

# How long a dropped websocket may stay down before the user hears about it. A
# drop that heals inside the grace is not announced: Android TV standby
# recycles the socket routinely, and Kodi replays every queued toast at wake.
LOST_TOAST_GRACE_SECONDS = 90.0

# How long after the websocket opens the service registers its capabilities:
# the server attaches the socket's session asynchronously.
SESSION_SETTLE_SECONDS = 2.0

# How long after Play all's queue is full the service starts it
# (_ipc_start_queue): the script that filled it can end over 100 ms after the
# first track was asked for. The wait for the queue to fill is capped at
# QUEUE_FILL_TIMEOUT.
QUEUE_START_DELAY = 0.3
QUEUE_FILL_TIMEOUT = 10.0

CAPABILITIES: dict[str, Any] = {
    "PlayableMediaTypes": "Audio,Video",
    "SupportsMediaControl": True,
    "SupportedCommands": (
        "MoveUp,MoveDown,MoveLeft,MoveRight,Select,"
        "Back,ToggleContextMenu,ToggleFullscreen,ToggleOsdMenu,"
        "GoHome,PageUp,NextLetter,GoToSearch,"
        "GoToSettings,PageDown,PreviousLetter,TakeScreenshot,"
        "VolumeUp,VolumeDown,ToggleMute,SendString,DisplayMessage,"
        "Mute,Unmute,SetVolume,"
        "Play,Playstate,PlayNext"
    ),
}


class Backoff:
    """Exponential retry schedule: 5s doubling to a 120s ceiling."""

    def __init__(self, start: float = 5.0, ceiling: float = 120.0) -> None:
        self._start = start
        self._ceiling = ceiling
        self._delay = start
        self.next_attempt = 0.0

    def failed(self, now: float) -> float:
        """Record a failure; returns the delay until the next attempt."""
        delay = self._delay
        self.next_attempt = now + delay
        self._delay = min(self._delay * 2, self._ceiling)
        return delay

    def succeeded(self) -> None:
        self._delay = self._start
        self.next_attempt = 0.0

    def due(self, now: float) -> bool:
        return now >= self.next_attempt


class Service(xbmc.Monitor):
    # The two notification tables: Kodi's bus by method, kofin's IPC by
    # message name — one small handler per arm, the guards inside the
    # handlers. Method names rather than bound methods, on the class rather
    # than built in __init__, because the unit suite legitimately builds a
    # Service with __new__ and no __init__ to drive onNotification alone.
    _KODI_HANDLERS: dict[str, str] = {
        "GUI.OnScreensaverDeactivated": "_kodi_screensaver_deactivated",
        "System.OnWake": "_kodi_wake",
        "System.OnSleep": "_kodi_sleep",
        "Player.OnPlay": "_kodi_player_play",
        "Player.OnStop": "_kodi_player_stop",
        "VideoLibrary.OnUpdate": "_kodi_library_update",
    }
    _IPC_HANDLERS: dict[str, str] = {
        ipc.RESTART: "_ipc_restart",
        ipc.AUTH_CHANGED: "_ipc_auth_changed",
        ipc.SYNCPLAY_MENU: "_ipc_syncplay_menu",
        ipc.WHO_IS_WATCHING: "_ipc_who_is_watching",
        ipc.ATTACH_SUBTITLE: "_ipc_attach_subtitle",
        ipc.START_QUEUE: "_ipc_start_queue",
        ipc.DOWNLOAD_ADD: "_ipc_download_add",
        ipc.DOWNLOAD_CANCEL: "_ipc_download_cancel",
        ipc.DOWNLOAD_REMOVE: "_ipc_download_remove",
        ipc.DOWNLOAD_REMOVE_ALL: "_ipc_download_remove_all",
        **{command: "_ipc_library_command" for command in LIBRARY_COMMANDS},
    }
    # The public provider contract: messages any add-on may send, validated
    # in core/contract.py. Routed by name for every sender that is neither
    # xbmc nor kofin — the sender IS the provider's own id, which is exactly
    # why these cannot live in the kofin-sender IPC table.
    _CONTRACT_HANDLERS: dict[str, str] = {
        contract.REGISTER: "_contract_register",
        contract.CLAIM: "_contract_claim",
        contract.PROPOSE: "_contract_propose",
        contract.MENU: "_contract_menu",
    }

    def __init__(self) -> None:
        super().__init__()
        self._restart_requested = False
        # This generation is tearing down: an Event owned by this generation.
        self._stopping = threading.Event()
        self.credentials = Credentials.load()
        self.http = Http(abort=self._abort_transport, user_agent=settings.user_agent())
        self.api = Api.from_credentials(self.http, self.credentials)
        self.ws: Optional[WSClient] = None
        self.player = Player(self.api, modal=self.modal)
        self.remote = RemoteHandler()
        self.kodi_userdata = KodiUserData(self.api)
        self.library: Optional[LibraryPort] = None
        self.downloads: Optional[DownloadsPort] = None
        self.syncplay: Optional[SyncPlayPort] = None
        self._syncplay_menu: Optional[threading.Thread] = None
        self._who_is_watching: Optional[threading.Thread] = None
        # The modal dialogs of ours that are open, by Kodi's window name
        # (Dialog.Close), counted: shutdown closes them so that no worker
        # waits on an answer for a generation that has gone.
        self._dialogs: dict[str, int] = {}
        self._dialogs_lock = threading.Lock()
        # Whether this generation has announced a refused session.
        self._session_rejected = False
        self._backdrop: Optional[threading.Thread] = None
        # Post-connect worker (see _on_ws_connected): the pending event is
        # how a reconnect that lands mid-run asks for one more pass.
        self._post_connect: Optional[threading.Thread] = None
        self._post_connect_pending = threading.Event()
        self._online = False
        # Whether ``run`` has prepared the backend, and whether a connection
        # still owes what it starts that reads the preparation
        # (_start_followers).
        self._backend_prepared = False
        self._followers_owed = False
        # Raised by the websocket's disconnect callback, consumed by the next
        # tick: a dropped socket asks for a *probe* rather than declaring the
        # server gone (see _verify_connection).
        self._verify_online = False
        self._backoff = Backoff()
        # The last tick failure, so a repeated one is logged once in full.
        self._tick_failure = ""
        # Paces _recover_threads' rebuilds of a library thread that keeps
        # dying; one that gets past startup resets it.
        self._library_backoff = Backoff()
        # Connection toasts announce states, not websocket edges (see
        # _connection_toast). Both fields are read and written under the lock,
        # from the websocket thread and the service tick.
        self._conn_toast_lock = threading.Lock()
        self._down_since: Optional[float] = None
        self._announce_next_connect = True
        # This generation's IPC secret (see ipc.GUARDED): minted here so the
        # plugin process picks it up from the moment the service exists, and
        # invalidated by the next restart.
        self._ipc_nonce = ipc.rotate_nonce()
        self.settings_apply = SettingsApplier(self)

    def _abort_transport(self) -> bool:
        """Whether a transport retry ladder should give up rather than replay.

        Two signals, deliberately both. ``self._stopping`` is this generation
        tearing itself down (see __init__). ``abortRequested()`` is Kodi
        stopping this *script* — an addon bounce, a profile switch, Kodi
        exiting — and Kodi raises it before ``_shutdown`` runs (the run loop
        is the thing that notices the flag), so a thread already inside a
        ladder would read the Event alone as "carry on".
        """
        return self._stopping.is_set() or self.abortRequested()

    # -- lifecycle -----------------------------------------------------------

    def run(self) -> bool:
        """Run until abort or restart; returns True when a rebuild is wanted."""
        LOG.debug("--->>> kofin service %s", addon_version())
        LOG.debug("kodi %s", xbmc.getInfoLabel("System.BuildVersion"))
        # The server is asked before anything is prepared. The probe, the
        # websocket and SyncPlay read none of it, and at Kodi's start the
        # preparation shares the interpreter lock with every other add-on's
        # scripts. What a connection starts that does read it waits for the
        # preparation (_start_followers).
        if not self.abortRequested():
            self._guarded_tick()
        self._settle_left_tempo()
        try:
            self._prepare_api_backend()
        except Exception:
            # Sync setup must not prevent connection, playback reporting or
            # live browsing, including when the private store is damaged.
            LOG.exception(
                "API backend preparation failed; native sync remains disabled"
            )
        self._backend_prepared = True
        started = time.time()
        try:
            while not self.abortRequested():
                if self._restart_requested:
                    break
                if (
                    not self.settings_apply.ready
                    and time.time() - started >= SETTINGS_READY_DELAY
                ):
                    self.settings_apply.mark_ready()
                self._guarded_tick()
                if self.waitForAbort(1):
                    break
        finally:
            self._shutdown()
        LOG.debug("---<<< kofin service")
        return self._restart_requested and not self.abortRequested()

    def _guarded_tick(self) -> None:
        """One tick, never fatal: Kodi does not start a service script again
        once it has ended, so an exception out of ``run`` would leave Kodi
        without the service until it restarts."""
        try:
            self._tick()
        except Exception as error:
            failure = "%s: %s" % (type(error).__name__, error)
            if failure == self._tick_failure:
                LOG.debug("service tick failed again (%s)", failure)
            else:
                LOG.exception("service tick failed")
            self._tick_failure = failure
            if not self._online:
                # Offline, the tick's work is the connection attempt: one that
                # failed outside the transport's errors is a failed attempt as
                # one inside them is, so it waits out the backoff and states
                # the outage (see _connect).
                self._backoff.failed(time.time())
                state.set_online(False)
        else:
            if self._online:
                # Offline, the ticks between attempts raise nothing, so only
                # a connection ends a failure: the same error on the next
                # attempt is a repeat.
                self._tick_failure = ""

    def _prepare_api_backend(self) -> None:
        from kofin.sync.backends.api import APIBackend, capabilities
        from kofin.sync.backends.api import status as apistatus
        from kofin.sync.catalogue import BackendMismatch
        from kofin.sync.private import addon_data_path
        import os

        self._api_interfaces = False
        backend = APIBackend()
        report = backend.capabilities()
        try:
            backend.initialize()
            report["private_state"] = "ready"
            self._api_interfaces = report["interfaces_passed"]
        except BackendMismatch:
            report["private_state"] = "fresh library required"
            self._api_interfaces = False
            report["native_sync_enabled"] = False
        directory = addon_data_path()
        os.makedirs(directory, exist_ok=True)
        target = os.path.join(directory, capabilities.REPORT)
        with open(target + ".part", "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        os.replace(target + ".part", target)
        LOG.debug(
            "API movie backend: interfaces=%s private_state=%s",
            report["interfaces_passed"],
            report["private_state"],
        )
        # Once, here: a feature this Kodi lacks is off by name, never an error
        # per item or per pass.
        LOG.debug("Kodi features %s", capabilities.summary(report))
        state.set_feature_tempo((report.get("features") or {}).get("tempo") is True)
        if report["private_state"] != "ready":
            apistatus.write_earlier()
        elif not self._api_interfaces:
            apistatus.write(settings.localized(30420) % "; ".join(report["errors"]))
        elif self.credentials.is_logged_in:
            # Published native work is replayable without waiting for Jellyfin
            # to reconnect after Kodi restarts.
            self._start_library()

    def _tick(self) -> None:
        # On every tick, not once at the start: after an add-on update the
        # generation before this one hands its play over only once its own
        # teardown reaches the player.
        self.player.adopt()
        self._maybe_announce_lost()
        if self._verify_online:
            self._verify_connection()
        if (
            self.credentials.is_logged_in
            and not self._online
            and self._backoff.due(time.time())
        ):
            self._connect()
        elif self._online:
            self._republish_online()
            # A thread can also die while the server stays perfectly
            # reachable, and then nothing else ever looks: ``_connect`` is the
            # only other rebuild path and it runs only on the offline→online
            # edge. Costs two ``is_alive()`` calls a second and does nothing
            # at all until one of them answers False.
            self._recover_threads()
            self.player.sweep_live_streams()
        if self._followers_owed and self._backend_prepared and self._online:
            self._followers_owed = False
            self._start_followers()

    def _republish_online(self) -> None:
        """Re-raise the online flag when something else lowered it.

        ``PROP_ONLINE`` is one window property shared by every generation, and
        a *superseded* service clears it on its way out (see ``_superseded``),
        so it is re-asserted on every tick while online rather than only
        written on the offline→online edge.
        """
        if state.is_online():
            return
        LOG.warning("the online flag was lowered under a live connection; restoring")
        state.set_online(True)

    def _recover_threads(self) -> None:
        """Rebuild the websocket and the sync manager if either has died.

        Silent death is the failure this answers. Both own a thread that ends
        on its own — the library on any exception, the websocket on an
        upstream raise — while the object stays in its slot, and every restart
        path guards on the slot rather than the thread.

        Library rebuilds are paced by ``_library_backoff``: the first rebuild
        after a healthy run is immediate, and only consecutive failures wait,
        5 s doubling to the 120 s ceiling. The offline→online edge
        (``_connect``) and the settings paths are not paced.
        """
        if self.ws is not None and not self.ws.is_alive():
            self._reap_websocket()

            if self.ws is None:
                self._start_websocket()

        library = self.library

        if library is None:
            return

        if library.is_alive():
            # Past startup and still in its service loop: whatever felled the
            # previous builds is over, so the next death starts a fresh
            # ladder. A manager that *failed* startup is also briefly alive on
            # its way out — with stop_thread already raised (run() raises it
            # before startup_done), which is what keeps a failing build from
            # resetting the ladder it is climbing.
            if library.startup_done and not library.stop_thread:
                self._library_backoff.succeeded()
            return

        if not self._library_backoff.due(time.time()):
            return

        self._library_backoff.failed(time.time())
        self._start_library()

    def _verify_connection(self) -> None:
        """Answer a dropped socket with a probe, not a verdict.

        A drop is a question the probe answers; lowering the online flag on
        every blink would act on it.
        """
        self._verify_online = False
        if not self._online:
            return
        try:
            self.api.probe_info()
        except JellyfinError as error:
            LOG.debug("socket dropped and the server does not answer (%s)", error)
            self._go_offline()
            return
        LOG.debug("socket dropped but the server answers; staying online")

    def _go_offline(self) -> None:
        """Declare the server gone: the flag drops and the connect loop
        takes over. The websocket is left alone deliberately — it owns its
        own reconnection, and stopping it here would either block this
        thread on its join or leave two clients once ``_connect`` rebuilt
        one."""
        self._online = False
        state.set_online(False)
        self._backoff.succeeded()  # probe now, not after the old backoff

    def _connect(self) -> None:
        # The probe budget, not the transport default: this runs on the
        # service loop, whose 1 s tick is also what notices stop requests,
        # and the backoff schedule is already the retry policy (see
        # api.PROBE_TIMEOUT).
        try:
            info = self.api.probe_info()
        except JellyfinError as error:
            delay = self._backoff.failed(time.time())
            LOG.warning("server not reachable (%s); retry in %.0fs", error, delay)
            # A failed probe is knowledge, whether or not we were ever online:
            # on a cold boot away from the server nothing else ever states the
            # outage, and the flag would sit absent forever — which reads as
            # "nobody has said yet" and leaves every refusal waiting for the
            # transport instead of answering.
            state.set_online(False)
            return

        LOG.debug("connected to %s (%s)", info.get("ServerName"), info.get("Version"))
        self._backoff.succeeded()
        self._online = True
        state.set_online(True)
        self._start_syncplay()  # before the websocket: messages route into it
        # Only when there is none: a reconnect after a confirmed outage finds
        # the previous client still running its own retry loop, and building a
        # second one would double every event the server pushes. Liveness, not
        # presence: the slot outlives the thread, so a client whose thread has
        # ended reads as "one is already running" and the reconnect silently
        # brings back no websocket at all.
        self._reap_websocket()
        if self.ws is None:
            self._start_websocket()
        self._followers_owed = True

    def _start_followers(self) -> None:
        """What a connection starts that reads what ``run`` prepares: the
        library entries read the capability report, and the library thread
        the interfaces it found. The downloads and the backdrop go with
        them, since nothing waits on either. The tick of the connection runs
        this, or the first tick after the preparation when the connection
        was made ahead of it."""
        try:
            from kofin.sync.dynamic import publish_from

            publish_from(self.api)
        except Exception:
            LOG.exception("dynamic library entries unavailable")
        self._start_library()
        self._start_downloads()
        self._start_backdrop()

    def _reap_websocket(self) -> None:
        """Empty the websocket slot when the thread behind it has ended.

        ``stop()`` on the way out rather than dropping the reference: the
        thread can die with the socket still open (an upstream raise out of
        ``run_forever`` does exactly that), and the descriptor is this
        object's only remaining handle on it.
        """
        client = self.ws

        if client is None or client.is_alive():
            return

        LOG.warning("websocket thread is gone; rebuilding the client")
        try:
            client.stop()
        except Exception:  # pragma: no cover - defensive
            LOG.exception("stopping the dead websocket client failed")
        self.ws = None

    def _reap_library(self) -> None:
        """Empty the library slot when the manager thread has ended.

        Held back while any worker it spawned is still running; the slot stays
        occupied and the next caller tries again.
        """
        library = self.library

        if library is None or library.is_alive():
            return

        library.stop_client()

        if library.workers_alive():
            LOG.debug("library thread gone but its workers are still running")
            return

        LOG.warning("library sync manager thread is gone; rebuilding")
        self.library = None

    def _start_library(self) -> None:
        """Start the sync manager when there is anything to sync or resume.
        Import and failures are contained: playback and remote control must
        survive a broken sync stack (degrade, don't die)."""
        if self._stopping.is_set():
            return
        if not getattr(self, "_api_interfaces", False):
            return
        self._reap_library()
        if self.library is not None:
            return
        try:
            from kofin.sync import private
            from kofin.sync.backends.api.library import Library as VideoLibrary
            from kofin.sync.backends.api.identity import current_store

            if not (
                settings.get_list("librarySelection") or private.get_sync()["Whitelist"]
            ):
                store = current_store()
                if not (store.has_pending() or store.local_pending()):
                    return
            self.library = VideoLibrary(self.api, self.player, self._new_api)
            self.library.start()
        except Exception:
            LOG.exception("API video sync manager failed to start")
            self.library = None

    def _start_downloads(self) -> None:
        """Build the download manager when enabled. Contained like the library
        manager: playback and sync must survive a broken downloads stack
        (degrade, don't die)."""
        if self._stopping.is_set():
            return
        if self.downloads is not None:
            return
        if not settings.get_bool("downloadsEnabled"):
            LOG.debug("downloadsEnabled off; no download manager built")
            return
        try:
            from kofin.downloads.manager import DownloadManager

            self.downloads = DownloadManager(
                self._new_api, self._refresh_downloads, self._stopping
            )
            self.downloads.start()
            LOG.debug("download manager started")
        except Exception:
            LOG.exception("download manager failed to start")
            self.downloads = None

    def _stop_downloads(self) -> None:
        manager = self.downloads
        if manager is None:
            return
        self.downloads = None
        try:
            manager.stop()
        except Exception:
            LOG.exception("download manager failed to stop")

    def _refresh_downloads(self, databases: list[str]) -> None:
        """The downloads manager's way onto screens: through the library
        manager, which queues a FastSync, never a bare builtin. No library
        manager means nothing native is rendering the rows anyway."""
        library = self.library
        if library is not None and databases:
            library.refresh_libraries()

    def _new_api(self) -> Api:
        """A fresh Api with its own HTTP session (one per sync worker).

        ``abort`` matters most here: these are the sessions of the download
        pool and of the library thread's page fetches, and a page fetch still
        riding its retry ladder is what keeps the library thread alive past
        the teardown.
        """
        return Api.from_credentials(
            Http(abort=self._abort_transport, user_agent=settings.user_agent()),
            Credentials.load(),
        )

    # -- syncplay --------------------------------------------------------------

    def _settle_left_tempo(self) -> None:
        """A SyncPlay pulse's rate outlives the service generation that asked
        for it: Kodi plays the item on at that rate until 1.0 is asked for.
        The record of it does too (``state.syncplay_pulse``), and this is
        what puts 1.0 back after an update or a crash mid-pulse."""
        try:
            from kofin.syncplay import tempo

            tempo.settle_left_rate(" by an earlier service")
        except Exception:
            LOG.exception("left tempo settle failed")

    def _start_syncplay(self) -> None:
        """Build the SyncPlay manager when enabled. Contained like the
        library manager: playback and remote control must survive a broken
        SyncPlay stack (degrade, don't die)."""
        if self._stopping.is_set():
            return
        if self.syncplay is not None:
            return
        if not settings.get_bool("syncPlayEnabled"):
            LOG.debug("syncPlayEnabled off; no SyncPlay manager built")
            return
        try:
            from kofin.syncplay import SyncPlayManager
            from kofin.syncplay.providers import jellyfin_registry

            manager = SyncPlayManager(
                self.api, self.player, providers=jellyfin_registry(self.api)
            )
            self.syncplay = manager
            handed = state.syncplay_group()
            if handed:
                state.clear_syncplay_group()
                manager.adopt_group(handed)
            self.player.syncplay = manager
            self.remote.syncplay = manager
            # The announce is what tells provider add-ons to (re)register
            # with this service generation — no persistence.
            manager.publish_session_state(announce=True)
            LOG.debug("SyncPlay manager started")
        except Exception:
            LOG.exception("SyncPlay manager failed to start")
            self.syncplay = None

    def _stop_syncplay(self) -> None:
        manager = self.syncplay
        if manager is None:
            return
        self.syncplay = None
        self.player.syncplay = None
        self.remote.syncplay = None
        try:
            # Restarted in place, the service keeps its group for the next
            # generation; stopped for good, it leaves.
            manager.stop(
                leave=not (self._restart_requested and not self.abortRequested())
            )
        except Exception:
            LOG.exception("SyncPlay manager failed to stop")
        # The mirror must not outlive the engine it describes; the ping
        # tells providers the session is gone (or restarting — the next
        # generation's announce follows).
        state.clear_syncsession()
        try:
            contract.publish_state()
        except Exception:
            pass

    def _open_syncplay_menu(self) -> None:
        """SyncPlayMenu IPC: run the (dialog-blocking) menu on a dedicated
        worker thread — never on the notification thread."""
        manager = self.syncplay
        if manager is None:
            # The plugin gates on syncPlayEnabled, so this is the service
            # not (yet) online/built — tell the user rather than nothing.
            toast.show(
                settings.localized(30574), toast.ERROR, heading="SyncPlay", time_ms=4000
            )
            return
        from kofin.syncplay import show_menu

        spawned = spawn_once(
            self._syncplay_menu, show_menu, "kofin-syncplay-menu", manager
        )
        if spawned is None:
            LOG.debug("SyncPlay menu already open")
            return
        self._syncplay_menu = spawned

    def _open_who_is_watching(self) -> None:
        """WhoIsWatching IPC: same contract as the SyncPlay menu — the picker
        blocks on a dialog, so it gets its own worker thread, never the
        notification thread."""
        spawned = spawn_once(
            self._who_is_watching, self._run_who_is_watching, "kofin-whoswatching"
        )
        if spawned is None:
            LOG.debug("who's-watching picker already open")
            return
        self._who_is_watching = spawned

    def _run_who_is_watching(self) -> None:
        from kofin.service import whoswatching

        try:
            whoswatching.show_picker(self.api, self.credentials, modal=self.modal)
        except Exception:
            LOG.exception("who's-watching picker failed")

    def _start_backdrop(self, force: bool = False) -> None:
        """Refresh the addon fanart from the server's splashscreen.

        On its own thread because it downloads an image and nothing waits on
        the result — a backdrop that lands a few seconds into the session is
        indistinguishable from one that was always there.
        """
        if self._stopping.is_set():
            return
        spawned = spawn_once(
            self._backdrop, self._run_backdrop, "kofin-backdrop", force
        )
        if spawned is None:
            LOG.debug("backdrop refresh already running")
            return
        self._backdrop = spawned

    def _run_backdrop(self, force: bool) -> None:
        backdrop.apply(self.api if self._online else None, time.time(), force=force)

    def _start_websocket(self) -> None:
        header = auth.build_auth_header(
            settings.device_name(),
            self.credentials.device_id,
            addon_version(),
            self.credentials.token,
        )
        self.ws = WSClient(
            self.credentials.server_address,
            header,
            on_event=self._on_ws_event,
            on_connected=self._on_ws_connected,
            on_disconnected=self._on_ws_disconnected,
            user_agent=settings.user_agent(),
            on_rejected=self._on_session_rejected,
        )
        self.ws.start()

    def _on_session_rejected(self) -> None:
        """The server answers but refuses this session (a password change, a
        disabled user, the device removed): said once, in a toast that names
        the way back in and in the Library status, while the server itself
        still counts as reachable."""
        if self._session_rejected:
            return
        self._session_rejected = True
        self._connection_toast(30022, level=toast.ERROR)
        try:
            from kofin.sync.backends.api import status as apistatus
            from kofin.sync.backends.api.store import namespace

            apistatus.write(
                settings.localized(30022),
                namespace=namespace(
                    self.credentials.server_id, self.credentials.user_id
                ),
            )
        except Exception:
            LOG.debug("rejected session not recorded in the library status")

    def _connection_toast(
        self, string_id: int, *args: Any, level: str = toast.INFO
    ) -> None:
        """Tell the user the server came, went or is restarting.

        The websocket's edges are coalesced into states on the service tick:
        a drop is stamped (``_down_since``) and announced only once it has
        outlived LOST_TOAST_GRACE_SECONDS, and a connect is announced only
        when ``_announce_next_connect`` says the last thing the user heard was
        bad news — true at start, after a shown loss, and after a restart or
        shutdown notice.

        Losing the connection, and a server restarting or shutting down, carry
        Kodi's warning glyph rather than kofin's icon.

        Nothing in here may raise: it is called first thing from
        ``_on_ws_connected``, which goes on to register capabilities and
        rejoin SyncPlay, and Kodi caches addon strings for the process
        lifetime, so a newly added id renders without its placeholder until
        the next full restart.
        """
        if not settings.get_bool("notifyConnection"):
            return

        try:
            message = settings.localized(string_id)

            if args:
                try:
                    message = message % args
                except TypeError:
                    # No placeholder to fill (uncached id, or a language pack
                    # without this string): show the bare text.
                    pass

            toast.show(message, level, time_ms=4000)
        except Exception as error:  # pragma: no cover - defensive
            LOG.warning("connection notification failed: %s", error)

    def _register_capabilities(self) -> None:
        try:
            self.api.post_capabilities(CAPABILITIES)
            LOG.debug("capabilities registered")
        except JellyfinError as error:
            LOG.warning("capabilities registration failed: %s", error)

    def _on_ws_disconnected(self) -> None:
        # Stamped, not toasted: the service tick announces the loss once the
        # grace has run out with the socket still down (_maybe_announce_lost).
        # The client reports this only for a socket that was actually open,
        # so a connect always sits between two drops and the stamp is never
        # overwritten mid-grace.
        with self._conn_toast_lock:
            self._down_since = time.monotonic()
        # A question for the next tick, not a verdict (see _verify_connection).
        self._verify_online = True

    def _maybe_announce_lost(self) -> None:
        """Announce a drop that has outlived the grace — from the service tick.

        On the one-second loop rather than a timer of its own, so there is
        nothing to cancel: the loop stops with the generation, and a stop
        raised mid-tick is caught by the same guard the transports use. The
        decision and the toast share the lock with the connect callback,
        which is what keeps "Lost" ahead of a "Connected" racing it on the
        websocket thread — the toast only queues, so the lock is held for
        microseconds.
        """
        with self._conn_toast_lock:
            if self._down_since is None:
                return
            down_for = time.monotonic() - self._down_since
            if down_for < LOST_TOAST_GRACE_SECONDS:
                return
            self._down_since = None
            if self._abort_transport():
                return
            if self._announce_next_connect or self._session_rejected:
                # A restart or shutdown notice, or the refused session,
                # already explained this downtime; a second adverse toast
                # would make Restarting, Lost, Connected an edge pair again.
                return
            self._announce_next_connect = True
            # Toasts leave no trace in kodi.log; this line does.
            LOG.debug("websocket down for %.0f s; announcing the loss", down_for)
            self._connection_toast(30416, level=toast.WARNING)

    def _on_ws_connected(self) -> None:
        """Runs on the websocket's own receive loop — toast, spawn, return.

        The post-connect work blocks for seconds (the parked-userdata
        replay, the catch-up enqueue, a deliberate settle wait, capabilities
        registration, the who's-watching restore), and for as long as on_open
        runs nothing is read off the socket — inbound Play/SyncPlay commands
        and pongs stall at exactly the moment the server pushes state at a
        fresh session. So the work moves to a worker; the pending flag makes
        a connect that lands mid-run schedule one more pass rather than pile
        up threads or be skipped — each pass re-reads current state, so the
        last one always serves the live session.
        """
        with self._conn_toast_lock:
            self._down_since = None
            announce = self._announce_next_connect
            self._announce_next_connect = False
            if announce:
                self._connection_toast(30415, self.credentials.server_name or "")
        # A live socket is the best evidence there is, and the websocket
        # reconnects itself — so this is a raising edge in its own right,
        # not only ``_connect``'s.
        self._online = True
        self._verify_online = False
        state.set_online(True)
        self._post_connect_pending.set()
        spawned = spawn_once(
            self._post_connect, self._run_post_connect, "kofin-postconnect"
        )
        if spawned is not None:
            self._post_connect = spawned

    def _run_post_connect(self) -> None:
        monitor = xbmc.Monitor()
        while self._post_connect_pending.is_set() and not monitor.abortRequested():
            self._post_connect_pending.clear()
            connected = time.monotonic()
            # Before the catch-up, deliberately: the replay writes what this
            # device did offline, and the FastSync that follows pulls the
            # server's answer back down. The other order would apply the
            # server's stale view first and then overwrite it, so every
            # replayed item would flicker through the wrong state.
            self._replay_pending_userdata()
            # Ahead of the session's settle: neither the replay nor the
            # catch-up is the socket session's, and the catch-up is all that
            # brings a device that slept what the server gained meanwhile.
            self._catch_up_after_reconnect()
            settle = SESSION_SETTLE_SECONDS - (time.monotonic() - connected)
            # A wait of no whole millisecond is Kodi's spelling of "for ever".
            if settle >= 0.001:
                monitor.waitForAbort(settle)
            self._register_capabilities()
            # Capabilities attach this device's session; re-apply the Who's
            # watching? set the plugin saved, which does not survive a new
            # session (Kodi restart or a reconnect that minted a fresh one).
            self._restore_additional_users()
            if self.syncplay is not None:
                # After any WS drop assume kicked; the manager probes
                # /SyncPlay/List and rejoins on its own thread.
                self.syncplay.on_notification("WebSocketConnected", {})

    def _restore_additional_users(self) -> None:
        """Re-attach saved co-watchers. Contained: must never break connect."""
        try:
            from kofin.service import whoswatching

            whoswatching.restore_additional_users(self.api, self.credentials.device_id)
        except Exception as error:  # pragma: no cover - defensive
            LOG.warning("who's-watching restore failed: %s", error)

    def _replay_pending_userdata(self) -> None:
        """Send what a playback produced while the server was unreachable.

        Contained and bounded: one row at a time, each failure counted so a
        row the server will never accept eventually leaves (pending.py), and
        the whole pass wrapped so a broken replay never costs the connect
        its catch-up.
        """
        try:
            from kofin.downloads import pending
        except Exception:  # pragma: no cover - defensive
            return
        try:
            rows = pending.rows()
        except Exception:
            LOG.exception("could not read the parked userdata")
            return
        if not rows:
            return
        LOG.debug("replaying %d parked userdata change(s)", len(rows))
        for row in rows:
            if self._stopping.is_set() or self.abortRequested():
                return
            try:
                current = (self.api.item(row.jellyfin_id) or {}).get("UserData") or {}
                payload = pending.resolve(row, current)
                if payload:
                    self.api.update_user_data(row.jellyfin_id, payload)
                    LOG.debug("replayed userdata for %s: %s", row.jellyfin_id, payload)
                pending.remove(row.jellyfin_id)
            except HttpError as error:
                if error.status == 404:
                    # The server no longer has the item: nothing to replay,
                    # and the rows behind it must not wait on it.
                    LOG.debug(
                        "parked userdata for %s dropped: the server no longer has it",
                        row.jellyfin_id,
                    )
                    pending.remove(row.jellyfin_id)
                    continue
                attempts = pending.record_attempt(row.jellyfin_id)
                LOG.warning(
                    "userdata replay failed for %s (attempt %d): %s",
                    row.jellyfin_id,
                    attempts,
                    error,
                )
                return  # the server is unwell; the rest keeps for next time
            except JellyfinError as error:
                attempts = pending.record_attempt(row.jellyfin_id)
                LOG.warning(
                    "userdata replay failed for %s (attempt %d): %s",
                    row.jellyfin_id,
                    attempts,
                    error,
                )
                return  # the server is unwell; the rest keeps for next time
            except Exception:
                LOG.exception("userdata replay failed for %s", row.jellyfin_id)
                pending.record_attempt(row.jellyfin_id)

    def _catch_up_after_reconnect(self) -> None:
        """Replay what the library missed while the socket was down.

        LibraryChanged is fire-and-forget: a message sent while the websocket
        is disconnected is gone, and the socket reconnects itself silently.
        The incremental catch-up asks the change feed for everything since the
        sync watermark, which advances only once a drain completes. Skipped
        until the library thread's startup has run.
        """
        library = self.library

        if library is None or not library.startup_done:
            return

        LOG.debug("websocket reconnected; catching up on missed changes")
        library.enqueue_command("Reconnected")

    def _on_ws_event(self, message_type: str, data: dict[str, Any]) -> None:
        if self.remote.handle(message_type, data):
            return

        # Handled ahead of the library events: neither carries a payload the
        # sync cares about.
        if message_type in SERVER_LIFECYCLE_MESSAGES:
            LOG.debug("[ %s ]", message_type)
            with self._conn_toast_lock:
                # An announced restart or shutdown is the downtime notice:
                # the grace-expiry toast stands down, and the reconnect that
                # follows gets its close-out even when the socket heals
                # inside the grace.
                self._announce_next_connect = True
                self._connection_toast(
                    SERVER_LIFECYCLE_MESSAGES[message_type], level=toast.WARNING
                )
            return

        library = self.library
        if library is not None and library.startup_done:
            if message_type == "LibraryChanged":
                LOG.debug("[ LibraryChanged ] %s", log.mask(str(data)))
                library.added(data.get("ItemsAdded") or [])
                library.updated(data.get("ItemsUpdated") or [])
                library.removed(data.get("ItemsRemoved") or [])
                return
            if message_type == "UserDataChanged":
                if not own_userdata(data, self.api.user_id):
                    # A co-watcher's own viewing, not ours. See own_userdata.
                    LOG.debug("[ UserDataChanged ] ignored: another user's")
                    return
                LOG.debug("[ UserDataChanged ] %s", log.mask(str(data)))
                library.userdata(data.get("UserDataList") or [])
                return

        LOG.debug("ws event %s (unhandled)", message_type)

    # -- kodi callbacks --------------------------------------------------------

    def onNotification(self, sender: str, method: str, data: str) -> None:
        """Three tables, one per bus: Kodi's own announcements by method,
        the public provider contract by name, and kofin's IPC by message
        name. A Kodi method not in the table is ignored; an IPC message is
        verified at the door and its secret spent before any handler runs."""
        if self._stopping.is_set():
            # A stopped generation still hears every callback. Kodi
            # unregisters a Monitor only in its destructor, and run_forever
            # dropping the generation does not run it: the settings applier
            # refers back to the service.
            return
        if sender == "xbmc":
            kodi_handler = self._KODI_HANDLERS.get(method)
            if kodi_handler is not None:
                getattr(self, kodi_handler)(data)
            return
        if sender != ipc.SENDER:
            # A third bus: the public provider contract, from any sender.
            name = ipc.method_name(method)
            contract_handler = self._CONTRACT_HANDLERS.get(name)
            if contract_handler is not None:
                payload = contract.decode(name, data)
                if payload is not None:
                    getattr(self, contract_handler)(sender, payload)
            return
        name = ipc.method_name(method)
        payload = ipc.decode(data)
        if not ipc.verify(name, payload, self._ipc_nonce):
            # Kodi passes the sender string through from whoever called
            # NotifyAll, so this is what a forged destructive command looks
            # like: our name, no secret. Logged rather than silent — if it is
            # ever a real kofin message, this line is the only trace.
            LOG.warning("dropped unauthenticated %s", name)
            return
        # Verified, and spent here: the library thread logs every command it
        # dequeues, and the secret must not reach kodi.log.
        payload.pop(ipc.NONCE_KEY, None)
        ipc_handler = self._IPC_HANDLERS.get(name)
        if ipc_handler is None:
            # Registered but matched by no arm, or not registered at all
            # (a message the registry once held, or a forgery that guessed
            # wrong). Nothing happens either way; this line is the only
            # trace that it arrived.
            LOG.debug("unhandled IPC %s", name)
            return
        getattr(self, ipc_handler)(name, payload)

    # -- the Kodi bus, one handler per method ----------------------------------

    def _kodi_screensaver_deactivated(self, data: str) -> None:
        if self.library is not None:
            # Unconditional: the wake catch-up is the only cover for a
            # websocket that went half-open during long idle (a dead
            # socket that never reported closing delivers nothing, and
            # the reconnect catch-up only fires on *detected* drops). An
            # empty catch-up costs one request. The screensaver itself
            # never pauses sync, so there is nothing to "resume" here, only
            # to re-check.
            LOG.debug("screensaver deactivated; catching up")
            self.library.enqueue_command("FastSync")
        # Independent of the sync kick above: a broken manager must never
        # suppress the library catch-up, and vice versa.
        self._syncplay_forward("on_wake")

    def _kodi_wake(self, data: str) -> None:
        self._syncplay_forward("on_wake")

    def _kodi_sleep(self, data: str) -> None:
        self._syncplay_forward("on_sleep")

    def _kodi_player_play(self, data: str) -> None:
        decoded = _decode_kodi_data(data)
        self._syncplay_forward("on_kodi_play", decoded)

    def _kodi_player_stop(self, data: str) -> None:
        if self.downloads is None:
            return
        # Let a pool held back by downloadsPauseDuringPlayback pick up
        # again now rather than at its next poll. Only a nudge — the
        # worker re-reads the gate itself, and its poll is the cover
        # for every stop that never reaches here.
        self.downloads.wake()

    def _kodi_library_update(self, data: str) -> None:
        if not self.credentials.is_logged_in:
            return
        self.kodi_userdata.submit(_decode_kodi_data(data))

    # -- kofin's IPC, one handler per message ----------------------------------

    def _ipc_restart(self, name: str, payload: dict[str, Any]) -> None:
        LOG.debug("restart requested")
        self._restart_requested = True

    def _ipc_auth_changed(self, name: str, payload: dict[str, Any]) -> None:
        LOG.debug("auth changed; restarting service cycle")
        self._restart_requested = True

    def _ipc_syncplay_menu(self, name: str, payload: dict[str, Any]) -> None:
        self._open_syncplay_menu()

    # -- the public provider contract, one handler per message ---------------

    def _contract_register(self, sender: str, payload: dict[str, Any]) -> None:
        self._syncplay_forward("on_provider_register", sender, payload)

    def _contract_claim(self, sender: str, payload: dict[str, Any]) -> None:
        self._syncplay_forward("on_foreign_claim", contract.engine_claim(payload))

    def _contract_propose(self, sender: str, payload: dict[str, Any]) -> None:
        self._syncplay_forward("on_propose", payload)

    def _contract_menu(self, sender: str, payload: dict[str, Any]) -> None:
        self._open_syncplay_menu()

    def _ipc_who_is_watching(self, name: str, payload: dict[str, Any]) -> None:
        self._open_who_is_watching()

    def _ipc_attach_subtitle(self, name: str, payload: dict[str, Any]) -> None:
        try:
            index = int(payload["Index"])
        except (KeyError, TypeError, ValueError):
            LOG.warning("AttachSubtitle without a usable index: %s", payload)
        else:
            self.player.fetch_subtitle(index)

    def _ipc_start_queue(self, name: str, payload: dict[str, Any]) -> None:
        """Start the music queue Play all is building, once it holds the
        tracks the request counts and a moment more: by then the plugin
        script that sent it has ended, and Kodi gives the first track's
        resolve the interpreter it keeps warm (ipc.START_QUEUE).
        Notification thread: the wait is a thread of its own."""
        try:
            count = int(payload.get("Count") or 0)
        except (TypeError, ValueError):
            count = 0
        owner = str(payload.get("Owner") or "")
        LOG.debug("music queue start asked for %d track(s)", count)
        starter = threading.Thread(
            target=self._start_queue, args=(count, owner), name="kofin-queue-start"
        )
        starter.daemon = True
        starter.start()

    def _start_queue(self, count: int = 0, owner: str = "") -> None:
        """Start the queue once it is full, unless a newer Play all has taken
        it: that one's own request starts it, and a start from here, up to
        QUEUE_FILL_TIMEOUT late, would open its position 0 a second time."""

        def superseded() -> bool:
            return bool(owner) and not state.owns_queue(owner)

        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        deadline = time.monotonic() + QUEUE_FILL_TIMEOUT
        while playlist.size() < count and time.monotonic() < deadline:
            if self._stopping.wait(0.05) or superseded():
                return
        if self._stopping.wait(QUEUE_START_DELAY) or superseded():
            return
        started = kodirpc.call(
            "Player.Open", {"item": {"playlistid": xbmc.PLAYLIST_MUSIC, "position": 0}}
        )
        if started is None or started is kodirpc.FAILED:
            LOG.warning("the music queue was not started: Kodi refused Player.Open")
        else:
            LOG.debug("music queue started")

    def _downloads_for(self, name: str) -> Optional[DownloadsPort]:
        """The download manager a download command goes to, started on
        demand. Notification thread: the manager's surface only enqueues
        onto its ops queue — no database, no socket."""
        self._start_downloads()
        if self.downloads is None:
            LOG.warning("download command %s ignored: manager not running", name)
        return self.downloads

    def _ipc_download_add(self, name: str, payload: dict[str, Any]) -> None:
        downloads = self._downloads_for(name)
        if downloads is None:
            return
        from kofin.downloads import wire

        request = wire.parse_add(payload)
        downloads.submit(
            request.ids,
            origin=request.origin,
            media_types=request.media_types,
            request_id=request.request_id,
            request_name=request.request_name,
        )

    def _ipc_download_cancel(self, name: str, payload: dict[str, Any]) -> None:
        downloads = self._downloads_for(name)
        if downloads is not None:
            from kofin.downloads import wire

            downloads.cancel(wire.item_id(payload))

    def _ipc_download_remove(self, name: str, payload: dict[str, Any]) -> None:
        downloads = self._downloads_for(name)
        if downloads is not None:
            from kofin.downloads import wire

            downloads.remove(
                wire.item_ids(payload), subscription=payload.get("Subscription") is True
            )

    def _ipc_download_remove_all(self, name: str, payload: dict[str, Any]) -> None:
        downloads = self._downloads_for(name)
        if downloads is not None:
            downloads.remove_all()

    def _ipc_library_command(self, name: str, payload: dict[str, Any]) -> None:
        self._start_library()
        if self.library is None:
            if name == ipc.SYNC_PLAYLISTS:
                # Nothing synced, so no library thread: the download orders
                # are the download manager's to bring up to date.
                downloads = self._downloads_for(name)
                if downloads is not None:
                    downloads.reconcile_subscriptions(str(payload.get("Id") or ""))
                return
            LOG.warning("library command %s ignored: manager not running", name)
            return
        self.library.enqueue_command(name, payload)

    def _syncplay_forward(self, name: str, *args: Any) -> None:
        forward(self.syncplay, name, *args)

    def onSettingsChanged(self) -> None:
        if self._stopping.is_set():
            return  # a stopped generation; see onNotification
        self.settings_apply.apply()

    # -- teardown ---------------------------------------------------------------

    def _superseded(self) -> bool:
        """Whether a newer service generation has taken over the shared state.

        Kodi does not wait for a stopping service script to exit before
        starting its replacement, and everything in ``core.state`` is one set
        of window properties with no room for a generation, so a teardown
        that writes them while the successor runs writes over the *live*
        service's. Every generation mints an IPC nonce at startup
        (``ipc.rotate_nonce``), so a value on disk that is not ours means a
        successor exists and the shared state is its. Our own threads stop
        regardless: the ``_stopping`` Event and ``Library.stop_client`` are
        instance-scoped.
        """
        current = ipc.nonce()
        return bool(current) and current != self._ipc_nonce

    @contextmanager
    def modal(self, kind: str) -> Iterator[None]:
        """A dialog of ours is open while the block runs. The caller reads
        ``_stopping`` after the dialog returns: an answer that arrived once
        the service stopped is Kodi closing the dialog, not the viewer."""
        with self._dialogs_lock:
            self._dialogs[kind] = self._dialogs.get(kind, 0) + 1
        try:
            yield
        finally:
            with self._dialogs_lock:
                left = self._dialogs.get(kind, 1) - 1
                if left > 0:
                    self._dialogs[kind] = left
                else:
                    self._dialogs.pop(kind, None)

    def _close_dialogs(self) -> None:
        with self._dialogs_lock:
            kinds = list(self._dialogs)
        for kind in kinds:
            LOG.debug("closing the open %s at shutdown", kind)
            xbmc.executebuiltin("Dialog.Close(%s,true)" % kind)

    def _shutdown(self) -> None:
        # The Event is what this generation's HTTP transports check between
        # retries, and what every start method and dialog worker reads: no
        # work starts once it is set.
        self._stopping.set()
        self._close_dialogs()
        self._stop_syncplay()
        # The websocket goes down before the library, not after: every event
        # it dispatches lands in the Library's queues — or, for UserDataChanged,
        # opens the kofin database — on the websocket thread. SyncPlay is
        # stopped above because it is the only other websocket consumer.
        if self.ws is not None:
            self.ws.stop()
            self.ws = None
        self._stop_downloads()
        if self.library is not None:
            self.library.stop_client()
            self._join_library()
            self.library = None
        self.player.stop_threads()
        self.kodi_userdata.stop()
        self._join_workers()
        self.http.close()
        # Last, once nothing of ours is still running. Re-asked rather than
        # reused from the top of the teardown: the join above can take
        # LIBRARY_JOIN_SECONDS, which is ample time for the successor to have
        # started, and by here the properties would be its.
        if self._superseded():
            LOG.debug("a newer service generation is live; leaving it its state")
            return
        state.clear_all()

    def _join_library(self) -> bool:
        """Wait for the library thread to die; True when it did.

        A deadline generous enough for a page fetch, and a truthful answer
        when it passes.

        A wait that goes long also dumps every thread's stack (core/diag.py):
        the first slow tick and the last one are both written down, so the log
        says what the thread was doing and whether it moved between the two.
        """
        library = self.library
        if library is None:
            return True
        waited = 0.0
        dumped = False
        first: dict[int, str] = {}
        while library.is_alive() and waited < LIBRARY_JOIN_SECONDS:
            library.join(timeout=5)
            if not library.is_alive():
                return True
            waited += 5
            if not dumped:
                dumped = True
                first = diag.thread_dump("library thread still stopping after 5s")
            else:
                LOG.warning(
                    "library thread still stopping after %.0fs: %s",
                    waited,
                    diag.positions().get(library.ident or -1, "gone"),
                )
            if self.abortRequested():
                LOG.warning("abort during teardown; library thread still alive")
                return False
        if library.is_alive():
            last = diag.thread_dump("library thread outlived the deadline")
            LOG.error(
                "library thread outlived %.0fs (%s)",
                LIBRARY_JOIN_SECONDS,
                diag.describe_movement(library.ident, first, last),
            )
            return False
        return True

    def _join_workers(self) -> None:
        """Join the named one-shot workers this service started.

        Unjoined, they outlive the rebuild and race their replacements against
        the same resources — the backdrop worker rewrites a file in the profile.
        """
        workers = (
            ("backdrop", self._backdrop),
            ("post-connect", self._post_connect),
            ("syncplay menu", self._syncplay_menu),
            ("who's watching", self._who_is_watching),
        )
        for name, worker in workers:
            if worker is None or not worker.is_alive():
                continue
            worker.join(timeout=10)
            if worker.is_alive():  # pragma: no cover - watchdog logging only
                # The dialogs are the expected case: both block on user input
                # and Kodi closes them when the addon goes.
                LOG.warning("%s worker did not stop within its deadline", name)


def _guid(value: Any) -> str:
    """Jellyfin ids compare dashless and case-insensitively."""
    return str(value or "").replace("-", "").lower()


def own_userdata(data: dict[str, Any], user_id: str) -> bool:
    """Whether a UserDataChanged payload is about the user this client mirrors.

    Jellyfin delivers UserDataChanged to every session that *contains* the
    subject user, and a session contains its additional users as well as its
    owner (``SessionInfo.ContainsUser``), so attaching a co-watcher subscribes
    this device to everything they watch **anywhere**. Nothing they do
    elsewhere belongs in this library.

    An unstated subject is treated as ours: the field is Jellyfin's to send,
    and dropping messages without it would silently stop userdata sync
    against any server that omits it.
    """
    subject = _guid(data.get("UserId"))
    return not subject or subject == _guid(user_id)


def _decode_kodi_data(data: str) -> dict[str, Any]:
    """Kodi-bus notification payloads are plain JSON objects."""
    try:
        payload = json.loads(data) if data else {}
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def run_forever() -> None:
    while True:
        service = Service()
        if not service.run():
            break
        del service
