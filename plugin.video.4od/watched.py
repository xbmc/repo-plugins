import sys
import os
import threading
import time

from resumeplayer import ResumePlayer 
import xbmc

class Watched():
    
    # Static constants for watch db and lockfile paths, set by default.py on plugin startup
    WATCHED_FILE = None
    WATCHED_LOCK_FILE = None
    ADDON = None
    
    watchedEpisodes = None
    
    def __init__(self, dataFolder):
        self.folder = os.path.join( dataFolder, 'watched' )

    @staticmethod
    def isWatched(episodeId):
        watchedEpisodes = Watched.load_watched_file()
        if episodeId in watchedEpisodes:
            return True
        
        return False 
        
    @staticmethod
    def setWatched(episodeId):
        """
        Updates the current date added for the currently playing episodeId, and commits the result to the watched db file
        """
        watchedEpisodes = Watched.load_watched_file()
        watchedEpisodes[episodeId] = time.time()
        xbmc.log(u"Saving watched entry (episodeId %s, dateAdded %d) to watched file" % (episodeId, watchedEpisodes[episodeId]), xbmc.LOGINFO)
        Watched.save_watched_file(watchedEpisodes)
        
    @staticmethod
    def clearWatched(episodeId):
        xbmc.log(u"WatchedPlayer: Deleting watched entry for episodeId %s" % episodeId, xbmc.LOGINFO)
        watchedEpisodes = Watched.load_watched_file()
        del watchedEpisodes[episodeId]
        Watched.save_watched_file(watchedEpisodes)

    @staticmethod
    def load_watched_file():
        """
        Loads and parses the watched file, and returns a dictionary mapping episodeId -> watched_point
        Watched file format is two columns, separated by a single space, with platform dependent newlines
        First column is episodeId (string), second  column is date added
        If date added is more than thirty days ago, the episodeId entry will be ignored for cleanup
        Will only actually load the file once, caching the result for future calls.
        """
        
        if not Watched.watchedEpisodes:
            # Load watched file
            Watched.watchedEpisodes = {}
            if os.path.isfile(Watched.WATCHED_FILE):
                xbmc.log(u"Watched: Loading watched file: %s" % (Watched.WATCHED_FILE), xbmc.LOGINFO)
                with open(Watched.WATCHED_FILE, 'rU') as watched_fh:
                    watched_str = watched_fh.read()
                tokens = watched_str.split()
                # Three columns, episodeId, seekTime (which is a float) and date added (which is an integer, datetime in seconds), per line
                episodeIds = tokens[0::2]
                datesAdded = [int(dateAdded) for dateAdded in tokens[1::2]]
                episodeId_to_date_added_map = []
                # if row was added less than days_to_keep days ago, add it to valid_mappings
                try: days_to_keep = int(Watched.ADDON.getSetting(u'watched_days_to_keep'))
                except: days_to_keep = 40
                limit_time = time.time() - 60*60*24*days_to_keep
                for i in range(len(episodeIds)):
                    if datesAdded[i] > limit_time:
                        episodeId_to_date_added_map.append( (episodeIds[i], datesAdded[i]) )

                Watched.watchedEpisodes = dict(episodeId_to_date_added_map)
                xbmc.log(u"Watched: Found %d watched entries" % (len(Watched.watchedEpisodes.keys())), xbmc.LOGINFO)
                
        return Watched.watchedEpisodes

    @staticmethod
    def save_watched_file(watchedEpisodes):
        """
        Saves the current watched dictionary to disk. See load_watched_file for file format
        """
        
        Watched.watchedEpisodes = watchedEpisodes
        
        string = u""
        xbmc.log(u"Watched: Saving %d entries to %s" % (len(watchedEpisodes.keys()), Watched.WATCHED_FILE), xbmc.LOGINFO)
        watched_fh = open(Watched.WATCHED_FILE, u'w')
        try:
            for episodeId in watchedEpisodes:
                string += u"%s %d%s" % (episodeId, watchedEpisodes[episodeId], os.linesep)
            watched_fh.write(string)
        finally:
             watched_fh.close()


SLEEP_MILLIS = 2000

class WatchedPlayer(ResumePlayer):
    
    def __init__(self, *args, **kwargs):
        super(WatchedPlayer, self).__init__(*args, **kwargs)    
        #self._playbackCompletedLock = threading.Event()
        #self._playbackCompletedLock.clear()
        self.totalTime = 1
        self.currentTime = 0


    def initialise(self, live, playerName, threshold, episodeId, resumeEnabled, log = None):
        super(WatchedPlayer, self).init(episodeId, live, playerName, resumeEnabled)
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
            Watched.setWatched(self.episodeId)
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
        
        watchedEpisodes = Watched.load_watched_file()
        if self.episodeId not in watchedEpisodes:
            self.log(u"%s: episodeId %s not watched, waiting for playback completion" % (self, self.episodeId), xbmc.LOGINFO)
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