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

import sys, urllib, urllib2, time, re, cookielib
try: import simplejson as json
except ImportError: import json

# ERRORCODES:
# 0 = Ignore
# 200 = OK
# 303 = See other (returned an error message)
# 500 = uncaught error

class VimeoLogin():

	def __init__(self):
		self.xbmc = sys.modules["__main__"].xbmc
		self.v = sys.modules["__main__"].client

		self.settings = sys.modules[ "__main__" ].settings
		self.language = sys.modules[ "__main__" ].language
		self.plugin = sys.modules[ "__main__"].plugin
		self.dbg = sys.modules[ "__main__" ].dbg

		self.utils =  sys.modules[ "__main__" ].utils
		self.common = sys.modules[ "__main__" ].common
		self.USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"
		
	def login(self, params = {}):
		self.settings.openSettings()
		(result, status ) = self._login()
		self.utils.showMessage( self.language( 30029 ), result)
		self.xbmc.executebuiltin( "Container.Refresh" )
		
	def _login(self):
		self.settings.setSetting("userid", "")
		self.settings.setSetting("oauth_token_secret", "")
		self.settings.setSetting("oauth_token", "")
		
		self.v.get_request_token()
		( result, status) = self.login_get_verifier(self.v.get_authorization_url("write"))

		if status != 200:
			return ( result, status)
		
		self.v.set_verifier(result)

		token = str(self.v.get_access_token())
		if self.dbg:
			print self.plugin + " login token: " + token
			
		match = re.match('oauth_token_secret=(.*)&oauth_token=(.*)', token)

		if not match:
			print self.plugin + " login failed"
			return ( self.language(30609), 303)
				
		self.settings.setSetting("oauth_token_secret", match.group(1))
		self.settings.setSetting("oauth_token", match.group(2))
			
		if self.dbg:
			print self.plugin + " login done"
		return ( self.language(30030), 200 )

#	def api_login(self):
		
	def login_get_verifier (self, auth_url):
		if self.dbg:
			print self.plugin + " login_get_verifier - auth_url: " + auth_url
		
		cj = cookielib.LWPCookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
		urllib2.install_opener(opener)
		
		# part 1 request a xsrft token from vimeo's login page
		url = urllib2.Request("http://vimeo.com/log_in")
		url.add_header('User-Agent', self.USERAGENT)
		
		con = urllib2.urlopen(url);
		page1 = con.read()
		con.close()
		
		# part 2: now that we have a token we can do the login procedure while appending token to prove we're legit.
		start = page1.find('<input type="hidden" id="xsrft" class="xsrft" name="token" value="') + len('<input type="hidden" id="xsrft" class="xsrft" name="token" value="')
		xsrft = page1[start:page1.find('"', start)]
		
		request = urllib.urlencode((('sign_in[email]',self.settings.getSetting("user_email")),
									('sign_in[password]', self.settings.getSetting("user_password")),
									('token', xsrft)))
		
		login_url = urllib2.Request("http://vimeo.com/log_in", request)
		login_url.add_header('User-Agent', self.USERAGENT)
		login_url.add_header("Referer", "http://www.vimeo.com/log_in")
		login_url.add_header('Content-Type', "application/x-www-form-urlencoded")
		login_url.add_header('Cookie', "xsrft=" + xsrft )
		
		com = urllib2.urlopen(login_url)
		page2 = com.read()
		
		# part 3: visit main page while referring to login page to recieve valid uid cookie
		third = urllib2.Request("http://vimeo.com/")
		third.add_header("Referer", "http://vimeo.com/log_in")
		third.add_header('User-Agent', self.USERAGENT)
		
		ck = cookielib.Cookie(version=0, name='cached_email', value=self.settings.getSetting("user_email"), port=None, port_specified=False, domain='.vimeo.com', domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=None, discard=False, comment=None, comment_url=None, rest={})
		cj.set_cookie(ck)
		
		cam = urllib2.urlopen(third)
		page3 = cam.read()
		
		if (page3.find("joinimage loggedout") > 0):
			if self.dbg:
				print self.plugin + " login_get_verifier sanity check failed, bad username or password?"
			return ( self.language(30621), 303)
		
		# We should check for this part on the web login to se if http failse and send the message back to the user
		# <div id="message" style="display:block;">
		#
		#	<div class="inner">
		#					The email address and password you entered do not match.			</div>
		# </div>
		if (self.dbg):
			print "Cookie jar contents: " + repr(cj)
		userid = ""
		
		for cookie in cj:
			if cookie.name == "uid":
				uid = urllib.unquote_plus(cookie.value)
				userid = uid.split("|")[0]
		
		if not userid:
			if self.dbg:
				print self.plugin + "login_get_verifier no userid in cookie jar login failed"
			return ( self.language(30606), 303 )
		
		if (self.dbg):
			print self.plugin + " setting userid: " + repr(userid)
		
		url = urllib2.Request(auth_url)
		url.add_header('User-Agent', self.USERAGENT)
		
		con = urllib2.urlopen(url);	
		value = con.read();
		con.close()
		
		if value.find('<span class="verifier">') == -1:
		
			if value.find('<input type="hidden" name="oauth_token" value="') == -1:
				if self.dbg:
					print self.plugin + " login_get_verifier no oauth_token: " #+ repr(value)
				return ( self.language(30606), 303 )

			start = value.find('<input type="hidden" name="oauth_token" value="') + len('<input type="hidden" name="oauth_token" value="')
			login_oauth_token = value[start:value.find('"', start)]

			start = value.find('<input type="hidden" id="xsrft" class="xsrft" name="token" value="') + len('<input type="hidden" id="xsrft" class="xsrft" name="token" value="')
			login_token = value[start:value.find('"', start)]
			
			url = urllib2.Request("http://vimeo.com/oauth/authorize?permission=write")
			url.add_header('User-Agent', self.USERAGENT)
			
			url.add_header('Content-Type', 'application/x-www-form-urlencoded')

			if self.settings.getSetting("accept") != "0":
				if self.dbg:
					print self.plugin + " login_get_verifier accept disabled"
				return ( self.language(30606), 303 )
													
			data = urllib.urlencode({'token': login_token,
									 'oauth_token': login_oauth_token,
									 'permission': 'write',
									 'accept': 'Yes, authorize Vimeo XBMC Plugin!'})
			
			con = urllib2.urlopen(url, data);
			
			value = con.read();
			con.close()
		
		if value.find('<span class="verifier">') == -1:
			if self.dbg:
				print self.plugin + " login_get_verifier no login verifier "
				print repr(value)
			return ( self.language(30606), 303 )
		
		start = value.find('<span class="verifier">') + len('<span class="verifier">')
		verifier = value[start:value.find('</span>', start)]
		self.settings.setSetting("userid", userid)
		
		self.common.log("login_get_verifier verifier: " + verifier, 3)
			
		return ( verifier, 200)
		
	def _apiLogin(self, error = 0):
		return ( self.language(30609), 303 )
	
	def _httpLogin(self, params = {}):
		get = params.get
		return (result, status)
