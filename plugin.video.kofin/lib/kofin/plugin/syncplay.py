"""The ``mode=syncplay`` plugin entry: one IPC message to the service.

The plugin invocation is transient — it cannot hold group state, an Api, or
the player — so everything SyncPlay lives in the service.
This handler only validates that a menu makes sense right now and sends
``SyncPlayMenu``; the service opens the menu on a dedicated worker thread.
"""

from kofin.core import ipc, settings, state, toast
from kofin.core.log import Logger
from kofin.plugin.router import Request

# Re-exported: the root listing and this route gate on them; the gates
# themselves live with the syncplay package so the service can read them
# without importing the plugin.
from kofin.syncplay.offer import available, external_player_configured

LOG = Logger(__name__)

__all__ = ["available", "external_player_configured", "menu"]


def menu(request: Request) -> None:
    if not settings.get_bool("syncPlayEnabled"):
        return

    if external_player_configured():
        _notify(settings.localized(30575))
        return

    if not state.is_online():
        _notify(settings.localized(30574))
        return

    LOG.debug("requesting the SyncPlay menu from the service")
    ipc.notify(ipc.SYNCPLAY_MENU)


def _notify(message: str) -> None:
    """Only ever used for "SyncPlay is unavailable", which is a failure."""
    toast.show(message, toast.ERROR, heading="SyncPlay", time_ms=4000)
