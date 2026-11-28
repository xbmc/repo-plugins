import sys
import traceback
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib.ui.UI import UI


def run(argv=None):
    argv = argv or sys.argv
    addon_handle = int(argv[1])
    args = urllib.parse.parse_qs(argv[2][1:])
    mode = args.get('mode', None)

    xbmc.log("plugin.video.3cat - addon.py - args: " + str(args))

    try:
        ui = UI(argv[0], addon_handle, args)
        ui.run(mode, args.get('url', ['']))
    except Exception:
        # Without this Kodi only shows a generic "error getting directory", and the busy
        # spinner of a video can hang until it times out.
        xbmc.log("plugin.video.3cat - unhandled error:\n" + traceback.format_exc(), xbmc.LOGERROR)
        addon = xbmcaddon.Addon()
        xbmcgui.Dialog().notification(addon.getAddonInfo('name'), addon.getLocalizedString(30038),
                                      xbmcgui.NOTIFICATION_ERROR)
        if mode and mode[0] == 'playVideo':
            xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
        else:
            xbmcplugin.endOfDirectory(addon_handle, succeeded=False)
