import json
from threading import Thread, Event
from requests import get
from xbmcaddon import Addon
from xbmcvfs import translatePath

from lib.utils import get_component

class Scheduler(Thread):
	def __init__(self):
		super(Scheduler, self).__init__()
		self._stop_event = Event()

	def run(self):
		while not self._stop_event.is_set():
			if Addon().getSettingBool('watch_history_enable') and len(Addon().getSettingString('watch_history_playlist')) > 0:
				history: list = list()
				history_playlist: list = get(f'{Addon().getSettingString("instance")}/playlists/{Addon().getSettingString("watch_history_playlist")}').json()['relatedStreams']
		
				for watched in history_playlist:
					history.append(get_component(watched['url'])['params']['v'])
		
				history.reverse()
		
				if len(history) > 0:
					with open(f'{translatePath(Addon().getAddonInfo("profile"))}/watch_history.json', 'w+') as f:
						json.dump(history, f)
		
			self._stop_event.wait(Addon().getSettingInt('watch_history_refresh') * 60_000)

	def stop(self, timeout=1):
		self._stop_event.set()
		self.join(timeout)