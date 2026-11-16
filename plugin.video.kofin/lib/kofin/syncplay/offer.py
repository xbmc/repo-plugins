"""Whether the SyncPlay root entry is offered at all.

Outside the plugin package so the service (settings_apply's root-menu mirror)
reads it without importing the plugin. The plugin route re-exports both names.
"""

import xbmcvfs

from kofin.core import settings


def external_player_configured() -> bool:
    """A playercorefactory override routes video to a non-kofin external
    player, which SyncPlay cannot drive — the root entry is hidden and the
    menu refuses."""
    return bool(
        xbmcvfs.exists("special://profile/playercorefactory.xml")
        or xbmcvfs.exists("special://masterprofile/playercorefactory.xml")
    )


def available() -> bool:
    """Whether the SyncPlay root entry should be offered (read fresh per
    root listing: the master toggle on, no external player configured)."""
    return settings.get_bool("syncPlayEnabled") and not external_player_configured()
