#!/usr/bin/python

import os,re,xbmc,xbmcgui,xbmcaddon

__addon__ = xbmcaddon.Addon()
__addonID__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__path__ = __addon__.getAddonInfo('path')
__LS__ = __addon__.getLocalizedString
__icon__ = xbmc.translatePath(os.path.join(__path__, 'icon.png'))

OSD = xbmcgui.Dialog()

# Helpers #

def notifyOSD(header, message, icon=xbmcgui.NOTIFICATION_INFO, disp=4000, enabled=True):
    if enabled:
        OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon, disp)

def writeLog(message, level=xbmc.LOGNOTICE):
        xbmc.log('[%s %s]: %s' % (__addonID__, __version__,  message.encode('utf-8')), level)

# End Helpers #

class MyMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs ):
        xbmc.Monitor.__init__(self)
        self.settingsChanged = False

    def onSettingsChanged(self):
        self.settingsChanged = True
        xbmc.executebuiltin('XBMC.RunScript(plugin.service.gto)')

class Starter():

    def __init__(self):
        self.enableinfo = False
        self.prefer_hd = True
        self.mdelay = 0
        self.screenrefresh = 0

    def getNumVals(self, setting, multiplicator):
        try:
            return int(re.match('\d+', __addon__.getSetting(setting)).group()) * multiplicator
        except AttributeError:
            return 0

    def getSettings(self):
        self.enableinfo = True if __addon__.getSetting('enableinfo').upper() == 'TRUE' else False
        self.prefer_hd = True if __addon__.getSetting('prefer_hd').upper() == 'TRUE' else False
        self.mdelay = self.getNumVals('mdelay', 60)
        self.screenrefresh = self.getNumVals('screenrefresh', 60)
        self.delay = self.getNumVals('delay', 1000)
        self.refreshcontent = self.mdelay/self.screenrefresh
        self.mincycle = int(re.match('\d+', __LS__(30151)).group()) * 60
        self.poll = self.screenrefresh/self.mincycle

        writeLog('Settings (re)loaded')
        writeLog('Show notifications:       %s' % (self.enableinfo), level=xbmc.LOGDEBUG)
        writeLog('Prefer HD channel:        %s' % (self.prefer_hd), level=xbmc.LOGDEBUG)
        writeLog('Scraper start delay:      %s msecs' % (self.delay), level=xbmc.LOGDEBUG)
        writeLog('Refresh interval content: %s secs' % (self.mdelay), level=xbmc.LOGDEBUG)
        writeLog('Refresh interval screen:  %s secs' % (self.screenrefresh), level=xbmc.LOGDEBUG)
        writeLog('Refreshing multiplicator: %s' % (self.refreshcontent), level=xbmc.LOGDEBUG)
        writeLog('Poll cycles:              %s' % (self.poll), level=xbmc.LOGDEBUG)

        if self.delay > 0:
            xbmc.sleep(self.delay)

        xbmc.executebuiltin('XBMC.RunScript(plugin.service.gto,action=scrape)')

    def start(self):
        writeLog('Starting %s V.%s' % (__addonname__, __version__))
        notifyOSD(__LS__(30010), __LS__(30106), __icon__, enabled=self.enableinfo)
        self.getSettings()

        _c = 0
        _pc = 0
        monitor = MyMonitor()
        while not monitor.abortRequested():

            if monitor.settingsChanged:
                _c = 0
                _pc = 0
                self.getSettings()
                monitor.settingsChanged = False

            if monitor.waitForAbort(self.mincycle):
                break
            _pc += 1
            if _pc < self.poll:
                continue
            _c += 1
            _pc = 0
            if _c >= self.refreshcontent:
                writeLog('Scraping feeds', level=xbmc.LOGDEBUG)
                xbmc.executebuiltin('XBMC.RunScript(plugin.service.gto,action=scrape)')
                _c = 0
            else:
                writeLog('Refresh content on home screen', level=xbmc.LOGDEBUG)
                xbmc.executebuiltin('XBMC.RunScript(plugin.service.gto,action=refresh)')

if __name__ == '__main__':
    starter = Starter()
    starter.start()
    xbmcgui.Window(10000).setProperty('GTO.blobs', '0')
    xbmcgui.Window(10000).clearProperty('GTO.timestamp')
    del starter
