"""Scoped readback of owned rows: one library's movies, one show's episodes,
one library's songs.

A video row is owned only when its namespaced unique id and its exact
resolver URL both say so. A song has no unique id -- Kodi keeps none for
music -- so its ownership is its URL alone: the directory it is filed under
is ours and the file name names the item. Readings are cached for the pass
that made them and dropped whenever a scan or a removal could have changed
them.

A music directory is read on its own, one filtered listing, until a pass
asks for the whole library (``folders``, ``songs_in`` from
``WHOLE_LIBRARY_FOLDERS`` directories on); then every song is read in one
listing (paged, 5,000 to a page), split by directory here, and every
directory is answered from it. A library's movies, albums and artists are
read a row at a time while the pass looks up fewer than
``WHOLE_LIBRARY_ROWS`` of them (``look_up``): a movie by its folder, an
album by its id and an artist by its name.
"""

import time
from typing import Any, Optional, Union
from collections.abc import Iterable

from kofin.core import kodirpc
from kofin.core.log import Logger
from . import paths
from .kinds import KINDS, Kind, properties, rpc

LOG = Logger(__name__)

PAGE = 5000

# Kinds filed in a folder of their own (paths.item_dir): one item's rows are
# read by its folder, without listing its library. An episode shares its
# show's folder and a music video its library's.
OWN_FOLDER = ("Movie", "Series")
# The episodes another source filed: every URL of ours is the add-on's.
FOREIGN_EPISODES = {
    "field": "path",
    "operator": "doesnotcontain",
    "value": "plugin://plugin.video.kofin/",
}


def artist_key(name: Optional[str]) -> str:
    return (name or "").strip(" \t\n\r\v\f").casefold()


class Readback:
    def __init__(self, key: str):
        self.key = key
        # The features of this Kodi (capabilities.features), set by the pass
        # that reads them: a property Kodi does not name is never asked for.
        self.features: frozenset[str] = frozenset()
        self._scopes: dict[tuple[Any, ...], dict[Any, dict[str, Any]]] = {}
        # library -> directory key -> item id -> row, for a library read
        # whole; (library, directory key) -> item id -> row, for a directory
        # read alone.
        self._folders: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
        self._directories: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
        # scope key -> Kodi id -> full row, for scopes mostly being compared
        self._full: dict[tuple[Any, ...], dict[Any, dict[str, Any]]] = {}
        # scope key -> item id -> the rows Kodi holds for the item's version
        # files beside the one that owns the identity
        self._versions: dict[tuple[Any, ...], dict[str, list[dict[str, Any]]]] = {}
        # (kind, library, item id) -> the row a show or a movie missing from
        # its listing was found by, or None (show, movie).
        self._adopted: dict[tuple[str, str, str], Optional[dict[str, Any]]] = {}
        # The (kind, library) scopes the pass looks up few rows of
        # (look_up), and the rows read one at a time for them: (library,
        # item id) -> (movie row or None, its version rows); (library,
        # albumid) -> album row; (library, artist key) -> artist row.
        self._few: set[tuple[str, str]] = set()
        self._movies: dict[
            tuple[str, str], tuple[Optional[dict[str, Any]], list[dict[str, Any]]]
        ] = {}
        self._albums: dict[tuple[str, int], Optional[dict[str, Any]]] = {}
        self._artists: dict[tuple[str, str], Optional[dict[str, Any]]] = {}

    def clear(self) -> None:
        """Drop every reading; what the pass looks up (look_up) stays."""
        self._scopes.clear()
        self._folders.clear()
        self._directories.clear()
        self._full.clear()
        self._versions.clear()
        self._adopted.clear()
        self._movies.clear()
        self._albums.clear()
        self._artists.clear()

    # A pass that looks up fewer rows of a library's movies, albums or
    # artists than this reads each alone; from this many on, the library in
    # one listing. One row costs Kodi a filtered listing or a details call,
    # the library a listing of every row with its art.
    WHOLE_LIBRARY_ROWS = 32
    BY_ROW = ("Movie", "MusicAlbum", "MusicArtist")

    def look_up(self, counts: dict[tuple[str, str], int]) -> None:
        """How many rows of each (kind, library) the pass is about to look
        up. A movie, album or artist scope with few is read a row at a time
        until something reads it whole; any other, and one not named, is
        read whole."""
        self._few = {
            (kind, library)
            for (kind, library), count in counts.items()
            if kind in self.BY_ROW and count < self.WHOLE_LIBRARY_ROWS
        }

    def by_row(self, kind: str, library: str) -> bool:
        """Whether the pass reads the scope's rows one at a time."""
        return (kind, library) in self._few and (kind, library, "") not in self._scopes

    @staticmethod
    def complete(reply: Any, key: str) -> list[dict[str, Any]]:
        if not isinstance(reply, dict) or "limits" not in reply:
            raise RuntimeError("incomplete native readback")
        rows: list[dict[str, Any]] = reply.get(key, [])
        if len(rows) != reply["limits"]["total"]:
            raise RuntimeError("partial native readback")
        return rows

    def _paged(self, table: Kind, params: dict[str, Any]) -> list[dict[str, Any]]:
        """A complete listing in pages; the total must hold across them."""
        began = time.monotonic()
        rows: list[dict[str, Any]] = []
        total: Optional[int] = None
        while True:
            page = dict(params, limits={"start": len(rows), "end": len(rows) + PAGE})
            reply = rpc(table.listing, page)
            if not isinstance(reply, dict) or not isinstance(
                reply.get("limits", {}).get("total"), int
            ):
                raise RuntimeError("incomplete native readback")
            count = reply["limits"]["total"]
            if total is not None and count != total:
                raise RuntimeError("native listing changed during readback")
            total = count
            chunk = reply.get(table.list_key, [])
            rows.extend(chunk)
            if len(rows) >= total:
                break
            if not chunk:
                raise RuntimeError("partial native readback")
        if len(rows) != total:
            raise RuntimeError("partial native readback")
        if total >= PAGE:
            LOG.debug(
                "read back %d %s in %.1f s",
                total,
                table.list_key,
                time.monotonic() - began,
            )
        return rows

    def _path_filter(self, prefix: str) -> dict[str, str]:
        return {"field": "path", "operator": "startswith", "value": prefix}

    # -- ownership -----------------------------------------------------------

    def owns(
        self, kind: str, row: dict[str, Any], library: str, parent_id: str = ""
    ) -> Optional[str]:
        """The item id of an owned row, or None."""
        if kind == "Audio":
            location, item_id = paths.parse_item(row.get("file") or "")
            if (
                location is None
                or location.key != self.key
                or location.library != library
                or location.content != "music"
                or not location.folder
                or not item_id
            ):
                return None
            if parent_id and location.folder != parent_id:
                return None
            return item_id
        if kind in ("MusicAlbum", "MusicArtist"):
            return None
        uid = str((row.get("uniqueid") or {}).get("kofin", ""))
        if not uid.startswith(self.key + ":"):
            return None
        item_id = uid[len(self.key) + 1 :]
        if kind == "Series":
            expected = paths.show_dir(self.key, library, item_id).rstrip("/")
            if (row.get("file") or "").rstrip("/") != expected:
                return None
        elif kind == "Movie":
            # A movie's version files carry its URL with the source named,
            # and Kodi lists the movie by the one the user made the default.
            if paths.without_source(row.get("file") or "") != paths.playback_url(
                self.key, kind, library, item_id
            ):
                return None
        elif row.get("file") != paths.playback_url(
            self.key, kind, library, item_id, parent_id
        ):
            return None
        return item_id

    @staticmethod
    def _prefer(
        kept: dict[str, Any], row: dict[str, Any], id_param: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Two movie rows of one identity: Kodi imported a version file as a
        movie of its own, which waits for the user to group it. The movie's
        own file owns the identity; between two version files the older row
        does. Two rows by the movie's own file are a duplicate of ours.
        Returns the row that owns the identity and the other one."""
        kept_version = paths.is_version_url(kept.get("file"))
        row_version = paths.is_version_url(row.get("file"))
        if not kept_version and not row_version:
            raise RuntimeError("duplicate owned Movie identity")
        if kept_version and (not row_version or row[id_param] < kept[id_param]):
            kept, row = row, kept
        return kept, row

    def version_rows(self, library: str, item_id: str) -> list[dict[str, Any]]:
        """The movie rows Kodi holds for an item's version files beside the
        row that owns its identity: ungrouped versions."""
        if self.by_row("Movie", library):
            return list(self._movie_folder(library, item_id)[1])
        return self.versions_in(library).get(item_id, [])

    def versions_in(self, library: str) -> dict[str, list[dict[str, Any]]]:
        """Every item of a library with ungrouped version rows."""
        self.scope("Movie", library)
        return {
            item_id: list(rows)
            for item_id, rows in self._versions.get(("Movie", library, ""), {}).items()
        }

    # -- scopes --------------------------------------------------------------

    def scope(
        self,
        kind: str,
        library: str = "",
        parent_id: str = "",
        tvshowid: Optional[int] = None,
    ) -> dict[Any, dict[str, Any]]:
        """Owned rows of one scanner scope, cached for the pass.

        Seasons key by number and sets by title: neither carries an id of
        ours, and both exist only through the rows that reference them.
        Albums key by Kodi's album id, found through the songs' ``albumid``;
        artists by name, which is all Kodi matches them by.
        """
        if kind == "Audio":
            if not parent_id:
                return self._songs(library)
            if library in self._folders:
                return self._folders[library].get(parent_id, {})
            key = (library, parent_id)
            if key not in self._directories:
                self._directories[key] = self.directory(library, parent_id)
            return self._directories[key]
        cache_key = (kind, library, parent_id)
        if cache_key in self._scopes:
            return self._scopes[cache_key]
        table = KINDS[kind]
        params: dict[str, Any] = {
            "properties": properties(kind, self.features, minimal=True)
        }
        if kind in ("Movie", "MusicVideo"):
            params["filter"] = self._path_filter(
                paths.library_dir(self.key, library, paths.CONTENT[kind])
            )
        elif kind == "Series":
            params["filter"] = self._path_filter(
                paths.library_dir(self.key, library, "tvshows")
            )
        elif kind in ("Episode", "Season"):
            if tvshowid is None:
                show = self.show(library, parent_id)
                if not show:
                    self._scopes[cache_key] = {}
                    return {}
                tvshowid = show["tvshowid"]
            params["tvshowid"] = tvshowid
        elif kind in ("MusicAlbum", "MusicArtist"):
            params["filter"] = self._path_filter(
                paths.library_dir(self.key, library, "music")
            )
            if kind == "MusicArtist":
                params["albumartistsonly"] = False
            rows = self._paged(table, params)
            result: dict[Any, Any] = {}
            for row in rows:
                if kind == "MusicAlbum":
                    result[row[table.id_param]] = row
                    continue
                name = artist_key(row.get("artist") or row.get("label"))
                # Two artists of one name: neither can be told apart by
                # anything the API lists, so neither is claimed.
                result[name] = None if name in result else row
            self._scopes[cache_key] = result
            return result
        rows = self._paged(table, params)
        result = {}
        self._versions.pop(cache_key, None)
        for row in rows:
            if kind == "Season":
                result[int(row.get("season", -1))] = row
                continue
            if kind == "BoxSet":
                result[row.get("title", "")] = row
                continue
            item_id = self.owns(kind, row, library, parent_id)
            if item_id is None:
                continue
            if item_id in result:
                if kind == "Movie":
                    result[item_id], other = self._prefer(
                        result[item_id], row, table.id_param
                    )
                    self._versions.setdefault(cache_key, {}).setdefault(
                        item_id, []
                    ).append(other)
                    continue
                raise RuntimeError("duplicate owned %s identity" % kind)
            result[item_id] = row
        self._scopes[cache_key] = result
        return result

    def _songs(self, library: str) -> dict[Any, dict[str, Any]]:
        cache_key = ("Audio", library, "")
        if cache_key in self._scopes:
            return self._scopes[cache_key]
        table = KINDS["Audio"]
        rows = self._paged(
            table,
            {
                "properties": properties("Audio", self.features),
                "filter": self._path_filter(
                    paths.library_dir(self.key, library, "music")
                ),
                "sort": {"method": "file", "order": "ascending"},
            },
        )
        result: dict[str, dict[str, Any]] = {}
        folders: dict[str, dict[str, dict[str, Any]]] = {}
        for row in rows:
            location, item_id = paths.parse_item(row.get("file") or "")
            if (
                location is None
                or location.key != self.key
                or location.library != library
                or not location.folder
                or not item_id
            ):
                continue
            # A song moved between albums has a row in each directory until
            # the old one is rescanned; the directory view keeps both, the
            # flat view is for presence only.
            result[item_id] = row
            folders.setdefault(location.folder, {})[item_id] = row
        self._scopes[cache_key] = result
        self._folders[library] = folders
        return result

    def folders(self, library: str) -> dict[str, dict[str, dict[str, Any]]]:
        """Every directory of the library's songs Kodi holds, with its rows."""
        self._songs(library)
        return self._folders[library]

    # A directory alone costs Kodi one filtered listing, the library a
    # listing of every song and a parse of each one's URL; from this many
    # directories on, the library is read whole.
    WHOLE_LIBRARY_FOLDERS = 32

    def songs_in(self, library: str, folders: Iterable[str]) -> None:
        """Read the songs of ``folders`` for the pass: the whole library in
        one listing when they are many, each directory alone otherwise, when
        ``scope`` first asks for it."""
        if len(set(folders)) >= self.WHOLE_LIBRARY_FOLDERS:
            self._songs(library)

    def directory(self, library: str, folder: str) -> dict[str, dict[str, Any]]:
        """One music directory's owned rows, read now and not cached: the
        confirmation after a scan, and the one lookup a playback needs."""
        rows = self._paged(
            KINDS["Audio"],
            {
                "properties": properties("Audio", self.features),
                "filter": self._path_filter(paths.music_dir(self.key, library, folder)),
            },
        )
        result = {}
        for row in rows:
            item_id = self.owns("Audio", row, library, folder)
            if item_id is not None:
                result[item_id] = row
        return result

    def item(
        self, kind: str, library: str, item_id: str
    ) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]]]:
        """One movie's or one show's owned row, read now and not cached, with
        the movie's version rows Kodi filed apart: the confirmation after a
        refresh. Read by its folder, not the library: a refresh is polled
        until Kodi has filed the row again."""
        if kind not in OWN_FOLDER:
            raise ValueError("%s has no folder of its own" % kind)
        table = KINDS[kind]
        rows = self._paged(
            table,
            {
                "properties": properties(kind, self.features, minimal=True),
                "filter": self._path_filter(
                    paths.item_dir(self.key, kind, library, item_id)
                ),
            },
        )
        found: Optional[dict[str, Any]] = None
        versions: list[dict[str, Any]] = []
        for row in rows:
            if self.owns(kind, row, library) != item_id:
                continue
            if found is None:
                found = row
            elif kind == "Movie":
                found, other = self._prefer(found, row, table.id_param)
                versions.append(other)
            else:
                raise RuntimeError("duplicate owned %s identity" % kind)
        return found, versions

    def forget_music(self, library: str) -> None:
        """Drop every music scope of a library: a scan or a patch changed it."""
        for kind in ("Audio", "MusicAlbum", "MusicArtist"):
            self.forget(kind, library)

    def forget(self, kind: str, library: str = "", parent_id: str = "") -> None:
        if kind == "Audio":
            self._scopes.pop(("Audio", library, ""), None)
            self._folders.pop(library, None)
            for key in [k for k in self._directories if k[0] == library]:
                self._directories.pop(key, None)
            return
        if kind == "Movie":
            for movie in [k for k in self._movies if k[0] == library]:
                self._movies.pop(movie, None)
        elif kind == "MusicAlbum":
            for album in [k for k in self._albums if k[0] == library]:
                self._albums.pop(album, None)
        elif kind == "MusicArtist":
            for artist in [k for k in self._artists if k[0] == library]:
                self._artists.pop(artist, None)
        self._scopes.pop((kind, library, parent_id), None)
        self._full.pop((kind, library, parent_id), None)
        self._versions.pop((kind, library, parent_id), None)
        for adopted in [k for k in self._adopted if k[0] == kind]:
            self._adopted.pop(adopted, None)
        if kind == "Series":
            # A show's episodes and seasons are read through its row.
            for key in [k for k in self._scopes if k[0] in ("Episode", "Season")]:
                self._scopes.pop(key, None)
            for key in [k for k in self._full if k[0] in ("Episode", "Season")]:
                self._full.pop(key, None)

    # -- the full row, for an item whose desired state moved ------------------

    FULL_SHARE = 0.1
    FULL_FLOOR = 25
    # Below the floor, a scope is still read in one listing when most of it
    # is wanted: a first import compares every row, and a show of a dozen
    # episodes read a row at a time is a dozen calls where one answers.
    SMALL_SHARE = 0.5

    def _scope_params(
        self, kind: str, library: str, parent_id: str
    ) -> Optional[tuple[Kind, dict[str, Any]]]:
        table = KINDS[kind]
        params: dict[str, Any] = {"properties": properties(kind, self.features)}
        if kind in ("Movie", "MusicVideo"):
            params["filter"] = self._path_filter(
                paths.library_dir(self.key, library, paths.CONTENT[kind])
            )
        elif kind == "Series":
            params["filter"] = self._path_filter(
                paths.library_dir(self.key, library, "tvshows")
            )
        elif kind in ("Episode", "Season"):
            show = self.show(library, parent_id)
            if not show:
                return None
            params["tvshowid"] = show["tvshowid"]
        return table, params

    def prefetch_full(
        self, kind: str, library: str, parent_id: str, count: int
    ) -> None:
        """Read a scope's full rows in one listing when most of it is about
        to be compared (a first import acknowledges every row); otherwise a
        row is read by id when its turn comes."""
        key = (kind, library, parent_id)
        if key in self._full or kind in ("Audio", "MusicAlbum", "MusicArtist"):
            return
        if self.by_row(kind, library):
            return
        known = len(self.scope(kind, library, parent_id))
        if count < 2 or count < known * self.FULL_SHARE:
            return
        if count < self.FULL_FLOOR and count < known * self.SMALL_SHARE:
            return
        found = self._scope_params(kind, library, parent_id)
        if found is None:
            return
        table, params = found
        self._full[key] = {
            row[table.id_param]: row
            for row in self._paged(table, params)
            if table.id_param in row
        }

    def full(
        self, kind: str, library: str, parent_id: str, row: dict[str, Any]
    ) -> dict[str, Any]:
        """The full row behind a scope row: from the prefetched listing when
        there is one, else by id."""
        table = KINDS[kind]
        kodi_id = row[table.id_param]
        cached = self._full.get((kind, library, parent_id), {}).get(kodi_id)
        if cached is not None:
            return cached
        reply = rpc(
            table.getter,
            {table.id_param: kodi_id, "properties": properties(kind, self.features)},
        )
        detail = reply.get(table.result_key) if isinstance(reply, dict) else None
        if not isinstance(detail, dict) or not detail:
            raise RuntimeError("%s row vanished during the pass" % kind)
        return detail

    def remember(
        self,
        kind: str,
        library: str,
        parent_id: str,
        cache_key: Union[str, int],
        row: dict[str, Any],
    ) -> None:
        """Put a freshly confirmed row into an existing cached scope."""
        if kind == "Audio":
            # A song is keyed by its item id; a season by its number.
            item_id = str(cache_key)
            if ("Audio", library, "") in self._scopes:
                self._scopes[("Audio", library, "")][item_id] = row
                self._folders[library].setdefault(parent_id, {})[item_id] = row
            elif (library, parent_id) in self._directories:
                self._directories[(library, parent_id)][item_id] = row
            return
        scope_key = (kind, library, parent_id)
        if scope_key in self._scopes:
            self._scopes[scope_key][cache_key] = row
        if kind == "Movie" and (library, str(cache_key)) in self._movies:
            versions = self._movies[(library, str(cache_key))][1]
            self._movies[(library, str(cache_key))] = (row, versions)

    def refreshed(
        self,
        kind: str,
        library: str,
        parent_id: str,
        item_id: str,
        old_id: int,
        row: dict[str, Any],
        versions: Optional[Iterable[dict[str, Any]]],
    ) -> None:
        """Put a refreshed row (``item``) into the cached scope in place of
        the one it replaced. Kodi files it under a new id, or under the old
        one again when that was the table's highest, so the full row read
        before the refresh is dropped by both. A show's seasons and episodes
        are read through its id and are read again."""
        scope_key = (kind, library, parent_id)
        full = self._full.get(scope_key, {})
        full.pop(old_id, None)
        full.pop(row[KINDS[kind].id_param], None)
        if scope_key in self._scopes:
            self._scopes[scope_key][item_id] = row
            if versions:
                self._versions.setdefault(scope_key, {})[item_id] = list(versions)
            else:
                self._versions.get(scope_key, {}).pop(item_id, None)
        if kind == "Movie" and (library, item_id) in self._movies:
            self._movies[(library, item_id)] = (row, list(versions or ()))
        if kind == "Series":
            for child in ("Episode", "Season"):
                self._scopes.pop((child, library, item_id), None)
                self._full.pop((child, library, item_id), None)

    def details(self, kind: str, kodi_id: int) -> dict[str, Any]:
        table = KINDS[kind]
        reply: dict[str, Any] = rpc(
            table.getter,
            {table.id_param: kodi_id, "properties": properties(kind, self.features)},
        )
        row: dict[str, Any] = reply.get(table.result_key, {})
        return row

    def lookup(self, kind: str, kodi_id: int) -> Optional[dict[str, Any]]:
        """The row under ``kodi_id``, or None when Kodi refuses the id, as it
        does an id it holds no row under. Raises when Kodi could not be
        asked: that answer says nothing about the row."""
        table = KINDS[kind]
        reply = kodirpc.call(
            table.getter,
            {table.id_param: kodi_id, "properties": properties(kind, self.features)},
        )
        if reply is kodirpc.FAILED:
            raise RuntimeError("Kodi could not be asked for %s %d" % (kind, kodi_id))
        if not isinstance(reply, dict):
            return None
        return reply.get(table.result_key) or None

    def movie_folder(self, library: str, item_id: str) -> list[dict[str, Any]]:
        """Every movie row filed under one movie's folder, in one listing:
        its own and any version file Kodi filed as a movie of its own. A
        path filter is answered from the database, without the add-on."""
        return self._paged(
            KINDS["Movie"],
            {
                "properties": properties("Movie", self.features, minimal=True),
                "filter": self._path_filter(
                    paths.movie_dir(self.key, library, item_id)
                ),
            },
        )

    def owned(
        self, kind: str, kodi_id: int, item_id: str, library: str, parent_id: str = ""
    ) -> dict[str, Any]:
        row = self.details(kind, kodi_id)
        if not self.holds(kind, row, library, item_id, parent_id):
            raise RuntimeError("%s ownership changed" % kind)
        return row

    def holds(
        self,
        kind: str,
        row: dict[str, Any],
        library: str,
        item_id: str,
        parent_id: str = "",
    ) -> bool:
        """Whether ``row`` is the item's: by its ids at its folder, or the row
        this pass found a show or a movie by (show, movie)."""
        if self.owns(kind, row, library, parent_id) == item_id:
            return True
        adopted = self._adopted.get((kind, library, item_id))
        id_param = KINDS[kind].id_param
        return adopted is not None and adopted.get(id_param) == row.get(id_param)

    # -- a show another source shares ----------------------------------------

    def show(self, library: str, series_id: str) -> Optional[dict[str, Any]]:
        """Our row for a show, by its ids at its folder or through its episodes.

        Kodi files a show from any source into the row it already holds for
        that show, matched by its main unique id, and rewrites the row from
        the source scanned last: scanned after ours, another source's show
        takes our ids off the row; scanned before, it keeps the row listed
        under its own folder, where the library's listing does not reach.
        Our episodes are filed under their own URLs and keep their ids, so
        the row they belong to is the show's (``stripped``, ``own_folder``).
        """
        found: Optional[dict[str, Any]] = self.scope("Series", library).get(series_id)
        if found is not None:
            return found
        key = ("Series", library, series_id)
        if key not in self._adopted:
            self._adopted[key] = self._adopt(library, series_id)
        return self._adopted[key]

    def movie(self, library: str, item_id: str) -> Optional[dict[str, Any]]:
        """Our row for a movie, by its ids and its file or by its file alone.

        Kodi groups a scanned movie with any movie sharing a unique id
        (GetSameVideoItems, "grouping of similar videos") and makes the newer
        file the movie's default version: another source's copy of a movie of
        ours turns our row into one listed under their file, where the
        library's listing does not reach. Kodi still finds the movie by our
        file, a version of it (GetMovieId), so the row is the one our URL
        names (``own_file``)."""
        found = self.listed_movie(library, item_id)
        if found is not None:
            return found
        key = ("Movie", library, item_id)
        if key not in self._adopted:
            self._adopted[key] = self._adopt_movie(library, item_id)
        return self._adopted[key]

    def listed_movie(self, library: str, item_id: str) -> Optional[dict[str, Any]]:
        """Our row for a movie as the library's listing has it: from the
        listing, or from the movie's folder while the pass reads the
        library's movies a row at a time (``by_row``)."""
        if self.by_row("Movie", library):
            return self._movie_folder(library, item_id)[0]
        found: Optional[dict[str, Any]] = self.scope("Movie", library).get(item_id)
        return found

    def _movie_folder(
        self, library: str, item_id: str
    ) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]]]:
        key = (library, item_id)
        if key not in self._movies:
            self._movies[key] = self.item("Movie", library, item_id)
        return self._movies[key]

    def album(self, library: str, albumid: int) -> Optional[dict[str, Any]]:
        """The album row Kodi filed our songs under, by its id: from the
        library's album listing, or alone while the pass reads the library's
        albums a row at a time (``by_row``). The id comes from songs of ours
        on the row, so the listing, filtered on our folder, holds it too."""
        if not self.by_row("MusicAlbum", library):
            return self.scope("MusicAlbum", library).get(albumid)
        key = (library, albumid)
        if key not in self._albums:
            table = KINDS["MusicAlbum"]
            try:
                reply = rpc(
                    table.getter,
                    {
                        table.id_param: albumid,
                        "properties": properties(
                            "MusicAlbum", self.features, minimal=True
                        ),
                    },
                )
            except RuntimeError:
                # Refused: no album of that id any more.
                reply = None
            row = reply.get(table.result_key) if isinstance(reply, dict) else None
            self._albums[key] = row if isinstance(row, dict) and row else None
        return self._albums[key]

    def artist(self, library: str, name: Optional[str]) -> Optional[dict[str, Any]]:
        """The artist row of a name: from the library's artist listing, or
        alone while the pass reads the library's artists a row at a time
        (``by_row``). Kodi's "is" is SQL LIKE, which folds ASCII case only,
        so a name outside ASCII, or one the filter does not find, is read
        from the listing, where names are compared casefolded."""
        key = artist_key(name)
        if not self.by_row("MusicArtist", library) or not key.isascii():
            return self.scope("MusicArtist", library).get(key)
        if (library, key) not in self._artists:
            rows = self._paged(
                KINDS["MusicArtist"],
                {
                    "properties": properties(
                        "MusicArtist", self.features, minimal=True
                    ),
                    "albumartistsonly": False,
                    "filter": {
                        "and": [
                            self._path_filter(
                                paths.library_dir(self.key, library, "music")
                            ),
                            {
                                "field": "artist",
                                "operator": "is",
                                "value": (name or "").strip(" \t\n\r\v\f"),
                            },
                        ]
                    },
                },
            )
            named = [
                row
                for row in rows
                if artist_key(row.get("artist") or row.get("label")) == key
            ]
            if not named:
                return self.scope("MusicArtist", library).get(key)
            # Two artists of one name: as in the listing, neither is claimed.
            self._artists[(library, key)] = named[0] if len(named) == 1 else None
        return self._artists[(library, key)]

    def album_folders(self, albumid: int) -> set[tuple[str, str]]:
        """The (library, directory) pairs of every song of ours Kodi files
        under an album row."""
        rows = self._paged(
            KINDS["Audio"], {"properties": ["file"], "filter": {"albumid": albumid}}
        )
        found: set[tuple[str, str]] = set()
        for row in rows:
            location, item_id = paths.parse_item(row.get("file") or "")
            if (
                location is not None
                and location.key == self.key
                and location.library
                and location.folder
                and item_id
            ):
                found.add((location.library, location.folder))
        return found

    def _adopt_movie(self, library: str, item_id: str) -> Optional[dict[str, Any]]:
        try:
            # Kodi lists the file's folder to answer: one listing of the
            # movie's folder, asked only for a movie missing from the scope.
            reply = rpc(
                "Files.GetFileDetails",
                {
                    "file": paths.playback_url(self.key, "Movie", library, item_id),
                    "media": "video",
                    "properties": ["file"],
                },
            )
        except RuntimeError:
            # Refused: a file Kodi holds no row for.
            return None
        details = (reply or {}).get("filedetails") or {}
        movieid = details.get("id")
        if (
            details.get("type") != "movie"
            or not isinstance(movieid, int)
            or movieid < 0
        ):
            return None
        row: dict[str, Any] = self.details("Movie", movieid)
        LOG.debug(
            "movie %s is Kodi's movie %d, listed under %s",
            item_id,
            movieid,
            row.get("file"),
        )
        return row

    def own_file(self, library: str, item_id: str, row: dict[str, Any]) -> bool:
        """Whether Kodi lists the movie's row under our file, where a refresh
        reads our listing; under another source's it reads theirs."""
        return bool(
            paths.without_source(str(row.get("file") or ""))
            == paths.playback_url(self.key, "Movie", library, item_id)
        )

    def _adopt(self, library: str, series_id: str) -> Optional[dict[str, Any]]:
        reply = rpc(
            "VideoLibrary.GetEpisodes",
            {
                "properties": ["file", "uniqueid", "tvshowid"],
                "filter": self._path_filter(
                    paths.show_dir(self.key, library, series_id)
                ),
                "limits": {"start": 0, "end": 1},
            },
        )
        episodes = (reply or {}).get("episodes") or []
        if (
            not episodes
            or self.owns("Episode", episodes[0], library, series_id) is None
        ):
            return None
        tvshowid = episodes[0].get("tvshowid")
        if not isinstance(tvshowid, int) or tvshowid < 0:
            return None
        row: dict[str, Any] = self.details("Series", tvshowid)
        LOG.debug(
            "show %s is Kodi's show %d, filed under %s with %s",
            series_id,
            tvshowid,
            row.get("file"),
            ", ".join(sorted(row.get("uniqueid") or {})) or "no unique id",
        )
        return row

    def stripped(self, library: str, series_id: str) -> bool:
        """Whether the show's row, found through its episodes, carries none
        of our ids: another source's scan rewrote it."""
        row = self._adopted.get(("Series", library, series_id))
        if row is None:
            return False
        uid = str((row.get("uniqueid") or {}).get("kofin", ""))
        return not uid.startswith(self.key + ":")

    def row_owner(self, row: dict[str, Any]) -> Optional[str]:
        """The series id our id on a show's row names, or None."""
        uid = str((row.get("uniqueid") or {}).get("kofin", ""))
        if not uid.startswith(self.key + ":"):
            return None
        return uid[len(self.key) + 1 :]

    def foreign_episodes(self, tvshowid: int) -> list[dict[str, Any]]:
        """The episodes Kofin did not file on one show's row."""
        params: dict[str, Any] = {"tvshowid": tvshowid, "filter": FOREIGN_EPISODES}
        reply = rpc(
            "VideoLibrary.GetEpisodes", dict(params, limits={"start": 0, "end": 1})
        )
        if not ((reply or {}).get("limits") or {}).get("total"):
            return []
        return self._paged(
            KINDS["Episode"], dict(params, properties=["file", "tvshowid"])
        )

    def own_folder(self, library: str, series_id: str, row: dict[str, Any]) -> bool:
        """Whether Kodi lists the show's row under our folder, where a refresh
        reads our listing; under another source's it reads theirs."""
        expected = paths.show_dir(self.key, library, series_id).rstrip("/")
        return bool(str(row.get("file") or "").rstrip("/") == expected)

    def stripped_shows(self) -> list[tuple[str, str]]:
        """The (library, series id) of every show this pass found stripped."""
        return [
            (library, series_id)
            for kind, library, series_id in self._adopted
            if kind == "Series" and self.stripped(library, series_id)
        ]
