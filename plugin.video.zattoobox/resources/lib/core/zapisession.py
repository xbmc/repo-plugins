# coding=utf-8

##################################
# Zappylib V0.5.2
# ZapiSession
# (c) 2014 Pascal Nançoz
##################################

import os, re, base64
import urllib, urllib2
import json

class ZapiSession:
	ZAPI_AUTH_URL = 'https://zattoo.com'
	ZAPI_URL = 'http://zattoo.com'
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
		self.HttpHandler = urllib2.build_opener()
		self.HttpHandler.addheaders = [('Content-type', 'application/x-www-form-urlencoded'),('Accept', 'application/json')]

	def init_session(self, username, password):
		self.Username = username
		self.Password = password
		return (self.CACHE_ENABLED and self.restore_session()) or self.renew_session()

	def restore_session(self):
		if os.path.isfile(self.COOKIE_FILE) and os.path.isfile(self.ACCOUNT_FILE):
			with open(self.ACCOUNT_FILE, 'r') as f:
				accountData = json.loads(base64.b64decode(f.readline()))
			if accountData['success'] == True:
				self.AccountData = accountData
				with open(self.COOKIE_FILE, 'r') as f:
					self.set_cookie(base64.b64decode(f.readline()))
				return True
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
		url = self.ZAPI_AUTH_URL + api if context == 'session' else self.ZAPI_URL + api
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
		handle = urllib2.urlopen(self.ZAPI_URL + '/')
		html = handle.read()
		return re.search("window\.appToken\s*=\s*'(.*)'", html).group(1)

	def announce(self):
		api = '/zapi/session/hello'
		params = {"client_app_token" : self.fetch_appToken(),
				  "uuid"    : "d7512e98-38a0-4f01-b820-5a5cf98141fe",
				  "lang"    : "en",
				  "format"	: "json"}
		resultData = self.exec_zapiCall(api, params, 'session')
		return resultData is not None

	def login(self):
		api = '/zapi/account/login'
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