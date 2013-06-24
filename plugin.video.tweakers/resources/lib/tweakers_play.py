#
# Imports
#
from BeautifulSoup import BeautifulSoup
from tweakers_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from tweakers_utils import HTTPCommunicator
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
		
		# Parse parameters
		self.video_page_url = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['video_page_url'][0]
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "self.video_page_url", str(self.video_page_url) ), xbmc.LOGNOTICE )

		#
		# Play video
		#
		self.playVideo()
	
	#
	# Play video
	#
	def playVideo( self ) :
		#
		# Get current list item details
		#
		title     = unicode( xbmc.getInfoLabel( "ListItem.Title"  ), "utf-8" )
		thumbnail =          xbmc.getInfoImage( "ListItem.Thumb"  )
		studio    = unicode( xbmc.getInfoLabel( "ListItem.Studio" ), "utf-8" )
		plot      = unicode( xbmc.getInfoLabel( "ListItem.Plot"   ), "utf-8" )
		genre     = unicode( xbmc.getInfoLabel( "ListItem.Genre"  ), "utf-8" )
		
		#
		# Show wait dialog while parsing data
		#
		dialogWait = xbmcgui.DialogProgress()
		dialogWait.create( __language__(30504), title )
		
		httpCommunicator = HTTPCommunicator()
		
		#video_page_url will be something like this: http://tweakers.net/video/7893/world-of-tanks-86-aankondiging.html
		#the real mp4 link can be found a this page: http://tweakers.net/video/player/7893/world-of-tanks-86-aankondiging.html
		#therefore adding '/player'
		self.video_page_url = str(self.video_page_url)
		self.video_page_url = self.video_page_url.replace('video/', 'video/player/')
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "altered self.video_page_url", str(self.video_page_url) ), xbmc.LOGNOTICE )
		
		try:
			html_data = httpCommunicator.get ( self.video_page_url )
		except urllib2.HTTPError, error:
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "HTTPError", str(error) ), xbmc.LOGNOTICE )
			dialogWait.close()
			del dialogWait
			xbmcgui.Dialog().ok( __language__(30000), __language__(30507) % (str(error) ))
			exit(1)
			
		soup = BeautifulSoup(html_data)
		
		#<video controls src="http://content.tweakers.tv/stream/item=piDTr63m3i/file=N8vjyj2e75/cid=Kn1cb9g4kfgdcZaRE57j/piDTr63m3i.mp4" width="620" height="349" preload="none" onclick="this.play()">
		#<a href="http://content.tweakers.tv/stream/item=piDTr63m3i/file=N8vjyj2e75/cid=Kn1cb9g4kfgdcZaRE57j/piDTr63m3i.mp4">Download de video:Samsung's Galaxy S4's: de Active en de Mini</a>
		#</video>

		video_urls = soup.findAll('a', attrs={'href': re.compile("http://content.tweakers.tv/stream/")})
		for video_url in video_urls :
			video_url = str(video_url)
			pos_of_href = video_url.find("href=")
			video_url = video_url[pos_of_href + len("href="):]
			#remove leading quote
			video_url = video_url[1:]
			pos_of_quote = video_url.find('"')
			video_url = video_url[0:pos_of_quote]
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_url", str(video_url) ), xbmc.LOGNOTICE )
		
		if len(video_url) == 0:
			no_url_found = True
		else:
			if httpCommunicator.exists( video_url ):
				have_valid_url = True
			else:
				unplayable_media_file = True
				
		# Play video
		if have_valid_url:
			playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
			playlist.clear()
		
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
			xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
			listitem.setInfo( "video", { "Title": title, "Studio" : "Tweakers", "Plot" : plot, "Genre" : genre } )
			playlist.add( video_url, listitem )
	
			# Close wait dialog
			dialogWait.close()
			del dialogWait
			
			# Play video
			xbmcPlayer = xbmc.Player()
			xbmcPlayer.play( playlist )
		#
		# Alert user
		#
	 	elif no_url_found:
			xbmcgui.Dialog().ok( __language__(30000), __language__(30505))
		elif unplayable_media_file:
			xbmcgui.Dialog().ok( __language__(30000), __language__(30506))
	
#
# The End
#