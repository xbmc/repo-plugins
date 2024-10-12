"""Video stream manager."""

from typing import Callable

import inputstreamhelper
import xbmc
import xbmcplugin

from lib.exceptions import AuthenticationRequired, StreamDataDecodeError, StreamNotIncluded
from lib.providers import get_provider
from lib.router import router
from lib.utils.gui import create_play_item
from lib.utils.kodi import localize, log, ok_dialog


class StreamManager:
    """Load video streams using active provider."""

    def __init__(self):
        """Initialize Stream Manager object."""
        self.provider = get_provider()

    def load_live_stream(self, stream_id: str) -> None:
        """Load live TV stream."""
        self._load_stream(self.provider.get_live_stream_info, stream_id=stream_id)

    def load_chatchup_stream(self, stream_id: str) -> None:
        """Load catchup TV stream."""
        self._load_stream(self.provider.get_catchup_stream_info, stream_id=stream_id)

    def _load_stream(self, stream_getter: Callable[[str], dict], stream_id: str) -> None:
        """Load stream."""
        try:
            stream_info = stream_getter(stream_id)
        except StreamNotIncluded:
            log("Stream not included in subscription", xbmc.LOGERROR)
            ok_dialog(localize(30900))
            xbmcplugin.setResolvedUrl(router.handle, False, create_play_item())
            return
        except StreamDataDecodeError:
            log("Cannot decode stream data", xbmc.LOGERROR)
            ok_dialog(localize(30900))
            xbmcplugin.setResolvedUrl(router.handle, False, create_play_item())
            return
        except AuthenticationRequired as e:
            log(e, xbmc.LOGERROR)
            ok_dialog(localize(30902))
            xbmcplugin.setResolvedUrl(router.handle, False, create_play_item())
            return

        is_helper = inputstreamhelper.Helper(stream_info["protocol"], drm=stream_info["drm_config"]["drm"])

        if is_helper.check_inputstream():
            play_item = create_play_item(stream_info, is_helper.inputstream_addon)
            xbmcplugin.setResolvedUrl(router.handle, True, play_item)
            return

        log("Cannot load InputStream", xbmc.LOGERROR)
        ok_dialog(localize(30901))
        xbmcplugin.setResolvedUrl(router.handle, False, create_play_item())
