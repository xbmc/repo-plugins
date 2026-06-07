import xbmc
from xbmcaddon import Addon

from lib.history import mark_as_watched

class Player(xbmc.Player):
	def __init__(self):
		super(xbmc.Player, self).__init__()

		self.video_id = None

	def watchHistoryEnabled(self):
		return Addon().getSettingBool('watch_history_enable') and len(Addon().getSettingString('watch_history_playlist')) > 0

	def markAsWatched(self):
		if self.watchHistoryEnabled() and self.video_id is not None:
			mark_as_watched(self.video_id)
			self.video_id = None

	def onPlayBackStarted(self):
		video_id = self.getPlayingItem().getProperty('piped_video_id')
		self.video_id = video_id if isinstance(video_id, str) and len(video_id) > 5 else None

		while self.video_id is not None:
			try:
				time_remaining: float = self.getTotalTime() - self.getTime()
				if time_remaining > 0. and time_remaining < 5.: self.markAsWatched()
			except:
				pass

			xbmc.sleep(500)

	def onPlayBackEnded(self):
		self.markAsWatched()

	def onPlayBackStopped(self):
		self.video_id = None

	def onPlayBackSeek(self, time, seekOffset):
		try:
			if time + seekOffset > (self.getTotalTime() - 5) * 1000:
				self.markAsWatched()
		except:
			pass
