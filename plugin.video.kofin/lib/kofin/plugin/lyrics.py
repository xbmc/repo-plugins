"""The lyrics directory: one list item per line of the playing song.

A skin renders lyrics with a fixedlist so Kodi animates the scroll, and a
fixedlist needs a directory to fill it. The lines come from the window
property the service published, so this never asks the server.
"""

from typing import Any

import xbmcgui
import xbmcplugin

from kofin.core import state
from kofin.core.log import Logger

LOG = Logger(__name__)

JsonDict = dict[str, Any]

# Blank rows after the last line. A list scrolls no further than its last
# item; twelve let the deepest page any known overlay is authored with bring
# the last line up to the middle.
TAIL_ROWS = 12


def lyrics(request: Any) -> None:
    """Serve the published lines as a directory."""
    lines = state.lyric_texts()
    LOG.debug("lyrics directory: %d lines", len(lines))
    for line in lines:
        # A blank line still has to occupy a row: the service addresses lines
        # by index, so dropping empties would shift every line after one.
        item = xbmcgui.ListItem(label=line or " ", offscreen=True)
        xbmcplugin.addDirectoryItem(request.handle, "", item, isFolder=False)
    for _ in range(TAIL_ROWS):
        item = xbmcgui.ListItem(label=" ", offscreen=True)
        xbmcplugin.addDirectoryItem(request.handle, "", item, isFolder=False)
    xbmcplugin.endOfDirectory(request.handle, cacheToDisc=False)
