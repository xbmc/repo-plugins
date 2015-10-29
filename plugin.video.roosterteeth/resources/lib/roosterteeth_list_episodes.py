#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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

RECENTLYADDEDURL = 'http://roosterteeth.com/episode/recently-added'

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
		self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
		self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
	
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.video_list_page_url", str(self.video_list_page_url) ), xbmc.LOGNOTICE )

		if self.next_page_possible == 'True':
			# Determine current item number, next item number, next_url
			pos_of_page		 			 	 = self.video_list_page_url.rfind('?page=')
			if pos_of_page >= 0:
				page_number_str			     = str(self.video_list_page_url[pos_of_page + len('?page='):pos_of_page + len('?page=') + len('000')])
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
		previous_video_page_url = ''
		after_tab_trending = False
		after_tab_episodes = False
		# 
		# Get HTML page
		#
		response = requests.get(self.video_list_page_url)
 		html_source = response.text
		html_source = html_source.encode('utf-8', 'ignore')
	
		# Parse response
		soup = BeautifulSoup( html_source )
		
		#<li>
		#	<a href="http://ah.roosterteeth.com/episode/red-vs-blue-season-13-episode-2">
		# 			<div class="block-container">
		# 				<div class="image-container">
		# 					<img src="//s3.amazonaws.com/cdn.roosterteeth.com/uploads/images/bfa39842-943e-49ea-9207-e71efe9544d2/md/ep10610.jpg">
		# 				</div>
		# 				<div class="watch-status-container">
		# 				</div>
		# 				<div class="play-button-container">
		# 					<p class="play-circle"><i class="icon ion-play"></i></p>
		# 					<p class="timestamp">8:11</p>
		# 				</div>
		# 			</div>
		#		<p class="name">Episode 2</p>
		#	</a>
		#	<p class="post-stamp">3 months ago</p>
		#</li>
		
		episodes = soup.findAll('li')
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(episodes)", str(len(episodes)) ), xbmc.LOGNOTICE )
		
		for episode in episodes:
			#Only display episodes of a season
			#The recently added page doesn't have a 'tab-episode'
			if str(self.video_list_page_url).find(RECENTLYADDEDURL) >= 0:
				pass
			else:
				#Only display episodes of a season
				#<li>
				#<input type='radio' name='tabs' id='tab-episodes' />
				if str(episode).find("tab-episodes") >= 0:
					after_tab_episodes = True
				# Skip if the episode isn't a season episode
				if after_tab_episodes == False:
					continue
			
			# Skip the recently-added url
 			if str(episode).find('recently-added') >= 0:
 				continue
			
			# Skip an episode if it does not contain class="name"
			pos_classname = str(episode).find('class="name"')
			if pos_classname == -1:
				continue

			video_page_url = episode.a['href']
			
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_page_url", str(video_page_url) ), xbmc.LOGNOTICE )
			
			# Skip a video_page_url is empty
			if video_page_url == '':
				continue
			
			# Skip episode if it's the same as the previous one
			if video_page_url == previous_video_page_url:
				continue
			else:
				previous_video_page_url = video_page_url
			
			try:
				thumbnail_url = "https:" + episode.img['src']
			except:
				thumbnail_url = ''
			
			title = str(episode)[pos_classname + len('class="name"') + 1:]
			pos_smallerthan = title.find("<")
			title = title [0:pos_smallerthan]

			#Clean up title
			try:
				title = title.encode('utf-8')
			except:
				pass
			
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
			
		# Next page entry...
		if self.next_page_possible == 'True':
			parameters = {"action" : "list-episodes", "url" : str(self.next_url), "next_page_possible": self.next_page_possible}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem (__language__(30200), iconImage = "DefaultFolder.png", thumbnailImage = os.path.join(__images_path__, 'next-page.png'))
			folder = True
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
		
		# Disable sorting...
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
 		
		# End of directory...
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )