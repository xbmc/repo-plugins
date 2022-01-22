"""
Wizard that runs a first-time start of the plug in
"""
import xbmc
import xbmcaddon
import xbmcgui

from . import kodiutils

ADDON = xbmcaddon.Addon()


def show_wizard():
    """Shows the first run wizard
    """

    if not ADDON.getSettingBool('run_wizard'):
        return False

    xbmc.log("Running first start wizard")
    dialog = xbmcgui.Dialog()

    # Information about 720p and 1080p
    complete = dialog.ok(kodiutils.get_string(30070),
                         kodiutils.get_string(30071))

    if complete:
        ADDON.setSettingBool('run_wizard', False)

    return True
