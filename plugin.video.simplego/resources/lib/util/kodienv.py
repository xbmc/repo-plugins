"""What the add-on knows of where it runs, with Kodi's core module only (quickplay's fast path uses it)."""

import xbmc

ADDON_ID = "plugin.video.simplego"
# Kodi's Home window: its properties are shared by all of the add-on's processes.
HOME_WINDOW = 10000


def android():
    """Return whether Kodi runs on Android."""
    return xbmc.getCondVisibility("System.Platform.Android")


def phone_or_tablet():
    """Return whether Kodi runs on an Android phone or tablet, which can open a link in its own browser.

    Kodi has no touch condition, but an Android TV build names itself "tv" in ro.build.characteristics.
    Unsure counts as a phone: a link that does nothing on a TV costs nothing, a missing one strands a phone.
    """
    if not android():
        return False
    import subprocess  # only here: quickplay's fast path imports this module

    try:
        found = subprocess.run(["getprop", "ro.build.characteristics"], capture_output=True, text=True, timeout=2)
    except (OSError, subprocess.SubprocessError):
        return True
    return "tv" not in found.stdout.strip().split(",")


def untrusted_widevine():
    """Return whether Kodi runs off Android, where playing is not even tried.

    The licence server refuses the Widevine module InputStream Helper installs there (tried on
    Windows, macOS, Linux and the Raspberry Pi).
    """
    return not android()


def isa_ready():
    """Return whether Kodi runs on Android with InputStream Adaptive enabled.

    Widevine is then built in, so InputStream Helper has nothing to check.
    """
    return android() and xbmc.getCondVisibility("System.AddonIsEnabled(inputstream.adaptive)")
