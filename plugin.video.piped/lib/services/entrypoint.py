from threading import Thread
import xbmc

from lib.services.httpserver import HttpService
from lib.services.scheduler import Scheduler
from lib.services.player import Player

class Service(xbmc.Monitor):
	def __init__(self):
		httpservice = Thread(target=HttpService)
		scheduler = Scheduler()
		httpservice.daemon = True
		scheduler.daemon = True
		player = Player()
		player.isPlaying()

		while not self.abortRequested():
			if self.waitForAbort(5):
				while scheduler.is_alive():
					scheduler.stop()
					xbmc.sleep(200)
				break

			try:
				if not httpservice.is_alive(): httpservice.start()
				if not scheduler.is_alive(): scheduler.start()
			except:
				pass