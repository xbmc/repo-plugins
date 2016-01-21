#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#
# Imports
#
from BeautifulSoup import BeautifulSoup
from tweakers_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from tweakers_utils import HTTPCommunicator
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
		self.DEBUG = __settings__.getSetting('debug')
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s, %s = %s" % ( __addon__, __version__, __date__, "ARGV", repr(sys.argv), "File", str(__file__) ), xbmc.LOGNOTICE )

		# Parse parameters
		if len(sys.argv[2]) == 0:
			self.plugin_category = __language__(30000)
			self.video_list_page_url = "http://tweakers.net/video/zoeken/?page=001"
			self.next_page_possible = "True"
		else:
			self.plugin_category = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['plugin_category'][0]
			self.video_list_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['url'][0]
			self.next_page_possible = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['next_page_possible'][0]
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.video_list_page_url", str(self.video_list_page_url) ), xbmc.LOGNOTICE )
		
		if self.next_page_possible == "True":
		# Determine current item number, next item number, next_url
		#f.e. http://www.tweakers.net/category/videos/page/001/
			pos_of_page	= self.video_list_page_url.rfind('?page=')
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
		#<img src="http://ic.tweakimg.net/img/accountid=1/externalid=7515/size=124x70/image.jpg" width=124 height=70 alt="">
		thumbnail_urls = soup.findAll('img', attrs={'src': re.compile("^http://ic.tweakimg.net/")})
			
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(thumbnail_urls)", str(len(thumbnail_urls)) ), xbmc.LOGNOTICE )
		
		# Get the video page urls
		#<td class="video-image">
		#	<a href="http://tweakers.net/video/7517/showcase-trailer-van-cryengine-3-van-gdc-2013.html" class="thumb video" title="Showcase-trailer van CryEngine 3 van GDC 2013"><img src="http://ic.tweakimg.net/img/accountid=1/externalid=7517/size=124x70/image.jpg" width=124 height=70 alt=""><span class="playtime">04:00</span></a>
		#</td>
		video_page_url_in_tds = soup.findAll('td', attrs={'class': re.compile("video-image")})
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(video_page_url_in_tds)", str(len(video_page_url_in_tds)) ), xbmc.LOGNOTICE )
			
		for video_page_url_in_td in video_page_url_in_tds :
			video_page_url = video_page_url_in_td.a['href']
			
			# Make title
			title = video_page_url_in_td.a['title']
			# Convert from unicode to encoded text (don't use str() to do this)
			
			try:
				title = title.encode('utf-8')
			except:
				pass
				
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "title", str(title) ), xbmc.LOGNOTICE )

			if thumbnail_urls_index >= len(thumbnail_urls):
				thumbnail_url = ''
			else:
				thumbnail_url = thumbnail_urls[thumbnail_urls_index]['src']

			# Add to list
			parameters = {"action" : "play", "video_page_url" : video_page_url}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
			listitem.setInfo( "video", { "Title" : title, "Studio" : "tweakers" } )
			listitem.addContextMenuItems([ ('Refresh', 'Container.Refresh') ])
			listitem.setArt({'fanart': os.path.join(__images_path__, 'fanart-blur.jpg')})
			folder = False
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)

			thumbnail_urls_index = thumbnail_urls_index + 1

		#Next page entry
		if self.next_page_possible == 'True':
			parameters = {"action" : "list", "plugin_category" : self.plugin_category, "url" : str(self.next_url), "next_page_possible": self.next_page_possible}
			url = sys.argv[0] + '?' + urllib.urlencode(parameters)
			listitem = xbmcgui.ListItem (__language__(30503), iconImage = "DefaultFolder.png", thumbnailImage = os.path.join(__images_path__, 'next-page.png'))
			listitem.setArt({'fanart': os.path.join(__images_path__, 'fanart-blur.jpg')})
			folder = True
			xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
			
		# Disable sorting
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
		
		# End of directory
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )
