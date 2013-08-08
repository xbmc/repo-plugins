# xbmc
import xbmc, xbmcgui, xbmcaddon

# python standart lib
import logging
import json
import sys
import datetime
from base64 import b64encode
from urllib import urlencode
from urllib2 import Request, urlopen, HTTPError, URLError
import httplib

# application
from utilities import *
import loggable
import resources.const as const


RATING_CODE = {
	1: 'like',
	2: 'neutral',
	3: 'dislike'
}

# api request title properties
commonTitleProps = ['id', 'cover_full', 'cover_large', 'cover_medium', 'cover_small', 'cover_thumbnail', 'date', 'genres', 'name', 'plot', 'released', 'trailer', 'type', 'year', 'url', 'directors', 'writers', 'runtime']
defaultIdentifyProps = commonTitleProps + ['tvshow_id']
watchableTitleProps = commonTitleProps + ['watched']
defaultTVShowProps = commonTitleProps + ['seasons']
smallListProps = ['id', 'cover_medium', 'name', 'watched', 'type']
defaultEpisodeProps = smallListProps + ['season_number', 'episode_number', 'cover_large', 'tvshow_id', 'tvshow_name']
allSeasonProps = ['id', 'cover_full', 'cover_large', 'cover_medium', 'cover_small', 'cover_thumbnail', 'season_number', 'episodes_count', 'watched_count']
defaultSeasonProps = ['id', 'cover_medium', 'season_number', 'episodes_count', 'watched_count']
defaultSeasonProps2 = ['id', 'episodes']
defaultSearchProps = defaultEpisodeProps + ['year', 'directors', 'cast']

class NotConnectedException(Exception):
	pass

class AuthenticationError(Exception):
	pass

class ApiCallError(Exception):
	pass

class ApiClient(loggable.Loggable):
	_instance = None
	def __init__(self, base_url, key, secret, username, password, device_id, originReqHost=None, debugLvl=logging.INFO, accessTokenTimeout=10, rel_api_url='api/public/1.0/'):
		super(ApiClient, self).__init__()
		self.baseUrl = base_url
		self.key = key
		self.secret = secret
		self.username = username
		self.password = password
		self.accessToken = None
		self.refreshToken = None
		self.apiUrl = self.baseUrl + rel_api_url
		self.originReqHost = originReqHost
		self.device_id = device_id
	
		self._log.setLevel(debugLvl)
		
		if len(self._log.handlers)==0:
			self._log.addHandler(logging.StreamHandler(sys.stdout))

		self.accessTokenTimeout = accessTokenTimeout		# [minutes] how long is stv accessToken valid ?
		self.accessTokenSessionStart = None
		self.failedRequest = []

	@classmethod
	def getDefaultClient(cls):
		if ApiClient._instance:
			return ApiClient._instance

		__addon__  = get_current_addon()

		iuid = get_install_id()

		# get or generate install-unique ID
		ApiClient._instance = cls(
			const.BASE_URL,
			const.KEY,
			const.SECRET,
			__addon__.getSetting('USER'),
			__addon__.getSetting('PASS'),
			iuid,
			debugLvl=int(addon_getSetting('NON_DEBUG_LOGLEVEL')),
			rel_api_url=const.REL_API_URL
		)

		return ApiClient._instance

	def setUserPass(self, username, password):
		self.username = username
		self.password = password

	def queueRequest(self, req):
		self.failedRequest.append(req)

	def tryEmptyQueue(self):
		# assume connected
		connected = True
		while connected and len(self.failedRequest) > 0:
			try:
				response = self.doRequest(self.failedRequest[0], False)
				# on success, pop the request out of queue
				self.pop(0)
			except:
				# if network failure
				connected = False

		return connected

	def doRequest(self, req, cacheable=True):
		#~ if not self.isAuthenticated():
			#~ access = self.getAccessToken()
			#~ if not access:
				#~ self._log.error('Could not get the auth token')
				#~ return False

		# put the cacheable request into queue
		if cacheable:
			self.queueRequest(req)
			# try to empty queue, if not success, return back
			if not self.tryEmptyQueue():
				raise NotConnectedException()
		else:
			response = urlopen(req)
			response_json = json.loads(response.readline())
			return response_json

	def getAccessToken(self):
		data = {
			'grant_type': 'password',
			'client_id': self.key,
			'client_secret': self.secret,
			'username': self.username,
			'password': self.password
		}

		authHeaders = {'AUTHORIZATION': 'BASIC %s' % b64encode("%s:%s" % (self.key, self.secret))}

		#~ self._log.debug('apiclient getaccesstoken u:%s p:%s' % (self.username, self.password))
		#~ self._log.debug('apiclient getaccesstoken %s' % str(data))

		# get token
		try:

			req = Request(
					self.baseUrl + 'oauth2/token/',
					data=urlencode(data),
					headers=authHeaders,
					origin_req_host=self.originReqHost)

			# self._log.debug('request REQ HOST:' + str(req.get_origin_req_host()))
			# self._log.debug('request URL:' + str(req.get_full_url()))
			# self._log.debug('request HEADERS:' + str(req.headers.items()))
			# self._log.debug('request DATA:' + str(req.get_data()))

			response = urlopen(req)

			# self._log.debug('request RESPONSE:' + str(response))
			response_json = json.loads(response.readline())

		except HTTPError as e:
			try:
				response = json.loads(e.read())
			
				if "User authentication failed" in response['error_description']:
					self._log.info('%d %s' % (e.code, response['error_description']))
				else:
					self._log.error('%d %s' % (e.code, e))
					self._log.error(e.read())
			except:
				self._log.error('HTTPError: %d\nReceived:\n"%s"' % (e.code, e.read()))
				

			raise AuthenticationError()

		except URLError as e:
			self._log.error(unicode(e))
			self._log.error(e.reason)
			raise AuthenticationError()

		except Exception as e:
		 	self._log.error('OTHER EXCEPTION:' + unicode(e))
			raise AuthenticationError()


		self.updateAccessTokenTimeout()
		self.accessToken = response_json['access_token']
		self.setRefreshToken(response_json['refresh_token'])
		self._log.debug('new access token: ' + self.accessToken)
		return True

	def setRefreshToken(self, token):
		self.refreshToken = token
		
	def updateAccessTokenTimeout(self):
		self.accessTokenSessionStart = datetime.datetime.now()

	def isAuthenticated(self):
		# if we have some acess token and if access token session didn't timeout
		return self.accessToken != None and self.accessTokenSessionStart + datetime.timedelta(minutes=self.accessTokenTimeout) > datetime.datetime.now()

	def _unicode_input(self, data):
		safe_data = {}
		for k, v in data.iteritems():
			if isinstance(v, unicode):
				safe_data[k] = unicode(v).encode('utf-8')
			elif isinstance(v, dict):
				safe_data[k] = self._unicode_input(v)
			else:
				safe_data[k] = v

		return safe_data


	def execute(self, requestData, cacheable=True):
		if requestData.get('_noauth'):
			return self.execute_noauth(requestData, cacheable)
		else:
			return self.execute_auth(requestData, cacheable)


	def execute_auth(self, requestData, cacheable=True):
		if not self.isAuthenticated():
			self.getAccessToken()

		return self.execute_noauth(requestData, cacheable=True)


	def execute_noauth(self, requestData, cacheable=True):
		self._log.debug('-' * 20)
		
		url = self.apiUrl + requestData['methodPath']
		method = requestData['method']
		data = None

		if not requestData.has_key('data'):
			requestData['data'] = {}
		else:
			requestData['data'] = self._unicode_input(requestData['data'])

		authHeaders = {'AUTHORIZATION': 'BASIC %s' % b64encode("%s:%s" % (self.key, self.secret))} 
	
		# append data to post
		if method == 'post':
			post = requestData['data']
			post['bearer_token'] = self.accessToken
			data = urlencode(post)

		# append data to get
		if method == 'get':
			get = requestData['data']
			get['bearer_token'] = self.accessToken
			url += '?' + urlencode(get)
			data = None

		if 'post' in locals():
			self._log.debug('post:' + str(post))
		if 'get' in locals():
			self._log.debug('URL:' + url)
			self._log.debug('get:' + str(get))
		if data:
			self._log.debug('data:' + str(data))

		try:
			response_json = self.doRequest(
				Request(
					url,
					data = data,
					headers = authHeaders,
					origin_req_host = self.originReqHost
				),
				False
			)

			if response_json.get('status') == 'error':
				raise ApiCallError('ApiClient response: ' + json.dumps(response_json.get('errors')))

			self.updateAccessTokenTimeout()

		except HTTPError as e:
			response_json_str = e.read()
			try:
				response_json = json.loads(response_json_str)
			except:
				response_json = response_json_str
				
			self._log.error('APICLIENT HTTP %s :\nURL:%s\nERROR STRING: %s\nSERVER RESPONSE: "%s"' % (e.code, url, unicode(e), response_json))

		except URLError as e:
			self._log.error('APICLIENT:' + url)
			self._log.error('APICLIENT:' + unicode(e))
			self._log.error('APICLIENT:' + unicode(e.reason))
			response_json = {}

		return response_json


#	api methods
#	list independent
	def titleWatched(self, titleId, **data):
		# normalize ratings
		if data.has_key('rating') and isinstance(data['rating'], (int, long)):
			data['rating'] = RATING_CODE[data['rating']]

		data['device_id'] = self.device_id
		req = {
			'methodPath': 'title/%d/watched/' % titleId,
			'method': 'post',
			'data': data
		}
				
		self.execute(req)

	def titleIdentify(self, props=defaultIdentifyProps, **data):
		""" Try to match synopsi title by various data """
		# filter-out empty data
		data = dict((k, v) for k, v in data.iteritems() if v)

		data['device_id'] = self.device_id
		data['title_property[]'] = ','.join(props)
		req = {
			'methodPath': 'title/identify/',
			'method': 'get',
			'data': data
		}

		return self.execute(req)

	def titleSimilar(self, titleId, props=smallListProps):
		req = {
			'methodPath': 'title/%d/similar/' % titleId,
			'method': 'get',
			'data': {
				'title_property[]': ','.join(props)
			}
		}

		return self.execute(req)

	def title_identify_correct(self, titleId, stv_title_hash, stv_subtitle_hash=None, replace_library_item='true'):		
		data = {
			'title_id': titleId,
			'stv_title_hash': stv_title_hash,
			'device_id': self.device_id,
			'replace_library_item': replace_library_item
		}

		if stv_subtitle_hash:
			data['stv_subtitle_hash'] = stv_subtitle_hash

		req = {
			'methodPath': 'title/identify/mark_pair/',
			'method': 'post',
			'data': data
		}

		return self.execute(req)

# conditionally dependent
	def profileRecco(self, atype, local=False, limit=None, props=watchableTitleProps):
		req = {
			'methodPath': 'profile/recco/',
			'method': 'get',
			'data': {
				'type': atype,
				'title_property[]': ','.join(props)
			}
		}

		if local:
			req['data']['device_id'] = self.device_id

		if limit:
			req['data']['limit'] = limit

		return self.execute(req)

# library dependent
	def libraryTitleAdd(self, titleId):
		req = {
			'methodPath': 'library/title/%d/add/' % titleId,
			'method': 'post',
			'data':
			{
				'device_id': self.device_id
			}
		}

		return self.execute(req)

	def libraryTitleRemove(self, titleId):
		req = {
			'methodPath': 'library/title/%d/' % titleId,
			'method': 'get',
			'data': {
				'_method': 'delete',
				'device_id': self.device_id
			}
		}

		return self.execute(req)

	def library(self, title_property=None):
		req = {
			'methodPath': 'library/%s/' % self.device_id,
			'method': 'get',
			'data': {
			}
		}

		if title_property:
			req['data']['title_property[]'] = ','.join(title_property)

		return self.execute(req)


	def title(self, titleId, props=watchableTitleProps, cast_props=None, cast_limit=None):
		" Get title from library "

		if cast_props:
			props += ['cast']

		req = {
			'methodPath': 'title/%d/' % titleId,
			'method': 'get',
			'data': {
				'title_property[]': ','.join(props)
			}
		}

		if 'cast' in props:
			if cast_limit:
				req['data']['cast_limit'] = cast_limit
			if cast_props:
				req['data']['cast_property[]'] = ','.join(cast_props)

		return self.execute(req)

	def tvshow(self, titleId, props=defaultTVShowProps, cast_props=None, cast_limit=None, season_props=defaultSeasonProps, season_limit=None):
		" Get title from library "

		if cast_props:
			props += ['cast']

		req = {
			'methodPath': 'tvshow/%d/' % titleId,
			'method': 'get',
			'data': {
				'title_property[]': ','.join(props),
				'season_property[]': ','.join(season_props)
			}
		}

		if 'cast' in props:
			if cast_limit:
				req['data']['cast_limit'] = cast_limit
			if cast_props:
				req['data']['cast_property[]'] = ','.join(cast_props)

		if 'seasons' in props:
			if season_limit:
				req['data']['season_limit'] = season_limit
			if season_props:
				req['data']['season_property[]'] = ','.join(season_props)

		return self.execute(req)

	def season(self, tvshow_id, props=defaultSeasonProps2, episode_props=defaultEpisodeProps):
		req = {
			'methodPath': 'season/%d/' % int(tvshow_id),
			'method': 'get',
			'data': {
				'title_property[]': ','.join(props),
				'episode_property[]': ','.join(episode_props)
			}
		}

		return self.execute(req)

	def unwatchedEpisodes(self, props=defaultEpisodeProps):
		req = {
			'methodPath': 'profile/unwatched_episodes/',
			'method': 'get',
			'data': {
				'title_property[]': ','.join(props)
			}
		}

		return self.execute(req)

	def search(self, term, limit=None, props=defaultSearchProps, props_cast=defaultCastProps):
		req = {
			'methodPath': 'search/',
			'method': 'get',
			'data': {
				'name': term,
				'title_property[]': ','.join(props)
			}
		}

		if limit:
			req['data']['limit'] = limit

		if 'cast' in props:
			req['data']['cast_property[]'] = ','.join(props_cast)

		return self.execute(req)

	def profileCreate(self, realname, email):
		req = {
			'_noauth': True,
			'methodPath': 'profile/create',
			'method': 'post',
			'data': {
				'realname': realname,
				'email': email,
			}
		}

		return self.execute(req)
		
		
