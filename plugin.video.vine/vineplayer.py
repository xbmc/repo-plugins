import sys
import os
import threading
import unicodedata

import xbmc


class VinePlayer(xbmc.Player):
    
    def initialise(self, log = None):
        self.stopped = False
                
        if log is None:
            self.log = xbmc.log
        else:
            self.log = log
            
        self.log('Initialised VinePlayer') 

    def normalize(self, text):
        try:
            text = text.decode('ascii')
        except:
            try:
                text = text.decode('latin1')
            except:
                text = text.decode('utf8', 'ignore')
                
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')

        
    def onPlayBackStarted(self):
        super(VinePlayer, self).onPlayBackStarted()
        self.log('onPlayBackStarted')

        self.log("Title: " + repr(type(self.getVideoInfoTag().getTitle())))        
        self.log("Plot: " + repr(type(self.getVideoInfoTag().getPlot())        ))
        name = self.normalize( self.getVideoInfoTag().getTitle() )
        message = self.normalize( self.getVideoInfoTag().getPlot() )
        
        self.log("name: " + repr(name))        
        self.log("message: " + repr(message))        
        if name != '' or message != '':
            if name == '':
                name = "Vine"

            xbmc.executebuiltin(u'XBMC.Notification(%s, %s)' % (name, message))
            
    def onPlayBackStopped(self):
        super(VinePlayer, self).onPlayBackStopped()
        self.log("onPlayBackStopped")

        self.stopped = True
        
    def isStopped(self):
        return self.stopped
