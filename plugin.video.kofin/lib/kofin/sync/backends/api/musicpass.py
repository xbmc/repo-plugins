"""The music half of a pass: the album directories Kodi must list again,
the scan that lists them, and the songs a scan lost.

Music is scanned by directory. A song is missing, or its tags have moved,
or it has moved album: each means its album directory is listed again. The
directories a pass wants listed are planned in order and scanned a part at
a time (``MusicPass.scan``), whether they are every album of a first import
or the one album a song was renamed in. ``walk`` is the order they are
listed in; this module decides which they are, runs the scan and owns the
bar across its parts. ``native`` keeps the scanner itself: the waits, the
hold and ``Native.scan``.
"""

import collections
import time
from collections import abc
from collections.abc import Collection
from typing import TYPE_CHECKING, Optional

from kofin.core.log import Logger
from . import metadata, paths, progress, walk
from .readback import artist_key
from .records import Record
from .store import Entry, Mapping, Placements

if TYPE_CHECKING:
    from .native import Native

LOG = Logger(__name__)


class MusicPass:
    """One pass's music work, and what it reads once for it: a library's
    album payloads, its song mappings and the tag hash of every song
    compared so far. The directory picker and the applier both need them,
    and a song's hash is a payload walk, a tag build and a digest.
    ``Native.reconcile`` makes one for each pass."""

    def __init__(self, native: "Native") -> None:
        self.native = native
        self.store = native.store
        self.key = native.key
        # (library, folder) pairs whose directory a scan of this pass was to
        # list, and (library, "*") when that was every directory of the
        # library: where a song can have been lost (lost_songs).
        self.rescanned: set[tuple[str, str]] = set()
        # Of those, the pairs whose listing Kodi was handed from the
        # catalogue (Store.listed). A scan stopped before a directory never
        # asks for it, and a song's tags reach Kodi only through it.
        self.listed: set[tuple[str, str]] = set()
        # Whether this pass read a whole library's rows: every song for the
        # comparison (check_due, lost_songs) or every album payload for a
        # scan; the pass hands that heap back (Native.reconcile).
        self.read_library = False
        self._album_items: dict[str, dict[str, dict]] = {}
        self._song_mappings: dict[str, dict[str, Mapping]] = {}
        self._tag_hashes: dict[str, str] = {}
        # Libraries whose every song this pass compared with Kodi's rows.
        self._compared: set[str] = set()
        # For the applier, per library: the album directories with a live
        # song, the artists live albums credit with the albums that credit
        # each, and the Kodi album id each album's songs were filed under --
        # read once a pass, not once a row.
        self._song_folders: dict[str, set[str]] = {}
        self._credited: dict[str, dict[str, set[str]]] = {}
        self._album_ids: dict[str, dict[str, Optional[int]]] = {}
        # (library, album directory) -> the Kodi album id, for a pass that
        # reads the library's albums a row at a time.
        self._album_of: dict[tuple[str, str], Optional[int]] = {}
        # Kodi's album and artist rows are not per library: two libraries
        # (or two albums of one) may share a row, and one of ours owns it.
        self._album_owners: Optional[dict[int, str]] = None
        self._owner_of: dict[int, Optional[str]] = {}
        self._artist_owners: Optional[dict[str, str]] = None

    def forget(self) -> None:
        """Drop what the pass read; what it re-listed stays on record."""
        self._album_items = {}
        self._song_mappings = {}
        self._tag_hashes = {}
        self._song_folders = {}
        self._credited = {}
        self._album_ids = {}
        self._album_of = {}
        self._album_owners = None
        self._owner_of = {}
        self._artist_owners = None

    def song_mappings(self, library: str) -> dict[str, Mapping]:
        """The library's song mappings, read once a pass: nothing between
        the directory picker and the lost-song check acknowledges a song."""
        if library not in self._song_mappings:
            self._song_mappings[library] = self.store.mappings(
                kind="Audio", library=library
            )
        return self._song_mappings[library]

    def album_items(self, library: str) -> dict[str, dict]:
        """The library's album payloads, read once a pass: a song's tag hash
        takes its album's artists and MusicBrainz ids."""
        if library not in self._album_items:
            self._album_items[library] = {
                i: r.item
                for i, r in self.store.records(
                    kind="MusicAlbum", library=library
                ).items()
            }
        return self._album_items[library]

    def song_folders(self, library: str) -> set[str]:
        if library not in self._song_folders:
            self._song_folders[library] = set(self.store.folders("Audio", library))
        return self._song_folders[library]

    def credited(self, library: str) -> dict[str, set[str]]:
        """The artist ids the library's live albums credit, each with the
        ids of the albums that credit it."""
        if library not in self._credited:
            artists: dict[str, set[str]] = {}
            for album_id, item in self.album_items(library).items():
                for credits in (item.get("AlbumArtists"), item.get("ArtistItems")):
                    for credit in credits or []:
                        if isinstance(credit, dict) and credit.get("Id"):
                            artists.setdefault(str(credit["Id"]), set()).add(album_id)
            self._credited[library] = artists
        return self._credited[library]

    def albums_filed(self, library: str, artist_id: str) -> bool:
        """Whether every album of the library that credits the artist and
        holds a song of ours has songs in Kodi: the scanner makes an
        artist's row from the tags of the songs it files."""
        holding = self.song_folders(library)
        return all(
            self.native.readback.scope("Audio", library, album)
            for album in sorted(self.credited(library).get(artist_id, ()))
            if album in holding
        )

    def artist_owner(self, record: Record) -> str:
        """Kodi keeps one artist per name; of our artists sharing a name the
        first by id owns the row's art and description."""
        if self._artist_owners is None:
            owners: dict[str, str] = {}
            for item_id, found in sorted(
                self.store.records(kind="MusicArtist").items()
            ):
                owners.setdefault(artist_key(found.item.get("Name")), item_id)
            self._artist_owners = owners
        return self._artist_owners.get(
            artist_key(record.item.get("Name")), record.item_id
        )

    def album_ids(self, library: str) -> dict[str, Optional[int]]:
        if library not in self._album_ids:
            ids: dict[str, Optional[int]] = {}
            for folder, rows in sorted(self.native.readback.folders(library).items()):
                found = _most_shared(rows)
                if found is not None:
                    ids[folder] = found
            self._album_ids[library] = ids
        return self._album_ids[library]

    def album_id(self, record: Record) -> Optional[int]:
        """Kodi's id for the album the record's songs were filed under: the
        one most of them share. A pass that reads the library's albums a row
        at a time reads the album's directory alone."""
        if self.native.readback.by_row("MusicAlbum", record.library):
            return self._directory_album(record.library, record.item_id)
        return self.album_ids(record.library).get(record.item_id)

    def _directory_album(self, library: str, folder: str) -> Optional[int]:
        key = (library, folder)
        if key not in self._album_of:
            self._album_of[key] = _most_shared(
                self.native.readback.scope("Audio", library, folder)
            )
        return self._album_of[key]

    def album_owner(self, albumid: int, library: str) -> Optional[str]:
        """Of our albums Kodi merged into one row, the first by id owns the
        row's art and description; the others are mapped and left. A pass
        that reads the library's albums a row at a time asks Kodi for the
        row's songs and reads only the directories they are in."""
        if self.native.readback.by_row("MusicAlbum", library):
            if albumid not in self._owner_of:
                self._owner_of[albumid] = min(
                    (
                        folder
                        for held_in, folder in self.native.readback.album_folders(
                            albumid
                        )
                        if self._directory_album(held_in, folder) == albumid
                    ),
                    default=None,
                )
            return self._owner_of[albumid]
        if self._album_owners is None:
            owners: dict[int, str] = {}
            for held_in in self.store.libraries("Audio"):
                for folder, found in sorted(self.album_ids(held_in).items()):
                    if found is not None and (
                        found not in owners or folder < owners[found]
                    ):
                        owners[found] = folder
            self._album_owners = owners
        return self._album_owners.get(albumid)

    def tag_hash(self, record: Record) -> str:
        """A song's tag hash, computed once a pass."""
        found = self._tag_hashes.get(record.item_id)
        if found is None:
            found = self._tag_hashes[record.item_id] = metadata.tag_hash(
                record.item, self.album_items(record.library).get(record.parent_id)
            )
        return found

    def finish(self, library: str, entries: abc.Mapping[str, Entry]) -> None:
        """Put back to pending whatever the scans just run should have
        filed and did not, and mark a library compared only once that
        check has run.

        A directory this pass was to list and did not leaves the library
        owing a whole compare, which finds the rows it holds. A scan that
        raised never reaches here, so a sweep a repair or a foreign scan
        marked stays due for the library.
        """
        # Every directory of the library this pass re-listed, the removal's
        # scans before this one included: none other can have lost a song.
        rescanned = {folder for lib, folder in self.rescanned if lib == library}
        if rescanned:
            lost = self.lost_songs(library, rescanned, entries)
            if lost:
                self.store.invalidate(lost)
                LOG.warning(
                    "music: %d acknowledged songs missing after the scan;"
                    " pending again",
                    len(lost),
                )
        # Every directory this pass re-listed has been checked.
        self.native.credit_music_scans(library)
        unread = {
            pair for pair in self.rescanned if pair[0] == library and pair[1] != "*"
        } - self.listed
        if unread:
            self.native.music_checked.discard(library)
            self.native.music_owed.add(library)
        elif library in self._compared:
            self.native.music_checked.add(library)
            self.native.music_owed.discard(library)

    def scan(self, library: str, folders: set[str], expected: int = 0) -> None:
        """Have Kodi list the changed album directories again.

        The directories are planned in listing order (``walk.rows``) and
        scanned a part at a time: each scan is of a directory that lists
        ``paths.MUSIC_PART`` of them, and the scanner goes into each.
        ``expected`` is the number of songs the scan should add, for the bar.
        """
        if not folders:
            return
        self.read_library = True
        every = walk.root_folders(self.store, library)
        rows = walk.rows(self.store, library, folders, self.album_items(library))
        # The applier reads the album payloads again after the scan; held
        # across it they are memory Kodi's scanner wants for its page cache.
        self._album_items.pop(library, None)
        self.store.plan_walk(library, rows)
        parts = walk.parts(len(rows))
        LOG.debug(
            "music: %d of %d directories changed; scanning them in %d part(s)",
            len(rows),
            len(every | set(folders)),
            parts,
        )
        began = time.monotonic()
        directories = [paths.music_part(self.key, library, n) for n in range(parts)]
        # One phase of the bar for the whole plan: Kodi's count of the
        # library's songs climbing towards ``expected`` across the parts,
        # where a phase a part would start the bar again thirty-two
        # directories on.
        native = self.native
        location = paths.parse(directories[0])
        heading = native.scan_heading(location, "music")
        saved = native.progress.phase(int(expected), heading) if expected else None
        try:
            native.scan(
                directories,
                "music",
                on_poll=(
                    native.scan_watch(location, heading, int(expected))
                    if saved is not None
                    else None
                ),
            )
        finally:
            if saved is not None:
                native.progress.restore(saved)
        LOG.debug(
            "music: %d directories scanned in %.1f s",
            len(rows),
            time.monotonic() - began,
        )
        self.rescanned.update((library, folder) for folder in folders)
        if every <= set(folders):
            self.rescanned.add((library, "*"))
        listed = self.store.listed(library) & set(folders)
        self.listed.update((library, folder) for folder in listed)
        if len(listed) < len(folders):
            LOG.debug(
                "music: Kodi read %d of the %d directories the scan was to list",
                len(listed),
                len(folders),
            )

    def lost_songs(
        self, library: str, folders: set[str], entries: abc.Mapping[str, Entry]
    ) -> list[str]:
        """Acknowledged songs the scan just run should have re-filed and did
        not: a listing that failed half way, or a scan stopped between its
        delete and its re-add. Nothing pending names them, so they are found
        by comparing what was acknowledged with what Kodi holds, and go back
        to pending for the next pass to re-list their directory (salted, if
        Kodi kept the hash of the listing that lost them)."""
        everywhere = (library, "*") in self.rescanned
        if everywhere:
            self.read_library = True
            held = self.native.readback.folders(library)
            mappings = self.song_mappings(library)
            _read_every(entries)
        else:
            held = {
                folder: self.native.readback.scope("Audio", library, folder)
                for folder in folders
            }
            mappings = self.store.mappings_of(
                self.store.placed_in("Audio", library, folders)
            )
            if isinstance(entries, Placements):
                entries.preload(mappings)
        lost: list[str] = []
        for item_id, known in mappings.items():
            if known.kodi_id is None:
                continue
            placed = entries.get(item_id)
            if placed is None or placed.kind != "Audio" or placed.library != library:
                continue
            if not everywhere and placed.parent_id not in folders:
                continue
            if item_id not in held.get(placed.parent_id, {}):
                lost.append(item_id)
        return lost

    def directories(
        self, upserts: dict[str, Record], library: str, entries: abc.Mapping[str, Entry]
    ) -> tuple[set[str], set[str]]:
        """The album directories whose listing Kodi must read again, split
        into those that hold a song with no row and the rest.

        A directory in both is returned with the new song only, and scanned
        once. A song with no row is missing; one whose tag hash moved since
        its row was acknowledged needs its tags re-read, which the scanner
        does only for a directory whose listing changed; one that moved
        album leaves its old directory only when that directory is listed
        without it. And a directory holding rows no live song of ours
        claims -- the old half of a move, or a listing that failed half
        way -- is settled by its complete listing too.

        Two kinds of applied song join the comparison uninvited: one whose
        album's payload moved, since its tags take the album's artists and
        MusicBrainz ids, and one Kodi does not hold (as ``lost_songs``).
        Either goes back to pending and into this pass. The first are the
        songs placed in the album's directory, read with it. The second
        needs every song of the library read, so that check runs when
        something can have changed what Kodi holds (``check_due``);
        otherwise only the pass's own songs are compared, each read with its
        directory.
        """
        songs = {
            r.item_id: r
            for r in upserts.values()
            if r.kind == "Audio" and r.library == library
        }
        fresh: set[str] = set()
        rest: set[str] = set()
        changed_albums = {
            r.item_id
            for r in upserts.values()
            if r.kind == "MusicAlbum" and r.library == library
        }
        whole = self.check_due(library, songs, changed_albums)
        if whole:
            self.read_library = True
            mappings = self.song_mappings(library)
            _read_every(entries)
            held = self.native.readback.folders(library)
            uninvited: list[str] = []
            for item_id, known in mappings.items():
                if item_id in songs or known.kodi_id is None:
                    continue
                placed = entries.get(item_id)
                if (
                    placed is None
                    or placed.kind != "Audio"
                    or placed.library != library
                ):
                    continue
                if (
                    item_id not in held.get(placed.parent_id, {})
                    or placed.parent_id in changed_albums
                ):
                    uninvited.append(item_id)
            if uninvited:
                songs.update(
                    self.store.records(
                        kind="Audio",
                        library=library,
                        item_ids=uninvited,
                        payloads=False,
                    )
                )
        else:
            if changed_albums:
                in_albums = [
                    item_id
                    for item_id in self.store.placed_in(
                        "Audio", library, changed_albums
                    )
                    if item_id not in songs
                ]
                filed = self.store.mappings_of(in_albums)
                songs.update(
                    self.store.records(
                        kind="Audio",
                        library=library,
                        item_ids=[
                            i
                            for i in in_albums
                            if i in filed and filed[i].kodi_id is not None
                        ],
                        payloads=False,
                    )
                )
            mappings = self.store.mappings_of(songs)
        revived: dict[str, Record] = {}
        if songs:
            # The bar names the phase and the log times it.
            began = time.monotonic()
            self.native.progress.note(progress.label("Audio"))

            def moved(record: Record, *, missing: bool) -> None:
                (fresh if missing else rest).add(record.parent_id)
                if record.item_id not in upserts:
                    revived[record.item_id] = record

            # Only a song with a row and an acknowledgement has tags to
            # compare, so only its payload is read.
            tagged: list[Record] = []
            for record in songs.values():
                item_id = record.item_id
                folder = record.parent_id
                row = self.native.readback.scope("Audio", library, folder).get(item_id)
                mapping = mappings.get(item_id)
                applied = mapping.applied if mapping else {}
                if row is None:
                    moved(record, missing=True)
                elif mapping is None:
                    # Imported but never acknowledged (a userdata patch
                    # failed): the row has the tags of the listing that made
                    # it unless the payload has moved since.
                    if record.generation > 1:
                        moved(record, missing=False)
                else:
                    tagged.append(record)
                previous = applied.get("dir")
                if previous and previous != folder:
                    rest.add(previous)
            # The walk is the long part (a payload parsed and a tag hash for
            # each song), so it is the part the bar counts.
            saved = self.native.progress.phase(len(tagged), progress.label("Audio"))
            try:
                for record in self.native.payloads.walk(tagged):
                    self.native.progress.step("Audio")
                    if mappings[record.item_id].applied.get("tag") != self.tag_hash(
                        record
                    ):
                        moved(record, missing=False)
            finally:
                self.native.progress.restore(saved)
            if revived:
                self.store.invalidate(revived)
                upserts.update(revived)
            LOG.debug(
                "music: %d songs compared in %.1f s; %d directories to scan,"
                " %d applied songs put back",
                len(songs),
                time.monotonic() - began,
                len(fresh | rest),
                len(revived),
            )
        if whole:
            for folder, rows in self.native.readback.folders(library).items():
                for item_id in rows:
                    placed = entries.get(item_id)
                    if (
                        placed is None
                        or placed.kind != "Audio"
                        or placed.library != library
                        or placed.parent_id != folder
                    ):
                        rest.add(folder)
                        break
            self._compared.add(library)
        rest -= fresh
        return fresh, rest

    def check_due(
        self, library: str, songs: dict[str, Record], changed_albums: Collection[str]
    ) -> bool:
        """Whether this pass compares every song of the library with Kodi's
        rows: a sweep is marked and this library has not been compared
        since (a repair, a music scan or clean that was not the pass's
        own), a pass left one of its directories unread, or the pass's songs
        and moved albums span enough directories that the library is read
        whole anyway. Below that, a moved album has the songs placed in its
        directory compared (``directories``)."""
        return (
            (self.native.music_sweep and library not in self.native.music_checked)
            or library in self.native.music_owed
            or len({r.parent_id for r in songs.values()} | set(changed_albums))
            >= self.native.readback.WHOLE_LIBRARY_FOLDERS
        )


def _read_every(entries: abc.Mapping[str, Entry]) -> None:
    """Every placement at once, for a caller about to read most of them one
    by one; a plain dict already holds them."""
    if isinstance(entries, Placements):
        entries.whole()


def _most_shared(rows: abc.Mapping[str, dict]) -> Optional[int]:
    """The album id most of a directory's song rows share, or None."""
    counted = collections.Counter(
        row.get("albumid") for row in rows.values() if row.get("albumid")
    )
    return counted.most_common(1)[0][0] if counted else None
