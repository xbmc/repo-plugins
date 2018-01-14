# -*- coding: utf-8 -*-
#
# MIT License
#
# Copyright (c) 2017-2018, Leo Moll
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -- Imports ------------------------------------------------
from __future__ import unicode_literals  # ,absolute_import, division
# from future import standard_library
# from builtins import *
# standard_library.install_aliases()
import os,re,sys,urlparse,datetime
import xbmcplugin,xbmcgui,xbmcvfs

from contextlib import closing

from resources.lib.kodi.KodiAddon import KodiPlugin
from resources.lib.kodi.KodiUI import KodiBGDialog

from resources.lib.store import Store
from resources.lib.notifier import Notifier
from resources.lib.settings import Settings
from resources.lib.filmui import FilmUI
from resources.lib.channelui import ChannelUI
from resources.lib.initialui import InitialUI
from resources.lib.showui import ShowUI
from resources.lib.ttml2srt import ttml2srt

# -- Classes ------------------------------------------------
class MediathekView( KodiPlugin ):

	def __init__( self ):
		super( MediathekView, self ).__init__()
		self.settings	= Settings()
		self.notifier	= Notifier()
		self.db			= Store( self.getNewLogger( 'Store' ), self.notifier, self.settings )

	def showMainMenu( self ):
		# Search
		self.addFolderItem( 30901, { 'mode': "search" } )
		# Search all
		self.addFolderItem( 30902, { 'mode': "searchall" } )
		# Browse livestreams
		self.addFolderItem( 30903, { 'mode': "livestreams" } )
		# Browse recently added
		self.addFolderItem( 30904, { 'mode': "recent", 'channel': 0 } )
		# Browse recently added by channel
		self.addFolderItem( 30905, { 'mode': "recentchannels" } )
		# Browse by Initial->Show
		self.addFolderItem( 30906, { 'mode': "initial", 'channel': 0 } )
		# Browse by Channel->Initial->Shows
		self.addFolderItem( 30907, { 'mode': "channels" } )
		# Database Information
		self.addActionItem( 30908, { 'mode': "action-dbinfo" } )
		self.endOfDirectory()

	def showSearch( self ):
		searchText = self.notifier.GetEnteredText( '', self.language( 30901 ).decode( 'UTF-8' ) )
		if len( searchText ) > 2:
			self.db.Search( searchText, FilmUI( self ) )
		else:
			self.info( 'The following ERROR can be ignored. It is caused by the architecture of the Kodi Plugin Engine' )
			self.endOfDirectory( False, cacheToDisc = True )
			# self.showMainMenu()

	def showSearchAll( self ):
		searchText = self.notifier.GetEnteredText( '', self.language( 30902 ).decode( 'UTF-8' ) )
		if len( searchText ) > 2:
			self.db.SearchFull( searchText, FilmUI( self ) )
		else:
			self.info( 'The following ERROR can be ignored. It is caused by the architecture of the Kodi Plugin Engine' )
			self.endOfDirectory( False, cacheToDisc = True )
			# self.showMainMenu()

	def showDbInfo( self ):
		info = self.db.GetStatus()
		heading = self.language( 30907 )
		infostr = self.language( {
			'NONE': 30941,
			'UNINIT': 30942,
			'IDLE': 30943,
			'UPDATING': 30944,
			'ABORTED': 30945
		}.get( info['status'], 30941 ) )
		infostr = self.language( 30965 ) % infostr
		totinfo = self.language( 30971 ) % (
			info['tot_chn'],
			info['tot_shw'],
			info['tot_mov']
		)
		updatetype = self.language( 30972 if info['fullupdate'] > 0 else 30973 )
		if info['status'] == 'UPDATING' and info['filmupdate'] > 0:
			updinfo = self.language( 30967 ) % (
				updatetype,
				datetime.datetime.fromtimestamp( info['filmupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				info['add_chn'],
				info['add_shw'],
				info['add_mov']
			)
		elif info['status'] == 'UPDATING':
			updinfo = self.language( 30968 ) % (
				updatetype,
				info['add_chn'],
				info['add_shw'],
				info['add_mov']
			)
		elif info['lastupdate'] > 0 and info['filmupdate'] > 0:
			updinfo = self.language( 30969 ) % (
				updatetype,
				datetime.datetime.fromtimestamp( info['lastupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				datetime.datetime.fromtimestamp( info['filmupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				info['add_chn'],
				info['add_shw'],
				info['add_mov'],
				info['del_chn'],
				info['del_shw'],
				info['del_mov']
			)
		elif info['lastupdate'] > 0:
			updinfo = self.language( 30970 ) % (
				updatetype,
				datetime.datetime.fromtimestamp( info['lastupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				info['add_chn'],
				info['add_shw'],
				info['add_mov'],
				info['del_chn'],
				info['del_shw'],
				info['del_mov']
			)
		else:
			updinfo = self.language( 30966 )

		xbmcgui.Dialog().textviewer(
			heading,
			infostr + '\n\n' +
			totinfo + '\n\n' +
			updinfo
		)

	def doDownloadFilm( self, filmid, quality ):
		if self.settings.downloadpath:
			film = self.db.RetrieveFilmInfo( filmid )
			if film is None:
				# film not found - should never happen
				return

			# check if the download path is reachable
			if not xbmcvfs.exists( self.settings.downloadpath ):
				self.notifier.ShowError( self.language( 30952 ), self.language( 30979 ) )
				return

			# get the best url
			if quality == '0' and film.url_video_sd:
				videourl = film.url_video_sd
			elif quality == '2' and film.url_video_hd:
				videourl = film.url_video_hd
			else:
				videourl = film.url_video

			# prepare names
			showname	= mvutils.cleanup_filename( film.show )[:64]
			filestem	= mvutils.cleanup_filename( film.title )[:64]
			extension	= os.path.splitext( videourl )[1]
			if not extension:
				extension = u'.mp4'
			if not filestem:
				filestem = u'Film-{}'.format( film.id )
			if not showname:
				showname = filestem

			# prepare download directory and determine episode number
			dirname = self.settings.downloadpath + showname + '/'
			episode = 1
			if xbmcvfs.exists( dirname ):
				( dirs, epfiles, ) = xbmcvfs.listdir( dirname )
				for epfile in epfiles:
					match = re.search( '^.* [eE][pP]([0-9]*)\.[^/]*$', epfile )
					if match and len( match.groups() ) > 0:
						if episode <= int( match.group(1) ):
							episode = int( match.group(1) ) + 1
			else:
				xbmcvfs.mkdir( dirname )

			# prepare resulting filenames
			fileepi = filestem + u' - EP%04d' % episode
			movname = dirname + fileepi + extension
			srtname = dirname + fileepi + u'.srt'
			ttmname = dirname + fileepi + u'.ttml'
			nfoname = dirname + fileepi + u'.nfo'

			# download video
			bgd = KodiBGDialog()
			bgd.Create( self.language( 30974 ), fileepi + extension )
			try:
				bgd.Update( 0 )
				result = mvutils.url_retrieve_vfs( videourl, movname, bgd.UrlRetrieveHook )
				bgd.Close()
				if result is not None:
					self.notifier.ShowNotification( self.language( 30960 ), self.language( 30976 ).format( videourl ) )
			except Exception as err:
				bgd.Close()
				self.error( 'Failure downloading {}: {}', videourl, err )
				self.notifier.ShowError( self.language( 30952 ), self.language( 30975 ).format( videourl, err ) )

			# download subtitles
			if film.url_sub:
				bgd = KodiBGDialog()
				bgd.Create( self.language( 30978 ), fileepi + u'.ttml' )
				try:
					bgd.Update( 0 )
					result = mvutils.url_retrieve_vfs( film.url_sub, ttmname, bgd.UrlRetrieveHook )
					try:
						ttml2srt( xbmcvfs.File( ttmname, 'r' ), xbmcvfs.File( srtname, 'w' ) )
					except Exception as err:
						self.info( 'Failed to convert to srt: {}', err )
					bgd.Close()
				except Exception as err:
					bgd.Close()
					self.error( 'Failure downloading {}: {}', film.url_sub, err )

			# create NFO Files
			self._make_nfo_files( film, episode, dirname, nfoname, videourl )
		else:
			self.notifier.ShowError( self.language( 30952 ), self.language( 30958 ) )

	def doEnqueueFilm( self, filmid ):
		self.info( 'Enqueue {}', filmid )

	def _make_nfo_files( self, film, episode, dirname, filename, videourl ):
		# create NFO files
		if not xbmcvfs.exists( dirname + 'tvshow.nfo' ):
			try:
				with closing( xbmcvfs.File( dirname + 'tvshow.nfo', 'w' ) ) as file:
					file.write( b'<tvshow>\n' )
					file.write( b'<id></id>\n' )
					file.write( bytearray( '\t<title>{}</title>\n'.format( film.show ), 'utf-8' ) )
					file.write( bytearray( '\t<sorttitle>{}</sorttitle>\n'.format( film.show ), 'utf-8' ) )
# TODO:				file.write( bytearray( '\t<year>{}</year>\n'.format( 2018 ), 'utf-8' ) )
					file.write( bytearray( '\t<studio>{}</studio>\n'.format( film.channel ), 'utf-8' ) )
					file.write( b'</tvshow>\n' )
			except Exception as err:
				self.error( 'Failure creating show NFO file for {}: {}', videourl, err )

		try:
			with closing( xbmcvfs.File( filename, 'w' ) ) as file:
				file.write( b'<episodedetails>\n' )
				file.write( bytearray( '\t<title>{}</title>\n'.format( film.title ), 'utf-8' ) )
				file.write( b'\t<season>1</season>\n' )
				file.write( bytearray( '\t<episode>{}</episode>\n'.format( episode ), 'utf-8' ) )
				file.write( bytearray( '\t<showtitle>{}</showtitle>\n'.format( film.show ), 'utf-8' ) )
				file.write( bytearray( '\t<plot>{}</plot>\n'.format( film.description ), 'utf-8' ) )
				file.write( bytearray( '\t<aired>{}</aired>\n'.format( film.aired ), 'utf-8' ) )
				if film.seconds > 60:
					file.write( bytearray( '\t<runtime>{}</runtime>\n'.format( int( film.seconds / 60 ) ), 'utf-8' ) )
				file.write( bytearray( '\t<studio>{}</studio\n'.format( film.channel ), 'utf-8' ) )
				file.write( b'</episodedetails>\n' )
		except Exception as err:
			self.error( 'Failure creating episode NFO file for {}: {}', videourl, err )

	def Init( self ):
		self.args = urlparse.parse_qs( sys.argv[2][1:] )
		self.db.Init()
		if self.settings.HandleFirstRun():
			# TODO: Implement Issue #16
			pass

	def Do( self ):
		mode = self.args.get( 'mode', None )
		if mode is None:
			self.showMainMenu()
		elif mode[0] == 'search':
			self.showSearch()
		elif mode[0] == 'searchall':
			self.showSearchAll()
		elif mode[0] == 'livestreams':
			self.db.GetLiveStreams( FilmUI( self, [ xbmcplugin.SORT_METHOD_LABEL ] ) )
		elif mode[0] == 'recent':
			channel = self.args.get( 'channel', [0] )
			self.db.GetRecents( channel[0], FilmUI( self ) )
		elif mode[0] == 'recentchannels':
			self.db.GetRecentChannels( ChannelUI( self.addon_handle, nextdir = 'recent' ) )
		elif mode[0] == 'channels':
			self.db.GetChannels( ChannelUI( self.addon_handle ) )
		elif mode[0] == 'action-dbinfo':
			self.showDbInfo()
		elif mode[0] == 'initial':
			channel = self.args.get( 'channel', [0] )
			self.db.GetInitials( channel[0], InitialUI( self.addon_handle ) )
		elif mode[0] == 'shows':
			channel = self.args.get( 'channel', [0] )
			initial = self.args.get( 'initial', [None] )
			self.db.GetShows( channel[0], initial[0], ShowUI( self.addon_handle ) )
		elif mode[0] == 'films':
			show = self.args.get( 'show', [0] )
			self.db.GetFilms( show[0], FilmUI( self ) )
		elif mode[0] == 'download':
			filmid	= self.args.get( 'id', [0] )
			quality	= self.args.get( 'quality', [1] )
			self.doDownloadFilm( filmid[0], quality[0] )
		elif mode[0] == 'enqueue':
			self.doEnqueueFilm( self.args.get( 'id', [0] )[0] )

	def Exit( self ):
		self.db.Exit()


# -- Main Code ----------------------------------------------
if __name__ == '__main__':
	addon = MediathekView()
	addon.Init()
	addon.Do()
	addon.Exit()
	del addon
