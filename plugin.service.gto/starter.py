#!/usr/bin/python

import os,re,xbmc,xbmcgui,xbmcaddon

__addon__ = xbmcaddon.Addon()
__addonID__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__path__ = __addon__.getAddonInfo('path')
__LS__ = __addon__.getLocalizedString
__icon__ = xbmc.translatePath(os.path.join(__path__, 'icon.png'))

HOME = xbmcgui.Window(10000)
DELAY = 15                      # wait for PVR content
CYCLE = 60                      # poll cycle
OSD = xbmcgui.Dialog()

__screenrefresh__ = 0
__refreshratio__ = 0

# Helpers #

def writeLog(message, level=xbmc.LOGDEBUG):
        xbmc.log('[%s %s]: %s' % (__addonID__, __version__,  message.encode('utf-8')), level)

# End Helpers #

def getNumVals(setting, multiplicator):
    try:
        return int(re.match('\d+', __addon__.getSetting(setting)).group()) * multiplicator
    except AttributeError:
        return 0

def getSettings():
    global __screenrefresh__
    global __refreshratio__

    __enableinfo__ = True if __addon__.getSetting('enableinfo').upper() == 'TRUE' else False
    __prefer_hd__ = True if __addon__.getSetting('prefer_hd').upper() == 'TRUE' else False
    __mdelay__ = getNumVals('mdelay', 60)
    __screenrefresh__ = getNumVals('screenrefresh', 60)
    __refreshratio__ = __mdelay__ / __screenrefresh__
    __scrapermodule__ = __addon__.getSetting('scraper')

    writeLog('Settings (re)loaded')
    writeLog('preferred scraper module: %s' % (__scrapermodule__))
    writeLog('Show notifications:       %s' % (__enableinfo__))
    writeLog('Prefer HD channel:        %s' % (__prefer_hd__))
    writeLog('Refresh interval content: %s secs' % (__mdelay__))
    writeLog('Refresh interval screen:  %s secs' % (__screenrefresh__))
    writeLog('Refreshing ratio:         %s' % (__refreshratio__))

    xbmc.executebuiltin('XBMC.RunScript(plugin.service.gto,action=scrape)')


class MyMonitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs ):
        xbmc.Monitor.__init__(self)
        self.settingsChanged = False

    def onSettingsChanged(self):
        self.settingsChanged = True
        getSettings()
        xbmc.executebuiltin('XBMC.RunScript(plugin.service.gto,action=scrape)')


class Starter():

    def __init__(self):
        pass

    def start(self):
        writeLog('Starting %s V.%s' % (__addonname__, __version__), level=xbmc.LOGNOTICE)
        getSettings()

        HOME.setProperty('PVRisReady', 'no')

        _c = 0
        _attempts = 4

        monitor = MyMonitor()

        while not monitor.abortRequested():

            if monitor.settingsChanged:
                _c = 0
                _attempts = 4
                monitor.settingsChanged = False

            while HOME.getProperty('PVRisReady') == 'no' and _attempts > 0:
                if monitor.waitForAbort(DELAY): return
                if HOME.getProperty('PVRisReady') == 'yes': break
                xbmc.executebuiltin('XBMC.RunScript(plugin.service.gto,action=refresh)')
                _attempts -= 1

            writeLog('Remaining next action in %s seconds' % (__screenrefresh__))
            if monitor.waitForAbort(__screenrefresh__): break
            _c += 1

            if _c >= __refreshratio__:
                writeLog('Scraping feeds')
                xbmc.executebuiltin('XBMC.RunScript(plugin.service.gto,action=scrape)')
                _c = 0

            writeLog('Refresh content')
            xbmc.executebuiltin('XBMC.RunScript(plugin.service.gto,action=refresh)')

if __name__ == '__main__':
    starter = Starter()
    starter.start()
    HOME.setProperty('GTO.blobs', '0')
    HOME.clearProperty('GTO.timestamp')
    del starter
