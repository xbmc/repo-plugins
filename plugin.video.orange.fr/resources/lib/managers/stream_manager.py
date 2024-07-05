"""Video stream manager."""

import inputstreamhelper
import xbmcgui
import xbmcplugin

from lib.providers import get_provider
from lib.router import router
from lib.utils.gui import create_video_item
from lib.utils.kodi import localize, ok_dialog


class StreamManager:
    """Load streams based using active provider."""

    def __init__(self):
        """Initialize Stream Manager object."""
        self.provider = get_provider()

    def load_live_stream(self, stream_id: str) -> xbmcgui.ListItem:
        """Load live TV stream."""
        stream_info = self.provider.get_live_stream_info(stream_id)
        if not stream_info:
            ok_dialog(localize(30900))
            return

        is_helper = inputstreamhelper.Helper(stream_info["manifest_type"], drm=stream_info["drm"])
        if not is_helper.check_inputstream():
            ok_dialog(localize(30901))
            return

        list_item = create_video_item(stream_info)
        xbmcplugin.setResolvedUrl(router.handle, True, list_item)

    def load_chatchup_stream(self, stream_id: str) -> xbmcgui.ListItem:
        """Load catchup TV stream."""
        stream_info = self.provider.get_catchup_stream_info(stream_id)
        if not stream_info:
            ok_dialog(localize(30900))
            return

        is_helper = inputstreamhelper.Helper(stream_info["manifest_type"], drm=stream_info["drm"])
        if not is_helper.check_inputstream():
            ok_dialog(localize(30901))
            return

        list_item = create_video_item(stream_info)
        xbmcplugin.setResolvedUrl(router.handle, True, list_item)
