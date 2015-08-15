#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from BeautifulSoup import BeautifulSoup
from gamekings_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from gamekings_utils import HTTPCommunicator
import os
import re
import sys
import base64
import urllib, urllib2
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

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
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "File", str(__file__) ), xbmc.LOGNOTICE )
		
		# Parse parameters
		self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
		self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.video_page_url", str(self.video_page_url) ), xbmc.LOGNOTICE )

		#
		# Play video
		#
		self.playVideo()
	
	#
	# Play video
	#
	def playVideo( self ) :
		#
		# Init
		#
		no_url_found = False
		unplayable_media_file = False
		have_valid_url = False
		
		#
		# Get current list item details
		#
		title     = unicode( xbmc.getInfoLabel( "ListItem.Title"  ), "utf-8" )
		thumbnail =          xbmc.getInfoImage( "ListItem.Thumb"  )
		studio    = unicode( xbmc.getInfoLabel( "ListItem.Studio" ), "utf-8" )
		plot      = unicode( xbmc.getInfoLabel( "ListItem.Plot"   ), "utf-8" )
		genre     = unicode( xbmc.getInfoLabel( "ListItem.Genre"  ), "utf-8" )
		
		#
		# Show wait dialog while parsing data
		#
		dialogWait = xbmcgui.DialogProgress()
		dialogWait.create( __language__(30504), title )
		
		httpCommunicator = HTTPCommunicator()
		
		#Sometimes a page request gets a HTTP Error 500: Internal Server Error
		#f.e. http://www.gamekings.tv/videos/het-fenomeen-minecraft/
		try:
			html_data = httpCommunicator.get ( self.video_page_url )
		except urllib2.HTTPError, error:
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "HTTPError", str(error) ), xbmc.LOGNOTICE )
			dialogWait.close()
			del dialogWait
			xbmcgui.Dialog().ok( __language__(30000), __language__(30507) % (str(error) ))
			exit(1)
			
		soup = BeautifulSoup(html_data)
		
		stream_gamekings_tv = False
		gogo_video = False
		gogo_youtube_video = False
		youtube_video = False

		# Get the video url

		# Is a stream?	
		
		#this is f.e. for Videos		
		#<meta property="og:video" content="http://stream.gamekings.tv/20130306_SpecialForces.mp4"/>
		#sometimes the content is not (!!) correct and the real link will be "http://stream.gamekings.tv/large/20130529_E3Journaal.mp4" :(
		#May 2014: videos are vimeo files now:
		#<meta property="og:video" content="http://stream.gamekings.tv/http://player.vimeo.com/external/111637217.hd.mp4?s=10e5d0efd4d10756b535b115140ebe13"/>
		video_urls = soup.findAll('meta', attrs={'content': re.compile("^http://stream.gamekings.tv/")}, limit=1)
		if len(video_urls) == 0:
			#let's search for something else 

			# is it youtube?
			
			#<iframe src="https://www.youtube.com/embed/8wTWeRg8RGQ" height="315" width="560" allowfullscreen="" frameborder="0"></iframe>
			video_urls = soup.findAll('iframe', attrs={'src': re.compile("^https://www.youtube.com/embed/")}, limit=1)
			if len(video_urls) == 0:
				pos_of_gogoVideo = str(html_data).find('gogoVideo')
				pos_of_youtube = str(html_data).find('www.youtube.com/watch?')
				
				# is it gogo video or gogo youtube video?
				
				if pos_of_gogoVideo < 0:
					pass
				else:
					if pos_of_youtube < 0:
		 				#This is f.e. for Gamekings Extra
		 				#<script type="text/javascript">
		 				#   gogoVideo(92091,"MjAxNDExMTNfRXh0cmEubXA0LGh0dHA6Ly93d3cuZ2FtZWtpbmdzLnR2L3dwLWNvbnRlbnQvdXBsb2Fkcy8yMDE0MTExNF9FeHRyYV9zcGxhc2gtMTAyNHg1NzYuanBnLEdhbWVraW5ncyBFeHRyYTogV2Vsa2UgZ2FtZXMgc3BlbGVuIHdpaiBkaXQgbmFqYWFyPw==");
		 				#</script>
		 				#the base86 encode string looks like this decoded:
		 				#20141113_Extra.mp4,http://www.gamekings.tv/wp-content/uploads/20141114_Extra_splash-1024x576.jpg,Gamekings Extra: Welke games spelen wij dit najaar?
						gogo_video = True
					else:
						#This is f.e. for Trailers
						#gogoVideo("http://www.gamekings.tv/wp-content/uploads/nieuws20150723_LifeisStrangeE4-1024x576.jpg","http://www.youtube.com/watch?v=AukgNY6Uxww",pseudo,host);
						gogo_youtube_video = True
			else:
				youtube_video = True
		else:
			stream_gamekings_tv = True
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "stream_gamekings_tv", str(stream_gamekings_tv) ), xbmc.LOGNOTICE )
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "gogo_video", str(gogo_video) ), xbmc.LOGNOTICE )
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "youtube_video", str(youtube_video) ), xbmc.LOGNOTICE )
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "gogo_youtube_video", str(gogo_youtube_video) ), xbmc.LOGNOTICE )
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(video_urls)", str(len(video_urls)) ), xbmc.LOGNOTICE )
		
		if stream_gamekings_tv or gogo_video or youtube_video or gogo_youtube_video :
			if stream_gamekings_tv:
				video_url = str(video_urls[0]['content'])
			elif gogo_video:
				search_for_string = 'gogoVideo'
				begin_pos = str(html_data).find(search_for_string)
				begin_pos_encoded_string = str(html_data).find('"',begin_pos)
				end_pos_encoded_string = str(html_data).find('"',begin_pos_encoded_string + 1)
				encoded_string = str(html_data)[begin_pos_encoded_string + 1:end_pos_encoded_string]
				video_urls_dec = str(base64.b64decode(encoded_string))
				video_urls_dict = video_urls_dec.split(',')
				video_url = str(video_urls_dict[0])
			elif youtube_video:
				video_url = str(video_urls[0]['src'])	
			elif gogo_youtube_video:
				search_for_string = 'www.youtube.com/watch?v='
				begin_pos = str(html_data).find(search_for_string) + len('www.youtube.com/watch?v=')
				end_pos = str(html_data).find('"',begin_pos)
				youtubeID = str(html_data)[begin_pos:end_pos]
				video_url = youtubeID

			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_url", str(video_url) ), xbmc.LOGNOTICE )

			# Check if it's a vimeo file
			if video_url.count("vimeo") > 0:
				#the vimeo video_url looks like this: http://stream.gamekings.tv/http://player.vimeo.com/external/118907131.hd.mp4?s=486e834bab4dc380743d814653c52050
				#therefore the stream stuff got to be removed
				video_url = video_url.replace("http://stream.gamekings.tv/large", "")
				video_url = video_url.replace("http://stream.gamekings.tv/", "")
				have_valid_url = True
			else:
				if youtube_video:
					youtubeID = video_url.replace("https://www.youtube.com/embed/", "")
					video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtubeID
					have_valid_url = True
				else:
					if gogo_youtube_video:
						video_url = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtubeID
						have_valid_url = True
					else:
						video_url = "http://stream.gamekings.tv/large/" + video_url
						if httpCommunicator.exists( video_url ):
							have_valid_url = True
						else:
							video_url = video_url.replace("http://stream.gamekings.tv/large", "http://stream.gamekings.tv/")
							if httpCommunicator.exists( video_url ):
								have_valid_url = True
							else:
								unplayable_media_file = True
		else:
			no_url_found = True
		
		if have_valid_url:
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_url to be played", str(video_url) ), xbmc.LOGNOTICE )
				
		# Play video
		if have_valid_url:
			playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
			playlist.clear()
		
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
			xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
			listitem.setInfo( "video", { "Title": title, "Studio" : "Gamekings", "Plot" : plot, "Genre" : genre } )
			playlist.add( video_url, listitem )
	
			# Close wait dialog
			dialogWait.close()
			del dialogWait
			
			# Play video
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