# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcaddon

addon = xbmcaddon.Addon()

if __name__ == '__main__':
    from resources import common
    common.log('ARGV: ' + repr(sys.argv))

    cookie_file = os.path.join(
        xbmc.translatePath(addon.getAddonInfo('profile')), 'fun-cookie.txt')

    from resources import Funimation
    api = Funimation(addon.getSetting('username'),
                     addon.getSetting('password'),
                     cookie_file)

    from resources import nav
    nav.list_menu()
