"""Confirmed native operations for every kind through Kodi's public
interfaces.

An accepted RPC is never a commit: every write is confirmed by reading the
owned row back (``readback``), removals wait for that confirmation
(``removal``) and patches go only where the scanner's row differs
(``patch``). This module owns the gates, the waits, the bindings and the
scans, and runs one pass in ``reconcile``.

Music is scanned by directory, a plan of them a part at a time. Which
directories, in which order and under what bar is ``musicpass`` and
``walk``; the scanner they drive is here.
"""

import json
import time
from collections import abc
from contextlib import contextmanager
from collections.abc import Callable, Collection, Iterable, Iterator
from typing import Any, NamedTuple, Optional, TypeVar

import xbmc

from kofin.core import memory, settings, state
from kofin.core.log import Logger
from kofin.sync.catalogue import BackendMismatch, EarlierLibrary
from . import capabilities, metadata, paths, progress, removal
from .kinds import MUSIC_FIRST, ORDER, rpc, rpc_batch
from .musicpass import MusicPass
from .patch import PRELOAD_ALL_MAPPINGS, Applier
from .readback import Readback
from .records import PayloadWindow, Record
from .store import Entry, PendingWork, Placements, Store

LOG = Logger(__name__)

T = TypeVar("T")

# A pass scans a movies root once instead of the missing movies' folders by
# name when at least this share of the library is missing.
ROOT_SCAN_SHARE = 0.5
# The most shows a pass scans by their own folders for new episodes; past
# it the library's root is scanned once. Each folder is a scan of its own: a
# call, a wait for the scanner and an announcement to the home widgets.
SHOW_FOLDER_SCANS = 5
# A hold is renewed before the provider's own limit on it runs out.
HOLD_RENEW = 480.0
ACTOR_THUMBS_SETTING = "videolibrary.actorthumbs"
# A video scan expected to file at least this many rows runs with Kodi's
# "Download actor thumbnails" off (Native.without_actor_thumbs).
ACTOR_THUMBS_FLOOR = 100
# The profile has had every movie folder bound with noupdate
# (Native.bind_movie_folders); a hidden string setting, since the store
# does not record a binding's flag. EXTRAS_BINDINGS_STATE follows it once the
# extras folders of the movies filed before they were bound are bound too.
MOVIE_BINDINGS_SETTING = "apiMovieBindings"
MOVIE_BINDINGS_STATE = "noupdate"
EXTRAS_BINDINGS_STATE = "noupdate+extras"
SCAN_POLL = 3.0  # seconds between reads of Kodi's row count during a scan
# The rows an earlier Kofin filed, as the listings that can hold them and
# the rule that picks them out: the add-on's plugin URL, and for a song of
# the SQL build also the server's stream URL. Native.setup refuses to import
# beside them. An episode has a show and an album or an artist has songs, so
# those listings are not asked.
KOFIN_FILED = {
    "field": "path",
    "operator": "startswith",
    "value": "plugin://plugin.video.kofin/",
}
SQL_STREAMED = {
    "and": [
        {"field": "path", "operator": "contains", "value": "/Audio/"},
        {"field": "filename", "operator": "startswith", "value": "stream."},
        {"field": "filename", "operator": "contains", "value": "static=true"},
    ]
}


def _under(prefix: str) -> dict[str, Any]:
    return {"field": "path", "operator": "startswith", "value": prefix}


LEFTOVERS = (
    ("VideoLibrary.GetMovies", KOFIN_FILED),
    ("VideoLibrary.GetTVShows", KOFIN_FILED),
    ("VideoLibrary.GetMusicVideos", KOFIN_FILED),
    ("AudioLibrary.GetSongs", KOFIN_FILED),
    ("AudioLibrary.GetSongs", SQL_STREAMED),
)
# A directory that is not there. Scanned, it is skipped at once and the scan
# still ends with the announcement home widgets listen for (library_event).
NOWHERE = "special://temp/kofin-no-such-directory/"


# The media types of the rows a library clear counts (removal.COUNTED), as
# Kodi names them in VideoLibrary.OnRemove.
REMOVED_TYPES = frozenset(("movie", "episode", "musicvideo"))
# The kind of the item filed on a row of each media type OnRemove names.
REMOVED_KINDS = {
    "movie": "Movie",
    "tvshow": "Series",
    "episode": "Episode",
    "musicvideo": "MusicVideo",
}


class Monitor(xbmc.Monitor):
    def __init__(self) -> None:
        super().__init__()
        self.finished = 0
        self.music_finished = 0
        self.cleaned = 0
        self.music_cleaned = 0
        # Movies, episodes and music videos Kodi has announced removing.
        self.removed = 0
        # (kind, Kodi id) of the rows Kodi has announced removing since the
        # library thread last took them (Native.refile_removed). Callbacks
        # run on the thread that made the monitor, which is that thread.
        self.lost: set[tuple[str, int]] = set()

    def onNotification(self, sender: str, method: str, data: str) -> None:
        if method != "VideoLibrary.OnRemove":
            return
        try:
            announced = json.loads(data)
            media = announced.get("type")
            kodi_id = announced.get("id")
        except (TypeError, ValueError, AttributeError):
            return
        if media in REMOVED_TYPES:
            self.removed += 1
        kind = REMOVED_KINDS.get(media)
        if kind is not None and isinstance(kodi_id, int):
            self.lost.add((kind, kodi_id))

    def onScanFinished(self, library: str) -> None:
        if library.lower() == "video":
            self.finished += 1
        elif library.lower() == "music":
            self.music_finished += 1

    def onCleanFinished(self, library: str) -> None:
        if library.lower() == "video":
            self.cleaned += 1
        elif library.lower() == "music":
            self.music_cleaned += 1


class VideoScan(NamedTuple):
    """What a pass has Kodi's video scanner list (Native.plan_video)."""

    directories: list[str]
    # Rows the scan of each directory is to file, for Kodi's own count.
    expected: dict[str, int]
    # (item id, generation, user data) of what the scanner is about to file.
    expectations: list[tuple[str, int, dict]]
    # Movie folders scanned by name: bound without noupdate for the scan
    # and with it afterwards (bind_folders).
    movie_folders: list[str]


# Passes a previous account's removal gets while each confirms more than the last.
RETIRE_PASSES = 3


class Native:
    SCAN_POLL = SCAN_POLL

    def __init__(
        self,
        store: Store,
        abort: Callable[[], bool] = lambda: False,
        bar: Optional[progress.Progress] = None,
    ) -> None:
        self.store = store
        self.key = store.namespace
        self.abort = abort
        self.monitor = Monitor()
        self.separator = metadata.item_separator()
        self.readback = Readback(self.key)
        # What this Kodi offers beyond the baseline, read once per pass
        # (capabilities.features) and handed to everything that shapes a
        # request or a desired state by it.
        self.features: frozenset[str] = frozenset()
        self._async_pending = False
        self.payloads = PayloadWindow(self.store)
        # The library thread's own bar when it made this pass (one bar from
        # a viewer's request to the end of the work), else one of its own.
        self.progress = bar if bar is not None else progress.Progress()
        self._server = ""
        # The pass's music work and what it reads once for it; a new one
        # for every pass (reconcile).
        self.music = MusicPass(self)
        # Which music libraries owe a compare of every song
        # (MusicPass.check_due). ``music_sweep``: every library does, but
        # those in ``music_checked``, since a repair or a music scan or
        # clean that was not the pass's own (note_music_changes).
        # ``music_owed``: a library a pass left a directory of unread
        # (MusicPass.finish). All start clear: a service start does not
        # compare every song.
        self.music_checked: set[str] = set()
        self.music_sweep = False
        self.music_owed: set[str] = set()
        # The music scans and cleans heard on the monitor so far, the scans
        # of the pass's own not yet matched to one of them, and this pass's
        # directory scans per library, which count as its own only once their
        # directories have been checked for lost songs (note_music_changes,
        # credit_music_scans).
        self._music_heard = 0
        self._own_music_scans = 0
        self._unchecked_scans: dict[str, int] = {}
        # scanner -> when the hold on it was taken.
        self._held: dict[str, float] = {}
        # Movie folders this pass scans for extras: their extras folder is
        # listed through Kodi just before the scan (_prepare_scan).
        self._extras_folders: set[str] = set()
        # library -> the episodes a pass that did not complete had the
        # scanner file from their shows' own folders (_show_directories).
        self._folder_scanned: dict[str, set[str]] = {}
        # Rows a refresh of the pass's replaced, by (kind, old Kodi id): Kodi
        # announces the old row's removal, and its number can come back as
        # the new row's (refile_removed).
        self.replaced: set[tuple[str, int]] = set()
        # A held Kodi setting is still to be given back (restore_settings),
        # and the ones whose refusal has been said.
        self.settings_owed = False
        self._refused_settings: set[str] = set()

    # -- gates ---------------------------------------------------------------

    def setup(self) -> None:
        """The first-run gate: no sync into a profile that still holds what
        an earlier Kofin filed.

        Those rows are in no catalogue, so an import beside them files every
        item twice and nothing would ever remove the first copy. They are
        told by where they are filed (LEFTOVERS), and they are all the gate
        refuses: a row that is not this catalogue's by its URL and unique id
        (Readback.owns) is never read as ours, patched or removed. What Kodi
        keeps by name is shared: a set of the same title, an artist of the
        same name.
        """
        owner = self.store.prepared()
        if owner and owner != self.key:
            self.retire(owner)
            return
        if owner == self.key:
            return
        own = 0
        for method, rule in LEFTOVERS:
            total = self._filed(method, rule)
            if not total:
                continue
            if rule is SQL_STREAMED:
                raise EarlierLibrary(
                    "Kodi still holds a library an earlier Kofin filed"
                )
            # Rows under the provider root are this build's: this profile's
            # own, when their key is this account's (a catalogue lost with
            # Kodi's rows kept), and the import files them again in place.
            # Another key's rows are another account's, which no catalogue
            # here can take out; anything else under the plugin root is the
            # SQL build's.
            native = self._filed(method, _under(paths.BASE))
            mine = self._filed(method, _under(paths.root(self.key)))
            if total - native:
                raise EarlierLibrary(
                    "Kodi still holds a library an earlier Kofin filed"
                )
            if native - mine:
                raise BackendMismatch(
                    "Kodi holds a library of another account; log in as that "
                    "account to remove it, or use a fresh profile"
                )
            own += mine
        if own:
            LOG.warning(
                "%d rows this profile filed before its catalogue was lost; "
                "importing over them",
                own,
            )
        self.store.prepare_empty()

    def retire(self, owner: str) -> None:
        """Another account owns the catalogue: its libraries leave Kodi before
        this one's sync starts, and the catalogue is then this account's.

        The previous account's rows are keyed to its namespace, so nothing
        this account syncs could own or remove them, and a row under the
        add-on's root that no catalogue names would be read as an earlier
        Kofin's by the gate. Every library of the owner's catalogue is
        tombstoned and a pass of the owner's own removes and confirms the
        rows, with this pass's bar; what that pass could not remove keeps the
        catalogue the owner's, and sync off, with the reason.
        """
        old = Store(owner)
        other = Native(old, self.abort, bar=self.progress)
        for library in old.all_libraries():
            old.publish([], library=library)
        # Its collections too: a set whose last movie left before the
        # switch is still an empty row of Kodi's to take out.
        old.publish([], complete_boxsets=True)
        # A removal is confirmed by a readback, and a music directory's by the
        # scan that re-listed it: a pass that confirms some rows and not the
        # rest is run again while it makes progress.
        left = old.unfinished_removals()
        for _ in range(RETIRE_PASSES):
            if not left or self.abort():
                break
            try:
                other.reconcile()
            except Exception as error:
                LOG.warning("the previous account's removal did not finish: %s", error)
            still = old.unfinished_removals()
            if still >= left:
                left = still
                break
            left = still
        if left or old.all_libraries():
            raise BackendMismatch(
                "the previous account's library could not be removed from Kodi "
                "(%d rows still to confirm); retry, or use a fresh profile" % left
            )
        self.store.adopt(owner)

    @staticmethod
    def _filed(method: str, rule: dict[str, Any]) -> int:
        """How many rows ``method`` lists under ``rule``: one row and the
        count, never a zero-width page (_count)."""
        reply = rpc(method, {"filter": rule, "limits": {"start": 0, "end": 1}})
        if not isinstance(reply, dict) or not isinstance(
            reply.get("limits", {}).get("total"), int
        ):
            raise RuntimeError(
                "cannot tell whether an earlier Kofin library is in Kodi"
            )
        return int(reply["limits"]["total"])

    # -- waits ---------------------------------------------------------------

    def _idle(self, scanner: str = "video") -> bool:
        if scanner == "music":
            return not xbmc.getCondVisibility("Library.IsScanningMusic")
        if scanner == "any":
            return self._idle("video") and self._idle("music")
        return not xbmc.getCondVisibility("Library.IsScanningVideo")

    def _scanning(self, scanner: str = "video") -> bool:
        return not self._idle(scanner)

    def wait(
        self,
        predicate: Callable[[], T],
        timeout: float = 60,
        busy: Callable[[], bool] = lambda: False,
        on_poll: Optional[Callable[[], None]] = None,
    ) -> T:
        """``timeout`` is idle time: the deadline moves while ``busy`` holds.

        ``on_poll`` runs once a loop, for a bar that reads progress off Kodi.
        """
        deadline = time.monotonic() + timeout
        while True:
            if self.abort() or self.monitor.waitForAbort(0.1):
                raise InterruptedError("native operation interrupted")
            value = predicate()
            if value:
                return value
            if on_poll is not None:
                on_poll()
            if busy():
                deadline = time.monotonic() + timeout
            elif time.monotonic() >= deadline:
                raise TimeoutError("native operation did not converge")

    def pump(self) -> None:
        """Run the callbacks Kodi has queued for this thread.

        Kodi queues one for every announcement on every Monitor object, and
        they leave the queue only when the thread that made the object waits
        on Kodi. The pass's setters announce every row they write, so a burst
        takes its own callbacks off as it goes. One millisecond, since a zero
        timeout is Kodi's spelling of "for ever".
        """
        if self.abort() or self.monitor.waitForAbort(0.001):
            raise InterruptedError("native operation interrupted")

    def server_url(self) -> str:
        if not self._server:
            self._server = self.store.server()
        return self._server

    # -- bindings and scans --------------------------------------------------

    def bind(self, library: str, content: str) -> None:
        path = paths.library_dir(self.key, library, content)
        if self.store.bindings().get(path) == content:
            return
        rpc(
            "VideoLibrary.SetSourceContent",
            {
                "path": path,
                "content": content,
                "scraperid": "metadata.local",
                "scanrecursive": False,
                "refresh": False,
            },
        )
        self.store.bind(path, content)

    def bind_folders(
        self,
        content: str,
        folders: Iterable[str],
        force: bool = False,
        noupdate: bool = False,
    ) -> None:
        """A folder under a root needs its own binding: Kodi derives a plugin
        path's parent as the plugin root, so the library binding is never
        found from beneath it (URIUtils::GetParentPath), and a folder without
        one is skipped by the scanner. A show folder is bound before the
        root scan that lists it; a movie folder only before a scan by name
        (``containssingleitem`` would make the folder the movie).

        A movie folder is bound with folder names on: the scanner reads an
        extras folder only from a directory whose settings say its movies
        are in folders of their own (AddVideoExtras, ``parent_name``).
        ``force`` binds a folder the store already knows, for a flag, and
        ``noupdate`` is the binding every movie folder ends up with
        (bind_movie_folders)."""
        bound = self.store.bindings()
        wanted = list(
            dict.fromkeys(folders if force else [p for p in folders if p not in bound])
        )
        if wanted:
            LOG.debug(
                "binding %d %s folder(s)%s",
                len(wanted),
                content,
                " noupdate" if noupdate else "",
            )
        for start in range(0, len(wanted), 25):
            chunk = wanted[start : start + 25]
            replies = rpc_batch(
                [
                    (
                        "VideoLibrary.SetSourceContent",
                        {
                            "path": path,
                            "content": content,
                            "scraperid": "metadata.local",
                            "containssingleitem": content == "tvshows",
                            "usedirectorynames": content == "movies",
                            "noupdate": noupdate,
                            "refresh": False,
                        },
                    )
                    for path in chunk
                ]
            )
            done = [
                path
                for path, reply in zip(chunk, replies)
                if not isinstance(reply, Exception)
            ]
            self.store.bind_many((path, content) for path in done)
            failed = [r for r in replies if isinstance(r, Exception)]
            if failed:
                raise failed[0]

    def bind_movie_folders(self) -> None:
        """Bind every movie folder of the catalogue with ``noupdate``, the
        folders of an older profile's rows included, since a pass plans
        pending rows only. Kodi's info dialog loads a library movie's full
        details, its cast among them, only when it finds a scraper on the
        movie's own folder (CGUIWindowVideoBase::ShowInfo,
        CVideoDatabase::GetScraperForPath); with ``noupdate`` Kodi's own
        Update library lists none of them.

        Once per profile every movie folder is bound again, for the folders
        an earlier build bound without the flag, and the extras folders of
        the movies with extras are bound, for the extras an earlier build
        filed; a scan binds the ones it files (scan_video). A movie with
        extras is told by its payload, never by its assets token, which a
        movie with versions alone has too. MOVIE_BINDINGS_SETTING is stored
        only after every folder is bound, so a failed read or binding is
        tried again."""
        state = settings.get_str(MOVIE_BINDINGS_SETTING)
        extras: set[str] = set()
        if state == EXTRAS_BINDINGS_STATE:
            entries = self.store.entries(kind="Movie")
        else:
            entries, extras = self.store.movies_with_extras(
                lambda item: bool(metadata.special_features(item))
            )
        folders = sorted(
            {paths.movie_dir(self.key, e.library, e.item_id) for e in entries.values()}
        )
        if not folders:
            return
        force = state not in (MOVIE_BINDINGS_STATE, EXTRAS_BINDINGS_STATE)
        if force:
            LOG.debug("binding every movie folder with noupdate, once")
        self.bind_folders("movies", folders, force=force, noupdate=True)
        if state != EXTRAS_BINDINGS_STATE:
            dirs = sorted(
                paths.extras_dir(self.key, entries[i].library, i)
                for i in extras
                if i in entries
            )
            if dirs:
                self.bind_folders("movies", dirs, noupdate=True)
            settings.set_str(MOVIE_BINDINGS_SETTING, EXTRAS_BINDINGS_STATE)

    def library_event(self) -> None:
        """Have Kodi announce that the video library changed, and scan
        nothing for it: a scan with no directory walks every bound folder.
        Not issued while a scan runs (see ``scan``).
        """
        if not self._idle("video"):
            return
        rpc("VideoLibrary.Scan", {"directory": NOWHERE, "showdialogs": False})

    def announce_writes(self) -> None:
        """``library_event`` for what a pass wrote, at its end.

        A video setter announces only a play count or a last played it
        moved (patch.ANNOUNCED), and a home widget reloads on an
        announcement and on nothing else. Issued
        through ``scan``, which waits for a running scan instead of stopping
        it, and never with Kodi's dialog, which would come up for a scan of
        nothing.
        """
        self.scan([NOWHERE], dialogs=False)

    def unbind_show(self, library: str, series_id: str) -> None:
        self.unbind_folder(paths.show_dir(self.key, library, series_id))

    def unbind_movie(self, library: str, item_id: str) -> None:
        self.unbind_folder(paths.movie_dir(self.key, library, item_id))

    def unbind_folder(self, path: str) -> None:
        try:
            rpc(
                "VideoLibrary.SetSourceContent",
                {
                    "path": path,
                    "content": "none",
                    "clearmode": "clear",
                    "refresh": False,
                },
            )
        except RuntimeError as error:
            LOG.warning("folder binding not cleared: %s", error)
        self.store.unbind(path)

    def _count(self, location: Optional[paths.Location]) -> Optional[int]:
        """Kodi's row count under a scanner directory's library, or None.

        One row is asked for with it, and never a zero-width page: the video
        library answers an end of 0 with no row, the audio library with
        every row.
        """
        if location is None or not location.library or not location.content:
            return None
        library_dir = paths.library_dir(self.key, location.library, location.content)
        method, key = {
            "music": ("AudioLibrary.GetSongs", "songs"),
            "movies": ("VideoLibrary.GetMovies", "movies"),
            "tvshows": ("VideoLibrary.GetEpisodes", "episodes"),
            "musicvideos": ("VideoLibrary.GetMusicVideos", "musicvideos"),
        }[location.content]
        reply = rpc(
            method,
            {
                "filter": {
                    "field": "path",
                    "operator": "startswith",
                    "value": library_dir,
                },
                "limits": {"start": 0, "end": 1},
            },
        )
        total = (reply or {}).get("limits", {}).get("total")
        return total if isinstance(total, int) else None

    def scan_heading(
        self, location: Optional[paths.Location], scanner: str = "video"
    ) -> str:
        return "%s: %s" % (
            xbmc.getLocalizedString(progress.SCANNING),
            progress.label(
                location.content if location and location.content else scanner
            ),
        )

    def scan_watch(
        self, location: Optional[paths.Location], heading: str, goal: int
    ) -> Optional[Callable[[], None]]:
        """A poll callback that reads Kodi's row count under the scan's
        library every few seconds and moves the bar towards ``goal``."""
        if not self.progress.open:
            return None
        try:
            baseline = self._count(location)
        except Exception:
            return None
        if baseline is None:
            return None
        polled = [time.monotonic()]

        def on_poll() -> None:
            if time.monotonic() - polled[0] < self.SCAN_POLL:
                return
            polled[0] = time.monotonic()
            try:
                now = self._count(location)
            except Exception:
                return
            if now is not None:
                done = max(0, now - baseline)
                self.progress.at(done, "%s %d / %d" % (heading, done, goal))

        return on_poll

    def scan(
        self,
        directories: list[str],
        scanner: str = "video",
        expected: Optional[dict[str, int]] = None,
        prepare: Optional[Callable[[str], None]] = None,
        on_poll: Optional[Callable[[], None]] = None,
        dialogs: Optional[bool] = None,
    ) -> None:
        """Scan each directory in turn and wait for the scanner to go idle.

        ``expected`` maps a directory to the rows its scan should add; while
        it runs the bar shows Kodi's own count climbing towards it, read every
        few seconds, since a scan is the longest phase and the pass counts
        nothing of its own until it ends. ``on_poll`` is called while a
        directory with no such count is scanned: the caller's own bar across
        the run (``MusicPass.scan``). ``prepare`` is called with each
        directory just before its scan.

        One scan at a time: the builtin behind the call stops a running scan
        instead of queuing the request.
        """
        if not directories:
            return

        def finished() -> int:
            return (
                self.monitor.music_finished
                if scanner == "music"
                else self.monitor.finished
            )

        method = "AudioLibrary.Scan" if scanner == "music" else "VideoLibrary.Scan"
        # Kodi's own scanning dialog shows the import item by item; the bar
        # above it names the phase. Never for music: with a dialog the music
        # scanner starts its MusicFileCounter thread, which lists every
        # directory a second time, concurrently, to size the bar
        # (MusicInfoScanner.cpp). The video scanner has no such thread.
        # ``dialogs`` is the caller's word against the setting's
        # (announce_writes).
        if dialogs is None:
            dialogs = progress.show_dialogs()
        dialogs = dialogs and scanner != "music"
        expected = expected or {}
        for directory in directories:
            self.wait(lambda: self._idle(scanner), busy=lambda: self._scanning(scanner))
            serial = finished()
            began = time.monotonic()

            def scanned(serial: int = serial) -> bool:
                return finished() > serial and self._idle(scanner)

            location = paths.parse(directory)
            heading = self.scan_heading(location, scanner)
            goal = int(expected.get(directory) or 0)
            saved = self.progress.phase(goal, heading) if goal else None
            watch = self.scan_watch(location, heading, goal) if saved else on_poll

            if prepare is not None:
                prepare(directory)
            rpc(method, {"directory": directory, "showdialogs": dialogs})
            self._async_pending = True
            try:
                self.wait(
                    scanned,
                    busy=lambda: self._scanning(scanner),
                    on_poll=watch,
                )
                LOG.debug(
                    "%s scan of %s took %.1f s",
                    scanner,
                    paths.describe(directory),
                    time.monotonic() - began,
                )
            except TimeoutError:
                if finished() == serial:
                    raise
            finally:
                if scanner == "music" and finished() > serial:
                    library = location.library if location else None
                    if library:
                        self._unchecked_scans[library] = (
                            self._unchecked_scans.get(library, 0) + 1
                        )
                self._async_pending = not self._idle(scanner)
                if saved is not None:
                    self.progress.restore(saved)
        if scanner == "music":
            for directory in directories:
                location = paths.parse(directory)
                if location is not None and location.library:
                    self.readback.forget_music(location.library)
        else:
            self.readback.clear()

    # -- movie versions and extras -------------------------------------------

    def _asset_folders(self, upserts: dict[str, Record], library: str) -> list[str]:
        """Movie folders whose listing Kodi has not seen: the assets token
        acknowledged for the movie (the listing a scan presented) differs
        from its payload's (metadata.assets_token). The root walk lists the
        movie's own file alone, so these are scanned by name -- a movie that
        lost its last version or extra too, so that the empty token the
        apply pass then acknowledges is one a scan presented. The scan never
        removes (provider.exists)."""
        movies = [
            r for r in upserts.values() if r.kind == "Movie" and r.library == library
        ]
        if not movies:
            return []
        mappings = self.store.mappings(kind="Movie", library=library)
        folders: list[str] = []
        for record in self.payloads.walk(movies):
            token = metadata.assets_token(record.item, self.features)
            mapping = mappings.get(record.item_id)
            previous = mapping.applied.get("assets", "") if mapping is not None else ""
            if previous == token:
                continue
            folder = paths.movie_dir(self.key, library, record.item_id)
            folders.append(folder)
            if metadata.special_features(record.item):
                self._extras_folders.add(folder)
        return folders

    def retire_assets(self, folders: Collection[str]) -> None:
        """Clean the folder of every movie whose listing dropped a version
        file or an extra this pass. With the asset_clean feature the clean
        of one folder removes what ``provider.exists`` says is gone and
        nothing else; one that fails leaves the rows to the viewer's Clean
        library.

        Without the feature a clean's stage after the directory's files asks
        the add-on about every bound folder of every library and deletes the
        path row of one left unanswered, so the rows are left for the
        viewer's own Clean library, said once here."""
        if not folders:
            return
        if "asset_clean" not in self.features:
            LOG.debug(
                "%d movie folder(s) lost a version or an extra; the rows are left "
                "for a Clean library of the viewer's (Kodi 22 keeps them until the "
                "movie leaves)",
                len(folders),
            )
            return
        for folder in sorted(folders):
            try:
                self.clean(folder)
                LOG.debug("retired the dropped versions and extras of %s", folder)
            except InterruptedError:
                raise
            except Exception:
                LOG.exception("movie folder %s not cleaned", folder)

    def clean(self, directory: str) -> None:
        """Run Kodi's clean of ``directory`` and wait for it to end, as a
        scan is waited for: never beside a scan."""
        self.wait(lambda: self._idle("video"), busy=lambda: self._scanning("video"))
        serial = self.monitor.cleaned
        rpc("VideoLibrary.Clean", {"directory": directory, "showdialogs": False})
        self._async_pending = True
        try:
            self.wait(
                lambda: self.monitor.cleaned > serial and self._idle("video"),
                busy=lambda: self._scanning("video"),
            )
        finally:
            self._async_pending = not self._idle("video")
        self.readback.clear()

    @contextmanager
    def without_actor_thumbs(self, rows: int) -> Iterator[None]:
        """Run a large video scan with Kodi's "Download actor thumbnails" off,
        and put the setting back.

        With it on the scanner asks the texture cache for every cast
        member's picture before it files the item (FetchActorThumbs,
        VideoInfoScanner.cpp), into a queue that a first import fills faster
        than its worker empties it. The pictures are not lost by the hold:
        the listing gives every actor's URL, AddActor stores it, and Kodi
        fetches a picture the first time something shows it.

        The value is recorded before it is changed (store.hold_setting), so
        a Kodi stopped mid-scan gets it back at the next start
        (restore_settings)."""
        held = False
        if rows >= ACTOR_THUMBS_FLOOR:
            try:
                reply = rpc(
                    "Settings.GetSettingValue", {"setting": ACTOR_THUMBS_SETTING}
                )
                if isinstance(reply, dict) and reply.get("value") is True:
                    self.store.hold_setting(ACTOR_THUMBS_SETTING, True)
                    try:
                        rpc(
                            "Settings.SetSettingValue",
                            {"setting": ACTOR_THUMBS_SETTING, "value": False},
                        )
                    except RuntimeError:
                        # Kodi kept its value, so nothing is held. A record
                        # left here would be given back at a later start,
                        # over whatever the user had set by then.
                        self.store.release_setting(ACTOR_THUMBS_SETTING)
                        raise
                    held = True
                    LOG.debug(
                        "Kodi setting %s off for a scan of %d rows",
                        ACTOR_THUMBS_SETTING,
                        rows,
                    )
            except RuntimeError as error:
                # The scan is the work; the hold only makes it shorter.
                LOG.warning("actor thumbnails left on for the scan: %s", error)
        try:
            yield
        finally:
            if held:
                self.restore_settings()

    def restore_settings(self) -> None:
        """Give back every Kodi setting a scan was holding: the scan that
        just ended, or one a stopped Kodi never finished. The record goes
        only after Kodi took the value.

        A value Kodi will not take now is no reason to stop: the record
        stays, ``settings_owed`` says so, and every later pass and service
        start asks again, as does the library thread while nothing is
        pending (``Library.apply``)."""
        owed = False
        for setting, value in self.store.held_settings().items():
            try:
                rpc("Settings.SetSettingValue", {"setting": setting, "value": value})
            except RuntimeError as error:
                owed = True
                say = LOG.debug if setting in self._refused_settings else LOG.warning
                self._refused_settings.add(setting)
                say("Kodi setting %s not given back yet: %s", setting, error)
                continue
            self.store.release_setting(setting)
            self._refused_settings.discard(setting)
            LOG.debug("Kodi setting %s back to %r", setting, value)
        self.settings_owed = owed

    def _prepare_scan(self, directory: str) -> None:
        """List a movie's extras folder through Kodi just before the folder
        is scanned, with the disc folders the scanner probes for below it.

        Before the scanner looks at a listing, every folder in it is probed
        for a disc structure (CFileItemList::Stack, GetOpticalMediaPath), and
        CPluginFile::Exists says yes to any plugin URL, so an extras folder
        is otherwise turned into a phantom VIDEO_TS.IFO. The probe asks the
        directory cache first (CFile::Exists), which holds the last fifty
        directories Kodi listed: listed here, the folder and its VIDEO_TS/
        and BDMV/ answer "no such file" and the folder stays a folder."""
        if directory not in self._extras_folders:
            return
        extras = directory + paths.EXTRAS
        for probe in (extras, extras + "VIDEO_TS/", extras + "BDMV/"):
            rpc("Files.GetDirectory", {"directory": probe, "media": "video"})

    def _forget_listing(self, directory: str) -> None:
        """Have Kodi drop its cached listing of ``directory``: the provider
        refuses the request (paths.FORGET), so Kodi answers with an error,
        which is the result."""
        try:
            rpc("Files.GetDirectory", {"directory": paths.forgetting(directory)})
        except RuntimeError:
            pass

    # -- the scanner hold ----------------------------------------------------

    def hold(self, scanner: str = "music") -> None:
        """Keep Kodi's scanner busy while the pass writes, so the writes are
        announced as a transaction and the home widgets stay quiet.

        The scanner lists the hold directory; the provider keeps that
        listing open until ``release`` clears the token (``provider._hold``).
        Only the music scanner marks its announcements this way -- the
        video database's ``AnnounceUpdate`` carries no flag.
        """
        since = self._held.get(scanner)
        if since is not None and time.monotonic() - since < HOLD_RENEW:
            return
        if since is not None:
            self.release(scanner)
        self.wait(lambda: self._idle(scanner), busy=lambda: self._scanning(scanner))
        state.set_native_hold(scanner)
        method = "AudioLibrary.Scan" if scanner == "music" else "VideoLibrary.Scan"
        rpc(
            method,
            {"directory": paths.hold_dir(self.key, scanner), "showdialogs": False},
        )
        try:
            self.wait(lambda: self._scanning(scanner), timeout=10)
            if scanner == "music":
                self._own_music_scans += 1
        except TimeoutError:
            LOG.warning("%s scanner did not take the hold; writing without it", scanner)
        self._held[scanner] = time.monotonic()

    def release(self, scanner: str = "music") -> None:
        if scanner not in self._held:
            return
        state.clear_native_hold(scanner)
        self._held.pop(scanner, None)
        self.wait(lambda: self._idle(scanner), busy=lambda: self._scanning(scanner))

    def release_all(self) -> None:
        for scanner in list(self._held):
            self.release(scanner)

    def note_music_changes(self) -> None:
        """Forget which music libraries have been compared whole once Kodi
        has scanned or cleaned music for anyone but the pass.

        Kodi announces the end of every scan it runs, the hold's included,
        and the announcement names no directory: the pass counts the scans
        it ran, and takes that many announcements as theirs. A directory
        scan counts only once the pass has checked the directories it
        re-listed for lost songs (credit_music_scans); one the pass did not
        get to check, a scan that failed part way or a removal's in a pass
        that filed nothing in the library, is a change like any other.
        kofin never cleans music.
        """
        self._unchecked_scans.clear()
        heard = self.monitor.music_finished + self.monitor.music_cleaned
        new = heard - self._music_heard
        self._music_heard = heard
        own = min(new, self._own_music_scans)
        self._own_music_scans -= own
        if new > own:
            self.music_checked.clear()
            self.music_sweep = True

    def credit_music_scans(self, library: str) -> None:
        """The library's directory scans this pass ran have had their
        directories checked for lost songs: they are the pass's own."""
        self._own_music_scans += self._unchecked_scans.pop(library, 0)

    # -- the pass ------------------------------------------------------------

    def reconcile(self, repair: bool = False) -> None:
        """Replay durable operations; an accepted RPC is never a commit.

        In order: the pass waits for Kodi's scanners and decides whether it
        compares every row; reads what is pending and where it is placed;
        removes; plans the sets and the upserts; scans and applies; settles
        the sets, the folders and the widgets; and gives back what it held,
        whether or not it completed.
        """
        repair, stamped, serializer = self._begin(repair)
        applier = Applier(self)
        completed = False
        large = repair
        try:
            self.payloads = PayloadWindow(self.store)
            pending, entries = self._pending(repair)
            errors: list[Exception] = []
            self._remove(pending, entries, errors)
            # The pin can predate a collection's removal (store.pin keeps a
            # pin an earlier pass left), and a collection read there would
            # keep its set on its movies while finish_sets lets it go.
            sets, boxsets = self._collections(pending, entries)
            collections = metadata.collections_of(boxsets)
            self.join_sets(pending, entries, sets, collections)
            upserts = self._upserts(pending, entries)
            self._look_up({i: (r.kind, r.library) for i, r in upserts.items()})
            self.progress.begin(len(upserts))
            large = large or len(upserts) >= PRELOAD_ALL_MAPPINGS
            self._apply(applier, upserts, entries, collections, repair, errors)
            self._settle(applier, pending, upserts, boxsets, errors)
            if errors:
                raise RuntimeError(
                    "%d native operations remain pending: %s" % (len(errors), errors[0])
                )
            completed = True
            # Every episode a folder scan was asked for is filed.
            self._folder_scanned.clear()
            if stamped != self.features or serializer != metadata.SERIALIZER:
                self.store.remember_features(self.features, metadata.SERIALIZER)
        finally:
            applier.commit()
            self.progress.close()
            self.payloads = PayloadWindow(self.store)
            self.music.forget()
            # The pass's tables are the largest Python objects in the
            # process; hand the heap back before Kodi's scanner needs the
            # page cache (core/memory.py).
            del applier
            self._release(completed, large)

    def _begin(
        self, repair: bool
    ) -> tuple[bool, Optional[frozenset[str]], Optional[int]]:
        """The pass waits for Kodi's scanners, pins the catalogue and decides
        whether every row is compared; returns the repair flag with the
        feature set and the serializer the last pass stamped."""
        # Until the first scan or the first row is counted, the pass waits
        # for Kodi's scanners, reads the catalogue, removes, binds and plans.
        self.progress.working(progress.PREPARING)
        self.setup()
        # A prior process may have died with its pin held, or left a scan
        # running that outlives it. Wait for Kodi to finish using it before
        # publishing the newer desired view to a scan, however long it runs.
        self.wait(lambda: self._idle("any"), busy=lambda: not self._idle("any"))
        self.restore_settings()
        self.store.pin()
        self.features = capabilities.features()
        self.readback.features = self.features
        # The feature set is an input of every acknowledgement: a Kodi that
        # gained or lost one since the last pass (an upgrade) has every row
        # compared again, which is what a repair pass does, and nothing is
        # written where the row already matches.
        stamped = self.store.features_applied()
        if stamped is not None and stamped != self.features and not repair:
            LOG.debug(
                "Kodi's features changed since the last pass (on: %s): comparing "
                "every row",
                ", ".join(sorted(self.features)) or "none",
            )
            repair = True
        # So is the serializer: a build whose desired state differs for the
        # same payload (metadata.SERIALIZER) compares every row once, or a
        # row that never changes again keeps the state the old build gave it.
        serializer = self.store.serializer_applied()
        if stamped is not None and serializer != metadata.SERIALIZER and not repair:
            LOG.debug(
                "the desired state changed since the last pass (serializer %s, "
                "now %d): comparing every row",
                serializer,
                metadata.SERIALIZER,
            )
            repair = True
        self.readback.clear()
        self.readback.look_up({})
        self.music = MusicPass(self)
        self.note_music_changes()
        if repair:
            self.music_checked.clear()
            self.music_sweep = True
        return repair, stamped, serializer

    def _pending(self, repair: bool) -> tuple[PendingWork, Placements]:
        """What the pass holds: the pending items as (generation, operation,
        payload), every record on a repair, and their placements. The
        pending items' are read up front and the rest as asked for; a
        repair, which holds every item, reads them all at once."""
        pending: dict[str, tuple[int, str, dict]] = {
            item_id: (generation, operation, payload)
            for item_id, generation, operation, payload in self.store.pending_work()
        }
        if repair:
            for item_id, record in self.store.records(payloads=False).items():
                if item_id not in pending:
                    pending[item_id] = (record.generation, "upsert", {})
        entries = self.store.placements(() if repair else pending)
        if repair:
            entries.whole()
        return pending, entries

    def _look_up(self, items: dict[str, tuple[str, str]]) -> None:
        """Tell the readback how many rows of each library the pass looks
        up, from each item's kind and library: a small pass reads its own
        movies, albums and artists alone."""
        counts: dict[tuple[str, str], int] = {}
        for scope in items.values():
            counts[scope] = counts.get(scope, 0) + 1
        self.readback.look_up(counts)

    def _remove(
        self, pending: PendingWork, entries: Placements, errors: list[Exception]
    ) -> None:
        """The tombstones applied, and what they put back to pending joined
        to this pass rather than the next: a removed collection's movies let
        go of its set before the set can and rejoin as upserts, and a
        whole-library clear puts other libraries' shows back."""
        self.store.invalidate(removal.set_members(pending))
        tombstones = self.store.tombstones()
        looked_up = {
            item_id: (entry.kind, entry.library)
            for item_id in pending
            if (entry := entries.get(item_id)) is not None
        }
        looked_up.update((i, (e.kind, e.library)) for i, e in tombstones.items())
        self._look_up(looked_up)
        removal.remove(self, pending, entries, tombstones, errors)
        for item_id, generation, operation, _ in self.store.pending_work():
            if operation == "upsert" and item_id not in pending:
                pending[item_id] = (generation, operation, {})
        entries.preload(pending)

    def _upserts(self, pending: PendingWork, entries: Placements) -> dict[str, Record]:
        """The records to apply: every pending upsert with a placement, its
        payload read through the window."""
        upserts: dict[str, Record] = {}
        for item_id, (generation, operation, _payload) in pending.items():
            entry = entries.get(item_id)
            if operation != "upsert" or entry is None:
                continue
            upserts[item_id] = Record(
                item_id,
                entry.kind,
                entry.library,
                entry.parent_id,
                None,
                generation,
                loader=self.payloads,
            )
        return upserts

    def _collections(
        self, pending: PendingWork, entries: Placements
    ) -> tuple[dict[str, Record], list[dict[str, Any]]]:
        """Every live collection, for ``join_sets`` and ``finish_sets``, read
        only when a movie or a collection is pending: membership is inside
        the payloads, and nothing else in the pass reads them.

        A movie's set is chosen among all its collections
        (``metadata.collections_of``), so the map is built from every one:
        built from fewer, a movie in two collections maps to the one that
        lost it, which then has no row to find.
        """

        def kind_of(item_id: str) -> str:
            try:
                return entries[item_id].kind
            except KeyError:
                return ""

        if not any(
            (operation == "upsert" and kind_of(item_id) == "Movie")
            or payload.get("Type") == "BoxSet"
            or kind_of(item_id) == "BoxSet"
            for item_id, (_, operation, payload) in pending.items()
        ):
            return {}, []
        live = {
            item_id: record
            for item_id, record in self.store.records(kind="BoxSet").items()
            if item_id not in pending or pending[item_id][1] != "remove"
        }
        return live, [record.item for record in live.values()]

    def _apply(
        self,
        applier: Applier,
        upserts: dict[str, Record],
        entries: Placements,
        collections: dict[str, str],
        repair: bool,
        errors: list[Exception],
    ) -> None:
        """The scans, then the setters.

        New movies, then new shows and episodes, then new music videos,
        then album directories that hold a song with no row, are scanned
        first. The album directories whose songs all have rows follow,
        then album and artist art and text (``kinds.MUSIC_FIRST``), which
        a music scan can file under a new row and so follows every one.
        Then the versions and extras of movies that already have a row,
        and every other kind in ``kinds.ORDER``. With no version or extra
        scan to wait for, the kinds keep their order and the music hold is
        taken once.
        """
        planned = self._plan_music(upserts, errors, entries)
        # An album brings its songs into the comparison only while it is
        # pending (MusicPass.directories): one of a library whose planning
        # failed waits for the next pass.
        upserts = {
            item_id: record
            for item_id, record in upserts.items()
            if record.kind != "MusicAlbum" or record.library in planned
        }
        fresh, assets = self.plan_video(upserts, errors)
        failed: set[str] = set()
        self.scan_video(fresh)
        self._scan_music(planned, upserts, errors, failed, fresh=True)
        self._scan_music(planned, upserts, errors, failed, fresh=False)
        self._finish_music(planned, entries, errors, failed)
        early = (
            [
                kind
                for kind in MUSIC_FIRST
                if any(r.kind == kind for r in upserts.values())
            ]
            if assets.directories
            else []
        )
        if early:
            applier.run(upserts, {}, set(), repair, errors, kinds=early)
        self.scan_video(assets)
        # Only a collection's planning asks which ids are movies.
        movies = (
            {i for i, e in entries.items() if e.kind == "Movie"}
            if any(r.kind == "BoxSet" for r in upserts.values())
            else set()
        )
        applier.run(
            upserts,
            collections,
            movies,
            repair,
            errors,
            kinds=[kind for kind in ORDER if kind not in early],
        )
        self.reclaim_shows(upserts)

    def _settle(
        self,
        applier: Applier,
        pending: PendingWork,
        upserts: dict[str, Record],
        boxsets: list[dict[str, Any]],
        errors: list[Exception],
    ) -> None:
        """After the setters, nothing counted: the sets, the asset folders,
        the movie folders' bindings, the acknowledgements and the widgets."""
        self.progress.working(progress.WAITING)
        removal.finish_sets(self, pending, boxsets, errors)
        self.retire_assets(applier.asset_folders)
        if any(r.kind == "Movie" for r in upserts.values()):
            # Only a pass that filed movies can leave a folder unbound;
            # an older profile's are bound once a service generation
            # (Library.apply).
            try:
                self.bind_movie_folders()
            except Exception:
                LOG.exception("movie folder bindings not completed")
        # Applier.run leaves no acknowledgement queued; this is that,
        # said here.
        applier.commit()
        if applier.unannounced:
            # After every setter of the pass, and once for all of them.
            try:
                self.announce_writes()
            except InterruptedError:
                raise
            except Exception:
                LOG.exception("home widgets not told of the pass's writes")

    def _release(self, completed: bool, large: bool) -> None:
        """What the pass held, given back: the heap after a large pass or a
        whole music read (a small pass frees too little to pay a collection
        for), the scanner holds, and the catalogue's pin once Kodi is idle."""
        if large or self.music.read_library:
            memory.release()
        try:
            self.release_all()
        except Exception:
            LOG.exception("scanner hold not released")
            state.clear_native_hold("music")
        # A timed-out scan must retain its snapshot until Kodi is idle.
        if (completed or not self._async_pending) and self._idle("any"):
            self.store.unpin()

    def join_sets(
        self,
        pending: PendingWork,
        entries: Placements,
        sets: dict[str, Record],
        collections: dict[str, str],
    ) -> None:
        """Put every collection a movie of this pass is filed under into the
        pass, pending before that movie is acknowledged.

        A set is Kodi's to make and to drop. It goes with the last movie
        that names it, and a scan or a movie's patch makes it again from the
        name alone, with no art and no plot. The collection's payload moves
        with none of that, so nothing but its movies can bring it here.
        Planned, a set is compared with its row (Applier.plan), and one found
        as it was left is sent nothing.
        """
        taken = {
            collections[item_id]
            for item_id, (_, operation, _) in pending.items()
            if operation == "upsert"
            and item_id in collections
            and item_id in entries
            and entries[item_id].kind == "Movie"
        }
        joined = {
            item_id: record
            for item_id, record in sets.items()
            if item_id not in pending
            and (record.item.get("Name") or "").strip(paths.ASCII_SPACE) in taken
        }
        self.store.invalidate(joined)
        for item_id, record in joined.items():
            pending[item_id] = (record.generation, "upsert", {})

    def _plan_music(
        self,
        upserts: dict[str, Record],
        errors: list[Exception],
        entries: abc.Mapping[str, Entry],
    ) -> dict[str, tuple[set[str], set[str]]]:
        """The album directories each library must list again, split into
        those that hold a song with no row and the rest. Nothing is scanned."""
        planned: dict[str, tuple[set[str], set[str]]] = {}
        for library in sorted({r.library for r in upserts.values() if r.library}):
            if not any(
                paths.CONTENT.get(r.kind) == "music"
                for r in upserts.values()
                if r.library == library
            ):
                continue
            try:
                planned[library] = self.music.directories(upserts, library, entries)
            except InterruptedError:
                raise
            except Exception as error:
                errors.append(error)
        return planned

    def _scan_music(
        self,
        planned: dict[str, tuple[set[str], set[str]]],
        upserts: dict[str, Record],
        errors: list[Exception],
        failed: set[str],
        fresh: bool,
    ) -> None:
        """Scan one half of what ``_plan_music`` named, every library's;
        a library whose first half failed is not scanned again."""
        for library, (new, rest) in planned.items():
            folders = new if fresh else rest
            if library in failed or not folders:
                continue
            try:
                self.music.scan(
                    library,
                    folders,
                    expected=sum(
                        1
                        for record in upserts.values()
                        if record.kind == "Audio"
                        and record.library == library
                        and record.parent_id in folders
                    ),
                )
            except InterruptedError:
                raise
            except Exception as error:
                errors.append(error)
                failed.add(library)

    def _finish_music(
        self,
        planned: dict[str, tuple[set[str], set[str]]],
        entries: abc.Mapping[str, Entry],
        errors: list[Exception],
        failed: set[str],
    ) -> None:
        """Lost songs, scan credit and the sweep flag, once both halves of
        a library have been scanned."""
        for library in planned:
            if library in failed:
                continue
            try:
                self.music.finish(library, entries)
            except InterruptedError:
                raise
            except Exception as error:
                errors.append(error)

    def refile_removed(self) -> int:
        """Put back to pending what Kodi removed of ours that we did not:
        the rows a viewer's removal of another source took with a show both
        hold, a Remove from library, a clean. Run between passes, where a
        row the pass removed names a tombstone or no item at all, and one it
        refreshed is in ``replaced``."""
        lost = self.monitor.lost - self.replaced
        self.monitor.lost = set()
        self.replaced = set()
        if not lost:
            return 0
        items = self.store.refile(lost)
        if items:
            LOG.debug(
                "Kodi removed %d row(s) filed for %d item(s); the next pass files them"
                " again: %s",
                len(lost),
                len(items),
                ", ".join(items[:20]),
            )
        return len(items)

    def plan_video(
        self, upserts: dict[str, Record], errors: list[Exception]
    ) -> tuple[VideoScan, VideoScan]:
        """Bind whatever the readback shows the video scanner has not filed.

        The first scan is new content, every library's movies, then its
        shows and episodes, then its music videos. The second is the
        version and extra folders of movies that already have a row, and
        of movies whose own file was listed by a root scan. A new movie
        scanned by its own folder already lists those files.
        """
        self._extras_folders = set()
        gathered: dict[str, list[tuple[str, list[Record], int, list[str]]]] = {
            "movies": [],
            "tvshows": [],
            "musicvideos": [],
        }
        for library in sorted({r.library for r in upserts.values() if r.library}):
            kinds = {r.kind for r in upserts.values() if r.library == library}
            for content in ("movies", "tvshows", "musicvideos"):
                if not any(paths.CONTENT.get(k) == content for k in kinds):
                    continue
                try:
                    self.bind(library, content)
                except InterruptedError:
                    raise
                except Exception as error:
                    errors.append(error)
                    continue
                missing, present = self._unfiled(content, library, upserts)
                asset_folders = (
                    self._asset_folders(upserts, library) if content == "movies" else []
                )
                if not missing and not asset_folders:
                    continue
                gathered[content].append((library, missing, present, asset_folders))
        directories: list[str] = []
        expected: dict[str, int] = {}
        expectations: list[tuple[str, int, dict[str, Any]]] = []
        movie_folders: list[str] = []
        asset_directories: list[str] = []
        for content in ("movies", "tvshows", "musicvideos"):
            for library, missing, present, asset_folders in gathered[content]:
                root = paths.library_dir(self.key, library, content)
                if content == "movies":
                    named, counts, folders, later = self._movie_directories(
                        library, root, present, missing, asset_folders
                    )
                    directories.extend(named)
                    expected.update(counts)
                    movie_folders.extend(folders)
                    asset_directories.extend(later)
                elif content == "tvshows":
                    named, counts = self._show_directories(library, root, missing)
                    directories.extend(named)
                    expected.update(counts)
                else:
                    directories.append(root)
                    expected[root] = sum(
                        1 for r in missing if r.kind in ("Episode", "MusicVideo")
                    )
                for record in self.payloads.walk(missing):
                    if record.kind in ("Movie", "Episode", "MusicVideo"):
                        expectations.append(
                            (
                                record.item_id,
                                record.generation,
                                metadata.userdata(record.item),
                            )
                        )
        return (
            VideoScan(directories, expected, expectations, movie_folders),
            VideoScan(asset_directories, {}, [], asset_directories),
        )

    def _unfiled(
        self, content: str, library: str, upserts: dict[str, Record]
    ) -> tuple[list[Record], int]:
        """The records of one library and content the readback shows the
        scanner has not filed, with the count of rows it has. A show's
        folder is bound as the show is found, since the scanner skips a
        folder without a binding of its own."""
        if content == "tvshows":
            missing = self._missing_tv(upserts, library)
            self.bind_folders(
                "tvshows",
                [
                    paths.show_dir(self.key, library, r.item_id)
                    for r in missing
                    if r.kind == "Series"
                ],
            )
            return missing, 0
        kind = "Movie" if content == "movies" else "MusicVideo"
        wanted = [
            r for r in upserts.values() if r.kind == kind and r.library == library
        ]
        if kind == "Movie" and self.readback.by_row(kind, library):
            # Each movie by its folder, and the library's rows counted.
            missing = [
                r
                for r in wanted
                if self.readback.listed_movie(library, r.item_id) is None
            ]
            counted = (
                self._count(paths.parse(paths.library_dir(self.key, library, content)))
                if missing
                else None
            )
            present = len(wanted) - len(missing) if counted is None else counted
        else:
            listed = self.readback.scope(kind, library)
            missing = [r for r in wanted if r.item_id not in listed]
            present = len(listed)
        if kind == "Movie" and missing:
            # Only a movie Kodi has filed for us can sit on a row
            # another source's file lists (Readback.movie), and a
            # first import files none: its mappings in one read.
            filed = self.store.mappings_of([r.item_id for r in missing])
            missing = [
                r
                for r in missing
                if r.item_id not in filed
                or self.readback.movie(library, r.item_id) is None
            ]
        return missing, present

    def _movie_directories(
        self,
        library: str,
        root: str,
        present: int,
        missing: list[Record],
        asset_folders: list[str],
    ) -> tuple[list[str], dict[str, int], list[str], list[str]]:
        """Directories for movies the scanner has not filed, and the asset
        folders that scan does not already list.

        A movie's URL sits in a folder of its own. A few new movies are
        scanned by folder, each bound first (Kodi finds a plugin folder's
        scraper only through the folder's own binding); a first import, or
        a library mostly missing, scans the root once, which lists every
        movie as a file under its folder's URL. A folder scanned by name
        lists that movie's version files and extras. A root scan lists the
        movie's own file alone, so those asset folders are returned apart,
        to be scanned after the new content.
        """
        directories: list[str] = []
        expected: dict[str, int] = {}
        movie_folders: list[str] = []
        if missing:
            total = present + len(missing)
            if len(missing) > total * ROOT_SCAN_SHARE:
                directories.append(root)
                expected[root] = len(missing)
            else:
                movie_folders = [
                    paths.movie_dir(self.key, library, r.item_id) for r in missing
                ]
                directories.extend(movie_folders)
                expected.update((folder, 1) for folder in movie_folders)
        later = [
            folder
            for folder in asset_folders
            if folder not in movie_folders and folder not in directories
        ]
        return directories, expected, movie_folders, later

    def _show_directories(
        self, library: str, root: str, missing: list[Record]
    ) -> tuple[list[str], dict[str, int]]:
        """Directories for the shows and episodes the scanner has not filed.

        A new episode of a show Kodi lists under our folder is scanned by
        that show's folder. Asked for a folder bound as one show, the scanner
        finds the show by the folder's path (CVideoDatabase::GetTvShowId) and
        lists that folder alone, where a scan of the root has the provider
        list every show of the library first.

        The scanner makes the folder's item itself, without the tag the
        root's listing gives a show, so the root is scanned for a show with
        no row, and for one whose row another source's folder lists. It is
        scanned as well when more than SHOW_FOLDER_SCANS shows have new
        episodes, and for an episode a pass that did not complete left to a
        folder scan: Kodi skips a folder whose listing matches the hash it
        stored for it, and under the root a show carries a hash of the
        provider's.
        """
        shows = self.readback.scope("Series", library)
        asked = self._folder_scanned.pop(library, set())
        folders: dict[str, int] = {}
        for record in missing:
            if (
                record.kind != "Episode"
                or record.parent_id not in shows
                or record.item_id in asked
            ):
                folders = {}
                break
            folder = paths.show_dir(self.key, library, record.parent_id)
            folders[folder] = folders.get(folder, 0) + 1
        if not folders or len(folders) > SHOW_FOLDER_SCANS:
            return [root], {root: sum(1 for r in missing if r.kind == "Episode")}
        self._folder_scanned[library] = {r.item_id for r in missing}
        return sorted(folders), dict(folders)

    def scan_video(self, video: VideoScan) -> None:
        """Have Kodi's video scanner list what plan_video named.

        A movies root Kodi may hold in its directory cache is forgotten
        before the first folder below it is scanned. Kodi decides whether a
        directory it is asked to scan exists from its cached listing of the
        parent when it has one (CDirectory::Exists,
        CDirectoryCache::FileExists), and a movies root lists files, never
        folders. A pass lists a library's root before its folders
        (plan_video), so one forget per root covers them all."""
        owed = {
            paths.library_dir(location.key, location.library, "movies")
            for location in map(paths.parse, video.movie_folders)
            if location is not None and location.library is not None
        }

        def prepare(directory: str) -> None:
            location = paths.parse(directory)
            if (
                location is not None
                and location.movie is not None
                and location.library is not None
            ):
                root = paths.library_dir(location.key, location.library, "movies")
                if root in owed:
                    owed.discard(root)
                    self._forget_listing(root)
            self._prepare_scan(directory)

        try:
            if video.movie_folders:
                # Without noupdate for the scan: the scanner skips a noupdate
                # folder it was not told to scan everything of.
                self.bind_folders("movies", video.movie_folders, force=True)
            if video.directories:
                self.store.expect_many(video.expectations)
                with self.without_actor_thumbs(sum(video.expected.values())):
                    self.scan(
                        video.directories,
                        expected=video.expected,
                        prepare=prepare,
                    )
        finally:
            # The flag goes back whether the scan finished or not, and
            # whether the lift itself finished: without it Kodi's own Update
            # library lists these folders.
            if video.movie_folders:
                self.bind_folders(
                    "movies", video.movie_folders, force=True, noupdate=True
                )
                # An extra's URL has no query, so Kodi files it under the
                # add-on's root (CVideoDatabase::SplitPath), and a clean asks
                # the add-on about a plugin file only where it finds a binding
                # for the file's folder: without one, Clean library deletes
                # every extra unasked. noupdate, so Update library never scans
                # extras as movies.
                extras = [
                    folder + paths.EXTRAS
                    for folder in video.movie_folders
                    if folder in self._extras_folders
                ]
                if extras:
                    self.bind_folders("movies", extras, noupdate=True)

    def reclaim_shows(self, upserts: dict[str, Record]) -> None:
        """A show another source's scan took our ids off, found by this pass
        through its episodes, goes back to pending unless this pass planned
        it: the next pass compares it and puts the ids back (Readback.show).
        """
        stripped = [
            series_id
            for _, series_id in self.readback.stripped_shows()
            if series_id not in upserts
        ]
        if stripped:
            LOG.debug(
                "%d show(s) another source's scan rewrote: compared again by the"
                " next pass",
                len(stripped),
            )
            self.store.invalidate(stripped)

    def _missing_tv(self, upserts: dict[str, Record], library: str) -> list[Record]:
        shows = self.readback.scope("Series", library)
        # Only a show Kodi has filed for us can sit on a row another source's
        # folder lists (Readback.show), and a first import files none: their
        # mappings in one read, and a lookup only for those.
        unlisted = {
            r.item_id if r.kind == "Series" else r.parent_id
            for r in upserts.values()
            if r.library == library and r.kind in ("Series", "Episode")
        } - set(shows)
        filed = self.store.mappings_of(sorted(unlisted)) if unlisted else {}

        def known(series_id: str) -> bool:
            if series_id in shows:
                return True
            return (
                series_id in filed
                and self.readback.show(library, series_id) is not None
            )

        missing = [
            r
            for r in upserts.values()
            if r.kind == "Series" and r.library == library and not known(r.item_id)
        ]
        episodes = [
            r for r in upserts.values() if r.kind == "Episode" and r.library == library
        ]
        for record in self.payloads.walk(episodes):
            if metadata.episode_numbers(record.item) is None:
                # Never listed, never imported: not a reason to scan.
                continue
            if not known(record.parent_id):
                missing.append(record)
                continue
            if record.item_id not in self.readback.scope(
                "Episode", library, record.parent_id
            ):
                missing.append(record)
        return missing
