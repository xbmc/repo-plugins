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

import sys, urllib, urllib2, re, os, cookielib, string, inspect, xbmc, time
from xml.dom.minidom import parseString
try: import simplejson as json
except ImportError: import json

# ERRORCODES:
# 0 = Ignore
# 200 = OK
# 303 = See other (returned an error message)
# 500 = uncaught error

cookiejar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
urllib2.install_opener(opener)

class url2request(urllib2.Request):
        """Workaround for using DELETE with urllib2"""
        def __init__(self, url, method, data=None, headers={}, origin_req_host=None, unverifiable=False):
                self._method = method
                urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)

        def get_method(self):
                if self._method:
                        return self._method
                else:
                        return urllib2.Request.get_method(self)

class YouTubeLogin(object):
	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__" ].__plugin__
	__dbg__ = sys.modules[ "__main__" ].__dbg__
	__dbglevel__ = 3
	__dbgv__ = False
	APIKEY = "AI39si6hWF7uOkKh4B9OEAX-gK337xbwR9Vax-cdeF9CF9iNAcQftT8NVhEXaORRLHAmHxj6GjM-Prw04odK4FxACFfKkiH9lg";
	USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"

	#===============================================================================
	#
	# External functions called by YouTubeNavigation.py
	#
	# return MUST be a tupple of ( result[string or dict], status[int] )
	# 
	#===============================================================================
	
	def __init__(self):
		timeout = self.__settings__.getSetting( "timeout" )
		if not timeout:
			timeout = "5"
		#socket.setdefaulttimeout(float(timeout))
		return None
		
	def login(self, params = {}):
		get = params.get
		self.log("")
		ouname = self.__settings__.getSetting("username")
		opass = self.__settings__.getSetting( "user_password" )
		self.__settings__.openSettings()
		uname = self.__settings__.getSetting("username")
		self.__dbg__ = self.__settings__.getSetting("debug") == "true"
		result = ""
		status = 500

		if uname != "":
			refreshed = False
			if get("new", "false") == "false" and self.__settings__.getSetting( "oauth2_refresh_token" ) and ouname == uname and opass == self.__settings__.getSetting( "user_password" ):
				self.log("refreshing token: " + str(refreshed))
				refreshed = self._oRefreshToken()

			if not refreshed:
				self.log("token not refresh, or new uname or password")

				self.__settings__.setSetting("oauth2_access_token","")
				self.__settings__.setSetting("oauth2_refresh_token","")
				self.__settings__.setSetting("oauth2_expires_at", "")
				self.__settings__.setSetting("nick", "")
				(result, status) = self._httpLogin({ "new": "true"})

				if status == 200:
					(result, status) = self._apiLogin()
				
				if status == 200:
					return (self.__language__(30030), 200)
				else:
					return (self.__language__(30609), 303)
		
		xbmc.executebuiltin( "Container.Refresh" )
		return (result, status)

	def _apiLogin(self, error = 0):
		self.log("errors: " + str(error))
		
		self.__settings__.setSetting("oauth2_expires_at", "")
		self.__settings__.setSetting("oauth2_access_token", "")
		self.__settings__.setSetting("oauth2_refresh_token", "")

		url = "https://accounts.google.com/o/oauth2/auth?client_id=208795275779.apps.googleusercontent.com&redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope=http%3A%2F%2Fgdata.youtube.com&response_type=code"

		logged_in = False
		fetch_options = { "link": url , "no-language-cookie": "true" }
		step = 0
		self.log("Part A")
		while not logged_in and fetch_options and step < 6:
			self.log("Step : " + str(step))
			step += 1

			ret = self._fetchPage(fetch_options)
			fetch_options = False
			
			newurl = self.parseDOM(ret["content"], "form", attrs= { "method": "POST"}, ret = "action")
			state_wrapper = self.parseDOM(ret["content"], "input", attrs= { "id": "state_wrapper" }, ret = "value")
			
			if len(newurl) > 0 and len(state_wrapper) > 0:
				url_data = { "state_wrapper": state_wrapper[0],
					     "submit_access": "true"}

				fetch_options = { "link": newurl[0].replace("&amp;", "&"), "url_data": url_data, "no-language-cookie": "true" }
				self.log("Part B")
				continue;

			code = self.parseDOM(ret["content"], "textarea", attrs = { "id": "code"})
			if len(code) > 0:
				url = "https://accounts.google.com/o/oauth2/token"
				url_data = { "client_id": "208795275779.apps.googleusercontent.com",
					     "client_secret": "sZn1pllhAfyonULAWfoGKCfp",
					     "code": code[0],
					     "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
					     "grant_type": "authorization_code" }
				fetch_options = { "link": url, "url_data": url_data}
				self.log("Part C")
				continue
			
			# use token
			if ret["content"].find("access_token") > -1:
				self.log("Part D")
				oauth = json.loads(ret["content"])

				if len(oauth) > 0:
					self.log("Part D " + repr(oauth["expires_in"]))
					self.__settings__.setSetting("oauth2_expires_at", str(int(oauth["expires_in"]) + time.time()) ) 
					self.__settings__.setSetting("oauth2_access_token", oauth["access_token"])
					self.__settings__.setSetting("oauth2_refresh_token", oauth["refresh_token"])
					
					logged_in = True
					self.log("Done:" + self.__settings__.getSetting( "username" ))
		
		if logged_in:
			return ( self.__language__(30030), 200 )
		else:
			self.log("Failed") 
		return ( self.__language__(30609), 303 )
	
	def _httpLogin(self, params = {}):
		get = params.get
		self.log("")
		result = ""
		status = 500

		if get("new", "false") == "true":
			self.__settings__.setSetting( "login_info", "" )
                        self.__settings__.setSetting( "SID", "" )
		elif self.__settings__.getSetting( "login_info" ) != "":
			self.log("returning existing login info: " + self.__settings__.getSetting( "login_info" ))
			return ( self.__settings__.getSetting( "login_info" ), 200)

		logged_in = False
		fetch_options = { "link": get("link", "http://www.youtube.com/") }
		step = 0
		galx = ""
		while not logged_in and fetch_options and step < 18: # 6 steps for 2-factor login
			self.log("Step : " + str(step))
			step += 1

			if step == 17:
				return ( self._findErrors(ret), 303)

			ret = self._fetchPage(fetch_options)
			if ret["content"].find("captcha") > -1:
				self.log("Captcha needs to be filled")
				break;
			fetch_options = False

			# Check if we are logged in.
                        nick = self.parseDOM(ret["content"], "span", attrs= { "class": "masthead-user-username"} )

			if len(nick) > 0:
				self.log("Logged in. Parsing data.")
				status = self._getLoginInfo(ret["content"])
                                return(ret, status)

			# Click login link on youtube.com
			newurl = self.parseDOM(ret["content"], "a", attrs = {"class": "end" }, ret = "href")
			if len(newurl) > 0:
				# Start login procedure
				if newurl[0] != "#":
					fetch_options = { "link": newurl[0].replace("&amp;", "&") }
					self.log("Part A : " + repr(fetch_options) )

			newurl = self.parseDOM(ret["content"], "meta", attrs = { "http-equiv": "refresh"}, ret = "content")
			if len(newurl) > 0 :
				self.log(repr(newurl))

			# Fill out login information and send.
			newurl = self.parseDOM(ret["content"].replace("\n", " "), "form", attrs = { "id": "gaia_loginform"}, ret = "action")
			if len(newurl) > 0:
				( galx, url_data ) = self._fillLoginInfo(ret["content"])
				if len(galx) > 0 and len(url_data) > 0:
					fetch_options = { "link": newurl[0], "no-language-cookie": "true", "url_data": url_data, "hidden": "true" }
					self.log("Part B:" + repr(fetch_options), 10) ## WARNING, SHOWS LOGIN INFO/PASSWORD
					continue
			
			newurl = self.parseDOM(ret["content"], "meta", attrs = { "http-equiv": "refresh"}, ret = "content")
			if len(newurl) > 0 :
				newurl = newurl[0].replace("&amp;", "&")
				newurl = newurl[newurl.find("&#39;") + 5 : newurl.rfind("&#39;")]
				fetch_options = { "link": newurl, "no-language-cookie": "true" }
				self.log("Part C: "  + repr(fetch_options))
				continue

			## 2-factor login start
			if ret["content"].find("smsUserPin") > -1:
				url_data = self._fillUserPin(ret["content"])

				target_url = ret["new_url"]
				if target_url.rfind("/") > 10:
					target_url = target_url[:target_url.find("/", 10)]
				else:
					target_url += "/"

				new_part = self.parseDOM(ret["content"], "form", attrs = { "name": "verifyForm"}, ret = "action")
				fetch_options = { "link": target_url + new_part[0], "url_data": url_data, "no-language-cookie": "true" }

				self.log("Part D: " + repr(fetch_options))
				continue

			smsToken = self.parseDOM(ret["content"].replace("\n", ""), "input", attrs= { "name": "smsToken" }, ret= "value")
			cont = self.parseDOM(ret["content"], "input", attrs= { "name": "continue"}, ret="value" )

			if len(cont) > 0 and len(smsToken) > 0 and galx != "":
				url_data = { "smsToken": smsToken[0],
					     "continue": cont[0],
					     "PersistentCookie": "yes",
					     "service": "youtube",
					     "GALX": galx}

				target_url = self.parseDOM(ret["content"], "form", attrs = { "name": "hiddenpost"}, ret = "action")
				fetch_options = { "link": target_url[0], "url_data": url_data, "no-language-cookie": "true" }
				self.log("Part E: " + repr(fetch_options))
				continue

			## 2-factor login finish
			
			if not fetch_options:
				# Look for errors and return error.
				return ( self._findErrors(ret), 303)
		
		if logged_in:
			status = self._getLoginInfo(ret["content"])
			if status == 200:
				result = self.__settings__.getSetting( "login_info" )
			## Maybe verify age here?

		return (result, status)

	def _fillLoginInfo(self, content):
		self.log("")
		rmShown = self.parseDOM(content, "input", attrs = { "name": "rmShown"}, ret = "value" )
		cont = self.parseDOM(content, "input", attrs = { "name": "continue"}, ret = "value")
		uilel = self.parseDOM(content, "input", attrs = { "name": "uilel" }, ret= "value")
		if len(uilel) == 0:
			uilel = self.parseDOM(content, "input", attrs= { "id": "uilel" }, ret= "value")
		dsh = self.parseDOM(content, "input", attrs = { "name": "dsh" }, ret = "value")
		if len(dsh) == 0:
			dsh = self.parseDOM(content, "input", attrs = { "id": "dsh" }, ret = "value")

		# Can we get this elsewhere?
		galx = self.parseDOM(content, "input", attrs = { "name": "GALX"}, ret = "value")
		uname = self.__settings__.getSetting( "username" )
		pword = self.__settings__.getSetting( "user_password" )

		if pword == "":
			pword = self._getUserInput(self.__language__(30628), hidden = True)

		if len(galx) == 0 or len(cont) == 0 or len(uilel) == 0 or len(dsh) == 0 or len(rmShown) == 0 or uname == "" or pword == "":
			self.log("_fillLoginInfo missing values for login form " + repr(galx) + repr(cont) + repr(uilel) + repr(dsh) + repr(rmShown) + repr(uname) + str(len(pword)))
			#self.log(repr(content))
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
			self.log("done")

			return ( galx, url_data)

	def _fillUserPin(self, content):
		smsToken = self.parseDOM(content, "input", attrs = { "name": "smsToken" }, ret = "value")
		self.smsToken = smsToken
		email = self.parseDOM(content, "input", attrs = { "name": "email" }, ret = "value")
		userpin = self._getUserInput(self.__language__(30627))

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

        def _getCookieInfoAsHTML(self):
		cookie = repr(cookiejar)
                cookie = cookie.replace("<_LWPCookieJar.LWPCookieJar[", "")
		cookie = cookie.replace("), Cookie(version=0,", "></cookie><cookie ")
		cookie = cookie.replace(")]>", "></cookie>")
		cookie = cookie.replace("Cookie(version=0,", "<cookie ")
                cookie = cookie.replace(", ", " ")
                return cookie

	def _getLoginInfo(self, content):
		nick = ""
		status = 303
		nick = self.parseDOM(content, "span", attrs= { "class": "masthead-user-username"} )

		if len(nick) > 0 :
                        self.__settings__.setSetting("nick", nick[0])
                else:
                        self.log("Failed to get usename from youtube")

		# Save cookiefile in settings
		self.log("Scanning cookies for login info")
		
		login_info = ""
		SID = ""
                cookies = self._getCookieInfoAsHTML()
		login_info = self.parseDOM(cookies, "cookie", attrs = { "name": "LOGIN_INFO" }, ret = "value")
                SID = self.parseDOM(cookies, "cookie", attrs = { "name": "SID", "domain": ".youtube.com"}, ret = "value")

                if len(login_info) == 1:
			self.log("LOGIN_INFO: " + repr(login_info))
			self.__settings__.setSetting( "login_info", login_info[0])
		else:
                        self.log("Failed to get LOGIN_INFO from youtube")

                if len(SID) == 1:
			self.log("SID: " + repr(SID))
                        self.__settings__.setSetting( "SID", SID[0])
		else:
                        self.log("Failed to get SID from youtube")

		if len(SID) == 1 and len(login_info) == 1:
			status = 200

		self.log("Done : " + str(status))
		return status


	def _fetchPage(self, params={}): # This does not handle cookie timeout for _httpLogin
		get = params.get
		link = get("link")
		ret_obj = { "status": 500, "content": ""}

		if (get("url_data") or get("request") or get("hidden")):
			self.log("called for : " + repr(params['link']))
		else:
			self.log("called for : " + repr(params))

		if get("auth", "false") == "true":
			self.log("got auth")
			if self._getAuth():
				if link.find("?") > -1:
					link += "&oauth_token=" + self.__settings__.getSetting("oauth2_access_token")
				else:
					link += "?oauth_token=" + self.__settings__.getSetting("oauth2_access_token")

				self.log("updated link: " + link)
			else:
				self.log("couldn't get login token")

		if not link or int(get("error", "0")) > 2 :
			self.log("giving up ")
			return ret_obj

		if get("url_data"):
			request = urllib2.Request(link, urllib.urlencode(get("url_data")))
			request.add_header('Content-Type', 'application/x-www-form-urlencoded')
		elif get("request", "false") == "false":
			request = url2request(link, get("method", "GET"));

		else:
			self.log("got request")
			request = urllib2.Request(link, get("request"))
			request.add_header('X-GData-Client', "")
			request.add_header('Content-Type', 'application/atom+xml') 
			request.add_header('Content-Length', str(len(get("request")))) 

		if get("api", "false") == "true":
			self.log("got api")
			request.add_header('GData-Version', '2.1')
			request.add_header('X-GData-Key', 'key=' + self.APIKEY)

		else:
			request.add_header('User-Agent', self.USERAGENT)

			if get("no-language-cookie", "false") == "false":
				request.add_header('Cookie', 'PREF=f1=50000000&hl=en')
		
		if get("login", "false") == "true":
			self.log("got login")
			if (self.__settings__.getSetting("username") == "" or self.__settings__.getSetting("user_password") == ""):
				self.log("_fetchPage, login required but no credentials provided")
				ret_obj["status"] = 303
				ret_obj["content"] = self.__language__(30622)
				return ret_obj

			if self.__settings__.getSetting("login_info") == "":
				self._httpLogin()

			if self.__settings__.getSetting("login_info") != "":
				self.log("returning existing login info: " + self.__settings__.getSetting("login_info"))
				info = self.__settings__.getSetting("login_info")
				request.add_header('Cookie', 'LOGIN_INFO=' + info)
		
		if get("auth", "false") == "true":
			self.log("got auth")
			if self._getAuth():
				request.add_header('Authorization', 'GoogleLogin auth=' + self.__settings__.getSetting("oauth2_access_token"))
			else:
				self.log("couldn't get login token")
		
		try:
			self.log("connecting to server... ")

			con = urllib2.urlopen(request)
			
			ret_obj["content"] = con.read()
			ret_obj["new_url"] = con.geturl()
			ret_obj["header"] = str(con.info())
			con.close()

			self.log("Result: %s " % repr(ret_obj), 9)
			# Return result if it isn't age restricted
			if (ret_obj["content"].find("verify-actions") == -1 and ret_obj["content"].find("verify-age-actions") == -1):
				self.log("done")
				ret_obj["status"] = 200
				return ret_obj
			else:
				self.log("found verify age request: " + repr(params))
				# We need login to verify age
				if not get("login"):
					params["error"] = get("error", "0")
					params["login"] = "true"
					return self._fetchPage(params)
				elif get("no_verify_age", "false") == "false":
					ret_obj["status"] = 303
					ret_obj["content"] = self.__language__(30606)
					return self._verifyAge(link, ret_obj["new_url"], params)
				else:
					#ret_obj["status"] = 303
					#ret_obj["content"] = self.__language__(30606)
					return ret_obj
		
		except urllib2.HTTPError, e:
			cont = False
			err = str(e)
			
			self.log("HTTPError : " + err)
			if e.code == 400 or True:
				msg = e.read()
				self.log("Unhandled HTTPError : [%s] %s " % ( e.code, msg), 1)
			
			if err.find("Token invalid") > -1:
				self.log("refreshing token")
				self._oRefreshToken()
			elif err.find("User Rate Limit Exceeded") > -1:
				self.log("Sleeping for 10 seconds")
				time.sleep(10)
			else:
				if e.fp:
					cont = e.fp.read()
				self.log("HTTPError - Headers: " + str(e.headers) + " - Content: " + cont)

			params["error"] = str(int(get("error", "0")) + 1)
			ret_obj = self._fetchPage(params)

			if cont and ret_obj["content"] == "":
				ret_obj["content"] = cont
				ret_obj["status"] = 303

			return ret_obj

		except urllib2.URLError, e:
			err = str(e)
			self.log("URLError : " + err)
			
			time.sleep(3)
			params["error"] = str(int(get("error", "0")) + 1)
			ret_obj = self._fetchPage(params)
			return ret_obj
		
	def _findErrors(self, ret):
		self.log("")

		## Couldn't find 2 factor or normal login
		error = self.parseDOM(ret['content'], "div", attrs={ "class": "errormsg" })
		if len(error) == 0:   
			# An error in 2-factor
			self.log("1")
			error = self.parseDOM(ret['content'], "div", attrs={ "class": "error smaller"})
		if len(error) == 0:
			self.log("2")
			error = self.parseDOM(ret['content'], "div", attrs={ "id": "unavailable-message"})
		if len(error) == 0 and ret['content'].find("yt:quota") > -1:
			self.log("3")
			# Api quota
			html = self.parseDOM(ret['content'], "error")
			error = self.parseDOM(html, "code")

		if len(error) > 0:
			self.log("4")
			error = error[0]
			error = urllib.unquote(error[0:error.find("[")]).replace("&#39;", "'")
			self.log("returning error : " + error.strip())
			return error.strip()

		self.log("couldn't find any errors: " + repr(ret))
		return False

	def _verifyAge(self, org_link, new_url, params={}):
		self.log("org_link : " + org_link + " - new_url: " + new_url)
		fetch_options = { "link": new_url, "no_verify_age": "true", "login": "true" }
		verified = False
		step = 0
		ret = {}
		while not verified and fetch_options and step < 6:
			self.log("Step : " + str(step))
			step += 1

			if step == 17:
				return ( self._findErrors(ret), 303)

			ret = self._fetchPage(fetch_options)
			fetch_options = False
			new_url = self.parseDOM(ret["content"], "form", attrs = { "id": "confirm-age-form"}, ret ="action")
			if len(new_url) > 0:
				self.log("Part A")
				new_url = "http://www.youtube.com/" + new_url[0]
				next_url = self.parseDOM(ret["content"], "input", attrs = { "name": "next_url" }, ret = "value")
				set_racy = self.parseDOM(ret["content"], "input", attrs = { "name": "set_racy" }, ret = "value")
				session_token_start = ret["content"].find("'XSRF_TOKEN': '") + len("'XSRF_TOKEN': '")
				session_token_stop = ret["content"].find("',", session_token_start)
				session_token = ret["content"][session_token_start:session_token_stop]

				fetch_options = { "link": new_url, "no_verify_age": "true", "login": "true", "url_data": { "next_url": next_url[0], "set_racy": set_racy[0], "session_token" : session_token} }

			if ret["content"].find("PLAYER_CONFIG") > -1:
				self.log("Found PLAYER_CONFIG. Verify successful")
				return ret

			if not fetch_options:
				self.log("Nothign hit, assume we are logged in.")
				fetch_options = { "link": org_link, "no_verify_age": "true", "login": "true" }
				return self._fetchPage(fetch_options)

		self.log("Done")

	def _oRefreshToken(self):
		self.log("")
		# Refresh token
		if self.__settings__.getSetting("oauth2_refresh_token"):
			url = "https://accounts.google.com/o/oauth2/token"
			data = { "client_id": "208795275779.apps.googleusercontent.com",
				"client_secret": "sZn1pllhAfyonULAWfoGKCfp",
				"refresh_token": self.__settings__.getSetting("oauth2_refresh_token"),
				"grant_type": "refresh_token"}
			self.__settings__.setSetting("oauth2_access_token", "")
			ret = self._fetchPage({ "link": url, "no-language-cookie": "true", "url_data": data})
			if ret["status"] == 200:
				oauth = ""
				try:
					oauth = json.loads(ret["content"])
				except:
					self.log("Except: " + repr(ret))
					return False
			
				self.log("- returning, got result a: " + repr(oauth))
				
				self.__settings__.setSetting("oauth2_access_token", oauth["access_token"])
				self.__settings__.setSetting("oauth2_expires_at", str(int(oauth["expires_in"]) + time.time()) )
				self.log("Success")
				return True
			else:
				self.log("Failure, Trying a clean login")
				self.login({ "new": "true"})
			return False

		self.log("didn't even try")

		return False

	def getDOMContent(self, html, name, match):
		self.log("match: " + match, 2)
		start = html.find(match)
		endstr = "</" + name + ">"
		end = html.find(endstr, start)

		pos = html.find("<" + name, start + 1 )
		self.log(str(start) + " < " + str(end) + ", pos = " + str(pos) + ", endpos: " + str(end), 8)

		while pos < end and pos != -1:
			tend = html.find(endstr, end + len(endstr))
                        if tend != -1:
                                end = tend
                        pos = html.find("<" + name, pos + 1)
			self.log("loop: " + str(start) + " < " + str(end) + " pos = " + str(pos), 8)

		self.log("start: %s, end: %s" % ( start + len(match), end), 2)
		if start == -1 and end == -1:
			html = ""
		elif start > -1 and end > -1:
			html = html[start + len(match):end]
		#elif end > -1:
		#	html = html[:end]
		#elif start > -1:
		#	html = html[start + len(match):]

		self.log("done html length: " + str(len(html)) + ", content: " + html, 2)
		return html

	def getDOMAttributes(self, lst):
		self.log("", 2)
		ret = []
		for tmp in lst:
			if tmp.find('="') > -1:
				tmp = tmp[:tmp.find('="')]

			if tmp.find('=\'') > -1:
				tmp = tmp[:tmp.find('=\'')]

			cont_char = tmp[0]
			tmp = tmp[1:]
			if tmp.rfind(cont_char) > -1:
				tmp = tmp[:tmp.rfind(cont_char)]
			tmp = tmp.strip()
			ret.append(tmp)

		self.log("Done: " + repr(ret), 2)
		return ret

	def parseDOM(self, html, name = "", attrs = {}, ret = False):
		# html <- text to scan.
		# name <- Element name
		# attrs <- { "id": "my-div", "class": "oneclass.*anotherclass", "attribute": "a random tag" }
		# ret <- Return content of element
		# Default return <- Returns a list with the content
		self.log("start: " + repr(name) + " - " + repr(attrs) + " - " + repr(ret) + " - " + str(type(html)), 1)

		if type(html) != type([]):
			html = [html]
		
		if not name.strip():
			self.log("Missing tag name")
			return ""

		ret_lst = []

		# Find all elements with the tag
			
		i = 0
		for item in html:
			item = item.replace("\n", "")
			lst = []

			for key in attrs:
				scripts = [ '(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"][^>]*?>))', # Hit often.
					    '(<' + name + ' (?:' + key + '=[\'"]' + attrs[key] + '[\'"])[^>]*?>)', # Hit twice
					    '(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"])[^>]*?>)'] # 

				lst2 = []
				for script in scripts:
					if len(lst2) == 0:
						#self.log("scanning " + str(i) + " " + str(len(lst)) + " Running :" + script, 2)
						lst2 = re.compile(script).findall(item)
						i += 1
				if len(lst2) > 0:
					if len(lst) == 0:
						lst = lst2;
						lst2 = []
					else:
						test = range(len(lst))
						test.reverse()
						for i in test: # Delete anything missing from the next list.
							if not lst[i] in lst2:
								self.log("Purging mismatch " + str(len(lst)) + " - " + repr(lst[i]), 1)
								del(lst[i])
	
			if len(lst) == 0 and attrs == {}:
				self.log("no list found, making one on just the element name", 1)
				lst = re.compile('(<' + name + '[^>]*?>)').findall(item)
	
			if ret != False:
				self.log("Getting attribute %s content for %s matches " % ( ret, len(lst) ), 2)
				lst2 = []
				for match in lst:
					tmp_list = re.compile('<' + name + '.*?' + ret + '=([\'"][^>]*?)>').findall(match)
					lst2 += self.getDOMAttributes(tmp_list)
					self.log(lst, 3)
					self.log(match, 3)
					self.log(lst2, 3)
				lst = lst2
			elif name != "img":
				self.log("Getting element content for %s matches " % len(lst), 2)
				lst2 = []
				for match in lst:
					temp = self.getDOMContent(item, name, match).strip()
					item = item[item.find(match + temp) + len(match + temp):]
					lst2.append(temp)
					self.log(lst, 3)
					self.log(match, 3)
					self.log(lst2, 3)
				lst = lst2
			ret_lst += lst

		self.log("Done", 1)
		return ret_lst

        # This function raises a keyboard for user input 
        def _getUserInput(self, title = "Input", default="", hidden=False):
                result = None

                # Fix for when this functions is called with default=None
                if not default:
                        default = ""

                keyboard = xbmc.Keyboard(default, title)
                keyboard.setHiddenInput(hidden)
                keyboard.doModal()

                if keyboard.isConfirmed():
                        result = keyboard.getText()

                return result

        def _getAuth(self):
		now = time.time()
                if self.__settings__.getSetting("oauth2_expires_at"):
			expire_at = float(self.__settings__.getSetting("oauth2_expires_at"))
                else:
			expire_at = now

                self.log("Oauth expires in %s seconds"  % int(expire_at - now))

                if expire_at <= now:
                        self._oRefreshToken()

                auth = self.__settings__.getSetting("oauth2_access_token")
                self.log("oauth2_access_token: " + repr(auth), 5)

                if (auth):
                        self.log("returning stored auth")
			return auth
		else:
			(result, status) = self.login.login()

		if status == 200:
			self.log("returning new auth")
			return self.__settings__.getSetting("oauth2_access_token")

		self.log("failed because login failed")
		
		return False

	def log(self, description, level = 0):
                if self.__dbg__ and self.__dbglevel__ > level:
			print "[%s] %s : '%s'" % (self.__plugin__, inspect.stack()[1][3], description.encode("utf8", "ignore"))

