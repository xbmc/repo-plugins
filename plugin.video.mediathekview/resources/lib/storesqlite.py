# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
import os, time
import sqlite3

import resources.lib.mvutils as mvutils

from resources.lib.film import Film
from resources.lib.exceptions import DatabaseCorrupted

# -- Classes ------------------------------------------------
class StoreSQLite( object ):
	def __init__( self, logger, notifier, settings ):
		self.logger		= logger
		self.notifier	= notifier
		self.settings	= settings
		# internals
		self.conn		= None
		self.dbfile		= os.path.join( self.settings.datapath, 'filmliste-v1.db' )
		# useful query fragments
		self.sql_query_films	= "SELECT film.id,title,show,channel,description,duration,size,datetime(aired, 'unixepoch', 'localtime'),url_sub,url_video,url_video_sd,url_video_hd FROM film LEFT JOIN show ON show.id=film.showid LEFT JOIN channel ON channel.id=film.channelid"
		self.sql_query_filmcnt	= "SELECT COUNT(*) FROM film LEFT JOIN show ON show.id=film.showid LEFT JOIN channel ON channel.id=film.channelid"
		self.sql_cond_recent	= "( ( UNIX_TIMESTAMP() - aired ) <= 86400 )"
		self.sql_cond_nofuture	= " AND ( ( aired IS NULL ) OR ( ( UNIX_TIMESTAMP() - aired ) > 0 ) )" if settings.nofuture else ""
		self.sql_cond_minlength	= " AND ( ( duration IS NULL ) OR ( duration >= %d ) )" % settings.minlength if settings.minlength > 0 else ""

	def Init( self, reset = False ):
		self.logger.info( 'Using SQLite version {}, python library sqlite3 version {}', sqlite3.sqlite_version, sqlite3.version )
		if not mvutils.dir_exists( self.settings.datapath ):
			os.mkdir( self.settings.datapath )
		if reset == True or not mvutils.file_exists( self.dbfile ):
			self.logger.info( '===== RESET: Database will be deleted and regenerated =====' )
			self._file_remove( self.dbfile )
			self.conn = sqlite3.connect( self.dbfile, timeout = 60 )
			self._handle_database_initialization()
		else:
			try:
				self.conn = sqlite3.connect( self.dbfile, timeout = 60 )
			except sqlite3.DatabaseError as err:
				self.logger.error( 'Error while opening database: {}. trying to fully reset the Database...', err )
				self.Init( reset = True )

		self.conn.execute( 'pragma journal_mode=off' )	# 3x speed-up, check mode 'WAL'
		self.conn.execute( 'pragma synchronous=off' )	# that is a bit dangerous :-) but faaaast

		self.conn.create_function( 'UNIX_TIMESTAMP', 0, UNIX_TIMESTAMP )
		self.conn.create_aggregate( 'GROUP_CONCAT', 1, GROUP_CONCAT )

	def Exit( self ):
		if self.conn is not None:
			self.conn.close()
			self.conn	= None

	def Search( self, search, filmui ):
		self._Search_Condition( '( ( title LIKE "%%%s%%" ) OR ( show LIKE "%%%s%%" ) )' % ( search, search ), filmui, True, True, self.settings.maxresults )

	def SearchFull( self, search, filmui ):
		self._Search_Condition( '( ( title LIKE "%%%s%%" ) OR ( show LIKE "%%%s%%" ) OR ( description LIKE "%%%s%%") )' % ( search, search, search ), filmui, True, True, self.settings.maxresults )

	def GetRecents( self, channelid, filmui ):
		sql_cond_channel = ' AND ( film.channelid=' + str( channelid ) + ' ) ' if channelid != '0' else ''
		self._Search_Condition( self.sql_cond_recent + sql_cond_channel, filmui, True, False, 10000 )

	def GetLiveStreams( self, filmui ):
		self._Search_Condition( '( show.search="LIVESTREAM" )', filmui, False, False, 10000 )

	def GetChannels( self, channelui ):
		self._Channels_Condition( None, channelui )

	def GetRecentChannels( self, channelui ):
		self._Channels_Condition( self.sql_cond_recent, channelui )

	def GetInitials( self, channelid, initialui ):
		if self.conn is None:
			return
		try:
			condition = 'WHERE ( channelid=' + str( channelid ) + ' ) ' if channelid != '0' else ''
			self.logger.info( 'SQlite Query: {}',
				'SELECT SUBSTR(search,1,1),COUNT(*) FROM show ' +
				condition +
				'GROUP BY LEFT(search,1)'
			)
			cursor = self.conn.cursor()
			cursor.execute(
				'SELECT SUBSTR(search,1,1),COUNT(*) FROM show ' +
				condition +
				'GROUP BY SUBSTR(search,1,1)'
			)
			initialui.Begin( channelid )
			for ( initialui.initial, initialui.count ) in cursor:
				initialui.Add()
			initialui.End()
			cursor.close()
		except sqlite3.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def GetShows( self, channelid, initial, showui ):
		if self.conn is None:
			return
		try:
			if channelid == '0' and self.settings.groupshows:
				query = 'SELECT GROUP_CONCAT(show.id),GROUP_CONCAT(channelid),show,GROUP_CONCAT(channel) FROM show LEFT JOIN channel ON channel.id=show.channelid WHERE ( show LIKE "%s%%" ) GROUP BY show' % initial
			elif channelid == '0':
				query = 'SELECT show.id,show.channelid,show.show,channel.channel FROM show LEFT JOIN channel ON channel.id=show.channelid WHERE ( show LIKE "%s%%" )' % initial
			else:
				query = 'SELECT show.id,show.channelid,show.show,channel.channel FROM show LEFT JOIN channel ON channel.id=show.channelid WHERE ( channelid=%s ) AND ( show LIKE "%s%%" )' % ( channelid, initial )
			self.logger.info( 'SQLite Query: {}', query )
			cursor = self.conn.cursor()
			cursor.execute( query )
			showui.Begin( channelid )
			for ( showui.id, showui.channelid, showui.show, showui.channel ) in cursor:
				showui.Add()
			showui.End()
			cursor.close()
		except sqlite3.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def GetFilms( self, showid, filmui ):
		if self.conn is None:
			return
		if showid.find( ',' ) == -1:
			# only one channel id
			condition = '( showid=%s )' % showid
			showchannels = False
		else:
			# multiple channel ids
			condition = '( showid IN ( %s ) )' % showid
			showchannels = True
		self._Search_Condition( condition, filmui, False, showchannels, 10000 )

	def _Channels_Condition( self, condition, channelui ):
		if self.conn is None:
			return
		try:
			if condition is None:
				query = 'SELECT id,channel,0 AS `count` FROM channel'
			else:
				query = 'SELECT channel.id AS `id`,channel,COUNT(*) AS `count` FROM film LEFT JOIN channel ON channel.id=film.channelid WHERE ' + condition + ' GROUP BY channel'
			self.logger.info( 'SQLite Query: {}', query )
			cursor = self.conn.cursor()
			cursor.execute( query )
			channelui.Begin()
			for ( channelui.id, channelui.channel, channelui.count ) in cursor:
				channelui.Add()
			channelui.End()
			cursor.close()
		except sqlite3.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def _Search_Condition( self, condition, filmui, showshows, showchannels, maxresults ):
		if self.conn is None:
			return
		try:
			maxresults = int( maxresults )
			self.logger.info( 'SQLite Query: {}',
				self.sql_query_films +
				' WHERE ' +
				condition +
				self.sql_cond_nofuture +
				self.sql_cond_minlength
			)
			cursor = self.conn.cursor()
			cursor.execute(
				self.sql_query_filmcnt +
				' WHERE ' +
				condition +
				self.sql_cond_nofuture +
				self.sql_cond_minlength +
				' LIMIT {}'.format( maxresults + 1 ) if maxresults else ''
			)
			( results, ) = cursor.fetchone()
			if maxresults and results > maxresults:
				self.notifier.ShowLimitResults( maxresults )
			cursor.execute(
				self.sql_query_films +
				' WHERE ' +
				condition +
				self.sql_cond_nofuture +
				self.sql_cond_minlength +
				' LIMIT {}'.format( maxresults ) if maxresults else ''
			)
			filmui.Begin( showshows, showchannels )
			for ( filmui.id, filmui.title, filmui.show, filmui.channel, filmui.description, filmui.seconds, filmui.size, filmui.aired, filmui.url_sub, filmui.url_video, filmui.url_video_sd, filmui.url_video_hd ) in cursor:
				filmui.Add( totalItems = results )
			filmui.End()
			cursor.close()
		except sqlite3.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def RetrieveFilmInfo( self, filmid ):
		if self.conn is None:
			return None
		try:
			condition = '( film.id={} )'.format( filmid )
			self.logger.info( 'SQLite Query: {}',
				self.sql_query_films +
				' WHERE ' +
				condition
			)
			cursor = self.conn.cursor()
			cursor.execute(
				self.sql_query_films +
				' WHERE ' +
				condition
			)
			film = Film()
			for ( film.id, film.title, film.show, film.channel, film.description, film.seconds, film.size, film.aired, film.url_sub, film.url_video, film.url_video_sd, film.url_video_hd ) in cursor:
				cursor.close()
				return film
			cursor.close()
		except sqlite3.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )
		return None

	def GetStatus( self ):
		status = {
			'modified': int( time.time() ),
			'status': '',
			'lastupdate': 0,
			'filmupdate': 0,
			'fullupdate': 0,
			'add_chn': 0,
			'add_shw': 0,
			'add_mov': 0,
			'del_chn': 0,
			'del_shw': 0,
			'del_mov': 0,
			'tot_chn': 0,
			'tot_shw': 0,
			'tot_mov': 0
		}
		if self.conn is None:
			status['status'] = "UNINIT"
			return status
		self.conn.commit()
		cursor = self.conn.cursor()
		cursor.execute( 'SELECT * FROM `status` LIMIT 1' )
		r = cursor.fetchall()
		cursor.close()
		if len( r ) == 0:
			status['status'] = "NONE"
			return status
		status['modified']		= r[0][0]
		status['status']		= r[0][1]
		status['lastupdate']	= r[0][2]
		status['filmupdate']	= r[0][3]
		status['fullupdate']	= r[0][4]
		status['add_chn']		= r[0][5]
		status['add_shw']		= r[0][6]
		status['add_mov']		= r[0][7]
		status['del_chn']		= r[0][8]
		status['del_shw']		= r[0][9]
		status['del_mov']		= r[0][10]
		status['tot_chn']		= r[0][11]
		status['tot_shw']		= r[0][12]
		status['tot_mov']		= r[0][13]
		return status

	def UpdateStatus( self, status = None, lastupdate = None, filmupdate = None, fullupdate = None, add_chn = None, add_shw = None, add_mov = None, del_chn = None, del_shw = None, del_mov = None, tot_chn = None, tot_shw = None, tot_mov = None ):
		if self.conn is None:
			return
		new = self.GetStatus()
		old = new['status']
		if status is not None:
			new['status'] = status
		if lastupdate is not None:
			new['lastupdate'] = lastupdate
		if filmupdate is not None:
			new['filmupdate'] = filmupdate
		if fullupdate is not None:
			new['fullupdate'] = fullupdate
		if add_chn is not None:
			new['add_chn'] = add_chn
		if add_shw is not None:
			new['add_shw'] = add_shw
		if add_mov is not None:
			new['add_mov'] = add_mov
		if del_chn is not None:
			new['del_chn'] = del_chn
		if del_shw is not None:
			new['del_shw'] = del_shw
		if del_mov is not None:
			new['del_mov'] = del_mov
		if tot_chn is not None:
			new['tot_chn'] = tot_chn
		if tot_shw is not None:
			new['tot_shw'] = tot_shw
		if tot_mov is not None:
			new['tot_mov'] = tot_mov
		# TODO: we should only write, if we have changed something...
		new['modified'] = int( time.time() )
		cursor = self.conn.cursor()
		if old == "NONE":
			# insert status
			cursor.execute(
				"""
				INSERT INTO `status` (
					`modified`,
					`status`,
					`lastupdate`,
					`filmupdate`,
					`fullupdate`,
					`add_chn`,
					`add_shw`,
					`add_mov`,
					`del_chm`,
					`del_shw`,
					`del_mov`,
					`tot_chn`,
					`tot_shw`,
					`tot_mov`
				)
				VALUES (
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?
				)
				""", (
					new['modified'],
					new['status'],
					new['lastupdate'],
					new['filmupdate'],
					new['fullupdate'],
					new['add_chn'],
					new['add_shw'],
					new['add_mov'],
					new['del_chn'],
					new['del_shw'],
					new['del_mov'],
					new['tot_chn'],
					new['tot_shw'],
					new['tot_mov'],
				)
			)
		else:
			# update status
			cursor.execute(
				"""
				UPDATE `status`
				SET		`modified`		= ?,
						`status`		= ?,
						`lastupdate`	= ?,
						`filmupdate`	= ?,
						`fullupdate`	= ?,
						`add_chn`		= ?,
						`add_shw`		= ?,
						`add_mov`		= ?,
						`del_chm`		= ?,
						`del_shw`		= ?,
						`del_mov`		= ?,
						`tot_chn`		= ?,
						`tot_shw`		= ?,
						`tot_mov`		= ?
				""", (
					new['modified'],
					new['status'],
					new['lastupdate'],
					new['filmupdate'],
					new['fullupdate'],
					new['add_chn'],
					new['add_shw'],
					new['add_mov'],
					new['del_chn'],
					new['del_shw'],
					new['del_mov'],
					new['tot_chn'],
					new['tot_shw'],
					new['tot_mov'],
				)
			)
		cursor.close()
		self.conn.commit()

	def SupportsUpdate( self ):
		return True

	def ftInit( self ):
		try:
			# prevent concurrent updating
			self.conn.commit()
			cursor = self.conn.cursor()
			cursor.execute(
				"""
				UPDATE	`status`
				SET		`modified`		= ?,
						`status`		= 'UPDATING'
				WHERE	( `status` != 'UPDATING' )
						OR
						( `modified` < ? )
				""", (
					int( time.time() ),
					int( time.time() ) - 86400
				)
			)
			retval = cursor.rowcount > 0
			self.conn.commit()
			cursor.close()
			self.ft_channel = None
			self.ft_channelid = None
			self.ft_show = None
			self.ft_showid = None
			return retval
		except sqlite3.DatabaseError as err:
			self._handle_database_corruption( err )
			raise DatabaseCorrupted( 'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format( err ) )

	def ftUpdateStart( self, full ):
		try:
			cursor = self.conn.cursor()
			if full:
				cursor.executescript( """
					UPDATE	`channel`
					SET		`touched` = 0;

					UPDATE	`show`
					SET		`touched` = 0;

					UPDATE	`film`
					SET		`touched` = 0;
				""" )
			cursor.execute( 'SELECT COUNT(*) FROM `channel`' )
			r1 = cursor.fetchone()
			cursor.execute( 'SELECT COUNT(*) FROM `show`' )
			r2 = cursor.fetchone()
			cursor.execute( 'SELECT COUNT(*) FROM `film`' )
			r3 = cursor.fetchone()
			cursor.close()
			self.conn.commit()
			return ( r1[0], r2[0], r3[0], )
		except sqlite3.DatabaseError as err:
			self._handle_database_corruption( err )
			raise DatabaseCorrupted( 'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format( err ) )

	def ftUpdateEnd( self, delete ):
		try:
			cursor = self.conn.cursor()
			cursor.execute( 'SELECT COUNT(*) FROM `channel` WHERE ( touched = 0 )' )
			( del_chn, ) = cursor.fetchone()
			cursor.execute( 'SELECT COUNT(*) FROM `show` WHERE ( touched = 0 )' )
			( del_shw, ) = cursor.fetchone()
			cursor.execute( 'SELECT COUNT(*) FROM `film` WHERE ( touched = 0 )' )
			( del_mov, ) = cursor.fetchone()
			if delete:
				cursor.execute( 'DELETE FROM `show` WHERE ( show.touched = 0 ) AND ( ( SELECT SUM( film.touched ) FROM `film` WHERE film.showid = show.id ) = 0 )' )
				cursor.execute( 'DELETE FROM `film` WHERE ( touched = 0 )' )
			else:
				del_chn = 0
				del_shw = 0
				del_mov = 0
			cursor.execute( 'SELECT COUNT(*) FROM `channel`' )
			( cnt_chn, ) = cursor.fetchone()
			cursor.execute( 'SELECT COUNT(*) FROM `show`' )
			( cnt_shw, ) = cursor.fetchone()
			cursor.execute( 'SELECT COUNT(*) FROM `film`' )
			( cnt_mov, ) = cursor.fetchone()
			cursor.close()
			self.conn.commit()
			return ( del_chn, del_shw, del_mov, cnt_chn, cnt_shw, cnt_mov, )
		except sqlite3.DatabaseError as err:
			self._handle_database_corruption( err )
			raise DatabaseCorrupted( 'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format( err ) )

	def ftInsertFilm( self, film, commit ):
		try:
			cursor = self.conn.cursor()
			newchn = False
			inschn = 0
			insshw = 0
			insmov = 0

			# handle channel
			if self.ft_channel != film['channel']:
				# process changed channel
				newchn = True
				cursor.execute( 'SELECT `id`,`touched` FROM `channel` WHERE channel.channel=?', ( film['channel'], ) )
				r = cursor.fetchall()
				if len( r ) > 0:
					# get the channel data
					self.ft_channel = film['channel']
					self.ft_channelid = r[0][0]
					if r[0][1] == 0:
						# updated touched
						cursor.execute( 'UPDATE `channel` SET `touched`=1 WHERE ( channel.id=? )', ( self.ft_channelid, ) )
				else:
					# insert the new channel
					inschn = 1
					cursor.execute( 'INSERT INTO `channel` ( `dtCreated`,`channel` ) VALUES ( ?,? )', ( int( time.time() ), film['channel'] ) )
					self.ft_channel = film['channel']
					self.ft_channelid = cursor.lastrowid

			# handle show
			if newchn or self.ft_show != film['show']:
				# process changed show
				cursor.execute( 'SELECT `id`,`touched` FROM `show` WHERE ( show.channelid=? ) AND ( show.show=? )', ( self.ft_channelid, film['show'] ) )
				r = cursor.fetchall()
				if len( r ) > 0:
					# get the show data
					self.ft_show = film['show']
					self.ft_showid = r[0][0]
					if r[0][1] == 0:
						# updated touched
						cursor.execute( 'UPDATE `show` SET `touched`=1 WHERE ( show.id=? )', ( self.ft_showid, ) )
				else:
					# insert the new show
					insshw = 1
					cursor.execute(
						"""
						INSERT INTO `show` (
							`dtCreated`,
							`channelid`,
							`show`,
							`search`
						)
						VALUES (
							?,
							?,
							?,
							?
						)
						""", (
							int( time.time() ),
							self.ft_channelid, film['show'],
							mvutils.make_search_string( film['show'] )
						)
					)
					self.ft_show = film['show']
					self.ft_showid = cursor.lastrowid

			# check if the movie is there
			cursor.execute( """
				SELECT		`id`,
							`touched`
				FROM		`film`
				WHERE		( film.channelid = ? )
							AND
							( film.showid = ? )
							AND
							( film.url_video = ? )
			""", ( self.ft_channelid, self.ft_showid, film['url_video'] ) )
			r = cursor.fetchall()
			if len( r ) > 0:
				# film found
				filmid = r[0][0]
				if r[0][1] == 0:
					# update touched
					cursor.execute( 'UPDATE `film` SET `touched`=1 WHERE ( film.id=? )', ( filmid, ) )
			else:
				# insert the new film
				insmov = 1
				cursor.execute(
					"""
					INSERT INTO `film` (
						`dtCreated`,
						`channelid`,
						`showid`,
						`title`,
						`search`,
						`aired`,
						`duration`,
						`size`,
						`description`,
						`website`,
						`url_sub`,
						`url_video`,
						`url_video_sd`,
						`url_video_hd`
					)
					VALUES (
						?,
						?,
						?,
						?,
						?,
						?,
						?,
						?,
						?,
						?,
						?,
						?,
						?,
						?
					)
					""", (
						int( time.time() ),
						self.ft_channelid,
						self.ft_showid,
						film['title'],
						mvutils.make_search_string( film['title'] ),
						film['airedepoch'],
						mvutils.make_duration( film['duration'] ),
						film['size'],
						film['description'],
						film['website'],
						film['url_sub'],
						film['url_video'],
						film['url_video_sd'],
						film['url_video_hd']
					)
				)
				filmid = cursor.lastrowid
			if commit:
				self.conn.commit()
			cursor.close()
			return ( filmid, inschn, insshw, insmov )
		except sqlite3.DatabaseError as err:
			self._handle_database_corruption( err )
			raise DatabaseCorrupted( 'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format( err ) )

	def _handle_database_corruption( self, err ):
		self.logger.error( 'Database error during critical operation: {} - Database will be rebuilt from scratch.', err )
		self.notifier.ShowDatabaseError( err )
		self.Exit()
		self.Init( reset = True )

	def _handle_database_initialization( self ):
		self.conn.executescript( """
PRAGMA foreign_keys = false;

-- ----------------------------
--  Table structure for channel
-- ----------------------------
DROP TABLE IF EXISTS "channel";
CREATE TABLE "channel" (
	 "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
	 "touched" integer(1,0) NOT NULL DEFAULT 1,
	 "channel" TEXT(255,0) NOT NULL
);

-- ----------------------------
--  Table structure for film
-- ----------------------------
DROP TABLE IF EXISTS "film";
CREATE TABLE "film" (
	 "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
	 "touched" integer(1,0) NOT NULL DEFAULT 1,
	 "channelid" INTEGER(11,0) NOT NULL,
	 "showid" INTEGER(11,0) NOT NULL,
	 "title" TEXT(255,0) NOT NULL,
	 "search" TEXT(255,0) NOT NULL,
	 "aired" integer(11,0),
	 "duration" integer(11,0),
	 "size" integer(11,0),
	 "description" TEXT(2048,0),
	 "website" TEXT(384,0),
	 "url_sub" TEXT(384,0),
	 "url_video" TEXT(384,0),
	 "url_video_sd" TEXT(384,0),
	 "url_video_hd" TEXT(384,0),
	CONSTRAINT "FK_FilmShow" FOREIGN KEY ("showid") REFERENCES "show" ("id") ON DELETE CASCADE,
	CONSTRAINT "FK_FilmChannel" FOREIGN KEY ("channelid") REFERENCES "channel" ("id") ON DELETE CASCADE
);

-- ----------------------------
--  Table structure for show
-- ----------------------------
DROP TABLE IF EXISTS "show";
CREATE TABLE "show" (
	 "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
	 "touched" integer(1,0) NOT NULL DEFAULT 1,
	 "channelid" INTEGER(11,0) NOT NULL DEFAULT 0,
	 "show" TEXT(255,0) NOT NULL,
	 "search" TEXT(255,0) NOT NULL,
	CONSTRAINT "FK_ShowChannel" FOREIGN KEY ("channelid") REFERENCES "channel" ("id") ON DELETE CASCADE
);

-- ----------------------------
--  Table structure for status
-- ----------------------------
DROP TABLE IF EXISTS "status";
CREATE TABLE "status" (
	 "modified" integer(11,0),
	 "status" TEXT(32,0),
	 "lastupdate" integer(11,0),
	 "filmupdate" integer(11,0),
	 "fullupdate" integer(1,0),
	 "add_chn" integer(11,0),
	 "add_shw" integer(11,0),
	 "add_mov" integer(11,0),
	 "del_chm" integer(11,0),
	 "del_shw" integer(11,0),
	 "del_mov" integer(11,0),
	 "tot_chn" integer(11,0),
	 "tot_shw" integer(11,0),
	 "tot_mov" integer(11,0)
);

-- ----------------------------
--  Indexes structure for table film
-- ----------------------------
CREATE INDEX "dupecheck" ON film ("channelid", "showid", "url_video");
CREATE INDEX "index_1" ON film ("channelid", "title" COLLATE NOCASE);
CREATE INDEX "index_2" ON film ("showid", "title" COLLATE NOCASE);

-- ----------------------------
--  Indexes structure for table show
-- ----------------------------
CREATE INDEX "category" ON show ("category");
CREATE INDEX "search" ON show ("search");
CREATE INDEX "combined_1" ON show ("channelid", "search");
CREATE INDEX "combined_2" ON show ("channelid", "show");

PRAGMA foreign_keys = true;
		""" )
		self.UpdateStatus( 'IDLE' )

	def _file_remove( self, name ):
		if mvutils.file_exists( name ):
			try:
				os.remove( name )
				return True
			except OSError as err:
				self.logger.error( 'Failed to remove {}: error {}', name, err )
		return False

def UNIX_TIMESTAMP():
	return int( time.time() )

class GROUP_CONCAT:
	def __init__( self ):
		self.value = ''

	def step( self, value ):
		if value is not None:
			if self.value == '':
				self.value = '{0}'.format( value )
			else:
				self.value = '{0},{1}'.format( self.value, value )

	def finalize(self):
		return self.value
