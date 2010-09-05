'''
    YouTube plugin for XBMC
    Copyright (C) 2010 Tobias Ussing And Henrik Mosgaard Jensen

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

import sys, urllib, urllib2, re, os, cookielib
from xml.dom.minidom import parse, parseString

# ERRORCODES:
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
				doc = doc.strip()   # Remove leading/trailing whitespace.
				firstline = doc.split('\n')[0]
				print "DOC:     ", firstline
	
						
	def login(self, error = 0):
		if self.__dbg__:
			print self.__plugin__ + " login - errors: " + str(error)
			
		uname = self.__settings__.getSetting( "username" )
		passwd = self.__settings__.getSetting( "user_password" )
		
		self.__settings__.setSetting('auth', "")
		self.__settings__.setSetting('nick', "")
		
		if ( uname == "" and passwd == "" ):
			if self.__dbg__:
				print self.__plugin__ + " login no username or password set "
			return ( "", 200 )

		url = urllib2.Request("https://www.google.com/youtube/accounts/ClientLogin");

		url.add_header('Content-Type', 'application/x-www-form-urlencoded')
		url.add_header('GData-Version', 2)
		
		data = urllib.urlencode({'Email': uname, 'Passwd': passwd, 'service': 'youtube', 'source': 'YouTube plugin'});
	
		try:
			con = urllib2.urlopen(url, data);
				
			value = con.read();
			con.close()

			result = re.compile('Auth=(.*)\nYouTubeUser=(.*)').findall(value);
					
			if len(result) > 0:
				( auth, nick ) = result[0]
				self.__settings__.setSetting('auth', auth)
				self.__settings__.setSetting('nick', nick)
				self._httpLogin()

				if self.__dbg__:
					print self.__plugin__ + " login done: " + nick
				return ( self.__language__(30030), 200 )
			
			return ( self.__language__(30609), 303 )
			
		except urllib2.HTTPError, e:
			error = str(e)
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit http except: " + error
			if e.code == 403:
				return ( self.__language__(30621), 303 )
			return ( error, 303 )
		
		except ValueError, e:
			error = repr(e)
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit valueerror except: " + error
			return ( error, 303 )
		
		except IOError, e:
			# http://bytes.com/topic/python/answers/33770-error-codes-urlerror
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit ioerror except2: : " + repr(e)
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				print self.interrogate(e)

			if error < 9:
				import time
				time.sleep(1)
				return self.login( error + 1 )
			
			return ( "IOERROR", 303 )
		
		except urllib2.URLError, e:
			error = repr(e)
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit url except: " + error
			return ( error, 303 )										
		except:
			if self.__dbg__:
				print self.__plugin__ + " login failed uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
			return ( self.__language__(30609), 500 );
	
	def search(self, query, page = "0"):
		if self.__dbg__:
			print self.__plugin__ + " search: " + repr(query) + " - page: " + repr(page)
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]
		safe_search = ("none", "moderate", "strict" ) [int( self.__settings__.getSetting( "safe_search" ) ) ]
		link = "http://gdata.youtube.com/feeds/api/videos?" + urllib.urlencode({'q': query}) + "&safeSearch=" + safe_search + "&start-index=" + str( per_page * int(page) + 1) + "&max-results=" + repr(per_page)
		try:
			authors = eval(self.__settings__.getSetting("stored_searches_author"))
		except:
			authors = {}
		if len(authors) > 0:
			print self.__plugin__ + " search test empty searches"
			print authors
			if query in authors:
				link += "&" + urllib.urlencode({'author': authors[query]})
			print link
		url = urllib2.Request(link);
		url.add_header('User-Agent', self.USERAGENT);
		url.add_header('GData-Version', 2)
		try:
			con = urllib2.urlopen(url);
			result = self._getvideoinfo(con.read())
			con.close()
			if len(result) > 0:
				if self.__dbg__:
					print self.__plugin__ + " search done :" + str(len(result))
				return (result, 200)
			else:
				if self.__dbg__:
					print self.__plugin__ + " search done with no results"
				return (self.__language__(30601), 303)
		except urllib2.HTTPError, e:
			error = str(e)
			if self.__dbg__:
				print self.__plugin__ + " search failed, hit except: " + error
			return ( error, 303 )
		except:
			if self.__dbg__:
				print self.__plugin__ + " search failed with uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
			return ( [], 500 )

	def feeds(self, feed, page = "0" ):
		if self.__dbg__:
			print self.__plugin__ + " feeds : " + repr(feed) + " page: " + repr(page)
		result = ""
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]
		
		if (feed.find("%s") > 0 ):
			time = ( "all_time", "today", "this_week", "this_month") [ int(self.__settings__.getSetting( "feed_time" ) ) ]
			feed = feed % time
		
		if ( feed.find("?") == -1 ):
			feed += "?"
		else:
			feed += "&"
		feed += "start-index=" + str( per_page * int(page) + 1) + "&max-results=" + repr(per_page)
			
		if (feed.find("standardfeeds") > 0):
			region = ('', 'AU', 'BR', 'CA', 'CZ', 'FR', 'DE', 'GB', 'NL', 'HK', 'IN', 'IE', 'IL', 'IT', 'JP', 'MX', 'NZ', 'PL', 'RU', 'KR', 'ES','SE', 'TW', 'US', 'ZA' )[ int( self.__settings__.getSetting( "region_id" ) ) ]
			if (region):
				feed = feed.replace("/standardfeeds/", "/standardfeeds/"+ region + "/")

		if self.__dbg__:
			print self.__plugin__ + " feeds : " + repr(feed) + " page: " + repr(page)
			
		url = urllib2.Request(feed);
		url.add_header('User-Agent', self.USERAGENT);
		url.add_header('GData-Version', 2)
		try:
			con = urllib2.urlopen(url);
			result = self._getvideoinfo(con.read())
			if self.__dbgv__:
				print self.__plugin__ + " feeds result: " + repr(result)

			con.close()
			if len(result) > 0:
				if self.__dbg__:
					print self.__plugin__ + " feeds done : " + str(len(result))
				return ( result, 200 )
			else:
				if self.__dbg__:
					print self.__plugin__ + " feeds done with no results"
				return (self.__language__(30602), 303)
			
		except urllib2.HTTPError, e:
			error = str(e)
			if self.__dbg__:
				print self.__plugin__ + " feed failed, hit except: " + error
			return ( error, 303 )										
		except:
			if self.__dbg__:
				print self.__plugin__ + " feed failed with uncaught exception dumping result"
				print self.__plugin__ + " feed result: " + repr(result)
				print self.__plugin__ + ' feed ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				
			return ( [], 500 )
	
	def list(self, feed, page = "0", retry = True):
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
		
		url = urllib2.Request(feed)
		url.add_header('User-Agent', self.USERAGENT)
		url.add_header('GData-Version', 2)
		url.add_header('Authorization', 'GoogleLogin auth=' + auth);
		url.add_header('X-GData-Key', 'key=' + self.APIKEY)
		try:
			con = urllib2.urlopen(url);
			result = con.read()
			con.close()

			if self.__dbgv__:
				print self.__plugin__ + " list result: " + repr(result)

			result = self._getvideoinfo(result)

			if len(result) > 0:
				if self.__dbg__:
					print self.__plugin__ + " list done :" + str(len(result))
				return (result, 200)
			else:
				if self.__dbg__:
					print self.__plugin__ + " list done with no results"
				return (self.__language__(30602), 303)

		except urllib2.HTTPError, e:
			error = str(e)
			if ( error.find("401") > 0 and retry ):
				if self.login():
					if self.__dbg__:
						print self.__plugin__ + " list done: retrying"
					return self.list(feed, page, False)
				else:
					if self.__dbg__:
						print self.__plugin__ + " list done: retrying failed because login failed"
					return ( error, 303 )
			elif ( error.find("403") > 0 ):
				# Happens if a user has subscriped to a user and the user has no uploads
				print self.__plugin__ + ' list ERROR: %s::%s (%d) - %s' % (self.__class__.__name__ , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				return (self.__language__(30601), 303)
			else:
				if self.__dbg__:
					print self.__plugin__ + " list except: " + error
				return ( error, 303 )
		except:
			if self.__dbg__:
				print self.__plugin__ + " list uncaught exception dumping result"
				print self.__plugin__ + " list result: " + repr(result)
				print self.__plugin__ + ' list ERROR: %s::%s (%d) - %s' % (self.__class__.__name__ , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
			return ( [], 500 )

	def delete_favorite(self, delete_url):
		return self._youTubeDel(delete_url)
	
	def remove_contact(self, contact_id):
		delete_url = "http://gdata.youtube.com/feeds/api/users/default/contacts/%s" % contact_id
		return self._youTubeDel(delete_url)

	def remove_subscription(self, editurl):
		return self._youTubeDel(editurl)

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

	def playlists(self, link, page = '0', retry = True):
		if self.__dbg__:
			print self.__plugin__ + " playlists " + repr(link) + " - page: " + repr(page)
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
		link += "start-index=" + str( per_page * int(page) + 1) + "&max-results=" + repr(per_page)

		url = urllib2.Request(link)
		url.add_header('User-Agent', self.USERAGENT)
		url.add_header('GData-Version', 2)
		url.add_header('Authorization', 'GoogleLogin auth=' + auth);
		url.add_header('X-GData-Key', 'key=' + self.APIKEY);
		
		try:
			con = urllib2.urlopen(url);
			result = con.read()
			con.close()
		except urllib2.HTTPError, e:
			error = str(e)
			if ( error.find("401") > 0 and retry ):
				if self.login():
					if self.__dbg__:
						print self.__plugin__ + " playlist retrying"
					return self.playlists(link, page, False)
				else:
					if self.__dbg__:
						print self.__plugin__ + " playlist retrying failed because login failed"
					return ( error, 303 )
				
			if self.__dbg__:
				print self.__plugin__ + " playlist except: " + error
			return ( error, 303 )
		except:
			if self.__dbg__:
				print self.__plugin__ + " playlist uncaught exception dumping result"
				print self.__plugin__ + " playlist result: " + repr(result)
				print self.__plugin__ + ' playlist ERROR: %s::%s (%d) - %s' % (self.__class__.__name__ , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])	
			return ( [], 500 )

		if self.__dbgv__:
			print self.__plugin__ + " playlist result: " + repr(result)

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
			video['Title'] = str(node.getElementsByTagName("title").item(0).firstChild.nodeValue.replace('Activity of : ', '').replace('Videos published by : ', '')).encode( "utf-8" );
			
			video['published'] = self._getNodeValue(node, "published", "2008-07-05T19:56:35.000-07:00")
			video['summary'] = self._getNodeValue(node, 'summary', 'Unknown')
			video['content'] = self._getNodeAttribute(node, 'content', 'src', 'FAIL')
			video['playlistId'] = self._getNodeValue(node, 'yt:playlistId', '')
			
			if node.getElementsByTagName("link"):
				link = node.getElementsByTagName("link")
				for i in range(len(link)):
					if link.item(i).getAttribute('rel') == 'edit':
						video['editurl'] = link.item(i).getAttribute('href')
																
			video['next'] = next

			playobjects.append(video);
			
		if self.__dbg__:
			print self.__plugin__ + " playlist done"
				
		return ( playobjects, 200 );
	
	def downloadVideo(self, path, params):
		get = params.get
		if ( not get("videoid") ):
			return ( "", 200)
		if self.__dbg__:
			print self.__plugin__ + " downloadVideo : " + repr(path) + " - videoid : " + repr(get("videoid"))
			
		( video, status )  = self.construct_video_url(params, download = True);
		
		if ( status == 200 ):
			path = self.__settings__.getSetting( "downloadPath" )
			try:
				if self.__dbg__:
					print self.__plugin__ + " downloadVideo stream_map: " + video['stream_map']
					
				if video['stream_map'] == "True":
					print self.__plugin__ + " downloadVideo stream_map not implemented in downloadVideo"
					return (self.__language__(30620), 303)
				else:
					url = urllib2.Request(video['video_url'])
					url.add_header('User-Agent', self.USERAGENT);
					filename = "%s/%s.flv" % ( path,video['Title'])
					file = open(filename, "wb")
					con = urllib2.urlopen(url);
					file.write(con.read())
					con.close()
					
					self.__settings__.setSetting( "vidstatus-" + get("videoid"), "1" )
			except urllib2.HTTPError, e:
				if self.__dbg__:
					print self.__plugin__ + " downloadVideo except: " + str(e)
				return ( str(e), 303 )
			except:
				if self.__dbg__:
					print self.__plugin__ + " downloadVideo uncaught exception"
					print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
									   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				
				return (self.__language__(30606), 303)
		else:
			if self.__dbg__:
				print self.__plugin__ + " downloadVideo got error from construct_video_url: [%s] %s" % ( status, video)
			return (video, status)

		if self.__dbg__:
			print self.__plugin__ + " downloadVideo done"
		return ( video, status )
	
	def construct_video_url(self, params, encoding = 'utf-8', download = False):
		get = params.get
		if ( not get("videoid") ):
			return ( "", 200)

		videoid = get("videoid")
		
		if self.__dbg__:
			print self.__plugin__ + " construct_video_url : " + repr(videoid)

		video = self._get_details(videoid)
		
		if not video:
			if self.__dbg__:
				print self.__plugin__ + " construct_video_url failed because of missing video from _get_details"
			return ("", 500)
		
		if ( 'apierror' in video):
			if self.__dbg__:
				print self.__plugin__ + " construct_video_url, got apierror: " + video['apierror']
			return (video['apierror'], 303)

		if not download:
			hd_quality = int(self.__settings__.getSetting( "hd_videos" ))
		else:
			hd_quality = int(self.__settings__.getSetting( "hd_videos_download" ))
			if ( hd_quality == 0 ):
				hd_quality = int(self.__settings__.getSetting( "hd_videos" ))
			else:
				hd_quality -= 1
		
		try:
			(fmtSource, swfConfig, video['stream_map']) = self._extractVariables(videoid)
			
			if not fmtSource:
				if self.__dbg__:
					print self.__plugin__ + " construct_video_url Hopefully this extra if check is now legacy"
					
				(fmtSource, swfConfig, video['stream_map']) = self._extractVariables(videoid, True)
				
				if not fmtSource:
					print self.__plugin__ + " IMPORTANT : " + videoid
					if self.__dbg__:
						print self.__plugin__ + " construct_video_url failed, empty fmtSource after trying with cookie"
					
					return (self.__language__(30618), 303)
			
			if ( video['stream_map'] == 303 ):
				return (fmtSource, 303)
			
			fmt_url_map = urllib.unquote_plus(fmtSource[0]).split('|')
			links = {};
			video_url = False

			print self.__plugin__ + " construct_video_url: stream_map : " + video['stream_map']
			if (video['stream_map'] == 'True'):
				if self.__dbg__:
					print self.__plugin__ + " construct_video_url: stream map"
					
				for fmt_url in fmt_url_map:
					if self.__dbg__:
						print self.__plugin__ + " construct_video_url: fmt_url : " + repr(fmt_url)
						
					if (len(fmt_url) > 7 and fmt_url.find(":\\/\\/") > 0):
						if (fmt_url.rfind(',') > fmt_url.rfind('\/id\/')):
							final_url = fmt_url[:fmt_url.rfind(',')]
							if (final_url.rfind('\/itag\/') > 0):
								quality = final_url[final_url.rfind('\/itag\/') + 8:]
							else :
								quality = "5"
							links[int(quality)] = final_url.replace('\/','/')
						else :
							final_url = fmt_url
							if (final_url.rfind('\/itag\/') > 0):
								quality = final_url[final_url.rfind('\/itag\/') + 8:]
							else :
								quality = "5"
							links[int(quality)] = final_url.replace('\/','/')
			
			else:
				if self.__dbg__:
					print self.__plugin__ + " construct_video_url: non stream map" 
				for fmt_url in fmt_url_map:
					if (len(fmt_url) > 7):
						if (fmt_url.rfind(',') > fmt_url.rfind('&id=')): 
							final_url = fmt_url[:fmt_url.rfind(',')]
							if (final_url.rfind('itag=') > 0):
								quality = final_url[final_url.rfind('itag=') + 5:]
								quality = quality[:quality.find('&')]
							else:
								quality = "5"
							links[int(quality)] = final_url.replace('\/','/')
						else :
							final_url = fmt_url
							if (final_url.rfind('itag=') > 0):
								quality = final_url[final_url.rfind('itag=') + 5:]
								quality = quality[:quality.find('&')]
							else :
								quality = "5"
							links[int(quality)] = final_url.replace('\/','/')
			
			get = links.get
			
			# SD videos are default, but we go for the highest res
			if (get(35)):
				video_url = get(35)
			elif (get(34)):
				video_url = get(34)
			elif (get(18)):
				video_url = get(18)
			elif (get(5)):
				video_url = get(5)
			
			if (hd_quality > 0): #<-- 720p
				if (get(22)):
					video_url = get(22)
			if (hd_quality > 1): #<-- 1080p
				if (get(37)):
					video_url = get(37)
					
			if ( not video_url ):
				if self.__dbg__:
					print self.__plugin__ + " construct_video_url failed, video_url not set"
				return (self.__language__(30607), 303)
			
			if (video['stream_map'] == 'True'):
				video['swf_config'] = swfConfig
				
			video['video_url'] = video_url;

			if self.__dbg__:
				print self.__plugin__ + " construct_video_url done"

			return (video, 200);
		except:
			if self.__dbg__:
				print self.__plugin__ + " construct_video_url uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__ , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
			return ('', 500)


	def arrayToPipe(self, input):
		pipedItems = ""
		for item in input:
			pipedItems += item + "|"
		return pipedItems

	def scrapeVideos(self, feed, params):
		if self.__dbg__:
			print self.__plugin__ + " scrapeVideos: " + repr(feed) + " - params: - " + repr(params)
		get = params.get
		page = int(get("page", "0"))
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.__settings__.getSetting( "perpage" ) ) ]

		oldVideos = self.__settings__.getSetting("recommendedVideos")

		if ( page == 0 or oldVideos == ""):
			( videos, result)  = self._scrapeYouTubeData(feed)
			if (result == 200):
				self.__settings__.setSetting("recommendedVideos", self.arrayToPipe(videos))									
			else:
				return ( videos, result )
		else:
			videos = oldVideos.split("|")
		
		if ( per_page * ( page + 1 ) < len(videos) ):
			next = 'true'
		else:
			next = 'false'

		subitems = videos[(per_page * page):(per_page * (page + 1))]
		ytobjects = []
		failed = []
		counter = 0
		link = ""

		for item in subitems:
			# Dashes break with google, fetch all video's with a dash in the videoid seperatly.
			if (item.find('-') == -1):
				link += item + "|"
				counter += 1;
			else:
				failed.append(item)
				
			if ( counter > 9 or item == subitems[len(subitems)-1] ):
				link += "&restriction=US"
				url = urllib2.Request("http://gdata.youtube.com/feeds/api/videos?q=" + link);
				url.add_header('User-Agent', self.USERAGENT);
				url.add_header('GData-Version', 2)

				try:
					con = urllib2.urlopen(url);
					value = con.read()
					con.close()
				except urllib2.HTTPError, e:
					if self.__dbg__:
						print self.__plugin__ + " scrapeVideos except: " + str(e)
					return ( str(e), 303 )
				except:
					if self.__dbg__:
						print self.__plugin__ + " scrapeVideos caught unknown exception"
						print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
										   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
					return ( "", 500 )
				
				temp = self._getvideoinfo(value)
				ytobjects += temp[0:counter]
				counter = 0
				link = ""

		for item in failed:
			videoitem = self._get_details(item)			
			if videoitem:
				if ( 'apierror' not in videoitem):
					ytobjects.append(videoitem)
				else:
					if self.__dbg__:
						print self.__plugin__ + " scrapeVideos, got apierror: " + videoitem['apierror']
										
		
		if (len(ytobjects) > 0):
			ytobjects[len(ytobjects)-1]['next'] = next

		if self.__dbg__:
			print self.__plugin__ + " scrapeVideos done"
		return ( ytobjects, 200 )

	#===============================================================================
	#
	# Internal functions to YouTubeCore.py
	#
	# Return should be value(True for bool functions), or False if failed.
	#
	# False MUST be handled properly in External functions
	#
	#===============================================================================

	def _extractVariables(self, videoid, login = False):
		if self.__dbg__:
			print self.__plugin__ + " extractVariables : " + repr(videoid)
		htmlSource = ""
				
		# add try except
		try:
			link = 'http://www.youtube.com/watch?v=' +videoid + "&safeSearch=none&restriction=US&hl=en_US"
			request = urllib2.Request(link);
			request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)');
			
			if ( login ):
				# Get a new LOGIN_INFO cookie (for some reason the old one will fail) and use request url again.
				if ( self._httpLogin() ):
					request.add_header('Cookie', 'LOGIN_INFO=' + self.__settings__.getSetting( "login_info" ) )
				else:
					if self.__dbg__:
						print self.__plugin__ + " _extractVariables login failed"
				
			con = urllib2.urlopen(request);
			htmlSource = con.read();
			con.close()
			if self.__dbgv__:
				print self.__plugin__ + " _extractVariables result: " + repr(htmlSource)

			swf_url = False
			fmtSource = re.findall('"fmt_url_map": "([^"]+)"', htmlSource);
			if fmtSource:
				stream_map = "False"
			else:
				if self.__dbg__:
					print self.__plugin__ + " _extractVariables exited. RTMP disabled."
				return ( self.__language__(30608), self.__language__(30608), 303 )

			if self.__dbg__:
				print self.__plugin__ + " extractVariables done"
				
		except urllib2.HTTPError, e:
			error = str(e)
			if self.__dbg__:
				print self.__plugin__ + " scrapeVideos except: " + error
			return ( error, 303 )
		except:
			if self.__dbg__:
				print self.__plugin__ + " _extractVariables uncaught exception dumping htmlSource"
				print self.__plugin__ + " _extractVariables result: " + repr(htmlSource)
				print self.__plugin__ + ' _extractVariables ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				
			return ( '', 500 )
									
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
			if self.login():
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
			request.add_header('GData-Version', 2)
			usock = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			error = str(e)
			if ( error.find("201") > 0):
				if self.__dbg__:
					print self.__plugin__ + " _youTubeAdd: Done"
				return ( "", 200)
			elif (error.find("503") > -1):
				if self.__dbg__:
					print self.__plugin__ + " _youTubeAdd: " + self.__language__(30615)
				return ( self.__language__(30615), 303 )
			elif ( error.find("401") > 0 and retry ):
				if self.login():
					if self.__dbg__:
						print self.__plugin__ + " _youTubeAdd: retry"
					return self.youTubeAdd(url, add_request, False)
				else:
					if self.__dbg__:
						print self.__plugin__ + " _youTubeAdd: " + error
					return ( error, 303 )
			else:
				if self.__dbg__:
					print self.__plugin__ + " _youTubeAdd: " + error
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
				if self.login():
					if self.__dbg__:
						print self.__plugin__ + " _youTubeDel: retrying"
					return self._youTubeDel(delete_url, False)
				else:
					resp = str(response.read())
					if self.__dbg__:
						print self.__plugin__ + " _youTubeDel: " + resp
					return ( resp, 303 )
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
				
			return ( "" , 500)
	
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

	def _getvideoinfo(self, value):
		if self.__dbg__:
			print self.__plugin__ + " _getvideoinfo: " + str(len(value))

		try:
			dom = parseString(value);
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

			#construct list of video objects					
			ytobjects = [];
			for node in entries:
				video = {};

				# http://code.google.com/intl/en/apis/youtube/2.0/reference.html#youtube_data_api_tag_yt:state <- more reason codes
				# requesterRegion - This video is not available in your region. <- fails
				# limitedSyndication - Syndication of this video was restricted by its owner. <- works
			
				if node.getElementsByTagName("yt:state").item(0):
				
					state = self._getNodeAttribute(node, "yt:state", 'name', 'Unknown Name')

					# Ignore unplayable items.
					if ( state == 'deleted' or state == 'rejected'):
						continue
					else:
						# Get reason for why we can't playback the file.		
						if node.getElementsByTagName("yt:state").item(0).hasAttribute('reasonCode'):
							reason = self._getNodeAttribute(node, "yt:state", 'reasonCode', 'Unknown reasonCode')
							value = self._getNodeValue(node, "yt:state", "Unknown reasonValue").encode('utf-8')
						
							if ( reason != 'limitedSyndication' ):
								video['reasonCode'] = reason
								video['reasonValue'] = value
						
							if self.__dbg__:
								print self.__plugin__ + "/ERROR reasonCode: [%s] %s " % ( reason, value )
							
							if reason == "private":
								continue

				video['videoid'] = self._getNodeValue(node, "yt:videoid", "missing")

				if ( video['videoid'] == "missing" ):
					video['videolink'] = node.getElementsByTagName("link").item(0).getAttribute('href')
					match = re.match('.*?v=(.*)\&.*', video['videolink'])
					if match:
						video['videoid'] = match.group(1)
					else:
						continue
				
				video['Title'] = self._getNodeValue(node, "media:title", "Unknown Title").encode('utf-8') # Convert from utf-16 to combat breakage
				video['Plot'] = self._getNodeValue(node, "media:description", "Unknown Plot").encode( "utf-8" )
				video['Date'] = self._getNodeValue(node, "published", "Unknown Date").encode( "utf-8" )
				video['user'] = self._getNodeValue(node, "name", "Unknown Name").encode( "utf-8" )
				video['Studio'] = self._getNodeValue(node, "media:credit", "Unknown Uploader").encode( "utf-8" )
				duration = int(self._getNodeAttribute(node, "yt:duration", 'seconds', '0'))
				video['Duration'] = "%02d:%02d" % ( duration / 60, duration % 60 )
				video['Rating'] = float(self._getNodeAttribute(node,"gd:rating", 'average', "0.0"))
				video['Genre'] = self._getNodeAttribute(node, "media:category", "label", "Unknown Genre").encode( "utf-8" )

				if node.getElementsByTagName("link"):
					link = node.getElementsByTagName("link")
					for i in range(len(link)):
						if link.item(i).getAttribute('rel') == 'edit':
							video['editurl'] = link.item(i).getAttribute('href')

				video['thumbnail'] = "http://i.ytimg.com/vi/" + video['videoid'] + "/0.jpg"
			
				overlay = self.__settings__.getSetting( "vidstatus-" + video['videoid'] )

				if overlay:
					video['Overlay'] = int(overlay)
				
				video['next'] = next

				ytobjects.append(video);

				if self.__dbg__:
					print self.__plugin__ + " _getvideoinfo done"
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

		link = 'http://www.youtube.com/watch?v=' +videoid + "&safeSearch=none"
		request = urllib2.Request(link);
		request.add_header('User-Agent', self.USERAGENT)
		
		if ( self._httpLogin() ):
			request.add_header('Cookie', 'LOGIN_INFO=' + self.__settings__.getSetting( "login_info" ) )

		con = urllib2.urlopen(request);
		http_result = con.read();
		
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

		url = urllib2.Request("http://gdata.youtube.com/feeds/api/videos/" + videoid);
		url.add_header('User-Agent', self.USERAGENT);
		url.add_header('GData-Version', 2)
		try:
			con = urllib2.urlopen(url);
			result = con.read();
			con.close()
			result = self._getvideoinfo(result)
			
			if len(result) == 0:
				if self.__dbg__:
					print self.__plugin__ + " _get_details result was empty"
				return False
			else:
				if self.__dbg__:
					print self.__plugin__ + " _get_details done"
				return result[0];
			
		except urllib2.URLError, err:
			if self.__dbg__:
				print self.__plugin__ + " _get_details except: " + str(err)

			video = {}
			video['Title'] = "Error"
			video['videoid'] = videoid
			video['thumbnail'] = "Error"
			video['video_url'] = False

			if (err.code == 403):
				# 403 == Forbidden
				# Happens on "removed by user" and "This video has been removed due to terms of use violation." and "This video is private
				
				video['apierror'] = self._getAlert(videoid)
				return video

			if (err.code == 503):
				if self.__dbg__:
					print self.__plugin__ + " _get_details exception 503: " + str(err)
				video['apierror'] = self.__language__(30605)
				return video
			else:
				if self.__dbg__:
					print self.__plugin__ + " _get_details uncaught except: [%s] %s" % ( err.code, str(err) )
				video['apierror'] = self.__language__(30606) + str(err.code)
				return video

		except:
			if self.__dbg__:
				print self.__plugin__ + " _get_details uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				
			return False
		
		
	def _httpLogin(self, error = 0):
		if self.__dbg__:
			print self.__plugin__ + " _httpLogin - errors: " + str(error)

		uname = self.__settings__.getSetting( "username" )
		pword = self.__settings__.getSetting( "user_password" )
		if ( uname == "" and pword == "" ):
			return False

		cj = cookielib.LWPCookieJar()
		
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
		urllib2.install_opener(opener)

		# Get GALX
		url = urllib2.Request(urllib.unquote("https://www.google.com/accounts/ServiceLogin?service=youtube"))
		url.add_header('User-Agent', self.USERAGENT)

		try:
			if self.__dbg__:
				print self.__plugin__ + " _httpLogin: step 1"
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
			if self.__dbg__:
				print self.__plugin__ + " _httpLogin: step 2"
			url = urllib2.Request('https://www.google.com/accounts/ServiceLoginAuth?service=youtube', params)
			url.add_header('User-Agent', self.USERAGENT)
		
			con = urllib2.urlopen(url)
			result = con.read()

			newurl = re.compile('<meta http-equiv="refresh" content="0; url=&#39;(.*)&#39;"></head>').findall(result)[0].replace("&amp;", "&")
			url = urllib2.Request(newurl)
			url.add_header('User-Agent', self.USERAGENT)
			
			# Login to youtube
			if self.__dbg__:
				print self.__plugin__ + " _httpLogin: step 3"
			con = urllib2.urlopen(newurl)
			
			# Save cookiefile in settings
			cookies = repr(cj)
			start = cookies.find("name='LOGIN_INFO', value='") + len("name='LOGIN_INFO', value='")
			login_info = cookies[start:cookies.find("', port=None", start)]
			self.__settings__.setSetting( "login_info", login_info )
			
			if self.__dbg__:
				print self.__plugin__ + " _httpLogin: Logged in on attempt %s with login_info cookie: %s " % ( str(error + 1), login_info)

			return True
		
		except IOError, e:
			# http://bytes.com/topic/python/answers/33770-error-codes-urlerror
			if self.__dbg__:
				print self.__plugin__ + " login failed, hit ioerror except2: : " + repr(e)
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				print self.interrogate(e)
				
				if error < 9:
					import time
					time.sleep(1)
					return self._httpLogin( error + 1 )
				
				return ( "IOERROR", 303 )
		except:
			if self.__dbg__:
				print self.__plugin__ + " _httpLogin: uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
			return False

	def _scrapeYouTubeData(self, feed, retry = True):
		if self.__dbg__:
			print self.__plugin__ + " _scrapeYouTubeData: " + repr(feed)
		result = ""

		login_info = self.__settings__.getSetting( "login_info" )
		if ( not login_info ):
			if ( self._httpLogin() ):
				login_info = self.__settings__.getSetting( "login_info" )
		
		url = urllib2.Request(feed + "&hl=en")
		url.add_header('User-Agent', self.USERAGENT)
		url.add_header('Cookie', 'LOGIN_INFO=' + login_info)

		try:
			con = urllib2.urlopen(url)
			result = con.read()
			if self.__dbgv__:
				print self.__plugin__ + " _scrapeYouTubeData result: " + repr(result)
			con.close()

			videos = re.compile('<a href="/watch\?v=(.*)&amp;feature=grec_browse" class=').findall(result);

			if len(videos) == 0:
				videos = re.compile('<div id="reco-(.*)" class=').findall(result);

			if ( len(videos) == 0 and retry ):
				self._httpLogin()
				videos = self._scrapeYouTubeData(feed, False)
			if self.__dbg__:
				print self.__plugin__ + " _scrapeYouTubeData done"
			return ( videos, 200 )
		except urllib2.HTTPError, e:
			if self.__dbg__:
				print self.__plugin__ + " _scrapeYouTubeData exception: " + str(e)
			return ( self.__language__(30619), "303" )
		except:
			if self.__dbg__:
				print self.__plugin__ + " _scrapeYouTubeData uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__
								   , sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				print self.__plugin__ + " _scrapeYouTubeData result: " + repr(result)
			
			return ( "", 500 )
