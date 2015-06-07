import os
import sys
import xbmc
import xbmcaddon

addon = xbmcaddon.Addon()

if __name__ == '__main__':
    import resources.lib.common as common
    common.log('ARGV: ' + repr(sys.argv))

    cookie_file = os.path.join(
        xbmc.translatePath(addon.getAddonInfo('profile')), 'fun-cookie.txt')

    from resources.lib import Funimation
    api = Funimation(addon.getSetting('username'),
                     addon.getSetting('password'),
                     cookie_file)

    import resources.lib.nav as nav
    nav.list_menu()
