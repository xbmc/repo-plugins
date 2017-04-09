from xbmcswift2 import xbmc
import sys

class MlbPlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        xbmc.Player.__init__(self)
        self.mlb_playlist = kwargs['mlb_playlist']
        self.curr_playing = ''

    def onPlayBackStopped(self):
        self.mlb_playlist.clear()
        self.stop()
        xbmc.executebuiltin('StopScript(%d)' % int(sys.argv[1]))

    def play_video(self, stream):
        if not stream:
            return
        # stream is a url with unique token each time..check root
        # of url for changes
        game_identifier = stream.split('.m3u8')[0]
        if game_identifier == self.curr_playing.split('.m3u8')[0]:
            return
        self.mlb_playlist.add(stream)
        if not self.isPlayingVideo():
            self.play(self.mlb_playlist)
        else:
            self.playnext()
        self.curr_playing = stream
