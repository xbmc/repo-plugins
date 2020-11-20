# -*- coding: utf-8 -*-
"""
The local SQlite database module

Copyright 2017-2019, Leo Moll
SPDX-License-Identifier: MIT
"""
# pylint: disable=too-many-lines,line-too-long

import os
import json
import time
import sqlite3
import hashlib

from contextlib import closing
from codecs import open

import resources.lib.mvutils as mvutils

from resources.lib.film import Film
from resources.lib.exceptions import DatabaseCorrupted

# -- Constants ----------------------------------------------
# DATABASE_URL = 'https://mvupdate.yeasoft.com/filmliste-v2.db.xz'
DATABASE_URL = 'https://liste.mediathekview.de/filmliste-v2.db.xz'
DATABASE_AKT = 'filmliste-v2.db.update'


class StoreSQLite(object):
    """
    The local SQlite database class

    Args:
        logger(KodiLogger): a valid `KodiLogger` instance

        notifier(Notifier): a valid `Notifier` instance

        settings(Settings): a valid `Settings` instance
    """

    def __init__(self, logger, notifier, settings):
        self.logger = logger
        self.notifier = notifier
        self.settings = settings
        # internals
        self.conn = None
        self.dbfile = os.path.join(self.settings.datapath, 'filmliste-v2.db')
        # useful query fragments
        self.sql_query_films = "SELECT film.id,title,show,channel,description,duration,size,datetime(aired, 'unixepoch', 'localtime'),url_sub,url_video,url_video_sd,url_video_hd FROM film LEFT JOIN show ON show.id=film.showid LEFT JOIN channel ON channel.id=film.channelid"
        self.sql_cond_recent = "( ( UNIX_TIMESTAMP() - {} ) <= {} )".format(
            "aired" if settings.recentmode == 0 else "film.dtCreated",
            settings.maxage
        )
        self.sql_cond_nofuture = " AND ( aired < UNIX_TIMESTAMP() )" if settings.nofuture else ""
        self.sql_cond_minlength = " AND ( duration >= %d )" % settings.minlength if settings.minlength > 0 else ""
        # update helper
        self.ft_channel = None
        self.ft_channelid = None
        self.ft_show = None
        self.ft_showid = None

    def init(self, reset=False, convert=False, failedCount = 0):
        """
        Startup of the database system

        Args:
            reset(bool, optional): if `True` the database
                will be cleaned up and recreated. Default
                is `False`

            convert(bool, optional): if `True` the database
                will be converted in case it is older than
                the supported version. If `False` a UI message
                will be displayed to the user informing that
                the database will be converted. Default is
                `False`
        """
        self.logger.info(
            'Using SQLite version {}, python library sqlite3 version {}',
            sqlite3.sqlite_version,
            sqlite3.version
        )
        if not mvutils.dir_exists(self.settings.datapath):
            os.mkdir(self.settings.datapath)

        # remove old versions
        mvutils.file_remove(os.path.join(
            self.settings.datapath,
            'filmliste-v1.db'
        ))

        if reset is True or not mvutils.file_exists(self.dbfile):
            self.logger.info(
                '===== RESET: Database will be deleted and regenerated =====')
            self.exit()
            mvutils.file_remove(self.dbfile)
            if self._handle_update_substitution():
                self.conn = sqlite3.connect(self.dbfile, timeout=60)
            else:
                self.conn = sqlite3.connect(self.dbfile, timeout=60)
                self._handle_database_initialization()
        else:
            try:
                if self._handle_update_substitution():
                    self._handle_not_update_to_date_dbfile()
                self.conn = sqlite3.connect(self.dbfile, timeout=60)
            except sqlite3.DatabaseError as err:
                self.logger.error(
                    'Error while opening database: {}. trying to fully reset the Database...', err)
                return self.init(reset=True, convert=convert)
        try:

            # 3x speed-up, check mode 'WAL'
            self.conn.execute('pragma journal_mode=off')
            # check if DB is ready or broken
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM `status` LIMIT 1')
            rs = cursor.fetchall()
            ##
            self.logger.info('Current DB Status Last modified {} ({})', time.ctime(rs[0][0]), rs[0][0])
            self.logger.info('Current DB Status Last lastupdate {} ({})', time.ctime(rs[0][2]), rs[0][2])
            self.logger.info('Current DB Status Last filmupdate {} ({})', time.ctime(rs[0][3]), rs[0][3])
            self.logger.info('Current DB Status Last fullupdate {}', rs[0][4])
            ##
            cursor.close()
        except sqlite3.DatabaseError as err:
            failedCount += 1
            if (failedCount > 3):
                self.logger.error('Failed to restore database, please uninstall plugin, delete user profile and reinstall')
                raise err
            self.logger.error('Error on first query: {}. trying to fully reset the Database...trying {} times', err, failedCount)
            return self.init(reset=True, convert=convert, failedCount=failedCount)
        # that is a bit dangerous :-) but faaaast
        self.conn.execute('pragma synchronous=off')
        self.conn.create_function('UNIX_TIMESTAMP', 0, get_unix_timestamp)
        self.conn.create_aggregate('GROUP_CONCAT', 1, GroupConcatClass)
        return True

    def exit(self):
        """ Shutdown of the database system """
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def search(self, search, filmui, extendedsearch=False):
        """
        Performs a search for films based on a search term
        and adds the results to the current UI directory

        Args:
            search(str): search term

            filmui(FilmUI): an instance of a film model view used
                for populating the directory

            extendedsearch(bool, optional): if `True` the search is
                performed also on film descriptions. Default is
                `False`
        """
        searchmask = '%' + search + '%'
        searchcond = '( ( title LIKE ? ) OR ( show LIKE ? ) OR ( description LIKE ? ) )' if extendedsearch is True else '( ( title LIKE ? ) OR ( show LIKE ? ) )'
        searchparm = (searchmask, searchmask, searchmask) if extendedsearch is True else (
            searchmask, searchmask, )
        return self._search_condition(
            condition=searchcond,
            params=searchparm,
            filmui=filmui,
            showshows=True,
            showchannels=True,
            maxresults=self.settings.maxresults,
            order='film.aired desc')

    def get_recents(self, channelid, filmui):
        """
        Populates the current UI directory with the recent
        film additions based on the configured interval.

        Args:
            channelid(id): database id of the selected channel.
                If 0, films from all channels are listed

            filmui(FilmUI): an instance of a film model view used
                for populating the directory
        """
        if channelid != '0':
            return self._search_condition(
                condition=self.sql_cond_recent + ' AND ( film.channelid=? )',
                params=(int(channelid), ),
                filmui=filmui,
                showshows=True,
                showchannels=False,
                maxresults=self.settings.maxresults,
                order='film.aired desc'
            )

        return self._search_condition(
            condition=self.sql_cond_recent,
            params=(),
            filmui=filmui,
            showshows=True,
            showchannels=False,
            maxresults=self.settings.maxresults,
            order='film.aired desc'
        )

    def get_live_streams(self, filmui):
        """
        Populates the current UI directory with the live
        streams

        Args:
            filmui(FilmUI): an instance of a film model view used
                for populating the directory
        """
        return self._search_condition(
            condition='( show.search="LIVESTREAM" )',
            params=(),
            filmui=filmui,
            showshows=False,
            showchannels=False,
            maxresults=0,
            limiting=False
        )

    def get_channels(self, channelui):
        """
        Populates the current UI directory with the list
        of available channels

        Args:
            channelui(ChannelUI): an instance of a channel model
                view used for populating the directory
        """
        self._search_channels_condition(None, channelui)

    def get_recent_channels(self, channelui):
        """
        Populates the current UI directory with the list
        of channels having recent film additions based on
        the configured interval.

        Args:
            channelui(ChannelUI): an instance of a channel model
                view used for populating the directory
        """
        self._search_channels_condition(self.sql_cond_recent, channelui)

    def get_initials(self, channelid, initialui):
        """
        Populates the current UI directory with a list
        of initial grouped entries.

        Args:
            channelid(id): database id of the selected channel.
                If 0, groups from all channels are listed

            initialui(InitialUI): an instance of a grouped entry
                model view used for populating the directory
        """
        if self.conn is None:
            return
        try:
            channelid = int(channelid)
            cursor = self.conn.cursor()
            if channelid != 0:
                self.logger.info(
                    'SQlite Query: SELECT SUBSTR(search,1,1),COUNT(*) FROM show WHERE ( channelid={} ) GROUP BY LEFT(search,1)',
                    channelid
                )
                cursor.execute("""
                    SELECT      SUBSTR(search,1,1),COUNT(*)
                    FROM        show
                    WHERE       ( channelid=? )
                    GROUP BY    SUBSTR(search,1,1)
                """, (channelid, ))
            else:
                self.logger.info(
                    'SQlite Query: SELECT SUBSTR(search,1,1),COUNT(*) FROM show GROUP BY LEFT(search,1)'
                )
                cursor.execute("""
                    SELECT      SUBSTR(search,1,1),COUNT(*)
                    FROM        show
                    GROUP BY    SUBSTR(search,1,1)
                """)
            initialui.begin(channelid)
            for (initialui.initial, initialui.count) in cursor:
                initialui.add()
            initialui.end()
            cursor.close()
        except sqlite3.Error as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)

    def get_shows(self, channelid, initial, showui, caching=True):
        """
        Populates the current UI directory with a list
        of shows limited to a specific channel or not.

        Args:
            channelid(id): database id of the selected channel.
                If 0, shows from all channels are listed

            initial(str): search term for shows

            showui(ShowUI): an instance of a show model view
                used for populating the directory
        """
        if self.conn is None:
            return

        if caching and self.settings.caching:
            channelid = int(channelid)
            if channelid == 0 and self.settings.groupshows:
                cache_condition = "SHOW:1:" + initial
            elif channelid == 0:
                cache_condition = "SHOW:2:" + initial
            elif initial:
                cache_condition = "SHOW:3:" + str(channelid) + ':' + initial
            else:
                cache_condition = "SHOW:3:" + str(channelid)
            cached_data = self._load_cache('get_shows', cache_condition)
            if cached_data is not None:
                showui.begin(channelid)
                for show_data in cached_data:
                    showui.set_from_dict(show_data)
                    showui.add()
                showui.end()
                return

        try:
            channelid = int(channelid)
            cached_data = []
            cursor = self.conn.cursor()
            if channelid == 0 and self.settings.groupshows:
                cursor.execute("""
                    SELECT      GROUP_CONCAT(show.id),
                                GROUP_CONCAT(channelid),
                                show,
                                GROUP_CONCAT(channel)
                    FROM        show
                    LEFT JOIN   channel
                        ON      ( channel.id = show.channelid )
                    WHERE       ( show LIKE ? )
                    GROUP BY    show
                """, (initial + '%', ))
            elif channelid == 0:
                cursor.execute("""
                    SELECT      show.id,
                                show.channelid,
                                show.show,
                                channel.channel
                    FROM        show
                    LEFT JOIN   channel
                        ON      ( channel.id = show.channelid )
                    WHERE       ( show LIKE ? )
                """, (initial + '%', ))
            elif initial:
                cursor.execute("""
                    SELECT      show.id,
                                show.channelid,
                                show.show,
                                channel.channel
                    FROM        show
                    LEFT JOIN   channel
                        ON      ( channel.id = show.channelid )
                    WHERE       (
                                    ( channelid=? )
                                    AND
                                    ( show LIKE ? )
                                )
                """, (channelid, initial + '%', ))
            else:
                cursor.execute("""
                    SELECT      show.id,
                                show.channelid,
                                show.show,
                                channel.channel
                    FROM        show
                    LEFT JOIN   channel
                        ON      ( channel.id = show.channelid )
                    WHERE       ( channelid=? )
                """, (channelid, ))
            showui.begin(channelid)
            for (showui.showid, showui.channelid, showui.show, showui.channel) in cursor:
                showui.add()
                if caching and self.settings.caching:
                    cached_data.append(showui.get_as_dict())
            showui.end()
            cursor.close()
            if caching and self.settings.caching:
                self._save_cache('get_shows', cache_condition, cached_data)
        except sqlite3.Error as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)

    def get_films(self, showid, filmui):
        """
        Populates the current UI directory with a list
        of films of a specific show.

        Args:
            showid(id): database id of the selected show.

            filmui(FilmUI): an instance of a film model view
                used for populating the directory
        """
        if self.conn is None:
            return
        if showid.find(',') == -1:
            # only one channel id
            return self._search_condition(
                condition='( showid=? )',
                params=(int(showid),),
                filmui=filmui,
                showshows=False,
                showchannels=False,
                maxresults=10000,
                order='film.aired desc'
            )

        # multiple channel ids
        return self._search_condition(
            condition='( showid IN ( {} ) )'.format(showid),
            params=(),
            filmui=filmui,
            showshows=False,
            showchannels=True,
            maxresults=10000,
            order='film.aired desc'
        )

    def _search_channels_condition(self, condition, channelui, caching=True):
        if self.conn is None:
            return
        if caching and self.settings.caching:
            cached_data = self._load_cache('search_channels', condition)
            if cached_data is not None:
                channelui.begin()
                for channel_data in cached_data:
                    channelui.set_from_dict(channel_data)
                    channelui.add()
                channelui.end()
                return

        try:
            if condition is None:
                query = 'SELECT id,channel,0 AS `count` FROM channel'
                qtail = ''
            else:
                query = 'SELECT channel.id AS `id`,channel,COUNT(*) AS `count` FROM film LEFT JOIN channel ON channel.id=film.channelid'
                qtail = ' WHERE ' + condition + ' GROUP BY channel'
            self.logger.info('SQLite Query: {}', query + qtail)
            cached_data = []
            cursor = self.conn.cursor()
            cursor.execute(query + qtail)
            channelui.begin()
            for (channelui.channelid, channelui.channel, channelui.count) in cursor:
                channelui.add()
                if caching and self.settings.caching:
                    cached_data.append(channelui.get_as_dict())
            channelui.end()
            cursor.close()
            if caching and self.settings.caching:
                self._save_cache('search_channels', condition, cached_data)
        except sqlite3.Error as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)

    def _search_condition(self, condition, params, filmui, showshows, showchannels, maxresults, limiting=True, caching=True, order=None):
        if self.conn is None:
            return 0

        maxresults = int(maxresults)
        if limiting:
            sql_cond_limit = self.sql_cond_nofuture + self.sql_cond_minlength
        else:
            sql_cond_limit = ''

        if caching and self.settings.caching:
            cache_condition = condition + sql_cond_limit + \
                (' LIMIT {}'.format(maxresults + 1)
                 if maxresults else '') + ':{}'.format(params)
            start = time.time()
            cached_data = self._load_cache('search_films', cache_condition)
            self.logger.info('LOAD_CACHE:{}', time.time() - start)
            if cached_data is not None:
                results = len(cached_data)
                filmui.begin(showshows, showchannels)
                start = time.time()
                for film_data in cached_data:
                    filmui.set_from_dict(film_data)
                    filmui.add(total_items=results)
                filmui.end()
                self.logger.info('FILL_KODI_LIST:{}', time.time() - start)
                return results

        try:
            cached_data = []
            order = (' ORDER BY ' + order) if order is not None else ''
            self.logger.info(
                'SQLite Query: {}',
                self.sql_query_films +
                ' WHERE ' +
                condition +
                sql_cond_limit +
                order
            )
            start = time.time()
            cursor = self.conn.cursor()
            cursor.execute(
                self.sql_query_films +
                ' WHERE ' +
                condition +
                sql_cond_limit +
                order +
                (' LIMIT {}'.format(maxresults + 1) if maxresults else ''),
                params
            )
            self.logger.info('QUERY_TIME:{}', time.time() - start)
            start = time.time()
            resultCount = 0
            for (filmui.filmid, filmui.title, filmui.show, filmui.channel, filmui.description, filmui.seconds, filmui.size, filmui.aired, filmui.url_sub, filmui.url_video, filmui.url_video_sd, filmui.url_video_hd) in cursor:
                resultCount += 1
                if maxresults and resultCount > maxresults:
                    break;
                cached_data.append(filmui.get_as_dict()) #write data to dict anyway because we want the total number of rows to be passed to add function
            ###
            results = len(cached_data)
            filmui.begin(showshows, showchannels)
            for film_data in cached_data:
                filmui.set_from_dict(film_data)
                filmui.add(total_items=results)
            filmui.end()
            if maxresults and resultCount > maxresults:
                self.notifier.show_limit_results(maxresults)        
            filmui.end()
            self.logger.info('FILL_KODI_LIST:{}', time.time() - start)
            cursor.close()
            if caching and self.settings.caching:
                self._save_cache('search_films', cache_condition, cached_data)
            return results
        except sqlite3.Error as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            return 0

    def retrieve_film_info(self, filmid):
        """
        Retrieves the spcified film information
        from the database

        Args:
            filmid(id): database id of the requested film
        """
        if self.conn is None:
            return None
        try:
            condition = '( film.id={} )'.format(filmid)
            self.logger.info(
                'SQLite Query: {}',
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
            for (film.filmid, film.title, film.show, film.channel, film.description, film.seconds, film.size, film.aired, film.url_sub, film.url_video, film.url_video_sd, film.url_video_hd) in cursor:
                cursor.close()
                return film
            cursor.close()
        except sqlite3.Error as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
        return None

    def get_status(self):
        """ Retrieves the database status information """
        status = {
            'modified': int(time.time()),
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
        cursor.execute('SELECT * FROM `status` LIMIT 1')
        result = cursor.fetchall()
        cursor.close()
        if not result:
            status['status'] = "NONE"
            return status
        status['modified'] = result[0][0]
        status['status'] = result[0][1]
        status['lastupdate'] = result[0][2]
        status['filmupdate'] = result[0][3]
        status['fullupdate'] = result[0][4]
        status['add_chn'] = result[0][5]
        status['add_shw'] = result[0][6]
        status['add_mov'] = result[0][7]
        status['del_chn'] = result[0][8]
        status['del_shw'] = result[0][9]
        status['del_mov'] = result[0][10]
        status['tot_chn'] = result[0][11]
        status['tot_shw'] = result[0][12]
        status['tot_mov'] = result[0][13]
        return status

    def update_status(self, status=None, lastupdate=None, filmupdate=None, fullupdate=None, add_chn=None, add_shw=None, add_mov=None, del_chn=None, del_shw=None, del_mov=None, tot_chn=None, tot_shw=None, tot_mov=None):
        """
        Updates the database status. Only supplied information
        will be updated.

        Args:
            status(status, optional): Status of the database. Can be:
                `NONE`, `UNINIT`, `IDLE`, `UPDATING`, `ABORTED`

            lastupdate(int, optional): Last update timestamp as UNIX epoch

            filmupdate(int, optional): Timestamp of the update list as UNIX epoch

            fullupdate(int, optional): Last full update timestamp as UNIX epoch

            add_chn(int, optional): Added channels during last update

            add_shw(int, optional): Added shows during last update

            add_mov(int, optional): Added films during last update

            del_chn(int, optional): Deleted channels during last update

            del_shw(int, optional): Deleted shows during last update

            del_mov(int, optional): Deleted films during last update

            tot_chn(int, optional): Total channels in database

            tot_shw(int, optional): Total shows in database

            tot_mov(int, optional): Total films in database
        """
        if self.conn is None:
            return
        new = self.get_status()
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
        new['modified'] = int(time.time())
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
                SET     `modified`      = ?,
                        `status`        = ?,
                        `lastupdate`    = ?,
                        `filmupdate`    = ?,
                        `fullupdate`    = ?,
                        `add_chn`       = ?,
                        `add_shw`       = ?,
                        `add_mov`       = ?,
                        `del_chm`       = ?,
                        `del_shw`       = ?,
                        `del_mov`       = ?,
                        `tot_chn`       = ?,
                        `tot_shw`       = ?,
                        `tot_mov`       = ?
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

    @staticmethod
    def supports_update():
        """
        Returns `True` if the selected database driver supports
        updating a local copy
        """
        return True

    def supports_native_update(self, full):
        """
        Returns `True` if the selected database driver supports
        updating a local copy with native functions and files

        Args:
            full(bool): if `True` a full update is requested
        """
        return full and self.settings.updnative

    def get_native_info(self, full):
        """
        Returns a tuple containing:
        - The URL of the requested update type dispatcher
        - the base name of the downloadable file

        Args:
            full(bool): if `True` a full update is requested
        """
        if full and self.settings.updnative:
            return (DATABASE_URL, DATABASE_AKT)
        return None

    def native_update(self, full):
        """
        Performs a native update of the database.

        Args:
            full(bool): if `True` a full update is started
        """
        if full:
            self.exit()
            self.init()
        return full

    def ft_init(self):
        """
        Initializes local database for updating
        """
        try:
            # prevent concurrent updating
            self.conn.commit()
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE  `status`
                SET     `modified`      = ?,
                        `status`        = 'UPDATING'
                WHERE   ( `status` != 'UPDATING' )
                        OR
                        ( `modified` < ? )
                """, (
                    int(time.time()),
                    int(time.time()) - 86400
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
            self._handle_database_corruption(err)
            raise DatabaseCorrupted(
                'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format(err))

    def ft_update_start(self, full):
        """
        Begins a local update procedure

        Args:
            full(bool): if `True` a full update is started
        """
        try:
            cursor = self.conn.cursor()
            if full:
                cursor.executescript("""
                    UPDATE  `channel`
                    SET     `touched` = 0;

                    UPDATE  `show`
                    SET     `touched` = 0;

                    UPDATE  `film`
                    SET     `touched` = 0;
                """)
            cursor.execute('SELECT COUNT(*) FROM `channel`')
            result1 = cursor.fetchone()
            cursor.execute('SELECT COUNT(*) FROM `show`')
            result2 = cursor.fetchone()
            cursor.execute('SELECT COUNT(*) FROM `film`')
            result3 = cursor.fetchone()
            cursor.close()
            self.conn.commit()
            return (result1[0], result2[0], result3[0], )
        except sqlite3.DatabaseError as err:
            self._handle_database_corruption(err)
            raise DatabaseCorrupted(
                'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format(err))

    def ft_update_end(self, delete):
        """
        Finishes a local update procedure

        Args:
            delete(bool): if `True` all records not updated
                will be deleted
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM `channel` WHERE ( touched = 0 )')
            (del_chn, ) = cursor.fetchone()
            cursor.execute('SELECT COUNT(*) FROM `show` WHERE ( touched = 0 )')
            (del_shw, ) = cursor.fetchone()
            cursor.execute('SELECT COUNT(*) FROM `film` WHERE ( touched = 0 )')
            (del_mov, ) = cursor.fetchone()
            if delete:
                cursor.execute(
                    'DELETE FROM `show` WHERE ( show.touched = 0 ) AND ( ( SELECT SUM( film.touched ) FROM `film` WHERE film.showid = show.id ) = 0 )')
                cursor.execute('DELETE FROM `film` WHERE ( touched = 0 )')
            else:
                del_chn = 0
                del_shw = 0
                del_mov = 0
            cursor.execute('SELECT COUNT(*) FROM `channel`')
            (cnt_chn, ) = cursor.fetchone()
            cursor.execute('SELECT COUNT(*) FROM `show`')
            (cnt_shw, ) = cursor.fetchone()
            cursor.execute('SELECT COUNT(*) FROM `film`')
            (cnt_mov, ) = cursor.fetchone()
            cursor.close()
            self.conn.commit()
            return (del_chn, del_shw, del_mov, cnt_chn, cnt_shw, cnt_mov, )
        except sqlite3.DatabaseError as err:
            self._handle_database_corruption(err)
            raise DatabaseCorrupted(
                'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format(err))

    def ft_insert_film(self, film, commit=True):
        """
        Inserts a film emtry into the database

        Args:
            film(Film): a film entry

            commit(bool, optional): the operation will be
                commited immediately. Default is `True`
        """
        try:
            cursor = self.conn.cursor()
            newchn = False
            inschn = 0
            insshw = 0
            insmov = 0
            channel = film['channel'][:64]
            show = film['show'][:128]
            title = film['title'][:128]

            # handle channel
            if self.ft_channel != channel:
                # process changed channel
                newchn = True
                cursor.execute(
                    'SELECT `id`,`touched` FROM `channel` WHERE channel.channel=?', (channel, ))
                result = cursor.fetchall()
                if result:
                    # get the channel data
                    self.ft_channel = channel
                    self.ft_channelid = result[0][0]
                    if result[0][1] == 0:
                        # updated touched
                        cursor.execute(
                            'UPDATE `channel` SET `touched`=1 WHERE ( channel.id=? )', (self.ft_channelid, ))
                else:
                    # insert the new channel
                    inschn = 1
                    cursor.execute('INSERT INTO `channel` ( `dtCreated`,`channel` ) VALUES ( ?,? )', (int(
                        time.time()), channel))
                    self.ft_channel = channel
                    self.ft_channelid = cursor.lastrowid

            # handle show
            if newchn or self.ft_show != show:
                # process changed show
                cursor.execute(
                    'SELECT `id`,`touched` FROM `show` WHERE ( show.channelid=? ) AND ( show.show=? )', (self.ft_channelid, show))
                result = cursor.fetchall()
                if result:
                    # get the show data
                    self.ft_show = show
                    self.ft_showid = result[0][0]
                    if result[0][1] == 0:
                        # updated touched
                        cursor.execute(
                            'UPDATE `show` SET `touched`=1 WHERE ( show.id=? )', (self.ft_showid, ))
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
                            int(time.time()),
                            self.ft_channelid, show,
                            mvutils.make_search_string(show)
                        )
                    )
                    self.ft_show = show
                    self.ft_showid = cursor.lastrowid

            # check if the movie is there
            checkString = "{}:{}:{}".format(self.ft_channelid, self.ft_showid, film['url_video'])
            idhash = hashlib.md5(checkString.encode('utf-8')).hexdigest()
            cursor.execute("""
                SELECT      `id`,
                            `touched`
                FROM        `film`
                WHERE       ( film.idhash = ? )
            """, (idhash, ))
            result = cursor.fetchall()
            if result:
                # film found
                filmid = result[0][0]
                if result[0][1] == 0:
                    # update touched
                    cursor.execute(
                        'UPDATE `film` SET `touched`=1 WHERE ( film.id=? )', (filmid, ))
            else:
                # insert the new film
                insmov = 1
                cursor.execute(
                    """
                    INSERT INTO `film` (
                        `idhash`,
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
                        ?,
                        ?
                    )
                    """, (
                        idhash,
                        int(time.time()),
                        self.ft_channelid,
                        self.ft_showid,
                        title,
                        mvutils.make_search_string(film['title']),
                        film['airedepoch'],
                        mvutils.make_duration(film['duration']),
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
            return (filmid, inschn, insshw, insmov)
        except sqlite3.DatabaseError as err:
            self._handle_database_corruption(err)
            raise DatabaseCorrupted(
                'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format(err))

    def _load_cache(self, reqtype, condition):
        filename = os.path.join(self.settings.datapath, reqtype + '.cache')
        dbLastUpdate = self.get_status()['modified']
        try:
            with closing(open(filename, encoding='utf-8')) as json_file:
                data = json.load(json_file)
                if isinstance(data, dict):
                    if data.get('type', '') != reqtype:
                        return None
                    if data.get('condition') != condition:
                        return None
                    if int(dbLastUpdate) != data.get('time', 0):
                        return None
                    data = data.get('data', [])
                    if isinstance(data, list):
                        return data
                    return None
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error(
                'Failed to load cache file {}: {}', filename, err)
        return None

    def _save_cache(self, reqtype, condition, data):
        if not isinstance(data, list):
            return False
        filename = os.path.join(self.settings.datapath, reqtype + '.cache')
        dbLastUpdate = self.get_status()['modified']
        cache = {
            "type": reqtype,
            "time": int(dbLastUpdate),
            "condition": condition,
            "data": data
        }
        try:
            with closing(open(filename, 'w', encoding='utf-8')) as json_file:
                json.dump(cache, json_file)
            return True
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error(
                'Failed to write cache file {}: {}', filename, err)
            return False

    def _handle_update_substitution(self):
        updfile = os.path.join(self.settings.datapath, DATABASE_AKT)
        sqlfile = os.path.join(self.settings.datapath, 'filmliste-v2.db')
        if mvutils.file_exists(updfile):
            self.logger.info('Native update file found. Updating database...')
            return mvutils.file_rename(updfile, sqlfile)
        return False

    def _handle_database_corruption(self, err):
        self.logger.error(
            'Database error during critical operation: {} - Database will be rebuilt from scratch.', err)
        self.notifier.show_database_error(err)
        self.exit()
        self.init(reset=True, convert=False)

    def _handle_not_update_to_date_dbfile(self):
        ###
        try:
            if self.conn is None:
                self.conn = sqlite3.connect(self.dbfile, timeout=60)
            cursor = self.conn.cursor()
            cursor.execute('SELECT modified FROM `status` LIMIT 1')
            rs = cursor.fetchall()
            modified = rs[0][0]
            current_time = int(time.time())
            target_time = modified + 8 * 60 * 60;
            if (target_time < current_time):
                self.logger.info("Outdated DB after full refresh! DB modified time is {} ({}) which is less than allowed {} ({})",time.ctime(modified),modified,time.ctime(target_time),target_time)
                cursor = self.conn.cursor()
                cursor.execute('UPDATE status SET modified = ?,lastupdate = ?, filmupdate = ?', (int(time.time()),int(time.time()),int(time.time())))
                cursor.close()
                self.conn.commit()
                return True
            self.conn.close()
            self.conn = None
        except sqlite3.DatabaseError as err:
            self.logger.error('HUST: {}', err)     
        return False

    def _handle_database_initialization(self):
        self.conn.executescript("""
PRAGMA foreign_keys = false;

-- ----------------------------
--  Table structure for channel
-- ----------------------------
DROP TABLE IF EXISTS "channel";
CREATE TABLE "channel" (
     "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
     "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
     "touched" integer(1,0) NOT NULL DEFAULT 1,
     "channel" TEXT(64,0) NOT NULL
);

-- ----------------------------
--  Table structure for film
-- ----------------------------
DROP TABLE IF EXISTS "film";
CREATE TABLE "film" (
     "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
     "idhash" TEXT(32,0) NOT NULL,
     "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
     "touched" integer(1,0) NOT NULL DEFAULT 1,
     "channelid" INTEGER(11,0) NOT NULL,
     "showid" INTEGER(11,0) NOT NULL,
     "title" TEXT(128,0) NOT NULL,
     "search" TEXT(128,0) NOT NULL,
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
     "show" TEXT(128,0) NOT NULL,
     "search" TEXT(128,0) NOT NULL,
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
CREATE INDEX "dupecheck" ON film ("idhash");
CREATE INDEX "index_1" ON film ("channelid", "title" COLLATE NOCASE);
CREATE INDEX "index_2" ON film ("showid", "title" COLLATE NOCASE);

-- ----------------------------
--  Indexes structure for table show
-- ----------------------------
CREATE INDEX "search" ON show ("search");
CREATE INDEX "combined_1" ON show ("channelid", "search");
CREATE INDEX "combined_2" ON show ("channelid", "show");

PRAGMA foreign_keys = true;
        """)
        self.update_status('IDLE')


class GroupConcatClass(object):
    """ Aggregate class for SQLite """

    def __init__(self):
        self.value = ''

    def step(self, value):
        """
        Accumulates the values to aggregate

        Args:
            value(any): Value to aggregate
        """
        if value is not None:
            if self.value == '':
                self.value = '{0}'.format(value)
            else:
                self.value = '{0},{1}'.format(self.value, value)

    def finalize(self):
        """ Returns the aggregated value """
        return self.value


def get_unix_timestamp():
    """ User defined function for SQLite """
    return int(time.time())
