#
# Imports
#
from BeautifulSoup import BeautifulSoup
from roosterteeth_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
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

reload(sys)  
sys.setdefaultencoding('utf8')

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
		#self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
		self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['show_url'][0]
		self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
	
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.video_list_page_url", str(self.video_list_page_url) ), xbmc.LOGNOTICE )
		
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
		# Get HTML page
		#
		response = requests.get(self.video_list_page_url)
 		html_source = response.text
		html_source = html_source.encode('utf-8', 'ignore')
	
		# Parse response
		soup = BeautifulSoup( html_source )
		
		pos_of_episodes = str(html_source).find('tab-episodes')
		
		#<li>
		#	<a href="http://ah.roosterteeth.com/episode/red-vs-blue-season-13-episode-2">
		# 		    <div class="block-container">
		# 		        <div class="image-container">
		# 		            <img src="//s3.amazonaws.com/cdn.roosterteeth.com/uploads/images/bfa39842-943e-49ea-9207-e71efe9544d2/md/ep10610.jpg">
		# 		        </div>
		# 		        <div class="watch-status-container">
		# 		        </div>
		# 		        <div class="play-button-container">
		# 		            <p class="play-circle"><i class="icon ion-play"></i></p>
		# 		            <p class="timestamp">8:11</p>
		# 		        </div>
		# 		    </div>
		#        <p class="name">Episode 2</p>
		#	</a>
		#	<p class="post-stamp">3 months ago</p>
		#</li>
		
		episodes = soup.findAll('li')
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(episodes)", str(len(episodes)) ), xbmc.LOGNOTICE )
		
		for episode in episodes:
			# Skip an episode if it does not contain class="name"
			pos_classname = str(episode).find('class="name"')
			if pos_classname < 0:
				continue

			video_page_url = episode.a['href']
			
			pos_of_url = str(html_source).find(video_page_url)
			# Skip an episode if it does not come after tab-episodes
			if pos_of_url < pos_of_episodes:
				continue
			
			try:
				thumbnail_url = "https:" + episode.img['src']
			except:
				thumbnail_url = ''
			
			title = str(episode)[pos_classname + len('class="name"') + 1:]
			pos_smallerthan = title.find("<")
			title = title [0:pos_smallerthan]

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
  		  	
			# Add to list...
			parameters = {"action" : "play", "video_page_url" : video_page_url}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
			listitem.setInfo( "video", { "Title" : title, "Studio" : "roosterteeth" } )
			folder = False
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
  		
		# Disable sorting...
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
 		
		# End of directory...
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )