#
# Imports
#
from BeautifulSoup import BeautifulSoup
from botchamania_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from botchamania_utils import HTTPCommunicator
import os
import re
import sys
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
		self.DEBUG     = __settings__.getSetting('debug')
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "File", str(__file__) ), xbmc.LOGNOTICE )

		# Parse parameters...
		self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
		self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
		self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.video_list_page_url", str(self.video_list_page_url) ), xbmc.LOGNOTICE )
		
		# Determine base_url
		#find last slash
		pos_of_last_slash 		 	 = self.video_list_page_url.rfind('/')
		#remove last slash
		self.video_list_page_url 	 = self.video_list_page_url[0 : pos_of_last_slash ]
		pos_of_last_slash 		 	 = self.video_list_page_url.rfind('/')
		self.base_url			     = self.video_list_page_url[0 : pos_of_last_slash + 1]
		#add last slash
		self.video_list_page_url 	= str(self.video_list_page_url) + "/" 
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.base_url", str(self.base_url) ), xbmc.LOGNOTICE )
		
		#
		# Get the videos...
		#
		self.getVideos()
	
	#
	# Get videos...
	#
	def getVideos( self ) :
		#
		# Init
		#
		self.thema_base_url = ""
		self.current_page = 1
		title = ""
		thumbnail_url = ""
		
		# 
		# Get HTML page...
		#
		html_source = HTTPCommunicator().get( self.video_list_page_url )

		# Parse response...
		soup = BeautifulSoup( html_source )
		
		video_page_urls = soup.findAll('a')
			
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(video_page_urls)", str(len(video_page_urls)) ), xbmc.LOGNOTICE )
		
		for video_page_url in video_page_urls :
			#http://botchamaniaarchive.com/
			#<a href="https://mega.co.nz/#!LMUWzb5S!Fi3RPBBrgrHWhfIabWD8D2VZEHxJ6hEjqkvXfUG4y9I">Botchamania 10 DL</a>
			#store title
			if str(video_page_url['href']).startswith("https://mega.co.nz/"):  
				title = str(video_page_url.string)
				title = title.replace("DL", "")
				pass
			#http://botchamaniaarchive.com/
			#<a href="http://www.tenchiforum.com/botchamaniaarchive.com/videos/Botchamania 178.mp4">Botchamania 178 DL</a>
			#store title
			elif str(video_page_url['href']).startswith("http://www.tenchiforum.com/"):  
				title = str(video_page_url.string)
				title = title.replace("DL", "")
				pass
			#http://botchamaniaarchive.com/
			#<a href="http://www.youtube.com/watch?v=ZesTkcghTU8">Alt Video Link</a>
			elif video_page_url.string == 'Alt Video Link':
				video_page_url = video_page_url['href']
				
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_page_url", str(video_page_url) ), xbmc.LOGNOTICE )
				
				# Add to list...
				parameters = {"action" : "play", "video_page_url" : video_page_url}
				url = sys.argv[0] + '?' + urllib.urlencode(parameters)
				listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
				listitem.setInfo( "video", { "Title" : title, "Studio" : "Botchamania" } )
				folder = False
				xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
			#Tag contains no title or video-url
			else:
			    pass	

		#Next page entry...
		if self.next_page_possible == 'True':
			self.next_page = self.current_page + 1 
			parameters = {"action" : "list", "plugin_category" : self.plugin_category, "url" : str(self.thema_base_url) + str(self.next_page) + '/', "next_page_possible": self.next_page_possible}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem (__language__(30503), iconImage = "DefaultFolder.png", thumbnailImage = os.path.join(__images_path__, 'next-page.png'))
			folder = True
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "next url", str(url) ), xbmc.LOGNOTICE )
				
		# Sort on labels...
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
		
		# End of directory...
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
