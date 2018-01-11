# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
import string, time
import mysql.connector

from classes.film import Film
from classes.exceptions import DatabaseCorrupted

# -- Classes ------------------------------------------------
class StoreMySQL( object ):
	def __init__( self, logger, notifier, settings ):
		self.conn		= None
		self.logger		= logger
		self.notifier	= notifier
		self.settings	= settings
		# useful query fragments
		self.sql_query_films	= "SELECT film.id,`title`,`show`,`channel`,`description`,TIME_TO_SEC(`duration`) AS `seconds`,`size`,`aired`,`url_sub`,`url_video`,`url_video_sd`,`url_video_hd` FROM `film` LEFT JOIN `show` ON show.id=film.showid LEFT JOIN `channel` ON channel.id=film.channelid"
		self.sql_cond_recent	= "( TIMESTAMPDIFF(HOUR,`aired`,CURRENT_TIMESTAMP()) < 24 )"
		self.sql_cond_nofuture	= " AND ( ( `aired` IS NULL ) OR ( TIMESTAMPDIFF(HOUR,`aired`,CURRENT_TIMESTAMP()) > 0 ) )" if settings.nofuture else ""
		self.sql_cond_minlength	= " AND ( ( `duration` IS NULL ) OR ( TIME_TO_SEC(`duration`) >= %d ) )" % settings.minlength if settings.minlength > 0 else ""

	def Init( self, reset = False ):
		self.logger.info( 'Using MySQL connector version {}', mysql.connector.__version__ )
		try:
			self.conn		= mysql.connector.connect(
				host		= self.settings.host,
				user		= self.settings.user,
				password	= self.settings.password,
				database	= self.settings.database
			)
		except mysql.connector.Error as err:
			self.conn		= None
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def Exit( self ):
		if self.conn is not None:
			self.conn.close()

	def Search( self, search, filmui ):
		self._Search_Condition( '( ( `title` LIKE "%%%s%%" ) OR ( `show` LIKE "%%%s%%" ) )' % ( search, search, ), filmui, True, True )

	def SearchFull( self, search, filmui ):
		self._Search_Condition( '( ( `title` LIKE "%%%s%%" ) OR ( `show` LIKE "%%%s%%" ) ) OR ( `description` LIKE "%%%s%%") )' % ( search, search, search ), filmui, True, True )

	def GetRecents( self, channelid, filmui ):
		sql_cond_channel = ' AND ( film.channelid=' + str( channelid ) + ' ) ' if channelid != '0' else ''
		self._Search_Condition( self.sql_cond_recent + sql_cond_channel, filmui, True, False )

	def GetLiveStreams( self, filmui ):
		self._Search_Condition( '( show.search="LIVESTREAM" )', filmui, False, False )

	def GetChannels( self, channelui ):
		self._Channels_Condition( None, channelui )

	def GetRecentChannels( self, channelui ):
		self._Channels_Condition( self.sql_cond_recent, channelui )

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
			condition = '( `showid=`%s )' % showid
			showchannels = False
		else:
			# multiple channel ids
			condition = '( `showid` IN ( %s ) )' % showid
			showchannels = True
		self._Search_Condition( condition, filmui, False, showchannels )

	def _Search_Condition( self, condition, filmui, showshows, showchannels ):
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
				self.sql_query_films +
				' WHERE ' +
				condition +
				self.sql_cond_nofuture +
				self.sql_cond_minlength
			)
			filmui.Begin( showshows, showchannels )
			for ( filmui.id, filmui.title, filmui.show, filmui.channel, filmui.description, filmui.seconds, filmui.size, filmui.aired, filmui.url_sub, filmui.url_video, filmui.url_video_sd, filmui.url_video_hd ) in cursor:
				filmui.Add()
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
			( self.ft_showid, insshw ) = self._insert_show( self.ft_channelid, self.ft_show, self._make_search( self.ft_show ) )
			if self.ft_showid == 0:
				self.logger.info( 'Undefined error adding show "{}"', self.ft_show )
				return ( 0, 0, 0, 0, )

		try:
			cursor = self.conn.cursor()
			cursor.callproc( 'ftInsertFilm', (
				self.ft_channelid,
				self.ft_showid,
				film["title"],
				self._make_search( film['title'] ),
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

	def _make_search( self, val ):
		cset = string.letters + string.digits + ' _-#'
		search = ''.join( [ c for c in val if c in cset ] )
		return search.upper().strip()
