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

import sys, urllib, urllib2, re, cookielib, socket
import xbmc

# ERRORCODES:
# 0 = Ignore
# 200 = OK
# 303 = See other (returned an error message)
# 500 = uncaught error

class YouTubeLogin(object):
	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__" ].__plugin__
	__utils__ = sys.modules[ "__main__" ].__utils__
	__dbg__ = sys.modules[ "__main__" ].__dbg__
	
	APIKEY = "AI39si6hWF7uOkKh4B9OEAX-gK337xbwR9Vax-cdeF9CF9iNAcQftT8NVhEXaORRLHAmHxj6GjM-Prw04odK4FxACFfKkiH9lg";
	USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"
		
	urls = {};
	urls['http_login'] = "https://www.google.com/accounts/ServiceLogin?service=youtube"
	urls['http_login_confirmation'] = "http://www.youtube.com/signin?action_handle_signin=true&nomobiletemp=1&hl=en_US&next=/index&hl=en_US&ltmpl=sso"
	urls['gdata_login'] = "https://www.google.com/accounts/ClientLogin"
	
	def __init__(self):
		timeout = self.__settings__.getSetting( "timeout" )
		if not timeout:
			timeout = "5"
		socket.setdefaulttimeout(float(timeout))
		return None

	def login(self, params = {}):
		self.__settings__.openSettings()
		
		if self.__settings__.getSetting("username") and self.__settings__.getSetting( "user_password" ):
			(result, status) = self._login()
		
			if status == 200:
				(http_login, status) = self._httpLogin(True)
				
			if status == 200:
				self.__utils__.showErrorMessage(self.__language__(30031), result, 303)
			else:
				self.__settings__.setSetting("auth","")
				self.__settings__.setSetting("nick","")
				self.__utils__.showErrorMessage(self.__language__(30609), result, status)
		
		xbmc.executebuiltin( "Container.Refresh" )
	
	def _login(self, error = 0):
		if self.__dbg__:
			print self.__plugin__ + " login - errors: " + str(error)
			
		uname = self.__settings__.getSetting( "username" )
		passwd = self.__settings__.getSetting( "user_password" )
		
		self.__settings__.setSetting('auth', "")
		self.__settings__.setSetting('nick', "")
		
		if ( uname == "" or passwd == "" ):
			if self.__dbg__:
				print self.__plugin__ + " login no username or password set "
			return ( "", 0 )

		url = urllib2.Request(self.urls['gdata_login'])
		url.add_header('Content-Type', 'application/x-www-form-urlencoded')
		data = urllib.urlencode({'Email': uname, 'Passwd': passwd, 'service': 'youtube', 'source': 'YouTube plugin'})
		
		try:
			con = urllib2.urlopen(url, data);
			
			value = con.read()
			con.close()
			
			result = re.compile('Auth=(.*)').findall(value)
					
			if len(result) > 0:
				self.__settings__.setSetting('auth', result[0])

				if self.__dbg__:
					print self.__plugin__ + " login done: " + uname
				return ( self.__language__(30030), 200 )
					
			return ( self.__language__(30609), 303 )
			
		except urllib2.HTTPError, e:
			err = str(e)
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit http error except: " + err
			if e.code == 403:
				return ( self.__language__(30621), 303 )
			return ( err, 303 )
		
		except ValueError, e:
			err = repr(e)
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit valueerror except: " + err
			return ( err, 303 )
		
		except IOError, e:
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit ioerror except: " + repr(e)
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				print self.__utils__.interrogate(e)

			if error < 9:
				if self.__dbg__:
					print self.__plugin__ + " login pre sleep"
				# Check if there is a timeout here.
				import time
				time.sleep(3)
				if self.__dbg__:
					print self.__plugin__ + " login post sleep"
				return self._login( error + 1 )
			return ( self.__language__(30623), 303 )
		
		except urllib2.URLError, e:
			err = repr(e)
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit url error except: " + err
			return ( err, 303 )										
		except:
			if self.__dbg__:
				print self.__plugin__ + " login failed uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
			return ( self.__language__(30609), 500 )
	
	def createUrl(self, params):
		url = ""
		return url
		
	def _getAuth(self):
		if self.__dbg__:
			print self.__plugin__ + " _getAuth"

		auth = self.__settings__.getSetting( "auth" )

		if ( auth ):
			if self.__dbg__:
				print self.__plugin__ + " _getAuth returning stored auth"
			return auth
		else:
			(result, status ) =  self.login()
			if status == 200:
				if self.__dbg__:
					print self.__plugin__ + " _getAuth returning new auth"
				
				return self.__settings__.getSetting( "auth" )
		
		if self.__dbg__:
			print self.__plugin__ + " _getAuth failed because login failed"
		
		return False
				
	def _httpLogin(self, new = False, error = 0):
		if self.__dbg__:
			print self.__plugin__ + " _httpLogin errors: " + str(error)
		result = ""
		status = 200
		
		uname = self.__settings__.getSetting( "username" )
		pword = self.__settings__.getSetting( "user_password" )
		
		if ( uname == "" and pword == "" ):
			return ""

		if ( new ):
			self.__settings__.setSetting( "login_info", "" )
		elif ( self.__settings__.getSetting( "login_info" ) != "" ):
			if self.__dbg__:
				print self.__plugin__ + " returning existing login info: " + self.__settings__.getSetting( "login_info" )
			return self.__settings__.getSetting( "login_info" )
		
		cj = cookielib.LWPCookieJar()
		
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
		urllib2.install_opener(opener)
		
		# Get GALX
		url = urllib2.Request(urllib.unquote("https://www.google.com/accounts/ServiceLogin?service=youtube"))
		url.add_header('User-Agent', self.USERAGENT)
		
		if self.__dbg__:
			print self.__plugin__ + " _httpLogin: getting new login_info"
		con = urllib2.urlopen(url)
		header = con.info()
		galx = re.compile('Set-Cookie: GALX=(.*);Path=/accounts;Secure').findall(str(header))[0]
		
		if self.__dbg__:
			print self.__plugin__ + " galx: " + repr(galx)
		
		cont = urllib.unquote("http%3A%2F%2Fwww.youtube.com%2Fsignin%3Faction_handle_signin%3Dtrue%26nomobiletemp%3D1%26hl%3Den_US%26next%3D%252Findex&hl=en_US&ltmpl=sso")
		if self.__dbg__:
			print self.__plugin__ + " cont_url = " + cont
		
		params = urllib.urlencode({'GALX': galx,
					   'Email': uname,
					   'Passwd': pword,
					   'PersistentCookie': 'yes',
					   'continue': cont})
		
		# Login to Google
		url = urllib2.Request('https://www.google.com/accounts/ServiceLoginAuth?service=youtube', params)
		url.add_header('User-Agent', self.USERAGENT)
		
		con = urllib2.urlopen(url)
		result = con.read()
			
		# Login to youtube
		newurl = re.compile('<meta http-equiv="refresh" content="0; url=&#39;(.*)&#39;"></head>').findall(result)[0].replace("&amp;", "&")
		if self.__dbg__:
			print self.__plugin__ + " new_url: " + repr(newurl)
		
		url = urllib2.Request(newurl)
		url.add_header('User-Agent', self.USERAGENT)
		
		con = urllib2.urlopen(newurl)
		result = con.read()
		con.close()

		# We need to do this twice now.
		newurl = re.compile('<meta http-equiv="refresh" content="0; url=&#39;(.*)&#39;"></head>').findall(result)[0].replace("&amp;", "&")
		if self.__dbg__:
			print self.__plugin__ + " new_url: " + repr(newurl)
		
		url = urllib2.Request(newurl)
		url.add_header('User-Agent', self.USERAGENT)
		
		con = urllib2.urlopen(newurl)
		result = con.read()
		con.close()
		
		if self.__dbg__:
			print self.__plugin__ + " searching for nick "
		
		nick = ""
		if result.find("USERNAME', ") > 0:
			nick = result[result.find("USERNAME', ") + 12:]
			nick = nick[:nick.find('")')]
		
		if nick:
			self.__settings__.setSetting("nick", nick)
		else:
			status = 303
			print self.__plugin__ + " _httpLogin failed to get usename from youtube"
		
		# Save cookiefile in settings
		if self.__dbg__:
			print self.__plugin__ + " _httpLogin scanning cookies for login info: "
		
		login_info = ""
		cookies = repr(cj)
			
		if cookies.find("name='LOGIN_INFO', value='") > 0:
			start = cookies.find("name='LOGIN_INFO', value='") + len("name='LOGIN_INFO', value='")
			login_info = cookies[start:cookies.find("', port=None", start)]
		
		if login_info:
			self.__settings__.setSetting( "login_info", login_info )
		else:
			status = 303
		
		if self.__dbg__:
			print self.__plugin__ + " _httpLogin done : " + str(status) + " - " + login_info
		
		result = self.__settings__.getSetting( "login_info" )
		
		return (result, status)
