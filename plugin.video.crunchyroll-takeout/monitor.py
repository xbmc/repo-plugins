import time
import xbmc

monitor_spew = False # see _Monitor.onNotication


class _Monitor(xbmc.Monitor):
    __leave = False # set to True to make onLeave() be true
    
    #Are we somehow requested to leave?
    def onLeave(self):
        return (self.__leave or 
                xbmc.Monitor().onAbortRequested()
               )

    #Main catcher
    def onNotification(self, sender, method, data):
        #To make debugging a lot easier
        if (monitor_spew): 
            print ("CR Monitor: \nsender: %s\nmethod: %s\ndata:   %s" % (sender, method, data))
        #Head honcho wants a words..
        if sender == "xbmc":
            #..we are requested to leave
            if method == "System.OnQuit":
                self.__leave = True
            #..it has started a scan of the videolibrary
            elif method == "VideoLibrary.OnScanStarted":
                print ("CR Monitor: We are scanning. Add code here")
            #..it has finished a scan of the videolibrary
            elif method == "VideoLibrary.OnScanFinished":
                print ("CR Monitor: We are done scanning. Add code here")

if __name__ == '__main__':
    monitor = _Monitor()
    while not (monitor.onLeave() ):
        xbmc.sleep(500)
        #Wait until the slow heat death of the universe...
