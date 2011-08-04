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

import sys, urllib, urllib2, re, os, cookielib, string
from xml.dom.minidom import parseString

# ERRORCODES:
# 0 = Ignore
# 200 = OK
# 303 = See other (returned an error message)
# 500 = uncaught error

class YouTubeCore(object):
	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__" ].__plugin__
	__dbg__ = sys.modules[ "__main__" ].__dbg__
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
		
	def interrogate(self, item):
		"""Print useful information about item."""
		if hasattr(item, '__name__'):
			print "NAME:    ", item.__name__
		if hasattr(item, '__class__'):
			print "CLASS:   ", item.__class__.__name__
		print "ID:      ", id(item)
		print "TYPE:    ", type(item)
		print "VALUE:   ", repr(item)
		print "CALLABLE:",
		if callable(item):
			print "Yes"
		else:
			print "No"
		
		if hasattr(item, '__doc__'):
			doc = getattr(item, '__doc__')
			if doc:
				doc = doc.strip() # Remove leading/trailing whitespace.
				firstline = doc.split('\n')[0]
				print "DOC:     ", firstline

	def login(self, error = 0):
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

		url = urllib2.Request("https://www.google.com/youtube/accounts/ClientLogin")

		url.add_header('Content-Type', 'application/x-www-form-urlencoded')
		url.add_header('GData-Version', '2')
		
		data = urllib.urlencode({'Email': uname, 'Passwd': passwd, 'service': 'youtube', 'source': 'YouTube plugin'})
		
		try:
			con = urllib2.urlopen(url, data);
			
			value = con.read()
			con.close()
		
			result = re.compile('Auth=(.*)\nYouTubeUser=(.*)').findall(value)
					
			if len(result) > 0:
				( auth, nick ) = result[0]
				self.__settings__.setSetting('auth', auth)
				self.__settings__.setSetting('nick', nick)

				if self.__dbg__:
					print self.__plugin__ + " login done: " + nick
				return ( self.__language__(30030), 200 )
					
			return ( self.__language__(30609), 303 )
			
		except urllib2.HTTPError, e:
			err = str(e)
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit http except: " + err
			if e.code == 403:
				return ( self.__language__(30621), 303 )
			return ( err, 303 )
		
		except ValueError, e:
			err = repr(e)
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit valueerror except: " + err
			return ( err, 303 )
		
		except IOError, e:
			# http://bytes.com/topic/python/answers/33770-error-codes-urlerror
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit ioerror except2: : " + repr(e)
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				print self.interrogate(e)

			if error < 9:
				if self.__dbg__:
					print self.__plugin__ + " login pre sleep"
				# Check if there is a timeout here.
				import time
				time.sleep(3)
				if self.__dbg__:
					print self.__plugin__ + " login post sleep"
				return self.login( error + 1 )
			return ( self.__language__(30623), 303 )
		
		except urllib2.URLError, e:
			err = repr(e)
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit url except: " + err
			return ( err, 303 )										
		except:
			if self.__dbg__:
				print self.__plugin__ + " login failed uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
			return ( self.__language__(30609), 500 )
	
	def search(self, query, page = "0"):
		if self.__dbg__:
			print self.__plugin__ + " search: " + repr(query) + " - page: " + repr(page)
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]
		safe_search = ("none", "moderate", "strict" ) [int( self.__settings__.getSetting( "safe_search" ) ) ]
		start_index = per_page * int(page) + 1
	

		link = "http://gdata.youtube.com/feeds/api/videos?q=%s&safeSearch=%s&start-index=%s&max-results=%s" % ( urllib.quote_plus(query), safe_search, start_index, per_page)
		authors = self.__settings__.getSetting("stored_searches_author")
		
		if len(authors) > 0:
			try:
				authors = eval(authors)
				if query in authors:
					link += "&" + urllib.urlencode({'author': authors[query]})
			except:
				print self.__plugin__ + " search - eval failed "
				
		( result, status ) = self._fetchPage(link, api = True)

		if status != 200:
			return ( result, status )

		result = self._getvideoinfo(result)
		
		if len(result) > 0:
			if self.__dbg__:
				print self.__plugin__ + " search done :" + str(len(result))
			return (result, 200)
		else:
			if self.__dbg__:
				print self.__plugin__ + " search done with no results"
			return (self.__language__(30601), 303)

	def feeds(self, feed, params ={} ):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " feeds : " + repr(feed) + " page: " + repr(get("page","0"))
		result = ""
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]
		
		if (feed.find("%s") > 0 ):
			time = ( "all_time", "today", "this_week", "this_month") [ int(self.__settings__.getSetting( "feed_time" ) ) ]
			feed = feed % time
		
		if ( feed.find("?") == -1 ):
			feed += "?"
		else:
			feed += "&"
			
		feed += "start-index=" + str( per_page * int(get("page","0")) + 1) + "&max-results=" + repr(per_page)
			
		if (feed.find("standardfeeds") > 0):
			region = ('', 'AU', 'BR', 'CA', 'CZ', 'FR', 'DE', 'GB', 'NL', 'HK', 'IN', 'IE', 'IL', 'IT', 'JP', 'MX', 'NZ', 'PL', 'RU', 'KR', 'ES','SE', 'TW', 'US', 'ZA' )[ int( self.__settings__.getSetting( "region_id" ) ) ]
			if (region):
				feed = feed.replace("/standardfeeds/", "/standardfeeds/"+ region + "/")

		( result, status ) = self._fetchPage(feed, api = True)

		if status != 200:
			return ( result, status )

		result = self._getvideoinfo(result)
					
		if len(result) > 0:
			if self.__dbg__:
				print self.__plugin__ + " feeds done : " + str(len(result))
			return ( result, 200 )
		else:
			if self.__dbg__:
				print self.__plugin__ + " feeds done with no results"
			return (self.__language__(30602), 303)
	
	def list(self, feed, params ={}):
		get = params.get
		page = get("page","0")
		if self.__dbg__:
			print self.__plugin__ + " list: " + repr(feed) + " - page: " + repr(page)
		result = ""
		auth = self._getAuth()
		if ( not auth ):
			if self.__dbg__:
				print self.__plugin__ + " playlists auth wasn't set "
			return ( self.__language__(30609) , 303 )
		
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]
	
		if ( feed.find("?") == -1 ):
			feed += "?"
		else:
			feed += "&"

		feed += "start-index=" + str( per_page * int(page) + 1) + "&max-results=" + repr(per_page)
		feed = feed.replace(" ", "+")
		
		( result, status ) = self._fetchPage(feed, auth = True)

		if status != 200:
			return ( result, status)

		result = self._getvideoinfo(result)

		if len(result) > 0:
			if self.__dbg__:
				print self.__plugin__ + " list done :" + str(len(result))
			return (result, 200)
		else:
			if self.__dbg__:
				print self.__plugin__ + " list done with no results"
			return (self.__language__(30602), 303)

	def delete_favorite(self, obj):
		delete_url = "http://gdata.youtube.com/feeds/api/users/%s/favorites/%s" % ( self.__settings__.getSetting( "nick" ), obj )
		return self._youTubeDel(delete_url)
	
	def remove_contact(self, obj):
		delete_url = "http://gdata.youtube.com/feeds/api/users/default/contacts/%s" % obj
		return self._youTubeDel(delete_url)

	def remove_subscription(self, obj):
		delete_url = "http://gdata.youtube.com/feeds/api/users/%s/subscriptions/%s" % ( self.__settings__.getSetting( "nick" ), obj )
		print self.__plugin__ + "remove : " + delete_url
		return self._youTubeDel(delete_url)

	def add_contact(self, contact_id):
		url = "http://gdata.youtube.com/feeds/api/users/default/contacts"
		add_request = '<?xml version="1.0" encoding="UTF-8"?> <entry xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://gdata.youtube.com/schemas/2007"><yt:username>%s</yt:username></entry>' % contact_id
		return self._youTubeAdd(url, add_request)
		
	def add_favorite(self, video_id):
		url = "http://gdata.youtube.com/feeds/api/users/default/favorites"
		add_request = '<?xml version="1.0" encoding="UTF-8"?><entry xmlns="http://www.w3.org/2005/Atom"><id>%s</id></entry>' % (video_id)
		return self._youTubeAdd(url, add_request)

	def add_subscription(self, user_id):
		url = "http://gdata.youtube.com/feeds/api/users/default/subscriptions"
		add_request = '<?xml version="1.0" encoding="UTF-8"?><entry xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://gdata.youtube.com/schemas/2007"> <category scheme="http://gdata.youtube.com/schemas/2007/subscriptiontypes.cat" term="user"/><yt:username>%s</yt:username></entry>' % (user_id)
		return self._youTubeAdd(url, add_request)

	def playlists(self, link, params = {}):
		get = params.get
		if self.__dbg__:
			print self.__plugin__ + " playlists " + repr(link) + " - page: " + repr(get("page","0"))
		result = ""

		auth = self._getAuth()
		if ( not auth ):
			if self.__dbg__:
				print self.__plugin__ + " playlists auth wasn't set "
			return ( self.__language__(30609) , 303 )
		
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]
		if ( link.find("?") == -1 ):
			link += "?"
		else:
			link += "&"
		link += "start-index=" + str( per_page * int(get("page","0")) + 1) + "&max-results=" + repr(per_page)
		
		if get("feed") == "playlists" or get("feed") == "subscriptions":
			link += "&orderby=published"


		( result, status ) = self._fetchPage(link, auth = True)

		if status != 200:
			return ( result, status )
		
		dom = parseString(result);
		links = dom.getElementsByTagName("link");
		entries = dom.getElementsByTagName("entry");
		next = "false"

		#find out if there are more pages
		if (len(links)):
			for link in links:
				lget = link.attributes.get
				if (lget("rel").value == "next"):
					next = "true"
					break
		
		playobjects = [];
		for node in entries:
			video = {};
			video['Title'] = node.getElementsByTagName("title").item(0).firstChild.nodeValue.replace('Activity of : ', '').replace('Videos published by : ', '').encode( "utf-8" );
			
			video['published'] = self._getNodeValue(node, "published", "2008-07-05T19:56:35.000-07:00")
			video['summary'] = self._getNodeValue(node, 'summary', 'Unknown')
			video['content'] = self._getNodeAttribute(node, 'content', 'src', 'FAIL')
			video['playlistId'] = self._getNodeValue(node, 'yt:playlistId', '')
			
			if node.getElementsByTagName("link"):
				link = node.getElementsByTagName("link")
				for i in range(len(link)):
					if link.item(i).getAttribute('rel') == 'edit':
						obj = link.item(i).getAttribute('href')
						video['editid'] = obj[obj.rfind('/')+1:]
			
			playobjects.append(video);
			
		if len(playobjects) > 0:
			playobjects[len(playobjects) - 1]['next'] = next
			
		if self.__dbg__:
			print self.__plugin__ + " playlist done"
				
		return ( playobjects, 200 );
	
	def downloadVideo(self, video):
		if self.__dbg__:
			print self.__plugin__ + " downloadVideo : " + video['Title']
			
		path = self.__settings__.getSetting( "downloadPath" )
		try:
			url = urllib2.Request(video['video_url'])
			url.add_header('User-Agent', self.USERAGENT);
			valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
			
			filename_incomplete = "%s/%s-incomplete.mp4" % ( path, ''.join(c for c in video['Title'] if c in valid_chars) )
			filename_complete = "%s/%s.mp4" % ( path, ''.join(c for c in video['Title'] if c in valid_chars) )
			file = open(filename_incomplete, "wb")
			con = urllib2.urlopen(url);
			file.write(con.read())
			con.close()
			file.close()
			
			os.rename(filename_incomplete, filename_complete)
			
			self.__settings__.setSetting( "vidstatus-" + video['videoid'], "1" )
		except urllib2.HTTPError, e:
			if self.__dbg__:
				print self.__plugin__ + " downloadVideo except: " + str(e)
			return ( str(e), 303 )
		except:
			if self.__dbg__:
				print self.__plugin__ + " downloadVideo uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__, sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				
			return (self.__language__(30606), 303)

		if self.__dbg__:
			print self.__plugin__ + " downloadVideo done"
		return ( video, 200 )
	
	def arrayToPipe(self, input):
		pipedItems = ""
		for item in input:
			pipedItems += item + "|"
		return pipedItems

	def _get_batch_details_thumbnails(self, items):
		request_start = "<feed xmlns='http://www.w3.org/2005/Atom'\n xmlns:media='http://search.yahoo.com/mrss/'\n xmlns:batch='http://schemas.google.com/gdata/batch'\n xmlns:yt='http://gdata.youtube.com/schemas/2007'>\n <batch:operation type='query'/> \n"
		request_end = "</feed>"
		
		video_request = ""
		
		ytobjects = []
		i = 1
		for (videoid, thumbs) in items:
			if videoid:
				video_request +=	"<entry> \n <id>http://gdata.youtube.com/feeds/api/videos/" + videoid+ "</id>\n</entry> \n"
				if i == 50:
					final_request = request_start + video_request + request_end
					request = urllib2.Request("http://gdata.youtube.com/feeds/api/videos/batch")
					request.add_data(final_request)
					con = urllib2.urlopen(request)
					result = con.read()
					(temp, status) = self._getVideoInfoBatch(result)
					ytobjects += temp
					if status != 200:
						return (ytobjects, status)
					video_request = ""
					i = 1
				i+=1
		
		
		final_request = request_start + video_request + request_end
		request = urllib2.Request("http://gdata.youtube.com/feeds/api/videos/batch")
		request.add_data(final_request)
					
		con = urllib2.urlopen(request)
		result = con.read()
				
		(temp, status) = self._getVideoInfoBatch(result)
		ytobjects += temp
		
		tempobjects = ytobjects
		ytobjects = []
		for i in range(0, len(items)):
			( videoid, thumbnail ) = items[i]
			for item in tempobjects:
				if item['videoid'] == videoid:
					item['thumbnail'] = thumbnail
					ytobjects.append(item)					

		while len(items) > len(ytobjects):
			ytobjects.append({'videoid': 'false'});
		
		return ( ytobjects, 200)
	
	def _get_batch_details(self, items):
		request_start = "<feed xmlns='http://www.w3.org/2005/Atom'\n xmlns:media='http://search.yahoo.com/mrss/'\n xmlns:batch='http://schemas.google.com/gdata/batch'\n xmlns:yt='http://gdata.youtube.com/schemas/2007'>\n <batch:operation type='query'/> \n"
		request_end = "</feed>"
		
		video_request = ""
		
		ytobjects = []
		i = 1
		for videoid in items:
			if videoid:
				video_request +=	"<entry> \n <id>http://gdata.youtube.com/feeds/api/videos/" + videoid+ "</id>\n</entry> \n"
				if i == 50:
					final_request = request_start + video_request + request_end
					request = urllib2.Request("http://gdata.youtube.com/feeds/api/videos/batch")
					request.add_data(final_request)
					con = urllib2.urlopen(request)
					result = con.read()
					(temp, status) = self._getVideoInfoBatch(result)
					ytobjects += temp
					if status != 200:
						return (ytobjects, status)
					video_request = ""
					i = 1
				i+=1
		
		
		final_request = request_start + video_request + request_end
		request = urllib2.Request("http://gdata.youtube.com/feeds/api/videos/batch")
		request.add_data(final_request)
					
		con = urllib2.urlopen(request)
		result = con.read()
				
		(temp, status) = self._getVideoInfoBatch(result)
		ytobjects += temp
				
		return ( ytobjects, 200)
		
	#===============================================================================
	#
	# Internal functions to YouTubeCore.py
	#
	# Return should be value(True for bool functions), or False if failed.
	#
	# False MUST be handled properly in External functions
	#
	#===============================================================================

	def _fetchPage(self, link, api = False, auth=False, login=False, error = 0):
		if self.__dbg__:
			print self.__plugin__ + " fetching page : " + link

		request = urllib2.Request(link)

		if api:
			request.add_header('GData-Version', '2')
		else:
			request.add_header('User-Agent', self.USERAGENT)

		if ( login ):
			if ( self.__settings__.getSetting( "username" ) == "" or self.__settings__.getSetting( "user_password" ) == "" ):
				if self.__dbg__:
					print self.__plugin__ + " _fetchPage, login required but no credentials provided"
				return ( self.__language__( 30608 ) , 303 )

			if self.__dbg__:
				print self.__plugin__ +  " _fetchPage adding cookie"
			request.add_header('Cookie', 'LOGIN_INFO=' + self._httpLogin() )
		
		if auth:
			authkey = self._getAuth()
			if ( not authkey ):
				if self.__dbg__:
					print self.__plugin__ + " _fetchPage couldn't set auth "
				
			request.add_header('Authorization', 'GoogleLogin auth=' + authkey)
			request.add_header('X-GData-Key', 'key=' + self.APIKEY)
		
		try:
			con = urllib2.urlopen(request)
			result = con.read()
			new_url = con.geturl()
			con.close()
			
			# Return result if it isn't age restricted
			if ( result.find("verify-actions") == -1 and result.find("verify-age-actions") == -1):
				return ( result, 200 )
			elif ( error < 10 ):
				# We need login to verify age.	     
				if not login:
					if self.__dbg__:
						print self.__plugin__ + " _fetchPage age verification required, retrying with login"
					error = error + 0
					return self._fetchPage(link, api, auth, login = True, error = error)
				
				if self.__dbg__:
					print self.__plugin__ + " _fetchPage verifying age"
				return self._verifyAge(result, new_url, link, api, auth, login, error) 
			
			if self.__dbg__:
				print self.__plugin__ + " _fetchPage. Too many errors"
			return ( "", 500 )
		
		except urllib2.HTTPError, e:
			err = str(e)
			if self.__dbg__:
				print self.__plugin__ + " _fetchPage HTTPError : " + err
			
			# 400 (Bad request) - A 400 response code indicates that a request was poorly formed or contained invalid data. The API response content will explain the reason wny the API returned a 400 response code.
			if ( err.find("400") > -1 ):
				return ( err, 303 )
			# 401 (Not authorized) - A 401 response code indicates that a request did not contain an Authorization header, that the format of the Authorization header was invalid, or that the authentication token supplied in the header was invalid.
			elif ( err.find("401") > -1 ):
				# If login credentials are given, try again.
				if ( self.__settings__.getSetting( "username" ) == "" or self.__settings__.getSetting( "user_password" ) == "" ):
					if self.__dbg__:
						print self.__plugin__ + " _fetchPage trying again with login "

					self.login()
					return self._fetchPage(link, api, auth, login, error +1)
				else:
					if self.__dbg__:
						print self.__plugin__ + " _fetchPage 401 Not Authorized and no login credentials written in settings"
					return ( self.__language__(30622), 303)
			# 403 (Forbidden) - A 403 response code indicates that you have submitted a request that is not properly authenticated for the requested operation.
			# Test all cases that cause 403 before 2.0, and verify the above statement.
			elif ( err.find("403") > -1 ):
				if self.__dbg__:
					print self.__plugin__ + " _fetchPage got empty results back "
				return (self.__language__(30601), 303)
			# 501 (Not implemented) - A 501 response code indicates that you have tried to execute an unsupported operation.
			elif ( err.find("501") > -1):
				return ( err, 303 )
			#500 (Internal error) - A 500 response code indicates that YouTube experienced an error handling a request. You could retry the request at a later time.
			#503 (Service unavailable) - A 503 response code indicates that the YouTube Data API service can not be reached. You could retry your request at a later time.
			elif ( err.find("500") > -1 or err.find("503") > -1 ):
				if self.__dbg__:
					print self.__plugin__ + " _fetchPage retry: " + error
				return self._fetchPage(link, api, auth, login, error +1)
			else:
				if self.__dbg__:
					print self.__plugin__ + " _fetchPage unknown error"
				return ( err, 303 )
							
		except:
			if self.__dbg__:
				print self.__plugin__ + ' _fetchPage ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
												 , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				
			return ( "", 500 )
			
	def _verifyAge(self, result, new_url, link, api = False, auth=False, login=False, error = 0):
		login_info = self._httpLogin(True)
		confirmed = "0"
		if self.__settings__.getSetting( "safe_search" ) != "2":
			confirmed = "1"
		
		request = urllib2.Request(new_url)
		request.add_header('User-Agent', self.USERAGENT)
		request.add_header('Cookie', 'LOGIN_INFO=' + login_info)
		con = urllib2.urlopen(request)
		result = con.read()
		
		# Fallback for missing confirm form.
		if result.find("confirm-age-form") == -1:
			if self.__dbg__ or True:
				print self.__plugin__ + " Failed trying to verify-age could find confirm age form."
				print self.__plugin__ + " html page given: " + repr(result)
			return ( self.__language__( 30600 ) , 303 )
						
		# get next_url
		next_url_start = result.find('"next_url" value="') + len('"next_url" value="')
		next_url_stop = result.find('">',next_url_start)
		next_url = result[next_url_start:next_url_stop]
		
		if self.__dbg__:
			print self.__plugin__ + " next_url=" + next_url
		
		# get session token to get around the cross site scripting prevetion
		session_token_start = result.find("'XSRF_TOKEN': '") + len("'XSRF_TOKEN': '")
		session_token_stop = result.find("',",session_token_start) 
		session_token = result[session_token_start:session_token_stop]
		
		if self.__dbg__:
			print self.__plugin__ + " session_token=" + session_token
		
		# post collected information to age the verifiaction page
		request = urllib2.Request(new_url)
		request.add_header('User-Agent', self.USERAGENT)
		request.add_header('Cookie', 'LOGIN_INFO=' + login_info )
		request.add_header("Content-Type","application/x-www-form-urlencoded")
		values = urllib.urlencode( { "next_url": next_url, "action_confirm": confirmed, "session_token":session_token })
		
		if self.__dbg__:
			print self.__plugin__ + " post page content: " + values
		
		con = urllib2.urlopen(request, values)
		new_url = con.geturl()
		result = con.read()
		con.close()
		
		#If verification is success full new url must look like: 'http://www.youtube.com/index?has_verified=1'
		if new_url.find("has_verified=1") > 0:
			if self.__dbg__:
				print self.__plugin__ + " Age Verification sucessfull " + new_url
			return self._fetchPage(link, api, auth, login = True, error = error + 1)
		
		# If verification failed we dump a shit load of info to the logs
		print self.__plugin__ + " age verification failed with result: " + repr(result)
		print self.__plugin__ + " result url: " + repr(new_url)
		return (self.__language__(30600), 303)

		
	def _extractVariables(self, videoid):
		if self.__dbg__:
			print self.__plugin__ + " extractVariables : " + repr(videoid)

		( htmlSource, status ) = self._fetchPage('http://www.youtube.com/watch?v=' +videoid + "&safeSearch=none&hl=en_us")

		if status != 200:
			return ( htmlSource, status, status )
		
		if self.__dbgv__:
			print self.__plugin__ + " _extractVariables result: " + repr(htmlSource)

		swf_url = False
		fmtSource = re.findall('"fmt_url_map": "([^"]+)"', htmlSource);
		if fmtSource:
			stream_map = "False"
		else:
			swfConfig = re.findall('var swfConfig = {"url": "(.*)", "min.*};', htmlSource)
			if len(swfConfig) > 0:
				swf_url = swfConfig[0].replace("\\", "")
				
			fmtSource = re.findall('"fmt_stream_map": "([^"]+)"', htmlSource);
			stream_map = 'True'
			
		if self.__dbg__:
			print self.__plugin__ + " extractVariables done"
				
		return (fmtSource, swf_url, stream_map)

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
			else:
				if self.__dbg__:
					print self.__plugin__ + " _getAuth failed because login failed"
				return False
	
	def _youTubeAdd(self, url, add_request, retry = True):
		if self.__dbg__:
			print self.__plugin__ + " _youTubeAdd: " + repr(url) + " add_request " + repr(add_request)
		auth = self._getAuth()
		if ( not auth ):
			if self.__dbg__:
				print self.__plugin__ + " playlists auth wasn't set "
			return ( self.__language__(30609) , 303 )
		
		try:
			request = urllib2.Request(url, add_request)
			request.add_header('Authorization', 'GoogleLogin auth=%s' % auth)
			request.add_header('X-GData-Client', "")
			request.add_header('X-GData-Key', 'key=%s' % self.APIKEY)
			request.add_header('Content-Type', 'application/atom+xml')
			request.add_header('Content-Length', str(len(add_request)))
			request.add_header('GData-Version', '2')
			usock = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			error = str(e)
			if self.__dbg__:
				print self.__plugin__ + " _youTubeAdd exception: " + error
				
			if ( error.find("201") > -1):
				if self.__dbg__:
					print self.__plugin__ + " _youTubeAdd: Done"
				return ( "", 200)
			elif (error.find("503") > -1):
				if self.__dbg__:
					print self.__plugin__ + " _youTubeAdd: " + self.__language__(30615)
				return ( self.__language__(30615), 303 )
			elif ( error.find("401") > -1 and retry):
				# If login credentials are given, try again.
				if ( self.__settings__.getSetting( "username" ) == "" or self.__settings__.getSetting( "user_password" ) == "" ):
					if self.__dbg__:
						print self.__plugin__ + " _youTubeAdd trying again with login "
						
					self.login()
					#def _fetchPage(self, link, api = False, auth=False, login=False, error = 0):
					return self._youTubeAdd(url, add_request, False)
					#return self._fetchPage(link, api, auth, login, error + 1)
				else:
					if self.__dbg__:
						print self.__plugin__ + " _youTubeAdd 401 Not Authorized and no login credentials written in settings"
					return ( self.__language__(30622), 303)
			else:
				if self.__dbg__:
					print self.__plugin__ + " _youTubeAdd error not caught " 
				return ( error, 303 )
	
	def _youTubeDel(self, delete_url, retry = True):
		if self.__dbg__:
			print self.__plugin__ + " _youTubeDel: " + delete_url

		auth = self._getAuth()
		if ( not auth ):
			if self.__dbg__:
				print self.__plugin__ + " _youTubeDel auth wasn't set "
			return ( self.__language__(30609) , 303 )

		try:
			headers = {}
			headers['Authorization'] = 'GoogleLogin auth=%s' % (auth)
			headers['X-GData-Client'] = ""
			headers['X-GData-Key'] = 'key=%s' % self.APIKEY
			headers['Content-Type'] = 'application/atom+xml'
			headers['Host'] = 'gdata.youtube.com'
			headers['GData-Version'] = '2'
			import httplib
			conn = httplib.HTTPConnection('gdata.youtube.com')
			conn.request('DELETE', delete_url, headers=headers)
			response = conn.getresponse()
			if (response.status == 200):
				if self.__dbg__:
					print self.__plugin__ + " _youTubeDel: done"
				return ( "", 200 )
			elif (response.status == 401 and retry):
				# If login credentials are given, try again.
				if ( self.__settings__.getSetting( "username" ) == "" or self.__settings__.getSetting( "user_password" ) == "" ):
					if self.__dbg__:
						print self.__plugin__ + " _youTubeDel trying again with login "
						
					self.login()
					return self._youTubeDel(delete_url, False);
					#return self._fetchPage(link, api, auth, login, error +1)
				else:
					if self.__dbg__:
						print self.__plugin__ + " _youTubeDel 401 Not Authorized and no login credentials written in settings"
					return ( self.__language__(30622), 303)
			else:
				resp = str(response.read())
				if self.__dbg__:
					print self.__plugin__ + " _youTubeDel: [%s] %s" % ( response.status, resp )
				return ( resp, 303 )
		except urllib2.HTTPError, e:
			if self.__dbg__:
				print self.__plugin__ + " _youTubeDel except: " + str(e)
			return ( str(e), 303 )
		except:
			if self.__dbg__:
				print self.__plugin__ + " _youTubeDel uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				
			return ( "", 500 )
	
	def _getNodeAttribute(self, node, tag, attribute, default = ""):
		if node.getElementsByTagName(tag).item(0):
			if node.getElementsByTagName(tag).item(0).hasAttribute(attribute):
				return node.getElementsByTagName(tag).item(0).getAttribute(attribute)

		return default;
	
	def _getNodeValue(self, node, tag, default = ""):
		if node.getElementsByTagName(tag).item(0):
			if node.getElementsByTagName(tag).item(0).firstChild:
				return node.getElementsByTagName(tag).item(0).firstChild.nodeValue
		
		return default;

	def _getVideoInfoBatch(self, value):
		if self.__dbg__:
			print self.__plugin__ + " _getvideoinfo: " + str(len(value))
		
		dom = parseString(value);
		links = dom.getElementsByTagName("atom:link");
		entries = dom.getElementsByTagName("atom:entry");
		next = "false"
			
		if (len(links)):
			for link in links:
				lget = link.attributes.get
				if (lget("rel").value == "next"):
					next = "true"
					break

		ytobjects = [];
		for node in entries:
			video = {};
			videoid = self._getNodeValue(node, "atom:id", "")
			
			if (not videoid):
				if node.getElementsByTagName("link").item(0):
					videoid = node.getElementsByTagName("link").item(0).getAttribute('href')
					match = re.match('.*?v=(.*)\&.*', videoid)
					if match:
						videoid = match.group(1)
			
			if (videoid):
				if (videoid.rfind("/") != -1):
					video['videoid'] = videoid[videoid.rfind("/") + 1:]
					
				if node.getElementsByTagName("yt:state").item(0):
					state = self._getNodeAttribute(node, "yt:state", 'name', 'Unknown Name')
	
					if ( state == 'deleted' or state == 'rejected'):
						video['videoid'] = "false"
						
					# Get reason for why we can't playback the file.		
					if node.getElementsByTagName("yt:state").item(0).hasAttribute('reasonCode'):
						reason = self._getNodeAttribute(node, "yt:state", 'reasonCode', 'Unknown reasonCode')
						value = self._getNodeValue(node, "yt:state", "Unknown reasonValue").encode('utf-8')
						if reason == "private":
							video['videoid'] = "false"
						elif reason == 'requesterRegion':
							video['videoid'] = "false"
						elif reason == 'limitedSyndication':
							if self.__dbg__:
								print "" #print self.__plugin__ + " _getvideoinfo hit limitedsyndication"
						else:
							video['videoid'] = "false";
				
				video['Title'] = self._getNodeValue(node, "media:title", "Unknown Title").encode('utf-8') # Convert from utf-16 to combat breakage
				video['Plot'] = self._getNodeValue(node, "media:description", "Unknown Plot").encode( "utf-8" )
				video['Date'] = self._getNodeValue(node, "atom:published", "Unknown Date").encode( "utf-8" )
				video['user'] = self._getNodeValue(node, "atom:name", "Unknown Name").encode( "utf-8" )
				
				# media:credit is not set for favorites, playlists or inbox
				video['Studio'] = self._getNodeValue(node, "media:credit", "").encode( "utf-8" )
				if video['Studio'] == "":
					video['Studio'] = self._getNodeValue(node, "atom:name", "Unknown Uploader").encode( "utf-8" )
					
	
				duration = int(self._getNodeAttribute(node, "yt:duration", 'seconds', '0'))
				video['Duration'] = "%02d:%02d" % ( duration / 60, duration % 60 )
				video['Rating'] = float(self._getNodeAttribute(node,"gd:rating", 'average', "0.0"))
				video['count'] = int(self._getNodeAttribute(node, "yt:statistics", 'viewCount', "0"))
				video['Genre'] = self._getNodeAttribute(node, "media:category", "label", "Unknown Genre").encode( "utf-8" )
				infoString =""
				if video['Date'] != "Unknown Date":
					infoString += "Date Uploaded: " + video['Date'][:video['Date'].find("T")] + ", "				
				infoString += "View count: " + str(video['count'])
				
				if node.getElementsByTagName("atom:link"):
					link = node.getElementsByTagName("atom:link")
					for i in range(len(link)):
						if link.item(i).getAttribute('rel') == 'edit':
							obj = link.item(i).getAttribute('href')
							video['editid'] = obj[obj.rfind('/')+1:]
	
				video['thumbnail'] = "http://i.ytimg.com/vi/" + video['videoid'] + "/0.jpg"
				
				overlay = self.__settings__.getSetting( "vidstatus-" + video['videoid'] )
	
				if overlay:
					video['Overlay'] = int(overlay)
				
				video['next'] = next
				
				ytobjects.append(video);
					
		if (ytobjects):
			return (ytobjects, 200);
		
		return ( "", 500 )
	
	def _getvideoinfo(self, value):
		if self.__dbg__:
			print self.__plugin__ + " _getvideoinfo: " + str(len(value))
		try:
			dom = parseString(value);
			links = dom.getElementsByTagName("link");
			entries = dom.getElementsByTagName("entry");
			if (not entries):
				entries = dom.getElementsByTagName("atom:entry");
			next = "false"

			#find out if there are more pages
			
			if (len(links)):
				for link in links:
					lget = link.attributes.get
					if (lget("rel").value == "next"):
						next = "true"
						break

			#construct list of video objects					
			ytobjects = [];
			for node in entries:
				video = {};

				video['videoid'] = self._getNodeValue(node, "yt:videoid", "missing")
				
				# http://code.google.com/intl/en/apis/youtube/2.0/reference.html#youtube_data_api_tag_yt:state <- more reason codes
				# requesterRegion - This video is not available in your region. <- fails
				# limitedSyndication - Syndication of this video was restricted by its owner. <- works

				if node.getElementsByTagName("yt:state").item(0):
				
					state = self._getNodeAttribute(node, "yt:state", 'name', 'Unknown Name')

					# Ignore unplayable items.
					if ( state == 'deleted' or state == 'rejected'):
						video['videoid'] = "false"
					
					# Get reason for why we can't playback the file.		
					if node.getElementsByTagName("yt:state").item(0).hasAttribute('reasonCode'):
						reason = self._getNodeAttribute(node, "yt:state", 'reasonCode', 'Unknown reasonCode')
						value = self._getNodeValue(node, "yt:state", "Unknown reasonValue").encode('utf-8')
						if reason == "private":
							video['videoid'] = "false"
						elif reason == 'requesterRegion':
							video['videoid'] = "false"
						elif reason == 'limitedSyndication':
							if self.__dbg__:
								print "" #print self.__plugin__ + " _getvideoinfo hit limitedsyndication"
						else:
							if self.__dbg__:
								print self.__plugin__ + " _getvideoinfo hit else : %s - %s" % ( reason, value)
							video['videoid'] = "false";
							
				if ( video['videoid'] == "missing" ):
					video['videolink'] = node.getElementsByTagName("link").item(0).getAttribute('href')
					match = re.match('.*?v=(.*)\&.*', video['videolink'])
					if match:
						video['videoid'] = match.group(1)
					else:
						video['videoid'] = "false"
				
				video['Title'] = self._getNodeValue(node, "media:title", "Unknown Title").encode('utf-8') # Convert from utf-16 to combat breakage
				video['Plot'] = self._getNodeValue(node, "media:description", "Unknown Plot").encode( "utf-8" )
				video['Date'] = self._getNodeValue(node, "published", "Unknown Date").encode( "utf-8" )
				video['user'] = self._getNodeValue(node, "name", "Unknown Name").encode( "utf-8" )
				
				# media:credit is not set for favorites, playlists or inbox
				video['Studio'] = self._getNodeValue(node, "media:credit", "").encode( "utf-8" )
				if video['Studio'] == "":
					video['Studio'] = self._getNodeValue(node, "name", "Unknown Uploader").encode( "utf-8" )
					
					

				duration = int(self._getNodeAttribute(node, "yt:duration", 'seconds', '0'))
				video['Duration'] = "%02d:%02d" % ( duration / 60, duration % 60 )
				video['Rating'] = float(self._getNodeAttribute(node,"gd:rating", 'average', "0.0"))
				video['count'] = int(self._getNodeAttribute(node, "yt:statistics", 'viewCount', "0"))
				infoString =""
				if video['Date'] != "Unknown Date":
					infoString += "Date Uploaded: " + video['Date'][:video['Date'].find("T")] + ", "				
				infoString += "View count: " + str(video['count'])
				video['Plot'] = infoString + "\n" + video['Plot']
				video['Genre'] = self._getNodeAttribute(node, "media:category", "label", "Unknown Genre").encode( "utf-8" )

				if node.getElementsByTagName("link"):
					link = node.getElementsByTagName("link")
					for i in range(len(link)):
						if link.item(i).getAttribute('rel') == 'edit':
							obj = link.item(i).getAttribute('href')
							video['editid'] = obj[obj.rfind('/')+1:]

				video['thumbnail'] = "http://i.ytimg.com/vi/" + video['videoid'] + "/0.jpg"
			
				overlay = self.__settings__.getSetting( "vidstatus-" + video['videoid'] )

				if overlay:
					video['Overlay'] = int(overlay)
				
				video['next'] = next
				
				if video['videoid'] == "false":
					if self.__dbg__:
						print self.__plugin__ + " _getvideoinfo videoid set to false"
														
				
				ytobjects.append(video);

			if self.__dbg__:
				print self.__plugin__ + " _getvideoinfo done : " + str(len(ytobjects))
			return ytobjects;
		except:
			if self.__dbg__:
				print self.__plugin__ + " _getvideoinfo uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				
			return ( "", 500 )

	def _getAlert(self, videoid):
		if self.__dbg__:
			print self.__plugin__ + " _getAlert"

		http_result = self._fetchPage('http://www.youtube.com/watch?v=' +videoid + "&safeSearch=none", login = True)
		
		start = http_result.find('class="yt-alert-content">')
		if start == -1:
			return self.__language__(30622)
		
		start += len('class="yt-alert-content">')
		result = http_result[start: http_result.find('</div>', start)].strip()

		# Why doesn't this work?
		#result = result.replace("\n", "")
		#alert = re.compile('class="yt-alert-content">(.*)</div>', re.M).findall(result);

		if self.__dbg__:
			print self.__plugin__ + " _getAlert : " + repr(start)
			print self.__plugin__ + " _getAlert done"

		return result
	
	def _get_details(self, videoid):
		if self.__dbg__:
			print self.__plugin__ + " _get_details: " + repr(videoid)

		( result, status ) = self._fetchPage("http://gdata.youtube.com/feeds/api/videos/" + videoid, api = True)

		if status == 200:
			result = self._getvideoinfo(result)
		
			if len(result) == 0:
				if self.__dbg__:
					print self.__plugin__ + " _get_details result was empty"
				return False
			else:
				if self.__dbg__:
					print self.__plugin__ + " _get_details done"
				return result[0];
		else:
			if self.__dbg__:
				print self.__plugin__ + " _get_details got bad status: " + str(status)
			video = {}
			video['Title'] = "Error"
			video['videoid'] = videoid
			video['thumbnail'] = "Error"
			video['video_url'] = False

			if (status == 403):
				# Override the 403 passed from _fetchPage with error provided by youtube.
				video['apierror'] = self._getAlert(videoid)
				return video
			elif (status == 503):
				video['apierror'] = self.__language__(30605)
				return video
			else:
				video['apierror'] = self.__language__(30606) + str(status)
				return video
		
	def _httpLogin(self, new = False, error = 0):
		if self.__dbg__:
			print self.__plugin__ + " _httpLogin errors: " + str(error)

		uname = self.__settings__.getSetting( "username" )
		pword = self.__settings__.getSetting( "user_password" )
		
		if ( uname == "" and pword == "" ):
			return ""

		if ( new ):
			if self.__dbg__:
				print self.__plugin__ + " _httpLogin clearing login_info"
			self.__settings__.setSetting( "login_info", "" )
		elif ( self.__settings__.getSetting( "login_info" ) != "" ):
			if self.__dbg__:
				print self.__plugin__ + " _httpLogin returning stored login_info"
				
			return self.__settings__.getSetting( "login_info" )
								
		cj = cookielib.LWPCookieJar()
		
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
		urllib2.install_opener(opener)

		# Get GALX
		url = urllib2.Request(urllib.unquote("https://www.google.com/accounts/ServiceLogin?service=youtube"))
		url.add_header('User-Agent', self.USERAGENT)

		try:
			if self.__dbg__:
				print self.__plugin__ + " _httpLogin: getting new login_info"
			con = urllib2.urlopen(url)
			header = con.info()
			galx = re.compile('Set-Cookie: GALX=(.*);Path=/accounts;Secure').findall(str(header))[0]

			cont = urllib.unquote("http%3A%2F%2Fwww.youtube.com%2Fsignin%3Faction_handle_signin%3Dtrue%26nomobiletemp%3D1%26hl%3Den_US%26next%3D%252Findex&hl=en_US&ltmpl=sso")

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

			newurl = re.compile('<meta http-equiv="refresh" content="0; url=&#39;(.*)&#39;"></head>').findall(result)[0].replace("&amp;", "&")
			url = urllib2.Request(newurl)
			url.add_header('User-Agent', self.USERAGENT)
			con = urllib2.urlopen(newurl)
			result = con.read()
			con.close()
			
			newurl = re.compile('<meta http-equiv="refresh" content="0; url=&#39;(.*)&#39;"></head>').findall(result)[0].replace("&amp;", "&")
			url = urllib2.Request(newurl)
			url.add_header('User-Agent', self.USERAGENT)
			con = urllib2.urlopen(newurl)
			result = con.read()
			con.close()
			
			# Save cookiefile in settings
			cookies = repr(cj)
			login_info = ""
			if cookies.find("name='LOGIN_INFO', value='") > 0:
				start = cookies.find("name='LOGIN_INFO', value='") + len("name='LOGIN_INFO', value='")
				login_info = cookies[start:cookies.find("', port=None", start)]

			self.__settings__.setSetting( "login_info", login_info )
			
			if self.__dbg__:
				print self.__plugin__ + " _httpLogin done: " + login_info

			return self.__settings__.getSetting( "login_info" )
		
		except IOError, e:
			# http://bytes.com/topic/python/answers/33770-error-codes-urlerror
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit ioerror except2: : " + repr(e)
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				print self.interrogate(e)
				
				if error < 9:
					if self.__dbg__:
						print self.__plugin__ + " login pre sleep"
					# Check if there is a timeout here.
					import time
					time.sleep(3)
					if self.__dbg__:
						print self.__plugin__ + " login post sleep"

					return self._httpLogin( new, error + 1 )
				
				return ""
		except:
			if self.__dbg__:
				print self.__plugin__ + " _httpLogin: uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
			return ""
		
