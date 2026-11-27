"""SyncPlay client for Kodi.

Follows the SyncPlay protocol specification (docs/SYNCPLAY.md in the
kontell/syncplay-conformance repository), speaking v1 to stock servers and v2
where negotiated (including the plugin binding: Hello capability probe §2.1,
dedicated time-sync socket §3.1, hot join §7.1). Wiring:

- service/remote.py routes SyncPlayCommand / SyncPlayGroupUpdate websocket
  messages into SyncPlayManager.on_notification; service/main.py forwards
  WebSocketConnected (reconnects) and the SyncPlayMenu IPC.
- service/player.py forwards its playback callbacks into the manager, which
  distinguishes user intent from SyncPlay's own player actions.
"""

from kofin.syncplay.manager import SyncPlayManager
from kofin.syncplay.ui import show_menu

__all__ = ["SyncPlayManager", "show_menu"]
