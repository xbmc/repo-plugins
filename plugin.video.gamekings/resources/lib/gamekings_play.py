#
# Imports
#
from BeautifulSoup import BeautifulSoup
from gamekings_const import __addon__, __settings__, __language__, __images_path__, __date__, __version__
from gamekings_utils import HTTPCommunicator
import os
import re
import sys
import base64
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
		# Init
		#
		no_url_found = False
		unplayable_media_file = False
		have_valid_url = False
		
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
		
		#Sometimes a page request gets a HTTP Error 500: Internal Server Error
		#f.e. http://www.gamekings.tv/videos/het-fenomeen-minecraft/
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
		
		# Get the video url
		#This is for Gamekings Extra
		#<script type="text/javascript">
		#   gogoVideo(92091,"MjAxNDExMTNfRXh0cmEubXA0LGh0dHA6Ly93d3cuZ2FtZWtpbmdzLnR2L3dwLWNvbnRlbnQvdXBsb2Fkcy8yMDE0MTExNF9FeHRyYV9zcGxhc2gtMTAyNHg1NzYuanBnLEdhbWVraW5ncyBFeHRyYTogV2Vsa2UgZ2FtZXMgc3BlbGVuIHdpaiBkaXQgbmFqYWFyPw==");
		#</script>
		#the base86 encode string looks like this decoded:
		#20141113_Extra.mp4,http://www.gamekings.tv/wp-content/uploads/20141114_Extra_splash-1024x576.jpg,Gamekings Extra: Welke games spelen wij dit najaar?
		if self.plugin_category == __language__(30002):
			video_urls = re.findall(r'"(.*?)"', str(soup.findAll('script', text=re.compile("gogoVideo"), limit=1)))
		else:
		#<meta property="og:video" content="http://stream.gamekings.tv/20130306_SpecialForces.mp4"/>
		#sometimes the content is not (!!) correct and the real link will be "http://stream.gamekings.tv/large/20130529_E3Journaal.mp4" :(
		#May 2014: videos are vimeo files now:
		#<meta property="og:video" content="http://stream.gamekings.tv/http://player.vimeo.com/external/111637217.hd.mp4?s=10e5d0efd4d10756b535b115140ebe13"/>
			video_urls = soup.findAll('meta', attrs={'content': re.compile("^http://stream.gamekings.tv/")}, limit=1)
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(video_urls)", str(len(video_urls)) ), xbmc.LOGNOTICE )
		
		if len(video_urls) == 0:
			no_url_found = True
		else:
			if self.plugin_category == __language__(30002):
				video_urls_dec = str(base64.b64decode(video_urls[0]))
				video_urls_dict = video_urls_dec.split(',')
				video_url = str(video_urls_dict[0])
			else:
				video_url = str(video_urls[0]['content'])
				
			if (self.DEBUG) == 'true':
				xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_url", str(video_url) ), xbmc.LOGNOTICE )

			# Check if it's a vimeo file
			if video_url.count("vimeo") > 0:
				#the vimeo video_url looks like this: http://stream.gamekings.tv/http://player.vimeo.com/external/118907131.hd.mp4?s=486e834bab4dc380743d814653c52050
				#therefore the stream stuff got to be removed
				video_url = video_url.replace("http://stream.gamekings.tv/large", "")
				video_url = video_url.replace("http://stream.gamekings.tv/", "")
				have_valid_url = True
			else:
				video_url = "http://stream.gamekings.tv/large/" + video_url
				if httpCommunicator.exists( video_url ):
					have_valid_url = True
				else:
					video_url = video_url.replace("http://stream.gamekings.tv/large", "http://stream.gamekings.tv/")
					if httpCommunicator.exists( video_url ):
						have_valid_url = True
					else:
						unplayable_media_file = True
		
		if (self.DEBUG) == 'true':
			xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "video_url to be played", str(video_url) ), xbmc.LOGNOTICE )
				
		# Play video
		if have_valid_url:
			playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
			playlist.clear()
		
			listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
			xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
			listitem.setInfo( "video", { "Title": title, "Studio" : "Gamekings", "Plot" : plot, "Genre" : genre } )
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