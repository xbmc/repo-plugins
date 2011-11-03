'''
    YouTube plugin for XBMC
    Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys, urllib2, time
try: import simplejson as json
except ImportError: import json

# ERRORCODES:
# 0 = Ignore
# 200 = OK
# 303 = See other (returned an error message)
# 500 = uncaught error

class YouTubeLogin():

	APIKEY = "AI39si6hWF7uOkKh4B9OEAX-gK337xbwR9Vax-cdeF9CF9iNAcQftT8NVhEXaORRLHAmHxj6GjM-Prw04odK4FxACFfKkiH9lg";

	def __init__(self):
		self.xbmc = sys.modules["__main__"].xbmc

		self.settings = sys.modules[ "__main__" ].settings
		self.language = sys.modules[ "__main__" ].language
		self.plugin = sys.modules[ "__main__"].plugin
		self.dbg = sys.modules[ "__main__" ].dbg

		self.utils =  sys.modules[ "__main__" ].utils
		self.core = sys.modules["__main__" ].core
		self.common = sys.modules[ "__main__" ].common
		self.cache = sys.modules[ "__main__" ].cache
		
	def login(self, params = {}):
		get = params.get
		self.common.log("")
		ouname = self.settings.getSetting("username")
		opass = self.settings.getSetting( "user_password" )
		self.settings.openSettings()
		uname = self.settings.getSetting("username")
		self.dbg = self.settings.getSetting("debug") == "true"
		result = ""
		status = 500

		if uname != "":
			refreshed = False
			if get("new", "false") == "false" and self.settings.getSetting( "oauth2_refresh_token" ) and ouname == uname and opass == self.settings.getSetting( "user_password" ):
				self.common.log("refreshing token: " + str(refreshed))
				refreshed = self.core._oRefreshToken()

			if not refreshed:
				self.common.log("token not refresh, or new uname or password")

				self.settings.setSetting("oauth2_access_token","")
				self.settings.setSetting("oauth2_refresh_token","")
				self.settings.setSetting("oauth2_expires_at", "")
				self.settings.setSetting("nick", "")
				(result, status) = self._httpLogin({ "new": "true"})

				if status == 200:
					(result, status) = self._apiLogin()
				
				if status == 200:
					self.utils.showErrorMessage(self.language(30031), result, 303)
				else:
					self.utils.showErrorMessage(self.language(30609), result, status)
		
		self.xbmc.executebuiltin( "Container.Refresh" )
		return (result, status)

	def _apiLogin(self, error = 0):
		self.common.log("errors: " + str(error))
		
		self.settings.setSetting("oauth2_expires_at", "")
		self.settings.setSetting("oauth2_access_token", "")
		self.settings.setSetting("oauth2_refresh_token", "")

		url = "https://accounts.google.com/o/oauth2/auth?client_id=208795275779.apps.googleusercontent.com&redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope=http%3A%2F%2Fgdata.youtube.com&response_type=code"

		logged_in = False
		fetch_options = { "link": url , "no-language-cookie": "true" }
		step = 0
		self.common.log("Part A")
		while not logged_in and fetch_options and step < 6:
			self.common.log("Step : " + str(step))
			step += 1

			ret = self.core._fetchPage(fetch_options)
			fetch_options = False
			
			newurl = self.common.parseDOM(ret["content"], "form", attrs= { "method": "POST"}, ret = "action")
			state_wrapper = self.common.parseDOM(ret["content"], "input", attrs= { "id": "state_wrapper" }, ret = "value")
			
			if len(newurl) > 0 and len(state_wrapper) > 0:
				url_data = { "state_wrapper": state_wrapper[0],
					     "submit_access": "true"}

				fetch_options = { "link": newurl[0].replace("&amp;", "&"), "url_data": url_data, "no-language-cookie": "true" }
				self.common.log("Part B")
				continue;

			code = self.common.parseDOM(ret["content"], "textarea", attrs = { "id": "code"})
			if len(code) > 0:
				url = "https://accounts.google.com/o/oauth2/token"
				url_data = { "client_id": "208795275779.apps.googleusercontent.com",
					     "client_secret": "sZn1pllhAfyonULAWfoGKCfp",
					     "code": code[0],
					     "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
					     "grant_type": "authorization_code" }
				fetch_options = { "link": url, "url_data": url_data}
				self.common.log("Part C")
				continue
			
			# use token
			if ret["content"].find("access_token") > -1:
				self.common.log("Part D")
				oauth = json.loads(ret["content"])

				if len(oauth) > 0:
					self.common.log("Part D " + repr(oauth["expires_in"]))
					self.settings.setSetting("oauth2_expires_at", str(int(oauth["expires_in"]) + time.time()) ) 
					self.settings.setSetting("oauth2_access_token", oauth["access_token"])
					self.settings.setSetting("oauth2_refresh_token", oauth["refresh_token"])
					
					logged_in = True
					self.common.log("Done:" + self.settings.getSetting( "username" ))
		
		if logged_in:
			return ( self.language(30030), 200 )
		else:
			self.common.log("Failed") 
		return ( self.language(30609), 303 )
	
	def _httpLogin(self, params = {}):
		get = params.get
		self.common.log("")
		result = ""
		status = 500

		if get("new", "false") == "true":
			self.settings.setSetting( "login_info", "" )
		elif self.settings.getSetting( "login_info" ) != "":
			self.common.log("returning existing login info: " + self.settings.getSetting( "login_info" ))
			return ( self.settings.getSetting( "login_info" ), 200)

		logged_in = False
		fetch_options = { "link": get("link", "http://www.youtube.com/") }
		step = 0
		galx = ""
		while not logged_in and fetch_options and step < 18: # 6 steps for 2-factor login
			self.common.log("Step : " + str(step))
			step += 1

			if step == 17:
				return ( self.core._findErrors(ret), 303)

			ret = self.core._fetchPage(fetch_options)
			if ret["content"].find("captcha") > -1:
				self.common.log("Captcha needs to be filled")
				break;
			fetch_options = False

			# Click login link on youtube.com
			newurl = self.common.parseDOM(ret["content"], "a", attrs = {"class": "end" }, ret = "href")
			if len(newurl) > 0:
				# Start login procedure
				if newurl[0] != "#":
					fetch_options = { "link": newurl[0].replace("&amp;", "&") }
					self.common.log("Part A : " + repr(fetch_options) )

			# Fill out login information and send.
			newurl = self.common.parseDOM(ret["content"].replace("\n", " "), "form", attrs = { "id": "gaia_loginform"}, ret = "action")
			if len(newurl) > 0:
				( galx, url_data ) = self._fillLoginInfo(ret["content"])
				if len(galx) > 0 and len(url_data) > 0:
					fetch_options = { "link": newurl[0], "no-language-cookie": "true", "url_data": url_data, "hidden": "true" }
					self.common.log("Part B:" + repr(fetch_options), 10) ## WARNING, SHOWS LOGIN INFO/PASSWORD
					continue
			
			newurl = self.common.parseDOM(ret["content"], "meta", attrs = { "http-equiv": "refresh"}, ret = "content")
			if len(newurl) > 0 :
				newurl = newurl[0].replace("&amp;", "&")
				newurl = newurl[newurl.find("&#39;") + 5 : newurl.rfind("&#39;")]
				fetch_options = { "link": newurl, "no-language-cookie": "true" }
				self.common.log("Part C: "  + repr(fetch_options))
				continue

			## 2-factor login start
			if ret["content"].find("smsUserPin") > -1:
				url_data = self._fillUserPin(ret["content"])

				target_url = ret["new_url"]
				if target_url.rfind("/") > 10:
					target_url = target_url[:target_url.find("/", 10)]
				else:
					target_url += "/"

				new_part = self.common.parseDOM(ret["content"], "form", attrs = { "name": "verifyForm"}, ret = "action")
				fetch_options = { "link": target_url + new_part[0], "url_data": url_data, "no-language-cookie": "true" }

				self.common.log("Part D: " + repr(fetch_options))
				continue

			smsToken = self.common.parseDOM(ret["content"].replace("\n", ""), "input", attrs= { "name": "smsToken" }, ret= "value")
			cont = self.common.parseDOM(ret["content"], "input", attrs= { "name": "continue"}, ret="value" )

			if len(cont) > 0 and len(smsToken) > 0 and galx != "":
				url_data = { "smsToken": smsToken[0],
					     "continue": cont[0],
					     "PersistentCookie": "yes",
					     "service": "youtube",
					     "GALX": galx}

				target_url = self.common.parseDOM(ret["content"], "form", attrs = { "name": "hiddenpost"}, ret = "action")
				fetch_options = { "link": target_url[0], "url_data": url_data, "no-language-cookie": "true" }
				self.common.log("Part E: " + repr(fetch_options))
				continue

			## 2-factor login finish
			
			if not fetch_options:
				# Check if we are logged in.
				if ret["content"].find("USERNAME', ") > 0:
					logged_in = True
					self.common.log("Logged in. Parsing data.")
					break;
				# Look for errors and return error.
				return ( self.core._findErrors(ret), 303)
		
		if logged_in:
			status = self._getLoginInfo(ret["content"])
			if status == 200:
				result = self.settings.getSetting( "login_info" )
			## Maybe verify age here?

		return (result, status)

	def _fillLoginInfo(self, content):
		rmShown = self.common.parseDOM(content, "input", attrs = { "name": "rmShown"}, ret = "value" )
		cont = self.common.parseDOM(content, "input", attrs = { "name": "continue"}, ret = "value")
		uilel = self.common.parseDOM(content, "input", attrs = { "name": "uilel" }, ret= "value")
		if len(uilel) == 0:
			uilel = self.common.parseDOM(content, "input", attrs= { "id": "uilel" }, ret= "value")
		dsh = self.common.parseDOM(content, "input", attrs = { "name": "dsh" }, ret = "value")
		if len(dsh) == 0:
			dsh = self.common.parseDOM(content, "input", attrs = { "id": "dsh" }, ret = "value")

		# Can we get this elsewhere?
		galx = self.common.parseDOM(content, "input", attrs = { "name": "GALX"}, ret = "value")
		uname = self.settings.getSetting( "username" )
		pword = self.settings.getSetting( "user_password" )

		if pword == "":
			pword = self.utils.getUserInput(self.language(30628), hidden = True)

		if len(galx) == 0 or len(cont) == 0 or len(uilel) == 0 or len(dsh) == 0 or len(rmShown) == 0 or uname == "" or pword == "":
			self.common.log("_fillLoginInfo missing values for login form " + repr(galx) + repr(cont) + repr(uilel) + repr(dsh) + repr(rmShown) + repr(uname) + str(len(pword)))
			return ( "", {} )
		else:
			galx = galx[0]
			url_data = { "pstMsg": "0",
				     "ltmpl": "sso",
				     "dnConn": "",
				     "continue": cont[0],
				     "service": "youtube",
				     "uilel": uilel[0],
				     "dsh": dsh[0],
				     "hl": "en_US",
				     "timeStmp": "",
				     "secTok": "",
				     "GALX": galx,
				     "Email": uname,
				     "Passwd": pword,
				     "PersistentCookie": "yes",
				     "rmShown": rmShown[0],
				     "signin": "Sign in",
				     "asts": ""
				     }
			return ( galx, url_data)

	def _fillUserPin(self, content):
		smsToken = self.common.parseDOM(content, "input", attrs = { "name": "smsToken" }, ret = "value")
		self.smsToken = smsToken
		email = self.common.parseDOM(content, "input", attrs = { "name": "email" }, ret = "value")
		userpin = self.utils.getUserInput(self.language(30627))

		if len(smsToken) > 0 and len(email) > 0 and len(userpin) > 0:
			url_data = { "smsToken": smsToken[0],
				     "PersistentCookie": "yes",
				     "smsUserPin" : userpin,
				     "smsVerifyPin" : "Verify",
				     "timeStmp" : "",
				     "secTok" : "",
				     "email" : email[0]}
			return url_data
		return {}

	def _getLoginInfo(self, content):
		nick = ""
		status = 303
		if content.find("USERNAME', ") > 0:
			nick = content[content.find("USERNAME', ") + 12:]
			nick = nick[:nick.find('")')]
		
		if nick:
			self.settings.setSetting("nick", nick)
		else:
			self.common.log("Failed to get usename from youtube")

		# Save cookiefile in settings
		self.common.log("Scanning cookies for login info")
		
		login_info = ""
		cookies = repr(sys.modules[ "__main__" ].cookiejar)
			
		if cookies.find("name='LOGIN_INFO', value='") > 0:
			start = cookies.find("name='LOGIN_INFO', value='") + len("name='LOGIN_INFO', value='")
			login_info = cookies[start:cookies.find("', port=None", start)]
		
		if login_info:
			self.settings.setSetting( "login_info", login_info )
			status = 200

		self.common.log("Done : " + str(status) + " - " + login_info)
		return status
