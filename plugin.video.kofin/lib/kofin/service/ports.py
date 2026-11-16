"""The service's view of its managers, and theirs of the service.

Protocols for the managers and for the service as ``SettingsApplier`` sees
it, checked where the concrete objects flow in:
``Library``/``DownloadManager``/``SyncPlayManager`` at their construction
sites in ``main.py``, and ``Service`` itself where it hands ``self`` to
``SettingsApplier``.
"""

import threading
from contextlib import AbstractContextManager, nullcontext
from typing import Any, Callable, Optional, Protocol
from collections.abc import Iterable

from kofin.core.log import Logger

LOG = Logger(__name__)


class LibraryPort(Protocol):
    """What the service drives on the library manager (a Thread)."""

    startup_done: bool
    stop_thread: bool

    @property
    def ident(self) -> Optional[int]: ...

    def start(self) -> None: ...

    def is_alive(self) -> bool: ...

    def join(self, timeout: Optional[float] = None) -> None: ...

    def workers_alive(self) -> bool: ...

    def stop_client(self) -> None: ...

    def enqueue_command(
        self, command: str, data: Optional[dict[str, Any]] = None
    ) -> None: ...

    def userdata(self, data: list[dict[str, Any]]) -> None: ...

    def added(self, ids: Iterable[str]) -> None: ...

    def updated(self, ids: Iterable[str]) -> None: ...

    def removed(self, ids: Iterable[str]) -> None: ...

    def refresh_libraries(self) -> None: ...


class DownloadsPort(Protocol):
    """What the service drives on the download manager."""

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def wake(self) -> None: ...

    def submit(
        self,
        item_ids: list[str],
        origin: str = ...,
        media_types: Optional[list[str]] = None,
        request_id: str = ...,
        request_name: str = ...,
    ) -> None: ...

    def cancel(self, item_id: str) -> None: ...

    def remove(self, item_ids: list[str], subscription: bool = False) -> None: ...

    def remove_all(self) -> None: ...

    def reconcile_subscriptions(self, playlist_id: str = ...) -> None: ...


class SyncPlayPort(Protocol):
    """What the service drives on the SyncPlay manager — directly, and the
    hook names ``forward`` reaches by string (on_wake/on_sleep/on_kodi_play)."""

    def stop(self, leave: bool = ...) -> None: ...

    def adopt_group(self, group_id: str) -> None: ...

    def on_notification(self, method: str, data: Any) -> None: ...

    def refresh_tempo_session(self) -> None: ...

    def on_wake(self) -> None: ...

    def on_sleep(self) -> None: ...

    def on_kodi_play(self, data: Any) -> None: ...

    def on_foreign_claim(self, claim: Any) -> None: ...

    def on_provider_register(self, sender: str, payload: Any) -> None: ...

    def on_propose(self, payload: Any) -> None: ...

    def publish_session_state(self, announce: bool = ...) -> None: ...


class ServiceHooks(Protocol):
    """What ``SettingsApplier`` reaches back into the service for."""

    _restart_requested: bool
    _online: bool
    _stopping: threading.Event
    library: Optional[LibraryPort]
    syncplay: Optional[SyncPlayPort]

    def modal(self, kind: str) -> AbstractContextManager[None]: ...

    def _start_library(self) -> None: ...

    def _start_syncplay(self) -> None: ...

    def _stop_syncplay(self) -> None: ...

    def _start_downloads(self) -> None: ...

    def _stop_downloads(self) -> None: ...

    def _start_backdrop(self, force: bool = ...) -> None: ...


def forward(manager: Optional[object], name: str, *args: Any) -> None:
    """Call a manager hook by name without letting it break the caller —
    the one shape behind ``main._syncplay_forward`` and
    ``player._syncplay_event``."""
    if manager is None:
        return
    try:
        getattr(manager, name)(*args)
    except Exception:
        LOG.exception("SyncPlay %s hook failed", name)


def no_modal(kind: str) -> AbstractContextManager[None]:
    """The dialog record of a player or picker built without a service."""
    return nullcontext()


def spawn_once(
    current: Optional[threading.Thread],
    target: Callable[..., None],
    name: str,
    *args: Any,
) -> Optional[threading.Thread]:
    """Start a named one-shot daemon worker unless the previous one still
    runs; returns the new thread, or None when busy. The caller
    keeps the slot — and its own busy message. ``current=None`` is the
    fire-and-forget case (the player's prompt threads)."""
    if current is not None and current.is_alive():
        return None
    thread = threading.Thread(target=target, args=args, name=name, daemon=True)
    thread.start()
    return thread
