#
# Imports
#
from BeautifulSoup import BeautifulSoup
from dumpert_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
import requests
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
		#http://www.dumpert.nl/
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
		thumbnail_urls_index = 0
		
		# 
		# Get HTML page...
		#
 		html_source = requests.get(self.video_list_page_url).text

		# Parse response...
		soup = BeautifulSoup( html_source )
		
		#<img src="http://static.dumpert.nl/s/trailerts_gr.jpg" alt="" />
		thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://static.dumpert.nl/")} )
										
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(thumbnail_urls)", str(len(thumbnail_urls)) ), xbmc.LOGNOTICE )
			
		#<a href="/themas/uit_het_archief/" class="themalink big">
		#<a href="/themas/liev/" class="themalink">	
		video_page_urls = soup.findAll('a', attrs={'class': re.compile("^themalink")} )
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(video_page_urls)", str(len(video_page_urls)) ), xbmc.LOGNOTICE )
					
		for video_page_url in video_page_urls :
			video_page_url = video_page_url['href']
			#remove '/themas/'
			video_page_url = video_page_url.replace('/themas/','')
			#http://www.dumpert.nl/<thema>/
			self.thema_base_url = str(self.base_url) + str(video_page_url)
			self.current_page = 1
						
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.thema_base_url", str(self.thema_base_url) ), xbmc.LOGNOTICE )	
						
			#Make title
			#http://static.dumpert.nl/themas/politiek_kl.jpg
			title = str(video_page_url)
			pos_of_last_slash = title.rfind('/')
			#remove last slash
			title = title[0 : pos_of_last_slash ]
			pos_of_last_slash = title.rfind('/')
			title = title[pos_of_last_slash + 1:]
			title = title.capitalize()
			title = title.replace('-',' ')
			title = title.replace('/',' ')
			title = title.replace('_kl','')
			title = title.replace('_',' ')
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "title", str(title) ), xbmc.LOGNOTICE )

			if thumbnail_urls_index >= len(thumbnail_urls):
				thumbnail_url = ''
			else:
				thumbnail_url = thumbnail_urls[thumbnail_urls_index]['src']
			
			# Add to list...
			parameters = {"action" : "list", "plugin_category" : self.plugin_category, "url" : str(self.thema_base_url) + str(self.current_page) + '/', "next_page_possible": "True"}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
			listitem.setInfo( "video", { "Title" : title, "Studio" : "Dumpert" } )
			folder = True
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
			
			thumbnail_urls_index = thumbnail_urls_index + 1

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
