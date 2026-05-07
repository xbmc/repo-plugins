#!/usr/bin/python
# coding: utf-8

########################

import xbmc

from resources.lib.helper import *

########################

class Service(xbmc.Monitor):
    def __init__(self):
        while not self.abortRequested():
            self.waitForAbort(100)

    ''' Local library is cached for 24h. This service updates the cache if the library has been changed.
        Since multiple .OnUpdate() callbacks can happen at the same time the refreshing is done by Kodi's AlarmClock function.
    '''
    def onNotification(self, sender, method, data):
        if method in ['VideoLibrary.OnUpdate', 'VideoLibrary.OnScanFinished', 'VideoLibrary.OnCleanFinished'] and ADDON.getSettingBool('cache_enabled'):
            execute('AlarmClock(AeonTajoInfoRefreshLibraryCache,RunScript(script.aeon.tajo.info,call=refresh_library_cache),00:05,silent)')


if __name__ == "__main__":
    ''' Cleanup old cache files on startup
    '''
    cache_cleanup()

    Service()
