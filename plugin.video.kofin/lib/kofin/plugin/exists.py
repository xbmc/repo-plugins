"""Answer Kodi's existence probe for a library row filed under a plugin URL
of kofin's own shape.

Kodi's clean asks the add-on about the rows under a bound plugin path. A row
under ``/native/`` is the pipeline's and the provider answers for it; this
route answers for the other shapes an earlier Kofin filed, a folder of one or
two Jellyfin ids or a ``mode=play`` file, from the URL alone and never the
server: a transient outage must not erase a library. Kodi only calls this
route after addon.xml has opted each video content type in through
``medialibraryscanpath``.
"""

from urllib.parse import urlsplit

import xbmcgui
import xbmcplugin

from kofin.plugin.router import Request


def check_exists(request: Request) -> None:
    """Resolve valid library folders and playable items without playing them."""
    url = urlsplit(request.base_url)
    parts = [part for part in url.path.split("/") if part]
    valid_folder = len(parts) in (1, 2) and all(_jellyfin_id(p) for p in parts)
    valid_file = (
        valid_folder
        and request.params.get("mode") == "play"
        and _jellyfin_id(request.params.get("id", ""))
    )
    valid = (
        request.params.get("kodi_action") == "check_exists"
        and url.scheme == "plugin"
        and url.netloc == "plugin.video.kofin"
        and (valid_file or (valid_folder and "mode" not in request.params))
    )
    # GetPluginResult only reads the success flag; the URL is never played.
    xbmcplugin.setResolvedUrl(
        request.handle, valid, xbmcgui.ListItem(path=request.base_url)
    )


def _jellyfin_id(value: str) -> bool:
    return len(value) == 32 and all(c in "0123456789abcdefABCDEF" for c in value)
