# xbmc
import xbmc, xbmcgui, xbmcaddon

# python standart lib
import json

# application
from utilities import *
from loggable import Loggable

defaultProperties = ['file', 'imdbnumber', "lastplayed", "playcount", "runtime"]

class xbmcRPCclient(Loggable):

	def __init__(self, logLevel = 0):
		super(xbmcRPCclient, self).__init__()
		self.__logLevel = logLevel

	def execute(self, methodName, params):
		req = {
			'params': params,
			'jsonrpc': '2.0',
			'method': methodName,
			'id': 1
		}


		self._log.debug('xbmc RPC request: ' + dump(req))

		response = xbmc.executeJSONRPC(json.dumps(req))

		json_response = json.loads(response)


		self._log.debug('xbmc RPC response: ' + dump(json_response))

		if json_response.has_key('error') and json_response['error']:
			self._log.debug('xbmc RPC ERROR: ' + json_response['error']['message'])
			self._log.debug('xbmc RPC request: ' + dump(req))
			self._log.debug('xbmc RPC response: ' + dump(json_response))
			raise Exception(json_response['error']['message'])

		return json_response['result']

	def get_movies(self, start=None, end=None):
		"""
		Get movies from xbmc library. Start is the first in list and end is the last.
		"""

		data = {
			'properties': defaultProperties
		}

		if start or end:
			data['limits'] = {}
			if start:
				data['limits']['start'] = start
			if end:
				data['limits']['end'] = end


		response = self.execute('VideoLibrary.GetMovies', data)

		return response

	def get_all_tvshows(self):
		"""
		Get movies from xbmc library. Start is the first in list and end is the last.
		"""
		properties = ['file', 'imdbnumber', "lastplayed", "playcount", "episode", "thumbnail"]

		response = self.execute(
			'VideoLibrary.GetTVShows',
			{
				'properties': properties
			}
		)

		return response

	def get_episodes(self, twshow_id, season=-1):
		"""
		Get episodes from xbmc library.
		"""
		properties = ['file', "lastplayed", "playcount", "season", "episode"]
		if season == -1:
			params = {
				'properties': properties,
				'tvshowid': twshow_id
			}
		else:
			params = {
				'properties': properties,
				'tvshowid': twshow_id,
				'season': season
			}

		response = self.execute(
			'VideoLibrary.GetEpisodes',
			params
		)

		return response

	def get_movie_details(self, movie_id, all_prop=False):
		"""
		Get dict of movie_id details.
		"""
		if all_prop:
			properties = [
				"title",
				"genre",
				"year",
				"rating",
				"director",
				"trailer",
				"tagline",
				"plot",
				"plotoutline",
				"originaltitle",
				"lastplayed",
				"playcount",
				"writer",
				"studio",
				"mpaa",
				"cast",
				"country",
				"imdbnumber",
				"premiered",
				"productioncode",
				"runtime",
				# "set",
				"showlink",
				"streamdetails",
				# "top250",
				"votes",
				# "fanart",
				# "thumbnail",
				"file",
				"sorttitle",
				"resume",
				# "setid
			]
		else:
			properties = defaultProperties

		response = self.execute(
			'VideoLibrary.GetMovieDetails',
			{
				'properties': properties,
				'movieid': movie_id  # s 1 e 2 writes 2
			}
		)

		return response['moviedetails']

	def get_tvshow_details(self, movie_id):
		"""
		Get dict of movie_id details.
		"""
		properties = defaultProperties
		#	"title",
		#   "genre",
		#   "year",
		#   "rating",
		#   "plot",
		#   "studio",
		#   "mpaa",
		#   "cast",
		#   "playcount",
		#   "episode",
		#   "imdbnumber",
		#   "premiered",
		#   "votes",
		#   "lastplayed",
		#   "fanart",
		#   "thumbnail",
		#   "file",
		#   "originaltitle",
		#   "sorttitle",
		#   "episodeguide"

		response = self.execute(
			'VideoLibrary.GetTVShowDetails',
			{
				'properties': properties,
				'tvshowid': movie_id
			}
		)

		return response

	def get_episode_details(self, movie_id):
		"""
		Get dict of movie_id details.
		"""
		properties = ['file', "lastplayed", "playcount", "season", "episode", "tvshowid"]

		response = self.execute(
			'VideoLibrary.GetEpisodeDetails',
			{
				'properties': properties,
				'episodeid': movie_id
			}
		)

		return response['episodedetails']

	def get_details(self, atype, aid, all_prop=False):
		if atype == "movie":
			movie = self.get_movie_details(aid, all_prop)
		elif atype == "episode":
			movie = self.get_episode_details(aid)
		elif atype == "tvshow":
			movie = self.get_tvshow_details(aid)
		else:
			raise Exception('Unknow video type: %s' % atype)

		return movie

	def GetInfoLabels(self):
		"""
		"""

		response = self.execute(
			'XBMC.GetInfoLabels',
			{
				'properties' : [ 'System.CpuFrequency', 'System.KernelVersion','System.FriendlyName','System.BuildDate','System.BuildVersion' ]
			}
		)

		return response


# init local variables
xbmc_rpc = xbmcRPCclient()
