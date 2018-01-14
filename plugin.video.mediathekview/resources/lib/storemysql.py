# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
import time
import mysql.connector

import resources.lib.mvutils as mvutils

from resources.lib.film import Film

# -- Classes ------------------------------------------------
class StoreMySQL( object ):
	def __init__( self, logger, notifier, settings ):
		self.conn		= None
		self.logger		= logger
		self.notifier	= notifier
		self.settings	= settings
		# useful query fragments
		self.sql_query_films	= "SELECT film.id,`title`,`show`,`channel`,`description`,TIME_TO_SEC(`duration`) AS `seconds`,`size`,`aired`,`url_sub`,`url_video`,`url_video_sd`,`url_video_hd` FROM `film` LEFT JOIN `show` ON show.id=film.showid LEFT JOIN `channel` ON channel.id=film.channelid"
		self.sql_query_filmcnt	= "SELECT COUNT(*) FROM `film` LEFT JOIN `show` ON show.id=film.showid LEFT JOIN `channel` ON channel.id=film.channelid"
		self.sql_cond_recent	= "( TIMESTAMPDIFF(HOUR,`aired`,CURRENT_TIMESTAMP()) < 24 )"
		self.sql_cond_nofuture	= " AND ( ( `aired` IS NULL ) OR ( TIMESTAMPDIFF(HOUR,`aired`,CURRENT_TIMESTAMP()) > 0 ) )" if settings.nofuture else ""
		self.sql_cond_minlength	= " AND ( ( `duration` IS NULL ) OR ( TIME_TO_SEC(`duration`) >= %d ) )" % settings.minlength if settings.minlength > 0 else ""

	def Init( self, reset = False ):
		self.logger.info( 'Using MySQL connector version {}', mysql.connector.__version__ )
		try:
			self.conn		= mysql.connector.connect(
				host		= self.settings.host,
				port		= self.settings.port,
				user		= self.settings.user,
				password	= self.settings.password
			)
			self.conn.database = self.settings.database
		except mysql.connector.Error as err:
			if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
				self.logger.info( '=== DATABASE {} DOES NOT EXIST. TRYING TO CREATE IT ===', self.settings.database )
				self._handle_database_initialization()
				return
			self.conn = None
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def Exit( self ):
		if self.conn is not None:
			self.conn.close()

	def Search( self, search, filmui ):
		self._Search_Condition( '( ( `title` LIKE "%%%s%%" ) OR ( `show` LIKE "%%%s%%" ) )' % ( search, search, ), filmui, True, True, self.settings.maxresults )

	def SearchFull( self, search, filmui ):
		self._Search_Condition( '( ( `title` LIKE "%%%s%%" ) OR ( `show` LIKE "%%%s%%" ) ) OR ( `description` LIKE "%%%s%%") )' % ( search, search, search ), filmui, True, True, self.settings.maxresults )

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
			condition = 'WHERE ( `channelid`=' + str( channelid ) + ' ) ' if channelid != '0' else ''
			self.logger.info( 'MySQL Query: {}',
				'SELECT LEFT(`search`,1) AS letter,COUNT(*) AS `count` FROM `show` ' +
				condition +
				'GROUP BY LEFT(search,1)'
			)
			cursor = self.conn.cursor()
			cursor.execute(
				'SELECT LEFT(`search`,1) AS letter,COUNT(*) AS `count` FROM `show` ' +
				condition +
				'GROUP BY LEFT(`search`,1)'
			)
			initialui.Begin( channelid )
			for ( initialui.initial, initialui.count ) in cursor:
				initialui.Add()
			initialui.End()
			cursor.close()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def GetShows( self, channelid, initial, showui ):
		if self.conn is None:
			return
		try:
			if channelid == '0' and self.settings.groupshows:
				query = 'SELECT GROUP_CONCAT(show.id),GROUP_CONCAT(`channelid`),`show`,GROUP_CONCAT(`channel`) FROM `show` LEFT JOIN `channel` ON channel.id=show.channelid WHERE ( `show` LIKE "%s%%" ) GROUP BY `show`' % initial
			elif channelid == '0':
				query = 'SELECT show.id,show.channelid,show.show,channel.channel FROM `show` LEFT JOIN channel ON channel.id=show.channelid WHERE ( `show` LIKE "%s%%" )' % initial
			else:
				query = 'SELECT show.id,show.channelid,show.show,channel.channel FROM `show` LEFT JOIN channel ON channel.id=show.channelid WHERE ( `channelid`=%s ) AND ( `show` LIKE "%s%%" )' % ( channelid, initial )
			self.logger.info( 'MySQL Query: {}', query )
			cursor = self.conn.cursor()
			cursor.execute( query )
			showui.Begin( channelid )
			for ( showui.id, showui.channelid, showui.show, showui.channel ) in cursor:
				showui.Add()
			showui.End()
			cursor.close()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def GetFilms( self, showid, filmui ):
		if self.conn is None:
			return
		if showid.find( ',' ) == -1:
			# only one channel id
			condition = '( `showid`=%s )' % showid
			showchannels = False
		else:
			# multiple channel ids
			condition = '( `showid` IN ( %s ) )' % showid
			showchannels = True
		self._Search_Condition( condition, filmui, False, showchannels, 10000 )

	def _Channels_Condition( self, condition, channelui):
		if self.conn is None:
			return
		try:
			if condition is None:
				query = 'SELECT `id`,`channel`,0 AS `count` FROM `channel`'
			else:
				query = 'SELECT channel.id AS `id`,`channel`,COUNT(*) AS `count` FROM `film` LEFT JOIN `channel` ON channel.id=film.channelid WHERE ' + condition + ' GROUP BY channel.id'
			self.logger.info( 'MySQL Query: {}', query )
			cursor = self.conn.cursor()
			cursor.execute( query )
			channelui.Begin()
			for ( channelui.id, channelui.channel, channelui.count ) in cursor:
				channelui.Add()
			channelui.End()
			cursor.close()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def _Search_Condition( self, condition, filmui, showshows, showchannels, maxresults ):
		if self.conn is None:
			return
		try:
			self.logger.info( 'MySQL Query: {}',
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
				' LIMIT {}'.format( maxresults + 1 ) if maxresults else ''
			)
			filmui.Begin( showshows, showchannels )
			for ( filmui.id, filmui.title, filmui.show, filmui.channel, filmui.description, filmui.seconds, filmui.size, filmui.aired, filmui.url_sub, filmui.url_video, filmui.url_video_sd, filmui.url_video_hd ) in cursor:
				filmui.Add( totalItems = results )
			filmui.End()
			cursor.close()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def RetrieveFilmInfo( self, filmid ):
		if self.conn is None:
			return None
		try:
			condition = '( film.id={} )'.format( filmid )
			self.logger.info( 'MySQL Query: {}',
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
		except mysql.connector.Error as err:
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
		try:
			cursor = self.conn.cursor()
			cursor.execute( 'SELECT * FROM `status` LIMIT 1' )
			r = cursor.fetchall()
			cursor.close()
			self.conn.commit()
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
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )
			status['status'] = "UNINIT"
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
		try:
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
						%s,
						%s,
						%s,
						%s,
						%s,
						%s,
						%s,
						%s,
						%s,
						%s,
						%s,
						%s,
						%s,
						%s
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
					SET		`modified`		= %s,
							`status`		= %s,
							`lastupdate`	= %s,
							`filmupdate`	= %s,
							`fullupdate`	= %s,
							`add_chn`		= %s,
							`add_shw`		= %s,
							`add_mov`		= %s,
							`del_chm`		= %s,
							`del_shw`		= %s,
							`del_mov`		= %s,
							`tot_chn`		= %s,
							`tot_shw`		= %s,
							`tot_mov`		= %s
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
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def SupportsUpdate( self ):
		return True

	def ftInit( self ):
		# prevent concurrent updating
		cursor = self.conn.cursor()
		cursor.execute(
			"""
			UPDATE	`status`
			SET		`modified`		= %s,
					`status`		= 'UPDATING'
			WHERE	( `status` != 'UPDATING' )
					OR
					( `modified` < %s )
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

	def ftUpdateStart( self, full ):
		param = ( 1, ) if full else ( 0, )
		try:
			cursor = self.conn.cursor()
			cursor.callproc( 'ftUpdateStart', param )
			for result in cursor.stored_results():
				for ( cnt_chn, cnt_shw, cnt_mov ) in result:
					cursor.close()
					self.conn.commit()
					return ( cnt_chn, cnt_shw, cnt_mov )
			# should never happen
			cursor.close()
			self.conn.commit()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )
		return ( 0, 0, 0, )

	def ftUpdateEnd( self, delete ):
		param = ( 1, ) if delete else ( 0, )
		try:
			cursor = self.conn.cursor()
			cursor.callproc( 'ftUpdateEnd', param )
			for result in cursor.stored_results():
				for ( del_chn, del_shw, del_mov, cnt_chn, cnt_shw, cnt_mov ) in result:
					cursor.close()
					self.conn.commit()
					return ( del_chn, del_shw, del_mov, cnt_chn, cnt_shw, cnt_mov )
			# should never happen
			cursor.close()
			self.conn.commit()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )
		return ( 0, 0, 0, 0, 0, 0, )

	def ftInsertFilm( self, film, commit ):
		newchn = False
		inschn = 0
		insshw = 0
		insmov = 0

		# handle channel
		if self.ft_channel != film['channel']:
			# process changed channel
			newchn = True
			self.ft_channel = film['channel']
			( self.ft_channelid, inschn ) = self._insert_channel( self.ft_channel )
			if self.ft_channelid == 0:
				self.logger.info( 'Undefined error adding channel "{}"', self.ft_channel )
				return ( 0, 0, 0, 0, )

		if newchn or self.ft_show != film['show']:
			# process changed show
			self.ft_show = film['show']
			( self.ft_showid, insshw ) = self._insert_show( self.ft_channelid, self.ft_show, mvutils.make_search_string( self.ft_show ) )
			if self.ft_showid == 0:
				self.logger.info( 'Undefined error adding show "{}"', self.ft_show )
				return ( 0, 0, 0, 0, )

		try:
			cursor = self.conn.cursor()
			cursor.callproc( 'ftInsertFilm', (
				self.ft_channelid,
				self.ft_showid,
				film["title"],
				mvutils.make_search_string( film['title'] ),
				film["aired"],
				film["duration"],
				film["size"],
				film["description"],
				film["website"],
				film["url_sub"],
				film["url_video"],
				film["url_video_sd"],
				film["url_video_hd"],
				film["airedepoch"],
			) )
			for result in cursor.stored_results():
				for ( filmid, insmov ) in result:
					cursor.close()
					if commit:
						self.conn.commit()
					return ( filmid, inschn, insshw, insmov )
				# should never happen
				cursor.close()
				if commit:
					self.conn.commit()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )
		return ( 0, 0, 0, 0, )

	def _insert_channel( self, channel ):
		try:
			cursor = self.conn.cursor()
			cursor.callproc( 'ftInsertChannel', ( channel, ) )
			for result in cursor.stored_results():
				for ( id, added ) in result:
					cursor.close()
					self.conn.commit()
					return ( id, added )
			# should never happen
			cursor.close()
			self.conn.commit()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )
		return ( 0, 0, )

	def _insert_show( self, channelid, show, search ):
		try:
			cursor = self.conn.cursor()
			cursor.callproc( 'ftInsertShow', ( channelid, show, search, ) )
			for result in cursor.stored_results():
				for ( idd, added ) in result:
					cursor.close()
					self.conn.commit()
					return ( idd, added )
			# should never happen
			cursor.close()
			self.conn.commit()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )
		return ( 0, 0, )

	def _handle_database_initialization( self ):
		cursor = None
		dbcreated = False
		try:
			cursor = self.conn.cursor()
			cursor.execute( 'CREATE DATABASE `{}` DEFAULT CHARACTER SET utf8'.format( self.settings.database ) )
			dbcreated = True
			self.conn.database = self.settings.database
			cursor.execute( 'SET FOREIGN_KEY_CHECKS=0' )
			self.conn.commit()
			cursor.execute(
				"""
CREATE TABLE `channel` (
	`id`			int(11)			NOT NULL AUTO_INCREMENT,
	`dtCreated`		timestamp		NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`touched`		smallint(1)		NOT NULL DEFAULT '1',
	`channel`		varchar(255)	NOT NULL,
	PRIMARY KEY						(`id`),
	KEY				`channel`		(`channel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
				"""
			)
			self.conn.commit()

			cursor.execute( """
CREATE TABLE `film` (
	`id`			int(11)			NOT NULL AUTO_INCREMENT,
	`dtCreated`		timestamp		NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`touched`		smallint(1)		NOT NULL DEFAULT '1',
	`channelid`		int(11)			NOT NULL,
	`showid`		int(11)			NOT NULL,
	`title`			varchar(255)	NOT NULL,
	`search`		varchar(255)	NOT NULL,
	`aired`			timestamp		NULL DEFAULT NULL,
	`duration`		time			DEFAULT NULL,
	`size`			int(11)			DEFAULT NULL,
	`description`	longtext,
	`website`		varchar(384)	DEFAULT NULL,
	`url_sub`		varchar(384)	DEFAULT NULL,
	`url_video`		varchar(384)	DEFAULT NULL,
	`url_video_sd`	varchar(384)	DEFAULT NULL,
	`url_video_hd`	varchar(384)	DEFAULT NULL,
	`airedepoch`	int(11)			DEFAULT NULL,
	PRIMARY KEY						(`id`),
	KEY				`index_1`		(`showid`,`title`),
	KEY				`index_2`		(`channelid`,`title`),
	KEY				`dupecheck`		(`channelid`,`showid`,`url_video`),
	CONSTRAINT `FK_FilmChannel` FOREIGN KEY (`channelid`) REFERENCES `channel` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION,
	CONSTRAINT `FK_FilmShow` FOREIGN KEY (`showid`) REFERENCES `show` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
			""" )
			self.conn.commit()

			cursor.execute( """
CREATE TABLE `show` (
	`id`			int(11)			NOT NULL AUTO_INCREMENT,
	`dtCreated`		timestamp		NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`touched`		smallint(1)		NOT NULL DEFAULT '1',
	`channelid`		int(11)			NOT NULL,
	`show`			varchar(255)	NOT NULL,
	`search`		varchar(255)	NOT NULL,
	PRIMARY KEY						(`id`),
	KEY				`show`			(`show`),
	KEY				`search`		(`search`),
	KEY				`combined_1`	(`channelid`,`search`),
	KEY				`combined_2`	(`channelid`,`show`),
	CONSTRAINT `FK_ShowChannel` FOREIGN KEY (`channelid`) REFERENCES `channel` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
			""" )
			self.conn.commit()

			cursor.execute( """
CREATE TABLE `status` (
	`modified`		int(11)			NOT NULL,
	`status`		varchar(255)	NOT NULL,
	`lastupdate`	int(11)			NOT NULL,
	`filmupdate`	int(11)			NOT NULL,
	`fullupdate`	int(1)			NOT NULL,
	`add_chn`		int(11)			NOT NULL,
	`add_shw`		int(11)			NOT NULL,
	`add_mov`		int(11)			NOT NULL,
	`del_chm`		int(11)			NOT NULL,
	`del_shw`		int(11)			NOT NULL,
	`del_mov`		int(11)			NOT NULL,
	`tot_chn`		int(11)			NOT NULL,
	`tot_shw`		int(11)			NOT NULL,
	`tot_mov`		int(11)			NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
			""" )
			self.conn.commit()

			cursor.execute( 'INSERT INTO `status` VALUES (0,"IDLE",0,0,0,0,0,0,0,0,0,0,0,0);' )
			self.conn.commit()

			cursor.execute( 'SET FOREIGN_KEY_CHECKS=1' )
			self.conn.commit()

			cursor.execute( """
CREATE PROCEDURE `ftInsertChannel`(
	_channel	VARCHAR(255)
)
BEGIN
	DECLARE	channelid_	INT(11);
	DECLARE	touched_	INT(1);
	DECLARE added_		INT(1) DEFAULT 0;

	SELECT	`id`,
			`touched`
	INTO	channelid_,
			touched_
	FROM	`channel`
	WHERE	( `channel`.`channel` = _channel );

	IF ( channelid_ IS NULL ) THEN
		INSERT INTO `channel` (
			`channel`
		)
		VALUES (
			_channel
		);
		SET channelid_	= LAST_INSERT_ID();
		SET added_ = 1;
	ELSE
		UPDATE	`channel`
		SET		`touched` = 1
		WHERE	( `id` = channelid_ );
	END IF;

	SELECT	channelid_	AS `id`,
			added_		AS `added`;
END
			""" )
			self.conn.commit()

			cursor.execute( """
CREATE PROCEDURE `ftInsertFilm`(
	_channelid		INT(11),
	_showid			INT(11),
	_title			VARCHAR(255),
	_search			VARCHAR(255),
	_aired			TIMESTAMP,
	_duration		TIME,
	_size			INT(11),
	_description	LONGTEXT,
	_website		VARCHAR(384),
	_url_sub		VARCHAR(384),
	_url_video		VARCHAR(384),
	_url_video_sd	VARCHAR(384),
	_url_video_hd	VARCHAR(384),
	_airedepoch		INT(11)
)
BEGIN
	DECLARE		id_			INT;
	DECLARE		added_		INT DEFAULT 0;

	SELECT		`id`
	INTO		id_
	FROM		`film` AS f
	WHERE		( f.channelid = _channelid )
				AND
				( f.showid = _showid )
				AND
				( f.url_video = _url_video );

	IF ( id_ IS NULL ) THEN
		INSERT INTO `film` (
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
			`url_video_hd`,
			`airedepoch`
		)
		VALUES (
			_channelid,
			_showid,
			_title,
			_search,
			IF(_aired = "1980-01-01 00:00:00", NULL, _aired),
			IF(_duration = "00:00:00", NULL, _duration),
			_size,
			_description,
			_website,
			_url_sub,
			_url_video,
			_url_video_sd,
			_url_video_hd,
			_airedepoch
		);
		SET id_			= LAST_INSERT_ID();
		SET added_		= 1;
	ELSE
		UPDATE	`film`
		SET		`touched` = 1
		WHERE	( `id` = id_ );
	END IF;
	SELECT	id_			AS `id`,
			added_		AS `added`;
END
			""" )
			self.conn.commit()

			cursor.execute( """
CREATE PROCEDURE `ftInsertShow`(
	_channelid	INT(11),
	_show		VARCHAR(255),
	_search		VARCHAR(255)
)
BEGIN
	DECLARE	showid_		INT(11);
	DECLARE	touched_	INT(1);
	DECLARE added_		INT(1) DEFAULT 0;

	SELECT	`id`,
			`touched`
	INTO	showid_,
			touched_
	FROM	`show`
	WHERE	( `show`.`channelid` = _channelid )
			AND
			( `show`.`show` = _show );

	IF ( showid_ IS NULL ) THEN
		INSERT INTO `show` (
			`channelid`,
			`show`,
			`search`
		)
		VALUES (
			_channelid,
			_show,
			_search
		);
		SET showid_	= LAST_INSERT_ID();
		SET added_ = 1;
	ELSE
		UPDATE	`show`
		SET		`touched` = 1
		WHERE	( `id` = showid_ );
	END IF;


	SELECT	showid_		AS `id`,
			added_		AS `added`;
END
			""" )
			self.conn.commit()

			cursor.execute( """
CREATE PROCEDURE `ftUpdateEnd`(
	_full	INT(1)
)
BEGIN
	DECLARE		del_chn_		INT DEFAULT 0;
	DECLARE		del_shw_		INT DEFAULT 0;
	DECLARE		del_mov_		INT DEFAULT 0;
	DECLARE		cnt_chn_		INT DEFAULT 0;
	DECLARE		cnt_shw_		INT DEFAULT 0;
	DECLARE		cnt_mov_		INT DEFAULT 0;

	IF ( _full = 1 ) THEN
		SELECT		COUNT(*)
		INTO		del_chn_
		FROM		`channel`
		WHERE		( `touched` = 0 );

		SELECT		COUNT(*)
		INTO		del_shw_
		FROM		`show`
		WHERE		( `touched` = 0 );

		SELECT		COUNT(*)
		INTO		del_mov_
		FROM		`film`
		WHERE		( `touched` = 0 );

		DELETE FROM	`show`
		WHERE		( `show`.`touched` = 0 )
					AND
					( ( SELECT SUM( `film`.`touched` ) FROM `film` WHERE `film`.`showid` = `show`.`id` ) = 0 );

		DELETE FROM	`film`
		WHERE		( `touched` = 0 );
	ELSE
		SET del_chn_ = 0;
		SET del_shw_ = 0;
		SET del_mov_ = 0;
	END IF;

	SELECT	del_chn_	AS	`del_chn`,
			del_shw_	AS	`del_shw`,
			del_mov_	AS	`del_mov`,
			cnt_chn_	AS	`cnt_chn`,
			cnt_shw_	AS	`cnt_shw`,
			cnt_mov_	AS	`cnt_mov`;
END
			""" )
			self.conn.commit()

			cursor.execute( """
CREATE PROCEDURE `ftUpdateStart`(
	_full	INT(1)
)
BEGIN
	DECLARE		cnt_chn_		INT DEFAULT 0;
	DECLARE		cnt_shw_		INT DEFAULT 0;
	DECLARE		cnt_mov_		INT DEFAULT 0;

	IF ( _full = 1 ) THEN
		UPDATE	`channel`
		SET		`touched` = 0;

		UPDATE	`show`
		SET		`touched` = 0;

		UPDATE	`film`
		SET		`touched` = 0;
	END IF;

	SELECT	COUNT(*)
	INTO	cnt_chn_
	FROM	`channel`;

	SELECT	COUNT(*)
	INTO	cnt_shw_
	FROM	`show`;

	SELECT	COUNT(*)
	INTO	cnt_mov_
	FROM	`film`;

	SELECT	cnt_chn_	AS `cnt_chn`,
			cnt_shw_	AS `cnt_shw`,
			cnt_mov_	AS `cnt_mov`;
END
			""" )
			self.conn.commit()

			cursor.close()
			self.logger.info( 'Database creation successfully completed' )
		except mysql.connector.Error as err:
			self.logger.error( '=== DATABASE CREATION ERROR: {} ===', err )
			self.notifier.ShowDatabaseError( err )
			try:
				if dbcreated:
					cursor.execute( 'DROP DATABASE `{}`'.format( self.settings.database ) )
					self.conn.commit()
				if cursor is not None:
					cursor.close()
					del cursor
				if self.conn is not None:
					self.conn.close()
					self.conn = None
			except mysql.connector.Error as err:
				# should never happen
				self.conn = None
