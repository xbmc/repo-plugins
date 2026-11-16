"""The service-side download manager.

A worker pool draining the kofin.db queue oldest-first: fetch to ``.part``
over :meth:`Api.download_stream`, verify the size, pull the external
subtitle sidecars, rename, hand to the pass, refresh. Owned by the service
the way the library manager is — built when enabled, degrade-don't-die,
stopped in ``_shutdown`` with bounded joins — and fed by the guarded download
IPC messages, whose handlers run on Kodi's notification thread and therefore
only enqueue here (the ops queue) rather than touch a database or a socket.

Stop discipline: the transport abort predicate bounds retries, a per-chunk
check bounds a live body (``StreamedResponse.chunks`` hears the service's
stop, and ``_write_body`` the manager's own, which the transport cannot), and
the read timeout bounds a dead one — so a stop request is honored within one
chunk plus one read timeout, never a file's worth of transfer. A download a
stop interrupts stays ``active`` and is re-queued by ``recover_interrupted``
at the next start, resuming originals from ``bytes_done`` with a Range.
"""

import os
import posixpath
import threading
import time
from queue import Empty, Queue
from typing import (
    Any,
    Callable,
    NamedTuple,
    Optional,
)
from collections.abc import Iterable

import xbmc

from kofin.core import settings, state, toast
from kofin.core.http import (
    JellyfinError,
    ServerUnreachable,
    StreamedResponse,
    Unauthorized,
)
from kofin.core.log import Logger
from kofin.downloads import (
    downloads_root,
    export,
    files,
    nativeport,
    notify_allowed,
    probe,
    progress,
    quality,
    store,
    subscriptions,
)

LOG = Logger(__name__)

JsonDict = dict[str, Any]

MEDIA_TYPE_BY_DTO = {"Movie": "movie", "Episode": "episode", "Audio": "song"}

# In addon_data: the folder the done rows were downloaded to (_root_in_hand).
ROOT_MEMORY = "downloads-root"

# What each worker pool claims. "" is the unknown kind — a row queued by a
# release that did not carry the type, or by a sender that had no DTO — and
# it belongs to the video pool, whose pacing already assumes an item might
# be a two-hour film.
VIDEO_KINDS = store.VIDEO_MEDIA_TYPES + ("",)
MUSIC_KINDS = ("song",)

# Per-item attempts before the row settles as failed. The store keeps
# bytes_done across the requeues, so original attempts resume with a Range.
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = 5.0

# How long an idle worker sleeps between queue polls when nothing wakes it.
IDLE_POLL_SECONDS = 30.0

# Same, while the server is unreachable: shorter, because nothing wakes a
# worker when the connection comes back — the service raises the online flag
# and this is what notices.
OFFLINE_POLL_SECONDS = 10.0

# Same again, while playback holds the pool back. Short because it is the
# floor on how long the queue stays idle after the credits: the service also
# wakes the pool on Player.OnStop, and this is the cover for the stop it
# never sees (a foreign player, a crash, a claim that never happened).
PLAYBACK_POLL_SECONDS = 5.0

# One join per worker at stop: a chunk-loop abort plus one full read timeout,
# with a little grace (core.http.DEFAULT_TIMEOUT read budget is 30 s).
JOIN_SECONDS = 35.0

# How often the maintenance thread sweeps watched auto-origin downloads.
# Kodi marks played at ~90%, so "promptly after the credits" needs no better
# than minutes.
RETENTION_SWEEP_SECONDS = 300.0

# The stale sweep's unit and its fallback: the setting is in days, and unset
# reads as the slider's default.
SECONDS_PER_DAY = 86400.0
STALE_DAYS_DEFAULT = 30

# Store progress roughly every 8 MiB rather than every chunk.
PROGRESS_EVERY_CHUNKS = 32

# A body is synced to storage every SYNC_BYTES and its pages dropped from the
# cache behind it. After a sync that took longer than its window took to
# arrive, the worker rests as long as the sync took, at most
# SYNC_REST_SECONDS.
SYNC_BYTES = 8 * 1024 * 1024
SYNC_REST_SECONDS = 2.0

# The longest a finished download waits to become visible while the pool is
# still busy. Short enough that a long album shows its first tracks well
# before the last one lands; long enough that a burst of tracks refreshes
# once rather than per track.
REFRESH_MAX_DEFER_SECONDS = 20.0

# ffmpeg-style codec -> sidecar extension, where they differ. Anything not
# listed uses the codec name itself, which is right for ass/ssa/vtt/sup.
SUBTITLE_EXTENSIONS = {"subrip": "srt", "webvtt": "vtt"}


class _Cancelled(Exception):
    """The item was cancelled mid-transfer (never an error)."""


class _Op(NamedTuple):
    """One item on the ops queue, applied by whichever worker drains it."""

    op: str
    item_id: str = ""
    origin: str = ""
    media_type: str = ""
    request_id: str = ""
    request_name: str = ""


def worker_count() -> int:
    configured = settings.get_int("downloadsMaxParallel")
    return max(1, min(4, configured or 2))


def music_worker_count() -> int:
    configured = settings.get_int("downloadsMusicParallel")
    return max(1, min(10, configured or 5))


class DownloadManager:
    def __init__(
        self,
        api_factory: Callable[[], Any],
        refresh: Callable[[list[str]], None],
        stopping: "threading.Event",
        native: Optional[nativeport.Native] = None,
    ) -> None:
        self._api_factory = api_factory
        self._refresh = refresh
        # What the Kodi library says about a download (downloads/nativeport.py).
        self.native: nativeport.Native = native or nativeport.for_build()
        # The service generation's own event (never state.should_stop —
        # the successor lowers that on its way up; see service/main.py).
        self._stopping = stopping
        self._stop = threading.Event()
        # One wake Event per worker: a shared one is cleared by whichever
        # worker wakes first, perhaps one that cannot claim the row. A set
        # between claim and wait is kept, where a Condition's notify_all
        # would drop it.
        self._wakes: list[threading.Event] = []
        self._wakes_lock = threading.Lock()
        self._ops: Queue[_Op] = Queue()
        self._cancels: set = set()
        self._cancels_lock = threading.Lock()
        self._attempts: dict[str, int] = {}
        self._workers: list[threading.Thread] = []
        self._reconciler: Optional[threading.Thread] = None
        # Which Kodi databases a finished download has made stale, and since
        # when. Coalesced rather than refreshed per item — see _mark_dirty.
        self._dirty: set[str] = set()
        self._playlist_dirty: set[str] = set()
        self._dirty_since = 0.0
        self._dirty_lock = threading.Lock()
        # The remembered folder (_remembered_root) and the claim of a new one
        # are read and moved under this lock, by the workers and the sweep.
        self._root_lock = threading.Lock()
        self._root_memory: Optional[str] = None  # None: not read yet
        # Held while a worker decides and records a target (_decide_target).
        self._target_lock = threading.Lock()
        # The network location last refused as the downloads folder.
        self._refused_root = ""
        # The Downloaded-music view is written once per generation, not once
        # per track (see _ensure_music_view).
        self._music_view_written = False
        # Requests and albums whose completion has already been announced.
        self._announced: set[str] = set()
        self._announce_lock = threading.Lock()
        # Downloads deleted since the last announcement (see _flush_removed).
        self._removed: list[str] = []
        self._removed_lock = threading.Lock()
        # One *video* transcode pull at a time: the encoder runs unthrottled,
        # so two parallel pulls would saturate the server. Originals keep the
        # full pool.
        #
        # Music's slot is as wide as its pool, so it never blocks; it stays a
        # semaphore so both paths share one shape.
        self._transcode_slot = threading.Semaphore(1)
        self._music_transcode_slot = threading.Semaphore(music_worker_count())
        # The aggregate bar on Kodi's library-update surface.
        self._progress = progress.Reporter(self._should_stop)

    # -- lifecycle -----------------------------------------------------------

    def _new_wake(self) -> "threading.Event":
        """A worker's own wake Event, registered so _wake_all reaches it."""
        event = threading.Event()
        with self._wakes_lock:
            self._wakes.append(event)
        return event

    def _wake_all(self, skip: Optional["threading.Event"] = None) -> None:
        with self._wakes_lock:
            for event in self._wakes:
                if event is not skip:
                    event.set()

    def start(self) -> None:
        # No wake needed for what recover_interrupted requeued: every worker
        # runs the loop body — drain, then claim — before it ever waits.
        store.recover_interrupted()
        self._reconciler = threading.Thread(
            target=self._run_maintenance,
            name="kofin-downloads-maintenance",
            daemon=True,
        )
        self._reconciler.start()
        # Two pools, one queue. The kinds a pool claims keep an album from
        # sitting behind a film.
        for index in range(worker_count()):
            self._spawn_worker("kofin-downloads-%d" % index, VIDEO_KINDS)
        for index in range(music_worker_count()):
            self._spawn_worker("kofin-downloads-music-%d" % index, MUSIC_KINDS)
        LOG.debug("download manager started (%d worker(s))", len(self._workers))

    def _spawn_worker(self, name: str, kinds: tuple[str, ...]) -> None:
        worker = threading.Thread(
            target=self._run_worker,
            args=(kinds, self._new_wake()),
            name=name,
            daemon=True,
        )
        worker.start()
        self._workers.append(worker)

    def stop(self) -> None:
        self._stop.set()
        self._wake_all()
        for worker in [self._reconciler] + self._workers:
            if worker is None or not worker.is_alive():
                continue
            worker.join(timeout=JOIN_SECONDS)
            if worker.is_alive():  # pragma: no cover - watchdog logging only
                LOG.warning("%s did not stop within its deadline", worker.name)
        # After the joins, so no worker races the close; unconditional, so
        # no bar ghosts in the corner past the manager that drew it.
        self._progress.close()
        LOG.debug("download manager stopped")

    def _should_stop(self) -> bool:
        return self._stop.is_set() or self._stopping.is_set()

    # -- the IPC surface (notification thread: enqueue only) -------------------

    def submit(
        self,
        item_ids: list[str],
        origin: str = store.ORIGIN_USER,
        media_types: Optional[list[str]] = None,
        request_id: str = "",
        request_name: str = "",
    ) -> None:
        """Queue ids, optionally with each one's Jellyfin DTO type.

        The type is what lets a row be claimed by the right worker pool
        before anything has been fetched for it. Unknown is fine and stays
        unknown until ``record_details`` learns it the slow way.

        ``request_id``/``request_name`` name the item the user selected,
        and ride onto every row this call creates so the
        completion toast can answer the request rather than each item
        (``_announce_complete``).
        """
        kinds = media_types or []
        for index, item_id in enumerate(item_ids):
            if not item_id:
                continue
            kind = MEDIA_TYPE_BY_DTO.get(kinds[index] if index < len(kinds) else "", "")
            self._ops.put(
                _Op("add", str(item_id), origin, kind, request_id, request_name)
            )
        self._wake_all()

    def cancel(self, item_id: str) -> None:
        with self._cancels_lock:
            self._cancels.add(item_id)
        self._ops.put(_Op("cancel", item_id))
        self._wake_all()

    def remove(self, item_ids: list[str], subscription: bool = False) -> None:
        """Delete finished downloads.

        One op for the lot; Jellyfin ids are hex, so the comma joining them
        cannot appear in one.
        """
        wanted = [item_id for item_id in item_ids if item_id]
        if not wanted:
            return
        self._ops.put(
            _Op("remove", ",".join(wanted), "subscription" if subscription else "")
        )
        self._wake_all()

    def reconcile_subscriptions(self, playlist_id: str = "") -> None:
        """Bring the standing download orders to the server's listing from
        here, for a service that runs no library thread (nothing synced)."""
        self._ops.put(_Op("subscriptions", playlist_id))
        self._wake_all()

    def remove_all(self) -> None:
        """The settings button: every download, finished or not.

        One op rather than one per row — the store is read on the worker
        side, where the walk is already serialized, and a NotifyAll per row
        would put a whole library's worth of messages through Kodi's
        notification bus for a single button press.
        """
        self._ops.put(_Op("removeall"))
        self._wake_all()

    def _cancelled(self, item_id: str) -> bool:
        with self._cancels_lock:
            return item_id in self._cancels

    def _clear_cancel(self, item_id: str) -> None:
        with self._cancels_lock:
            self._cancels.discard(item_id)

    # -- workers ---------------------------------------------------------------

    def _run_worker(
        self,
        kinds: tuple[str, ...] = VIDEO_KINDS,
        wake: Optional["threading.Event"] = None,
    ) -> None:
        # Own Event, never the pool's (see _wakes). Defaulted so a test can
        # drive one pass of this loop without standing a worker up.
        wake = self._new_wake() if wake is None else wake
        api = self._api_factory()
        try:
            while not self._should_stop():
                self._drain_ops(own=wake)
                if state.is_offline():
                    # Hold the queue rather than burn it: every claim while
                    # the server is gone would fail its attempts and settle.
                    # Ops still drain above, so a cancel or a remove works
                    # offline.
                    self._progress.idle()
                    if wake.wait(timeout=OFFLINE_POLL_SECONDS):
                        wake.clear()
                    continue
                if self._paused_for_playback():
                    # The gate is on claiming only: a transfer already
                    # running finishes, and ops still drain above.
                    self._progress.idle()
                    if wake.wait(timeout=PLAYBACK_POLL_SECONDS):
                        wake.clear()
                    continue
                row = store.claim(kinds)
                if row is None:
                    if not self._ops.empty():
                        # Ops arrived while this worker was claiming: never
                        # sleep on a non-empty queue.
                        continue
                    # Nothing left for this pool: the moment to pay for the
                    # refreshes the finished items deferred.
                    self._flush_refresh(force=True)
                    self._progress.idle()
                    if wake.wait(timeout=IDLE_POLL_SECONDS):
                        wake.clear()
                    continue
                try:
                    self._process(api, row)
                except Exception:
                    # Contain per item: a store hiccup must not kill the
                    # worker for the rest of the generation.
                    LOG.exception("download processing died for %s", row.jellyfin_id)
                    store.fail(row.jellyfin_id, "internal error")
                self._flush_refresh()
        except Exception:  # pragma: no cover - the backstop, never expected
            LOG.exception("download worker died")
        finally:
            api.close()

    def _drain_ops(self, own: Optional["threading.Event"] = None) -> None:
        """Apply everything waiting on the ops queue.

        Wakes the other workers once an add created a row: ``submit``'s wake
        fires before the row exists, so the worker that could claim it may
        already be asleep. ``own`` is skipped because it is about to claim.
        """
        queued = False
        while True:
            try:
                entry = self._ops.get_nowait()
            except Empty:
                break
            try:
                if entry.op == "add":
                    queued = self._apply_add(entry) or queued
                elif entry.op == "cancel":
                    self._apply_cancel(entry.item_id)
                elif entry.op == "remove":
                    self._apply_remove_batch(
                        entry.item_id.split(","),
                        subscription=entry.origin == "subscription",
                    )
                elif entry.op == "removeall":
                    self._apply_remove_all()
                elif entry.op == "subscriptions":
                    self._apply_subscriptions(entry.item_id)
            except Exception:
                LOG.exception("download op %s failed for %s", entry.op, entry.item_id)
        if queued:
            self._wake_all(skip=own)

    def _apply_add(self, entry: "_Op") -> bool:
        """Queue a row; True when one was actually created (see _drain_ops)."""
        if store.queue(
            store.Download(
                jellyfin_id=entry.item_id,
                origin=entry.origin,
                media_type=entry.media_type or "",
                request_id=entry.request_id,
                request_name=entry.request_name,
            )
        ):
            self._attempts.pop(entry.item_id, None)
            # Re-arm only the group this work could complete. An unrelated
            # queue must not make a late worker repeat an already announced
            # request; older automatic music still re-arms album grouping.
            with self._announce_lock:
                if entry.request_id:
                    self._announced.discard("request:%s" % entry.request_id)
                else:
                    self._announced.difference_update(
                        {
                            key
                            for key in self._announced
                            if not key.startswith("request:")
                        }
                    )
            LOG.debug("download queued: %s", entry.item_id)
            return True
        return False

    def _apply_cancel(self, item_id: str) -> None:
        row = store.get(item_id)
        if row is None or row.state == store.DONE:
            # Done rows are removed, not cancelled; active ones abort at the
            # next chunk and clean themselves up.
            self._clear_cancel(item_id)
            return
        if row.state in (store.QUEUED, store.FAILED):
            self._delete_media(row)
            store.remove(item_id)
            self._clear_cancel(item_id)
            LOG.debug("download cancelled: %s", item_id)

    def _remove_row(self, row: "store.Download") -> None:
        """The ordered removal every path shares: media, store row, then the
        pass, which must find the row gone."""
        self._delete_media(row)
        store.remove(row.jellyfin_id)
        self.native.detached(row)

    def _apply_remove_batch(
        self, item_ids: Iterable[str], subscription: bool = False
    ) -> None:
        """One request's worth of removals: every row, then one refresh and
        one toast.

        A removal is answered once per request, not per row, and does not
        wait out the completion path's defer window.
        """
        for item_id in item_ids:
            if self._should_stop():
                break
            if subscription:
                row = store.get(item_id)
                if (
                    row is None
                    or not row.origin.startswith(
                        ("auto:playlist:", "auto:musiclibrary:")
                    )
                    or store.has_subscription_claim(item_id)
                ):
                    continue
            self._apply_remove(item_id)
        self._flush_refresh(force=True)
        self._flush_removed()

    def _apply_remove(self, item_id: str) -> None:
        """One row. Every caller flushes the refresh and the announcement
        itself, once its whole batch is applied (_apply_remove_batch)."""
        row = store.get(item_id)
        if row is None:
            return
        if row.state != store.DONE:
            self._apply_cancel(item_id)
            return
        self._remove_row(row)
        self._mark_dirty(row.media_type)
        if row.media_type == "song":
            self._mark_playlist_dirty(row.jellyfin_id)
        with self._removed_lock:
            self._removed.append(_display_name(row))
        LOG.debug("download removed: %s", item_id)

    def _apply_subscriptions(self, playlist_id: str) -> None:
        api = self._api_factory()
        try:
            if playlist_id:
                subscriptions.reconcile_playlist_direct(api, playlist_id)
            else:
                subscriptions.reconcile_music_libraries(api)
                subscriptions.reconcile_playlists_direct(api)
        finally:
            api.close()

    def _apply_remove_all(self) -> None:
        """Every download goes: finished rows through the full remove path,
        unfinished ones cancelled in place (an active transfer aborts off the
        flag), then the empty category directories unless a stop cut the
        loop short; one refresh and one toast at the end.
        """
        rows = store.rows()

        if not rows:
            return

        stopped = False
        for row in rows:
            if self._should_stop():
                stopped = True
                break
            if row.state == store.DONE:
                self._apply_remove(row.jellyfin_id)
            else:
                with self._cancels_lock:
                    self._cancels.add(row.jellyfin_id)
                self._apply_cancel(row.jellyfin_id)

        if not stopped:
            sweep_category_dirs(downloads_root())
            # A playlist or library kept in sync would download the lot
            # again on its next pass.
            subscriptions.release_all()
        LOG.debug("removed all %d download(s)", len(rows))
        self._flush_refresh(force=True)
        self._flush_removed()

    # -- the transfer ----------------------------------------------------------

    def _process(self, api: Any, row: "store.Download") -> None:
        item_id = row.jellyfin_id
        try:
            item = api.item(item_id)
            self._transfer(api, row, item)
        except _Cancelled:
            self._delete_part(store.get(item_id) or row)
            store.remove(item_id)
            self._clear_cancel(item_id)
            LOG.debug("download cancelled mid-transfer: %s", item_id)
        except Unauthorized as error:
            # The server's EnableContentDownloading gate: retrying cannot fix
            # a permission, so the row settles immediately.
            store.fail(item_id, "download not permitted: %s" % error)
            if not row.request_id:
                self._toast(30713, item_id)
        except JellyfinError as error:
            self._retry_or_fail(row, str(error))
        except OSError as error:
            self._retry_or_fail(row, self._explain_write_error(error))
        finally:
            # Every exit leaves the active set — done, failed, cancelled or
            # requeued — and only a completed item advances the bar.
            self._progress.finish(item_id, store.is_done(item_id))
            current = store.get(item_id)
            if (
                current is not None
                and current.state == store.FAILED
                and current.request_id
            ):
                self._announce_request_terminal(current)

    def _transfer(self, api: Any, row: "store.Download", item: JsonDict) -> None:
        item_id = row.jellyfin_id
        media_type = MEDIA_TYPE_BY_DTO.get(str(item.get("Type")))
        if media_type is None:
            store.fail(item_id, "unsupported type %r" % item.get("Type"))
            return
        source = (item.get("MediaSources") or [{}])[0]

        decision = quality.decide(api, item)  # JellyfinError -> retry ladder
        original = decision.kind == quality.ORIGINAL
        if row.rel_path and row.quality != decision.kind:
            # The target was frozen for the other kind (the settings moved
            # between attempts): the extension and the resume semantics are
            # both wrong for it, so unfreeze and let this attempt re-decide.
            self._delete_part(row)
            store.record_target(item_id, "", "")
            row.rel_path = ""

        container = (
            str(source.get("Container") or "").split(",")[0]
            if original
            else decision.container
        )
        # A transcode's finished size is unknowable up front; 0 keeps the
        # size verification and the free-space precheck honest (the reserve
        # still applies).
        size_expected = int(source.get("Size") or 0) if original else 0
        # The grouping id (the series_id column): what the item's directory
        # belongs to — a show for episodes, an album for songs.
        group_id = str(item.get("SeriesId") or item.get("AlbumId") or "")
        store.record_details(
            item_id,
            media_type,
            group_id,
            size_expected,
            _userdata_json(item.get("UserData")),
            decision.kind,
        )

        root = downloads_root()
        if not files.on_this_device(root):
            store.fail(item_id, "the downloads folder is not on this device")
            if root != self._refused_root:
                # Once per folder, not once per item of a request. The
                # location itself can carry a password.
                self._refused_root = root
                LOG.warning("the downloads folder is a network location")
                toast.show(settings.localized(30717), toast.WARNING)
            return
        if row.rel_path and files.path_in(root, row.rel_path) is None:
            # A target an earlier build froze from a server's answer, outside
            # the folder: decided again, and nothing at the old path touched.
            LOG.debug("download target of %s left its folder; deciding again", item_id)
            store.record_target(item_id, "", "")
            row.rel_path = ""
        if not row.rel_path and not files.free_space_ok(root, size_expected):
            store.fail(item_id, "not enough free space")
            if not row.request_id:
                self._toast(30715, item.get("Name", item_id))
            return

        if not self._claim_root(root):
            # Decided before a byte moves: a folder that cannot carry the
            # marker cannot carry a download either.
            store.fail(item_id, "the downloads folder cannot be written")
            if root != self._refused_root:
                self._refused_root = root
                toast.show(settings.localized(30717), toast.WARNING)
            return

        owner_id = group_id or item_id
        if original:
            rel_path, actual = self._pull_original(
                api, row, item, owner_id, container, size_expected, root
            )
        else:
            rel_path, actual = self._pull_transcode(
                api, row, item, source, owner_id, decision, root
            )

        # The chunk loop checks the cancel flag before each chunk, so check
        # once more with the body complete. From store.finish on, completion
        # wins.
        if self._cancelled(item_id):
            raise _Cancelled()
        absolute = files.absolute_path(root, rel_path)
        part = files.part_path(root, rel_path)
        self._download_subtitles(
            api,
            item,
            source,
            os.path.dirname(absolute),
            rel_path,
            include_embedded=not original,
        )
        os.replace(part, absolute)
        if settings.available() and not _same_folder(downloads_root(), root):
            # The location moved while this downloaded. The file stays where
            # it landed, and the row leaves as a previous location's rows do:
            # unwatched, and without a toast.
            LOG.debug(
                "download of %s landed in %s, no longer the downloads folder; "
                "not tracked",
                item_id,
                root,
            )
            store.remove(item_id)
            return
        if not self._claim_root(root):
            # The marker went while this downloaded (the folder emptied, or
            # unmounted and mounted again); the file is where it landed, and
            # the row says why it is not a download.
            store.fail(item_id, "the downloads folder cannot be written")
            return
        store.finish(item_id, rel_path, container, actual)
        # Spent: a cancel that arrived after the check above completed
        # anyway, and left in the set it would cancel the *next* download
        # of this id at its first chunk.
        self._clear_cancel(item_id)
        self._attempts.pop(item_id, None)
        finished = store.get(item_id)
        if finished is not None:
            self.native.attached(finished, root)
        if media_type in store.VIDEO_MEDIA_TYPES:
            self._capture_segments(api, item_id)
        if settings.get_bool("downloadsExportMetadata"):
            export.export_item(api, item, absolute)  # best-effort by contract
        if media_type == "song":
            self._ensure_music_view()
        # Deferred, not fired here: the flusher refreshes once the pool goes
        # quiet.
        self._mark_dirty(media_type)
        if media_type == "song":
            self._mark_playlist_dirty(item_id)
        self._announce_complete(media_type, group_id, item, finished)
        LOG.debug("download complete: %s (%d bytes) at %s", item_id, actual, rel_path)

    def _capture_segments(self, api: Any, item_id: str) -> None:
        """The offline segment cache, taken at completion. Best-effort:
        segments never fail a download."""
        import json

        try:
            payload = api.media_segments(item_id)
            store.set_segments(item_id, json.dumps(payload))
        except Exception as error:
            # Broad on purpose: this runs after the download already
            # finished, and any escape here would mislabel a completed
            # download as an internal error.
            LOG.debug("segment capture skipped for %s: %s", item_id, error)

    def _ensure_music_view(self, force: bool = False) -> None:
        """The Downloaded-music view, the ``.m3u8`` of finished songs, exists
        from the first song on; idempotent, and never worth failing a
        download over.

        Once per manager generation, not once per track: each track's
        rewrite goes through ``_mark_playlist_dirty`` and
        ``refresh_song_playlists``. ``force`` is the reconcile, which runs
        to heal a file somebody deleted by hand.
        """
        if self._music_view_written and not force:
            return
        try:
            self.native.music_view(force)
            self._music_view_written = True
        except Exception:  # pragma: no cover - the view is best-effort
            LOG.exception("downloaded-music view refresh failed")

    def _pull_original(
        self,
        api: Any,
        row: "store.Download",
        item: JsonDict,
        owner_id: str,
        container: str,
        size_expected: int,
        root: str,
    ) -> tuple[str, int]:
        """The original bytes, Range-resumable."""
        item_id = row.jellyfin_id
        rel_path = row.rel_path
        start = 0
        if rel_path:
            part_existing = files.part_path(root, rel_path)
            if os.path.exists(part_existing):
                start = os.path.getsize(part_existing)
        stream = api.download_stream(item_id, start=start, if_range=row.validator)
        try:
            if not rel_path:
                # First contact decides the name: the server states it in
                # Content-Disposition on this very response, so one open
                # serves both the headers and the body.
                rel_path = self._decide_target(
                    item,
                    item_id,
                    owner_id,
                    container,
                    stream.header("Content-Disposition"),
                    root,
                )
            absolute = files.absolute_path(root, rel_path)
            part = files.part_path(root, rel_path)
            os.makedirs(os.path.dirname(absolute), exist_ok=True)
            expected_total = _expected_total(stream, start, size_expected)
            self._progress.begin(
                item_id, str(item.get("Name") or item_id), expected_total
            )
            if not stream.already_complete:
                if stream.status == 200 and start:
                    # The server ignored the range, or its file is no longer
                    # the one the .part began from: write fresh.
                    start = 0
                if not start:
                    # Emptied before the validator is stored, so the .part
                    # never holds bytes of a file its validator does not name.
                    open(part, "wb").close()
                    store.record_validator(item_id, _validator(stream))
                self._write_body(stream, part, start, item_id)
        finally:
            stream.close()

        actual = os.path.getsize(part) if os.path.exists(part) else 0
        if expected_total and actual != expected_total:
            mismatch = "size mismatch: %d of %d bytes" % (actual, expected_total)
            if actual > expected_total:
                # Longer than the whole file, so not a head of it: the next
                # attempt starts from zero rather than resuming past its end.
                _remove_quietly(part)
                actual = 0
            store.record_progress(item_id, actual)
            raise JellyfinError(mismatch)
        return rel_path, actual

    def _pull_transcode(
        self,
        api: Any,
        row: "store.Download",
        item: JsonDict,
        source: JsonDict,
        owner_id: str,
        decision: "quality.Decision",
        root: str,
    ) -> tuple[str, int]:
        """A progressive fMP4 (or music) transcode.

        Never resumed — a re-encode is not byte-stable, so every attempt
        starts from a clean ``.part`` — and verified by the duration probe,
        because a dead encoder ends the response cleanly and leaves no
        Content-Length to miss.
        """
        item_id = row.jellyfin_id
        slot = self._slot_for(MEDIA_TYPE_BY_DTO.get(str(item.get("Type")), ""))
        if not self._acquire_transcode_slot(item_id, slot):
            raise JellyfinError("interrupted waiting for the transcode slot")
        try:
            runtime_ticks = int(
                source.get("RunTimeTicks") or item.get("RunTimeTicks") or 0
            )
            self._progress.begin(
                item_id,
                str(item.get("Name") or item_id),
                quality.estimated_bytes(decision.url, runtime_ticks),
            )
            rel_path = row.rel_path
            stream = api.transcode_stream(decision.url)
            try:
                if not rel_path:
                    rel_path = self._decide_target(
                        item,
                        item_id,
                        owner_id,
                        decision.container,
                        stream.header("Content-Disposition"),
                        root,
                    )
                absolute = files.absolute_path(root, rel_path)
                part = files.part_path(root, rel_path)
                os.makedirs(os.path.dirname(absolute), exist_ok=True)
                _remove_quietly(part)
                self._write_body(stream, part, 0, item_id)
            finally:
                stream.close()

            actual = os.path.getsize(part) if os.path.exists(part) else 0
            self._verify_transcode(item, source, part, decision.container, actual)
            return rel_path, actual
        finally:
            self._close_transcode(api, decision.play_session_id)
            slot.release()

    def _slot_for(self, media_type: str) -> "threading.Semaphore":
        """Which transcode counter this item queues on — see the two
        semaphores in ``__init__``. Video is one at a time; music is as wide
        as its pool."""
        return (
            self._music_transcode_slot if media_type == "song" else self._transcode_slot
        )

    def _acquire_transcode_slot(
        self, item_id: str, slot: "threading.Semaphore"
    ) -> bool:
        """Wait for a transcode slot; False when stop or an outage ends the
        wait (the caller raises into the interruption paths). A worker parks
        here while another transcodes — accepted: the rest of the pool keeps
        draining originals, and the wait honors stop, outage and this item's
        own cancel within half a second."""
        while not self._should_stop() and not state.is_offline():
            if self._cancelled(item_id):
                raise _Cancelled()
            if slot.acquire(timeout=0.5):
                return True
        return False

    def _verify_transcode(
        self,
        item: JsonDict,
        source: JsonDict,
        part: str,
        container: str,
        actual: int,
    ) -> None:
        if actual <= 0:
            raise JellyfinError("transcode produced no bytes")
        runtime_ticks = int(source.get("RunTimeTicks") or item.get("RunTimeTicks") or 0)
        expected_seconds = runtime_ticks / 10_000_000
        if expected_seconds <= 0:
            return  # nothing to hold it to
        probed = probe.duration_seconds(part, container)
        if probed is None:
            return  # container this probe cannot read; clean EOF stands alone
        if probed < expected_seconds * 0.9 - 5:
            raise JellyfinError(
                "transcode truncated: %.0fs of %.0fs on disk"
                % (probed, expected_seconds)
            )

    def _close_transcode(self, api: Any, play_session_id: str) -> None:
        """End the server-side job by name. Also fired on success — closing a
        finished job is a no-op there, and saying it is free; on failure and
        cancel it is what stops an encoder working for nobody (the closed
        connection kills it too, eventually, but not promptly)."""
        if not play_session_id:
            return
        try:
            api.close_transcode(api.device_id, play_session_id)
        except JellyfinError as error:
            LOG.debug("closing the transcode job failed: %s", error)

    def _decide_target(
        self,
        item: JsonDict,
        item_id: str,
        owner_id: str,
        container: str,
        disposition: str,
        root: str,
    ) -> str:
        """Freeze the target path on first contact (files.py owns the rules).
        One worker decides at a time, so two transfers never take one name."""
        owning, leaf = files.item_dirs(item)
        fallback = files.default_filename(item, container)
        filename = files.filename_from_disposition(disposition, fallback)
        with self._target_lock:
            owning = files.unique_dir(owning, owner_id, _dir_taken_by_other(owner_id))
            directory = owning if leaf is None else "%s/%s" % (owning, leaf)
            unique = files.unique_filename(
                filename, _held_stems(root, directory, item_id)
            )
            if unique is None:
                raise JellyfinError("no free name for %s in %s" % (item_id, directory))
            rel_path = "%s/%s" % (directory, unique)
            if not files.contained(rel_path):
                raise JellyfinError("download path of %s leaves its folder" % item_id)
            store.record_target(item_id, rel_path, container)
        return rel_path

    def _write_body(
        self, stream: StreamedResponse, part: str, start: int, item_id: str
    ) -> None:
        written = start
        synced = start
        chunk_count = 0
        arriving = time.monotonic()
        try:
            with open(part, "ab" if start else "wb") as handle:
                for chunk in stream.chunks():
                    if self._cancelled(item_id):
                        raise _Cancelled()
                    if self._should_stop():
                        raise ServerUnreachable("stream abandoned while stopping")
                    handle.write(chunk)
                    written += len(chunk)
                    if written - synced >= SYNC_BYTES:
                        handle.flush()
                        began = time.monotonic()
                        _sync(handle.fileno(), synced, written - synced)
                        synced = written
                        busy = time.monotonic() - began
                        if busy > began - arriving:
                            self._stop.wait(min(busy, SYNC_REST_SECONDS))
                        arriving = time.monotonic()
                    chunk_count += 1
                    if chunk_count % PROGRESS_EVERY_CHUNKS == 0:
                        store.record_progress(item_id, written)
                        self._progress.tick(item_id, written)
        finally:
            # Also on the way out through an abort or a dead socket: the
            # resume reads the .part's real size, but a watermark left at
            # whatever the last 8 MiB tick happened to catch (or at 0)
            # misreports an interrupted download to everything that renders
            # one.
            store.record_progress(item_id, written)

    def _download_subtitles(
        self,
        api: Any,
        item: JsonDict,
        source: JsonDict,
        directory: str,
        rel_path: str,
        include_embedded: bool = False,
    ) -> None:
        """Subtitle sidecars beside the media file.

        An original download does not contain the external subtitles the
        streaming play route attaches, so a local play would lose them. A
        *transcoded* download loses the embedded text tracks too — the fMP4
        output carries no subtitles — so those are extracted as sidecars as
        well (``include_embedded``); the endpoint serves both kinds,
        converting embedded text to the asked-for srt. Embedded image tracks
        (PGS/DVDSUB) stay lost: Kodi cannot render a standalone one, and
        burning-in is a quality decision nobody made. Kodi auto-loads
        sidecars by name. Failures are logged and non-fatal — a missing
        subtitle must never fail the download.
        """
        base = os.path.basename(rel_path).rsplit(".", 1)[0]
        taken: set = set()
        for stream_info in source.get("MediaStreams") or []:
            if stream_info.get("Type") != "Subtitle":
                continue
            external = bool(stream_info.get("IsExternal"))
            if external:
                codec = str(stream_info.get("Codec") or "").lower()
                extension = files.extension(SUBTITLE_EXTENSIONS.get(codec, codec), "")
            elif include_embedded and stream_info.get("IsTextSubtitleStream"):
                extension = "srt"
            else:
                continue
            if not extension:
                continue
            language = str(stream_info.get("Language") or "und")
            url = api.subtitle_stream_url(
                str(item.get("Id")),
                str(source.get("Id")),
                int(stream_info.get("Index") or 0),
                extension,
            )
            # Two tracks of one language must not overwrite each other; the
            # second takes a numbered name (Kodi lists both).
            stem = "%s.%s" % (base, files.sanitize(language))
            candidate = "%s.%s" % (stem, extension)
            ordinal = 2
            while candidate in taken:
                candidate = "%s.%d.%s" % (stem, ordinal, extension)
                ordinal += 1
            taken.add(candidate)
            target = os.path.join(directory, candidate)
            try:
                payload = api.download(url)
                with open(target, "wb") as handle:
                    handle.write(payload)
            except (JellyfinError, OSError) as error:
                LOG.warning("subtitle sidecar failed for %s: %s", url, error)

    # -- failure and cleanup ---------------------------------------------------

    def _retry_or_fail(self, row: "store.Download", error: str) -> None:
        item_id = row.jellyfin_id
        if state.is_offline():
            # The server went away mid-transfer: back to queued without
            # spending an attempt, for the offline hold to pick up.
            LOG.debug("download interrupted by an outage: %s", item_id)
            store.release(item_id)
            return
        if self._should_stop():
            # Not a failure: the service is going away mid-transfer, and the
            # abort that ended the chunk loop is our own. The row stays
            # ``active`` so ``recover_interrupted`` re-queues it at the next
            # start, resuming from the .part with a Range; settling it as
            # failed would lose the automatic resume.
            LOG.debug("download interrupted by shutdown: %s", item_id)
            return
        attempts = self._attempts.get(item_id, 0) + 1
        self._attempts[item_id] = attempts
        store.fail(item_id, error)
        if attempts < MAX_ATTEMPTS and not self._should_stop():
            LOG.warning(
                "download attempt %d/%d failed for %s: %s",
                attempts,
                MAX_ATTEMPTS,
                item_id,
                error,
            )
            # fail -> queue re-queues in place, keeping bytes_done for the
            # Range resume; only this worker sits out the backoff.
            store.queue(
                store.Download(
                    jellyfin_id=item_id,
                    origin=row.origin,
                    quality=row.quality,
                    request_id=row.request_id,
                    request_name=row.request_name,
                )
            )
            self._stopping_aware_sleep(BACKOFF_SECONDS * attempts)
            return
        self._attempts.pop(item_id, None)
        LOG.error("download failed for %s: %s", item_id, error)
        if not row.request_id:
            self._toast(30713, item_id)

    def _stopping_aware_sleep(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline and not self._should_stop():
            time.sleep(0.2)

    def _delete_part(self, row: "store.Download") -> None:
        """Drop a partial transfer and the directories it created.

        A cancel before the first byte still made the season folder; prune
        to the same category floor as ``_delete_media``, so cancel and
        delete leave the same tree.
        """
        if not row.rel_path:
            return
        root = downloads_root()
        absolute = files.path_in(root, row.rel_path)
        if absolute is None:
            return
        _remove_quietly(absolute + ".part")
        _prune_empty_dirs(
            os.path.dirname(absolute), _category_floor(root, row.rel_path)
        )

    def _delete_media(self, row: "store.Download") -> None:
        """The media file, its .part and its sidecars, then any empty dirs."""
        delete_media_files(row)

    def _explain_write_error(self, error: OSError) -> str:
        if getattr(error, "errno", None) == 27:  # EFBIG
            return "file exceeds the filesystem's size limit (FAT32's 4 GiB?)"
        if getattr(error, "errno", None) == 28:  # ENOSPC
            return "disk full"
        return "write failed: %s" % error

    # -- maintenance: reconcile once, then the retention sweep ------------------

    def _run_maintenance(self) -> None:
        """Reconcile at start, then sweep on a slow beat. The first sweep
        runs right after the reconcile — it covers items watched while the
        service was down."""
        self._reconcile_once()
        self._backfill_segment_caches()
        self._retention_sweep()
        self._stale_sweep()
        while not self._stop.wait(timeout=RETENTION_SWEEP_SECONDS):
            if self._should_stop():
                return
            # Before the retention sweep: a file somebody deleted by hand is
            # not a download any more, and the sweep should not spend a
            # watched-check on it.
            self._sweep_vanished()
            self._retention_sweep()
            self._stale_sweep()

    def _backfill_segment_caches(self) -> None:
        """Downloads without a segment cache get one at the next start:
        pre-cache downloads, and any whose capture failed. Online only,
        never-fetched rows only — a known-empty answer is kept — so the pass
        is one bounded fetch per healed row, then permanently quiet."""
        if state.is_offline():
            return
        wanting = [
            row
            for row in store.rows(store.DONE)
            if row.media_type in store.VIDEO_MEDIA_TYPES and not row.segments_json
        ]
        if not wanting:
            return
        api = self._api_factory()
        try:
            for row in wanting:
                if self._should_stop():
                    return
                self._capture_segments(api, row.jellyfin_id)
        finally:
            api.close()

    def _reconcile_once(self) -> None:
        """Walk the done rows once at start: a missing file is cleaned up
        after (:meth:`_handle_vanished`), and a present file is handed to the
        pass again (``native.attached``), which heals a badge a finish never
        got."""
        try:
            root = downloads_root()
            in_hand = self._root_in_hand(root)
            touched = False
            songs = False
            repointed_songs: set[str] = set()
            for row in store.rows(store.DONE):
                if self._should_stop():
                    return
                songs = songs or row.media_type == "song"
                absolute = files.path_in(root, row.rel_path) if row.rel_path else ""
                if absolute is None:
                    continue  # outside the folder: not kofin's file to look at
                if not absolute or not os.path.exists(absolute):
                    # Asked again for every missing file: a drive that goes
                    # during the walk takes its marker with it.
                    if in_hand and self._root_in_hand(root):
                        self._handle_vanished(row, root)
                        touched = True
                    continue
                if self.native.attached(row, root):
                    touched = True
                    if row.media_type == "song":
                        repointed_songs.add(row.jellyfin_id)
            if songs:
                self._ensure_music_view(force=True)  # heals a hand-deleted .m3u8 too
            if repointed_songs:
                self._refresh_song_playlists(repointed_songs)
            if touched:
                self._refresh_quietly(["music", "video"] if songs else ["video"])
        except Exception:  # pragma: no cover - never break service start
            LOG.exception("downloads reconcile failed")

    def _handle_vanished(self, row: "store.Download", root: str) -> None:
        """A downloaded file deleted behind Kodi's back — a file manager, a
        card pulled and cleaned up on a computer, another app.

        It goes through the removal path proper: the row, the sidecars and
        the badge go, and nothing else moves. A deleted file says nothing
        about whether the item was watched, and a watched mark reaches every
        client of the account.
        """
        LOG.warning("downloaded file missing for %s; cleaning up", row.jellyfin_id)
        self._remove_row(row)
        self._mark_dirty(row.media_type)
        if row.media_type == "song":
            self._mark_playlist_dirty(row.jellyfin_id)

    def _root_in_hand(self, root: str) -> bool:
        """Whether a done row's file missing under ``root`` was deleted.

        Only in the remembered folder (``_remembered_root``) while its marker
        (``files.MARKER``) says the volume is mounted. With no folder
        remembered yet, ``root`` is adopted when it already holds a done
        row's file: the folder of a build from before the marker. Anything
        else (a drive not mounted, a new folder that is not claimed yet, a
        settings store that cannot be read and so names the default folder)
        is not a deletion.
        """
        if not settings.available() or not os.path.isdir(root):
            return False
        with self._root_lock:
            remembered = self._remembered_root()
            if remembered is not None:
                return _same_folder(remembered, root) and files.has_marker(root)
            if self._holds_a_download(root) and files.write_marker(root):
                self._remember_root(root)
                return True
        LOG.debug(
            "downloads folder %s holds no download yet; missing files left alone", root
        )
        return False

    def _claim_root(self, root: str) -> bool:
        """Remember ``root``, which a download is about to land in; False
        when the download must not go there.

        A done row whose file is not there was downloaded to the folder the
        location named before. It leaves without being marked watched, since
        once the folder is remembered the sweep would read it as deleted.
        With no folder remembered yet, a ``root`` that already holds a done
        row's file is the folder of a build from before the marker, and keeps
        its rows. The remembered folder found with neither its marker nor
        any of its files has been emptied: the rows of what it held leave the
        same way and the folder is marked again.
        """
        if not settings.available():
            return True
        try:
            os.makedirs(root, exist_ok=True)
        except OSError as error:
            LOG.debug("downloads folder %s cannot be made: %s", root, error)
            return False
        with self._root_lock:
            remembered = self._remembered_root()
            if remembered is not None and _same_folder(remembered, root):
                if files.has_marker(root):
                    return True
                if not self._holds_a_download(root):
                    self._drop_absent(root, store.rows(store.DONE), emptied=True)
                return files.write_marker(root)
            if remembered is not None or not self._holds_a_download(root):
                self._drop_absent(root, store.rows(store.DONE))
            if not files.write_marker(root):
                return False
            self._remember_root(root)
            return True

    def _drop_absent(
        self, root: str, rows: Iterable["store.Download"], emptied: bool = False
    ) -> None:
        """Forget the done rows whose files are not in ``root``: their badges
        go, their files are wherever they were downloaded to."""
        absent = [row for row in rows if not _present(root, row)]
        if emptied and absent:
            LOG.warning(
                "downloads folder %s holds none of %d download(s) and no marker; "
                "taken as emptied, their rows dropped",
                root,
                len(absent),
            )
        for row in absent:
            LOG.debug(
                "download of %s is not in %s; no longer tracked", row.jellyfin_id, root
            )
            store.remove(row.jellyfin_id)
            self.native.detached(row)
            self._mark_dirty(row.media_type)
            if row.media_type == "song":
                self._mark_playlist_dirty(row.jellyfin_id)

    @staticmethod
    def _holds_a_download(root: str) -> bool:
        return any(_present(root, row) for row in store.rows(store.DONE))

    def _remembered_root(self) -> Optional[str]:
        """The folder the done rows were downloaded to. It is kept in
        addon_data, where a drive that is not mounted cannot take it away.
        Called under ``_root_lock``."""
        if self._root_memory is None:
            try:
                with open(_root_memory_path(), encoding="utf-8") as stored:
                    self._root_memory = stored.read().strip()
            except OSError:
                self._root_memory = ""
        return self._root_memory or None

    def _remember_root(self, root: str) -> None:
        """Called under ``_root_lock``."""
        folder = os.path.normpath(root)
        path = _root_memory_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as stored:
                stored.write(folder)
        except OSError as error:
            LOG.warning("could not record the downloads folder: %s", error)
        self._root_memory = folder

    def _sweep_vanished(self) -> None:
        """The presence check on the maintenance beat: ``_reconcile_once``
        runs only at start."""
        try:
            root = downloads_root()
            if not self._root_in_hand(root):
                return
            touched = False
            songs = False
            for row in store.rows(store.DONE):
                if self._should_stop():
                    return
                absolute = files.path_in(root, row.rel_path) if row.rel_path else ""
                if absolute is None or (absolute and os.path.exists(absolute)):
                    # Present, or outside the folder and not kofin's to judge.
                    continue
                if self._playing_now(row):
                    # Not gone, just unreadable for a moment (a network share
                    # blinking); tearing the row down under the player would
                    # turn a stutter into a lost download.
                    continue
                if not self._root_in_hand(root):
                    continue  # the folder went during the walk
                songs = songs or row.media_type == "song"
                self._handle_vanished(row, root)
                touched = True
            if touched:
                self._refresh_quietly(["music", "video"] if songs else ["video"])
        except Exception:  # pragma: no cover - never kill the maintenance loop
            LOG.exception("vanished-download sweep failed")

    def _retention_sweep(self) -> None:
        """Remove watched downloads, through the full remove path —
        never a bare unlink.

        The backstop for what the end-of-playback offer cannot see: an item
        watched while the service was down, or through something other than
        kofin's player. It runs only in the *silent* mode — with the confirm
        mode chosen, removal is a question, and this sweep has no one to ask
        (the thing it noticed may have finished an hour ago).

        Two exclusions are load-bearing: songs are never swept (a played
        track is not a finished one), and the item currently playing is
        skipped — Kodi marks played at ~90%, and a sweep firing in a binge
        episode's last minutes would delete the file under the player.

        Watched means watched since the download landed, from Kodi's own
        state, which works offline: a play count, a last played later than
        ``done_at``, and no resume point. A download of something already
        watched carries the server's count and its earlier date, and Kodi
        stamps the date of a play stopped part way too, leaving its resume
        point.
        """
        try:
            if not settings.get_bool("downloadsDeleteAfterWatching"):
                return
            if not settings.get_bool("downloadsDeleteAutomatically"):
                return
            for row in store.rows(store.DONE):
                if self._should_stop():
                    return
                if row.media_type not in store.VIDEO_MEDIA_TYPES:
                    continue
                if not _watched_locally(row):
                    continue
                touched = _last_touch(row)
                if touched is None:
                    continue
                last_played, resuming = touched
                if resuming or last_played <= row.done_at:
                    continue
                if self._playing_now(row):
                    continue
                LOG.debug(
                    "retention: removing watched %s (%s)",
                    row.jellyfin_id,
                    row.origin,
                )
                self._apply_remove(row.jellyfin_id)
            self._flush_refresh(force=True)
            self._flush_removed()
        except Exception:  # pragma: no cover - never kill the maintenance loop
            LOG.exception("retention sweep failed")

    def _stale_sweep(self) -> None:
        """Remove downloads nobody has touched in ``downloadsStaleDays`` days,
        through the full remove path.

        Age is the later of ``done_at`` and Kodi's last played. Never stale:
        an item with a resume point (Kodi drops it at the end, and the pass
        writes the server's play state), the file playing, songs, and a row
        whose age is unknown.
        """
        try:
            if not settings.get_bool("downloadsDeleteStale"):
                return
            days = max(1, settings.get_int("downloadsStaleDays") or STALE_DAYS_DEFAULT)
            cutoff = time.time() - days * SECONDS_PER_DAY
            for row in store.rows(store.DONE):
                if self._should_stop():
                    return
                if row.media_type not in store.VIDEO_MEDIA_TYPES:
                    continue
                if not row.done_at or row.done_at > cutoff:
                    # The cheap half, off the store row alone: a row inside
                    # its window never asks Kodi.
                    continue
                touched = _last_touch(row)
                if touched is None:
                    continue
                last_played, resuming = touched
                if resuming or last_played > cutoff:
                    continue
                if self._playing_now(row):
                    continue
                LOG.debug(
                    "stale: removing %s, untouched for %d day(s)",
                    row.jellyfin_id,
                    int(
                        (time.time() - max(row.done_at, last_played)) / SECONDS_PER_DAY
                    ),
                )
                self._apply_remove(row.jellyfin_id)
            self._flush_refresh(force=True)
            self._flush_removed()
        except Exception:  # pragma: no cover - never kill the maintenance loop
            LOG.exception("stale-download sweep failed")

    def _paused_for_playback(self) -> bool:
        """Whether the pool should stop claiming while something plays.

        ``isPlaying`` rather than ``state.get_playing_id``: the property only
        covers playbacks kofin claimed, and a download competing for
        bandwidth does not care who started the video. Audio counts too — a
        transcode pull saturates the same link either way.
        """
        if not settings.get_bool("downloadsPauseDuringPlayback"):
            return False
        try:
            return bool(xbmc.Player().isPlaying())
        except RuntimeError:  # pragma: no cover - no player, so nothing plays
            return False

    def wake(self) -> None:
        """Let the pool re-check its gates now rather than at the next poll —
        the service calls this when playback stops."""
        self._wake_all()

    def _playing_now(self, row: "store.Download") -> bool:
        try:
            playing = xbmc.Player().getPlayingFile()
        except RuntimeError:
            return False
        if not playing or not row.rel_path:
            return False
        absolute = files.path_in(downloads_root(), row.rel_path)
        return absolute is not None and os.path.abspath(playing) == os.path.abspath(
            absolute
        )

    # -- making writes visible --------------------------------------------------

    def _mark_dirty(self, media_type: str) -> None:
        """Note that a database needs a refresh, without doing it yet.

        Songs move Kodi's music database, everything else the video one.
        """
        with self._dirty_lock:
            self._dirty.add("music" if media_type == "song" else "video")
            if not self._dirty_since:
                self._dirty_since = time.monotonic()

    def _mark_playlist_dirty(self, item_id: str) -> None:
        with self._dirty_lock:
            self._playlist_dirty.add(item_id)

    def _refresh_song_playlists(self, item_ids: set[str]) -> None:
        try:
            self.native.refresh_song_playlists(item_ids)
        except Exception:
            LOG.exception("managed playlist refresh after song repoint failed")

    def _flush_refresh(self, force: bool = False) -> None:
        """Refresh the dirty databases — on ``force`` (the pool went quiet),
        or once the oldest mark has waited out the defer window."""
        with self._dirty_lock:
            if not self._dirty and not self._playlist_dirty:
                return
            waited = time.monotonic() - self._dirty_since
            if not force and waited < REFRESH_MAX_DEFER_SECONDS:
                return
            databases = sorted(self._dirty)
            playlist_ids = self._playlist_dirty
            self._playlist_dirty = set()
            self._dirty.clear()
            self._dirty_since = 0.0
        if playlist_ids:
            self._refresh_song_playlists(playlist_ids)
        if databases:
            self._refresh_quietly(databases)

    def _refresh_quietly(self, databases: Optional[list[str]] = None) -> None:
        try:
            self._refresh(databases or ["video"])
        except Exception:  # pragma: no cover - refresh is best-effort
            LOG.exception("downloads refresh failed")

    def _announce_complete(
        self,
        media_type: str,
        group_id: str,
        item: JsonDict,
        row: Optional["store.Download"] = None,
    ) -> None:
        """Announce a user request once, after all of its items settle.

        Older and automatic rows have no request ID. Their music keeps the
        album grouping and their video keeps the item-level notification.
        """
        if row is None:
            row = store.get(str(item.get("Id") or ""))
        if row is not None and row.request_id:
            self._announce_request_terminal(row)
            return
        if media_type != "song":
            self._toast(30712, item.get("Name") or item.get("Id", ""))
            return
        if not group_id:
            self._toast(30712, item.get("Name") or item.get("Id", ""))
            return
        self._announce_once(
            group_id,
            store.container_counts(group_id)["pending"],
            item.get("Album") or item.get("Name") or group_id,
        )

    def _announce_request_terminal(self, row: "store.Download") -> None:
        counts = store.request_counts(row.request_id)
        if not counts["total"]:
            return
        self._announce_once(
            "request:%s" % row.request_id,
            counts["pending"],
            row.request_name or row.request_id,
            30713 if counts["failed"] else 30712,
        )

    def _announce_once(
        self, key: str, pending: int, name: Any, string_id: int = 30712
    ) -> None:
        """Toast for ``key`` when nothing under it is still coming, and only
        for the worker that gets there first."""
        with self._announce_lock:
            if key in self._announced:
                return
            if pending:
                return  # more of this one is still coming
            self._announced.add(key)
        self._toast(string_id, name)

    def _flush_removed(self) -> None:
        """Announce the batch just deleted: one toast per batch, the name for
        one, a count for several. Automatic removals announce here too."""
        with self._removed_lock:
            names = self._removed
            self._removed = []

        if not names:
            return

        if len(names) == 1:
            self._toast(30823, names[0])
            return

        self._toast(30824, len(names))

    def _toast(self, string_id: int, name: Any) -> None:
        if not notify_allowed(string_id):
            return
        try:
            toast.show(settings.localized(string_id) % name, time_ms=4000)
        except Exception:  # pragma: no cover - uncached string etc.
            LOG.debug("download toast failed for %s", string_id)


def _display_name(row: "store.Download") -> str:
    """What a toast can call a download: the file's own name, which is what
    the user sees in the downloads folder — the row carries no title."""
    base = os.path.splitext(os.path.basename(row.rel_path))[0]
    return base or row.jellyfin_id


def _expected_total(stream: StreamedResponse, start: int, fallback: int) -> int:
    """What the finished file must weigh, from the response's own headers.

    A 206 states the whole in Content-Range ("bytes a-b/total") — including
    the 416 already-complete answer's "bytes */total". A 200's Content-Length
    is the whole outright. A transcode states neither, which is what the
    fallback (and clean-EOF completion) is for.
    """
    content_range = stream.header("Content-Range")
    if "/" in content_range:
        total = content_range.rsplit("/", 1)[1].strip()
        if total.isdigit():
            return int(total)
    length = stream.header("Content-Length")
    if length.isdigit():
        return start + int(length) if stream.status == 206 else int(length)
    return int(fallback)


def _validator(stream: StreamedResponse) -> str:
    """What a resume's If-Range names the response's file by: its ETag, which
    must not be a weak one there, else its Last-Modified; "" for neither."""
    tag = stream.header("ETag")
    if tag and not tag.startswith("W/"):
        return tag
    return stream.header("Last-Modified")


def _userdata_json(userdata: Any) -> str:
    import json

    if not isinstance(userdata, dict):
        return ""
    try:
        return json.dumps(userdata)
    except (TypeError, ValueError):
        return ""


def _dir_taken_by_other(owner_id: str) -> Callable[[str], bool]:
    """Is this directory already claimed by a *different* owner? A row's
    owner is its series (episodes) or itself (films), matching how
    files.item_dirs assigns directories."""

    def taken(directory: str) -> bool:
        prefix = directory + "/"
        for row in store.rows():
            if not row.rel_path.startswith(prefix):
                continue
            if (row.series_id or row.jellyfin_id) != owner_id:
                return True
        return False

    return taken


def _held_stems(root: str, directory: str, item_id: str) -> list[str]:
    """The file stems ``directory`` holds already: another row's file's, and
    those of the files there that no row names, which a download never
    writes over. A ``.part`` counts only through its row: one with no row is
    a stale transfer's, and is written over."""
    folded = directory.casefold()
    names = [
        posixpath.basename(rel_path)
        for other_id, rel_path in store.targets_under(directory)
        if other_id != item_id and posixpath.dirname(rel_path).casefold() == folded
    ]
    absolute = files.path_in(root, directory)
    if absolute is not None:
        try:
            names.extend(
                name for name in os.listdir(absolute) if not name.endswith(".part")
            )
        except OSError:
            pass  # not made yet
    return [files.stem(name) for name in names]


# The sweep's two reads of Kodi's own play state, as module functions so a
# test can stand them in (downloads/nativeport.py).
_as_epoch = nativeport._as_epoch


def _watched_locally(row: "store.Download") -> bool:
    return nativeport.for_build().watched_locally(row)


def _last_touch(row: "store.Download") -> Optional[tuple[float, bool]]:
    return nativeport.for_build().last_touch(row)


def _sync(descriptor: int, offset: int, length: int) -> None:
    """Write the file through to storage and drop ``length`` bytes from
    ``offset`` from the page cache. A file system that refuses the sync costs
    only the pacing."""
    try:
        getattr(os, "fdatasync", os.fsync)(descriptor)
    except OSError as error:
        LOG.debug("download sync refused: %s", error)
        return
    if hasattr(os, "posix_fadvise"):
        try:
            os.posix_fadvise(descriptor, offset, length, os.POSIX_FADV_DONTNEED)
        except OSError:
            pass


def _remove_quietly(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


def delete_media_files(row: "store.Download") -> None:
    """One download's media file, its .part and its sidecars, then empty dirs.

    Scoped to the row's own ``rel_path`` rather than sweeping the downloads
    root: the root is user-configurable, and someone who pointed it at a
    folder they share with other media must lose only what kofin put there.
    """
    if not row.rel_path:
        return
    root = downloads_root()
    absolute = files.path_in(root, row.rel_path)
    if absolute is None:
        return
    directory = os.path.dirname(absolute)
    base = os.path.basename(row.rel_path).rsplit(".", 1)[0]
    _remove_quietly(absolute + ".part")
    _remove_quietly(absolute)
    try:
        for name in os.listdir(directory):
            if name.startswith(base + "."):
                _remove_quietly(os.path.join(directory, name))
    except OSError:
        pass
    _prune_empty_dirs(directory, _category_floor(root, row.rel_path))


# The three directories the layout puts under the root (files.item_dirs).
# They are a floor, not a target: deleting downloads one at a time prunes
# the title, season and album directories inside them and stops there, so
# a folder the user has pointed something at — a Kodi source, a file
# manager shortcut — does not disappear from under it the moment its last
# item goes. Only remove-all takes them (sweep_category_dirs).
CATEGORY_DIRS = frozenset({files.MOVIES_DIR, files.SHOWS_DIR, files.MUSIC_DIR})


def _category_floor(root: str, rel_path: str) -> str:
    """The directory pruning must stop at for ``rel_path``.

    ``<root>/<category>`` when the path starts with one of the three names
    the layout writes, and the root itself for anything else — a row whose
    layout predates a category, or a hand-made path, prunes to the root
    rather than being kept alive by a name nobody recognises.
    """
    head = rel_path.split("/", 1)[0]
    if head in CATEGORY_DIRS:
        return os.path.join(root, head)
    return root


def sweep_category_dirs(root: str) -> int:
    """Remove the empty category directories, and only those. Returns how
    many went.

    The other half of the floor above: "delete all downloads" takes the
    folders the per-row deletes leave — only the three by name, only when
    empty, never the root.
    """
    swept = 0
    for name in sorted(CATEGORY_DIRS):
        directory = os.path.join(root, name)
        try:
            os.rmdir(directory)
        except OSError:
            continue
        swept += 1
    return swept


# What the metadata export leaves at directory level. A directory holding
# only these counts as empty for pruning: the media left, and its
# escape-hatch sidecars must not keep the tree alive. The per-item
# ``<basename>.nfo`` needs no entry — the sibling sweep in ``_delete_media``
# already takes everything sharing the media file's stem.
EXPORTED_COMPANIONS = frozenset(
    {"poster.jpg", "fanart.jpg", "tvshow.nfo", "folder.jpg", "album.nfo", "artist.nfo"}
)


def _sweep_exported(directory: str) -> None:
    try:
        names = os.listdir(directory)
    except OSError:
        return
    if not names or not set(names) <= EXPORTED_COMPANIONS:
        return
    for name in names:
        _remove_quietly(os.path.join(directory, name))


def _prune_empty_dirs(directory: str, floor: str) -> None:
    """Remove now-empty directories up to (never including) ``floor``; a
    directory down to its exported metadata counts as empty.

    ``floor`` is the category directory for a row that has one and the
    downloads root otherwise (:func:`_category_floor`).
    """
    current = os.path.abspath(directory)
    stop = os.path.abspath(floor)
    while current.startswith(stop) and current != stop:
        _sweep_exported(current)
        try:
            os.rmdir(current)
        except OSError:
            return
        current = os.path.dirname(current)


def _present(root: str, row: "store.Download") -> bool:
    """Whether the row's file is in ``root``. A stored path outside the
    folder is not, and is never looked at."""
    absolute = files.path_in(root, row.rel_path) if row.rel_path else None
    return absolute is not None and os.path.exists(absolute)


def _same_folder(first: str, second: str) -> bool:
    return os.path.normpath(first) == os.path.normpath(second)


def _root_memory_path() -> str:
    from kofin.sync import private

    return os.path.join(private.addon_data_path(), ROOT_MEMORY)
