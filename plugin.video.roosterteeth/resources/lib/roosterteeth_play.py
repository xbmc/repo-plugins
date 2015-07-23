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
import this

reload(sys)  
sys.setdefaultencoding('utf8')

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
		dialogWait.create( __language__(30504), title )

		try:
			if self.IS_SPONSOR == 'true':
 				# Login-url: 'http://roosterteeth.com/login'
 				# 'username':  __settings__.getSetting('username')
 				# 'password': __settings__.getSetting('password')
 				# and something with a cookie ?!
 				#
 				# I have no idea how to do the login stuff :( *shakes fist*
 			 	# And that means no sponsered vidz for anybody! *laments*
 			 	# A sponsor video: "http://roosterteeth.com/episode/rt-sponsor-cut-season-2-rt-life-jeremys-frosting-facial"
 			 	response = requests.get(self.video_page_url) 
			 	html_source = response.text
	 			html_source = html_source.encode('utf-8', 'ignore')
 			else:
 			 	response = requests.get(self.video_page_url) 
			 	html_source = response.text
			 	html_source = html_source.encode('utf-8', 'ignore')
	 	except urllib2.HTTPError, error:
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "HTTPError", str(error) ), xbmc.LOGNOTICE )
			dialogWait.close()
			del dialogWait
			xbmcgui.Dialog().ok( __language__(30000), __language__(30507) % (str(error) ))
			exit(1)

		soup = BeautifulSoup(html_source)
		
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
			search_for_string = "manifest: '"
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
					response = requests.get(m3u8_url) 
			 		html_source = response.text
		 			html_source = html_source.encode('utf-8', 'ignore')
				except urllib2.HTTPError, error:
					if (self.DEBUG) == 'true':
						xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "HTTPError", str(error) ), xbmc.LOGNOTICE )
					dialogWait.close()
					del dialogWait
					xbmcgui.Dialog().ok( __language__(30000), __language__(30507) % (str(error) ))
					exit(1)
					
    			#High quality
    			if self.PREFERRED_QUALITY == '0':
					search_for_string = 'NAME="720"'
					pos_name = str(html_source).find(search_for_string)
					if pos_name >=0 :
						begin_pos_playlist = str(html_source).find('http',pos_name)
						end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
						video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
						have_valid_url = True
    			#Medium	
        		elif self.PREFERRED_QUALITY == '1':
        			search_for_string = 'NAME="360"'
        			pos_name = str(html_source).find(search_for_string)
        			if pos_name >=0 :
						begin_pos_playlist = str(html_source).find('http',pos_name)
						end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
						video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
						have_valid_url = True	
        		#Low
				elif self.PREFERRED_QUALITY == '2':
					search_for_string = 'NAME="270"'
					pos_name = str(html_source).find(search_for_string)
					if pos_name >=0 :
						begin_pos_playlist = str(html_source).find('http',pos_name)
						end_pos_playlist = str(html_source).find("m3u8",begin_pos_playlist) + len("m3u8") 			
						video_url = str(html_source)[begin_pos_playlist:end_pos_playlist]
						have_valid_url = True	

				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "blip playlist video_url", str(video_url) ), xbmc.LOGNOTICE )
		
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
			dialogWait.close()
			del dialogWait
			
			# Play video...
			xbmcPlayer = xbmc.Player()
			xbmcPlayer.play( playlist )
		#
		# Alert user
		#
	 	elif no_url_found:
			xbmcgui.Dialog().ok( __language__(30000), __language__(30505))
		elif unplayable_media_file:
			xbmcgui.Dialog().ok( __language__(30000), __language__(30506))
	
#
# The End
#