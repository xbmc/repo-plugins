import xbmc
import xbmcgui
import xbmcaddon

class Database():

    logLevel = 0
    addonSettings = None
    getString = None
    LogCalls = False
    TrackLog = ""
    TotalUrlCalls = 0

    def __init__(self, *args):
        self.addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        self.getString = self.addonSettings.getLocalizedString

    def get(self, key):
        return xbmcgui.Window( 10000 ).getProperty(key)
        
    def set(self, key, value):
        if value==None:
            value=''
        xbmcgui.Window( 10000 ).setProperty(key, value)
        
    def __del__(self):
        return
        # xbmc.log("\rURL_REQUEST_REPORT : Total Calls : " + str(self.TotalUrlCalls) + "\r" + self.TrackLog)
        
        