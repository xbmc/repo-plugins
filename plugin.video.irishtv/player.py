import os
import sys
import re

from loggingexception import LoggingException

if hasattr(sys.modules["__main__"], "xbmc"):
    xbmc = sys.modules["__main__"].xbmc
else:
    import xbmc

if hasattr(sys.modules["__main__"], "xbmcgui"):
    xbmcgui = sys.modules["__main__"].xbmcgui
else:
    import xbmcgui

if hasattr(sys.modules["__main__"], "xbmcplugin"):
    xbmcplugin = sys.modules["__main__"].xbmcplugin
else:
    import xbmcplugin

import utils

class PlayerLockException(LoggingException):
    """
    Exception raised when IPlayer fails to obtain a resume lock
    """
    pass

class IrishTVPlayer(xbmc.Player):
    """
    An XBMC player object, for supporting Irish TV plugin features during playback
    """

    # Static constants for resume db and lockfile paths, set by default.py on plugin startup
    RESUME_FILE = None
    RESUME_LOCK_FILE = None

    resume = None
    dates_added = None

    def __init__( self, pid, live ):
        if hasattr(sys.modules["__main__"], "log"):
            self.log = sys.modules["__main__"].log
        else:
            from utils import log
            self.log = log

            self.log("")

        self.log("%s: IrishTVPlayer initialised (core_player: %d, pid: %s, live: %s)" % (self, pid, live), xbmc.LOGINFO)
        self.paused = False
        self.live = live
        self.pid = pid
        if os.environ.get( "OS" ) != "xbox":
            self.cancelled = threading.Event()
        if live:
            # Live feed - no resume
            # Setup scheduling?
            pass
        else:
            if os.environ.get( "OS" ) != "xbox":
                # Acquire the resume lock, store the pid and load the resume file
                self._acquire_lock()

    def __del__( self ):
        self.log("%s: De-initialising..." % self, xbmc.LOGINFO)
        # If resume is enabled, try to release the resume lock
        if os.environ.get( "OS" ) != "xbox":
            if not self.live:
                try: self.heartbeat.cancel()
                except: self.log('%s: No heartbeat on destruction' % self, xbmc.LOGWARNING)
                self._release_lock()
            # Refresh container to ensure '(resumeable)' is added if necessary
            xbmc.executebuiltin('Container.Refresh')


    def _acquire_lock( self ):
        if os.path.isfile(IrishTVPlayer.RESUME_LOCK_FILE):
            raise PlayerLockException("Only one instance of IrishTVPlayer can be run at a time. Please stop any other streams you may be watching before opening a new stream")
        else:
            lock_fh = open(IrishTVPlayer.RESUME_LOCK_FILE, 'w')
            try:
                lock_fh.write("%s" % self)
            finally:
                lock_fh.close()

    def _release_lock( self ):
        self_has_lock = False
        lock_fh = open(IrishTVPlayer.RESUME_LOCK_FILE)
        try:
            self_has_lock = (lock_fh.read() == "%s" % self)
        finally:
            lock_fh.close()

        xbmc.log("Lock owner test: %s" % self_has_lock, level=xbmc.LOGDEBUG)
        if self_has_lock:
            self.log("%s: Removing lock file." % self, xbmc.LOGINFO)
            try:
                os.remove(IrishTVPlayer.RESUME_LOCK_FILE)
            except Exception, e:
                l("Error removing IrishTVPlayer resume lock file! (%s)" % e, xbmc.LOGWARNING)

    @staticmethod
    def force_release_lock():
        """
        If something goes wrong and the lock file is present after the IrishTVPlayer object that made it dies,
        it can be force deleted here (accessible from advanced plugin options)
        """
        try:
            os.remove(IrishTVPlayer.RESUME_LOCK_FILE)
            dialog = xbmcgui.Dialog()
            dialog.ok('Lock released', 'Successfully released lock')
        except:
            dialog = xbmcgui.Dialog()
            dialog.ok('Failed to force release lock', 'Failed to release lock')

    def run_heartbeat( self ):
        """
        Method is run every second to perform housekeeping tasks, e.g. updating the current seek time of the player.
        Heartbeat will continue until player stops playing.
        """
        xbmc.log("%s: Heartbeat %d" % (self, time.time()), level=xbmc.LOGDEBUG)
        self.heartbeat = threading.Timer(1.0, self.run_heartbeat)
        self.heartbeat.setDaemon(True)
        self.heartbeat.start()
        if not self.live and not self.cancelled.is_set():
            self.current_seek_time = self.getTime()
            xbmc.log("%s IrishTVPlayer: current_seek_time %s" % (self, self.current_seek_time), level=xbmc.LOGDEBUG)
        elif self.cancelled.is_set():
            self.onPlayBackEnded()

    def onPlayBackStarted( self ):
        # Will be called when xbmc starts playing the stream
        self.log( "%s: Begin playback of pid %s" % (self, self.pid), xbmc.LOGINFO )
        self.paused = False
        if os.environ.get( "OS" ) != "xbox":
            self.run_heartbeat()

    def onPlayBackEnded( self ):
        # Will be called when xbmc stops playing the stream
        if self.heartbeat: self.heartbeat.cancel()
        self.log( "%s: Playback ended." % self, xbmc.LOGINFO)
        if os.environ.get( "OS" ) != "xbox":
            if not self.live:
                self.log( "%s: Saving resume point for pid %s at %fs." % (self, self.pid, self.current_seek_time), xbmc.LOGINFO )
                self.save_resume_point( self.current_seek_time )
        self.__del__()

    def onPlayBackStopped( self ):
        if self.heartbeat: self.heartbeat.cancel()
        # Will be called when user stops xbmc playing the stream
        # The player needs to be unloaded to release the resume lock
        self.log( "%s: Playback stopped." % self, xbmc.LOGINFO)
        if os.environ.get( "OS" ) != "xbox":
            if not self.live:
                self.log("%s: Saving resume point for pid %s at %fs." % (self, self.pid, self.current_seek_time), xbmc.LOGINFO )
                self.save_resume_point( self.current_seek_time )
        self.__del__()

    def onPlayBackPaused( self ):
        # Will be called when user pauses playback on a stream
        self.log( "%s: Playback paused." % self, xbmc.LOGINFO)
        if os.environ.get( "OS" ) != "xbox":
            if not self.live:
                self.log("%s: Saving resume point for pid %s at %fs." % (self, self.pid, self.getTime()), xbmc.LOGINFO )
                self.save_resume_point( self.current_seek_time )
        self.paused = True

    def save_resume_point( self, resume_point ):
        """
        Updates the current resume point for the currently playing pid to resume_point, and commits the result to the resume db file
        """
        resume, dates_added = IrishTVPlayer.load_resume_file()
        resume[self.pid] = resume_point
        dates_added[self.pid] = time.time()
        self.log("%s: Saving resume point (pid %s, seekTime %fs, dateAdded %d) to resume file" % (self, self.pid, resume[self.pid], dates_added[self.pid]), xbmc.LOGINFO)
        IrishTVPlayer.save_resume_file(resume, dates_added)

    @staticmethod
    def load_resume_file():
        """
        Loads and parses the resume file, and returns a dictionary mapping pid -> resume_point
        Resume file format is three columns, separated by a single space, with platform dependent newlines
        First column is pid (string), second column is resume point (float), third column is date added
        If date added is more than thirty days ago, the pid entry will be ignored for cleanup
        Will only actually load the file once, caching the result for future calls.
        """
        
        if not IrishTVPlayer.resume:
            # Load resume file
            IrishTVPlayer.resume = {}
            IrishTVPlayer.dates_added = {}
            if os.path.isfile(IrishTVPlayer.RESUME_FILE):
                self.log("IrishTVPlayer: Loading resume file: %s" % (IrishTVPlayer.RESUME_FILE), xbmc.LOGINFO)
                with open(IrishTVPlayer.RESUME_FILE, 'rU') as resume_fh:
                    resume_str = resume_fh.read()
                tokens = resume_str.split()
                # Three columns, pid, seekTime (which is a float) and date added (which is an integer, datetime in seconds), per line
                pids = tokens[0::3]
                seekTimes = [float(seekTime) for seekTime in tokens[1::3]]
                datesAdded = [int(dateAdded) for dateAdded in tokens[2::3]]
                pid_to_resume_point_map = []
                pid_to_date_added_map = []
                # if row was added less than days_to_keep days ago, add it to valid_mappings
                try: days_to_keep = int(__addon__.getSetting('resume_days_to_keep'))
                except: days_to_keep = 40
                limit_time = time.time() - 60*60*24*days_to_keep
                for i in range(len(pids)):
                    if datesAdded[i] > limit_time:
                        pid_to_resume_point_map.append( (pids[i], seekTimes[i]) )
                        pid_to_date_added_map.append( (pids[i], datesAdded[i]) )
                IrishTVPlayer.resume = dict(pid_to_resume_point_map)
                IrishTVPlayer.dates_added = dict(pid_to_date_added_map)
                self.log("IrishTVPlayer: Found %d resume entries" % (len(IrishTVPlayer.resume.keys())), xbmc.LOGINFO)
                
        return IrishTVPlayer.resume, IrishTVPlayer.dates_added

    @staticmethod
    def delete_resume_point(pid_to_delete):
        self.log("IrishTVPlayer: Deleting resume point for pid %s" % pid_to_delete, xbmc.LOGINFO)
        resume, dates_added = IrishTVPlayer.load_resume_file()
        del resume[pid_to_delete]
        del dates_added[pid_to_delete]
        IrishTVPlayer.save_resume_file(resume, dates_added)

    @staticmethod
    def save_resume_file(resume, dates_added):
        """
        Saves the current resume dictionary to disk. See load_resume_file for file format
        """
        
        IrishTVPlayer.resume = resume
        IrishTVPlayer.dates_added = dates_added
        
        str = ""
        self.log("IrishTVPlayer: Saving %d entries to %s" % (len(resume.keys()), IrishTVPlayer.RESUME_FILE), xbmc.LOGINFO)
        resume_fh = open(IrishTVPlayer.RESUME_FILE, 'w')
        try:
            for pid, seekTime in resume.items():
                str += "%s %f %d%s" % (pid, seekTime, dates_added[pid], os.linesep)
            resume_fh.write(str)
        finally:
             resume_fh.close()

    def resume_and_play( self, url, listitem, is_tv, playresume=False ):
        """
        Intended to replace xbmc.Player.play(playlist), this method begins playback and seeks to any recorded resume point.
        XBMC is muted during seeking, as there is often a pause before seeking begins.
        """

        if os.environ.get( "OS" ) != "xbox" and not self.live and playresume:
            resume, dates_added = IrishTVPlayer.load_resume_file()
            if self.pid in resume.keys():
                self.log("%s: Resume point found for pid %s at %f, seeking..." % (self, self.pid, resume[self.pid]), xbmc.LOGINFO)
                listitem.setProperty('StartOffset', '%d' % resume[self.pid])

        if is_tv:
            play = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        else:
            play = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        play.clear()
        play.add(url, listitem)

        self.play(play)

