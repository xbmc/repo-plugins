#
# Imports
#
import os
import sys
import datetime
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import urllib
from BeautifulSoup import SoupStrainer
from BeautifulSoup import BeautifulSoup

#
# Main class
#
class Main:
	#
	# Init
	#
	def __init__( self ) :
		# Constants
		self.__addon__ = xbmcaddon.Addon('plugin.video.gamesonnet')
		self.__setting__ = self.__addon__.getSetting
		self.__lang__ = self.__addon__.getLocalizedString
		self.__cwd__ = self.__addon__.getAddonInfo('path')
		self.DEBUG            = False
		self.IMAGES_PATH      = xbmc.translatePath( os.path.join( self.__cwd__, 'resources', 'images' ) )
		self.USER_DATE_FORMAT = xbmc.getRegion( "dateshort" ).replace( "MM", "%m" ).replace( "DD", "%d" ).replace( "YYYY", "%Y" ).strip()
		
		# Parse parameters...
		if sys.argv[ 2 ] != "" :
			params  = dict(part.split('=') for part in sys.argv[ 2 ][ 1: ].split('&'))
			page_no = int( params[ "page" ] )
		else :
			page_no = 1

		#
		# Get the videos...
		#
		self.getVideos( page_no )

	#
	# Get plugins...
	#
	def getVideos( self, page_no ) :
		#
		# Init
		#

		#
		# Get HTML page...
		#
		url = "http://games.on.net/filelist.php?type=v&p=%u" % ( page_no )
		usock = urllib.urlopen( url )
		htmlSource = usock.read()
		usock.close()

		#
		# Parse response...
		#
		soupStrainer  = SoupStrainer( "div", { "class" : "file_list" } )
		beautifulSoup = BeautifulSoup( htmlSource, soupStrainer )

		table_file_list = beautifulSoup.table
		table_rows = table_file_list.findAll( "tr" )
		for table_row in table_rows :
			table_row_columns = table_row.findAll( "td" )
			if len(table_row_columns) == 4 :
				# 1st column - date
				video_date = table_row_columns[0].string

				# 2nd column - video page url + summary
				a = table_row_columns[1].a
				if a == None :
					continue

				video_page_url = a[ "href" ]
				video_summary  = a.string
				
				# 3rd column - Approximate File Size
				video_size = table_row_columns[2].string
				

				# Prepare date in user format...
				video_date_display = datetime.date ( int( video_date.split( "/" )[ 2 ] ),
													int( video_date.split( "/" )[ 1 ] ),
													int( video_date.split( "/" )[ 0 ] ) ).strftime( self.USER_DATE_FORMAT )

				#
				# Add to list...
				#
				listitem        = xbmcgui.ListItem( video_summary, iconImage="DefaultVideo.png", thumbnailImage = os.path.join(self.IMAGES_PATH, 'logo.png' ) )
				listitem.setInfo( "video", { "Title" : video_summary, "Studio" : "Games On Net", "Genre" : video_date_display, "Size" : video_size } )
				plugin_play_url = '%s?action=play&video_page_url=%s' % ( sys.argv[ 0 ], urllib.quote_plus( video_page_url ) )
				xbmcplugin.addDirectoryItem( handle=int(sys.argv[ 1 ]), url=plugin_play_url, listitem=listitem, isFolder=False)

		# Next page entry...
		listitem = xbmcgui.ListItem (self.__lang__(30402), iconImage = "DefaultFolder.png", thumbnailImage = os.path.join(self.IMAGES_PATH, 'next-page.png'))
		xbmcplugin.addDirectoryItem( handle = int(sys.argv[1]), url = "%s?action=list&page=%i" % ( sys.argv[0], page_no + 1 ), listitem = listitem, isFolder = True)

		# Label (top-right)...
		#  xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=( xbmc.getLocalizedString(30401)  % page_no ) )

		# Disable sorting...
		xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )

		# End of directory...
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )