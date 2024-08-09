"""Video stream manager."""

import inputstreamhelper
import xbmcplugin

from lib.providers import get_provider
from lib.router import router
from lib.utils.gui import create_play_item
from lib.utils.kodi import localize, ok_dialog


class StreamManager:
    """Load streams based using active provider."""

    def __init__(self):
        """Initialize Stream Manager object."""
        self.provider = get_provider()

    def load_live_stream(self, stream_id: str) -> None:
        """Load live TV stream."""
        stream_info = self.provider.get_live_stream_info(stream_id)
        self._load_stream(stream_info)

    def load_chatchup_stream(self, stream_id: str) -> None:
        """Load catchup TV stream."""
        stream_info = self.provider.get_catchup_stream_info(stream_id)
        self._load_stream(stream_info)

    def _load_stream(self, stream_info: dict = None) -> None:
        """Load stream."""
        if stream_info is None:
            ok_dialog(localize(30900))
            xbmcplugin.setResolvedUrl(router.handle, False)
            return

        is_helper = inputstreamhelper.Helper(stream_info["manifest_type"], drm=stream_info["license_type"])

        if is_helper.check_inputstream():
            play_item = create_play_item(stream_info, is_helper.inputstream_addon)
            xbmcplugin.setResolvedUrl(router.handle, True, play_item)
            return

        ok_dialog(localize(30901))
        xbmcplugin.setResolvedUrl(router.handle, False)
