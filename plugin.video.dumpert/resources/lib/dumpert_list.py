#
# Imports
#
from BeautifulSoup import BeautifulSoup
from dumpert_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from dumpert_utils import HTTPCommunicator
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
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "File", str(__file__) ), xbmc.LOGNOTICE )

		# Parse parameters
		self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
		self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
		self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
	
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.video_list_page_url", str(self.video_list_page_url) ), xbmc.LOGNOTICE )
		
		# Determine current page number and base_url
		#http://www.dumpert.nl/toppers/
		#http://www.dumpert.nl/
		#http://www.dumpert.nl/<thema>/
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
		
		# Find titles and thumnail-urls
		#img src="http://static.dumpert.nl/sq_thumbs/2245331_272bd4c3.jpg" alt="Turnlulz" title="Turnlulz" width="100" height="100" />
		#titles_and_thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://static.dumpert.nl/")} )
		titles_and_thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("thumb")} )
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(titles_and_thumbnail_urls)", str(len(titles_and_thumbnail_urls)) ), xbmc.LOGNOTICE )
		
		# Find video page urls
		#<a href="http://www.dumpert.nl/mediabase/2245331/272bd4c3/turnlulz.html" class="dumpthumb" title="Turnlulz">	
		video_page_urls = soup.findAll('a', attrs={'class': re.compile("dumpthumb")} )
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(video_page_urls)", str(len(video_page_urls)) ), xbmc.LOGNOTICE )
			
		#in thema pages the first thumbnail is a thumbnail of the thema itself and not of a video
		#if that's the case: skip the first thumbnail
		if len(titles_and_thumbnail_urls) == len(video_page_urls) + 1:
			titles_and_thumbnail_urls_index = titles_and_thumbnail_urls_index + 1	
			
		for video_page_url in video_page_urls :
			pos_of_video_tag = str(video_page_url).find('class="video"')
			if pos_of_video_tag >= 0: 
				pass
			else:
				#skip video page url without a video
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "skipped video_page_url without video", str(video_page_url) ), xbmc.LOGNOTICE )
				titles_and_thumbnail_urls_index = titles_and_thumbnail_urls_index + 1
				continue
			
			video_page_url = video_page_url['href']
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_page_url", str(video_page_url) ), xbmc.LOGNOTICE )
			
			#if link doesn't contain 'html': skip the link ('continue')
			if video_page_url.find('html') >= 0:
				pass
			else:
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "skipped video_page_url without html", str(video_page_url) ), xbmc.LOGNOTICE )
				titles_and_thumbnail_urls_index = titles_and_thumbnail_urls_index + 1
				continue
			
			#Make title
			try:
				title = titles_and_thumbnail_urls[titles_and_thumbnail_urls_index]['title']
				#convert from unicode to encoded text (don't use str() to do this)
				title = title.encode('utf-8')	
			#<a href="http://www.dumpert.nl/mediabase/1958831/21e6267f/pixar_s_up_inspreken.html?thema=animatie" class="dumpthumb" title="Pixar's &quot;Up&quot; inspreken ">
			except KeyError:
	 			#http://www.dumpert.nl/mediabase/6532392/82471b66/dumpert_heeft_talent.html
	 			title = str(video_page_url)
	 			pos_last_slash = title.rfind('/')
	 			pos_last_dot = title.rfind('.')
	 			title = title[pos_last_slash + 1:pos_last_dot]
	 			title = title.capitalize()
	 		
			title = title.replace('-',' ')
			title = title.replace('/',' ')
			title = title.replace('_',' ')
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "title", str(title) ), xbmc.LOGNOTICE )

			if titles_and_thumbnail_urls_index >= len(titles_and_thumbnail_urls):
				thumbnail_url = ''
			else:
				thumbnail_url = titles_and_thumbnail_urls[titles_and_thumbnail_urls_index]['src']
				
			# Add to list...
			parameters = {"action" : "play", "video_page_url" : video_page_url}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
			listitem.setInfo( "video", { "Title" : title, "Studio" : "Dumpert" } )
			folder = False
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
			
			titles_and_thumbnail_urls_index = titles_and_thumbnail_urls_index + 1

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
