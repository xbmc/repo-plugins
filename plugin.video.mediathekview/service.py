# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The main service module

MIT License

Copyright (c) 2017-2020, Leo Moll
"""

# -- Imports ------------------------------------------------
from resources.lib.service import MediathekViewService
import resources.lib.appContext as appContext
from resources.lib.loggerKodi import LoggerKodi
from resources.lib.settingsKodi import SettingsKodi
from resources.lib.notifierKodi import NotifierKodi
import xbmcaddon

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
    appContext.init()
    appContext.initAddon(xbmcaddon.Addon())
    appContext.initLogger(LoggerKodi(appContext.ADDONCLASS.getAddonInfo('id'), appContext.ADDONCLASS.getAddonInfo('version')))
    appContext.initSettings(SettingsKodi(appContext.ADDONCLASS))
    appContext.initNotifier(NotifierKodi(appContext.ADDONCLASS))

    SERVICE = MediathekViewService()
    SERVICE.init()
    SERVICE.run()
    SERVICE.exit()
    del SERVICE
