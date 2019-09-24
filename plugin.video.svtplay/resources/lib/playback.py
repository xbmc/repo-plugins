from __future__ import absolute_import,unicode_literals
import time
import xbmc # pylint: disable=import-error
import xbmcgui # pylint: disable=import-error
import xbmcplugin # pylint: disable=import-error

from resources.lib import helper

class Playback:
    S_SHOW_SUBTITLES = "showsubtitles"

    def __init__(self, plugin_handle):
        self.plugin_handle = plugin_handle
    
    def play_video(self, video_url, subtitle_url):
        player = xbmc.Player()
        start_time = time.time()
        xbmcplugin.setResolvedUrl(self.plugin_handle, True, xbmcgui.ListItem(path=video_url))
        if subtitle_url:
            while not player.isPlaying() and time.time() - start_time < 10:
                time.sleep(1.)
                player.setSubtitles(subtitle_url)
            if not helper.getSetting(self.S_SHOW_SUBTITLES):
                player.showSubtitles(False)    