"""The apply pass: desired state against the scanner's row, patched only
where they differ, confirmed by readback, acknowledged by the batch.

Setters merge maps and replace tags, so a patch clears only the keys Kofin
owned last time and keeps what Kodi or the user added. A refresh is the one
operation that replaces a row: cast and streams have no setter.

Music is confirmed by the scope, not the row. A song's patch is its play
count and last played; thousands of them on a first import would cost a
details call each to confirm, so the kinds the scanner derives are patched
in batches and then read back in one listing per library.
"""

import time
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import unquote

from kofin.core.log import Logger
from . import metadata, paths
from .kinds import (
    BATCH,
    DERIVED,
    EXPECTED,
    FILED,
    KINDS,
    ORDER,
    PLAYABLE,
    properties,
    rpc,
    rpc_batch,
)
from .readback import OWN_FOLDER
from .records import Record
from . import downloaded
from .store import Mapping, hash_matches, payload_hash

if TYPE_CHECKING:
    from .native import Native

LOG = Logger(__name__)

# A refresh takes seconds; re-reading every poll would ask Kodi dozens of
# times for one changed item. A movie or a show is read by its folder
# (Readback.item); an episode's refresh re-lists its show's scope.
REFRESH_POLL = 1.0

# A pass of at least this many rows reads every mapping in one query; a
# smaller one reads only its own, which is most passes: a play, a favourite,
# a catch-up of a few items.
PRELOAD_ALL_MAPPINGS = 2000


def _with_asset_files(
    applied: dict[str, Any],
    assets: Optional[str],
    files: Optional[dict[str, Any]],
    previous: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """The acknowledged file list beside the token: the movie's current
    assets, or the empty entry once a movie that had assets has none
    (metadata.asset_files). ``previous`` is the last acknowledgement as it
    was read; whether the movie had assets is read from it, by its file
    list or, for an acknowledgement older than the list, by its assets
    token."""
    if assets is None:
        return applied
    before = previous if previous is not None else applied
    had = "asset_files" in before or bool(before.get("assets"))
    if files is not None:
        if applied.get("asset_files") != files:
            applied = dict(applied, asset_files=files)
    elif had and applied.get("asset_files") != metadata.NO_ASSET_FILES:
        applied = dict(applied, asset_files=metadata.NO_ASSET_FILES)
    return applied


def _listed(asset_files: Optional[dict[str, Any]]) -> set[str]:
    """Every URL an acknowledged file list names."""
    if not isinstance(asset_files, dict):
        return set()
    return {str(entry[0]) for entry in asset_files.get("versions") or []} | {
        str(url) for url in asset_files.get("extras") or []
    }


def assets_dropped(previous: dict[str, Any], applied: dict[str, Any]) -> bool:
    """Whether a version file or an extra the movie's folder listed has
    left its listing. An acknowledgement older than the file list names no
    files: a token that moved off a non-empty one may have lost some."""
    if "asset_files" not in previous:
        return bool(previous.get("assets")) and previous.get("assets") != applied.get(
            "assets"
        )
    return bool(_listed(previous["asset_files"]) - _listed(applied.get("asset_files")))


# The fields a video setter announces when it moves them: it calls
# CVideoDatabase::SetPlayCount, which announces OnUpdate. Every other field,
# the resume point included, is written without an announcement a home
# widget hears.
ANNOUNCED = frozenset(("playcount", "lastplayed"))


class Patch:
    def __init__(
        self,
        record: Record,
        kodi_id: int,
        desired: dict[str, Any],
        compare: dict[str, Any],
        applied: dict[str, Any],
    ) -> None:
        self.record = record
        self.kodi_id = kodi_id
        self.desired = desired
        self.compare = compare
        self.applied = applied


class Applier:
    def __init__(self, native: "Native") -> None:
        self.native = native
        self.store = native.store
        self.key = native.key
        self.readback = native.readback
        # Per-pass write batches.
        self._acks: list[tuple[str, int, Optional[int], dict[str, Any], str]] = []
        self._expectations: list[tuple[str, int, dict[str, Any]]] = []
        self._mappings: dict[str, Any] = {}
        self._mappings_loaded = False
        # The items whose mappings were read, or None when every one was.
        self._preloaded: Optional[set[str]] = None
        self.collections: dict[str, str] = {}
        self.movies: set[str] = set()
        # Title to the collection id that owns Kodi's one set of that name.
        self.set_owners: dict[str, str] = {}
        self.local: set[str] = set()
        # Per show: the season numbers with an importable episode.
        self._seasons_with_episodes: dict[str, set[int]] = {}
        self._deferred: list[Patch] = []
        self._rpc_seconds = 0.0
        # Whether this run's music writes hold the scanner (run, flush).
        self._hold_music = False
        self._failures: list[tuple[str, int, str]] = []
        self._salted: set[str] = set()
        # Downloaded items and the shows with a downloaded episode: their
        # rows carry the badge and the tag (downloaded.py), read once a pass.
        self.downloaded: set[str] = set()
        self.downloaded_series: dict[str, set[str]] = {}
        self._downloaded_seasons: dict[str, set[int]] = {}
        # Whether a video patch of this pass moves a field outside ANNOUNCED,
        # or clears a season's name: Kodi's setter announces neither
        # (Native.announce_writes).
        self.unannounced = False
        # Folders of movies whose listing dropped a version file or an
        # extra this pass: cleaned once the pass has applied
        # (Native.retire_assets).
        self.asset_folders: set[str] = set()

    # -- batches -------------------------------------------------------------

    def _note_dropped_assets(
        self, record: Record, previous: dict[str, Any], applied: dict[str, Any]
    ) -> None:
        if record.kind == "Movie" and assets_dropped(previous, applied):
            self.asset_folders.add(
                paths.movie_dir(self.key, record.library, record.item_id)
            )

    def ack(
        self,
        item_id: str,
        generation: int,
        kodi_id: Optional[int],
        applied: dict[str, Any],
        kind: str,
    ) -> None:
        self._acks.append((item_id, generation, kodi_id, applied, kind))
        if len(self._acks) >= 200:
            self.commit()

    def fail(self, record: Record, error: Exception, errors: list[Exception]) -> None:
        """Record a failure for the batch and keep the error for the pass."""
        self._failures.append(
            (
                record.item_id,
                record.generation,
                type(error).__name__ + ": " + str(error),
            )
        )
        errors.append(error)
        if len(self._failures) >= 200:
            self.commit()

    def commit(self) -> None:
        if self._failures:
            failures, self._failures = self._failures, []
            self.store.failed_many(failures)
        if self._expectations:
            self.store.expect_many(self._expectations)
            self._expectations = []
        if self._acks:
            acks, self._acks = self._acks, []
            self.store.remember_many(acks)
            if self._mappings_loaded:
                # Keep the preloaded mappings current instead of reloading
                # them.
                for item_id, _, kodi_id, applied, kind in acks:
                    self._mappings[item_id] = Mapping(kodi_id, applied or {}, kind)

    def mapping(self, item_id: str) -> Optional[Mapping]:
        if self._mappings_loaded and (
            self._preloaded is None or item_id in self._preloaded
        ):
            return self._mappings.get(item_id)
        return self.store.mapping(item_id)

    # -- the pass ------------------------------------------------------------

    def run(
        self,
        upserts: dict[str, Record],
        collections: dict[str, str],
        movies: set[str],
        repair: bool,
        errors: list[Exception],
        kinds: Sequence[str] = ORDER,
    ) -> None:
        """Plan and patch the pass's records of ``kinds``, in that order."""
        # One music row is one setter at most, whose announcement refreshes
        # the home widgets once, as the end of a hold would.
        self._hold_music = (
            sum(
                1
                for r in upserts.values()
                if r.kind in kinds and KINDS[r.kind].removal == "rescan"
            )
            > 1
        )
        self.downloaded, self.downloaded_series = downloaded.marks()
        self._downloaded_seasons = {}
        self.collections = collections
        self.movies = movies
        # The collection that owns each title's one set: the lowest id
        # whose members are filed under it. One with none is rowless.
        self.set_owners = {}
        for record in upserts.values():
            if record.kind != "BoxSet":
                continue
            title = (record.item.get("Name") or "").strip(paths.ASCII_SPACE)
            members = record.item.get("KofinMembers") or []
            if not title or not any(
                member in self.movies and self.collections.get(member) == title
                for member in members
            ):
                continue
            if title not in self.set_owners or record.item_id < self.set_owners[title]:
                self.set_owners[title] = record.item_id
        self.local = {item_id for item_id, _ in self.store.local_pending()}
        if not self._mappings_loaded:
            if len(upserts) >= PRELOAD_ALL_MAPPINGS:
                self._mappings = self.store.mappings()
                self._preloaded = None
            else:
                self._mappings = self.store.mappings_of(upserts)
                self._preloaded = set(upserts)
            self._mappings_loaded = True
        queue: list[Patch] = []
        for kind in kinds:
            ids = sorted(i for i, r in upserts.items() if r.kind == kind)
            if not ids:
                continue
            began = time.monotonic()
            self._rpc_seconds = 0.0
            # The kind's name before its first row is counted: the readback
            # that comes first can take as long as the rows themselves.
            self.native.progress.applying(kind, len(ids))
            if kind == "BoxSet":
                # A library clear reads the set listing to see what it
                # emptied, and a movie patched since may have made a set that
                # listing never saw.
                self.readback.forget("BoxSet")
            if KINDS[kind].removal != "rescan":
                # A scope mostly about to be compared is read in full once.
                per_scope: dict[tuple[str, str], int] = {}
                for item_id in ids:
                    record = upserts[item_id]
                    scope = (record.library, record.parent_id)
                    if kind == "BoxSet":
                        scope = ("", "")
                    per_scope[scope] = per_scope.get(scope, 0) + 1
                for (library, parent_id), count in per_scope.items():
                    try:
                        self.readback.prefetch_full(kind, library, parent_id, count)
                    except InterruptedError:
                        raise
                    except Exception as error:
                        LOG.debug("full readback not prefetched: %s", error)
            for record in self.native.payloads.walk(upserts[i] for i in ids):
                try:
                    if self.native.abort():
                        raise InterruptedError("native sync stopped")
                    self.native.progress.step(kind)
                    patch = self.plan(record, repair)
                    if patch is not None:
                        queue.append(patch)
                        if len(queue) >= BATCH:
                            self.flush(queue, errors)
                except InterruptedError:
                    raise
                except Exception as error:
                    self.fail(record, error, errors)
            self.flush(queue, errors)
            if KINDS[kind].removal == "rescan":
                self.confirm_by_scope(kind, errors)
            self.commit()
            if kind == kinds[-1] or KINDS[kind].removal != "rescan":
                self.native.release_all()
            LOG.debug(
                "%s: %d planned in %.1f s, %.1f s of it in Kodi calls",
                kind.lower(),
                len(ids),
                time.monotonic() - began,
                self._rpc_seconds,
            )

    def row_for(self, record: Record) -> Optional[dict[str, Any]]:
        kind = record.kind
        if kind == "Audio":
            return self.readback.scope("Audio", record.library, record.parent_id).get(
                record.item_id
            )
        if kind == "MusicAlbum":
            albumid = self.native.music.album_id(record)
            if albumid is None:
                return None
            return self.readback.album(record.library, albumid)
        if kind == "MusicArtist":
            return self.readback.artist(record.library, record.item.get("Name"))
        if kind == "Season":
            number = record.item.get("IndexNumber")
            if number is None:
                return None
            return self.readback.scope("Season", record.library, record.parent_id).get(
                int(number)
            )
        if kind == "BoxSet":
            name = (record.item.get("Name") or "").strip(paths.ASCII_SPACE)
            return self.readback.scope("BoxSet").get(name)
        if kind == "Series":
            return self.readback.show(record.library, record.item_id)
        if kind == "Movie":
            return self.readback.movie(record.library, record.item_id)
        return self.readback.scope(kind, record.library, record.parent_id).get(
            record.item_id
        )

    def rowless(self, record: Record) -> bool:
        """Whether an item of this kind is applied with no native row.

        Kodi cannot file an unnumbered special; GetSeasons joins episodes,
        so an empty season is invisible; a set exists only once a movie Kodi
        holds has filed it under that very name -- a collection whose movies
        are outside the selected libraries, or the one a movie in two
        collections did not take, never has a row to find.
        """
        kind = record.kind
        if kind == "Episode":
            return metadata.episode_numbers(record.item) is None
        if kind == "Season":
            return not self.season_has_episodes(record)
        if kind == "MusicAlbum":
            # An album Kodi derives exists only through songs of ours in it.
            return record.item_id not in self.native.music.song_folders(record.library)
        if kind == "MusicArtist":
            # An artist no live album credits -- a guest on a track, or one
            # whose albums are outside the selection -- has no row of ours to
            # find by name, and one whose albums have rows but whose name
            # Kodi spells otherwise has none either. One whose album the
            # scanner has not filed yet is waiting for its row.
            if record.item_id not in self.native.music.credited(record.library):
                return True
            if self.row_for(record) is not None:
                return False
            return self.native.music.albums_filed(record.library, record.item_id)
        if kind == "BoxSet":
            name = (record.item.get("Name") or "").strip(paths.ASCII_SPACE)
            return not any(
                member in self.movies and self.collections.get(member) == name
                for member in record.item.get("KofinMembers") or []
            )
        return False

    def plan(self, record: Record, repair: bool) -> Optional[Patch]:
        """The patch a record needs, or None once it is acknowledged, left to
        a viewer's edit or to the item of ours that owns its row; raises when
        the scanner has not filed it yet. In order: the kinds applied without
        a row, a collection sharing its title's set, the row, music's own
        plan, the viewer's edit, the row another item owns, the
        acknowledgement short-circuit, the refresh, the compare.
        """
        kind = record.kind
        if self.rowless(record):
            self.ack(record.item_id, record.generation, None, {}, kind)
            return None
        row = self._filed_row(record)
        if kind == "BoxSet":
            # Kodi holds one set of the title. The lowest id with a row owns
            # its plot. Another collection of the title is acknowledged
            # against that row.
            title = (record.item.get("Name") or "").strip(paths.ASCII_SPACE)
            if self.set_owners.get(title) not in (None, record.item_id):
                self.ack(
                    record.item_id,
                    record.generation,
                    row[KINDS[kind].id_param],
                    {},
                    kind,
                )
                return None
        if kind in DERIVED or kind == "Audio":
            return self.plan_music(record, row, repair)
        seasons = (
            [
                r.item
                for r in self.store.records(
                    kind="Season", parent_id=record.item_id
                ).values()
            ]
            if kind == "Series"
            else ()
        )
        set_name = self.collections.get(record.item_id, "") if kind == "Movie" else None
        mark = downloaded.flag(
            kind,
            record.item_id,
            self.downloaded,
            self.downloaded_series,
            season=kind == "Season" and self.season_is_downloaded(record),
        )
        mapping = self.mapping(record.item_id)
        previous = mapping.applied if mapping else {}
        if self._viewer_edited(record, row, previous):
            return None
        kodi_id = row[KINDS[kind].id_param]
        if self._owned_by_another(record, row, kodi_id):
            return None
        payload = payload_hash(record.item)
        inputs = metadata.inputs_token(
            self.native.server_url(),
            self.key,
            record.library,
            self.native.separator,
            seasons,
            set_name,
            downloaded=mark,
            features=self.native.features,
        )
        assets, files = self._assets(record)
        if self._acknowledged(
            record, kodi_id, mapping, previous, inputs, assets, files, repair
        ):
            return None
        desired = metadata.details(
            record.item,
            self.native.server_url(),
            self.key,
            record.library,
            self.native.separator,
            seasons,
            set_name,
            features=self.native.features,
        )
        downloaded.apply(kind, desired, mark)
        parts = metadata.refresh_parts(record.item, seasons) if kind in FILED else {}
        if kind in FILED:
            row = self._refreshed(record, row, kodi_id, desired, parts, previous)
            kodi_id = row[KINDS[kind].id_param]
        # Only now the full row: the scope carries what finds and owns it.
        row = self.readback.full(kind, record.library, record.parent_id, row)
        applied = {
            "hash": payload,
            "inputs": inputs,
            "owned": metadata.owned(desired),
        }
        if parts:
            applied["refresh"] = parts
        if assets is not None:
            applied["assets"] = assets
        applied = _with_asset_files(applied, assets, files, previous)
        self._note_dropped_assets(record, previous, applied)
        return self._compared(
            record, row, kodi_id, desired, applied, previous, mapping, repair
        )

    def _filed_row(self, record: Record) -> dict:
        """The row Kodi filed for the record; raises when the scanner has not
        imported it. A season, a set or an album has its episodes, movies or
        songs imported this pass or the next, with nothing native to confirm
        yet. A song listed and scanned this pass and still absent is a
        directory Kodi skipped "due to no change": its listing is salted,
        once per directory and pass, so the next scan sees a change
        (store.salt)."""
        row: Optional[dict] = self.row_for(record)
        if row is not None:
            return row
        kind = record.kind
        if kind in ("Season", "BoxSet", "MusicAlbum"):
            raise RuntimeError("%s has no native row yet" % kind)
        if kind == "Audio" and (
            (record.library, record.parent_id) in self.native.music.rescanned
            or (record.library, "*") in self.native.music.rescanned
        ):
            if record.parent_id not in self._salted:
                self._salted.add(record.parent_id)
                self.store.bump_salt(record.parent_id)
            raise RuntimeError(
                "scanner did not import Audio; directory salted (%d)"
                % self.store.salt(record.parent_id)
            )
        raise RuntimeError("scanner did not import %s" % kind)

    def _viewer_edited(
        self, record: Record, row: dict[str, Any], previous: dict[str, Any]
    ) -> bool:
        """Whether a viewer's edit of the row goes first: a real edit is
        delivered before any server snapshot and never overwritten by an
        older one during a retry or a refresh. The scope row carries the
        userdata, so the edit is seen before anything else is read or
        built."""
        if record.item_id in self.local:
            return True
        if record.kind in PLAYABLE and previous.get("userdata"):
            edits = local_edits(
                row, previous["userdata"], metadata.userdata(record.item)
            )
            if edits:
                self.store.local(record.item_id, edits)
                return True
        return False

    def _owned_by_another(
        self, record: Record, row: dict[str, Any], kodi_id: int
    ) -> bool:
        """Two items of ours that Kodi filed on one row (one show in two of
        our libraries, one movie Kodi grouped with another): the one whose
        id the row carries owns its details, and this one is mapped to it
        and left."""
        kind = record.kind
        owner = self.readback.row_owner(row) if kind in ("Series", "Movie") else None
        if owner is None or owner == record.item_id:
            return False
        LOG.debug(
            "%s %s shares Kodi's row %d with %s",
            kind.lower(),
            record.item_id,
            kodi_id,
            owner,
        )
        self.ack(record.item_id, record.generation, kodi_id, {}, kind)
        return True

    def _assets(self, record: Record) -> tuple[Optional[str], Optional[dict[str, Any]]]:
        """The versions and extras a movie's folder listed, as the token and
        the file list, acknowledged so the pass stops scanning the folder
        for them (native._asset_folders); None for every other kind."""
        if record.kind != "Movie":
            return None, None
        return (
            metadata.assets_token(record.item, self.native.features),
            metadata.asset_files(
                record.item, self.key, record.library, self.native.features
            ),
        )

    def _acknowledged(
        self,
        record: Record,
        kodi_id: int,
        mapping: Optional[Mapping],
        previous: dict[str, Any],
        inputs: str,
        assets: Optional[str],
        files: Optional[dict[str, Any]],
        repair: bool,
    ) -> bool:
        """The desired state this payload and these inputs produce was
        acknowledged against this very row: nothing to build, read or
        compare. A retried pass and a re-published item take this path, and
        a repair never does."""
        kind = record.kind
        if (
            not repair
            # A set's id is no proof of its row: Kodi numbers a new set from
            # the highest one left, so a set deleted and made again answers
            # under the number it was acknowledged by (Native.join_sets).
            and kind != "BoxSet"
            # Another source's scan took our ids off the show's row: the row
            # Kodi holds is no longer the one acknowledged.
            and not (
                kind == "Series"
                and self.readback.stripped(record.library, record.item_id)
            )
            and mapping is not None
            and mapping.kodi_id == kodi_id
            and hash_matches(previous.get("hash"), record.item)
            and previous.get("inputs") == inputs
        ):
            acked = previous
            if assets is not None and previous.get("assets", "") != assets:
                acked = dict(previous, assets=assets)
            acked = _with_asset_files(acked, assets, files, previous)
            self._note_dropped_assets(record, previous, acked)
            self.ack(record.item_id, record.generation, kodi_id, acked, kind)
            return True
        return False

    def _refreshed(
        self,
        record: Record,
        row: dict[str, Any],
        kodi_id: int,
        desired: dict[str, Any],
        parts: dict[str, str],
        previous: dict[str, Any],
    ) -> dict[str, Any]:
        """The row after the refresh a moved token calls for, or the row as
        it is: listed under another source's folder or file, a show or a
        movie would be refreshed from that source, and the setter writes our
        ids instead."""
        kind = record.kind
        token = desired["uniqueid"]["kofinrefresh"]
        if (row.get("uniqueid") or {}).get("kofinrefresh") == token:
            return row
        if (
            kind == "Series"
            and not self.readback.own_folder(record.library, record.item_id, row)
        ) or (
            kind == "Movie"
            and not self.readback.own_file(record.library, record.item_id, row)
        ):
            LOG.debug(
                "%s %s is listed under another source's file: not refreshed",
                kind.lower(),
                record.item_id,
            )
            return row
        LOG.debug(
            "refreshing %s %s: %s",
            kind.lower(),
            record.item_id,
            moved_parts(previous.get("refresh"), parts),
        )
        return self.refresh(record, kodi_id, token)

    def _compared(
        self,
        record: Record,
        row: dict[str, Any],
        kodi_id: int,
        desired: dict[str, Any],
        applied: dict[str, Any],
        previous: dict[str, Any],
        mapping: Optional[Mapping],
        repair: bool,
    ) -> Optional[Patch]:
        """The patch for a row that differs from the desired state, or None
        for one acknowledged as it stands. Repair re-sends a row whose
        acknowledged hash moved, for the fields a readback cannot show; a
        row with no acknowledgement yet was just filed by the scanner from
        this very listing, so there is nothing stale behind it, and the pass
        that follows every complete enumeration runs as a repair. A
        withdrawn season name is a clear the readback cannot show."""
        kind = record.kind
        compare = merge(kind, desired, row, previous.get("owned", {}))
        if kind in PLAYABLE:
            applied["userdata"] = metadata.userdata(record.item)
        if kind in EXPECTED:
            self._expectations.append(
                (record.item_id, record.generation, applied["userdata"])
            )
        clearing = kind == "Season" and desired.get("title") == ""
        if (
            not clearing
            and matches(row, compare)
            and (
                not repair
                or mapping is None
                or hash_matches(previous.get("hash"), record.item)
            )
        ):
            self.ack(record.item_id, record.generation, kodi_id, applied, kind)
            return None
        if clearing or any(
            key not in ANNOUNCED and not matches(row, {key: value})
            for key, value in compare.items()
        ):
            self.unannounced = True
        return Patch(record, kodi_id, desired, compare, applied)

    def plan_music(
        self, record: Record, row: dict[str, Any], repair: bool
    ) -> Optional[Patch]:
        kind = record.kind
        table = KINDS[kind]
        kodi_id = row[table.id_param]
        mapping = self.mapping(record.item_id)
        previous = mapping.applied if mapping else {}
        desired = metadata.details(record.item, self.native.server_url(), self.key, "")
        applied: dict[str, Any] = {
            "hash": payload_hash(record.item),
            "owned": metadata.owned(desired),
        }
        if kind == "Audio":
            if record.item_id in self.local:
                return None
            if previous.get("userdata"):
                edits = local_edits(row, previous["userdata"], desired)
                if edits:
                    self.store.local(record.item_id, edits)
                    return None
            applied["tag"] = self.native.music.tag_hash(record)
            applied["dir"] = record.parent_id
            applied["userdata"] = metadata.userdata(record.item)
            if previous.get("tag") not in (None, applied["tag"]) and (
                (record.library, record.parent_id) not in self.native.music.listed
            ):
                # The tags moved and Kodi was not handed the directory's
                # listing this pass: the row still carries the old ones.
                raise RuntimeError("song awaits its directory's rescan")
        elif kind == "MusicAlbum":
            owner = self.native.music.album_owner(kodi_id, record.library)
            if owner is not None and owner != record.item_id:
                # Kodi merged two of our albums into one row; the first owns
                # its art and description, the other is mapped and left.
                self.ack(record.item_id, record.generation, kodi_id, {}, kind)
                return None
        elif kind == "MusicArtist":
            if self.native.music.artist_owner(record) != record.item_id:
                self.ack(record.item_id, record.generation, kodi_id, {}, kind)
                return None
        compare = merge(kind, desired, row, previous.get("owned", {}))
        if matches(row, compare) and (
            # A song's desired state is its play count and last played, and
            # the readback shows both: a matching row has nothing a repair
            # could re-send, and the setter is not free -- without the
            # song_date_added feature UpdateSong rewrites the song's dateAdded
            # to the moment of the call.
            kind == "Audio"
            # As for video (plan): a row with no acknowledgement was filed
            # by the scanner from this very listing.
            or not repair
            or mapping is None
            or hash_matches(previous.get("hash"), record.item)
        ):
            self.ack(record.item_id, record.generation, kodi_id, applied, kind)
            return None
        return Patch(record, kodi_id, desired, compare, applied)

    def season_is_downloaded(self, season: Record) -> bool:
        number = season.item.get("IndexNumber")
        if number is None or season.parent_id not in self.downloaded_series:
            return False
        return int(number) in self.downloaded_seasons(season.parent_id)

    def downloaded_seasons(self, series_id: str) -> set[int]:
        """The season numbers of a show that hold a downloaded episode, read
        once a show: the payloads of its downloaded episodes, which are few,
        and only for a show that has any."""
        if series_id not in self._downloaded_seasons:
            found: set[int] = set()
            episodes = sorted(self.downloaded_series.get(series_id) or ())
            for item in self.store.payloads(episodes).values():
                numbers = metadata.episode_numbers(item)
                if numbers is not None:
                    found.add(numbers["season"])
            self._downloaded_seasons[series_id] = found
        return self._downloaded_seasons[series_id]

    def season_has_episodes(self, season: Record) -> bool:
        number = season.item.get("IndexNumber")
        if number is None:
            return False
        return int(number) in self.seasons_with_episodes(season.parent_id)

    def seasons_with_episodes(self, series_id: str) -> set[int]:
        """The season numbers of a show that hold an importable episode,
        read once a show."""
        if series_id not in self._seasons_with_episodes:
            found: set[int] = set()
            for episode in self.store.records(
                kind="Episode", parent_id=series_id
            ).values():
                numbers = metadata.episode_numbers(episode.item)
                if numbers is not None:
                    found.add(numbers["season"])
            self._seasons_with_episodes[series_id] = found
        return self._seasons_with_episodes[series_id]

    # -- refresh -------------------------------------------------------------

    def refresh(self, record: Record, kodi_id: int, token: str) -> dict[str, Any]:
        """Re-import a row whose cast or streams changed; confirmed by token.

        A show is refreshed alone (``refreshepisodes`` false): Kodi rewrites
        the show's own row from the listing, cast included, and keeps its
        id, its seasons and its episodes (CVideoInfoScanner::
        RetrieveInfoForTvShow, the refresh-show-info-only branch). Asked to
        refresh the episodes too, it deletes the show and every episode and
        imports them again under new ids. A show refresh cannot change the
        plot of a season Kodi already has (AddSeason only inserts); the
        season's own patch does that (SetSeasonDetails).
        """
        kind = record.kind
        table = KINDS[kind]
        if table.refresh is None:
            raise RuntimeError("%s has no refresh" % kind)
        self.readback.owned(
            kind, kodi_id, record.item_id, record.library, record.parent_id
        )
        params: dict[str, Any] = {table.id_param: kodi_id, "ignorenfo": False}
        if kind == "Series":
            params["refreshepisodes"] = False
        self.native.replaced.add((kind, kodi_id))
        rpc(table.refresh, params)
        self.native._async_pending = True
        last = [0.0]
        own_folder = kind in OWN_FOLDER
        versions: list[dict[str, Any]] = []

        def refreshed() -> Optional[dict[str, Any]]:
            nonlocal versions
            now = time.monotonic()
            if now - last[0] < REFRESH_POLL:
                return None
            last[0] = now
            if own_folder:
                found, versions = self.readback.item(
                    kind, record.library, record.item_id
                )
            else:
                self.readback.forget(kind, record.library, record.parent_id)
                found = self.readback.scope(kind, record.library, record.parent_id).get(
                    record.item_id
                )
            if found and (found.get("uniqueid") or {}).get("kofinrefresh") == token:
                return found
            return None

        row = self.native.wait(refreshed, busy=self.native._scanning)
        assert row is not None  # wait returns only a value that holds
        self.native._async_pending = False
        if own_folder:
            self.readback.refreshed(
                kind,
                record.library,
                record.parent_id,
                record.item_id,
                kodi_id,
                row,
                versions,
            )
        return row

    # -- patches -------------------------------------------------------------

    def confirm_by_scope(self, kind: str, errors: list[Exception]) -> None:
        """Read the kind's rows back in one listing per library and settle
        every deferred patch against it."""
        if not self._deferred:
            return
        patches, self._deferred = self._deferred, []
        for library in sorted({p.record.library for p in patches}):
            self.readback.forget(kind, library)
            if kind == "Audio":
                self.readback.songs_in(
                    library,
                    (
                        p.record.parent_id
                        for p in patches
                        if p.record.library == library
                    ),
                )
        for patch in patches:
            record = patch.record
            try:
                row = self.row_for(record)
                if row is None:
                    raise RuntimeError("%s row vanished after its patch" % kind)
                if not matches(row, patch.compare):
                    fields = [
                        key
                        for key, value in patch.compare.items()
                        if not matches(row, {key: value})
                    ]
                    raise RuntimeError(
                        "%s detail readback differs: %s" % (kind, ", ".join(fields))
                    )
                self.ack(
                    record.item_id,
                    record.generation,
                    patch.kodi_id,
                    patch.applied,
                    kind,
                )
            except InterruptedError:
                raise
            except Exception as error:
                self.fail(record, error, errors)

    def flush(self, queue: list[Patch], errors: list[Exception]) -> None:
        if not queue:
            return
        patches, queue[:] = list(queue), []
        # Expectations go in ahead of the setters they cover.
        if self._expectations:
            self.store.expect_many(self._expectations)
            self._expectations = []
        # Kodi logs no announcements, so this line is the only count of
        # what a pass actually wrote (an import whose rows match sends none).
        LOG.debug("patching %d %s rows", len(patches), patches[0].record.kind.lower())
        if KINDS[patches[0].record.kind].removal == "rescan" and self._hold_music:
            # Writes announced during a music scan are a transaction to the
            # home widgets: hold the scanner for the burst (native.hold).
            self.native.hold("music")
        setters: list[tuple[str, Optional[dict[str, Any]]]] = []
        for patch in patches:
            table = KINDS[patch.record.kind]
            params = dict(patch.desired)
            params[table.id_param] = patch.kodi_id
            setters.append((table.setter, params))
        began = time.monotonic()
        replies = rpc_batch(setters)
        self._rpc_seconds += time.monotonic() - began
        # Every setter announced its row (native.pump).
        self.native.pump()
        confirmations: list[tuple[str, Optional[dict[str, Any]]]] = []
        confirming = []
        for patch, reply in zip(patches, replies):
            if isinstance(reply, Exception):
                self.fail(patch.record, reply, errors)
                continue
            table = KINDS[patch.record.kind]
            if table.removal == "rescan":
                # Confirmed by the scope once the kind's patches are all sent.
                self._deferred.append(patch)
                continue
            confirmations.append(
                (
                    table.getter,
                    {
                        table.id_param: patch.kodi_id,
                        "properties": properties(
                            patch.record.kind, self.native.features
                        ),
                    },
                )
            )
            confirming.append(patch)
        for patch, reply in zip(confirming, rpc_batch(confirmations)):
            record = patch.record
            try:
                if isinstance(reply, Exception):
                    raise reply
                row = (
                    reply.get(KINDS[record.kind].result_key, {})
                    if isinstance(reply, dict)
                    else {}
                )
                if record.kind in FILED and not self.readback.holds(
                    record.kind, row, record.library, record.item_id, record.parent_id
                ):
                    raise RuntimeError("%s ownership changed" % record.kind)
                if not matches(row, patch.compare):
                    fields = [
                        key
                        for key, value in patch.compare.items()
                        if not matches(row, {key: value})
                    ]
                    raise RuntimeError(
                        "%s detail readback differs: %s"
                        % (record.kind, ", ".join(fields))
                    )
                self.ack(
                    record.item_id,
                    record.generation,
                    patch.kodi_id,
                    patch.applied,
                    record.kind,
                )
                cache_key: Any = record.item_id
                if record.kind == "Season":
                    cache_key = int(record.item.get("IndexNumber") or 0)
                elif record.kind == "BoxSet":
                    cache_key = row.get("title", "")
                self.readback.remember(
                    record.kind, record.library, record.parent_id, cache_key, row
                )
            except InterruptedError:
                raise
            except Exception as error:
                self.fail(record, error, errors)


def moved_parts(before: Optional[dict[str, str]], now: dict[str, str]) -> str:
    """Which parts of a refresh token moved, for the log. A row acknowledged
    by an earlier build has no parts on record, and one the scanner filed
    and nothing acknowledged has none either."""
    if not before:
        return "what moved is not on record"
    moved = sorted(
        part for part in set(before) | set(now) if before.get(part) != now.get(part)
    )
    return "its %s moved" % ", ".join(moved) if moved else "nothing on record moved"


def local_edits(
    row: dict[str, Any], previous: dict[str, Any], desired: dict[str, Any]
) -> dict[str, Any]:
    """Userdata the viewer changed in Kodi since the last write, if any.

    A viewer's edit of a play count is the watched mark going on or off. A
    count that differs only in size is Kodi and the server having counted
    differently, and the server's count is then written to Kodi like any
    other field.

    A song's mark never comes off in Kodi, which has no way to unmark one: a
    played song at zero is a row a scan built again, and the server's count
    goes back into it."""
    edits = {}
    playcount = row.get("playcount", 0) or 0
    watched = bool(playcount)
    song = "resume" not in desired
    if (
        watched != bool(previous.get("playcount"))
        and watched != bool(desired["playcount"])
        and (watched or not song)
    ):
        edits["playcount"] = playcount
    if song:
        # Kodi's music library keeps no resume point either.
        return edits
    position = (row.get("resume") or {}).get("position", 0) or 0
    if (
        abs(position - previous.get("resume", {}).get("position", 0)) >= 1
        and abs(position - desired["resume"]["position"]) >= 1
    ):
        edits["position"] = position
    return edits


def tag_key(tag: str) -> str:
    """A tag as Kodi's tag table tells tags apart. Kodi files a tag by
    ``like`` against the names it holds (CVideoDatabase::AddToTable), which
    ignores ASCII case, so a row links to the spelling filed first whatever
    spelling it was sent."""
    return "".join(c.lower() if "A" <= c <= "Z" else c for c in tag)


def merge(
    kind: str,
    desired: dict[str, Any],
    row: dict[str, Any],
    owned_before: dict[str, list[str]],
) -> dict[str, Any]:
    """Setters merge maps and replace tags. Clear only keys previously owned
    by Kofin, retaining Kodi defaults and local additions. Returns the state
    the readback must match; ``desired`` is updated in place to send."""
    compare = dict(desired)
    if "tag" in compare:
        # The library tag is Kofin's on any row, owned or not, and no
        # desired state carries it, so it comes off.
        old_tags = set(owned_before.get("tag", [])) | {
            tag
            for tag in row.get("tag", [])
            if tag.startswith(metadata.LIBRARY_TAG_PREFIX)
        }
        # A row tag that is one of these to Kodi is Kofin's, in Kodi's
        # spelling, not a tag of the viewer's to keep beside it.
        ours = {tag_key(tag) for tag in old_tags} | {
            tag_key(tag) for tag in compare["tag"]
        }
        viewers = {tag for tag in row.get("tag", []) if tag_key(tag) not in ours}
        compare["tag"] = sorted(set(compare["tag"]) | viewers)
        desired["tag"] = compare["tag"]
    for field in ("art", "ratings", "uniqueid"):
        if field not in compare:
            continue
        owned = set(owned_before.get(field, []))
        if field == "art":
            # Dotted keys are Kodi's own (metadata.own_art): never sent,
            # compared or cleared, even where an older acknowledgement owned
            # one.
            owned = {key for key in owned if "." not in key}
        merged = dict(compare[field])
        merged.update({key: None for key in owned if key not in merged})
        merged.update(
            {
                key: value
                for key, value in (row.get(field) or {}).items()
                if key not in merged and key not in owned and key != "icon"
            }
        )
        if field == "art":
            merged = {
                key: (
                    unquote(value[8:].rstrip("/"))
                    if isinstance(value, str) and value.startswith("image://")
                    else value
                )
                for key, value in merged.items()
                if "." not in key
            }
        desired[field] = merged
        compare[field] = merged
    if kind == "Season":
        if not desired.get("title"):
            if "title" in owned_before:
                desired["title"] = ""
            else:
                desired.pop("title", None)
            compare.pop("title", None)
        compare.pop("uniqueid", None)
        desired.pop("uniqueid", None)
    return compare


def matches(row: dict[str, Any], desired: dict[str, Any]) -> bool:
    for key, value in desired.items():
        actual = row.get(key)
        if key == "resume":
            if abs((actual or {}).get("position", 0) - value["position"]) >= 1:
                return False
        elif key in ("ratings", "uniqueid", "art"):
            actual = actual or {}
            for name, wanted in value.items():
                got = actual.get(name)
                if key == "art" and isinstance(got, str) and got.startswith("image://"):
                    got = unquote(got[8:].rstrip("/"))
                if key == "ratings" and wanted:
                    if (
                        not got
                        or abs(got["rating"] - wanted["rating"]) >= 0.01
                        or got.get("votes", 0) != wanted["votes"]
                    ):
                        return False
                elif (got or None) != (wanted or None):
                    return False
        elif key == "rating":
            if abs(float(actual or 0) - float(value or 0)) >= 0.01:
                return False
        elif key == "lastplayed":
            if not metadata.same_play(actual or "", value or ""):
                return False
        elif key == "tag":
            if {tag_key(tag) for tag in actual or []} != {
                tag_key(tag) for tag in value
            }:
                return False
        elif isinstance(value, list):
            if sorted(actual or []) != sorted(value):
                return False
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if (actual or 0) != value:
                return False
        elif (actual or "") != (value or ""):
            return False
    return True
