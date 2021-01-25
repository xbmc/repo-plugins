from future.utils import PY2
import xbmc
import os
import xbmcaddon
import xbmcvfs
 
ampache = xbmcaddon.Addon("plugin.audio.ampache")

class Main():

    def __init__(self):
        self.monitor = ServiceMonitor()

        # start mainloop
        self.main_loop()

    def main_loop(self):
        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(1):
                # Abort was requested while waiting. We should exit
                break

    def close():
        pass

class ServiceMonitor( xbmc.Monitor ):

    onPlay = False

    def __init__( self, *args, **kwargs ):
        xbmc.log( 'AmpachePlugin::ServiceMonitor called', xbmc.LOGDEBUG)
        #pass

    def onNotification(self, sender, method, data):
        #i don't know why i have called monitor.onNotification, but now it
        #seems useless
        #xbmc.Monitor.onNotification(self, sender, method, data)
        xbmc.log('AmpachePlugin::Notification %s from %s, params: %s' % (method, sender, str(data)))

        #a little hack to avoid calling rate every time a song start
        if method == 'Player.OnStop':
            self.onPlay = False
        if method == 'Player.OnPlay':
            self.onPlay = True
        #called on infoChanged ( rating )
        if method == 'Info.OnChanged' and self.onPlay:
            #call setRating
            if xbmc.Player().isPlaying():
                xbmc.executebuiltin('RunPlugin(plugin://plugin.audio.ampache/?mode=47)')


def clean_cache():
    if PY2:
        base_dir = xbmc.translatePath( ampache.getAddonInfo('profile'))
        base_dir = base_dir.decode('utf-8')
    else:
        base_dir = xbmcvfs.translatePath( ampache.getAddonInfo('profile'))
    #hack to force the creation of profile directory if don't exists
    if not os.path.isdir(base_dir):
        ampache.setSetting("api-version","350001")
    mediaDir = os.path.join( base_dir , 'media' )
    cacheDir = os.path.join( mediaDir , 'cache' )

    #if cacheDir doesn't exist, create it
    if not os.path.isdir(mediaDir):
        os.mkdir(mediaDir)
        if not os.path.isdir(cacheDir):
            os.mkdir(cacheDir)

    #clean cache on start
    for currentFile in os.listdir(cacheDir):
        #xbmc.log("Clear Cache Art " + str(currentFile),xbmc.LOGDEBUG)
        pathDel = os.path.join( cacheDir, currentFile)
        os.remove(pathDel)


if __name__ == '__main__':
    clean_cache()
    Main()
