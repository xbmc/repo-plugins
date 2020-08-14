import xbmc, xbmcaddon

class settings():

    def init(self):
        addon = xbmcaddon.Addon()
        self.logLevel = addon.getSetting('log_level')
        if self.logLevel and len(self.logLevel) > 0:
            self.logLevel = int(self.logLevel)
        else:
            self.logLevel = LOG_INFO
            
        self.service_enabled = addon.getSetting('enabled') == 'true'
    
    def __init__( self ):
        self.init()
        
    def Convert(self, origList): 
        newList = list(origList.split(",")) 
        return newList
        
    def readPrefs(self):
      addon = xbmcaddon.Addon()    

      self.iftttKey = addon.getSetting('iftttKey')
      self.iftttUrl = addon.getSetting('iftttUrl')
      self.iftttPath = addon.getSetting('iftttPath')
      self.eventStart = addon.getSetting('eventStart')
      self.eventResume = addon.getSetting('eventResume')
      self.eventPause = addon.getSetting('eventPause')
      self.eventStop = addon.getSetting('eventStop')