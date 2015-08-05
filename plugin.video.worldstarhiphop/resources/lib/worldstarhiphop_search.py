#
# Imports
#
from BeautifulSoup import BeautifulSoup
from worldstarhiphop_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from worldstarhiphop_utils import HTTPCommunicator
import os
import re
import sys
import urllib, urllib2
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

reload(sys)  
sys.setdefaultencoding('utf8')

BASEURL = "http://www.worldstarhiphop.com"
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
 			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "File", str(__file__) ), xbmc.LOGNOTICE )

		try:
			self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
			self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
			self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
		except:
			self.plugin_category = __language__(30000)
 			self.next_page_possible = "True"
 			#Get the search-string from the user
			keyboard = xbmc.Keyboard('', __language__(30103))
			keyboard.doModal()
	   		if keyboard.isConfirmed():
	   			self.search_string = keyboard.getText()
		   		self.video_list_page_url = "http://www.worldstarhiphop.com/videos/search.php?s=%s&start=001" % (self.search_string)

		if self.next_page_possible == 'True':
		# Determine current item number, next item number, next_url
			pos_of_page		 			 	 = self.video_list_page_url.rfind('&start=')
			if pos_of_page >= 0:
				page_number_str			     = str(self.video_list_page_url[pos_of_page + len('&start='):pos_of_page + len('&start=') + len('000')])
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
		
		# 
		# Get HTML page...
		#
		html_source = HTTPCommunicator().get( self.video_list_page_url )

		# Parse response...
		soup = BeautifulSoup( html_source )
		
		#<section class="box">
		#                 <a href="/videos/video.php?v=wshhf1jtojJPKCOEOd1n" class="video-box">
		#                 <img src="http://hw-static.worldstarhiphop.com/u/pic/2015/06/Oe4nzSMG4iuf.jpg" width="222" height="125" alt="">
		#                 </a>
		#                 <strong class="title"><a href="/videos/video.php?v=wshhf1jtojJPKCOEOd1n">Blues Version Of &quot;The Fresh Prince Of Bel-Air&quot; Theme!</a></strong>
		#                 <div>
		#                         <span class="views">58,847</span> 
		#                         <span class="comments"><a href="http://www.worldstarhiphop.com/videos/video.php?v=wshhf1jtojJPKCOEOd1n#disqus_thread" data-disqus-identifier="83085"></a></span>
		#                 </div>
		#</section>

		#Clean title: Blues Version Of "The Fresh Prince Of Bel-Air" Theme!
		
		items = soup.findAll('section', attrs={'class': re.compile("^box")})
				
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(items)", str(len(items)) ), xbmc.LOGNOTICE )
		
		for item in items :
			item_string = str(item)

			#Get video-page-url
			start_pos_url1 = item_string.find('"/videos/video.php?v=' , 0)

			#skip the item if nothing was found
			if start_pos_url1 == -1:
				continue
			
			end_pos_url1 = item_string.find('"', start_pos_url1 + 1)
			video_url = item_string[start_pos_url1 + 1 :end_pos_url1]
			video_page_url = BASEURL + video_url

			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_page_url", str(video_page_url) ), xbmc.LOGNOTICE )

			#Get thumbnail url
			item_string = str(item)
			start_pos_url = item_string.find('http://hw-static.worldstarhiphop.com' , 0)
			end_pos_url = item_string.find('"' , start_pos_url)
			thumbnail_url = item_string[start_pos_url:end_pos_url]
						
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "thumbnail_url", str(thumbnail_url) ), xbmc.LOGNOTICE )
	
			#Get title			
			start_pos_url2 = item_string.find('"/videos/video.php?v=' , end_pos_url1 + 1)
			end_pos_url2 = item_string.find('"', start_pos_url2 + 1)
			start_pos_title = item_string.find('>', end_pos_url2 + 1)
			end_pos_title = item_string.find('<', start_pos_title + 1)
			title = item_string[start_pos_title + 1 :end_pos_title]
			
			#Clean up title
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
			title = title.replace('  ',' ')
			title = title.replace('  ',' ')
			#welcome to characterset-hell
			title = title.replace('&amp;#039;',"'")
			title = title.replace('&amp;#39;',"'")
			title = title.replace('&amp;quot;','"')
			title = title.replace("&#039;","'")
  			title = title.replace("&#39;","'")
  			title = title.replace('&amp;amp;','&')
  			title = title.replace('&amp;','&')
  			title = title.replace('&quot;','"')
  		 	title = title.replace('&ldquo;','"')
  		  	title = title.replace('&rdquo;','"')
  		  	title = title.replace('&rsquo;',"'")
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "title", str(title) ), xbmc.LOGNOTICE )
							
			# Add to list...
			parameters = {"action" : "play", "video_page_url" : video_page_url}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
			listitem.setInfo( "video", { "Title" : title, "Studio" : "WorldWideHipHop" } )
			folder = False
			
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)

		# Next page entry...
		if self.next_page_possible == 'True':
			parameters = {"action" : "search", "plugin_category" : self.plugin_category, "url" : str(self.next_url), "next_page_possible": self.next_page_possible}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem (__language__(30503), iconImage = "DefaultFolder.png", thumbnailImage = os.path.join(__images_path__, 'next-page.png'))
			folder = True
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
			
		# Disable sorting...
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
		
		# End of directory...
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )