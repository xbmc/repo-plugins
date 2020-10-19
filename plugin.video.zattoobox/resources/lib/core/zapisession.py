# coding=utf-8

##################################
# Zappylib V1.0.7
# ZapiSession
# (c) 2014-2020 Pascal Nançoz
##################################

import os, re, base64, uuid
import urllib, urllib2
import json

class ZapiSession:
	ZAPI_URL = 'https://zattoo.com'
	ZAPI_UUID = None
	CACHE_ENABLED = False
	CACHE_FOLDER = None
	COOKIE_FILE = None
	ACCOUNT_FILE = None
	HttpHandler = None
	Username = None
	Password = None
	AccountData = None

	def __init__(self, cacheFolder):
		if cacheFolder is not None:
			self.CACHE_ENABLED = True
			self.CACHE_FOLDER = cacheFolder
			self.COOKIE_FILE = os.path.join(cacheFolder, 'session.cache')
			self.ACCOUNT_FILE = os.path.join(cacheFolder, 'account.cache')
		self.ZAPI_UUID = uuid.uuid4()
		self.HttpHandler = urllib2.build_opener()
		self.HttpHandler.addheaders = [('Content-type', 'application/x-www-form-urlencoded'),('Accept', 'application/json')]

	def init_session(self, username, password):
		self.Username = username
		self.Password = password
		return (self.CACHE_ENABLED and self.restore_session()) or self.renew_session()

	def restore_session(self):
		try:
			if os.path.isfile(self.COOKIE_FILE) and os.path.isfile(self.ACCOUNT_FILE):
				with open(self.ACCOUNT_FILE, 'r') as f:
					accountData = json.loads(base64.b64decode(f.readline()))
				if accountData['session'] is not None and accountData['success'] == True:
					self.AccountData = accountData
					with open(self.COOKIE_FILE, 'r') as f:
						self.set_cookie(base64.b64decode(f.readline()))
					return True
		except Exception:
			pass
		return False

	def extract_sessionId(self, cookieContent):
		if cookieContent is not None:
			return re.search("beaker\.session\.id\s*=\s*([^\s;]*)", cookieContent).group(1)
		return None

	def persist_accountData(self, accountData):
		with open(self.ACCOUNT_FILE, 'w') as f:
			f.write(base64.b64encode(json.dumps(accountData)))

	def persist_sessionId(self, sessionId):
		with open(self.COOKIE_FILE, 'w') as f:
			f.write(base64.b64encode(sessionId))

	def set_cookie(self, sessionId):
		self.HttpHandler.addheaders.append(('Cookie', 'beaker.session.id=' + sessionId))

	def request_url(self, url, params):
		try:
			response = self.HttpHandler.open(url, urllib.urlencode(params) if params is not None else None)
			if response is not None:
				sessionId = self.extract_sessionId(response.info().getheader('Set-Cookie'))
				if sessionId is not None:
					self.set_cookie(sessionId)
					if self.CACHE_ENABLED:
						self.persist_sessionId(sessionId)
				return response.read()
		except Exception:
			pass
		return None

	def exec_zapiCall(self, api, params, context='default'):
		url = self.ZAPI_URL + api
		content = self.request_url(url, params)
		if content is None and context != 'session' and self.renew_session():
			content = self.request_url(url, params)
		if content is None:
			return None
		try:
			resultData = json.loads(content)
			if resultData['success'] == True:
				return resultData
		except Exception:
			pass
		return None

	def fetch_appToken(self):
		try:
			handle = urllib2.urlopen(self.ZAPI_URL + '/token-46a1dfccbd4c3bdaf6182fea8f8aea3f.json')
			resultData = json.loads(handle.read())
			return resultData['session_token']
		except Exception:
			pass
		return None
		

	def announce(self):
		api = '/zapi/session/hello'
		params = {"client_app_token" : self.fetch_appToken(),
				  "uuid"    : self.ZAPI_UUID,
				  "lang"    : "en",
				  "format"  : "json"}
		resultData = self.exec_zapiCall(api, params, 'session')
		return resultData is not None

	def login(self):
		api = '/zapi/v2/account/login'
		params = {"login": self.Username, "password" : self.Password}
		accountData = self.exec_zapiCall(api, params, 'session')
		if accountData is not None:
			self.AccountData = accountData
			if self.CACHE_ENABLED:
				self.persist_accountData(accountData)
			return True
		return False

	def renew_session(self):
		return self.announce() and self.login()