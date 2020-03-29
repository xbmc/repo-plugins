# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import sys

import xbmcgui
import xbmcaddon


def install_widevine():
    # Because Retrospect also has a config.py module, we can't really use Retrospect and the
    # AdaptiveStream Helper add-on in a single Python scripts. Doing it barefoot then.
    add_on = xbmcaddon.Addon(sys.argv[1])
    msg_box = xbmcgui.Dialog()
    ok = msg_box.yesno(add_on.getLocalizedString(30532), add_on.getLocalizedString(30533))
    if ok:
        try:
            import inputstreamhelper
            is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
            if is_helper.check_inputstream():
                xbmcgui.Dialog().notification(
                    add_on.getLocalizedString(30532),
                    add_on.getLocalizedString(30535),
                    icon="info",
                    time=5000)
            else:
                xbmcgui.Dialog().notification(
                    add_on.getLocalizedString(30532),
                    add_on.getLocalizedString(30534),
                    icon="error",
                    time=5000)
        except:
            xbmcgui.Dialog().notification(
                add_on.getLocalizedString(30532),
                add_on.getLocalizedString(30534),
                icon="error",
                time=5000)


install_widevine()
