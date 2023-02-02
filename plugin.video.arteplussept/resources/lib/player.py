from xbmcswift2 import xbmc
from . import api

# this player send request to Arte TV API
# to synchronise playback progress
# when playback is paused or stopped or crashed
class Player(xbmc.Player):

    def __init__(self, plugin, settings, program_id):
        super(Player, self).__init__()
        self.plugin=plugin
        self.settings=settings
        self.program_id=program_id
        self.last_time=None

    def isPlayback(self):
        try:
            # need to keep track of last time to avoid 
            # RuntimeError: Kodi is not playing any media file
            # when calling player.getTime() in onPlayBackStopped()
            self.last_time = self.getTime()
            return self.isPlaying() and self.isPlayingVideo() and self.last_time >= 0
        except Exception:
            return False

    def onPlayBackStopped(self):
        # Will be called when user stops playing a file.
        self.synchProgress()
        pass

    def onPlayBackEnded(self):
        # Will be called when kodi stops playing a file.
        self.synchProgress()
        pass

    def onPlayBackError(self):
        # Will be called when kodi stops playing a file.
        self.synchProgress()
        pass

    def onPlayBackPaused(self):
        # Will be called when kodi stops playing a file.
        self.synchProgress()
        pass

    def synchProgress(self):
        if not self.settings.username or not self.settings.password:
            xbmc.log("Unable to synchronise progress with Arte TV for {pid}".format(pid=self.program_id))
            xbmc.log("Missing user or password to authenticate")
            return 400

        if not self.last_time:
            xbmc.log("Unable to synchronise progress with Arte TV for {pid}.".format(pid=self.program_id))
            xbmc.log("Missing time to synch")
            return 400

        self.last_time = round(self.last_time)
        status = api.sync_last_viewed(
            self.plugin,
            self.settings.username, self.settings.password,
            self.program_id, self.last_time)
        xbmc.log("Synchronisation of progress {t}s with Arte TV for {pid} ended with {status}".format(t=self.last_time, pid=self.program_id, status=status))
        return status
