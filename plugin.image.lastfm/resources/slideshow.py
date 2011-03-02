import urllib,urllib2,re
import xbmcaddon,xbmcgui
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='script.image.lastfm.slideshow')
__language__ = __settings__.getLocalizedString

def SlideShow():
	class MyPlayer( xbmc.Player ) :            
		def __init__ ( self ):
			xbmc.Player.__init__( self )
				
		def onPlayBackStarted(self):
			print 'music --> playback started'
			startSlideShow()
			while (True):
				if self.isPlaying():
					xbmc.sleep(1000)
				else:
					print 'music --> broke out of loop'
					#startSlideShow()                 
					break

		def onPlayBackStopped(self):
			print "music --> onPlayBackStopped"
			return True

		def onPlayBackEnded(self):
			print "music --> onPlayBackEnded"

	def startSlideShow():
		if xbmc.Player().isPlayingAudio()==False:
			dialog = xbmcgui.Dialog()
			ok = dialog.ok(__language__(30000),__language__(30001))			
			return
		else:
			name = xbmc.Player().getMusicInfoTag().getArtist()
			url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getimages&artist='+name.replace(' ','+')+'&autocorrect=1&api_key=71e468a84c1f40d4991ddccc46e40f1b'
			req = urllib2.Request(url)
			response = urllib2.urlopen(req)
			link=response.read()
			response.close()
			soup = BeautifulSoup(link)
			images = soup('image')
			xbmc.executehttpapi("ClearSlideshow")
			for image in images:
				url = image.size.string
				xbmc.executehttpapi("AddToSlideshow(%s)" % url)
			xbmc.executebuiltin( "SlideShow(,,notrandom)" )

	MyPlayer().onPlayBackStarted()

SlideShow()