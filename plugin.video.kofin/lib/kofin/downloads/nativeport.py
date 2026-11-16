"""The library side of a download.

A download is a file on disk and a row in kofin's own store, and nothing of
Kodi's moves for it: the row keeps its plugin URL, the resolver plays the
local file for a downloaded item however it is reached (plugin/play.py), and
the badge and the tag reach the row through the catalogue's pass, which
re-plans the item with its download state as an input
(sync/backends/api/downloaded.py). Kodi's own play state is read back
through JSON-RPC by the mapped id, so the retention sweep still works
offline.
"""

import time
from datetime import datetime
from typing import Any, Optional, Protocol
from collections.abc import Iterable

from kofin.core.log import Logger

LOG = Logger(__name__)


class Native(Protocol):
    def attached(self, row: Any, root: str) -> bool: ...

    def detached(self, row: Any) -> None: ...

    def watched_locally(self, row: Any) -> bool: ...

    def last_touch(self, row: Any) -> Optional[tuple[float, bool]]: ...

    def music_view(self, force: bool) -> None: ...

    def refresh_song_playlists(self, item_ids: Iterable[str]) -> None: ...


def for_build() -> Native:
    return NativeApi()


def _as_epoch(stamp: Any) -> float:
    """A Kodi timestamp as unix seconds; 0.0 for unset or unparseable.

    Two spellings reach it and both are local time: Kodi's own
    ``'%Y-%m-%d %H:%M:%S'`` and the ISO ``T`` form. 0.0 rather than an
    exception for anything else: a value kofin did not write is not a reason
    to abandon a sweep.
    """
    if not stamp:
        return 0.0
    try:
        # time.strptime, for the reason metadata.same_play gives.
        parsed = time.strptime(str(stamp)[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
        return datetime(*parsed[:6]).timestamp()
    except ValueError:
        return 0.0


# Kodi's media type of a download row, for the readback by id.
_MEDIA = {"movie": "movie", "episode": "episode", "song": "song"}
_READ = {
    "movie": ("VideoLibrary.GetMovieDetails", "movieid", "moviedetails"),
    "episode": ("VideoLibrary.GetEpisodeDetails", "episodeid", "episodedetails"),
}


class NativeApi:
    @staticmethod
    def _store() -> Any:
        from kofin.sync.backends.api.identity import current_store

        return current_store()

    def attached(self, row: Any, root: str) -> bool:
        """Always true: the startup reconcile re-plans every done file,
        which is how a finish that died before this call gets its badge."""
        self._replan(row)
        return True

    def detached(self, row: Any) -> None:
        self._replan(row)

    def _replan(self, row: Any) -> None:
        """Have the pass build the row again with its download state: the
        badge on a movie or an episode, the tag on a movie or on the show
        an episode belongs to, and the badge on that show and on the season
        the episode is in. Every season of the show is handed over: which
        of them holds a download is the pass's to say, by the episodes'
        numbers, and a show's seasons are few."""
        items: list[str] = [row.jellyfin_id]
        try:
            store = self._store()
            if row.media_type == "episode" and row.series_id:
                items.append(row.series_id)
                items.extend(
                    store.records(
                        kind="Season",
                        parent_id=row.series_id,
                        pinned=False,
                        payloads=False,
                    )
                )
            store.invalidate(items)
        except Exception:
            LOG.exception(
                "download state of %s not handed to the pass", row.jellyfin_id
            )

    def _row(self, row: Any, properties: list[str]) -> Optional[dict]:
        from kofin.core import kodirpc
        from kofin.sync.backends.api.identity import native_id_for

        read = _READ.get(row.media_type)
        if read is None:
            return None
        kodi_id = native_id_for(row.jellyfin_id, _MEDIA.get(row.media_type, "movie"))
        if kodi_id is None:
            return None
        method, id_param, result_key = read
        reply = kodirpc.call(method, {id_param: kodi_id, "properties": properties})
        if not isinstance(reply, dict):
            return None
        found = reply.get(result_key)
        return found if isinstance(found, dict) else None

    def watched_locally(self, row: Any) -> bool:
        found = self._row(row, ["playcount"])
        return bool(found and found.get("playcount"))

    def last_touch(self, row: Any) -> Optional[tuple[float, bool]]:
        found = self._row(row, ["lastplayed", "resume"])
        if found is None:
            return None
        resume = found.get("resume") or {}
        return _as_epoch(found.get("lastplayed")), bool(resume.get("position"))

    def music_view(self, force: bool) -> None:
        # A download keeps its row's plugin URL, so a smart playlist's rule
        # on the downloads folder would match nothing: the view is a
        # playlist of the finished songs, written whole each time.
        from kofin.sync.backends.api import playlists as api_playlists

        api_playlists.write_downloaded_music(self._store())

    def refresh_song_playlists(self, item_ids: Iterable[str]) -> None:
        # A song's line in a server playlist is its plugin URL, which a
        # download never moves; the Downloaded-music view is the set of
        # finished songs, which did.
        self.music_view(True)
