# -*- coding: utf-8 -*-
# Copyright (c) 2017-2018, Leo Moll

# -- Imports ------------------------------------------------
import os
import time
import ijson
import random
import urllib2
import datetime
import subprocess

import defusedxml.ElementTree as etree
import resources.lib.mvutils as mvutils

from operator import itemgetter
#from resources.lib.utils import *
from resources.lib.store import Store
from resources.lib.exceptions import DatabaseCorrupted
from resources.lib.exceptions import DatabaseLost
from resources.lib.exceptions import ExitRequested

# -- Unpacker support ---------------------------------------
upd_can_bz2 = False
upd_can_gz  = False

try:
	import bz2
	upd_can_bz2 = True
except ImportError:
	pass

try:
	import gzip
	upd_can_gz = True
except ImportError:
	pass

# -- Constants ----------------------------------------------
FILMLISTE_AKT_URL = 'https://res.mediathekview.de/akt.xml'
FILMLISTE_DIF_URL = 'https://res.mediathekview.de/diff.xml'

# -- Classes ------------------------------------------------
class MediathekViewUpdater( object ):
	def __init__( self, logger, notifier, settings, monitor = None ):
		self.logger		= logger
		self.notifier	= notifier
		self.settings	= settings
		self.monitor	= monitor
		self.db			= None
		self.cycle		= 0
		self.use_xz     = mvutils.find_xz() is not None

	def Init( self, convert = False ):
		if self.db is not None:
			self.Exit()
		self.db = Store( self.logger, self.notifier, self.settings )
		self.db.Init( convert = convert )

	def Exit( self ):
		if self.db is not None:
			self.db.Exit()
			del self.db
			self.db = None

	def Reload( self ):
		self.Exit()
		self.Init()

	def IsEnabled( self ):
		return self.settings.updenabled

	def GetCurrentUpdateOperation( self, force = False ):
		if self.db is None:
			# db not available - no update
			self.logger.info( 'Update disabled since database not available' )
			return 0

		elif self.settings.updmode == 0:
			# update disabled - no update
			return 0

		elif self.settings.updmode == 1 or self.settings.updmode == 2:
			# manual update or update on first start
			if self.settings.IsUpdateTriggered() is True:
				return self._getNextUpdateOperation( True )
			else:
				# no update on all subsequent calls
				return 0

		elif self.settings.updmode == 3:
			# automatic update
			if self.settings.IsUserAlive():
				return self._getNextUpdateOperation( force )
			else:
				# no update of user is idle for more than 2 hours
				return 0

	def _getNextUpdateOperation( self, force = False ):
		status = self.db.GetStatus()
		tsnow = int( time.time() )
		tsold = status['lastupdate']
		dtnow = datetime.datetime.fromtimestamp( tsnow ).date()
		dtold = datetime.datetime.fromtimestamp( tsold ).date()
		if status['status'] == 'UNINIT':
			# database not initialized - no update
			self.logger.debug( 'database not initialized' )
			return 0
		elif status['status'] == "UPDATING" and tsnow - tsold > 10800:
			# process was probably killed during update - no update
			self.logger.info( 'Stuck update pretending to run since epoch {} reset', tsold )
			self.db.UpdateStatus( 'ABORTED' )
			return 0
		elif status['status'] == "UPDATING":
			# already updating - no update
			self.logger.debug( 'Already updating' )
			return 0
		elif not force and tsnow - tsold < self.settings.updinterval:
			# last update less than the configured update interval - no update
			self.logger.debug( 'Last update less than the configured update interval. do nothing' )
			return 0
		elif dtnow != dtold:
			# last update was not today. do full update once a day
			self.logger.debug( 'Last update was not today. do full update once a day' )
			return 1
		elif status['status'] == "ABORTED" and status['fullupdate'] == 1:
			# last full update was aborted - full update needed
			self.logger.debug( 'Last full update was aborted - full update needed' )
			return 1
		else:
			# do differential update
			self.logger.debug( 'Do differential update' )
			return 2

	def Update( self, full ):
		if self.db is None:
			return
		if self.db.SupportsUpdate():
			if self.GetNewestList( full ):
				if self.Import( full ):
					self.cycle += 1
			self.DeleteList( full )

	def Import( self, full ):
		( _, _, destfile, avgrecsize ) = self._get_update_info( full )
		if not mvutils.file_exists( destfile ):
			self.logger.error( 'File {} does not exists', destfile )
			return False
		# estimate number of records in update file
		records = int( mvutils.file_size( destfile ) / avgrecsize )
		if not self.db.ftInit():
			self.logger.warn( 'Failed to initialize update. Maybe a concurrency problem?' )
			return False
		try:
			self.logger.info( 'Starting import of approx. {} records from {}', records, destfile )
			with open( destfile, 'r' ) as file:
				parser = ijson.parse( file )
				flsm = 0
				flts = 0
				( self.tot_chn, self.tot_shw, self.tot_mov ) = self._update_start( full )
				self.notifier.ShowUpdateProgress()
				for prefix, event, value in parser:
					if ( prefix, event ) == ( "X", "start_array" ):
						self._init_record()
					elif ( prefix, event ) == ( "X", "end_array" ):
						self._end_record( records )
						if self.count % 100 == 0 and self.monitor.abortRequested():
							# kodi is shutting down. Close all
							self._update_end( full, 'ABORTED' )
							self.notifier.CloseUpdateProgress()
							return True
					elif ( prefix, event ) == ( "X.item", "string" ):
						if value is not None:
	#						self._add_value( value.strip().encode('utf-8') )
							self._add_value( value.strip() )
						else:
							self._add_value( "" )
					elif ( prefix, event ) == ( "Filmliste", "start_array" ):
						flsm += 1
					elif ( prefix, event ) == ( "Filmliste.item", "string" ):
						flsm += 1
						if flsm == 2 and value is not None:
							# this is the timestmap of this database update
							try:
								fldt = datetime.datetime.strptime( value.strip(), "%d.%m.%Y, %H:%M" )
								flts = int( time.mktime( fldt.timetuple() ) )
								self.db.UpdateStatus( filmupdate = flts )
								self.logger.info( 'Filmliste dated {}', value.strip() )
							except TypeError:
								# SEE: https://forum.kodi.tv/showthread.php?tid=112916&pid=1214507#pid1214507
								# Wonderful. His name is also Leopold
								try:
									flts = int( time.mktime( time.strptime( value.strip(), "%d.%m.%Y, %H:%M" ) ) )
									self.db.UpdateStatus( filmupdate = flts )
									self.logger.info( 'Filmliste dated {}', value.strip() )
								except Exception as err:
									# If the universe hates us...
									self.logger.debug( 'Could not determine date "{}" of filmliste: {}', value.strip(), err )
							except ValueError as err:
								pass

			self._update_end( full, 'IDLE' )
			self.logger.info( 'Import of {} in update cycle {} finished', destfile, self.cycle )
			self.notifier.CloseUpdateProgress()
			return True
		except KeyboardInterrupt:
			self._update_end( full, 'ABORTED' )
			self.logger.info( 'Update cycle {} interrupted by user', self.cycle )
			self.notifier.CloseUpdateProgress()
			return False
		except DatabaseCorrupted as err:
			self.logger.error( '{} on update cycle {}', err, self.cycle )
			self.notifier.CloseUpdateProgress()
		except DatabaseLost as err:
			self.logger.error( '{} on update cycle {}', err, self.cycle )
			self.notifier.CloseUpdateProgress()
		except Exception as err:
			self.logger.error( 'Error {} while processing {} on update cycle {}', err, destfile, self.cycle )
			self._update_end( full, 'ABORTED' )
			self.notifier.CloseUpdateProgress()
		return False

	def GetNewestList( self, full ):
		( url, compfile, destfile, _ ) = self._get_update_info( full )
		if url is None:
			self.logger.error( 'No suitable archive extractor available for this system' )
			self.notifier.ShowMissingExtractorError()
			return False

		# get mirrorlist
		self.logger.info( 'Opening {}', url )
		try:
			data = urllib2.urlopen( url ).read()
		except urllib2.URLError as err:
			self.logger.error( 'Failure opening {}', url )
			self.notifier.ShowDownloadError( url, err )
			return False
		root = etree.fromstring ( data )
		urls = []
		for server in root.findall( 'Server' ):
			try:
				URL = server.find( 'URL' ).text
				Prio = server.find( 'Prio' ).text
				urls.append( ( self._get_update_url( URL ), float( Prio ) + random.random() * 1.2 ) )
				self.logger.info( 'Found mirror {} (Priority {})', URL, Prio )
			except AttributeError:
				pass
		urls = sorted( urls, key = itemgetter( 1 ) )
		urls = [ url[0] for url in urls ]

		# cleanup downloads
		self.logger.info( 'Cleaning up old downloads...' )
		mvutils.file_remove( compfile )
		mvutils.file_remove( destfile )

		# download filmliste
		self.notifier.ShowDownloadProgress()
		lasturl = ''
		for url in urls:
			try:
				lasturl = url
				self.logger.info( 'Trying to download {} from {}...', os.path.basename( compfile ), url )
				self.notifier.UpdateDownloadProgress( 0, url )
				mvutils.url_retrieve( url, filename = compfile, reporthook = self.notifier.HookDownloadProgress, aborthook = self.monitor.abortRequested )
				break
			except urllib2.URLError as err:
				self.logger.error( 'Failure downloading {}', url )
				self.notifier.CloseDownloadProgress()
				self.notifier.ShowDownloadError( lasturl, err )
				return False
			except ExitRequested as err:
				self.logger.error( 'Immediate exit requested. Aborting download of {}', url )
				self.notifier.CloseDownloadProgress()
				self.notifier.ShowDownloadError( lasturl, err )
				return False
			except Exception as err:
				self.logger.error( 'Failure writng {}', url )
				self.notifier.CloseDownloadProgress()
				self.notifier.ShowDownloadError( lasturl, err )
				return False

		# decompress filmliste
		if self.use_xz is True:
			self.logger.info( 'Trying to decompress xz file...' )
			retval = subprocess.call( [ mvutils.find_xz(), '-d', compfile ] )
			self.logger.info( 'Return {}', retval )
		elif upd_can_bz2 is True:
			self.logger.info( 'Trying to decompress bz2 file...' )
			retval = self._decompress_bz2( compfile, destfile )
			self.logger.info( 'Return {}', retval )
		elif upd_can_gz is True:
			self.logger.info( 'Trying to decompress gz file...' )
			retval = self._decompress_gz( compfile, destfile )
			self.logger.info( 'Return {}', retval )
		else:
			# should nebver reach
			pass

		self.notifier.CloseDownloadProgress()
		return retval == 0 and mvutils.file_exists( destfile )

	def DeleteList( self, full ):
		( _, compfile, destfile, _ ) = self._get_update_info( full )
		self.logger.info( 'Cleaning up downloads...' )
		mvutils.file_remove( compfile )
		mvutils.file_remove( destfile )

	def _get_update_info( self, full ):
		if self.use_xz is True:
			ext = 'xz'
		elif upd_can_bz2 is True:
			ext = 'bz2'
		elif upd_can_gz is True:
			ext = 'gz'
		else:
			return ( None, None, None, 0, )

		if full:
			return (
				FILMLISTE_AKT_URL,
				os.path.join( self.settings.datapath, 'Filmliste-akt.' + ext ),
				os.path.join( self.settings.datapath, 'Filmliste-akt' ),
				600,
			)
		else:
			return (
				FILMLISTE_DIF_URL,
				os.path.join( self.settings.datapath, 'Filmliste-diff.' + ext ),
				os.path.join( self.settings.datapath, 'Filmliste-diff' ),
				700,
			)

	def _get_update_url( self, url ):
		if self.use_xz is True:
			return url
		elif upd_can_bz2 is True:
			return os.path.splitext( url )[0] + '.bz2'
		elif upd_can_gz is True:
			return os.path.splitext( url )[0] + '.gz'
		else:
			# should never happen since it will not be called
			return None

	def _update_start( self, full ):
		self.logger.info( 'Initializing update...' )
		self.add_chn = 0
		self.add_shw = 0
		self.add_mov = 0
		self.add_chn = 0
		self.add_shw = 0
		self.add_mov = 0
		self.del_chn = 0
		self.del_shw = 0
		self.del_mov = 0
		self.index = 0
		self.count = 0
		self.film = {
			"channel": "",
			"show": "",
			"title": "",
			"aired": "1980-01-01 00:00:00",
			"duration": "00:00:00",
			"size": 0,
			"description": "",
			"website": "",
			"url_sub": "",
			"url_video": "",
			"url_video_sd": "",
			"url_video_hd": "",
			"airedepoch": 0,
			"geo": ""
		}
		return self.db.ftUpdateStart( full )

	def _update_end( self, full, status ):
		self.logger.info( 'Added: channels:%d, shows:%d, movies:%d ...' % ( self.add_chn, self.add_shw, self.add_mov ) )
		( self.del_chn, self.del_shw, self.del_mov, self.tot_chn, self.tot_shw, self.tot_mov ) = self.db.ftUpdateEnd( full and status == 'IDLE' )
		self.logger.info( 'Deleted: channels:%d, shows:%d, movies:%d' % ( self.del_chn, self.del_shw, self.del_mov ) )
		self.logger.info( 'Total: channels:%d, shows:%d, movies:%d' % ( self.tot_chn, self.tot_shw, self.tot_mov ) )
		self.db.UpdateStatus(
			status,
			int( time.time() ) if status != 'ABORTED' else None,
			None,
			1 if full else 0,
			self.add_chn, self.add_shw, self.add_mov,
			self.del_chn, self.del_shw, self.del_mov,
			self.tot_chn, self.tot_shw, self.tot_mov
		)

	def _init_record( self ):
		self.index = 0
		self.film["title"] = ""
		self.film["aired"] = "1980-01-01 00:00:00"
		self.film["duration"] = "00:00:00"
		self.film["size"] = 0
		self.film["description"] = ""
		self.film["website"] = ""
		self.film["url_sub"] = ""
		self.film["url_video"] = ""
		self.film["url_video_sd"] = ""
		self.film["url_video_hd"] = ""
		self.film["airedepoch"] = 0
		self.film["geo"] = ""

	def _end_record( self, records ):
		if self.count % 1000 == 0:
			percent = int( self.count * 100 / records )
			self.logger.info( 'In progress (%d%%): channels:%d, shows:%d, movies:%d ...' % ( percent, self.add_chn, self.add_shw, self.add_mov ) )
			self.notifier.UpdateUpdateProgress( percent if percent <= 100 else 100, self.count, self.add_chn, self.add_shw, self.add_mov )
			self.db.UpdateStatus(
				add_chn = self.add_chn,
				add_shw = self.add_shw,
				add_mov = self.add_mov,
				tot_chn = self.tot_chn + self.add_chn,
				tot_shw = self.tot_shw + self.add_shw,
				tot_mov = self.tot_mov + self.add_mov
			)
			self.count = self.count + 1
			( _, cnt_chn, cnt_shw, cnt_mov ) = self.db.ftInsertFilm( self.film, True )
		else:
			self.count = self.count + 1
			( _, cnt_chn, cnt_shw, cnt_mov ) = self.db.ftInsertFilm( self.film, False )
		self.add_chn += cnt_chn
		self.add_shw += cnt_shw
		self.add_mov += cnt_mov

	def _add_value( self, val ):
		if self.index == 0:
			if val != "":
				self.film["channel"] = val
		elif self.index == 1:
			if val != "":
				self.film["show"] = val[:255]
		elif self.index == 2:
			self.film["title"] = val[:255]
		elif self.index == 3:
			if len(val) == 10:
				self.film["aired"] = val[6:] + '-' + val[3:5] + '-' + val[:2]
		elif self.index == 4:
			if ( self.film["aired"] != "1980-01-01 00:00:00" ) and ( len(val) == 8 ):
				self.film["aired"] = self.film["aired"] + " " + val
		elif self.index == 5:
			if len(val) == 8:
				self.film["duration"] = val
		elif self.index == 6:
			if val != "":
				self.film["size"] = int(val)
		elif self.index == 7:
			self.film["description"] = val
		elif self.index == 8:
			self.film["url_video"] = val
		elif self.index == 9:
			self.film["website"] = val
		elif self.index == 10:
			self.film["url_sub"] = val
		elif self.index == 12:
			self.film["url_video_sd"] = self._make_url(val)
		elif self.index == 14:
			self.film["url_video_hd"] = self._make_url(val)
		elif self.index == 16:
			if val != "":
				self.film["airedepoch"] = int(val)
		elif self.index == 18:
			self.film["geo"] = val
		self.index = self.index + 1

	def _make_url( self, val ):
		x = val.split( '|' )
		if len( x ) == 2:
			cnt = int( x[0] )
			return self.film["url_video"][:cnt] + x[1]
		else:
			return val

	def _decompress_bz2( self, sourcefile, destfile ):
		blocksize = 8192
		try:
			with open( destfile, 'wb' ) as df, open( sourcefile, 'rb' ) as sf:
				decompressor = bz2.BZ2Decompressor()
				for data in iter( lambda : sf.read( blocksize ), b'' ):
					df.write( decompressor.decompress( data ) )
		except Exception as err:
			self.logger.error( 'bz2 decompression failed: {}'.format( err ) )
			return -1
		return 0

	def _decompress_gz( self, sourcefile, destfile ):
		blocksize = 8192
		try:
			with open( destfile, 'wb' ) as df, gzip.open( sourcefile ) as sf:
				for data in iter( lambda : sf.read( blocksize ), b'' ):
					df.write( data )
		except Exception as err:
			self.logger.error( 'gz decompression failed: {}'.format( err ) )
			return -1
		return 0
