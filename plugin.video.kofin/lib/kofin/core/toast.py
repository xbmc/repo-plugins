"""The one place a toast's heading, icon and sound are decided.

Kodi takes the icon as a *string*: "info", "warning" and "error" select its own
three glyphs, and any other value is used as an image path
(``interfaces/legacy/Dialog.cpp``, which also turns an empty icon into "info").
So the level a caller asks for is what picks between kofin's icon and Kodi's:

* :data:`INFO` -- kofin reporting that something happened. The addon icon says
  who is talking, which is the useful information; Kodi's blue "i" says
  nothing a viewer needs.
* :data:`WARNING` / :data:`ERROR` -- something was refused or went wrong, and
  Kodi's glyph is the fastest way to read that at a glance. Branding a failure
  only softens it.

Sound is off by default and no caller turns it on. Kodi's own default is
``sound=True``.

Nothing here raises. A toast is cosmetic, and every caller sits on a path
where losing the *message* is survivable but losing the work behind it is not
-- a websocket callback that goes on to register capabilities, a sync worker
mid-library, a player callback thread.
"""

import os

import xbmcgui

from kofin.core import settings
from kofin.core.log import Logger

LOG = Logger(__name__)

INFO = "info"
WARNING = "warning"
ERROR = "error"

DEFAULT_HEADING = "Kofin"
DEFAULT_TIME_MS = 5000

# Per addon.xml's <icon>. Kodi resolves the path itself, so a plain filesystem
# path from the addon's own install directory is enough.
ICON_RELATIVE_PATH = ("resources", "media", "icon.png")


def addon_icon() -> str:
    """The addon icon's absolute path, or "" when it cannot be determined.

    Read fresh rather than cached: ``addon_path()`` is one cheap call, toasts
    are rare, and a module-level cache would be exactly the kind of global the
    service's in-process restart has to survive.
    """
    try:
        path = settings.addon_path()
    except Exception:  # pragma: no cover - defensive
        return ""
    if not path:
        # A settings read can come back empty when Kodi fails to load the
        # addon document (see service/settings_apply.py); fall back rather
        # than hand Kodi a path to nowhere, which draws a blank icon.
        return ""
    return os.path.join(path, *ICON_RELATIVE_PATH)


def icon_for(level: str) -> str:
    """The icon string Kodi should get for ``level``."""
    if level == INFO:
        return addon_icon() or xbmcgui.NOTIFICATION_INFO
    if level == WARNING:
        return xbmcgui.NOTIFICATION_WARNING
    return xbmcgui.NOTIFICATION_ERROR


def show(
    message: str,
    level: str = INFO,
    heading: str = DEFAULT_HEADING,
    time_ms: int = DEFAULT_TIME_MS,
    sound: bool = False,
) -> None:
    """Raise a toast. Never raises, whatever Kodi does with it."""
    try:
        xbmcgui.Dialog().notification(heading, message, icon_for(level), time_ms, sound)
    except Exception as error:  # pragma: no cover - defensive
        LOG.warning("toast failed (%s): %s", message, error)
