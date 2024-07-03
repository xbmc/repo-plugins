"""Channel stream loader."""

import inputstreamhelper
import xbmcgui

from lib.providers import get_provider
from lib.utils.xbmctools import localize, ok_dialog


class ChannelManager:
    """."""

    def load_channel_listitem(self, channel_id: str):
        """."""
        stream = get_provider().get_stream_info(channel_id)
        if not stream:
            ok_dialog(localize(30900))
            return

        is_helper = inputstreamhelper.Helper(stream["manifest_type"], drm=stream["drm"])
        if not is_helper.check_inputstream():
            ok_dialog(localize(30901))
            return

        listitem = xbmcgui.ListItem(path=stream["path"])
        listitem.setMimeType(stream["mime_type"])
        listitem.setContentLookup(False)
        listitem.setProperty("inputstream", "inputstream.adaptive")
        listitem.setProperty("inputstream.adaptive.license_type", stream["license_type"])
        listitem.setProperty("inputstream.adaptive.license_key", stream["license_key"])

        return listitem
