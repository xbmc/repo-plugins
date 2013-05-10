#
# Imports
#
from BeautifulSoup import BeautifulSoup
from teamhww_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from teamhww_utils import HTTPCommunicator
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
			pos_of_page		 			 	 = self.video_list_page_url.rfind('/page/')
			if pos_of_page >= 0:
				page_number_str			     = str(self.video_list_page_url[pos_of_page + len('/page/'):pos_of_page + len('/page/') + len('000')])
				self.page_number					 = int(page_number_str)
				page_number_next			 = self.page_number + 1
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
		article_number = 1
		
		# 
		# Get HTML page
		#
		html_source = HTTPCommunicator().get( self.video_list_page_url )

		# Parse response
		soup = BeautifulSoup( html_source )
		
		# Get the articles
		#<article>
		# 				<a href='http://www.teamhww.nl/2013/05/wat-weten-we-over-de-hardware-van-de-volgende-xbox/'>
		# 					<h1>Wat weten we over de hardware van de volgende Xbox</h1></a>
		# 				
		# 				<hr class='primaryColor'>
		# 				<small class='tertiaryColor'>01/05/2013 | 1 dag, 23 uur geleden | door Marvin Witlox | <a href='http://www.teamhww.nl/2013/05/wat-weten-we-over-de-hardware-van-de-volgende-xbox/#disqus_thread'></a></small>
		# 				<div class='col'>
		# 					<img src='http://www.teamhww.nl/wp-content/uploads/2013/05/20130501_XboxSplash-145x100.jpg' alt="Wat weten we over de hardware van de volgende Xbox Thumbnail">
		# 					<span class='pImg primaryColor tip'>
		# 						
		# 						<img src='/wp-content/themes/teamHWW/images/tip_small_hww.png' class='tip' alt='Style Tip' />
		# 					</span>
		# 					<span class='tags'>Tags:<br/><a href="/tag/hardware">hardware</a>, <a href="/tag/microsoft">microsoft</a>, <a href="/tag/xbox">xbox</a>, <a href="/tag/xbox-720">xbox 720</a></span>
		# 				</div>
		# 				<a href='http://www.teamhww.nl/2013/05/wat-weten-we-over-de-hardware-van-de-volgende-xbox/'><span class='excerpt'>
		# Het kan je niet ontgaan zijn dat de console oorlog weer op het punt staat los te barsten. Na de persconferentie van Sony waarin ze de PlayStation 4 hebben aangekondigd gaat nu ook Microsoft hun nieuwe Xbox bekend maken. Allemaal leuk en aardig natuurlijk, maar hoe zit het met de kracht van deze consoles? Dat [...]
		# 				</span></a>
		#</article>
		
		articles = soup.findAll('article')
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(articles)", str(len(articles)) ), xbmc.LOGNOTICE )
		
		for article in articles :
			if self.page_number == 1:
				pass	
			else:
				#skip the first 4 articles on pages after the first page
				if article_number <= 4:
					article_number = article_number + 1
					continue
				else:
					pass
						
			video_page_url = str(article.a['href'])
			#if link ends with a '/': process the link, if not: skip the link
			if video_page_url.endswith('/'):
				pass
			else:
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "skipped video_page_url not ending on '/'", str(video_page_url) ), xbmc.LOGNOTICE )
				continue

			# Make title
			#for category is 'afleveringen' use the video_page_url to make the title	
			title = article.img['alt']

			#convert from unicode to encoded text (don't use str() to do this)
			title = title.encode('utf-8')
			title = title.replace('Thumbnail','')
			
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

			thumbnail_url = str(article.img['src'])

			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "thumbnail_url", str(thumbnail_url) ), xbmc.LOGNOTICE )

			# Add to list
			parameters = {"action" : "play", "video_page_url" : video_page_url}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
			listitem.setInfo( "video", { "Title" : title, "Studio" : "TeamHww" } )
			folder = False
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)

			article_number = article_number + 1
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
