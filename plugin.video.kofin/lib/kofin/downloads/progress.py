"""The download progress bar, on Kodi's own library-update surface.

``xbmcgui.DialogProgressBG`` is the window Kodi's library scanner reports
through. One aggregate bar for the whole queue, never one per worker: the
window cycles between registered handles, so per-worker bars would flicker.
Progress is counted in items — completed plus the active transfers' byte
fractions, over completed plus the store's remainder.

Nothing is created once the manager is stopping.
"""

import threading
import time
from typing import Callable, Optional

import xbmcgui

from kofin.core import settings
from kofin.core.log import Logger
from kofin.downloads import store

LOG = Logger(__name__)

# At most one repaint a second beyond the forced ones on begin/finish: the
# write loop ticks every 8 MiB, which on a LAN is many times a second.
RENDER_SECONDS = 1.0

HEADING = 30737


class _Transfer:
    __slots__ = ("name", "done", "total")

    def __init__(self, name: str, total: int) -> None:
        self.name = name
        self.done = 0
        self.total = max(int(total), 0)


class Reporter:
    """The manager's aggregate progress bar; every method is thread-safe."""

    def __init__(self, should_stop: Callable[[], bool]) -> None:
        self._should_stop = should_stop
        self._lock = threading.Lock()
        self._dialog: Optional[xbmcgui.DialogProgressBG] = None
        self._transfers: dict[str, _Transfer] = {}
        self._completed = 0
        self._current = ""
        self._rendered_at = 0.0

    def begin(self, item_id: str, name: str, total_bytes: int) -> None:
        with self._lock:
            self._transfers[item_id] = _Transfer(name, total_bytes)
            self._current = name
            self._render(force=True)

    def tick(self, item_id: str, done_bytes: int) -> None:
        with self._lock:
            transfer = self._transfers.get(item_id)
            if transfer is None:
                return
            transfer.done = max(int(done_bytes), 0)
            self._current = transfer.name
            self._render(force=False)

    def finish(self, item_id: str, completed: bool) -> None:
        """The item left the active set — done, failed, cancelled or up for
        retry. Only a *completed* one advances the count: a retried item is
        back in the pending remainder, and counting its attempt would
        inflate the bar past the work actually done."""
        with self._lock:
            if self._transfers.pop(item_id, None) is None:
                return
            if completed:
                self._completed += 1
            self._render(force=True)

    def idle(self) -> None:
        """A worker found nothing to transfer (an empty queue, or the
        offline hold). The bar closes once nothing is actually moving; the
        next ``begin`` opens a fresh session."""
        with self._lock:
            if not self._transfers:
                self._close()

    def close(self) -> None:
        with self._lock:
            self._close()

    # -- internals (called with the lock held) ---------------------------------

    def _close(self) -> None:
        if self._dialog is not None:
            try:
                self._dialog.close()
            except Exception:  # pragma: no cover - Kodi teardown races
                LOG.debug("progress bar close failed")
            self._dialog = None
        self._completed = 0
        self._current = ""
        self._rendered_at = 0.0

    def _render(self, force: bool) -> None:
        if self._should_stop():
            return  # stop() closes; nothing new appears while stopping
        now = time.monotonic()
        if not force and now - self._rendered_at < RENDER_SECONDS:
            return
        remaining = store.pending_count()
        if not self._transfers:
            if remaining == 0:
                self._close()
            # Otherwise keep the last frame: the gap between two items of a
            # busy queue is one claim cycle, and closing/reopening per item
            # would flicker. A queue *held* with nothing moving is the
            # idle() case, which does close.
            return
        total_items = self._completed + max(remaining, len(self._transfers))
        fractions = sum(
            min(transfer.done / transfer.total, 1.0)
            for transfer in self._transfers.values()
            if transfer.total
        )
        percent = int(100 * (self._completed + fractions) / max(total_items, 1))
        message = "%d/%d — %s" % (
            min(self._completed + 1, total_items),
            total_items,
            self._current,
        )
        heading = settings.localized(HEADING)
        if self._dialog is None:
            dialog = xbmcgui.DialogProgressBG()
            dialog.create(heading, message)
            self._dialog = dialog
        self._dialog.update(min(percent, 100), heading, message)
        self._rendered_at = now
