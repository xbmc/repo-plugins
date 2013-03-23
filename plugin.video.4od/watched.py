import sys
import os
import threading

import xbmc

class Watched():
    
    def __init__(self):
        self.folder = sys.modules["__main__"].WATCHED_FOLDER
    
    def isWatched(self, episodeId):
        filePath = os.path.join(self.folder, episodeId)

        if os.access(filePath, os.F_OK):
            return True
        
        return False

    def setWatched(self, episodeId):
        if not os.path.isdir(self.folder):
            os.makedirs(self.folder)
            
        filePath = os.path.join(self.folder, episodeId)
        
        open(filePath, 'w').close()
        
    def clearWatched(self, episodeId):
        filePath = os.path.join(self.folder, episodeId)

        if os.access(filePath, os.F_OK):
            os.remove(filePath)

SLEEP_MILLIS = 2000

class WatchedPlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        super(WatchedPlayer, self).__init__(*args, **kwargs)    
        #self._playbackCompletedLock = threading.Event()
        #self._playbackCompletedLock.clear()
        self.totalTime = 1
        self.currentTime = 0


    def initialise(self, threshold, episodeId, log = None):
        self.threshold = threshold
        self.episodeId = episodeId
        
        if log is None:
            self.log = xbmc.log
        else:
            self.log = log
            
        self.log('Initialised WatchedPlayer, threshold: %s' % threshold) 

        
    
#    def play(self, url = None, listitem = None, windowed = False):
#        super(WatchedPlayer, self).play(url, listitem, windowed)
        
        #xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, listitem, windowed)
#        self.episodeId = listitem['episodeId']
        
    def waitForPlaybackCompleted(self):
        try:
            #while self.isPlaying() and not self._playbackCompletedLock.isSet():
            while self.isPlaying():
                self.currentTime = self.getTime()
                xbmc.sleep(SLEEP_MILLIS)
        except (Exception) as exception:
            self.log("Exception: " + repr(exception))
            
    def checkWatched(self):
        percentWatched = self.currentTime / self.totalTime

        self.log( 'current time: ' + str(self.currentTime) + ' total time: ' + str(self.totalTime) + ' percent watched: ' + str(percentWatched))
        if percentWatched >= self.threshold:
            self.log( 'Auto-Watch - Setting %s to watched' % self.episodeId )
            Watched().setWatched(self.episodeId)
            xbmc.executebuiltin( "Container.Refresh" )

    def onPlayBackStarted(self):
        super(WatchedPlayer, self).onPlayBackStarted()

        self.totalTime = self.getTotalTime()
        
        if self.totalTime == 0:
            xbmc.sleep(1000)
            self.totalTime = self.getTotalTime()
        
        if self.totalTime == 0:
            self.log("Error getting totalTime", xbmc.LOGWARNING)
            return
            
        self.currentTime = 0
        
        if not Watched().isWatched(self.episodeId):
            self.waitForPlaybackCompleted()
            self.checkWatched()
        
    """     
    def onPlayBackStopped(self):
        super(WatchedPlayer, self).onPlayBackStopped()
        self.log("onPlayBackStopped")

        self._playbackCompletedLock.set()
        self.active = False
        self.checkWatched()

    def onPlayBackEnded(self):
        super(WatchedPlayer, self).onPlayBackEnded()
        self.log("onPlayBackEnded")

        self._playbackCompletedLock.set()
        self.active = False
        self.checkWatched()
    """