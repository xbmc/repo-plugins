"""Kodi plumbing every part of the add-on shares: settings, strings, logging, platform checks."""

import json
import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib.util import kodienv

_addon = xbmcaddon.Addon()
ADDON_ID = kodienv.ADDON_ID
PROFILE = xbmcvfs.translatePath(_addon.getAddonInfo("profile"))
ADDON_PATH = xbmcvfs.translatePath(_addon.getAddonInfo("path"))

# The platform checks live with the fast path's (see kodienv).
android = kodienv.android
phone_or_tablet = kodienv.phone_or_tablet
untrusted_widevine = kodienv.untrusted_widevine
isa_ready = kodienv.isa_ready

# Set on login and logout, so the service rewrites the Kodi TV files (public guide vs subscriber's).
LOGIN_CHANGED = "%s.login_changed" % ADDON_ID
# A settings change the service should export for (the parental lock). A list change (favourites,
# channel order) is not one: the next scheduled export takes it up.
EXPORT_REQUEST = "%s.export_request" % ADDON_ID


def addon():
    """Return the add-on, with its settings as reload_settings last read them."""
    return _addon


def open_in_browser(url):
    """Open the address in the device's default browser (Android).

    No package: Kodi then passes a null one, so Android picks the default app for the address.
    """
    xbmc.executebuiltin('StartAndroidActivity("","android.intent.action.VIEW","","%s")' % url)


def set_setting(setting_id, value):
    """Write a setting (bool, int or text by the value's type), only if it changed.

    Each write wakes the service (see service.background._Monitor), and read-only rows are rewritten often.
    """
    settings = addon()
    if isinstance(value, bool):
        read, write = settings.getSettingBool, settings.setSettingBool
    elif isinstance(value, int):
        read, write = settings.getSettingInt, settings.setSettingInt
    else:
        read, write = settings.getSetting, settings.setSetting
    if read(setting_id) != value:
        write(setting_id, value)


def reload_settings():
    """Make a fresh Addon object, to read the settings as they are now.

    An older one keeps the settings as they were then (Kodi 20+).
    """
    global _addon
    _addon = xbmcaddon.Addon()


def name():
    """Return the add-on's name."""
    return _addon.getAddonInfo("name")


def string(string_id):
    """Return the add-on's localized string with this ID."""
    return _addon.getLocalizedString(string_id)


def log(msg, level=xbmc.LOGDEBUG):
    """Write a line to Kodi's log, tagged with the add-on's ID.

    Debug by default: the official repository wants no more from an add-on's routine lines
    (https://kodi.wiki/view/Add-on_rules#Requirements_for_all_python_addons).
    """
    xbmc.log("[%s] %s" % (ADDON_ID, msg), level)


def coloured(colour, text):
    """Return text in a colour by its name in Kodi's colour list (a skin can set it), as label markup."""
    return "[COLOR %s]%s[/COLOR]" % (colour, text)


def home():
    """Return Kodi's Home window: its properties are shared by all of the add-on's processes."""
    return xbmcgui.Window(kodienv.HOME_WINDOW)


def cast_kinds():
    """Return the programme types ("movie", "series", "other") the cast settings want the cast of."""
    return {kind for kind in ("movie", "series", "other") if addon().getSettingBool("info_" + kind)}


def close_settings():
    """Close the add-on's settings dialog (Kodi saves what it shows), and wait until it has."""
    xbmc.executebuiltin("Dialog.Close(addonsettings,true)")
    monitor = xbmc.Monitor()
    for _ in range(40):
        if not xbmc.getCondVisibility("Window.IsActive(addonsettings)") or monitor.waitForAbort(0.25):
            return


def open_settings():
    """Open the add-on's settings dialog anew: Kodi lists its categories only when it opens."""
    xbmc.executebuiltin("Addon.OpenSettings(%s)" % ADDON_ID)


def json_rpc(method, **params):
    """Make a JSON-RPC call and return its result; None if Kodi answered with an error."""
    reply = xbmc.executeJSONRPC(json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}))
    try:
        return json.loads(reply).get("result")
    except (TypeError, ValueError):
        return None


def kodi_setting(setting, default=None):
    """Return one of Kodi's own settings (Settings.GetSettingValue), or default."""
    return (json_rpc("Settings.GetSettingValue", setting=setting) or {}).get("value", default)


def kodi_major():
    """Return Kodi's major version (21 for Kodi 21.x)."""
    return int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])


_KODI_STRINGS = {}  # Kodi's own strings, asked once per call of the add-on (see kodi_string)


def kodi_string(string_id):
    """Return one of Kodi's own strings (xbmc.getLocalizedString), asked once: rows ask the same ones."""
    if string_id not in _KODI_STRINGS:
        _KODI_STRINGS[string_id] = xbmc.getLocalizedString(string_id)
    return _KODI_STRINGS[string_id]


def clock(seconds):
    """Format seconds as a clock ("1:02:03")."""
    return "%d:%02d:%02d" % (seconds // 3600, seconds % 3600 // 60, seconds % 60)


def ensure_dir(path):
    """Create the folder if missing, and return its path."""
    os.makedirs(path, exist_ok=True)
    return path
