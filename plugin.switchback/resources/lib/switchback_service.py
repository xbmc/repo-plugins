from bossanova808.utilities import *
from resources.lib.store import Store
from resources.lib.monitor import KodiEventMonitor
from resources.lib.player import KodiPlayer
import xbmc


# This is 'main'...
def run():
    Logger.start("(Service)")
    Store()
    Store.kodi_event_monitor = KodiEventMonitor(xbmc.Monitor)
    Store.kodi_player = KodiPlayer(xbmc.Player)

    while not Store.kodi_event_monitor.abortRequested():
        # Abort was requested while waiting. We should exit.
        if Store.kodi_event_monitor.waitForAbort(1):
            break
        # Otherwise, if we're playing something, record where we are up to, for later resumes
        # (Playback record is created onAVStarted in player.py, so check here that it is available)
        elif Store.current_playback and Store.current_playback.source != "pvr_live" and Store.kodi_player.isPlaying():
            Store.current_playback.resumetime = Store.kodi_player.getTime()
            xbmc.sleep(500)

    # Tidy up if the user wants us to
    if not Store.save_across_sessions:
        Logger.info('save_across_sessions is False, so deleting switchback.json')
        Store.switchback.delete_file()

    # And, we're done...
    Logger.stop("(Service)")
