import xbmc, xbmcgui, xbmcaddon
from mythread import MyThread
import time
import socket
import json
import re
import traceback
from utilities import *
from cache import *


ABORT_REQUESTED = False


class RPCListener(MyThread):
	def __init__(self, cache, scrobbler):
		super(RPCListener, self).__init__()

		self.cache = cache
		self.scrobbler = scrobbler
		self.sock = socket.socket()
		self.sock.settimeout(5)
		self.connected = False
		self._stop = False
		sleepTime = 100
		t = time.time()
		port = get_api_port()
		while sleepTime<500 and (not self.connected or ABORT_REQUESTED or xbmc.abortRequested):
			try:
				self.sock.connect(("localhost", port))
			except Exception, exc:
				log('%0.2f %s' % (time.time() - t, str(exc)))
				xbmc.sleep(int(sleepTime))
				sleepTime *= 1.5
			else:
				self._log.info('Connected to %d' % port)
				self.connected = True

		self.sock.setblocking(True)

	def process(self, data):
		pass

	def run(self):
		global ABORT_REQUESTED

		if not self.connected:
			self._log.error('RPC Listener cannot run, there is not connection to xbmc')
			return False

		while not self._stop:
			data = self.sock.recv(8192)
			data = data.replace('}{', '},{')
			datapack='[%s]' % data
			# self._log.debug('SynopsiTV: {0}'.format(str(data)))
			try:
				data_json = json.loads(datapack)
			except ValueError, e:
				self._log.error('RPC ERROR:' + unicode(e))
				self._log.error('RPC ERROR DATA:' + unicode(data))
				continue

			for request in data_json:
				method = request.get("method")

				if method == "System.OnQuit":
					self._stop = True
					ABORT_REQUESTED = True
					break
				else:
					self.process(request)

		self.sock.close()
		self._log.info('Library thread end')

	def process(self, data):
		methodName = data['method'].replace('.', '_')
		method = getattr(self, methodName, None)
		if method == None:
			self._log.warn('Unknown method: ' + methodName)
			return

		self._log.debug(str(data))

		#   Try to call that method
		try:
			method(data)
		except:
			self._log.error('Error in method "' + methodName + '"')
			self._log.error(traceback.format_exc())

		#   http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v4


class RPCListenerHandler(RPCListener):
	"""
	RPCListenerHandler defines event handler methods that are autotically called from parent class's RPCListener
	"""
	def __init__(self, cache, scrobbler):
		super(RPCListenerHandler, self).__init__(cache, scrobbler)

	def _xbmc_time2sec(self, time):
		return time["hours"] * 3600 + time["minutes"] * 60 + time["seconds"] + time["milliseconds"] / 1000

	#   NOT USED NOW
	def playerEvent(self, data):
		self._log.debug(dump(data))

	def VideoLibrary_OnUpdate(self, data):
		i = data['params']['data']['item']
		self.cache.addorupdate(i['type'], i['id'])

	def VideoLibrary_OnRemove(self, data):
		d = data['params']['data']
		self.cache.remove(d['type'], d['id'])

	def Player_OnPlay(self, data):
		self.playerEvent(data)

	def Player_OnStop(self, data):
		self.playerEvent(data)

	def Player_OnSeek(self, data):
		position = self._xbmc_time2sec(data['params']['data']['player']['time'])
		self.scrobbler.player.playerEventSeek(position)

	def Player_OnPause(self, data):
		self.playerEvent(data)
		pass

	def Player_OnResume(self, data):
		self.playerEvent(data)
		pass

	def GUI_OnScreenSaverActivated(self, data):
		self.playerEvent(data)
		pass

	def GUI_OnScreenSaverDeactivated(self, data):
		self.playerEvent(data)
		pass

