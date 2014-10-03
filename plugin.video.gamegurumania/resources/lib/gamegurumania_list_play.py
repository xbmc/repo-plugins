# Imports
#
from BeautifulSoup import BeautifulSoup
from gamegurumania_const import __settings__, __language__, __images_path__, __addon__, __plugin__, __author__, __url__, __date__, __version__
from gamegurumania_utils import HTTPCommunicator
import os
import re
import sys
import urllib
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
			print 'Python Version: ' + sys.version
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "File", str(__file__) ), xbmc.LOGNOTICE )

		# Parse parameters...
		self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
		self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
		self.video_list_page_url = str(self.video_list_page_url)
		self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.video_list_page_url", str(self.video_list_page_url) ), xbmc.LOGNOTICE )
		
		if self.next_page_possible == 'True':
		# Determine current item number, next item number, next_url
		#http://www.ggmania.com/more.php3?next=000&kategory=movie
			pos_of_next	 			 	 = self.video_list_page_url.rfind('next=')
			item_number_str			     = str(self.video_list_page_url[pos_of_next + len('next='):pos_of_next + len('next=') + len('000')])
			item_number	 				 = int(item_number_str)
			#the site only skips 10 items per page, seems like a bug. Skip 20 to go onto next new itempage
			item_number_next			 = item_number + 20
			if item_number_next >= 100:
				item_number_next_str = str(item_number_next)
			else:				
				item_number_next_str = '0' + str(item_number_next)
			self.next_url = self.video_list_page_url.replace(item_number_str, item_number_next_str)
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.next_url", str(urllib.unquote_plus(self.next_url)) ), xbmc.LOGNOTICE )
		
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
		video_page_url_napdis = ''
		video_page_url_iframe = '' 
		video_page_url_youtube = '' 
		nadpis_found = False
		iframe_found = False
		youtube_found = False
		thumbnail_url = ''
		
		# 
		# Get HTML page...
		#
		html_source = HTTPCommunicator().get( self.video_list_page_url )

		# Parse response...
		soup = BeautifulSoup(html_source)

		#find a title and directly after it a video-link. Some title don't have a video-link and must be skipped. 
		#Find Title
		#<a class="nadpis" name="shadowrun-returns-alpha-gameplay-video-34776" href="http://www.ggmania.com/?smsid=shadowrun-returns-alpha-gameplay-video-34776">Shadowrun Returns - Alpha Gameplay Video</a>
		#Find youtubeID
		#<iframe width="560" height="315" src="http://www.youtube.com/embed/9MiMjQwd2VE" frameborder="0" allowfullscreen="allowfullscreen"></iframe>		
		#<div class="youtube" id="fDZF-jIhhbk" style="width: 640px; height: 360px;">
		
		video_page_urls = soup.findAll ( ["a", "iframe", "div"] )
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(video_page_urls)", str(len(video_page_urls)) ), xbmc.LOGNOTICE )
		
		for video_page_url in video_page_urls:
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_page_url", str(video_page_url) ), xbmc.LOGNOTICE )

			video_page_url_str = str(video_page_url)
			if video_page_url_str.startswith('<a class="nadpis"'):
				nadpis_found = True
				youtube_found = False
				video_page_url_napdis = video_page_url
			if video_page_url_str.startswith('<iframe'):
				iframe_found = True
				video_page_url_iframe = video_page_url				
			if video_page_url_str.startswith('<div class="youtube"'):
				youtube_found = True
				video_page_url_youtube = video_page_url
			if (nadpis_found == True and iframe_found == True) or (nadpis_found == True and youtube_found == True):
				#Find Title
				#<a class="nadpis" name="shadowrun-returns-alpha-gameplay-video-34776" href="http://www.ggmania.com/?smsid=shadowrun-returns-alpha-gameplay-video-34776">Shadowrun Returns - Alpha Gameplay Video</a>
					
				video_page_url_napdis_str = str(video_page_url_napdis)
				start_pos_title = video_page_url_napdis_str.find(">") + 1
				title = video_page_url_napdis_str[start_pos_title:]
				title = title.replace("</a>","")
		
				title = title.capitalize()
				title = title.replace('/',' ')
				title = title.replace('&amp;','&')
				title = title.replace(' i ',' I ')
				title = title.replace(' amp ',' & ')
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
				
				#Find youtubeID
				#<iframe width="560" height="315" src="http://www.youtube.com/embed/9MiMjQwd2VE" frameborder="0" allowfullscreen="allowfullscreen"></iframe>				
				#<div class="youtube" id="fDZF-jIhhbk" style="width: 640px; height: 360px;">
				if iframe_found == True:
					youtubeID = str(video_page_url_iframe['src'])
					youtubeID = youtubeID.replace("//www.youtube.com/embed/", '')
				if youtube_found == True:
					youtubeID = str(video_page_url_youtube['id'])
				
				youtube_url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % youtubeID
						
				if (self.DEBUG) == 'true':
					xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "youtube_url", str(youtube_url) ), xbmc.LOGNOTICE )
							
				# Add to list...
				listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
				listitem.setInfo( "video", { "Title" : title, "Studio" : "GameGuruMania" } )
				listitem.setProperty('IsPlayable', 'true')
				plugin_play_url = youtube_url
				folder = False
				xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url=plugin_play_url, listitem=listitem, isFolder=folder)
				
				nadpis_found = False
				iframe_found = False
				youtube_found = False
			
		#Next page entry...
		if self.next_page_possible == 'True':
			parameters = {"action" : "list-play", "plugin_category" : self.plugin_category, "url" : str(self.next_url), "next_page_possible": self.next_page_possible}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem (__language__(30503), iconImage = "DefaultFolder.png", thumbnailImage = os.path.join(__images_path__, 'next-page.png'))
			folder = True
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
		
		# Disable sorting...
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
		
		# End of directory...
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
