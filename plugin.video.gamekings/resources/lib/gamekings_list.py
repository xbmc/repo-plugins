#
# Imports
#
from BeautifulSoup import BeautifulSoup
from gamekings_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from gamekings_utils import HTTPCommunicator
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
		
		if self.next_page_possible == 'True':
		# Determine current item number, next item number, next_url
		#f.e. http://www.gamekings.tv/category/videos/page/001/
			pos_of_page		 			 	 = self.video_list_page_url.rfind('/page/')
			if pos_of_page >= 0:
				page_number_str			     = str(self.video_list_page_url[pos_of_page + len('/page/'):pos_of_page + len('/page/') + len('000')])
				page_number					 = int(page_number_str)
				page_number_next			 = page_number + 1
				if page_number_next >= 100:
					page_number_next_str = str(page_number_next)
				elif page_number_next >= 10:
					page_number_next_str = '0' + str(page_number_next)
				else:				
					page_number_next_str = '00' + str(page_number_next)
				self.next_url = str(self.video_list_page_url).replace(page_number_str, page_number_next_str)
			
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.next_url", str(urllib.unquote_plus(self.next_url)) ), xbmc.LOGNOTICE )
	
		#
		# Get the videos
		#
		self.getVideos()
	
	#
	# Get videos
	#
	def getVideos( self ) :
		#
		# Init
		#
		thumbnail_urls_index = 0
		
		# 
		# Get HTML page
		#
		html_source = HTTPCommunicator().get( self.video_list_page_url )

		# Parse response
		soup = BeautifulSoup( html_source )
		
		# Get the thumbnail urls
		#<img src="http://www.gamekings.tv/wp-content/uploads/20130307_gowascensionreviewsplash1-75x75.jpg" alt="God of War: Ascension Review">
		#for http://www.gamekings.tv/pcgamersunite/ the thumbnail links sometimes contain '//': f.e. http://www.gamekings.tv//wp-content/uploads/20110706_hww_alienwarelaptop_slider-75x75.jpg
		#thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://www.gamekings.tv/wp-content/uploads/")})
		thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://www.gamekings.tv/")})
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(thumbnail_urls)", str(len(thumbnail_urls)) ), xbmc.LOGNOTICE )
		
		# Get the titles and video page urls
		#<a href="http://www.gamekings.tv/videos/lars-gustavsson-over-battlefield-4/" title="Lars Gustavsson over Battlefield 4">
		#skip this: <a href='http://www.gamekings.tv/videos/lars-gustavsson-over-battlefield-4/#disqus_thread'>
		
		#this is Videos	
		if self.plugin_category == __language__(30000):
			video_page_urls_and_titles = soup.findAll('a', attrs={'href': re.compile("^http://www.gamekings.tv/")})
		#this is Afleveringen	
		elif self.plugin_category == __language__(30001):
			video_page_urls_and_titles = soup.findAll('a', attrs={'href': re.compile("^http://www.gamekings.tv/")})
		#this is Gamekings Extra	
		elif self.plugin_category == __language__(30002):
			video_page_urls_and_titles = soup.findAll('a', attrs={'href': re.compile("^http://www.gamekings.tv/nieuws/")})
		#this is Trailers
		elif self.plugin_category == __language__(30003):
			video_page_urls_and_titles = soup.findAll('a', attrs={'href': re.compile("^http://www.gamekings.tv/nieuws/")})
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(video_page_urls_and_titles)", str(len(video_page_urls_and_titles)) ), xbmc.LOGNOTICE )
			
		for video_page_url_and_title in video_page_urls_and_titles :
			video_page_url = video_page_url_and_title['href']
			#if link ends with a '/': process the link, if not: skip the link
			if video_page_url.endswith('/'):
				pass
			else:
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "skipped video_page_url not ending on '/'", str(video_page_url) ), xbmc.LOGNOTICE )
				continue

			#this is category Videos		
			if self.plugin_category == __language__(30000):
			    if video_page_url.find('videos') >= 0:
			    	pass
			    elif video_page_url.find('uncategorized') >= 0:
			    	pass
			    else:
					#skip url
					if (self.DEBUG) == 'true':
						xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "skipped video_page_url aflevering in video category", str(video_page_url) ), xbmc.LOGNOTICE )
					continue

			#don't skip aflevering if category is 'afleveringen'			
			if self.plugin_category == __language__(30001):
				pass
			#if 'aflevering' found in video page url, skip the video page url
			elif video_page_url.find('aflevering') >= 0:
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "skipped video_page_url aflevering in non-afleveringen category", str(video_page_url) ), xbmc.LOGNOTICE )
			#skip the thumbnail too			
				thumbnail_urls_index = thumbnail_urls_index + 1
				continue
			
			# Make title
			#for category is 'afleveringen' use the video_page_url to make the title	
			if self.plugin_category == __language__(30001):
				title = str(video_page_url)
				title = title[31:]
				title = title.capitalize()
			#for other categories use the title attribute	
			else:
				title = video_page_url_and_title['title']
				#convert from unicode to encoded text (don't use str() to do this)
				title = title.encode('utf-8')
			
			title = title.replace('-',' ')
			title = title.replace('/',' ')
			title = title.replace(' i ',' I ')
			title = title.replace(' ii ',' II ')
			title = title.replace(' iii ',' III ')
			title = title.replace(' iv ',' IV ')
			title = title.replace(' v ',' V ')
			title = title.replace(' vi ',' VI ')
			title = title.replace(' vii ',' VII ')
			title = title.replace(' viii ',' VIII ')
			title = title.replace(' ix ',' IX ')
			title = title.replace(' x ',' X ')
			title = title.replace(' xi ',' XI ')
			title = title.replace(' xii ',' XII ')
			title = title.replace(' xiii ',' XIII ')
			title = title.replace(' xiv ',' XIV ')
			title = title.replace(' xv ',' XV ')
			title = title.replace(' xvi ',' XVI ')
			title = title.replace(' xvii ',' XVII ')
			title = title.replace(' xviii ',' XVIII ')
			title = title.replace(' xix ',' XIX ')
			title = title.replace(' xx ',' XXX ')
			title = title.replace(' xxi ',' XXI ')
			title = title.replace(' xxii ',' XXII ')
			title = title.replace(' xxiii ',' XXIII ')
			title = title.replace(' xxiv ',' XXIV ')
			title = title.replace(' xxv ',' XXV ')
			title = title.replace(' xxvi ',' XXVI ')
			title = title.replace(' xxvii ',' XXVII ')
			title = title.replace(' xxviii ',' XXVIII ')
			title = title.replace(' xxix ',' XXIX ')
			title = title.replace(' xxx ',' XXX ')
						
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "title", str(title) ), xbmc.LOGNOTICE )
			
			title_lowercase = str(title.lower())
			
			#this is category Gamekings Extra
			if self.plugin_category == __language__(30002):
				if title_lowercase.find('gamekings extra') >= 0:
					pass
				else:
					#skip url
					if (self.DEBUG) == 'true':
						xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "skipped video_page_url in gamekings extra category", str(video_page_url) ), xbmc.LOGNOTICE )
					#skip the thumbnail too			
					thumbnail_urls_index = thumbnail_urls_index + 1
					continue
	
			#this is category Gamekings Extra
			if self.plugin_category == __language__(30002):
				title = title.replace('Gamekings Extra: ','')
				
			if thumbnail_urls_index >= len(thumbnail_urls):
				thumbnail_url = ''
			else:
				thumbnail_url = thumbnail_urls[thumbnail_urls_index]['src']

			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "thumbnail_url", str(thumbnail_url) ), xbmc.LOGNOTICE )

			#in afleveringen category, skip link if there's no thumbnail. i do this because those links repeat on every page and are redundant imho.
			#it's bit of a hack but it'll do for now			
			if self.plugin_category == __language__(30001):
				if thumbnail_url == '':
					if (self.DEBUG) == 'true':
						xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "skipped video_page_url aflevering in pc category because it doesn't have a thumbnail", str(video_page_url_and_title) ), xbmc.LOGNOTICE )
					continue

			# Add to list
			parameters = {"action" : "play", "video_page_url" : video_page_url, "plugin_category" : self.plugin_category}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
			listitem.setInfo( "video", { "Title" : title, "Studio" : "Gamekings" } )
			folder = False
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)

			thumbnail_urls_index = thumbnail_urls_index + 1

		#Next page entry
		if self.next_page_possible == 'True':
			parameters = {"action" : "list", "plugin_category" : self.plugin_category, "url" : str(self.next_url), "next_page_possible": self.next_page_possible}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem (__language__(30503), iconImage = "DefaultFolder.png", thumbnailImage = os.path.join(__images_path__, 'next-page.png'))
			folder = True
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
			
		# Disable sorting
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
		
		# End of directory
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
