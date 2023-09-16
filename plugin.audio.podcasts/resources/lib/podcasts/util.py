import os

import xbmcaddon
import xbmcvfs


def get_asset_path(asset: str) -> str:

    addon = xbmcaddon.Addon()
    return os.path.join(xbmcvfs.translatePath(addon.getAddonInfo('path')),
                        "resources",
                        "assets", asset)
