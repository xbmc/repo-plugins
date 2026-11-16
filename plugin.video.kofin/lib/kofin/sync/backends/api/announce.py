"""New content: the toasts, and the downloads that follow it.

An item is new when a catch-up publishes it and the catalogue places no item
of its id, and it is announced when the pass has filed it, which is when its
catalogue row is applied. A complete enumeration (a first listing, Update
libraries, the schedule) and a repair announce nothing, and a played item is
never announced (newcontent.entry_for).
"""

from typing import TYPE_CHECKING, Any, Optional
from collections.abc import Collection, Iterable

import xbmc

from kofin.core import settings, toast
from kofin.core.log import Logger
from kofin.downloads import auto as downloads_auto
from kofin.sync import newcontent

if TYPE_CHECKING:
    from kofin.core.api import Api

    from .store import Store

LOG = Logger(__name__)

# How many filed items wait for a toast at most, the oldest dropped first,
# and how long a toast stays up. Nothing caps what is not filed yet: an item
# dropped there would never reach the downloads.
LIMIT = 500
TOAST_MS = 5000


class Arrivals:
    """Items new to the catalogue, held until the pass has filed them, and
    then until a toast may be raised for them."""

    def __init__(self) -> None:
        # Published, not filed yet: item id -> entry, oldest first.
        self.arriving: dict[str, newcontent.Entry] = {}
        # Filed, not announced yet.
        self.backlog: list[newcontent.Entry] = []
        # New songs, not filed or not claimed yet: item id -> library. Never
        # announced (an album says it arrived) but claimed for a subscribed
        # music library. Not capped: a song dropped here is in the catalogue
        # and never offered again.
        self.songs: dict[str, str] = {}

    def published(
        self,
        items: Iterable[dict[str, Any]],
        known: Collection[str],
        membership: Optional[dict[str, str]] = None,
    ) -> None:
        """Note what a catch-up publishes that ``known``, the ids the
        catalogue placed before the publish, did not hold."""
        for item in items:
            if item.get("Id") in known:
                continue
            entry = newcontent.entry_for(item)
            if entry is None:
                continue
            if entry.type in newcontent.ANNOUNCED:
                self.arriving[entry.item_id] = entry
            elif entry.type == "Audio" and (membership or {}).get(entry.item_id):
                self.songs[entry.item_id] = (membership or {})[entry.item_id]

    def flush(self, store: "Store", api: "Api", player: Optional[xbmc.Player]) -> None:
        """Hand what the pass has filed to the downloads, and announce it
        unless a video is playing."""
        self._claim_songs(store)
        landed = self._landed(store)
        if landed:
            # Before the toast's hold: the hold paces announcements, and
            # pacing must not delay or lose a download.
            try:
                downloads_auto.queue_new_content(api, landed)
            except Exception:
                LOG.exception("auto-download hook failed")
            self.backlog.extend(landed)
            del self.backlog[:-LIMIT]
        self._announce(player)

    def _landed(self, store: "Store") -> list[newcontent.Entry]:
        if not self.arriving:
            return []
        states = store.states(list(self.arriving))
        landed = []
        for item_id in list(self.arriving):
            state = states.get(item_id)
            if state is None or state.operation != "upsert":
                # Gone again before the pass filed it: nothing arrived.
                del self.arriving[item_id]
            elif state.status == "applied":
                landed.append(self.arriving.pop(item_id))
        return landed

    def _claim_songs(self, store: "Store") -> None:
        if not self.songs:
            return
        states = store.states(list(self.songs))
        filed: dict[str, str] = {}
        for item_id in list(self.songs):
            state = states.get(item_id)
            if state is None or state.operation != "upsert":
                del self.songs[item_id]
            elif state.status == "applied":
                filed[item_id] = self.songs.pop(item_id)
        if not filed:
            return
        from kofin.downloads import subscriptions

        try:
            subscriptions.claim_library_songs(filed)
        except Exception:
            # Asked again on the next flush: the catalogue holds these now,
            # and no later catch-up would offer them again.
            LOG.exception("music-library subscription claim failed")
            self.songs.update(filed)

    def _announce(self, player: Optional[xbmc.Player]) -> None:
        if not self.backlog:
            return
        if not settings.get_bool("notifyNewContent"):
            # Read here, so turning it off silences what is already held.
            self.backlog = []
            return
        if (
            player is not None
            and player.isPlayingVideo()
            and not xbmc.getCondVisibility("VideoPlayer.Content(livetv)")
        ):
            # Held, not dropped: the news keeps until the video ends.
            return
        pending, self.backlog = self.backlog, []
        try:
            messages = newcontent.summarize(pending)
        except Exception:
            LOG.exception("could not summarize %s new item(s)", len(pending))
            return
        if not messages:
            return
        LOG.debug("--[ new content ] %s", " | ".join(messages))
        for message in messages:
            toast.show(message, time_ms=TOAST_MS)
