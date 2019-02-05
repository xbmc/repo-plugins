import xbmc
import xbmcaddon
from resources.lib.kodiwrappers import kodiwrapper
from resources.lib.vrtplayer import tokenresolver


class VrtMonitor(xbmc.Monitor):

    def __init__(self):
       xbmc.Monitor.__init__(self)

    def onSettingsChanged(self):
       addon = xbmcaddon.Addon(id='plugin.video.vrt.nu')
       kodi_wrapper = kodiwrapper.KodiWrapper(None, None, addon)
       kodi_wrapper.log_notice('VRT NU Addon: settings changed')
       token_resolver = tokenresolver.TokenResolver(kodi_wrapper)
       token_resolver.reset_cookies()
       

if __name__ == '__main__':

    monitor = VrtMonitor()

    while not monitor.abortRequested():
       if monitor.waitForAbort(10):
           break