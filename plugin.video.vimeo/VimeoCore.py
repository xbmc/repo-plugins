'''
   Vimeo plugin for XBMC
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

import sys, urllib2, string

class VimeoCore:
	
	def __init__(self):
		self.v = sys.modules["__main__"].client
		self.soup = sys.modules["__main__"].soup
		self.settings = sys.modules[ "__main__" ].settings
		self.language = sys.modules[ "__main__" ].language
		self.plugin = sys.modules[ "__main__" ].plugin	
		self.dbg = sys.modules[ "__main__" ].dbg
		self.utils = sys.modules[ "__main__" ].utils
		self.login = sys.modules[ "__main__" ].login	

		self.oauth_secret = False
		self.oauth_token_secret = False
	
		self.hq_thumbs = self.settings.getSetting( "high_quality_thumbs" ) == "true"
	
		self.USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"

	#===============================================================================
	#
	# External functions called by YouTubeNavigation.py
	#
	# return MUST be a tupple of ( result[string or dict], status[int] )
	#
	#===============================================================================
	
	def init(self):
		if self.dbg:
			print self.plugin + " init " 
		
		self.oauth_token = self.settings.getSetting("oauth_token")
		self.oauth_token_secret = self.settings.getSetting("oauth_token_secret")
		
		if ( self.oauth_token and self.oauth_token_secret ):
			self.v.init(token = self.oauth_token, token_secret = self.oauth_token_secret)

	def downloadVideo(self, video):
		if self.dbg:
			print self.plugin + " downloadVideo : " + video['Title']
		
		path = self.settings.getSetting( "downloadPath" )
		try:
			url = urllib2.Request(video['video_url'])
			url.add_header('User-Agent', self.USERAGENT);
			valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
			
			filename = "%s/%s.mp4" % ( path, ''.join(c for c in video['Title'] if c in valid_chars) )
			file = open(filename, "wb")
			con = urllib2.urlopen(url);
			file.write(con.read())
			con.close()
				
			self.settings.setSetting( "vidstatus-" + video['videoid'], "1" )
		except urllib2.HTTPError, e:
			if self.dbg:
				print self.plugin + " downloadVideo except: " + str(e)
			return ( str(e), 303 )
		except:
			if self.dbg:
				print self.plugin + " downloadVideo uncaught exception"
				print 'ERROR: %s::%s (%d) - %s' % (self.__class__.__name__, sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, sys.exc_info()[1])
				
			return (self.language(30606), 303)

		if self.dbg:
			print self.plugin + " downloadVideo done"
		return ( video, 200 )
	
	def setLike(self, params):
		if self.dbg:
			print self.plugin + " setLike "
			
		get = params.get
		
		if (get("action") == "add_favorite"): 
			result = self.v.vimeo_videos_setLike(like = "true", video_id=get("videoid"), oauth_token=self.oauth_token)
		else:
			result = self.v.vimeo_videos_setLike(like = "false", video_id=get("videoid"), oauth_token=self.oauth_token)

		if self.dbg:
			print self.plugin + " setLike done"
				
		return self._get_return_status(result)
	
	def updateContact(self, params):
		if self.dbg:
			print self.plugin + " updateContact"

		get = params.get
		
		if (get("action") == "add_contact"): 
			result = self.v.vimeo_people_addContact(user_id=get("contact"), oauth_token=self.oauth_token)
		else:
			result = self.v.vimeo_people_removeContact(user_id=get("contact"), oauth_token=self.oauth_token)

		if self.dbg:
			print self.plugin + " updateContact done"
				
		return self._get_return_status(result)

	def addToWatchLater(self, params):
		if self.dbg:
			print self.plugin + " addToWatchLater"
		get = params.get
		
		result = self.v.vimeo_albums_addToWatchLater(video_id = get("videoid") )
		
		return self._get_return_status(result)
		
	def removeWatchLater(self, params):
		if self.dbg:
			print self.plugin + " removeFromWatchLater"
		get = params.get
		
		result = self.v.vimeo_albums_removeFromWatchLater(video_id = get("videoid"))
		
		return self._get_return_status(result) 
		
	def updateGroup(self, params):
		if self.dbg:
			print self.plugin + " updateGroup"

		get = params.get
		
		if (get("action") == "join_group"): 
			result = self.v.vimeo_groups_join(group_id=get("group"), oauth_token=self.oauth_token)
		else:
			result = self.v.vimeo_groups_leave(group_id=get("group"), oauth_token=self.oauth_token)

		if self.dbg:
			print self.plugin + " updateGroup done"
				
		return self._get_return_status(result)

	def updateSubscription(self, params):
		if self.dbg:
			print self.plugin + " updateSubscription"
				
		get = params.get

		if (get("action") == "add_subscription"): 
			result = self.v.vimeo_channels_subscribe(channel_id=get("channel"), oauth_token=self.oauth_token)
		else:
			result = self.v.vimeo_channels_unsubscribe(channel_id=get("channel"), oauth_token=self.oauth_token)

		if self.dbg:
			print self.plugin + " updateSubscription done"
				
		return self._get_return_status(result)
	
	def construct_video_url(self, videoid, encoding = 'utf-8'):
		if self.dbg:
			print self.plugin + " construct_video_url : " + repr(videoid)
			
		video = self._get_details(videoid)
		
		get = video.get
		if not video:
			# we need a scrape the homepage fallback when the api doesn't want to give us the URL
			if self.dbg:
				print self.plugin + " construct_video_url failed because of missing video from _get_details"
			return ("", 500)
		
		quality = "sd"
		hd_quality = int(self.settings.getSetting( "hd_videos" ))
		
		if (hd_quality and get("isHD","0") == "1"):
			quality = "hd"
		
		if ( 'apierror' not in video):
			video_url = "http://player.vimeo.com/play_redirect?clip_id=%s&sig=%s&time=%s&quality=%s&codecs=H264,VP8,VP6&type=moogaloop_local&embed_location=" % ( videoid, video['request_signature'], video['request_signature_expires'], quality )
			url = urllib2.Request(video_url)
			url.add_header('User-Agent', self.USERAGENT);
			con = urllib2.urlopen(url);
			video['video_url'] = con.geturl()
			con.close()
			
			if self.dbg:
				print self.plugin + " construct_video_url done"
					
			return ( video, 200 )
		else:
			if self.dbg:
				print self.plugin + " construct_video_url, got apierror: " + video['apierror']
			return (video['apierror'], 303)
		
	def search(self, query, page = "0"):
		if self.dbg:
			print self.plugin + " search: " + repr(query)
		
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.settings.getSetting( "perpage" ) ) ]
		
		result = self.v.vimeo_videos_search(query=query, page=int(page) + 1, per_page=per_page, full_response="true")
		result = self._getvideoinfo(result);
		
		if result:
			if self.dbg:
				print self.plugin + " search done :" + str(len(result))
			return (result, 200)
		else:
			if self.dbg:
				print self.plugin + " search done with no results"
			return (self.language(30601), 303)

	def listVideoFeed(self, params):
		if self.dbg:
			print self.plugin + " listVideoFeed"
				
		get = params.get
		
		page = int(get("page","0")) + 1
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.settings.getSetting( "perpage" ) ) ]

		if (get("channel")):
			result = self.v.vimeo_channels_getVideos(channel_id=get("channel"), page=page, per_page=per_page, full_response="true")
		elif (get("album")):
			result = self.v.vimeo_albums_getVideos(album_id=get("album"), page=page, per_page=per_page, full_response="true")
		elif (get("group")):		
			result = self.v.vimeo_groups_getVideos(group_id=get("group"), page=page, per_page=per_page, full_response="true")

		if (not result):
			if self.dbg:
				print self.plugin + " listVideoFeed result was empty"
			return (result, 303)
		else:
			result = self._getvideoinfo(result);

		if self.dbg:
			print self.plugin + " listVideoFeed done"
				
		return ( result, 200 )
	
	def getUserData(self, params):
		if self.dbg:
			print self.plugin + " getUserData"

		get = params.get

		page = int(get("page", "0")) + 1
		per_page = ( 10, 15, 20, 25, 30, 40, 50, )[ int( self.settings.getSetting( "perpage" ) ) ]
		
		user_id = self.settings.getSetting("userid")

		if (get("external")):
			user_id = get("contact")
		
		if self.dbg:
			print self.plugin + " calling vimeo api for " + get("api") + " with user_id: " + repr(user_id) + " page: " + repr(page) + " per_page: " + repr(per_page)
		
		if (get("api") == "my_videos"):
			result = self.v.vimeo_videos_getAll(user_id=user_id, per_page=per_page, page=page, full_response="true")
			result = self._getvideoinfo(result)  
		elif (get("api") == "my_likes"):
			result = self.v.vimeo_videos_getLikes(user_id=user_id, per_page=per_page, page=page, full_response="true")
			result = self._getvideoinfo(result)
		elif (get("api") == "my_watch_later" and not get("external")):
			result = self.v.vimeo_albums_getWatchLater(per_page=per_page, page=page, full_response="true")
			result = self._getvideoinfo(result)
		elif (get("api") == "my_newsubscriptions"):
			result = self.v.vimeo_videos_getSubscriptions(user_id=user_id, per_page=per_page, page=page, full_response="true", sort="newest")
			result = self._getvideoinfo(result)
		elif (get("api") == "my_albums"):	 
			result = self.v.vimeo_albums_getAll(user_id =user_id, per_page=per_page, page=page, full_response="true")
			result = self._get_list('album', result)
		elif (get("api") == "my_groups"):
			result = self.v.vimeo_groups_getAll(user_id = user_id, per_page=per_page, page=page, full_response="true")
			result = self._get_list('group', result)
		elif (get("api") == "my_channels"):
			result = self.v.vimeo_channels_getAll(user_id = user_id, per_page=per_page, page=page, full_response="true")
			result = self._get_list('channel', result)
		elif (get("api") == "my_contacts"):
			result = self.v.vimeo_contacts_getAll(user_id = user_id, per_page=per_page, page=page, full_response="true")
			result = self._get_contacts(result)
			
		if (not result):
			if self.dbg:
				print self.plugin + " getUserData result was empty"
					
			return (self.language(30602), 303)

		if self.dbg:
			print self.plugin + " getUserData done"
				
		return (result, 200) 

	def _get_return_status(self, result):
		if self.dbg:
			print self.plugin + " _get_return_status "
		
		xml = self.soup.BeautifulStoneSoup(result)
		
		result = [];
		if (len(xml) > 0):
			stat = xml.rsp["stat"]
			if stat == "ok":
				return ( result, 200 )
			elif stat == "fail":
				message = xml.rsp.err["message"]
				if self.dbg:
					print self.plugin + " _get_return_status fail: " + repr(message)
						
				return ( message, 303 )
			else:
				return ( "", 500 )
		else:
			if self.dbg:
				print self.plugin + " _get_return_status invalid response xml from vimeo api"
		
		return ( "No response from Vimeo API", 303 )
																
	def _get_details(self, videoid):
		if self.dbg:
			print self.plugin + " _get_details: " + repr(videoid)
			
		url = urllib2.Request("http://www.vimeo.com/moogaloop/load/clip:%s/local/" % videoid);
		url.add_header('User-Agent', self.USERAGENT);

		con = urllib2.urlopen(url);
		value = con.read()	
		con.close()

		soup = self.soup.BeautifulStoneSoup(value)
		
		result = []
		if (len(soup.video) > 0):
			video = {}
			video['videoid'] = videoid
			title = soup.video.caption.contents[0].encode("utf-8")
			if title:
				title = title.replace("&amp;", "&")
				title = title.replace("&quot;", '"')
				title = title.replace("&hellip;", "...")
				title = title.replace("&gt;",">")
				title = title.replace("&lt;","<")
			else: 
				title = "Unknown"
			video['Title'] = title
			video['Duration'] = soup.video.duration.contents[0]
			video['thumbnail'] = soup.video.thumbnail.contents[0]
			video['Studio'] = soup.video.uploader_display_name.contents[0].encode( "utf-8" )
			video['request_signature'] = soup.request_signature.contents[0]
			video['request_signature_expires'] = soup.request_signature_expires.contents[0]
			video['isHD'] = soup.video.ishd.contents[0]
			result.append(video)
			
		if len(result) == 0:
			if self.dbg:
				print self.plugin + " _get_details result was empty"
			return False
		else:				
			if self.dbg:
				print self.plugin + " _get_details done"
			return result[0];
		
	def _get_list(self, tag, result):
		if self.dbg:
			print self.plugin + " _get_list: "
		
		xml = self.soup.BeautifulStoneSoup(result)
		item = xml.find(name=tag)
		next = "false"
		
		result = [];

		while item != None:
			group = {}
			title = ""
			if (item.find(name="name") != None):
				ti = item.find(name="name")
				title = ti.contents[0]
			else:
				title = item.title.contents[0]
			
			title = self.utils.replaceHtmlCodes(title)
			group[tag] = item["id"]
			group['Title'] = title
			
			if (item.description != None):
				group['Description'] = item.description.contents[0]
			
			if (tag == "group"):
				if item.logo_url != None:
					group["thumbnail"] = item.logo_url.contents[0]
				else:
					group["thumbnail"] = "default"
			if (tag == "album"):
				group["thumbnail"] = self.getThumbnail(item, "default") 
			if (tag == "channel"):
				thumbnail = ""
				if (item.badge_url != None and item.badge_url.contents[0].rfind("default") == -1):
					thumbnail = item.badge_url.contents[0]
				
				if (not thumbnail):
					if (item.logo_url != None and item.logo_url.contents[0].rfind("default") == -1):
						thumbnail = item.logo_url.contents[0]
					else:
						thumbnail = "default"
				group["thumbnail"] = thumbnail

			result.append(group)
			
			item = item.findNextSibling(name=tag)
					
		if len(result) == 0:
			if self.dbg:
				print self.plugin + " _get_list result was empty"
			return False
		else:				
			if self.dbg:
				print self.plugin + " _get_list done"
			return result;
	
	def _get_contacts(self, result):
		if self.dbg:
			print self.plugin + " _get_contacts: " + result
			
		xml = self.soup.BeautifulStoneSoup(result)
		contact = xml.contacts.contact
		next = "false"
		
		result = [];
		
		while contact != None:
			group = {}
			group['contact'] = contact["id"]
			group['Title'] = contact['display_name']
			
			portrait = contact.portraits.portrait
			while (portrait != None):
				
				width = portrait["width"]
				if (int(width) <= 300):
					group['thumbnail'] = portrait.contents[0]
				
				portrait = portrait.findNextSibling(name="portrait")
			result.append(group)
			contact = contact.findNextSibling(name="contact")
					
		if len(result) == 0:
			if self.dbg:
				print self.plugin + " _get_contacts result was empty"
			return False
		else:				
			if self.dbg:
				print self.plugin + " _get_contacts done"
			return result;

	def _getvideoinfo(self, value):
		if self.dbg:
			print self.plugin + " _getvideoinfo: " + str(len(value))
		next = "false"
		vobjects = [];
		
		soup = self.soup.BeautifulStoneSoup(value)
		if not soup.videos:
			return vobjects
		
		if (soup.videos["perpage"] == soup.videos["on_this_page"]):
			next = "true"
	
		entry = soup.videos.video
		
		while (entry != None):
			video = {}
			video['videoid'] = entry["id"]			
			video['Title'] = self.utils.replaceHtmlCodes(entry.title.contents[0])
			
			video['Plot'] = entry.description.contents[0]
			video['Studio'] = entry.owner["display_name"]
			video['contact'] = entry.owner["id"]
			video['thumbnail'] = self.getThumbnail(entry, "default")
			
			duration = int(entry.duration.contents[0])
			video['Duration'] = "%02d:%02d" % ( duration / 60, duration % 60 )
			video["next"] = next
			overlay = self.settings.getSetting( "vidstatus-" + video['videoid'] )
			
			if overlay:
				video['Overlay'] = int(overlay)

			vobjects.append(video)
			entry = entry.findNextSibling(name="video")

		if self.dbg:
			print self.plugin + " _get_videoinfo done"
			
		return vobjects
	
	def getThumbnail(self, item, default = "default"):
		thumb = item.thumbnails.thumbnail
		while thumb != None:
			width = thumb["width"]
			if (width):
				if (self.hq_thumbs):
					if (int(width) <= 640 and thumb.contents[0].rfind("default") == -1):
						default = thumb.contents[0]
				else:
					if (int(width) <= 200 and thumb.contents[0].rfind("default") == -1):
						default = thumb.contents[0]
			thumb = thumb.findNextSibling(name="thumbnail")
		
		return default
