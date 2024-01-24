import xbmc

from lib.services.httpserver import HttpService
from lib.services.scheduler import Scheduler
from lib.services.player import Player

class Service(xbmc.Monitor):
	def __init__(self):
		httpservice = HttpService()
		scheduler = Scheduler()
		httpservice.daemon = True
		scheduler.daemon = True
		player = Player()

		while not self.waitForAbort(5):
			try:
				if not httpservice.is_alive(): httpservice.start()
				if not scheduler.is_alive(): scheduler.start()
			except:
				pass

		scheduler.stop()
		httpservice.stop()