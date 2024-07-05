"""Make the use of some Kodi functions easier."""

from enum import Enum
from json import dumps, loads
from string import Formatter

import xbmc
import xbmcaddon
import xbmcgui

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")


class DRM(Enum):
    """List DRM providers."""

    WIDEVINE = "com.widevine.alpha"
    PLAYREADY = "com.microsoft.playready"


def build_addon_url(path: str = "") -> str:
    """Build addon URL from path."""
    return f"plugin://{ADDON_ID}{path}"


def log(msg: str, log_level: int = xbmc.LOGINFO) -> None:
    """Prefix logs with addon name."""
    xbmc.log(f"[{ADDON_ID}] {msg}", log_level)


def get_addon_info(name: str) -> str:
    """Get addon info from name."""
    return ADDON.getAddonInfo(name)


def get_addon_setting(name: str) -> str:
    """Get addon setting from name."""
    return ADDON.getSetting(name)


def get_drm() -> DRM:
    """Return the DRM system available for the current platform."""
    return DRM.WIDEVINE


def get_global_setting(name: str):
    """Get global Kodi setting from name."""
    cmd = {"id": 0, "jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params": {"setting": name}}

    return loads(xbmc.executeJSONRPC(dumps(cmd))).get("result", {}).get("value")


def localize(string_id: int, **kwargs) -> str:
    """Return the translated string from the .po language files, optionally translating variables."""
    if not isinstance(string_id, int) and not string_id.isdecimal():
        return string_id
    if kwargs:
        return Formatter().vformat(ADDON.getLocalizedString(string_id), (), **kwargs)
    return ADDON.getLocalizedString(string_id)


def ok_dialog(msg: str) -> None:
    """Display a popup window with a button."""
    xbmcgui.Dialog().ok(get_addon_info("name"), msg)
