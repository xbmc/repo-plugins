"""Make the use of some Kodi functions easier."""

import json
from enum import Enum
from string import Formatter
from typing import Type, TypeVar

import xbmc
import xbmcaddon
import xbmcgui

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")

T = TypeVar("T", str, int, bool, dict)


class DRM(Enum):
    """List DRM providers."""

    CLEAR_KEY = "org.w3.clearkey"
    PLAY_READY = "com.microsoft.playready"
    WIDEVINE = "com.widevine.alpha"
    WISEPLAY = "com.huawei.wiseplay"


def build_addon_url(path: str = "") -> str:
    """Build addon URL from path."""
    return f"plugin://{ADDON_ID}{path}"


def log(msg: str, log_level: int = xbmc.LOGINFO) -> None:
    """Prefix logs with addon name."""
    xbmc.log(f"[{ADDON_ID}] {msg}", log_level)


def get_addon_info(name: str) -> str:
    """Get addon info from name."""
    return ADDON.getAddonInfo(name)


def get_addon_setting(name: str, t: Type[T] = str) -> T:
    """Get addon setting from name."""
    if t is bool:
        return ADDON.getSettings().getBool(name)

    if t is int:
        return ADDON.getSettings().getInt(name)

    if t is dict:
        try:
            return json.loads(ADDON.getSettings().getString(name))
        except json.decoder.JSONDecodeError:
            return {}

    return ADDON.getSettings().getString(name)


def get_drm() -> str:
    """Return the DRM system available for the current platform."""
    return DRM.WIDEVINE.value


def get_global_setting(name: str, t: Type[T] = str) -> T:
    """Get global Kodi setting from name."""
    cmd = {"id": 0, "jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params": {"setting": name}}
    value = json.loads(xbmc.executeJSONRPC(json.dumps(cmd))).get("result", {}).get("value")

    if t is bool:
        return value == "true"

    if t is int:
        return int(value)

    if t is dict:
        try:
            return json.loads(value)
        except json.decoder.JSONDecodeError:
            return {}

    return value


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


def set_addon_setting(name: str, value: T) -> None:
    """Set addon setting from name."""
    if isinstance(value, bool):
        value = "true" if value else "false"

    if isinstance(value, int):
        value = str(value)

    if isinstance(value, dict):
        value = json.dumps(value)

    ADDON.setSetting(name, value)
