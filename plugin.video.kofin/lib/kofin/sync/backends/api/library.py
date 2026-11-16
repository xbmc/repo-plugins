"""API coordinator. Network enumeration precedes publication.

One worker serializes publication and native jobs. Callbacks enqueue intent
and never wait on Kodi scans. A complete enumeration -- startup without a
watermark, Update library, a sync-queue retention overrun, the scheduled full
update when one is set -- is the only listing that may imply deletion;
between passes the websocket and a watermarked catch-up on
the shared change-feed contract carry the changes. Native operations already
published are replayed even if Jellyfin is offline.
"""

import collections
import functools
import queue
import threading
import re
import time
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Callable, Collection, Iterable, Sequence
from typing import TYPE_CHECKING, Any, Optional

import xbmc

from kofin.core import memory, settings, state, toast
from kofin.core.http import HttpError, JellyfinError, ServerUnreachable, Unauthorized
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.sync import changefeed, kofindb, private
from kofin.sync.catalogue import BackendMismatch, EarlierLibrary
from . import announce, capabilities, metadata, progress
from . import playlists as api_playlists
from . import status as apistatus
from .native import Native
from .store import REBUILDING, Store, namespace

if TYPE_CHECKING:
    from kofin.core.api import Api
    from kofin.service.player import Player

LOG = Logger(__name__)

KINDS_BY_COLLECTION = {
    "movies": ("Movie",),
    "tvshows": ("Series", "Season", "Episode"),
    "musicvideos": ("MusicVideo",),
    "mixed": ("Movie", "Series", "Season", "Episode", "MusicVideo"),
    "music": ("MusicArtist", "MusicAlbum", "Audio"),
}
SUPPORTED = ("movies", "tvshows", "musicvideos", "mixed", "music")
# SpecialFeatureCount says which movies have extras to fetch (attach_extras).
# The fields every video listing asks the server for.
VIDEO_FIELDS = (
    "Path,Genres,SortName,OriginalTitle,Studios,Writer,Taglines,LocalTrailerCount,"
    "OfficialRating,CumulativeRunTimeTicks,ItemCounts,"
    "Metascore,AirTime,DateCreated,People,Overview,"
    "Etag,ShortOverview,ProductionLocations,"
    "Tags,ProviderIds,ParentId,RemoteTrailers,SpecialEpisodeNumbers,"
    "MediaSources,VoteCount,RecursiveItemCount,PrimaryImageAspectRatio,"
    "SpecialFeatureCount"
)
FIELDS = VIDEO_FIELDS + ",MediaStreams,SpecialFeatureCount"


def library_filter(
    api: "Api", parent_id: str, item_types: Optional[str] = None
) -> dict[str, Any]:
    """The filter every library listing shares: this parent, recursive,
    real files only (present, not virtual-unaired), sets uncollapsed."""
    return {
        "userId": api.user_id,
        "ParentId": parent_id,
        "IncludeItemTypes": item_types,
        "CollapseBoxSetItems": False,
        "IsVirtualUnaired": False,
        "LocationTypes": "FileSystem,Remote,Offline",
        "IsMissing": False,
        "Recursive": True,
    }


# Music asks for what its tags and art need and nothing the server has to
# count (RecursiveItemCount is slow); People, trailers and streams have no
# music setter.
MUSIC_FIELDS = (
    "DateCreated,Genres,ProviderIds,MediaSources,Overview,SortName,Etag,"
    "ParentId,PremiereDate,Tags"
)
MUSIC_KINDS = ("MusicArtist", "MusicAlbum", "Audio")
# What a listing asks the server for, recorded per library when its listing
# is published (store.remember_listing). A catch-up fetches changed items
# alone, so rows filed from a listing that lacked a field would never get
# it: a library whose record differs is listed again by name, at the first
# catch-up and then at each one until it has been (stale_listings).
LISTING = FIELDS + "|" + MUSIC_FIELDS
CHANGEFEED_TYPES = ("movies", "tvshows", "boxsets", "musicvideos", "music")
# Between the websocket and the sync-queue feed the catch-up is a safety
# net. A full enumeration on a clock is the viewer's choice
# (fullUpdateInterval, in days, 0 for none). Without the sync queue the
# catch-up reads save dates and cannot see a deletion.
CATCHUP_INTERVAL = 1800
# A catch-up's cursor is stored this many seconds behind the clock it read:
# a feed can write a record after a catch-up has read past the time the
# record is stamped with, and without a companion the cursor is Kodi's clock
# against the server's save dates. A change read twice costs only its
# re-fetch.
CATCHUP_OVERLAP = 300
DAY = 86400
# A selected library the server stopped listing leaves once GET
# /Items/{id} has answered 404 twice this far apart (settle_missing).
MISSING_CONFIRM = CATCHUP_INTERVAL


def full_interval() -> Optional[float]:
    """Seconds between scheduled complete enumerations, or None for none."""
    days = settings.get_int("fullUpdateInterval")
    return days * DAY if days > 0 else None


PAGE = 200
# A song's DTO is about a tenth of a movie's, so its pages are larger.
MUSIC_PAGE = 500
# Pages of one listing in flight at once: a page's wait is the wire, not the
# server or the client.
PAGERS = 3
# Ids named in one /Items request. Each costs 35 characters of the request
# line, which Kestrel caps at 8 KiB by default and answers 414 past.
IDS_PER_REQUEST = 50
# How long after a playback stopped the user data held for its item is
# applied when the server has sent nothing newer. The server's own entry
# for the stop arrives within a second or two and replaces the held one.
HELD_USERDATA_GRACE = 20.0

# A pass waits until nothing has been published for PASS_SETTLE and no event
# is queued unread, and no longer than PASS_SETTLE_MAX after its work
# appeared: one change often comes as two publishes (the outbox's re-read of
# an edit and the server's echo of it, a moment apart), and every pass costs
# seconds whatever it holds.
PASS_SETTLE = 1.0
PASS_SETTLE_MAX = 3.0
# What a viewer asks for by name: the bar is up from the request to the end
# of the work (progress.Progress.attend).
ATTENDED = ("SyncLibrary", "UpdateLibrary", "RepairLibrary", "RemoveLibrary")
HAS_CONTENT = {
    "Movie": "Movies",
    "Series": "TVShows",
    "MusicVideo": "MusicVideos",
    "Audio": "Music",
}


def status(value: str, listing: Iterable[str] = (), namespace: str = "") -> None:
    """What the sync is doing, for the status dialog (status.py), under the
    account whose thread says so."""
    apistatus.write(value, listing, namespace)


def collection_kinds(view: dict[str, Any]) -> tuple[str, ...]:
    collection = view.get("CollectionType") or "mixed"
    return KINDS_BY_COLLECTION.get(collection, ())


def fetch_kind(
    api: "Api",
    library: str,
    kind: str,
    abort: Callable[[], bool] = lambda: False,
    extra: Optional[dict[str, Any]] = None,
    on_page: Optional[Callable[[int, int], None]] = None,
    api_factory: Optional[Callable[[], "Api"]] = None,
) -> list[dict[str, Any]]:
    """Only a complete, stable, duplicate-free pagination can imply deletion.

    ``on_page(fetched, total)`` is told after every page, for the bar.

    With ``api_factory`` the pages after the first are asked for PAGERS at
    a time, each worker on a client of its own, and taken in listing order.
    Nothing is relaxed for it: every page reports the first page's total
    and is exactly as long as its place in the listing says, or the
    enumeration fails as a whole.
    """
    result: list[dict] = []
    seen = set()
    limit = MUSIC_PAGE if kind in MUSIC_KINDS else PAGE

    def ask(client: "Api", start: int) -> tuple[int, list[dict[str, Any]]]:
        if abort():
            raise InterruptedError("enumeration stopped")
        params = {
            **library_filter(client, library, kind),
            "Fields": MUSIC_FIELDS if kind in MUSIC_KINDS else FIELDS,
            "StartIndex": start,
            "Limit": limit,
            "SortBy": "DateCreated,SortName",
            "SortOrder": "Ascending,Ascending",
            "EnableTotalRecordCount": True,
        }
        params.update(extra or {})
        page = client.items(params)
        count = page.get("TotalRecordCount")
        rows = page.get("Items")
        if not isinstance(count, int) or count < 0 or not isinstance(rows, list):
            raise ValueError("incomplete %s page" % kind)
        return count, rows

    def take(rows: list[dict[str, Any]], total: int) -> None:
        for item in rows:
            if (
                not isinstance(item, dict)
                or not item.get("Id")
                or item.get("Type") != kind
                or not item.get("Name")
                or item["Id"] in seen
                or (kind in ("Season", "Episode") and not item.get("SeriesId"))
            ):
                raise ValueError("invalid or duplicate %s" % kind)
            seen.add(item["Id"])
            result.append(metadata.compact(item))
        if len(result) > total or (not rows and len(result) < total):
            raise ValueError("short %s page" % kind)
        if on_page is not None:
            on_page(len(result), total)

    total, rows = ask(api, 0)
    take(rows, total)
    starts = list(range(limit, total, limit))
    if api_factory is not None and len(starts) > 1 and len(rows) == limit:
        _fetch_pages(ask, take, starts, total, limit, kind, api_factory, api)
    while len(result) < total:
        count, rows = ask(api, len(result))
        if count != total:
            raise ValueError("%s listing changed during enumeration" % kind)
        take(rows, total)
    if kind == "Movie":
        attach_extras(api, result, abort)
    return result


def _account(client: "Api") -> tuple[Any, Any]:
    return getattr(client, "server", None), getattr(client, "user_id", None)


def _fetch_pages(
    ask: Callable[["Api", int], tuple[int, list[dict[str, Any]]]],
    take: Callable[[list[dict[str, Any]], int], None],
    starts: Sequence[int],
    total: int,
    limit: int,
    kind: str,
    api_factory: Callable[[], "Api"],
    api: "Api",
) -> None:
    """The pages at ``starts``, PAGERS in flight, taken in listing order.

    At most PAGERS pages wait to be taken, so a slow first page never lets
    the rest of a catalogue pile up behind it in memory.

    Every page client answers for the account ``api`` asked the first page
    as. The factory reads the stored credentials when it is called, so a
    sign-in changed while the enumeration runs fails it as a whole.
    """
    local = threading.local()
    clients: list[Any] = []
    account = _account(api)

    def page(start: int) -> tuple[int, list[dict[str, Any]]]:
        client = getattr(local, "client", None)
        if client is None:
            client = api_factory()
            clients.append(client)
            if _account(client) != account:
                raise ValueError("account changed during %s enumeration" % kind)
            local.client = client
        return ask(client, start)

    pending = iter(starts)
    window: collections.deque = collections.deque()
    pool = ThreadPoolExecutor(
        max_workers=min(PAGERS, len(starts)), thread_name_prefix="kofin-page"
    )

    def top_up() -> None:
        while len(window) < PAGERS:
            start = next(pending, None)
            if start is None:
                return
            window.append((start, pool.submit(page, start)))

    try:
        top_up()
        while window:
            start, future = window.popleft()
            count, rows = future.result()
            if count != total:
                raise ValueError("%s listing changed during enumeration" % kind)
            if len(rows) != min(limit, total - start):
                raise ValueError("short %s page" % kind)
            top_up()
            take(rows, total)
    finally:
        for _, future in window:
            future.cancel()
        pool.shutdown(wait=True)
        for client in clients:
            try:
                client.close()
            except Exception as error:
                LOG.debug("page client not closed: %s", error)


def attach_extras(
    api: "Api", items: list[dict[str, Any]], abort: Callable[[], bool] = lambda: False
) -> None:
    """A movie's special features travel in its payload: the scanner's
    listings never contact the server, and the movie folder's extras folder
    is built from them. Only a movie whose count says it has any is asked.

    Every path that publishes a movie goes through here -- ``fetch_kind``
    for an enumeration or a catch-up, ``fetch_items`` and ``flush_local``
    for a single re-fetch -- because a payload without its features reads as
    a movie without extras: the token goes empty and Clean, asking
    ``provider.exists`` per file, would drop rows the server still has."""
    for item in items:
        if item.get("Type") != "Movie" or not item.get("SpecialFeatureCount"):
            continue
        if abort():
            raise InterruptedError("enumeration stopped")
        features = api.special_features(item["Id"])
        item["SpecialFeatures"] = [
            metadata.compact_extra(feature)
            for feature in features
            if isinstance(feature, dict) and feature.get("Id") and feature.get("Name")
        ]


def fetch_boxsets(
    api: "Api",
    abort: Callable[[], bool] = lambda: False,
    ids: Optional[Iterable[str]] = None,
) -> list[dict[str, Any]]:
    """Collections with their movie members; sets live outside any library."""
    params: dict[str, Any] = {
        "userId": api.user_id,
        "IncludeItemTypes": "BoxSet",
        "Recursive": True,
        "Fields": FIELDS,
        "EnableTotalRecordCount": True,
    }
    rows: list[Any] = []
    if ids is None:
        page = api.items(params)
        listed = page.get("Items")
        if not isinstance(listed, list) or page.get("TotalRecordCount") != len(listed):
            raise ValueError("incomplete collection listing")
        rows = listed
    else:
        wanted = list(ids)
        for start in range(0, len(wanted), IDS_PER_REQUEST):
            if abort():
                raise InterruptedError("enumeration stopped")
            chunk = ",".join(wanted[start : start + IDS_PER_REQUEST])
            listed = api.items(dict(params, Ids=chunk)).get("Items")
            if not isinstance(listed, list):
                raise ValueError("incomplete collection listing")
            rows.extend(listed)
    result = []
    for boxset in rows:
        if abort():
            raise InterruptedError("enumeration stopped")
        if not isinstance(boxset, dict) or boxset.get("Type") != "BoxSet":
            raise ValueError("invalid collection")
        members = api.items(
            {
                "userId": api.user_id,
                "ParentId": boxset["Id"],
                "IncludeItemTypes": "Movie",
                "Fields": "Etag",
                "EnableTotalRecordCount": True,
            }
        )
        items = members.get("Items")
        if not isinstance(items, list) or members.get("TotalRecordCount") != len(items):
            raise ValueError("incomplete collection membership")
        compacted = metadata.compact(boxset)
        compacted["KofinMembers"] = sorted(
            i["Id"] for i in items if isinstance(i, dict) and i.get("Id")
        )
        result.append(compacted)
    return result


# Seconds before the idle binding backfill is tried again after a failure.
BINDINGS_RETRY = 300.0
# And between two idle attempts to give a held Kodi setting back.
SETTINGS_RETRY = 300.0
# A pass that fails the same way again waits twice as long as the time
# before, from the first to the last of these, unless new work is pending
# (Library.apply).
RETRY_FIRST = 5.0
RETRY_MAX = float(CATCHUP_INTERVAL)


def _signature(error: BaseException) -> str:
    """What makes two failures the same one: the type and the text, less
    the object addresses a transport's message carries (``<HTTPConnection
    object at 0x7f…>``), which differ on every attempt."""
    return re.sub(r"0x[0-9a-fA-F]+", "0x?", "%s: %s" % (type(error).__name__, error))


class Library(threading.Thread):
    def __init__(
        self, api: "Api", player: Optional["Player"], api_factory: Callable[[], "Api"]
    ) -> None:
        super().__init__(name="kofin-api", daemon=True)
        creds = Credentials.load()
        self.store = Store(namespace(creds.server_id, creds.user_id))
        self.progress = progress.Progress()
        self.api = api
        self.player = player
        self.api_factory = api_factory
        self.startup_done = False
        self._reload_owed: set[str] = set()
        self.stop_thread = False
        self._stop_event = threading.Event()
        # (command, data), and a third member on an entry that is a retry.
        self._queue: queue.Queue[tuple[Any, ...]] = queue.Queue()
        self._catchup_due = 0.0
        self._full_due = False
        self._repair = False
        self.changefeed: Any = None
        # Libraries selected while no worker ran, enumerated once each: a
        # library the server no longer lists never reaches the whitelist and
        # must not be retried on every tick ahead of the catch-up.
        self._unsynced_tried: set[str] = set()
        # The library ids the server's last listing named, hidden ones
        # included, and the selected libraries it left out that answered
        # 404 by id, with when they first did (settle_missing).
        self._listed: Optional[set[str]] = None
        self._missing: dict[str, float] = {}
        # Libraries a repair is rebuilding: their rows are leaving Kodi, and
        # nothing is enumerated until they have left (rebuild_stale, refresh).
        self._rebuilding: set[str] = set()
        self._first_attended = False
        # The server's user data for the item this Kodi is playing, kept
        # back until it has stopped (apply_userdata): item id -> the newest
        # entry and when the item was first seen no longer playing.
        self._held_userdata: dict[str, tuple[dict, Optional[float]]] = {}
        self._playlists_due = False
        # When kofin last published to the catalogue, and when the work now
        # pending was first seen (PASS_SETTLE).
        self._published_at = 0.0
        self._pending_since: Optional[float] = None
        # What catch-ups bring that the catalogue did not hold, until the
        # pass has filed it and a toast may go up (announce.Arrivals).
        self.arrivals = announce.Arrivals()
        # When the idle binding backfill is next due: now, then never once
        # it succeeded, or a pause after a failure (apply).
        self._bindings_due = 0.0
        # When a Kodi setting a scan held and Kodi would not take back is
        # next asked for while nothing is pending (apply).
        self._settings_due = 0.0
        # The last pass's failure, how long its retry waits, when that ends,
        # and what was pending then (Library.apply).
        self._failure: Optional[str] = None
        self._failure_delay = 0.0
        self._retry_at = 0.0
        # The tick's own backoff, for a stage (the outbox, a command, the
        # playlists) that fails the same way each time (_note_work_failure).
        self._work_failures: dict[str, float] = {}
        self._work_delay = RETRY_FIRST
        self._work_failed_with: tuple[Any, ...] = ()
        self._failed_with: Optional[tuple[int, int]] = None
        # The failure the last pass raised when it repeated the one before.
        self._repeated: Optional[BaseException] = None

    def stop_client(self) -> None:
        self.stop_thread = True
        self._stop_event.set()

    def workers_alive(self) -> bool:
        return False

    def enqueue_command(self, command: str, data: Any = None) -> None:
        if command in (
            "FastSync",
            "Reconnected",
            "SyncLibrary",
            "UpdateLibrary",
            "RepairLibrary",
            "RemoveLibrary",
            "SyncPlaylists",
            "SyncMusicPlaylists",
            "CleanupMusicPlaylists",
        ):
            self._queue.put((command, data or {}))

    def added(self, ids: Iterable[str]) -> None:
        self._queue.put(("changed", list(ids)))

    updated = added
    artwork = added

    def removed(self, ids: Iterable[str]) -> None:
        self._queue.put(("removed", list(ids)))

    def userdata(self, data: list[Any]) -> None:
        self._queue.put(("userdata", list(data)))

    def refresh_libraries(self) -> None:
        self.enqueue_command("FastSync")

    # -- the loop ----------------------------------------------------------------

    def run(self) -> None:
        monitor = xbmc.Monitor()
        try:
            # One connection to kofin.db for as long as this thread runs: it
            # is the thread that asks the store for work twice a second and
            # the one every pass runs on (private.hold_connections).
            with private.hold_connections():
                self._run(monitor)
        except EarlierLibrary as error:
            apistatus.write_earlier(self.store.namespace)
            LOG.warning("API sync blocked: %s", error)
        except BackendMismatch as error:
            self._status(settings.localized(30420) % str(error))
            LOG.warning("API sync blocked: %s", error)
        except Exception:
            LOG.exception("API video worker stopped")
        finally:
            self.stop_thread = True
            # A stop in the middle of a request leaves nobody to finish its
            # bar: the tick that would have settled it never ran.
            try:
                self._bar().finish()
            except Exception:
                LOG.debug("progress bar not taken down at the stop")

    def _run(self, monitor: xbmc.Monitor) -> None:
        self.store.initialize(self.api.server)
        # A rebuild a stopped service left half done is still one.
        self._rebuilding.update(self.store.rebuilding())
        native = Native(self.store, self._stop_event.is_set, bar=self._bar())
        native.setup()
        # A Kodi stopped mid-scan never gave back the setting the scan was
        # holding (Native.without_actor_thumbs); a pass would, but none may
        # be due.
        try:
            native.restore_settings()
        except Exception:
            LOG.exception("held Kodi settings not restored; the next pass retries")
        self._settings_due = time.monotonic() + SETTINGS_RETRY
        # The applier hears only the changes made while the service runs,
        # and Kodi moves a stored default to a new one as it loads the
        # settings: the switch can read off with playlists still written.
        try:
            self._playlists_due = api_playlists.owed()
        except Exception:
            LOG.exception("playlist state not read; the next enumeration retries")
        self.startup_done = True
        while not self.stop_thread and not monitor.abortRequested():
            failed = False
            try:
                if native.refile_removed():
                    # A removal announces row by row: the pass waits for the
                    # rest of it (PASS_SETTLE).
                    self._published_at = time.monotonic()
            except Exception:
                LOG.exception(
                    "rows Kodi removed not put back; the next complete listing does"
                )
            # Away from the server the pending work is applied before
            # anything asks for it: each stage below can wait out a
            # transport's retries. While the server answers, the stages go
            # first and the pass after them takes what was pending with what
            # they bring, so the work an earlier session left and the
            # catch-up of this one are one pass.
            if not state.is_online():
                try:
                    self.apply(native)
                except InterruptedError:
                    break
                except Exception as error:
                    # A failed native job must not stop a newer server edit
                    # from replacing its payload, or poison jobs never heal.
                    self._log_failure("API native work remains pending", error)
                    failed = True
            # Local delivery and individual events can fail permanently
            # (e.g. an item deleted before its update event is processed).
            # Neither may prevent enumeration from repairing the snapshot.
            for work in (
                self.flush_local,
                self.commands,
                self.release_userdata,
                self.refresh,
                lambda: self.apply(native),
                self.announce_new_content,
                self.playlists_pass,
                self.flush_pending_reload,
            ):
                try:
                    work()
                except InterruptedError:
                    return
                except Exception as error:
                    self._note_work_failure(error)
                    self._log_failure("API video sync will retry", error)
                    self._status(settings.localized(30403))
                    failed = True
            self.settle_progress(failed)
            if failed:
                if self._wait_out_work_failure():
                    break
            else:
                self._work_failures = {}
                self._work_delay = RETRY_FIRST
            if monitor.waitForAbort(0.5):
                break

    def commands(self) -> None:
        failed = False
        # Only visit each queued command once per tick, including failures.
        for _ in range(min(100, self._queue.qsize())):
            entry = self._queue.get_nowait()
            command, data = entry[0], entry[1]
            try:
                self.command(command, data, retry=len(entry) > 2)
            except InterruptedError:
                raise
            except Exception:
                LOG.exception("API video command will retry: %s", command)
                # Marked as a retry: it is not the viewer asking again, and
                # the bar must not come back up for each one while the
                # server is away (settle_progress).
                self._queue.put((command, data, True))
                failed = True
        if failed:
            raise RuntimeError("API video commands remain pending")

    def settle_progress(self, failed: bool = False) -> None:
        """Take the bar down when what the viewer asked for is done: nothing
        queued, nothing to list, nothing pending. A tick that failed takes
        it down too; the retries that follow are not what was asked for
        and may go on for as long as the server is away."""
        bar = self._bar()
        if not bar.attended:
            return
        if failed or not (
            self._queue.qsize()
            or self._full_due
            or self._rebuilding
            or self.store.has_pending()
        ):
            bar.finish()

    def refresh(self) -> None:
        if self._rebuilding:
            if self.store.removing(self._rebuilding):
                # Listed again while its rows are still in Kodi, a library
                # is only compared with them, and they are the old rows.
                return
            self._rebuilding.clear()
        watermark, enumerated = self.store.watermark()
        unsynced = sorted(
            set(settings.get_list("librarySelection"))
            - set(private.get_sync()["Whitelist"])
            - self._unsynced_tried
        )
        if unsynced and enumerated and watermark and not self._full_due:
            # Selected while no worker was running to hear the setting change.
            self._unsynced_tried.update(unsynced)
            self._catchup_due = time.monotonic() + 30
            self._bar().attend()
            self.full_sync(unsynced)
            return
        if (
            self._full_due
            or not enumerated
            or not watermark
            or self._schedule_due(enumerated)
        ):
            if time.monotonic() < self._catchup_due:
                return
            # Advance before the call so failure gets a bounded retry rather
            # than keeping the already-expired deadline on every tick.
            self._catchup_due = time.monotonic() + 30
            if (
                not enumerated
                and not self._first_attended
                and settings.get_list("librarySelection")
            ):
                # The first listing of a profile is its first import, and
                # attended once: a listing that failed is tried again every
                # half minute.
                self._first_attended = True
                self._bar().attend()
            self.full_sync()
            self._full_due = False
            self._catchup_due = time.monotonic() + CATCHUP_INTERVAL
            return
        if time.monotonic() >= self._catchup_due:
            self._catchup_due = time.monotonic() + 30
            stale = self.stale_listings()
            if stale:
                # A library missing from the server's views is skipped by
                # the listing and stays stale for the next catch-up.
                LOG.debug(
                    "listing %d librar%s again for fields their last listing lacked",
                    len(stale),
                    "y" if len(stale) == 1 else "ies",
                )
                self.full_sync(stale)
            self.catch_up()
            # A retention overrun (catch_up) owes the complete listing now.
            self._catchup_due = (
                0.0 if self._full_due else time.monotonic() + CATCHUP_INTERVAL
            )

    def stale_listings(self) -> list[str]:
        """The synced, selected libraries whose last published listing asked
        the server for less than LISTING, or was never recorded."""
        selected = set(settings.get_list("librarySelection"))
        recorded = self.store.listings()
        return sorted(
            library
            for library in private.get_sync()["Whitelist"]
            if library in selected and recorded.get(library) != LISTING
        )

    @staticmethod
    def _schedule_due(enumerated: float) -> bool:
        interval = full_interval()
        return interval is not None and time.time() - enumerated >= interval

    # -- enumeration -----------------------------------------------------------------

    def _supported_views(self) -> dict[str, dict[str, Any]]:
        # Hidden from My Media is the user's home screen setting, never a
        # reason to stop syncing a library.
        views = self.api.views(include_hidden=True).get("Items")
        if not isinstance(views, list):
            raise ValueError("incomplete library listing")
        self._listed = {v["Id"] for v in views if v.get("Id")}
        from kofin.core.api import library_folders

        unlisted = [
            library
            for library in settings.get_list("librarySelection")
            if library not in self._listed
        ]
        grouped, unread = library_folders(self.api, unlisted)
        if unread:
            # A pass without them would move the watermark past their
            # changes. A 404 is not unread, so settle_missing still removes
            # a library the server says is gone.
            raise JellyfinError("selected libraries not read: %s" % ", ".join(unread))
        self._listed |= {folder["Id"] for folder in grouped}
        views = views + grouped
        return {
            v["Id"]: v
            for v in views
            if v.get("Id") and (v.get("CollectionType") or "mixed") in SUPPORTED
        }

    def _status(self, value: str, listing: Iterable[str] = ()) -> None:
        status(value, listing, self.store.namespace)

    def settle_missing(self) -> None:
        """Remove a selected library the server says is gone.

        A library the server's last listing left out is asked for by its
        id: Jellyfin answers 404 for one that was deleted and for one the
        user can no longer see. Two such answers MISSING_CONFIRM apart take
        it out of the selection and out of Kodi, as an untick would, with
        one notification and no question: the server has decided. An error
        or an item that is there after all keeps it, and a listing that
        names it again forgets the first answer. Until it leaves, Library
        status names it.
        """
        if self._listed is None:
            return
        selected = settings.get_list("librarySelection")
        missing = [library for library in selected if library not in self._listed]
        for library in list(self._missing):
            if library not in missing:
                del self._missing[library]
        now = time.monotonic()
        gone = []
        for library in missing:
            try:
                self.api.item(library)
            except HttpError as error:
                if error.status == 404:
                    first = self._missing.setdefault(library, now)
                    if now - first >= MISSING_CONFIRM:
                        gone.append(library)
                continue
            except Exception as error:
                # The server could not say: the library stays.
                LOG.debug("library %s not confirmed: %s", library, error)
                continue
            self._missing.pop(library, None)
        names = self._view_names() if self._missing else {}
        if gone:
            whitelist = {
                entry.replace("Mixed:", "") for entry in private.get_sync()["Whitelist"]
            }
            synced = [library for library in gone if library in whitelist]
            # The whitelist before the selection: the settings applier then
            # finds nothing to confirm in the selection written next.
            if synced:
                self.drop_libraries(synced)
            settings.set_str(
                "librarySelection",
                ",".join(library for library in selected if library not in gone),
            )
            for library in gone:
                del self._missing[library]
                name = names.get(library, library)
                LOG.debug("library %s (%s) is gone from the server", library, name)
                toast.show(settings.localized(30895) % name)
        apistatus.record_missing(
            [names.get(library, library) for library in sorted(self._missing)],
            self.store.namespace,
        )

    @staticmethod
    def _view_names() -> dict[str, str]:
        with private.Database() as db:
            return kofindb.JellyfinDatabase(db.cursor).view_names()

    def _changefeed(self) -> Any:
        """The change feed, or None for a server without a companion; raises
        when the server could not say (changefeed.detect). Taken for none, a
        catch-up reads the save dates, which see no deletion, and moves the
        cursor past the feed's removals."""
        if self.changefeed is None:
            self.changefeed = changefeed.detect(self.api)
            # For the status dialog: a found feed is kept for the thread's
            # life, a missing one is looked for again on every call, and the
            # record moves with the answer.
            feed = self.changefeed
            apistatus.record_feed(
                feed.tier if feed is not None else changefeed.TIER_NONE,
                self.store.namespace,
            )
        return self.changefeed

    def _server_now(self) -> int:
        try:
            feed = self._changefeed()
            if feed is not None:
                now: int = feed.server_now()
                return now
        except Exception as error:
            LOG.warning("server clock unavailable: %s", error)
        # Without a companion the catch-up is MinDateLastSaved against the
        # local clock.
        return int(time.time()) - CATCHUP_OVERLAP

    def _bar(self) -> "progress.Progress":
        """The enumeration's progress bar, made on first use."""
        bar = getattr(self, "progress", None)
        if bar is None:
            bar = self.progress = progress.Progress()
        return bar

    def full_sync(self, libraries: Optional[Iterable[str]] = None) -> None:
        """Enumerate the selected libraries (or the named ones) completely."""
        bar = self._bar()
        try:
            self._full_sync(libraries, bar)
        finally:
            bar.close()
        # The pass that follows says when the update is done; a listing that
        # left it nothing to do ends here. One that failed is the tick's to
        # report.
        if not (self.store.has_pending() or self._repair):
            self._status(xbmc.getLocalizedString(20177))
        else:
            self._status(settings.localized(30401))

    def _full_sync(
        self, libraries: Optional[Iterable[str]], bar: progress.Progress
    ) -> None:
        # Until the first page of the first kind arrives nothing is counted:
        # the libraries are asked for, the server's clock is read.
        bar.working(progress.PREPARING)
        selected = self._selection()
        supported = self._supported_views()
        self.settle_missing()
        # A library being rebuilt is listed when its old rows have left Kodi,
        # whoever asks: refresh waits for that, and a listing asked for by
        # name (SyncLibrary) must not publish it over them either.
        held = {i for i in self._rebuilding if self.store.removing([i])}
        targets = [
            library
            for library in sorted(libraries if libraries is not None else selected)
            if library in supported and library in selected and library not in held
        ]
        complete = libraries is None
        # A listing is minutes of a first import, and until it is published
        # the catalogue has no row of a library selected for the first time.
        whitelist = private.get_sync()["Whitelist"]
        self._status(
            settings.localized(30401),
            listing=[
                supported[library].get("Name", library)
                for library in targets
                if library not in whitelist
            ],
        )
        started = self._server_now()
        fetched: dict[str, list[dict]] = {}
        for library in targets:
            rows: list[dict] = []
            for kind in collection_kinds(supported[library]):
                began = time.monotonic()
                bar.asking(kind)
                found = fetch_kind(
                    self.api,
                    library,
                    kind,
                    self._stop_event.is_set,
                    on_page=functools.partial(bar.track, kind),
                    api_factory=getattr(self, "api_factory", None),
                )
                LOG.debug(
                    "enumerated %d %s in %.1f s",
                    len(found),
                    kind,
                    time.monotonic() - began,
                )
                rows.extend(found)
            fetched[library] = rows
        # The collections, the catalogue and the node tree follow, with
        # nothing to count.
        bar.working(progress.SAVING)
        movies_selected = any(
            "Movie" in collection_kinds(supported[library])
            for library in selected
            if library in supported
        )
        boxsets = (
            fetch_boxsets(self.api, self._stop_event.is_set)
            if movies_selected
            and (
                complete
                or any(
                    "Movie" in collection_kinds(supported[library])
                    for library in targets
                )
            )
            else []
        )
        # Enumeration takes minutes on a real catalogue. A library deselected
        # meanwhile is not published: its RemoveLibrary is already queued, and
        # publishing it here would import every item only to remove it again.
        selected = self._selection()
        committed = [library for library in fetched if library in selected]
        if not committed and not (complete and boxsets):
            if complete:
                # Complete with nothing to publish, and stamped as such:
                # refresh lists the whole profile until it is.
                self.store.set_watermark(
                    watermark=changefeed.unix_to_watermark(started),
                    enumerated=time.time(),
                )
            return
        items: list[dict] = []
        membership: dict[str, str] = {}
        for library in committed:
            for item in fetched[library]:
                if item["Id"] in membership:
                    continue
                membership[item["Id"]] = library
                items.append(item)
        invalidate = self._collection_changes(boxsets, complete)
        began = time.monotonic()
        self.publish(
            items + boxsets,
            settle=False,
            membership=membership,
            complete_libraries=committed,
            complete_boxsets=complete and movies_selected,
        )
        LOG.debug(
            "published %d items in %.1f s",
            len(items) + len(boxsets),
            time.monotonic() - began,
        )
        del items, fetched
        memory.release()
        self.store.invalidate(invalidate)
        # Only what was listed and published: a selected library the server
        # did not show, or one being rebuilt, keeps its old record.
        self.store.remember_listing(committed, LISTING)
        if complete:
            self.store.set_watermark(
                watermark=changefeed.unix_to_watermark(started), enumerated=time.time()
            )
            self._repair = True
        for library in committed:
            state = private.get_sync()
            if library not in state["Whitelist"]:
                state["Whitelist"].append(library)
                if not self.store.has_rows(library):
                    # Nothing of it is in Kodi yet, so every row it gets is
                    # filed by this build's listing.
                    self.store.set_scanner_format(
                        library, metadata.scanner_format(capabilities.features())
                    )
            private.save_sync(state)
            with private.Database() as db:
                kofindb.JellyfinDatabase(db.cursor).remember_view(
                    library,
                    supported[library].get("Name", library),
                    supported[library].get("CollectionType") or "mixed",
                )
        self.publish_selection()
        # The playlists follow the catalogue they point into.
        self._playlists_due = True

    @staticmethod
    def _selection() -> list[str]:
        """The selected libraries, for a listing to rely on. A settings store
        Kodi has unregistered, or a settings document that did not load,
        reads every string blank, so an empty selection counts only beside a
        ``deviceId`` that answers (the settings applier's LOAD_CANARY), and
        the listing fails otherwise: stamped, it would record a listing that
        never ran and move the cursor past every change it was for."""
        selected = settings.get_list("librarySelection")
        if not selected and not settings.get_str("deviceId"):
            raise RuntimeError("library selection not read: settings unavailable")
        return selected

    def _collection_changes(
        self, boxsets: list[dict[str, Any]], complete: bool
    ) -> set[str]:
        """Movies whose one native set changes with these collections."""
        before = {
            r.item_id: set(r.item.get("KofinMembers") or [])
            for r in self.store.records(kind="BoxSet", pinned=False).values()
        }
        after = {b["Id"]: set(b.get("KofinMembers") or []) for b in boxsets}
        affected: set[str] = set()
        for boxset_id, members in after.items():
            affected |= members ^ before.get(boxset_id, set())
        if complete:
            for boxset_id, members in before.items():
                if boxset_id not in after:
                    affected |= members
        return affected

    def _removed_collection_members(self, ids: Iterable[str]) -> set[str]:
        """Movies filed under a collection that is going: their one set changes."""
        boxsets = self.store.records(kind="BoxSet", item_ids=list(ids), pinned=False)
        members: set[str] = set()
        for record in boxsets.values():
            members.update(record.item.get("KofinMembers") or [])
        return members

    def _orphaned(self, removed: Collection[str]) -> list[str]:
        """The albums, and their songs, that a removed artist took with it
        unannounced.

        Deleting an artist's folder, Jellyfin announces the artist's removal
        alone. It deletes the songs below it without a word and keeps each
        album, its parent gone, answering a request for its id though no
        listing holds it, the next library scan's included. So the albums
        whose payload names a removed artist, or a removed item the
        catalogue does not place, as their parent are asked for with their
        songs inside their library, and what the server does not list goes
        with the artist. An album the removal already names is asked for
        too: its removal does not take its songs, which leave only by their
        own.
        """
        if not removed:
            return []
        placed = self.store.placements(removed)
        parents = {
            item_id
            for item_id in removed
            if (entry := placed.get(item_id)) is None or entry.kind == "MusicArtist"
        }
        if not parents:
            return []
        albums: dict[str, list[str]] = {}
        for record in self.store.records(kind="MusicAlbum", pinned=False).values():
            if record.item.get("ParentId") in parents:
                albums.setdefault(record.library, []).append(record.item_id)
        named = set(removed)
        gone: list[str] = []
        for library, album_ids in sorted(albums.items()):
            wanted = album_ids + self.store.placed_in("Audio", library, album_ids)
            listed = self._listed_in(library, wanted)
            gone.extend(i for i in wanted if i not in listed and i not in named)
        if gone:
            LOG.debug(
                "%d album(s) and song(s) of a removed artist the server no longer"
                " lists: removed with it",
                len(gone),
            )
        return gone

    def _listed_in(self, library: str, ids: list[str]) -> set[str]:
        """Which of ``ids`` the server lists inside ``library``."""
        listed: set[str] = set()
        for start in range(0, len(ids), IDS_PER_REQUEST):
            if self._stop_event.is_set():
                raise InterruptedError("item fetch stopped")
            page = self.api.items(
                {
                    "userId": self.api.user_id,
                    "ParentId": library,
                    "Recursive": True,
                    "Ids": ",".join(ids[start : start + IDS_PER_REQUEST]),
                    "EnableImages": False,
                    "EnableUserData": False,
                }
            )
            rows = page.get("Items")
            if not isinstance(rows, list):
                raise ValueError("incomplete item fetch")
            listed.update(
                str(i["Id"]) for i in rows if isinstance(i, dict) and i.get("Id")
            )
        return listed

    def catch_up(self) -> None:
        """Changes since the watermark, on the shared change-feed contract."""
        watermark, _ = self.store.watermark()
        if not watermark:
            self.full_sync()
            return
        supported = self._supported_views()
        self.settle_missing()
        selected = settings.get_list("librarySelection")
        selected = [library for library in selected if library in supported]
        feed = self._changefeed()
        if feed is None:
            self._catch_up_by_date(watermark, selected, supported)
            return
        change_set = feed.changes(watermark, CHANGEFEED_TYPES, selected)
        if changefeed.retention_overrun(
            watermark, change_set.envelope.retention_cutoff
        ):
            LOG.debug("sync queue retention exceeded; scheduling a full enumeration")
            self._full_due = True
        removed = [r.id for r in change_set.records if r.status == "Removed"]
        removed += self._orphaned(removed)
        self.store.invalidate(self._removed_collection_members(removed))
        wanted = {}
        for record in change_set.records:
            if record.status == "Removed":
                continue
            if record.library_ids is not None and not set(record.library_ids) & set(
                selected
            ):
                if self.store.entry(record.id) is None:
                    continue
            wanted[record.id] = record
        items, membership = self._resolve(list(wanted), selected, supported, wanted)
        self.arrivals.published(
            items, self.store.known(i["Id"] for i in items), membership
        )
        self.publish(items, settle=False, membership=membership, removed=removed)
        self.apply_userdata(change_set.userdata, settle=False)
        if change_set.envelope.server_time:
            self.store.set_watermark(
                watermark=changefeed.unix_to_watermark(
                    change_set.envelope.server_time - CATCHUP_OVERLAP
                )
            )

    def _catch_up_by_date(
        self,
        watermark: str,
        selected: Iterable[str],
        supported: dict[str, dict[str, Any]],
    ) -> None:
        started = int(time.time()) - CATCHUP_OVERLAP
        items: list[dict] = []
        membership: dict[str, str] = {}
        for library in sorted(selected):
            for kind in collection_kinds(supported[library]):
                for item in fetch_kind(
                    self.api,
                    library,
                    kind,
                    self._stop_event.is_set,
                    {"MinDateLastSaved": watermark},
                ):
                    if item["Id"] not in membership:
                        membership[item["Id"]] = library
                        items.append(item)
        boxsets: list[dict] = []
        if any("Movie" in collection_kinds(supported[library]) for library in selected):
            changed = self.api.items(
                {
                    "userId": self.api.user_id,
                    "IncludeItemTypes": "BoxSet",
                    "Recursive": True,
                    "MinDateLastSaved": watermark,
                    "Fields": "Etag",
                }
            ).get("Items")
            if isinstance(changed, list):
                boxsets = fetch_boxsets(
                    self.api,
                    self._stop_event.is_set,
                    [b["Id"] for b in changed if isinstance(b, dict) and b.get("Id")],
                )
        invalidate = self._collection_changes(boxsets, False)
        self.arrivals.published(
            items, self.store.known(i["Id"] for i in items), membership
        )
        self.publish(items + boxsets, settle=False, membership=membership)
        self.store.invalidate(invalidate)
        self.store.set_watermark(watermark=changefeed.unix_to_watermark(started))

    def fetch_items(self, ids: Iterable[str]) -> list[dict[str, Any]]:
        """Full DTOs by id; the server lists only what this user may see."""
        result: list[dict] = []
        ids = list(ids)
        for start in range(0, len(ids), IDS_PER_REQUEST):
            if self._stop_event.is_set():
                raise InterruptedError("item fetch stopped")
            chunk = ids[start : start + IDS_PER_REQUEST]
            page = self.api.items(
                {"userId": self.api.user_id, "Ids": ",".join(chunk), "Fields": FIELDS}
            )
            rows = page.get("Items")
            if not isinstance(rows, list):
                raise ValueError("incomplete item fetch")
            result.extend(
                metadata.compact(i)
                for i in rows
                if isinstance(i, dict) and i.get("Id") and i.get("Name")
            )
        attach_extras(self.api, result, self._stop_event.is_set)
        return result

    def _library_of(
        self,
        item: dict[str, Any],
        selected: Collection[str],
        hints: Optional[Iterable[str]] = None,
    ) -> Optional[str]:
        """The selected library an item belongs to, or None."""
        entry = self.store.entry(item["Id"])
        if entry is not None and entry.library in selected:
            return entry.library
        for hint in hints or ():
            if hint in selected:
                return hint
        if item.get("SeriesId"):
            parent = self.store.entry(item["SeriesId"])
            if parent is not None and parent.library in selected:
                return parent.library
        if item.get("AlbumId"):
            parent = self.store.entry(item["AlbumId"])
            if parent is not None and parent.library in selected:
                return parent.library
        if self._stop_event.is_set():
            raise InterruptedError("item placement stopped")
        for ancestor in self.api.ancestors(item["Id"]):
            if isinstance(ancestor, dict) and ancestor.get("Id") in selected:
                found: str = ancestor["Id"]
                return found
        return None

    def _resolve(
        self,
        ids: Iterable[str],
        selected: Collection[str],
        supported: dict[str, dict[str, Any]],
        hints: Optional[dict[str, changefeed.ChangeRecord]] = None,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        """Fetch changed items and place each in its selected library."""
        items = []
        membership: dict[str, str] = {}
        boxsets = []
        for item in self.fetch_items([i for i in ids]):
            kind = item.get("Type")
            if kind == "BoxSet":
                boxsets.append(item["Id"])
                continue
            if kind not in (
                "Movie",
                "Series",
                "Season",
                "Episode",
                "MusicVideo",
                "MusicArtist",
                "MusicAlbum",
                "Audio",
            ):
                continue
            hint = hints.get(item["Id"]) if hints else None
            library = self._library_of(
                item, selected, hint.library_ids if hint is not None else None
            )
            if library is None:
                continue
            view = supported.get(library)
            if view is None or kind not in collection_kinds(view):
                continue
            membership[item["Id"]] = library
            items.append(item)
        if boxsets:
            sets = fetch_boxsets(self.api, self._stop_event.is_set, boxsets)
            self.store.invalidate(self._collection_changes(sets, False))
            items.extend(sets)
        return items, membership

    def _playing(self) -> str:
        """The item this Kodi is playing through kofin, or ''."""
        item = self.player.current_item() if self.player is not None else None
        return str((item or {}).get("Id") or "")

    def apply_userdata(self, data: list[Any], settle: bool = True) -> None:
        """Merge the server's user data into the catalogue, except for the
        item this Kodi is playing. ``settle`` as for ``publish``.

        Kodi's player owns the row of what it plays. That something came
        for it is kept, and the entry the server sends when the playback
        stops is applied in its place; when none comes, the server is asked
        a while after the stop (release_userdata).
        """
        playing = self._playing()
        items = []
        settled = []
        for entry in data:
            item_id = entry.get("ItemId") if isinstance(entry, dict) else entry
            if not item_id:
                continue
            if isinstance(entry, dict) and item_id == playing:
                self._held_userdata[item_id] = (entry, None)
                continue
            settled.append(item_id)
            item = self.store.item(item_id)
            if item is None:
                continue
            item["UserData"] = dict(item.get("UserData") or {}, **entry)
            items.append(item)
        if items:
            self.store.publish(items)
            if settle:
                self._published_at = time.monotonic()
        # Only now. A release has no queue behind it: dropped before a
        # publish that failed, its entry was gone for good.
        for item_id in settled:
            self._held_userdata.pop(item_id, None)

    def publish(
        self, items: list[dict[str, Any]], settle: bool = True, **placement: Any
    ) -> None:
        """Publish full items as the server sent them, all but the user data
        of the item this Kodi is playing, which is held like an entry sent
        for it (apply_userdata) while the item keeps what the catalogue has.

        ``settle`` has the next pass wait for more of the same change
        (PASS_SETTLE): an event or an edit's re-read can be followed by the
        server's echo of it. A listing or a catch-up is an answer as of one
        moment, and nothing follows it.
        """
        playing = self._playing()
        if playing:
            for item in items:
                if item.get("Id") != playing:
                    continue
                known = self.store.item(playing)
                if known is not None and isinstance(item.get("UserData"), dict):
                    self._held_userdata[playing] = (
                        dict(item["UserData"], ItemId=playing),
                        None,
                    )
                    item["UserData"] = known.get("UserData") or {}
                break
        self.store.publish(items, **placement)
        if settle:
            self._published_at = time.monotonic()

    def announce_new_content(self) -> None:
        """Announce what the pass filed of the new content catch-ups brought."""
        self.arrivals.flush(self.store, self.api, self.player)

    def release_userdata(self) -> None:
        """Once an item has stopped and the server has had time to settle
        the play, ask it what the play made of the item.

        The last entry heard may be a progress report, and the entry the
        stop sent may never arrive.
        """
        if not self._held_userdata:
            return
        playing = self._playing()
        now = time.monotonic()
        due = []
        for item_id, (entry, stopped) in list(self._held_userdata.items()):
            if item_id == playing:
                self._held_userdata[item_id] = (entry, None)
            elif stopped is None:
                self._held_userdata[item_id] = (entry, now)
            elif now - stopped >= HELD_USERDATA_GRACE:
                due.append(item_id)
        if not due:
            return
        try:
            page = self.api.items({"userId": self.api.user_id, "Ids": ",".join(due)})
            rows = page.get("Items")
            if not isinstance(rows, list):
                raise ValueError("incomplete item fetch")
        except Exception as error:
            # Held, and asked again a grace period on: the server may stay
            # away for as long as it likes, and this is no failure of a tick.
            LOG.debug("user data of %d finished play(s) not read: %s", len(due), error)
            for item_id in due:
                self._held_userdata[item_id] = (self._held_userdata[item_id][0], now)
            return
        fresh = {
            row["Id"]: dict(row.get("UserData") or {}, ItemId=row["Id"])
            for row in rows
            if isinstance(row, dict) and row.get("Id")
        }
        for item_id in due:
            if item_id not in fresh:
                # The server no longer lists it; its removal is another path's.
                self._held_userdata.pop(item_id, None)
        # apply_userdata drops each from the held set once it is published.
        self.apply_userdata([fresh[item_id] for item_id in due if item_id in fresh])

    def publish_selection(self) -> None:
        """The selection moved: the node tree and the skin entries follow it."""
        whitelist = private.get_sync()["Whitelist"]
        with private.Database() as db:
            views = kofindb.JellyfinDatabase(db.cursor).view_names()
        names = [
            name
            for key, name in sorted(views.items(), key=lambda kv: kv[1])
            if key in whitelist
        ]
        LOG.debug("synced libraries: %s", ", ".join(names) or "none")
        try:
            from kofin.sync.dynamic import publish_from

            publish_from(self.api)
        except Exception:
            LOG.exception("library nodes not republished")

    # -- commands ----------------------------------------------------------------------

    def drop_libraries(self, libraries: Iterable[str]) -> None:
        """Tombstone every item of these libraries and take them off the
        whitelist; the next pass removes their rows.

        A library is named by its id or by an entry the whitelist still
        stores as ``Mixed:<id>``. Its items are filed under the bare id, so
        both spellings tombstone the same items and take every entry of
        either spelling off the whitelist."""
        for library in dict.fromkeys(i.replace("Mixed:", "") for i in libraries):
            self.store.publish([], library=library)
            state = private.get_sync()
            state["Whitelist"] = [
                i for i in state["Whitelist"] if i.replace("Mixed:", "") != library
            ]
            private.save_sync(state)
        self.publish_selection()
        # The playlists of a side whose last library left are pruned
        # by the next pass (backends/api/playlists.reconcile).
        self._playlists_due = True

    def rebuild_stale(self, picked: Iterable[str]) -> list[str]:
        """Remove the rows of every picked video library filed under an
        older scanner format, so the enumeration that follows imports them
        again; returns those libraries.

        What the format numbers (metadata.SCANNER_FORMAT) has no setter, so
        a row filed without it gets it only by being filed again, and
        removing the rows and scanning the root is a first import, far
        cheaper than a refresh per row. It is the viewer's to ask for, never
        a pass's: the library is gone from Kodi until the import has run. A
        music library has no such rows and is repaired by comparison.
        """
        whitelist = private.get_sync()["Whitelist"]
        with private.Database() as db:
            media = {
                view.view_id: view.media_type
                for view in kofindb.JellyfinDatabase(db.cursor).views()
            }
        # The format this Kodi's listing reaches: a library filed at a lower
        # one is stale here, never one filed at the format this Kodi lacks.
        current = metadata.scanner_format(capabilities.features())
        stale = [
            library
            for library in sorted(picked or whitelist)
            if library in whitelist
            and media.get(library) != "music"
            and self.store.scanner_format(library) < current
        ]
        rebuild = [library for library in stale if self.store.has_rows(library)]
        for library in stale:
            if library not in rebuild:
                # Nothing was ever filed for it; whatever comes is current.
                self.store.set_scanner_format(library, current)
        if rebuild:
            LOG.debug(
                "repair: %d library(ies) filed before scanner format %d;"
                " their rows are removed and imported again: %s",
                len(rebuild),
                current,
                ", ".join(rebuild),
            )
            # Recorded before the rows are tombstoned: a service stopped
            # between the two must not list the library over its old rows.
            for library in rebuild:
                self.store.set_scanner_format(library, REBUILDING)
            # And off the whitelist before a row is tombstoned: a service
            # stopped after this write leaves it selected and not synced,
            # listed again over the rows it still has, and still asking for
            # its repair.
            state = private.get_sync()
            state["Whitelist"] = [i for i in state["Whitelist"] if i not in rebuild]
            private.save_sync(state)
            self.drop_libraries(rebuild)
            self._rebuilding.update(rebuild)
        return rebuild

    def command(self, command: str, data: Any, retry: bool = False) -> None:
        if command in ATTENDED and not retry:
            self._bar().attend()
            # The viewer asked: the next pass runs now, failing or not.
            self._failure = self._repeated = None
        if command == "RemoveLibrary":
            self.drop_libraries([i for i in data.get("Id", "").split(",") if i])
            return
        if command == "removed":
            removed = list(data) + self._orphaned(data)
            self.store.invalidate(self._removed_collection_members(removed))
            self.store.publish([], removed=removed)
            return
        if command == "userdata":
            self.apply_userdata(data)
            return
        if command == "changed":
            known = [i for i in data if self.store.entry(i) is not None]
            if len(known) < len(data):
                # A new item: its library is the catch-up's to decide.
                self._catchup_due = 0
            if known:
                selected = settings.get_list("librarySelection")
                items, membership = self._resolve(
                    known, selected, self._supported_views()
                )
                if items:
                    self.publish(items, membership=membership)
            return
        if command == "SyncLibrary":
            if not self.store.watermark()[1]:
                # Nothing has ever been listed whole, so the refresh that
                # follows in this tick lists every selected library, this
                # one among them.
                self._full_due = True
                self._catchup_due = 0
                return
            self.full_sync([i for i in data.get("Id", "").split(",") if i])
            return
        if command == "SyncPlaylists":
            playlist_id = (data or {}).get("Id") or ""
            if playlist_id:
                if api_playlists.apply(self.api, self.store, playlist_id) is None:
                    # The whole pass is owed until the switch can be read.
                    self._playlists_due = True
                self.reconcile_subscriptions(playlist_id)
            else:
                self._playlists_due = True
            return
        if command in ("SyncMusicPlaylists", "CleanupMusicPlaylists"):
            # Queued by the switch going on or off: the playlists pass
            # writes or removes the files by the switch as it reads then.
            self._playlists_due = True
            return
        if command == "FastSync":
            self._catchup_due = 0
            return
        if command == "Reconnected":
            # The server that came back may have gained or lost a companion
            # (a plugin install is a server restart), and a found feed is
            # otherwise kept for the thread's life: the catch-up that runs
            # now detects it again, and the status row moves with it.
            self.changefeed = None
            self._catchup_due = 0
            return
        rebuilt = (
            self.rebuild_stale([i for i in (data or {}).get("Id", "").split(",") if i])
            if command == "RepairLibrary"
            else []
        )
        self._full_due = True
        self._catchup_due = 0
        # A rebuild's first pass only removes; the pass after the complete
        # enumeration that follows is the repair (full_sync).
        self._repair = self._repair or (command == "RepairLibrary" and not rebuilt)

    # -- native application -----------------------------------------------------------

    def _settling(self) -> bool:
        """Whether the pending work waits for more of the same change."""
        now = time.monotonic()
        if self._pending_since is None:
            self._pending_since = now
        recent = now - self._published_at < PASS_SETTLE or not self._queue.empty()
        return recent and now - self._pending_since < PASS_SETTLE_MAX

    def _log_failure(self, message: str, error: BaseException) -> None:
        """The whole failure the first time, with a catch-up soon, since a
        server change the work needed may be behind it; a line once it
        repeats, when a catch-up does nothing for it."""
        if error is not self._repeated:
            LOG.exception(message)
            self._catchup_due = min(self._catchup_due, time.monotonic() + 30)
            return
        LOG.debug(
            "%s, the same way again; next try in %.0f s unless new work arrives: %s",
            message,
            self._failure_delay,
            error,
        )

    def _note_work_failure(self, error: BaseException) -> None:
        """A tick's stage failed: the same failure again waits twice as long
        before the next try, up to the catch-up interval, and is logged whole
        only the first time (_log_failure reads ``_repeated``). Failures are
        told apart by signature, so two stages failing in turn (the outbox
        every tick, the catch-up when it is due) each keep their own count
        and the tick waits for the longer."""
        signature = _signature(error)
        repeated = signature in self._work_failures
        delay = (
            min(self._work_failures[signature] * 2, RETRY_MAX)
            if repeated
            else RETRY_FIRST
        )
        self._work_failures[signature] = delay
        self._work_delay = max(self._work_failures.values())
        self._failure_delay = self._work_delay
        self._repeated = error if repeated else None
        self._work_failed_with = self._work_signature()

    def _work_signature(self) -> tuple[Any, ...]:
        """What a stage could have new to do: the pending rows, the outbox
        and the command queue. A change in any is tried at once."""
        try:
            return (
                self.store.pending_signature(),
                len(self.store.local_pending()),
                self._queue.qsize(),
            )
        except Exception:
            return (None, None, self._queue.qsize())

    def _wait_out_work_failure(self) -> bool:
        """Wait the failure's delay in one-second steps, ending early for
        new work; True when the thread was told to stop."""
        deadline = time.monotonic() + self._work_delay
        while time.monotonic() < deadline:
            if self._stop_event.wait(1):
                return True
            if self._work_signature() != self._work_failed_with:
                return False
        return False

    def _note_failure(self, error: BaseException) -> None:
        signature = _signature(error)
        repeated = signature == self._failure
        self._failure_delay = (
            min(self._failure_delay * 2, RETRY_MAX) if repeated else RETRY_FIRST
        )
        self._failure = signature
        self._retry_at = time.monotonic() + self._failure_delay
        self._failed_with = self.store.pending_signature()
        self._repeated = error if repeated else None

    def _waiting_out_failure(self) -> bool:
        """Whether the pending work is what the last pass failed on and its
        retry is not due: a pass that fails the same way each time is tried
        less often, and new work is tried at once."""
        if self._failure is None or time.monotonic() >= self._retry_at:
            return False
        return self.store.pending_signature() == self._failed_with

    def apply(self, native: Native) -> None:
        pending = self.store.has_pending()
        if not pending:
            self._pending_since = None
            if not self._repair:
                # A repair still owed is retried below, and its wait needs
                # the failure; the pass that succeeds clears it.
                self._failure = self._repeated = None
        elif not self._repair and self._settling():
            return
        if (pending or self._repair) and self._waiting_out_failure():
            return
        if pending or self._repair:
            self._pending_since = None
            self._status(settings.localized(30401))
            populated = {kind: self.store.populated(kind) for kind in HAS_CONTENT}
            began = time.monotonic()
            try:
                native.reconcile(repair=self._repair)
                LOG.debug("native pass done in %.1f s", time.monotonic() - began)
            except InterruptedError:
                raise
            except Exception as error:
                self._note_failure(error)
                raise
            else:
                self._failure = self._repeated = None
            finally:
                # A home widget whose last fetch found nothing is deaf to
                # every later library announcement, and the skin's widget
                # sections bake their Library.HasContent gate at window load.
                # Only a skin reload shows content that arrived into an empty
                # library, so the empty -> populated transition owes one.
                for kind, before in populated.items():
                    if not before and self.store.populated(kind):
                        self._reload_owed.add(kind)
            self._repair = False
            self._status(xbmc.getLocalizedString(20177))
            # The playlists and the skin's reload follow, counting nothing.
            self._bar().working(progress.WAITING)
            self.flush_pending_reload()
        elif time.monotonic() >= self._bindings_due:
            # Nothing pending, so no pass: the movie folders an older
            # profile's rows never had bound are bound here, once per
            # service generation (Native.bind_movie_folders); a failure
            # (Kodi's RPC away) is retried after a pause, not every tick.
            try:
                native.bind_movie_folders()
            except Exception:
                LOG.exception("movie folder bindings not completed")
                self._bindings_due = time.monotonic() + BINDINGS_RETRY
            else:
                self._bindings_due = float("inf")
        elif native.settings_owed and time.monotonic() >= self._settings_due:
            # A pass gives a held setting back when it starts, and none may
            # come for hours: the user's "Download actor thumbnails" must
            # not stay off for that long because one call was refused.
            self._settings_due = time.monotonic() + SETTINGS_RETRY
            native.restore_settings()

    def playlists_pass(self) -> None:
        """Rewrite the managed playlist files after an enumeration or a
        request, once the pass has filed the rows they point at."""
        if not self._playlists_due:
            return
        self._playlists_due = False
        try:
            stats = api_playlists.reconcile(self.api, self.store)
        except Exception:
            LOG.exception("playlists not reconciled; next enumeration retries")
        else:
            if stats is None:
                # Owed until the settings can say which way the switch is.
                self._playlists_due = True
                return
            if stats:
                LOG.debug("playlists reconciled: %s", stats)
        self.reconcile_subscriptions()

    def reconcile_subscriptions(self, playlist_id: str = "") -> None:
        """Bring the music-library and playlist download subscriptions to the
        server's listing: one playlist's when a request names it, every
        subscription's after a complete enumeration and when the viewer
        subscribes."""
        from kofin.downloads import subscriptions

        try:
            if playlist_id:
                subscriptions.reconcile_playlist_direct(self.api, playlist_id)
            else:
                subscriptions.reconcile_music_libraries(self.api)
                subscriptions.reconcile_playlists_direct(self.api)
        except Exception:
            LOG.exception("download subscriptions not reconciled")

    def flush_pending_reload(self) -> None:
        """Fire the owed first-content skin reload once nothing is playing."""
        if not self._reload_owed:
            return
        if self.player is not None and self.player.isPlayingVideo():
            # A reload rebuilds the OSD under the viewer; the tick retries.
            return
        monitor = xbmc.Monitor()
        # The scan cycle re-samples Kodi's cached HasContent bool; a reload
        # against the stale value becomes right only on the next one.
        for kind in sorted(self._reload_owed):
            flag = "Library.HasContent(%s)" % HAS_CONTENT[kind]
            for _ in range(40):
                if xbmc.getCondVisibility(flag):
                    break
                if monitor.waitForAbort(0.25):
                    return
            else:
                LOG.warning("%s did not flip; reloading anyway", flag)
        self._reload_owed.clear()
        LOG.debug("first content synced; reloading skin for home widgets")
        xbmc.executebuiltin("ReloadSkin()")

    def flush_local(self) -> None:
        """Tell the server what was marked or played in Kodi.

        Each edit on its own: an edit of an item the server does not have
        (404) is dropped, and any other failure is raised once the rest have
        been delivered. A write that cannot reach the server, or that the
        server refuses for the account, is raised at once: every edit behind
        it would fail alike, and they wait for the next round.
        """
        failure: Optional[Exception] = None
        for item_id, values in self.store.local_pending():
            if self._stop_event.is_set():
                raise InterruptedError("play state delivery stopped")
            written = False
            try:
                self._write_local(item_id, values)
                written = True
                self._read_back_local(item_id, values)
            except InterruptedError:
                raise
            except (ServerUnreachable, Unauthorized) as error:
                if not written:
                    raise
                failure = failure or error
            except HttpError as error:
                if error.status == 404:
                    LOG.debug(
                        "play state of %s not sent: the server no longer has it",
                        item_id,
                    )
                    self.store.local_done(item_id, values)
                    continue
                failure = failure or error
            except Exception as error:
                failure = failure or error
        if failure is not None:
            raise failure

    def _write_local(self, item_id: str, values: dict[str, Any]) -> None:
        payload: dict[str, Any] = {}
        if "playcount" in values:
            # The watched mark and never the count: the server and Kodi each
            # count their own plays.
            payload["Played"] = values["playcount"] > 0
        if "position" in values:
            payload["PlaybackPositionTicks"] = int(values["position"] * 10000000)
        # The partial setter is idempotent across an interrupted reply;
        # MarkPlayed would increment the server count again on retry.
        self.api.update_user_data(item_id, payload)

    def _read_back_local(self, item_id: str, values: dict[str, Any]) -> None:
        # Re-fetch the authoritative full DTO before acknowledging the
        # local outbox; a failed read remains replayable.
        item = metadata.compact(self.api.item(item_id))
        attach_extras(self.api, [item], self._stop_event.is_set)
        if self.store.entry(item_id) is not None:
            self.publish([item])
        self.store.local_done(item_id, values)
