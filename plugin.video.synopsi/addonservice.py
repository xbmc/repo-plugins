# python standart lib
import mythread
import traceback
import SocketServer
import thread

# application
from utilities import *
import dialog
import resources.const as const

class ServiceTCPHandler(SocketServer.StreamRequestHandler):
	def __init__(self, *args, **kwargs):
		SocketServer.StreamRequestHandler.__init__(self, *args, **kwargs)

	def handle(self):
		# self.request is the TCP socket connected to the client

		self.data = self.rfile.readline()

		# parse data
		try:
			json_data = json.loads(self.data)
		except:
			self.server._log.debug('Invalid data "%s"' % str(self.data))
			return

		try:
			# check interface version
			iface_version = json_data['iface_version']
			if iface_version != const.SERVICE_IFACE_VERSION:
				exc = { 'type': 'VersionMismatch',
						'message': 'plugin version (%s) doesn\'t match service version (%s). Please restart service' % (iface_version, const.SERVICE_IFACE_VERSION) }
				self.wfile.write(json.dumps({'exception': exc}))
				return
			
			# handle requested method
			methodName = json_data['command']
			arguments = json_data.get('arguments', {})

			method = getattr(self, methodName)
			result = method(**arguments)

			# convert non-string result to json string
			if result == None:
				result = '{}'
			elif not isinstance(result, str):
				result = json.dumps(result)

			self.server._log.debug('RESULT: ' + result)

			self.wfile.write(result)

		except Exception as e:
			# raise
			self.server._log.error('ERROR CALLING METHOD "%s": %s' % (methodName, unicode(e)))
			self.server._log.error('TRACEBACK / ' + traceback.format_exc())


# handler methods
class AddonHandler(ServiceTCPHandler):
	def get_global_recco(self, movie_type):
		return self.server.apiClient.get_global_recco(movie_type)

	def get_local_tvshows(self):
		local_tvshows = self.server.stvList.getAllByType('tvshow')
		log('local tvshows ' + dump(local_tvshows))
		return local_tvshows.values()

	def get_top_tvshows(self):
		return self.server.apiClient.get_top_tvshows()

	def get_local_recco(self, movie_type):
		return self.server.apiClient.get_local_recco(movie_type)
		
	def get_local_recco2(self, movie_type):
		""" Updates the get_local_recco function result to include stv_title_hash """
		recco = self.get_local_recco(movie_type)['titles']

		log('local recco: ' + dump(recco))
		for title in recco:
			self.server.stvList.updateTitle(title)

		return recco

	def get_unwatched_episodes(self):
		return self.server.apiClient.get_unwatched_episodes()

	def get_upcoming_episodes(self):
		return self.server.apiClient.get_upcoming_episodes()

	def get_tvshow_season(self, season_id):
		return self.server.apiClient.get_tvshow_season(season_id)

	def get_title(self, stv_id, detailProps=defaultDetailProps, castProps=defaultCastProps):
		return self.server.apiClient.get_title(stv_id, detailProps, castProps)

	def get_title_similars(self, stv_id):
		self.server.apiClient.get_title_similars(stv_id)

	def get_tvshow(self, stv_id, **kwargs):
		return self.server.apiClient.get_tvshow(stv_id, **kwargs)

	def get_local_movies(self):
		return self.server.apiClient.get_local_movies()

	def show_submenu(self, action_code, **kwargs):
		kwargs['action_code'] = action_code
		thread.start_new_thread(dialog.show_submenu, (), kwargs)
				
	def show_video_dialog(self, json_data):
		thread.start_new_thread(dialog.show_video_dialog, (json_data, ))

	def show_video_dialog_byId(self, stv_id):
		thread.start_new_thread(dialog.show_video_dialog_byId, (stv_id, ))

	def open_settings(self):
		__addon__ = get_current_addon()
		thread.start_new_thread(__addon__.openSettings, ())

	def debug_1(self):
		self.server.stvList.clear()
		episode = {
			'tvshow_id': 14335,
			'type': 'episode',
			'id': 22835,
			'name': 'Something Blue',
			'file': '/media/sdb1/blah blah.avi'
		}

		self.server.stvList.put(episode)
		self.server.stvList.add_tvshow(1, 14335)
		self.server.stvList.list()

	def debug_2(self):
		self.server.stvList.list()

	def debug_3(self):
		log(dump(self.server.stvList.byStvId))


class AddonServer(SocketServer.TCPServer):
	allow_reuse_address = True
	def __init__(self, host, port):
		tport = port
		while True:
			try:
				SocketServer.TCPServer.__init__(self, (host, tport), AddonHandler)
				break
			except:
				tport += 1
				if tport > 65500:
					raise


		addon = get_current_addon()
		addon.setSetting('ADDON_SERVICE_PORT', str(tport))

class AddonService(mythread.MyThread):
	def __init__(self, host, port, apiClient, stvList):
		super(AddonService, self).__init__()
		self.host = host		# Symbolic name meaning all available interfaces
		self.port = port		# Arbitrary non-privileged port

		self.server = AddonServer(self.host, self.port)
		self.server.apiClient = apiClient
		self.server.stvList = stvList


	def run(self):
		self._log.debug('ADDON SERVICE / Thread start')

		# Create the server
		self.server._log = self._log
		self.server.serve_forever()

		self._log.debug('ADDON SERVICE / Thread end')

	def stop(self):
		self.server.shutdown()

