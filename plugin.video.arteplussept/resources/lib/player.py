"""Events enhancing behavior of default Kodi player"""
# pylint: disable=import-error
from xbmcswift2 import xbmc
from . import api

# this player send request to Arte TV API
# to synchronise playback progress
# when playback is paused or stopped or crashed
# https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python___player_c_b.html
class Player(xbmc.Player):
    """Events enhancing behavior of default Kodi player
    used to track in Arte TV progress time and history"""

    def __init__(self, plugin, settings, program_id):
        super().__init__()
        self.plugin = plugin
        self.settings = settings
        self.program_id = program_id
        self.last_time = 0

    def is_playback(self):
        """Track progress time during playback"""
        try:
            # need to keep track of last time to avoid
            # RuntimeError: Kodi is not playing any media file
            # when calling player.getTime() in onPlayBackStopped()
            self.last_time = self.getTime()
            return self.isPlaying() and self.isPlayingVideo() and self.last_time >= 0
        # pylint: disable=broad-exception-caught
        # https://codedocs.xyz/MartijnKaijser/xbmc/group__python___player.html
        except Exception:
            return False

    def onAVStarted(self):
        # pylint: disable=invalid-name
        # method name defined by Kodi framework
        """Track progress time when user stars playing"""
        self.synch_progress()

    def onPlayBackStopped(self):
        # pylint: disable=invalid-name
        # method name defined by Kodi framework
        """Track progress time when user stops playing"""
        self.synch_progress()

    def onPlayBackEnded(self):
        # pylint: disable=invalid-name
        # method name defined by Kodi framework
        """Track progress time when kodi stops playing"""
        self.synch_progress()

    def onPlayBackError(self):
        # pylint: disable=invalid-name
        # method name defined by Kodi framework
        """Track progress time when kodi stops playing"""
        self.synch_progress()

    def onPlayBackPaused(self):
        # pylint: disable=invalid-name
        # method name defined by Kodi framework
        """Track progress time when kodi pauses playing"""
        self.synch_progress()

    def synch_progress(self):
        """Track progress/playback time and share it with Arte TV,
        so that other device with the user account can share progress and history"""
        if not self.settings.username or not self.settings.password:
            xbmc.log(f"Unable to synchronise progress with Arte TV for {self.program_id}",
                     level=xbmc.LOGWARNING)
            xbmc.log("Missing user or password to authenticate", level=xbmc.LOGWARNING)
            return 400

        if not self.last_time:
            xbmc.log(f"Unable to synchronise progress with Arte TV for {self.program_id}.",
                     level=xbmc.LOGWARNING)
            xbmc.log("Missing time to synch", level=xbmc.LOGWARNING)
            return 400

        self.last_time = round(self.last_time)
        status = api.sync_last_viewed(
            self.plugin,
            self.settings.username, self.settings.password,
            self.program_id, self.last_time)
        xbmc.log(f"Synchronisation of progress {self.last_time}s with Arte TV " +
                 f"for {self.program_id} ended with {status}",
                 level=xbmc.LOGINFO)
        return status
