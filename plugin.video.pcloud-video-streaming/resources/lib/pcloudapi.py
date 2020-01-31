import xbmc
import xbmcaddon
import json
import hashlib
from numbers import Number 	# to check whether a certain variable is numeric
from .loginfailedexception import LoginFailedException
import os
import operator # it's for use sort with operator
import sys
import re
from datetime import date
if sys.version_info.major >= 3:
	# Python 3 stuff
	from urllib.parse import urlparse, urlencode
	from urllib.request import urlopen, Request, build_opener
	from urllib.error import HTTPError
else:
	# Python 2 stuff
	from urlparse import urlparse
	from urllib import urlencode
	from urllib2 import urlopen, Request, HTTPError, build_opener

class PCloudApi:

	def __init__(self):
		# auth typically comes from xbmcaddon.Addon() followed by myAddon.getSetting("auth")
		self.auth = None
		self.PCLOUD_BASE_URL = 'https://api.pcloud.com/'
		self.TOKEN_EXPIRATION_SECONDS = 100 * 86400 # 100 days
		self.HttpHandler = build_opener()
		self.HttpHandler.addheaders = [('Accept', 'application/json')]

	def CheckIfAuthPresent(self):
		if self.auth is None or self.auth == "":
			raise Exception ("Auth not present. Call PerformLogon() or SetAuth() first.")

	def GetErrorMessage(self, errorCode):
		if errorCode == 1000:
			errorText = "Log in required."
		elif errorCode == 1002:
			errorText = "No full path or folderid provided."
		elif errorCode == 1004:
			errorText = "No fileid or path provided"
		elif errorCode == 1076:
			errorText = "Please provide 'tokenid'"
		elif errorCode == 2000:
			errorText = "Log in failed"
		elif errorCode == 2002:
			errorText = "A component of parent directory does not exist"
		elif errorCode == 2003:
			errorText = "Access denied. You do not have permissions to preform this operation"
		elif errorCode == 2005:
			errorText = "Directory does not exist"
		elif errorCode == 2009:
			errorText = "File not found"
		elif errorCode == 2010:
			errorText = "Invalid path."
		elif errorCode == 2102:
			errorText = "Provided 'tokenid' not found."
		elif errorCode == 4000:
			errorText = "Too many login tries from this IP address."
		elif errorCode == 5000:
			errorText = "Internal error. Try again later."
		else:
			errorText = "Unknown error"
		return errorText

	def SetAuth(self, auth):
		self.auth = auth

	def ExecuteRequest(self, api, data = None):
		"""
		Private method to execute a JSON POST request and return its results raw.
		"""
		url = '{0}{1}'.format(self.PCLOUD_BASE_URL, api)
		xbmc.log ('Calling {0}...'.format(url))
		requestData = {}
		requestHeaders = {}
		method = 'GET'
		if data is not None:
			requestData = data.encode('utf-8')
			method = 'POST'
		if sys.version_info.major >= 3:
			# Python 3 stuff
			httpRequest = Request(
				url,
				data=requestData,
				method=method)
		else:
			# Python 2 stuff. Request for Python 2 (at least on Android) does not
			# support the "method" keyword.
			httpRequest = Request(
				url,
				data=requestData)			
		response = self.HttpHandler.open(httpRequest)
		responseStr = response.read().decode('utf-8')
		self.HttpHandler.close()
		return json.loads(responseStr)

	def PerformLogon(self, username, password):
		""" This must be the first API that gets called after the constructor
			Returns auth
		"""
		api = "getdigest"
		response = self.ExecuteRequest(api)
		if response["result"] != 0:
			errorMessage = self.GetErrorMessage(response["result"])
			raise Exception("Error calling getdigest: " + errorMessage)
		sha1 = hashlib.sha1()
		sha1.update(username.encode('utf-8'))
		usernameDigest = sha1.hexdigest() # hexdigest outputs hex-encoded bytes
		sha1 = hashlib.sha1()
		sha1.update(password.encode('utf-8') + usernameDigest.encode('utf-8') + response["digest"].encode('utf-8'))
		passwordDigest = sha1.hexdigest()
		# Here we use POST instead of GET in order to account for folders with lots of files
		authApi = 'userinfo'
		params = { "getauth": 1, "logout": 1, "username": username, "digest": response["digest"],
					"authexpire": str(self.TOKEN_EXPIRATION_SECONDS), "passworddigest": passwordDigest }
		paramsUrlEncoded = urlencode(params)
		response = self.ExecuteRequest(authApi, paramsUrlEncoded)
		if response["result"] != 0:
			errorMessage = self.GetErrorMessage(response["result"])
			raise Exception("Error calling userinfo: " + errorMessage)
		self.auth = response["auth"]
		return self.auth

	def ListFolderContents(self, folderNameOrID, isMyShares = False):
		self.CheckIfAuthPresent()
		tryAgain = True
		while tryAgain:
			if not isMyShares:
				# This is for regular folders, i.e. anything else than the "My Shares" folder
				url = "listfolder?auth=" + self.auth
				if isinstance (folderNameOrID, Number):
					url += "&folderid=" + str(folderNameOrID) # string coercion
				else:
					url += "&path=" + folderNameOrID
			else:
				# This is ONLY for the "My Shares" folder
				url = "listpublinks?auth=" + self.auth
			response = self.ExecuteRequest(url)
			errCode = response["result"]
			if errCode == 2005: # directory does not exist
				folderNameOrID = 0
				tryAgain = True # try again on the root directory
			elif errCode == 2000: # Log in failed. Perhaps old token?
				raise LoginFailedException("Error: Log in failed (2000)")
				tryAgain = False
			else:
				tryAgain = False
				if errCode != 0:
					errorMessage = self.GetErrorMessage(errCode)
					raise Exception("Error calling listfolder or listpublinks: {0} ({1})".format(errorMessage, errCode))
				# We will sort contents by name
				elif not isMyShares:
					response["metadata"]["contents"].sort(key=operator.itemgetter('name'))
		return response

	def GetStreamingUrl(self, fileID):
		self.CheckIfAuthPresent()
		url = "getfilelink?auth=" + self.auth + "&fileid=" + str(fileID)
		response = self.ExecuteRequest(url)
		if response["result"] != 0:
			errorMessage = self.GetErrorMessage(response["result"])
			raise Exception("Error calling getfilelink: " + errorMessage)
		streamingUrl = "https://%s%s" % (response["hosts"][0], response["path"])
		return streamingUrl

	def GetThumbnails (self, fileIDSequence):
		self.CheckIfAuthPresent()
		commaSeparated = ",".join(str(oneFileID) for oneFileID in fileIDSequence) # coerce to string before comma-joining
		url = "getthumbslinks"
		# Here we use POST instead of GET in order to account for folders with lots of files
		params = { "auth": self.auth, "fileids": commaSeparated, "size": "256x256", "format": "png" }
		paramsUrlEncoded = urlencode(params)
		response = self.ExecuteRequest(url, paramsUrlEncoded)
		if response["result"] != 0:
			errorMessage = self.GetErrorMessage(response["result"])
			raise Exception("Error calling getthumbslinks: " + errorMessage)
		# Turn it into a dictionary indexed by file ID, the value being the thumbnail URL
		thumbs = dict()
		for oneThumb in response["thumbs"]:
			if oneThumb["result"] == 0:
				thumbs[oneThumb["fileid"]] = "https://{0}{1}".format(oneThumb["hosts"][0], oneThumb["path"])
		# NOTE: cannot use list comprehension (like below) because the Python interpreter in
		# the Android Kodi port does not seem to understand the syntax.
		# thumbs = { oneThumb["fileid"]: "https://{0}{1}".format(oneThumb["hosts"][0], oneThumb["path"]) for oneThumb in response["thumbs"] if oneThumb["result"] == 0 }
		return thumbs

	def DeleteFile(self, fileID):
		self.CheckIfAuthPresent()
		url = "deletefile?auth=" + self.auth + "&fileid=" + str(fileID)
		self.ExecuteRequest(url)
		if response["result"] != 0:
			errorMessage = self.GetErrorMessage(response["result"])
			raise Exception("Error calling deletefile: " + errorMessage)

	def DeleteFolder(self, folderID):
		self.CheckIfAuthPresent()
		url = self.PCLOUD_BASE_URL + "deletefolderrecursive?auth=" + self.auth + "&folderid=" + str(folderID)
		response = self.ExecuteRequest(url)
		if response["result"] != 0:
			errorMessage = self.GetErrorMessage(response["result"])
			raise Exception("Error calling deletefolderrecursive: " + errorMessage)

	def translateDate(self, dateInPCloudFormat):
		""" Translates a date from the PCloud format ("Thu, 19 Sep 2013 07:31:46 +0000") to
		the Kodi format ("19.09.2013")
		"""
		match = re.search("^[A-Za-z]{3}, (\d{1,2}) ([A-Za-z]{3}) (\d{4})", dateInPCloudFormat)
		if match is None or match.lastindex < 3:
			return date.today().strftime("%d.%m.%Y")
		# Group 1 is the day, group 2 is the month abbreviation, group 3 is the year
		day = int(match.group(1))
		monthDict = { "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
			"Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12  }
		month = monthDict[match.group(2)]
		year = int(match.group(3))
		return date(year, month, day).strftime("%d.%m.%Y")

#auth = PerformLogon("username@example.com", "password")
#ListFolderContents("/Vcast")
#ListFolderContents(34719254)
#ListFolderContents(4684587) # random number, probably invalid
#folderContents = ListFolderContents("/Vcast")
#for oneItem in folderContents["metadata"]["contents"]:
#	print oneItem["name"]
#tempFilename = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8'), 'pippo.json')
#with open(tempFilename, 'w') as f:
#	f.write(json.dumps(response))
