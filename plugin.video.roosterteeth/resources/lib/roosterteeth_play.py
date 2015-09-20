#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from BeautifulSoup import BeautifulSoup
from roosterteeth_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
import requests
import os
import re
import base64
import ast
import sys
import urllib, urllib2
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

LOGINURL = 'http://roosterteeth.com/login'

#
# Main class
#
class Main:
	#
	# Init
	#
	def __init__( self ) :
		# Get plugin settings

		self.DEBUG = __settings__.getSetting('debug')
		self.PREFERRED_QUALITY = __settings__.getSetting('quality')
		self.IS_SPONSOR = __settings__.getSetting('is_sponsor')
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "File", str(__file__) ), xbmc.LOGNOTICE )
		
		# Parse parameters...
		self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.video_page_url", str(self.video_page_url) ), xbmc.LOGNOTICE )
		#
		# Play video...
		#
		self.playVideo()

	#
	# Play video...
	#
	def playVideo( self ) :
		#
		# Init
		#
		no_url_found = False
		unplayable_media_file = False
		have_valid_url = False
		embed_found = False
		
		#
		# Get current list item details...
		#
		title     	  = unicode( xbmc.getInfoLabel( "ListItem.Title"  ), "utf-8" )
		thumbnail_url =          xbmc.getInfoImage( "ListItem.Thumb"  )
		studio    	  = unicode( xbmc.getInfoLabel( "ListItem.Studio" ), "utf-8" )
		plot          = unicode( xbmc.getInfoLabel( "ListItem.Plot"   ), "utf-8" )
		genre         = unicode( xbmc.getInfoLabel( "ListItem.Genre"  ), "utf-8" )
		
		#
		# Show wait dialog while parsing data...
		#
		dialogWait = xbmcgui.DialogProgress()
		dialogWait.create( __language__(30100), title )
		
		try:
			# requests is sooooo nice, respect!
			self.session = requests.Session()
			
			# get the page that contains the video
		 	reply = self.session.get(self.video_page_url)
		 	
			# is it a sponsored video? 
			if str(reply.text).find('sponsor-only') >= 0:
				if self.IS_SPONSOR == 'true':
					try:
						# we need a NEW (!!!) session
						self.session = requests.Session()
						
						# get the LOGIN-page
						reply = self.session.get(LOGINURL)
						
						if (self.DEBUG) == 'true':
					 		xbmc.log('get login page request, status_code:' + str(reply.status_code))
					
						# This is part of the LOGIN page, it contains a token!:
						#
						# 	<input name="_token" type="hidden" value="Zu8TRC43VYiTxfn3JnNgiDnTpbQvPv5xWgzFpEYJ">
						#     <fieldset>
						#       <h3 class="content-title">Log In</h3>
						# 	  <label for="username">Username</label>
						# 	  <input name="username" type="text" value="" id="username">
						# 	  <label for="password">Password</label>
						# 	  <input name="password" type="password" value="" id="password">
						# 	<input type="submit" value="Log in">
						# 	</fieldset>
							
						# get the token
						soup = BeautifulSoup(reply.text)
						video_urls = soup.findAll('input', attrs={'name': re.compile("_token")}, limit=1)
						token = str(video_urls[0]['value'])
					
						# set the needed LOGIN-data
						payload = { '_token': token, 'username': __settings__.getSetting('username'), 'password': __settings__.getSetting('password') }
						# post the LOGIN-page with the LOGIN-data, to actually login this session
						reply = self.session.post(LOGINURL, data=payload)
						
						if (self.DEBUG) == 'true':
							xbmc.log('post login page response, status_code:' + str(reply.status_code))
						
						# check that the login was technically ok (status_code 200). This in itself does NOT mean that the username/password were correct. 
						if reply.status_code == 200:
							pass
							# check that the username is in the response. If that's the case, the login was ok and the username and password in settings are ok.
							if str(reply.text).find(__settings__.getSetting('username')) >= 0:
								if (self.DEBUG) == 'true':
									xbmc.log('login was successfull!')
								pass
							else:
								try:
									dialogWait.close()
									del dialogWait
								except:
									pass
								xbmcgui.Dialog().ok( __language__(30000), __language__(30101), __language__(30102), __language__(30103) )
								exit(1)
						else:
							try:
								dialogWait.close()
								del dialogWait
							except:
								pass
							xbmcgui.Dialog().ok( __language__(30000), __language__(30104) % (str(reply.status_code)) )
							exit(1)
						
						# let's try getting the page again after a login
						reply = self.session.get(self.video_page_url)
							
				 	except urllib2.HTTPError, error:
						if (self.DEBUG) == 'true':
							xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "HTTPError", str(error) ), xbmc.LOGNOTICE )
						try:
							dialogWait.close()
							del dialogWait
						except:
							pass
						xbmcgui.Dialog().ok( __language__(30000), __language__(30106) % (str(error) ))
						exit(1)						
					except:
						exception = sys.exc_info()[0]
						if (self.DEBUG) == 'true':
							xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "Exception1:", str(exception) ), xbmc.LOGNOTICE )
						try:
							dialogWait.close()
							del dialogWait
						except:
							pass
						exit(1)									

				else:
					try:
						dialogWait.close()
						del dialogWait
					except:
						pass
					xbmcgui.Dialog().ok( __language__(30000), __language__(30105) )
					exit(1)

	 	except urllib2.HTTPError, error:
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "HTTPError", str(error) ), xbmc.LOGNOTICE )
				try:
					dialogWait.close()
					del dialogWait
				except:
					pass
			xbmcgui.Dialog().ok( __language__(30000), __language__(30106) % (str(error) ))
			exit(1)
 		except:
 			exception = sys.exc_info()[0]
 			if (self.DEBUG) == 'true':
 				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "Exception2:", str(exception) ), xbmc.LOGNOTICE )
 			try:
 				dialogWait.close()
 				del dialogWait
 			except:
 				pass
 			exit(1)
						
		html_source = reply.text
		html_source = html_source.encode('utf-8', 'ignore')		

		soup = BeautifulSoup(html_source)
		
		video_url = ''
		no_url_found = True
		have_valid_url = False
		youtube_video = False
		blip_video = False
		cloudfront_video = False
		
		# Is it a youtube video ?
		# f.e. http://ah.roosterteeth.com/episode/happy-hour-season-1-happy-hour-1
		#       <script>
		#             onYouTubeIframeAPIReady = RT.youtube.onReady;
		#             RT.youtube.player({
		#                 iframeId: "iframe-9415",
		#                 videoId: '9415',
		#                 youtubeKey: 'zRc1CcRDI_k',
		#                 autoplay: 1,
		#                 markWatchedForm : 'watch-11630'
		#             });
		#       </script>      
		search_for_string = "youtubeKey: '"
		begin_pos_search_for_youtubeID = str(html_source).find(search_for_string)
		if begin_pos_search_for_youtubeID >= 0:
			begin_pos_youtubeID = begin_pos_search_for_youtubeID + len(search_for_string)
			youtube_video = True
			rest = str(html_source)[begin_pos_youtubeID:]
			length_youtubeID = rest.find("'")
			end_pos_youtubeID = begin_pos_youtubeID + length_youtubeID
			youtubeID = str(html_source)[begin_pos_youtubeID:end_pos_youtubeID]		
			video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtubeID
			have_valid_url = True		
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "youtube video_url", str(video_url) ), xbmc.LOGNOTICE )
		
		if have_valid_url:
			pass
		else:
			# Is it a blip tv video ?
			# f.e. http://ah.roosterteeth.com/episode/happy-hour-season-1-happy-hour-5
			#manifest: 'http://wpc.1765A.taucdn.net/801765A/video/blip/9704/9704-manifest.m3u8'
			
#			The content looks something like this
#			#EXTM3U
#			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=872448,RESOLUTION=640x360,NAME="360"
#			http://wpc.1765A.taucdn.net/831765A/video/blip/9704/RoosterTeeth-RTLifePresentsHappyHour5932.m4v.m3u8
#			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=615424,RESOLUTION=480x270,NAME="270"
#			http://wpc.1765A.taucdn.net/831765A/video/blip/9704/RoosterTeeth-RTLifePresentsHappyHour5539.mp4.m3u8
#			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3024896,RESOLUTION=1280x720,NAME="720"
#			http://wpc.1765A.taucdn.net/831765A/video/blip/9704/RoosterTeeth-RTLifePresentsHappyHour5425.m4v.m3u8

#           or like this for a sponsored video f.e.: "http://www.roosterteeth.com/episode/rt-sponsor-cut-season-2-kerry-comes-out-of-the-closet"
#			#EXTM3U
#           #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=559104,RESOLUTION=640x360,NAME="360"
#           http://wpc.1765A.taucdn.net/831765A/video/blip/1684/RoosterTeeth-KerryComesOutOfCloset959.m4v.m3u8

#			or like this for achievementhunter f.e.: "http://achievementhunter.com/episode/lets-play-lets-play-let-s-play-no-time-to-explain"
# 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=16655000,RESOLUTION=1920x1080,CODECS="avc1.4d001f,mp4a.40.2"
# 			1080P.m3u8
# 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=7264000,RESOLUTION=1280x720,CODECS="avc1.4d001f,mp4a.40.2"
# 			720P.m3u8
# 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3377000,RESOLUTION=640x360,CODECS="avc1.4d001f,mp4a.40.2"
# 			480P.m3u8
# 			#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1740000,RESOLUTION=426x238,CODECS="avc1.4d001f,mp4a.40.2"
# 			240P.m3u8

			search_for_string = "manifest: '"
			begin_pos_search_for_blip = str(html_source).find(search_for_string)
			if begin_pos_search_for_blip < 0:
				#if nothings found, let's try and search for something else 	
				search_for_string = "file: '"
				begin_pos_search_for_blip = str(html_source).find(search_for_string)
				if begin_pos_search_for_blip < 0:
					#if nothings found, let's try and search for something else 	
					search_for_string = "file : '"
					begin_pos_search_for_blip = str(html_source).find(search_for_string)
					
			if begin_pos_search_for_blip >= 0:
				begin_pos_m3u8_url = begin_pos_search_for_blip + len(search_for_string)
				blip_video = True
				rest = str(html_source)[begin_pos_m3u8_url:]
				length_m3u8_url = rest.find("'")
				end_pos_m3u8_url = begin_pos_m3u8_url + length_m3u8_url	
				m3u8_url = str(html_source)[begin_pos_m3u8_url:end_pos_m3u8_url]				
			
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "blip playlists m3u8_url", str(m3u8_url) ), xbmc.LOGNOTICE )
				
				try:
					reply = self.session.get(m3u8_url) 
					html_source = reply.text

					if (self.DEBUG) == 'true':
						xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "content blip playlists m3u8_url", str(html_source) ), xbmc.LOGNOTICE )
					
	 				html_source = html_source.encode('utf-8', 'ignore')
				except urllib2.HTTPError, error:
					if (self.DEBUG) == 'true':
						xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "HTTPError", str(error) ), xbmc.LOGNOTICE )
					try:
						dialogWait.close()
						del dialogWait
					except:
						pass
					xbmcgui.Dialog().ok( __language__(30000), __language__(30106) % (str(error) ))
					exit(1)
				
				#Very High quality
				if self.PREFERRED_QUALITY == '0':
					search_for_string = '1080'
					pos_name = str(html_source).find(search_for_string)
					if pos_name >=0 :
						begin_pos_playlist = str(html_source).find('http',pos_name)
						if begin_pos_playlist == -1:
							video_url = str(m3u8_url).replace('index', str(search_for_string) + 'P')
							have_valid_url = True
						else:
							end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
							video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
							have_valid_url = True
					else:
						search_for_string = '720'
						pos_name = str(html_source).find(search_for_string)
						if pos_name >=0 :
							begin_pos_playlist = str(html_source).find('http',pos_name)
							if begin_pos_playlist == -1:
								video_url = str(m3u8_url).replace('index', str(search_for_string) + 'P')
								have_valid_url = True
							else:
								end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
								video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
								have_valid_url = True
						else:
							search_for_string = '360'
							pos_name = str(html_source).find(search_for_string)
							if pos_name >=0 :
								begin_pos_playlist = str(html_source).find('http',pos_name)
								if begin_pos_playlist == -1:
									video_url = str(m3u8_url).replace('index', str(search_for_string) + 'P')
									have_valid_url = True
								else:
									end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
									video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
									have_valid_url = True
							else:
								search_for_string = '270'
								pos_name = str(html_source).find(search_for_string)
								if pos_name >=0 :
									begin_pos_playlist = str(html_source).find('http',pos_name)
									if begin_pos_playlist == -1:
										video_url = str(m3u8_url).replace('index', str(search_for_string) + 'P')
										have_valid_url = True
									else:
										end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
										video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
										have_valid_url = True				
    			#High quality
				elif self.PREFERRED_QUALITY == '1':
					search_for_string = '720'
					pos_name = str(html_source).find(search_for_string)
					if pos_name >=0 :
						begin_pos_playlist = str(html_source).find('http',pos_name)
						if begin_pos_playlist == -1:
							video_url = str(m3u8_url).replace('index', str(search_for_string) + 'P')
							have_valid_url = True
						else:
							end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
							video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
							have_valid_url = True
					else:
						search_for_string = '360'
						pos_name = str(html_source).find(search_for_string)
						if pos_name >=0 :
							begin_pos_playlist = str(html_source).find('http',pos_name)
							if begin_pos_playlist == -1:
								video_url = str(m3u8_url).replace('index', str(search_for_string) + 'P')
								have_valid_url = True
							else:
								end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
								video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
								have_valid_url = True
						else:
							search_for_string = '270'
							pos_name = str(html_source).find(search_for_string)
							if pos_name >=0 :
								begin_pos_playlist = str(html_source).find('http',pos_name)
								if begin_pos_playlist == -1:
									video_url = str(m3u8_url).replace('index', str(search_for_string) + 'P')
									have_valid_url = True
								else:
									end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
									video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
									have_valid_url = True								
    			#Medium	
				elif self.PREFERRED_QUALITY == '2':
					search_for_string = '360'
					pos_name = str(html_source).find(search_for_string)
					if pos_name >=0 :
						begin_pos_playlist = str(html_source).find('http',pos_name)
						if begin_pos_playlist == -1:
							video_url = str(m3u8_url).replace('index', str(search_for_string) + 'P')
							have_valid_url = True
						else:
							end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
							video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
							have_valid_url = True
					else:
						search_for_string = '270'
						pos_name = str(html_source).find(search_for_string)
						if pos_name >=0 :
							begin_pos_playlist = str(html_source).find('http',pos_name)
							if begin_pos_playlist == -1:
								video_url = str(m3u8_url).replace('index', str(search_for_string) + 'P')
								have_valid_url = True
							else:
								end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
								video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
								have_valid_url = True							
        		#Low
				elif self.PREFERRED_QUALITY == '3':
					search_for_string = '270'
					pos_name = str(html_source).find(search_for_string)
					if pos_name >=0 :
						begin_pos_playlist = str(html_source).find('http',pos_name)
						if begin_pos_playlist == -1:
							video_url = str(m3u8_url).replace('index', str(search_for_string) + 'P')
							have_valid_url = True
						else:
							end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
							video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
							have_valid_url = True								

				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "blip playlist video_url", str(video_url) ), xbmc.LOGNOTICE )
				
				#last ditch effort when m3u8 content wasn't quite what i expected 
				if video_url == '':
					video_url = m3u8_url	
					have_valid_url = True			
					if (self.DEBUG) == 'true':
						xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "corrected blip playlist video_url", str(video_url) ), xbmc.LOGNOTICE )
		
		if have_valid_url:
			pass
		else:
			# Is it a cloudfront tv video ?
			#     <script type='text/javascript'>
			#                     jwplayer('video-9902').setup({
			#                         image: "http://s3.amazonaws.com/s3.roosterteeth.com/assets/epart/ep9902.jpg",
			#                         sources: [
			#                             {file: "http://d1gi7itbhq9gjf.cloudfront.net/encoded/9902/RT_54526b494490c6.67517070-480p.mp4", label: "480p SD","default": "true"},
			#                             {file: "http://d1gi7itbhq9gjf.cloudfront.net/encoded/9902/RT_54526b494490c6.67517070-720p.mp4", label: "720p HD"},
			#                             {file: "http://d1gi7itbhq9gjf.cloudfront.net/encoded/9902/RT_54526b494490c6.67517070-1080p.mp4", label: "1080p HD"},
			#                         ],
			#                         title: 'RWBY Volume 2, Chapter 12',
			#                         width: '590',
			#                         height: '405',
			#                         aspectratio: '16:9',
			#                         sharing: '{}',
			#                           advertising: {
			#                             client: 'googima',
			#                             tag: 'http://googleads.g.doubleclick.net/pagead/ads?ad_type=video&client=ca-video-pub-0196071646901426&description_url=http%3A%2F%2Froosterteeth.com&videoad_start_delay=0&hl=en&max_ad_duration=30000'
			#                           }
			#                     });
			#                 </script>			
			search_for_string = "sources"
			begin_pos_search_for_cloudfront = str(html_source).find(search_for_string)
			if begin_pos_search_for_cloudfront == -1: 
				path = ""
			else:
				start_pos_480p = data.find("{",begin_pos_search_for_cloudfront)
				end_pos_480p = data.find("}",start_pos_480p + 1)
				string_480p = data[start_pos_480p:end_pos_480p + 1]
				start_pos_480p_file = string_480p.find("http")
				end_pos_480p_file = string_480p.find('"',start_pos_480p_file + 1)
				string_480p_file = string_480p[start_pos_480p_file:end_pos_480p_file]
				
				start_pos_720p = data.find("{",end_pos_480p + 1)
				end_pos_720p = data.find("}",start_pos_720p + 1)
				string_720p = data[start_pos_720p:end_pos_720p + 1]
				start_pos_720p_file = string_720p.find("http")
				end_pos_720p_file = string_720p.find('"',start_pos_720p_file + 1)
				string_720p_file = string_720p[start_pos_720p_file:end_pos_720p_file]
				
				start_pos_1080p = data.find("{",end_pos_720p + 1)
				end_pos_1080p = data.find("}",start_pos_1080p + 1)
				string_1080p = data[start_pos_1080p:end_pos_1080p + 1]
				start_pos_1080p_file = string_1080p.find("http")
				end_pos_1080p_file = string_1080p.find('"',start_pos_1080p_file + 1)
				string_1080p_file = string_1080p[start_pos_1080p_file:end_pos_1080p_file]
				
				# high video quality  
				if self.PREFERRED_QUALITY == '0':
					video_url = string_1080p_file
					have_valid_url = True	
				# medium video quality  
				elif self.PREFERRED_QUALITY == '1':
					video_url = string_720p_file
					have_valid_url = True	
				# low video quality          
				elif self.PREFERRED_QUALITY == '2':
					video_url = string_480p_file
					have_valid_url = True	
				
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "cloudfront video_url", str(video_url) ), xbmc.LOGNOTICE )
		
		# Play video...
		if have_valid_url:
			playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
			playlist.clear()
		
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
			xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
			listitem.setInfo( "video", { "Title": title, "Studio" : "roosterteeth", "Plot" : plot, "Genre" : genre } )
			playlist.add( video_url, listitem )
	
			# Close wait dialog...
			try:
				dialogWait.close()
				del dialogWait
			except:
				pass
			
			# Play video...
			xbmcPlayer = xbmc.Player()
			xbmcPlayer.play( playlist )
		#
		# Alert user
		#
	 	elif no_url_found:
			xbmcgui.Dialog().ok( __language__(30000), __language__(30107))
		elif unplayable_media_file:
			xbmcgui.Dialog().ok( __language__(30000), __language__(30108))

#
# The End
#