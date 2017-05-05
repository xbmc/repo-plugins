import xbmc
import utils

from shareddata import SharedData

class MyPlayer(xbmc.Player):

    def onPlayBackEnded(self):
        utils.log("Playback ENDED...")

        shared_data = SharedData()
        shared_data.set("playing", {})

    def onPlayBackStopped(self):
        utils.log("Playback STOPPED...")

        shared_data = SharedData()
        shared_data.set("playing", {})