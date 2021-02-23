# -*- coding: utf-8 -*-
"""
The main addon module

Copyright (c) 2017-2018, Leo Moll
SPDX-License-Identifier: MIT

"""

# -- Imports ------------------------------------------------
from resources.lib.plugin import MediathekViewPlugin
from resources.lib.loggerKodi import LoggerKodi
from resources.lib.settingsKodi import SettingsKodi
from resources.lib.notifierKodi import NotifierKodi
import xbmcaddon
import resources.lib.appContext as appContext

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
    appContext.init()
    appContext.initAddon(xbmcaddon.Addon())
    appContext.initLogger(LoggerKodi(appContext.ADDONCLASS.getAddonInfo('id'), appContext.ADDONCLASS.getAddonInfo('version')))
    appContext.initSettings(SettingsKodi(appContext.ADDONCLASS))
    appContext.initNotifier(NotifierKodi(appContext.ADDONCLASS))
    PLUGIN = MediathekViewPlugin()
    PLUGIN.run()
    PLUGIN.exit()
    del PLUGIN
