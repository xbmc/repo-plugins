
# xbmc
import xbmcgui

# application
from apiclient import *
from utilities import *
import threading
import top


class LoginState:
	Notify = 1
	AddonDialog = 2

class AppApiClient(ApiClient):
	def __init__(self, base_url, key, secret, username, password, device_id, originReqHost=None, debugLvl=logging.INFO, accessTokenTimeout=10, rel_api_url='api/public/1.0/', lsa=LoginState.Notify):
		super(AppApiClient, self).__init__(base_url, key, secret, username, password, device_id, originReqHost, debugLvl, accessTokenTimeout, rel_api_url)
		self._lock_access_token = threading.Lock()
		self._rejected_to_correct = False
		self.login_state_announce = lsa

	def reloadUserPass(self):
		__addon__ = get_current_addon()
		changed = False

		if self.username != __addon__.getSetting('USER'):
			self.username = __addon__.getSetting('USER')
			changed = True

		if self.password != __addon__.getSetting('PASS'):
			self.password = __addon__.getSetting('PASS')
			changed = True

		return changed

	def clearAccessToken(self):
		self.accessToken = None
		self.accessTokenSessionStart = None

	def checkUserPass(self):
		if self.reloadUserPass():
			self.clearAccessToken()
			return True

		return False

	def isAuthenticated(self):
		" Returns true if user is authenticated. This method adds to its parent method a check if user credentials have changed "
		self.checkUserPass()
		return ApiClient.isAuthenticated(self)

	def getAccessToken(self):
		if not self._lock_access_token.acquire():
			self._log.debug('getAccessToken lock NOT acquired')
			return False
		else:
			self._log.debug(threading.current_thread().name + ' getAccessToken LOCK ACQUIRED')

		finished = False
		while not finished:
			try:
				# check to clear tokens if user credentials changed
				self.checkUserPass()

				# try to log in
				ApiClient.getAccessToken(self)
				if self.login_state_announce==LoginState.Notify:
					notification('Logged in as %s' % self.username)

			# in failure, ask for new login/pass and repeat if dialog was not canceled
			except AuthenticationError:
				if self.login_state_announce==LoginState.Notify:
					if self._rejected_to_correct:
						notification('Authentication failed. Correct your login/password in plugin settings')
						res = False
						finished = True
					else:
						if not dialog_check_login_correct():
							self._rejected_to_correct = True
							res = False
							finished = True

				elif self.login_state_announce==LoginState.AddonDialog:
					raise

			except Exception as e:
				finished = True
				self._log.debug('Unknown exception')
				self._log.debug(unicode(e))
				res = False
			else:
				finished = True
				self._log.debug('Login success')
				res = True

		self._log.debug(threading.current_thread().name + ' getAccessToken LOCK RELEASE')
		self._lock_access_token.release()
		return res

	def setRefreshToken(self, token):
		ADDON = get_current_addon()
		ADDON.setSetting('REFTOKEN', token)		

	# convienent functions
	def get_unwatched_episodes(self):
		episodes = self.unwatchedEpisodes()

		# self._log.debug('unwatched episodes')
		# for title in episodes['lineup']:
		#	 self._log.debug(title['name'])

		result = episodes['lineup']
		return result

	def get_upcoming_episodes(self):
		episodes = self.unwatchedEpisodes()

		# self._log.debug('upcoming episodes')
		# for title in episodes['upcoming']:
		#	 self._log.debug(title['name'])

		result = episodes['upcoming']
		return result

	def get_global_recco(self, movie_type):
		resRecco = self.profileRecco(movie_type, False, reccoDefaulLimit, reccoDefaultProps)

		# log('global recco for ' + movie_type)
		# for title in resRecco['titles']:
		#	log(title['name'])

		return resRecco.get('titles', [])

	def get_top_tvshows(self):
		episodes = self.unwatchedEpisodes()

		# log('top tvshows')
		# for title in episodes['top']:
		#	 log(title['name'])

		result = episodes['top'][0:29]
		return result


	def get_local_recco(self, movie_type):
		resRecco = self.profileRecco(movie_type, True, reccoDefaulLimit, reccoDefaultProps)

		return resRecco

	def get_local_recco2(self, movie_type):
		""" Updates the get_local_recco function result to include stv_title_hash """
		recco = self.get_local_recco(movie_type)['titles']

		for title in recco:
			top.stvList.updateTitle(title)

		return recco

	def get_tvshow_season(self, season_id):
		season = self.season(season_id)
		
		return season

	def get_title(self, stv_id, detailProps=defaultDetailProps, castProps=defaultCastProps):
		return self.title(stv_id, detailProps, castProps)

	def get_title_similars(self, stv_id):
		self.titleSimilar(stv_id)

	def get_tvshow(self, stv_id, **kwargs):
		return self.tvshow(stv_id, **kwargs)

	def get_local_movies(self):
		props = reccoDefaultProps
		library = self.library(title_property=props)['titles']
		
		# pass only movies through filter
		def filter_movies(item):
			return item['type']=='movie'

		library = filter(filter_movies, library)

		for title in library:
			top.stvList.updateTitle(title)

		return library

	def get_item_list(self, **kwargs):
		action_code = kwargs['action_code']

		log('get_item_list:' + str(action_code))
		
		if action_code==ActionCode.MovieRecco:
			return self.get_global_recco('movie')

		elif action_code==ActionCode.LocalMovieRecco:
			return self.get_local_recco2('movie')

		elif action_code==ActionCode.LocalMovies:
			return self.get_local_movies()

		elif action_code==ActionCode.TVShows:
			return self.get_top_tvshows()

		elif action_code==ActionCode.LocalTVShows:
			return top.stvList.get_local_tvshows()

		elif action_code==ActionCode.UnwatchedEpisodes:
			return self.get_unwatched_episodes()

		elif action_code==ActionCode.UpcomingEpisodes:
			return self.get_upcoming_episodes()

		elif action_code==ActionCode.TVShowEpisodes:
			return self.get_tvshow_season(kwargs['stv_id'])
		

	def titleIdentify(self, props=defaultIdentifyProps, **data):
		data['file_name'] = rel_path(data['file_name'])
		return ApiClient.titleIdentify(self, props, **data)

	def titleWatched(self, titleId, **data):
		data['software_info'] = software_info()
		return ApiClient.titleWatched(self, titleId, **data)

