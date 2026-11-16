"""Kodi-side watched / resume changes pushed back to Jellyfin.

Kodi's own context items — "Mark as watched", "Mark as unwatched", "Reset
resume position" — write straight into MyVideos and announce
``VideoLibrary.OnUpdate`` in one of two shapes::

    play count   {"item": {"id": 5910, "type": "episode"}, "playcount": 1}
    resume reset {"id": 5910, "type": "episode"}

The flat one carries identity and nothing else, and Kodi emits it for a change
of art or title as well as for its resume-bookmark delete
(``UpdateArtForItem``, ``UpdateFanart``, ``UpdateMovieTitle``,
``UpdateVideoSortTitle``). So the position is read back out of Kodi: a row
that still holds one was not reset, and a row that holds none is queued as
reset whatever kofin last filed on it, since Kodi's player writes its bookmark
at a stop before the pass has filed the play.

Kofin's own writes announce too: ``Store.is_echo`` filters them out, and the
user's edits are queued durably in kofin.db for the server.
"""

import queue
import threading
from typing import Any, Optional

from kofin.core import kodirpc
from kofin.core.api import Api
from kofin.core.http import JellyfinError
from kofin.core.log import Logger

LOG = Logger(__name__)

JsonDict = dict[str, Any]

UPDATE_PLAYCOUNT = "playcount"
UPDATE_RESUME = "resume"

# Kodi media types that have both a kofin.db mapping and a Jellyfin user-data
# record. Music is absent: AudioLibrary.OnUpdate is a different announcement
# and Kodi has no watched/resume UI for songs.
WATCHED_MEDIA = ("movie", "episode", "musicvideo")


def parse_update(data: JsonDict) -> Optional[tuple[str, int, str, int]]:
    """``(kind, kodi id, media type, play count)`` for an OnUpdate payload.

    ``kind`` is :data:`UPDATE_PLAYCOUNT` (the nested shape, carrying a new
    play count) or :data:`UPDATE_RESUME` (the flat shape); the play count is 0
    for the latter. None for every announcement kofin does not act on — a
    library add, an unmapped media type, a malformed payload.
    """
    item = data.get("item")
    if isinstance(item, dict):
        kodi_id, media = item.get("id"), item.get("type")
        playcount = data.get("playcount")
        if not isinstance(playcount, int):
            return None  # a library add or metadata refresh, not a watch state
        kind = UPDATE_PLAYCOUNT
    else:
        kodi_id, media = data.get("id"), data.get("type")
        playcount, kind = 0, UPDATE_RESUME
    if not isinstance(kodi_id, int) or media not in WATCHED_MEDIA:
        return None
    return kind, kodi_id, str(media), playcount


class KodiUserData:
    """Applies Kodi-side watched/resume changes to the Jellyfin server.

    Work runs on one worker thread, so the JSON-RPC read and the kofin.db
    write stay off Kodi's notification thread, where the announcements
    arrive; marking a whole season watched fires one announcement per episode.
    """

    def __init__(self, api: Api) -> None:
        self.api = api
        self._queue: queue.Queue[Optional[tuple[str, int, str, int]]] = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def submit(self, data: JsonDict) -> None:
        """Queue an OnUpdate payload; ignores what kofin does not act on."""
        parsed = parse_update(data)
        if parsed is None:
            return
        with self._lock:
            if self._worker is None:
                # Started on the first announcement worth acting on: most
                # sessions never see one, and a parked thread that never wakes
                # still has to be joined on every service restart.
                self._worker = threading.Thread(target=self._run, name="kofin-userdata")
                self._worker.daemon = True
                self._worker.start()
        self._queue.put(parsed)

    def stop(self) -> None:
        with self._lock:
            worker = self._worker
            self._worker = None
        if worker is None:
            return
        self._queue.put(None)
        worker.join(timeout=10)
        if worker.is_alive():  # pragma: no cover - watchdog only
            LOG.warning("kodi userdata worker did not stop within deadline")

    def _run(self) -> None:
        while True:
            job = self._queue.get()
            if job is None:
                return
            try:
                self._apply(*job)
            except JellyfinError as error:
                LOG.debug("userdata push failed (%s); parking it for replay", error)
                self._park(*job)
            except Exception:
                LOG.exception("kodi userdata push failed")

    def _park(self, kind: str, kodi_id: int, media: str, playcount: int) -> None:
        try:
            from kofin.downloads import pending
            from kofin.service.libraryclaim import mapped_jellyfin_id

            jellyfin_id = mapped_jellyfin_id(kodi_id, media)
            if not jellyfin_id:
                return
            if kind == UPDATE_PLAYCOUNT:
                pending.enqueue(jellyfin_id, media, played=playcount > 0)
            else:
                pending.enqueue(jellyfin_id, media, position_ticks=0)
        except Exception:  # pragma: no cover - defensive
            LOG.exception("could not park userdata for replay")

    def _apply(self, kind: str, kodi_id: int, media: str, playcount: int) -> None:
        from kofin.sync.backends.api.identity import current_store, mapped_item

        item_id = mapped_item(kodi_id, media)
        if not item_id:
            return
        store = current_store()
        if kind == UPDATE_PLAYCOUNT:
            if store.is_echo(item_id, "playcount", playcount):
                return
            store.local(item_id, {"playcount": playcount})
        else:
            position = kodirpc.resume_seconds(kodi_id, media)
            if position is None or position:
                return
            if store.is_echo(item_id, "resume", {"position": position}):
                return
            store.local(item_id, {"position": position})
