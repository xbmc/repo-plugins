"""A plugin call on its way, so that the background Kodi TV export steps aside for it.

All of Kodi's Python interpreters share one lock: the export's guide parsing slowed a menu's start
from 0.3 s to over 6 s on a TV stick. The export waits between its steps while a call is marked.
"""

import time

import xbmcgui

from resources.lib.util import kodienv

# Home window property: when the plugin call on its way started. One mark for all calls: of two at
# once, the first to end clears it, and the export may go on early, which costs only speed.
PROPERTY = "%s.plugin_busy" % kodienv.ADDON_ID
# A mark older than this (seconds) is a failed call's: the export goes on.
STALE = 30
# How often (seconds) a waiting export looks again.
WAIT_STEP = 0.2


def begin():
    """Mark a plugin call as on its way."""
    _home().setProperty(PROPERTY, "%.3f" % time.time())


def end():
    """Clear the mark: the call is done."""
    _home().clearProperty(PROPERTY)


def wait_while_busy():
    """Return once no plugin call is on its way (or its mark has gone stale)."""
    home = _home()
    while True:
        mark = home.getProperty(PROPERTY)
        if not mark or time.time() - float(mark) > STALE:
            return
        time.sleep(WAIT_STEP)


def _home():
    return xbmcgui.Window(kodienv.HOME_WINDOW)
