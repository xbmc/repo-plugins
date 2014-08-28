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
		self.DEBUG = __settings__.getSetting('debug')
		
		if (self.DEBUG) == 'true':
			print 'Python Version: ' + sys.version
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "File", str(__file__) ), xbmc.LOGNOTICE )

		# Parse parameters
		self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
		self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
		self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
	
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.video_list_page_url", str(self.video_list_page_url) ), xbmc.LOGNOTICE )
		
		# Determine current page number and base_url
		#find last slash
		pos_of_last_slash 		 	 = self.video_list_page_url.rfind('/')
		#remove last slash
		self.video_list_page_url 	 = self.video_list_page_url[0 : pos_of_last_slash ]
		pos_of_last_slash 		 	 = self.video_list_page_url.rfind('/')
		self.base_url			     = self.video_list_page_url[0 : pos_of_last_slash + 1]
		self.current_page 		 	 = self.video_list_page_url[pos_of_last_slash + 1:]
		self.current_page 		 	 = int(self.current_page) 
		#add last slash
		self.video_list_page_url = str(self.video_list_page_url) + "/" 
		
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
		titles_and_thumbnail_urls_index = 0
		
		# 
		# Get HTML page
		#
		html_source = HTTPCommunicator().get( self.video_list_page_url )

		# Parse response
		soup = BeautifulSoup( html_source )
		
		# Find titles, thumbnail-urls and videopage-urls
		#<div class="item-header">
		#  <a href="http://botchamania.com/delriomania/" class="img-hover-effect loadingvideo">
		#     <img src="http://botchamania.com/wp-content/themes/videomag-theme/images/aspect-px.png" width="16" height="9" class="aspect-px" rel="http://botchamania.com/wp-content/uploads/2014/08/delriomania-549x316_c.jpg" alt="DelRioMania" />
		#  </a>
		#</div>
		titles_thumbnail_videopage_urls = soup.findAll('div', attrs={'class': re.compile("item-header")} )
		
		#dirty remove of last 3 found item-headers (Popular Posts)
		if len(titles_thumbnail_videopage_urls) >= 3:
			titles_thumbnail_videopage_urls = titles_thumbnail_videopage_urls[0:len(titles_thumbnail_videopage_urls)-3]

		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(titles_thumbnail_videopage_urls)", str(len(titles_thumbnail_videopage_urls)) ), xbmc.LOGNOTICE )

		for titles_thumbnail_videopage_url in titles_thumbnail_videopage_urls :
			video_page_url = titles_thumbnail_videopage_url.a['href']
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_page_url", str(video_page_url) ), xbmc.LOGNOTICE )

 			#Make title
 			try:
 				title = titles_thumbnail_videopage_url.img['alt']
 				#convert from unicode to encoded text (don't use str() to do this)
 				title = title.encode('utf-8')	
			except KeyError:
 	 			pass
 	 		
 			title = title.replace('-',' ')
 			title = title.replace('/',' ')
 			title = title.replace('_',' ')
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "title", str(title) ), xbmc.LOGNOTICE )

			thumbnail_url = titles_thumbnail_videopage_url.img['rel']

			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "thumbnail_url", str(thumbnail_url) ), xbmc.LOGNOTICE )

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
			parameters = {"action" : "list", "plugin_category" : self.plugin_category, "url" : str(self.base_url) + str(self.next_page) + '/', "next_page_possible": self.next_page_possible}
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