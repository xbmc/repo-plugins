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
from operator import pos

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
		self.current_page = 1
		title = ""
		thumbnail_url = ""
		
		# 
		# Get HTML page...
		#
		html_source = HTTPCommunicator().get( self.video_list_page_url )

		# Parse response...
		soup = BeautifulSoup( html_source )

        #Find link with maximum category 
        #<a href="http://www.botchamaniaarchive.com/category/51-100/">51-100</a></li>		
		categories = soup.findAll('a', attrs={'href': re.compile("^http://www.botchamaniaarchive.com/category/")} )
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(categories)", str(len(categories)) ), xbmc.LOGNOTICE )
		
 		max_category_number = 0
 		max_category = ""
 		for category in categories:
 			category_str = str(category)
 			pos_of_dash = category_str.find('-')
 			if pos_of_dash >= 0:
 				try:
 				 	category_number = int(category_str[pos_of_dash+1:pos_of_dash+1+3])
 				except:
 					category_number = 0
 				if category_number > max_category_number:
 					max_category_number = category_number
 					max_category = category	

 		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "max_category['href']", str(max_category['href']) ), xbmc.LOGNOTICE )

		# 
		# Get HTML page...
		#
 		html_source = HTTPCommunicator().get( max_category['href'] )

		# Parse response...
		soup = BeautifulSoup( html_source ) 		
 		
#		<a class="clip-link" data-id="776" title="Botchamania 252" href="http://www.botchamaniaarchive.com/botchamania-252/">
		video_page_urls = soup.findAll('a', attrs={'href': re.compile("^http://www.botchamaniaarchive.com/botchamania-")} )

		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(video_page_urls)", str(len(video_page_urls)) ), xbmc.LOGNOTICE )

		max_video_page_url_number = 0
 		max_video_page_url = ""
 		for video_page_url in video_page_urls:
 			video_page_url_str = str(video_page_url)
 			pos_of_dash = video_page_url_str.find('http://www.botchamaniaarchive.com/botchamania-')
 			if pos_of_dash >= 0:
 				try:
 				 	video_page_url_number = int(video_page_url_str[pos_of_dash+len('http://www.botchamaniaarchive.com/botchamania-'):pos_of_dash+len('http://www.botchamaniaarchive.com/botchamania-')+3])
 				except:
 					video_page_url_number = 0
 				if video_page_url_number > max_video_page_url_number:
 					max_video_page_url_number = video_page_url_number
 					max_video_page_url = video_page_url	

		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "max_video_page_url_number", str(max_video_page_url_number) ), xbmc.LOGNOTICE )
		
#		http://www.botchamaniaarchive.com/botchamania-27/">
		BASE_URL = "http://www.botchamaniaarchive.com/botchamania-"
		BASE_TITLE = "Botchamania "

		for num in range(1,max_video_page_url_number+1): 
			if num == 1:
				title = str(BASE_TITLE) + '1-2-3'
				video_page_url = str(BASE_URL) + '1-2-3'
			elif num == 2:
				continue
			elif num == 3:
				continue
			else:
				title = str(BASE_TITLE) + str(num)
				video_page_url = str(BASE_URL) + str(num)
				
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_page_url", str(video_page_url) ), xbmc.LOGNOTICE )
			
			# Add to list...
			parameters = {"action" : "play", "video_page_url" : video_page_url}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
			listitem.setInfo( "video", { "Title" : title, "Studio" : "Botchamania" } )
			folder = False
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
			
		#Next page entry...
		if self.next_page_possible == 'True':
			self.next_page = self.current_page + 1 
			parameters = {"action" : "list-specials", "plugin_category" : self.plugin_category, "url" : str(self.base_url) + str(self.next_page) + '/', "next_page_possible": self.next_page_possible}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem (__language__(30503), iconImage = "DefaultFolder.png", thumbnailImage = os.path.join(__images_path__, 'next-page.png'))
			folder = True
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "next url", str(url) ), xbmc.LOGNOTICE )
				
		# Disable sorting...
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
		
		# End of directory...
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
