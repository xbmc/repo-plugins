
import sys
import xbmcgui
import xbmc

class PersonInfo(xbmcgui.WindowXMLDialog):

    details = {}
    showMovies = False
    
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        xbmc.log("WINDOW INITIALISED")

    def onInit(self):
        self.action_exitkeys_id = [10, 13]
        
        self.getControl(3000).setLabel(self.details["name"])
        self.getControl(3001).setText(self.details["overview"])
           
    def setInfo(self, data):
        self.details = data
            
    def onFocus(self, controlId):
        pass
        
    def doAction(self):
        pass

    def closeDialog(self):
        self.close()        
        
    def onClick(self, controlID):

        if(controlID == 3002):
            self.showMovies = True
            
            xbmc.executebuiltin('Dialog.Close(movieinformation)') 
            self.close()

        pass        

