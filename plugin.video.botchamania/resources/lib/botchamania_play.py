#
# Imports
#
from BeautifulSoup import BeautifulSoup
from botchamania_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from botchamania_utils import HTTPCommunicator
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
import YDStreamExtractor

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
		self.VIDEO = __settings__.getSetting('video')
		
		if (self.DEBUG) == 'true':
			print 'Python Version: ' + sys.version
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
		
		#We still need to find out the video-url
		if str(self.video_page_url).startswith("http://botchamania.com/"):
			httpCommunicator = HTTPCommunicator()
			
			try:
				html_data = httpCommunicator.get ( self.video_page_url )
			except urllib2.HTTPError, error:
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "first HTTPError", str(error) ), xbmc.LOGNOTICE )
				#Retry to (hopefully) get rid of a time-out http error
				try:
					html_data = httpCommunicator.get ( self.video_page_url )
				except urllib2.HTTPError, error:
					if (self.DEBUG) == 'true':
						xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "second HTTPError", str(error) ), xbmc.LOGNOTICE )
					dialogWait.close()
					del dialogWait
					xbmcgui.Dialog().ok( __language__(30000), __language__(30507) % (str(error) ))
					exit(1)
	
			soup = BeautifulSoup(html_data)
	
	 	    #Parse video file url
			video_urls = soup.findAll('iframe')
		
			video_urls_index = 0
			for video_url in video_urls :
				no_url_found = False
				unplayable_media_file = False
				have_valid_url = False
				
				if len(video_urls) == 0:
					no_url_found = True
				else:
					video_url = video_urls[video_urls_index]['src']
					#eventually fix video-url
					video_url = str(video_url)
					if video_url.startswith("http"):
						pass
					elif video_url.startswith("//"): 
						video_url = "http:" + video_url
					elif video_url.startswith("/"): 
						video_url = "http:/" + video_url
					else: 
						video_url = "http://" + video_url
						
					if (self.DEBUG) == 'true':
						xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_url", str(video_url) ), xbmc.LOGNOTICE )
					
					#This will return True if the URL points (probably) to a video without actually fetching all the stream info:
					#YDStreamExtractor.mightHaveVideo(video_url)	
					YDStreamExtractor.disableDASHVideo(True)  #Kodi (XBMC) only plays the video for DASH streams, so you don't want these normally. Of course these are the only 1080p streams on YouTube
					try:
						vid = YDStreamExtractor.getVideoInfo(video_url,quality=int(self.VIDEO)) #quality is 0=SD, 1=720p, 2=1080p and is a maximum
						#found a working video! (champagne for everybody!), exit the loop
						stream_video_url = vid.streamURL()
						have_valid_url = True
						break
					except:
						#Try another video-url if available
						video_urls_index = video_urls_index + 1
						unplayable_media_file = True
						if (self.DEBUG) == 'true':
							xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "skipping this video_url", str(video_url) ), xbmc.LOGNOTICE )
			
		else:	
			video_url = self.video_page_url
			YDStreamExtractor.disableDASHVideo(True) #Kodi (XBMC) only plays the video for DASH streams, so you don't want these normally. Of course these are the only 1080p streams on YouTube 
			try:
				vid = YDStreamExtractor.getVideoInfo(video_url,quality=int(self.VIDEO)) #quality is 0=SD, 1=720p, 2=1080p and is a maximum
				stream_video_url = vid.streamURL()
				have_valid_url = True
			except:
				unplayable_media_file = True
 	
 		if (self.DEBUG) == 'true':
 			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "have_valid_url", str(have_valid_url) ), xbmc.LOGNOTICE )
 			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_url", str(video_url) ), xbmc.LOGNOTICE )
	
		if have_valid_url:
			playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
			playlist.clear()
		
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
			xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
			listitem.setInfo( "video", { "Title": title, "Studio" : "Botchamania", "Plot" : plot, "Genre" : genre } )
			playlist.add( stream_video_url, listitem )
	
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