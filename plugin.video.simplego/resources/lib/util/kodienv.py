"""What the add-on knows of where it runs, with Kodi's core module only (quickplay's fast path uses it)."""

import xbmc

ADDON_ID = "plugin.video.simplego"


def android():
    """Return whether Kodi runs on Android."""
    return xbmc.getCondVisibility("System.Platform.Android")


def untrusted_widevine():
    """Return whether Kodi runs on Windows or macOS, where playing is not even tried.

    Its desktop Widevine module is refused by the licence server (3099).
    """
    return xbmc.getCondVisibility("System.Platform.Windows") or xbmc.getCondVisibility("System.Platform.OSX")


def isa_ready():
    """Return whether Kodi runs on Android with InputStream Adaptive enabled.

    Widevine is then built in, so InputStream Helper has nothing to check.
    """
    return android() and xbmc.getCondVisibility("System.AddonIsEnabled(inputstream.adaptive)")
