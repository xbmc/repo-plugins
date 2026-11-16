"""The settings diff engine: a registry of ``setting id -> handler(old, new)``
consulted from the service's ``onSettingsChanged``.

The table (``SettingsApplier.handlers``) holds one handler per setting whose
change the running service has to act on; everything not in the table is read
fresh wherever it is used. The whitelist handler computes add/remove sets
against the *synced* whitelist (sync.json), not the previous csv, so a
partially failed sync self-heals on the next apply.

Kodi fires ``onSettingsChanged`` while it loads the profile settings, and the
fresh-``Addon()``-per-call reads (needed for reuselanguageinvoker correctness)
can transiently return "" before the persisted value lands. So the applier
ignores every change until the service marks it ready, then re-baselines
against the settled store.

The same read can fail *after* ready, so emptying a guarded setting is
corroborated before it is believed (``_is_spurious_clear``).
"""

import threading
from typing import Callable, Optional

import xbmcgui

from kofin.core import settings, state
from kofin.core.log import Logger
from kofin.service.ports import LibraryPort, ServiceHooks, spawn_once

LOG = Logger(__name__)

Handler = Callable[[str, str], None]

# Settings whose emptied value destroys data if believed too readily, so an
# empty read is corroborated before it is acted on (``_is_spurious_clear``).
# ``libraryNodes`` is the switch for the managed playlist files and the node
# tree.
GUARDED_CLEARS = ("librarySelection", "syncMusicPlaylists", "libraryNodes")

# Non-empty for the whole life of an installed addon: Credentials.load
# generates it on first use and logging out deliberately keeps it. So an empty
# read of it never means "the user changed something" — it means the settings
# document did not load.
LOAD_CANARY = "deviceId"


class SettingsApplier:
    def __init__(self, service: ServiceHooks) -> None:
        self.service = service
        self.ready = False
        self.handlers: dict[str, Handler] = {
            "librarySelection": self._library_selection_changed,
            "syncPlayEnabled": self._syncplay_enabled_changed,
            "syncPlayTempo": self._syncplay_tempo_changed,
            "whoIsWatchingShortlist": self._who_shortlist_changed,
            "contextBitrates": self._context_bitrates_changed,
            "libraryNodes": self._library_nodes_changed,
            "useServerBackdrop": self._server_backdrop_changed,
            "downloadsEnabled": self._downloads_enabled_changed,
            "downloadsPath": self._downloads_path_changed,
        }
        self.snapshot: dict[str, str] = self._read_all()
        # The one-shot worker a library removal's confirmation runs on; its
        # slot, so a second save while the dialog is up is refused rather
        # than doubled (see _library_selection_changed).
        self._removal_worker: Optional[threading.Thread] = None

    def _read_all(self) -> dict[str, str]:
        return {
            setting_id: settings.get_str(setting_id) for setting_id in self.handlers
        }

    def mark_ready(self) -> None:
        """Start honoring settings changes, re-baselining against the settings
        store now that startup's transient reads are over. Idempotent."""
        if self.ready:
            return
        self.snapshot = self._read_all()
        self.ready = True
        # Publish rather than wait for a change: the plugin process reads this
        # property on every context-menu draw, including the first.
        state.set_context_bitrates(self.snapshot.get("contextBitrates", ""))
        # Same reason: skins cannot read the settings that hide these two
        # root entries, so the service mirrors the offer onto properties.
        self._publish_root_menus()
        LOG.debug("settings applier ready; baseline re-read")

    def apply(self) -> None:
        """Run the handler for every watched setting whose value changed."""
        if not self.ready:
            LOG.debug("settings change before ready; ignored")
            return
        # A whole-document load failure blanks every setting (or, for booleans
        # with a default of false, surfaces the default). If the canary is
        # empty, trust nothing this cycle.
        if settings.get_str(LOAD_CANARY) == "":
            LOG.warning(
                "settings document failed to load (%s empty); skipping apply cycle",
                LOAD_CANARY,
            )
            return
        for setting_id, handler in self.handlers.items():
            new = settings.get_str(setting_id)
            old = self.snapshot.get(setting_id, "")
            if new == old:
                continue
            if self._is_spurious_clear(setting_id, old, new):
                # Snapshot deliberately not advanced: the real value is still
                # pending, and a later genuine edit must still register.
                continue
            self.snapshot[setting_id] = new
            LOG.debug("setting %s changed: %r -> %r; applying", setting_id, old, new)
            try:
                handler(old, new)
            except Exception:
                LOG.exception("apply failed for %s", setting_id)

    def _is_spurious_clear(self, setting_id: str, old: str, new: str) -> bool:
        """Whether an emptied setting is a failed read rather than an edit.

        Kodi can fail to load settings.xml mid-session and hand back "" for a
        setting that is intact on disk. The failure comes in bursts, so a
        re-read that agrees is not proof; a failed load empties *every*
        setting, so a ``deviceId`` that reads empty is. Both checks are single
        reads, so a genuine clear still proceeds without waiting on anything.
        """
        if setting_id not in GUARDED_CLEARS or new != "" or old == "":
            return False

        confirm = settings.get_str(setting_id)
        if confirm != new:
            LOG.warning(
                "ignoring spurious empty read of %s (re-read returned %r); "
                "treating it as a failed settings load, not a user edit",
                setting_id,
                confirm,
            )
            return True

        if settings.get_str(LOAD_CANARY) == "":
            LOG.warning(
                "ignoring empty read of %s: %s came back empty too, so the "
                "settings document failed to load rather than %s being cleared",
                setting_id,
                LOAD_CANARY,
                setting_id,
            )
            return True

        return False

    # -- handlers -------------------------------------------------------------

    def _syncplay_enabled_changed(self, old: str, new: str) -> None:
        """The SyncPlay master toggle builds/tears down the manager live —
        off means no manager thread at all."""
        service = self.service
        if new == "true":
            if service._online:
                service._start_syncplay()
        else:
            service._stop_syncplay()
        self._publish_root_menus()

    def _syncplay_tempo_changed(self, old: str, new: str) -> None:
        """Fine sync arms at group join; a toggle while in a group takes
        effect now rather than at the next join."""
        manager = self.service.syncplay
        if manager is not None:
            manager.refresh_tempo_session()

    def _who_shortlist_changed(self, old: str, new: str) -> None:
        """The Advanced-tab shortlist is also how Who's watching? is
        switched off (the nobody sentinel). Republish so a skin button
        tracks the root entry without waiting for a service restart."""
        self._publish_root_menus()

    def _publish_root_menus(self) -> None:
        """Mirror addon-root Who's watching? / SyncPlay visibility for skins.

        Same gates as ``plugin.browse.root``: logged in, and the feature's
        own offer function. Written rather than derived in the skin because
        a ``<visible>`` cannot read an addon setting (core/state.py).
        """
        from kofin.core.settings import Credentials
        from kofin.service import whoswatching
        from kofin.syncplay import offer

        logged_in = Credentials.load().is_logged_in
        state.set_menu_who(logged_in and whoswatching.is_enabled())
        state.set_menu_syncplay(logged_in and offer.available())

    def _context_bitrates_changed(self, old: str, new: str) -> None:
        """Keep the property addon.xml gates the transcode context item on."""
        state.set_context_bitrates(new)

    def _confirmed_off(self, setting_id: str) -> bool:
        """Whether a boolean read as off was really switched off.

        The off direction of these settings is destructive (it deletes the
        managed playlists). A failed settings load can surface the boolean
        default ("false") while the document is mid-rewrite after
        setSettingBool — corroborate before wiping, and leave the snapshot on
        so a real off after recovery still applies.
        """
        confirm = settings.get_str(setting_id)
        # Only an explicit "false" is off: an empty read is a document that
        # did not load, whatever the canary says this time round.
        if settings.get_str(LOAD_CANARY) == "" or confirm != "false":
            LOG.warning(
                "ignoring unconfirmed %s off "
                "(confirm=%r, canary empty=%s); leaving managed files",
                setting_id,
                confirm,
                settings.get_str(LOAD_CANARY) == "",
            )
            self.snapshot[setting_id] = "true"
            return False
        return True

    def _library_nodes_changed(self, old: str, new: str) -> None:
        """The presentation switch (``sync/dynamic.py``).

        On: the node tree and the smart playlists are written now and the
        Jellyfin playlists at the next pass. Off: the managed playlists go
        through the library thread and the tree with the republish; a
        toggle that lands while the server is away is caught up by the
        publish that follows the next enumeration.
        """
        library = self._library_manager()
        if new == "true":
            if library is not None:
                library.enqueue_command("SyncMusicPlaylists")
            self._regenerate_nodes()
            return
        if not self._confirmed_off("libraryNodes"):
            return
        if library is not None:
            library.enqueue_command("CleanupMusicPlaylists")
        self._regenerate_nodes()

    def _server_backdrop_changed(self, old: str, new: str) -> None:
        """Swap the addon fanart now rather than at the next connect."""
        service = self.service
        service._start_backdrop(force=True)

    def _downloads_enabled_changed(self, old: str, new: str) -> None:
        """The downloads master toggle builds/tears down the manager live,
        the same shape as SyncPlay's."""
        service = self.service
        if new == "true":
            if service._online:
                service._start_downloads()
            from kofin.downloads import subscriptions

            if subscriptions.subscribed(
                subscriptions.LIBRARY_SETTING
            ) or subscriptions.subscribed(subscriptions.PLAYLIST_SETTING):
                library = self._library_manager()
                if library is not None:
                    library.enqueue_command("SyncMusicPlaylists")
        else:
            service._stop_downloads()
        self._regenerate_nodes()

    def _regenerate_nodes(self) -> None:
        """Rewrite the generated library nodes now.

        The Downloaded nodes exist only while the feature is on. Contained: a
        node write must never take a settings apply down with it, and nothing
        is asked of a server that is not there.
        """
        try:
            from kofin.sync.dynamic import publish_from

            service = self.service
            api = getattr(service, "api", None)
            if api is not None and getattr(service, "_online", False):
                publish_from(api)
        except Exception:
            LOG.exception("node regeneration after a settings change failed")

    def _downloads_path_changed(self, old: str, new: str) -> None:
        """Write-probe the new root now, not at the first download.

        The probe is the whole apply: existing downloads stay where they are,
        and the manager reads the setting per download, so nothing needs a
        restart.
        """
        import os

        from kofin.downloads import downloads_root

        root = downloads_root()
        probe = os.path.join(root, ".kofin-write-probe")
        try:
            os.makedirs(root, exist_ok=True)
            with open(probe, "w") as handle:
                handle.write("probe")
            os.remove(probe)
        except OSError as error:
            LOG.warning("downloads path %r is not writable: %s", root, error)
            xbmcgui.Dialog().notification(
                "Kofin", settings.localized(30717), xbmcgui.NOTIFICATION_WARNING, 5000
            )
            return

        # The generated nodes name the root, so they are as stale as the
        # downloads were.
        self._regenerate_nodes()

    def _library_selection_changed(self, old: str, new: str) -> None:
        """The apply-on-save path for the library multiselect."""
        from kofin.sync import private as sync_db

        selection = {part for part in new.split(",") if part}

        sync = sync_db.get_sync()
        whitelist_entries = sync["Whitelist"]
        synced_ids = {entry.replace("Mixed:", "") for entry in whitelist_entries}

        additions = sorted(selection - synced_ids)
        removal_entries = [
            entry
            for entry in whitelist_entries
            if entry.replace("Mixed:", "") not in selection
        ]

        if not additions and not removal_entries:
            return

        if removal_entries:
            # Confirmed on a worker: this handler runs inside
            # Service.onSettingsChanged, on the service main thread, where a
            # modal would hold the run loop and every kofin player and monitor
            # callback until answered. A second save while the dialog is up is
            # refused with a log line.
            def confirm_and_dispatch() -> None:
                confirmed = self._confirm_removals(removal_entries, selection)
                if self.service._stopping.is_set():
                    return
                self._dispatch_selection(confirmed, additions)

            worker = spawn_once(
                self._removal_worker, confirm_and_dispatch, "kofin-library-removal"
            )
            if worker is None:
                LOG.debug("a library removal is already awaiting confirmation")
                return
            self._removal_worker = worker
            return

        self._dispatch_selection([], additions)

    def join_removal(self, timeout: float = 5.0) -> None:
        """Wait for a removal confirmation still in progress (tests, teardown)."""
        worker = self._removal_worker
        if worker is not None:
            worker.join(timeout)

    def _dispatch_selection(
        self, removal_entries: list[str], additions: list[str]
    ) -> None:
        library = self._library_manager()
        if library is None:
            LOG.warning("library selection changed but sync manager unavailable")
            return

        if removal_entries:
            library.enqueue_command("RemoveLibrary", {"Id": ",".join(removal_entries)})

        if additions:
            library.enqueue_command("SyncLibrary", {"Id": ",".join(additions)})

    # -- plumbing -------------------------------------------------------------

    def _library_manager(self) -> Optional[LibraryPort]:
        service = self.service
        service._start_library()
        return service.library

    def _confirm_removals(
        self, removal_entries: list[str], selection: set
    ) -> list[str]:
        """Yes/no gate before rows are deleted; declined removals go back
        into librarySelection so the stored intent matches reality."""
        from kofin.sync import private as sync_db
        from kofin.sync import kofindb

        names = []
        with sync_db.Database("kofin") as opened:
            db = kofindb.JellyfinDatabase(opened.cursor)
            for entry in removal_entries:
                view = db.get_view(entry.replace("Mixed:", ""))
                names.append(view.name if view else entry)

        with self.service.modal("yesnodialog"):
            confirmed = xbmcgui.Dialog().yesno(
                settings.localized(30264),
                settings.localized(30265) % ", ".join(names),
            )
        if self.service._stopping.is_set():
            # Kodi closed the dialog for a service that has stopped: not an
            # answer, and nothing starts work for a generation that is gone.
            LOG.debug("library removal confirmation dropped: the service stopped")
            return []
        if confirmed:
            return removal_entries

        restored = sorted(
            selection | {entry.replace("Mixed:", "") for entry in removal_entries}
        )
        restored_csv = ",".join(restored)
        self.snapshot["librarySelection"] = restored_csv
        settings.set_str("librarySelection", restored_csv)
        LOG.debug("library removal declined; selection restored")
        return []
