# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import sys


if len(sys.argv) < 2:
    import xbmcaddon
    from resources.lib.xbmcwrapper import XbmcWrapper
    from resources.lib.helpers.languagehelper import LanguageHelper

    # We do this without the LanguageHelper code, as it will require a Logger
    title = xbmcaddon.Addon().getLocalizedString(LanguageHelper.UpdateRequired)
    message = xbmcaddon.Addon().getLocalizedString(LanguageHelper.UpdateToNewKodi)
    XbmcWrapper.show_dialog(title, message)
else:
    from resources.lib import menu
    add_on_id, command = sys.argv[0:2]

    with menu.Menu(command) as m:
        if command == "queue":
            import xbmc
            xbmc.executebuiltin("Action(Queue)")
        elif command == "refresh":
            import xbmc
            xbmc.executebuiltin("Container.Refresh()")
        elif command == "hidechannel":
            m.hide_channel()
        elif command == "cloak" or command == "uncloak":
            m.toggle_cloak()
        elif command == "bitrate":
            m.set_bitrate()
        elif command == "adaptive":
            m.set_inputstream_adaptive()
        elif command == "channel_settings":
            m.channel_settings()
        elif command == "channel_favs":
            m.favourites()
        elif command == "all_favs":
            m.favourites(all_favorites=True)
        elif command == "add_fav":
            m.add_favourite()
        elif command == "remove_fav":
            m.remove_favourite()
        elif command == "channel_selection":
            m.select_channels()
        elif command == "country_selection":
            m.show_country_settings()
        elif command == "settings":
            m.show_settings()
        else:
            raise IndexError("Missing command in sys.argv: {}".format(sys.argv))
