# -*- coding: utf-8 -*-
"""
The MySQL database support module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
"""
# pylint: disable=too-many-lines,line-too-long

import time
import mysql.connector

import resources.lib.mvutils as mvutils

from resources.lib.film import Film


class StoreMySQL(object):
    """
    The local MySQL database class

    Args:
        logger(KodiLogger): a valid `KodiLogger` instance

        notifier(Notifier): a valid `Notifier` instance

        settings(Settings): a valid `Settings` instance
    """

    def __init__(self, logger, notifier, settings):
        self.conn = None
        self.logger = logger
        self.notifier = notifier
        self.settings = settings
        # updater state variables
        self.ft_channel = None
        self.ft_channelid = None
        self.ft_show = None
        self.ft_showid = None
        # useful query fragments
        # pylint: disable=line-too-long
        self.sql_query_films = "SELECT film.id,`title`,`show`,`channel`,`description`,TIME_TO_SEC(`duration`) AS `seconds`,`size`,`aired`,`url_sub`,`url_video`,`url_video_sd`,`url_video_hd` FROM `film` LEFT JOIN `show` ON show.id=film.showid LEFT JOIN `channel` ON channel.id=film.channelid"
        self.sql_query_filmcnt = "SELECT COUNT(*) FROM `film` LEFT JOIN `show` ON show.id=film.showid LEFT JOIN `channel` ON channel.id=film.channelid"
        self.sql_cond_recent = "( TIMESTAMPDIFF(SECOND,{},CURRENT_TIMESTAMP()) <= {} )".format(
            "aired" if settings.recentmode == 0 else "film.dtCreated", settings.maxage)
        self.sql_cond_nofuture = " AND ( `aired` < CURRENT_DATE() )" if settings.nofuture else ""
        self.sql_cond_minlength = " AND ( TIME_TO_SEC(`duration`) >= %d )" % settings.minlength if settings.minlength > 0 else ""

        self.films_to_insert = []
        self.sql_films_prepareTT = """
CREATE TEMPORARY TABLE IF NOT EXISTS `t_film`(
  `channelid`      INT(11),
  `showid`         INT(11),
  `title`          VARCHAR(128),
  `search`         VARCHAR(128),
  `aired`          DATETIME,
  `duration`       TIME,
  `size`           INT(11),
  `description`    LONGTEXT,
  `website`        VARCHAR(384),
  `url_sub`        VARCHAR(384),
  `url_video`      VARCHAR(384),
  `url_video_sd`   VARCHAR(384),
  `url_video_hd`   VARCHAR(384),
  `airedepoch`     INT(11),
  `_idhash`        CHAR(32)
);

TRUNCATE TABLE `t_film`;
"""
        self.sql_films_insertTT = """
INSERT INTO `t_film` (
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
  ) VALUES (
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
    %s)
"""
        self.sql_films_process = """
UPDATE `t_film`
  SET `_idhash` = MD5(CONCAT(channelid, ':', showid, ':', url_video));

UPDATE `t_film`
  INNER JOIN `film` ON
    `t_film`.`_idhash` = `film`.`idhash`
  SET `film`.`touched` = 1;

INSERT INTO `film` (
    `idhash`,
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
  SELECT
      `t_film`.`_idhash`,
      `t_film`.`channelid`,
      `t_film`.`showid`,
      `t_film`.`title`,
      `t_film`.`search`,
      `t_film`.`aired`,
      `t_film`.`duration`,
      `t_film`.`size`,
      `t_film`.`description`,
      `t_film`.`website`,
      `t_film`.`url_sub`,
      `t_film`.`url_video`,
      `t_film`.`url_video_sd`,
      `t_film`.`url_video_hd`,
      `t_film`.`airedepoch`
    FROM `t_film`
    LEFT JOIN `film` ON
      `t_film`.`_idhash` = `film`.`idhash`
	WHERE `film`.`idhash` IS NULL;

DROP TEMPORARY TABLE IF EXISTS `t_film`;
"""

    def init(self, reset=False, convert=False):
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
        self.logger.info('Using MySQL connector version {}',
                         mysql.connector.__version__)
        if reset:
            self.logger.warn('Reset not supported')
        try:
            # TODO Kodi 19 - we can update to mysql connector which supports auth_plugin parameter
            connectargs = {
                'host': self.settings.host,
                'port': self.settings.port,
                'user': self.settings.user,
                'password': self.settings.password
            }
            if mysql.connector.__version_info__ > (1, 2):
                connectargs['auth_plugin'] = 'mysql_native_password'
            else:
                self.logger.debug('Not using auth_plugin parameter')
            if mysql.connector.__version_info__ > (2, 1) and mysql.connector.HAVE_CEXT:
                connectargs['use_pure'] = True
                self.logger.debug('Forcefully disabling C extension')
            self.conn = mysql.connector.connect(**connectargs)
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT VERSION()')
                (version, ) = cursor.fetchone()
                self.logger.info(
                    'Connected to server {} running {}', self.settings.host, version)
            # pylint: disable=broad-except
            except Exception:
                self.logger.info('Connected to server {}', self.settings.host)
            self.conn.database = self.settings.database
            ## check tables
            cursor.execute('SELECT * FROM status')
            cursor.fetchone()
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.logger.info(
                    '=== DATABASE {} DOES NOT EXIST. TRYING TO CREATE IT ===', self.settings.database)
                return self._handle_database_initialization()
            if err.errno == mysql.connector.errorcode.ER_NO_SUCH_TABLE:
                self.logger.info(
                    '=== TABLE DOES NOT EXIST. TRYING TO CREATE IT ===')
                return self._handle_database_initialization()
            self.conn = None
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
            return False

        # handle schema versioning
        return self._handle_database_update(convert)

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
        searchcond = '( ( `title` LIKE %s ) OR ( `show` LIKE %s ) OR ( `description` LIKE %s ) )' if extendedsearch is True else '( ( `title` LIKE %s ) OR ( `show` LIKE %s ) )'
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
                condition=self.sql_cond_recent + ' AND ( film.channelid=%s )',
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
                    'MySQL Query: SELECT LEFT(`search`,1) AS letter,COUNT(*) AS `count` FROM `show` WHERE ( `channelid`={} ) GROUP BY LEFT(search,1)',
                    channelid
                )
                cursor.execute("""
                    SELECT      LEFT(`search`,1)    AS `letter`,
                                COUNT(*)            AS `count`
                    FROM        `show`
                    WHERE       ( `channelid`=%s )
                    GROUP BY    LEFT(`search`,1)
                """, (channelid, ))
            else:
                self.logger.info(
                    'MySQL Query: SELECT LEFT(`search`,1) AS letter,COUNT(*) AS `count` FROM `show` GROUP BY LEFT(search,1)'
                )
                cursor.execute("""
                    SELECT      LEFT(`search`,1)    AS `letter`,
                                COUNT(*)            AS `count`
                    FROM        `show`
                    GROUP BY    LEFT(`search`,1)
                """)
            initialui.begin(channelid)
            for (initialui.initial, initialui.count) in cursor:
                initialui.add()
            initialui.end()
            cursor.close()
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)

    def get_shows(self, channelid, initial, showui):
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
        try:
            channelid = int(channelid)
            cursor = self.conn.cursor()
            if channelid == 0 and self.settings.groupshows:
                cursor.execute("""
                    SELECT      GROUP_CONCAT(show.id),
                                GROUP_CONCAT(`channelid`),
                                `show`,
                                GROUP_CONCAT(`channel`)
                    FROM        `show`
                    LEFT JOIN   `channel`
                        ON      ( channel.id = show.channelid )
                    WHERE       ( `show` LIKE %s )
                    GROUP BY    `show`
                """, (initial + '%', ))
            elif channelid == 0:
                cursor.execute("""
                    SELECT      show.id,
                                show.channelid,
                                show.show,
                                channel.channel
                    FROM        `show`
                    LEFT JOIN   `channel`
                        ON      ( channel.id = show.channelid )
                    WHERE       ( `show` LIKE %s )
                """, (initial + '%', ))
            elif initial:
                cursor.execute("""
                    SELECT      show.id,
                                show.channelid,
                                show.show,
                                channel.channel
                    FROM        `show`
                    LEFT JOIN   `channel`
                        ON      ( channel.id = show.channelid )
                    WHERE       (
                                    ( `channelid` = %s )
                                    AND
                                    ( `show` LIKE %s )
                                )
                """, (channelid, initial + '%', ))
            else:
                cursor.execute("""
                    SELECT      show.id,
                                show.channelid,
                                show.show,
                                channel.channel
                    FROM        `show`
                    LEFT JOIN   `channel`
                        ON      ( channel.id = show.channelid )
                    WHERE       ( `channelid` = %s )
                """, (channelid, ))
            showui.begin(channelid)
            for (showui.showid, showui.channelid, showui.show, showui.channel) in cursor:
                showui.add()
            showui.end()
            cursor.close()
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
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
                condition='( `showid` = %s )',
                params=(int(showid), ),
                filmui=filmui,
                showshows=False,
                showchannels=False,
                maxresults=self.settings.maxresults,
                order='film.aired desc'
            )
        # multiple channel ids
        return self._search_condition(
            condition='( `showid` IN ( {} ) )'.format(showid),
            params=(),
            filmui=filmui,
            showshows=False,
            showchannels=True,
            maxresults=self.settings.maxresults,
            order='film.aired desc'
        )

    def _search_channels_condition(self, condition, channelui):
        if self.conn is None:
            return
        try:
            if condition is None:
                query = 'SELECT `id`,`channel`,0 AS `count` FROM `channel`'
                qtail = ''
            else:
                query = 'SELECT channel.id AS `id`,`channel`,COUNT(*) AS `count` FROM `film` LEFT JOIN `channel` ON channel.id=film.channelid'
                qtail = ' WHERE ' + condition + self.sql_cond_nofuture + \
                    self.sql_cond_minlength + ' GROUP BY channel.id'
            self.logger.info('MySQL Query: {}', query + qtail)

            cursor = self.conn.cursor()
            cursor.execute(query + qtail)
            channelui.begin()
            for (channelui.channelid, channelui.channel, channelui.count) in cursor:
                channelui.add()
            channelui.end()
            cursor.close()
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)

    def _search_condition(self, condition, params, filmui, showshows, showchannels, maxresults, limiting=True, order=''):
        if self.conn is None:
            return 0
        try:
            if len(order) > 0:
                order = ' ORDER BY ' + order
            if limiting:
                sql_cond_limit = self.sql_cond_nofuture + self.sql_cond_minlength
            else:
                sql_cond_limit = ''
            self.logger.info(
                'MySQL Query: {}',
                self.sql_query_films +
                ' WHERE ' +
                condition +
                sql_cond_limit +
                order
            )
            cursor = self.conn.cursor()
            cursor.execute(
                self.sql_query_filmcnt +
                ' WHERE ' +
                condition +
                sql_cond_limit +
                order +
                (' LIMIT {}'.format(maxresults + 1) if maxresults else ''),
                params
            )
            (results, ) = cursor.fetchone()
            if maxresults and results > maxresults:
                self.notifier.show_limit_results(maxresults)
            cursor.execute(
                self.sql_query_films +
                ' WHERE ' +
                condition +
                sql_cond_limit +
                order +
                (' LIMIT {}'.format(maxresults + 1) if maxresults else ''),
                params
            )
            filmui.begin(showshows, showchannels)
            for (filmui.filmid, filmui.title, filmui.show, filmui.channel, filmui.description, filmui.seconds, filmui.size, filmui.aired, filmui.url_sub, filmui.url_video, filmui.url_video_sd, filmui.url_video_hd) in cursor:
                filmui.add(total_items=results)
            filmui.end()
            cursor.close()
            return results
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
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
                'MySQL Query: {}',
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
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
        return None

    def get_status(self, reconnect=True):
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
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM `status` LIMIT 1')
            result = cursor.fetchall()
            cursor.close()
            self.conn.commit()
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
        except mysql.connector.Error as err:
            if err.errno == -1:
                # connection lost. Retry:
                if reconnect:
                    self.logger.warn(
                        'Database connection lost. Trying to reconnect...')
                    if self.reinit():
                        self.logger.info('Reconnection successful')
                        return self.get_status(False)
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
            status['status'] = "UNINIT"
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
                    SET     `modified`      = %s,
                            `status`        = %s,
                            `lastupdate`    = %s,
                            `filmupdate`    = %s,
                            `fullupdate`    = %s,
                            `add_chn`       = %s,
                            `add_shw`       = %s,
                            `add_mov`       = %s,
                            `del_chm`       = %s,
                            `del_shw`       = %s,
                            `del_mov`       = %s,
                            `tot_chn`       = %s,
                            `tot_shw`       = %s,
                            `tot_mov`       = %s
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
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)

    @staticmethod
    def supports_update():
        """
        Returns `True` if the selected database driver supports
        updating a local copy
        """
        return True

    # pylint: disable=unused-argument
    @staticmethod
    def supports_native_update(full):
        """
        Returns `True` if the selected database driver supports
        updating a local copy with native functions and files

        Args:
            full(bool): if `True` a full update is requested
        """
        return False

    @staticmethod
    def get_native_info(full):
        """
        Returns a tuple containing:
        - The URL of the requested update type dispatcher
        - the base name of the downloadable file

        Args:
            full(bool): if `True` a full update is requested
        """
        return None

    @staticmethod
    def native_update(full):
        """
        Performs a native update of the database.

        Args:
            full(bool): if `True` a full update is started
        """
        return False

    def reinit(self):
        """ Reinitializes the database connection """
        self.exit()
        return self.init(False, False)

    def ft_init(self):
        """
        Initializes local database for updating
        """
        # prevent concurrent updating
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE  `status`
            SET     `modified`      = %s,
                    `status`        = 'UPDATING'
            WHERE   ( `status` != 'UPDATING' )
                    OR
                    ( `modified` < %s )
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

    def ft_update_start(self, full):
        """
        Begins a local update procedure

        Args:
            full(bool): if `True` a full update is started
        """
        param = (1, ) if full else (0, )
        try:
            cursor = self.conn.cursor()
            cursor.callproc('ftUpdateStart', param)
            for result in cursor.stored_results():
                for (cnt_chn, cnt_shw, cnt_mov) in result:
                    cursor.close()
                    self.conn.commit()
                    return (cnt_chn, cnt_shw, cnt_mov)
            # should never happen
            cursor.close()
            self.conn.commit()
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
        return (0, 0, 0, )

    def ft_update_end(self, delete):
        """
        Finishes a local update procedure

        Args:
            delete(bool): if `True` all records not updated
                will be deleted
        """
        # Close the batch update
        if (len(self.films_to_insert) > 0):
            self.ft_insert_film(None, True)

        param = (1, ) if delete else (0, )
        try:
            cursor = self.conn.cursor()
            cursor.callproc('ftUpdateEnd', param)
            for result in cursor.stored_results():
                for (del_chn, del_shw, del_mov, cnt_chn, cnt_shw, cnt_mov) in result:
                    cursor.close()
                    self.conn.commit()
                    return (del_chn, del_shw, del_mov, cnt_chn, cnt_shw, cnt_mov)
            # should never happen
            cursor.close()
            self.conn.commit()
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
        return (0, 0, 0, 0, 0, 0, )

    def ft_insert_film(self, film, commit=True):
        """
        Inserts a film emtry into the database

        Args:
            film(Film): a film entry or a tuple of values for insert

            commit(bool, optional): If true, collected content in
            self.sql_films_to_insert is bulk-inserted into database
            and processed there.
            Default is `True`
        """
        newchn = False
        inschn = 0
        insshw = 0
        insmov = 0

        if (film is not None):
            if isinstance(film, tuple):
                self.films_to_insert.append(film)
            else:
                channel = film['channel'][:64]
                show = film['show'][:128]
                title = film['title'][:128]
    
                # handle channel
                if self.ft_channel != channel:
                    # process changed channel
                    newchn = True
                    self.ft_channel = channel
                    (self.ft_channelid, inschn) = self._insert_channel(self.ft_channel)
                    if self.ft_channelid == 0:
                        self.logger.info(
                            'Undefined error adding channel "{}"', self.ft_channel)
                        return (0, 0, 0, 0, )
    
                if newchn or self.ft_show != show:
                    # process changed show
                    self.ft_show = show
                    (self.ft_showid, insshw) = self._insert_show(self.ft_channelid,
                                                                 self.ft_show, mvutils.make_search_string(self.ft_show))
                    if self.ft_showid == 0:
                        self.logger.info(
                            'Undefined error adding show "{}"', self.ft_show)
                        return (0, 0, 0, 0, )
    
                self.films_to_insert.append((
                        self.ft_channelid,
                        self.ft_showid,
                        title,
                        mvutils.make_search_string(title),
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
                      ))

        if commit:
            cursor = self.conn.cursor()
            try:
                for result in cursor.execute(self.sql_films_prepareTT, multi=True): pass

                if len(self.films_to_insert) == 1:
                    # For single row inserts use execute instead of executemany
                    # in hope of failing single row inserts give us more detailed
                    # feedback about a violating value.
                    cursor.execute(self.sql_films_insertTT, self.films_to_insert[0])
                else :
                    cursor.executemany(self.sql_films_insertTT, self.films_to_insert)

                for result in cursor.execute(self.sql_films_process, multi=True):
                    if not result.with_rows:
                        if result.statement.startswith("INSERT INTO `film`"):
                            insmov = result.rowcount

                self.films_to_insert = []
            except mysql.connector.Error as err:
                self.logger.error('Database error: {}, {}', err.errno, err)
                # pop up databse error only on single row inserts
                if len(self.films_to_insert) == 1:
                    self.notifier.show_database_error(err)
                else:
                    # If in multirow mode, step down to single row mode by
                    # feeding content of self.films_to_insert row by row
                    # to ft_insert_film to isolate the failing dataset.

                    # At first of all clone self.films_to_insert into _rows
                    # because it has to be emptyed for this process.
                    _rows = []
                    for row in self.films_to_insert:
                        insmov += _rows.append(row)[3]

                    self.films_to_insert = []

                    for row in _rows:
                        self.ft_insert_film(row, True)

                self.films_to_insert = []

            cursor.close()

        return (0, inschn, insshw, insmov)

    def _insert_channel(self, channel):
        try:
            cursor = self.conn.cursor()
            cursor.callproc('ftInsertChannel', (channel, ))
            for result in cursor.stored_results():
                for (idd, added) in result:
                    cursor.close()
                    self.conn.commit()
                    return (idd, added)
            # should never happen
            cursor.close()
            self.conn.commit()
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
        return (0, 0, )

    def _insert_show(self, channelid, show, search):
        try:
            cursor = self.conn.cursor()
            cursor.callproc('ftInsertShow', (channelid, show, search, ))
            for result in cursor.stored_results():
                for (idd, added) in result:
                    cursor.close()
                    self.conn.commit()
                    return (idd, added)
            # should never happen
            cursor.close()
            self.conn.commit()
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
        return (0, 0, )

    def _get_schema_version(self):
        if self.conn is None:
            return 0
        cursor = self.conn.cursor()
        try:
            cursor.execute('SELECT `version` FROM `status` LIMIT 1')
            (version, ) = cursor.fetchone()
            del cursor
            return version
        except mysql.connector.errors.ProgrammingError:
            return 1
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
            return 0

    def _handle_database_update(self, convert, version=None):
        if version is None:
            return self._handle_database_update(convert, self._get_schema_version())
        if version == 0:
            # should never happen - something went wrong...
            self.exit()
            return False
        elif version == 3:
            # current version
            return True
        elif version == 2:
            self.logger.info('Converting database to version ')
            self.notifier.show_update_scheme_progress()
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT @@SESSION.sql_mode')
                (sql_mode, ) = cursor.fetchone()
                self.logger.info('Current SQL mode is {}', sql_mode)
                cursor.execute('SET SESSION sql_mode = ""')
                ##
                self.logger.info('Change airdate to datetime...')
                self.logger.info('add column')
                cursor.execute('ALTER TABLE `film` ADD COLUMN `aired2` DATETIME')
                self.notifier.update_update_scheme_progress(5)
                self.logger.info('update column')
                cursor.execute('UPDATE `film` SET `aired2` = FROM_UNIXTIME(UNIX_TIMESTAMP(`aired`))')
                self.notifier.update_update_scheme_progress(30)
                self.logger.info('drop old column')
                cursor.execute('ALTER TABLE `film` DROP COLUMN `aired`')
                self.notifier.update_update_scheme_progress(60)
                self.logger.info('rename column')
                cursor.execute('ALTER TABLE `film` CHANGE `aired2` `aired` DATETIME')
                self.notifier.update_update_scheme_progress(70)
                ##
                self.logger.info('change column idHash to char')
                cursor.execute('ALTER TABLE `film` CHANGE `idhash` `idhash` CHAR(32)')
                self.notifier.update_update_scheme_progress(80)
                ##
                self.logger.info('Update duration')
                cursor.execute("UPDATE `film` SET `duration` = '00:00:00' where `duration` is null")
                self.notifier.update_update_scheme_progress(90)
                ##
                self.logger.info('drop procedure')
                cursor.execute('DROP PROCEDURE IF EXISTS `ftInsertFilm`')
                self.notifier.update_update_scheme_progress(95)
                ##
                self.logger.info('Update Version')
                cursor.execute('UPDATE `status` SET `version` = 3')
                #
                self.logger.info('Resetting SQL mode to {}', sql_mode)
                cursor.execute('SET SESSION sql_mode = %s', (sql_mode, ))
                self.logger.info('Scheme successfully updated to version 2')
                self.notifier.close_update_scheme_progress()
            except mysql.connector.Error as err:
                self.logger.error(
                    '=== DATABASE SCHEME UPDATE ERROR: {} ===', err)
                self.exit()
                self.notifier.close_update_scheme_progress()
                self.notifier.show_database_error(err)
                return False
            return True
        elif convert is False:
            # do not convert (Addon threads)
            self.exit()
            self.notifier.show_updating_scheme()
            return False
        elif version == 1:
            # convert from 1 to 2
            self.logger.info('Converting database from version 2 to version 3')
            self.notifier.show_update_scheme_progress()
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT @@SESSION.sql_mode')
                (sql_mode, ) = cursor.fetchone()
                self.logger.info('Current SQL mode is {}', sql_mode)
                cursor.execute('SET SESSION sql_mode = ""')

                self.logger.info('Reducing channel name length...')
                cursor.execute(
                    'ALTER TABLE `channel` CHANGE COLUMN `channel` `channel` varchar(64) NOT NULL')
                self.notifier.update_update_scheme_progress(5)
                self.logger.info('Reducing show name length...')
                cursor.execute(
                    'ALTER TABLE `show` CHANGE COLUMN `show` `show` varchar(128) NOT NULL')
                self.notifier.update_update_scheme_progress(10)
                cursor.execute(
                    'ALTER TABLE `show` CHANGE COLUMN `search` `search` varchar(128) NOT NULL')
                self.notifier.update_update_scheme_progress(15)
                self.logger.info('Reducing film title length...')
                cursor.execute(
                    'ALTER TABLE `film` CHANGE COLUMN `title` `title` varchar(128) NOT NULL')
                self.notifier.update_update_scheme_progress(50)
                cursor.execute(
                    'ALTER TABLE `film` CHANGE COLUMN `search` `search` varchar(128) NOT NULL')
                self.notifier.update_update_scheme_progress(80)
                self.logger.info('Deleting old dupecheck index...')
                cursor.execute('ALTER TABLE `film` DROP KEY `dupecheck`')
                self.logger.info('Creating and filling new column idhash...')
                cursor.execute(
                    'ALTER TABLE `film` ADD COLUMN `idhash` varchar(32) NULL AFTER `id`')
                self.notifier.update_update_scheme_progress(82)
                cursor.execute(
                    'UPDATE `film` SET `idhash`= MD5( CONCAT( `channelid`, ":", `showid`, ":", `url_video` ) )')
                self.notifier.update_update_scheme_progress(99)
                self.logger.info('Creating new dupecheck index...')
                cursor.execute(
                    'ALTER TABLE `film` ADD KEY `dupecheck` (`idhash`)')
                self.logger.info('Adding version info to status table...')
                cursor.execute(
                    'ALTER TABLE `status` ADD COLUMN `version` INT(11) NOT NULL DEFAULT 2')
                self.logger.info('Resetting SQL mode to {}', sql_mode)
                cursor.execute('SET SESSION sql_mode = %s', (sql_mode, ))
                self.logger.info('Scheme successfully updated to version 2')
                self.notifier.close_update_scheme_progress()
            except mysql.connector.Error as err:
                self.logger.error(
                    '=== DATABASE SCHEME UPDATE ERROR: {} ===', err)
                self.exit()
                self.notifier.close_update_scheme_progress()
                self.notifier.show_database_error(err)
                return False
        return True

    def _handle_database_initialization(self):
        cursor = None
        dbcreated = False
        try:
            cursor = self.conn.cursor()
            cursor.execute('CREATE DATABASE IF NOT EXISTS `{}` DEFAULT CHARACTER SET utf8'.format(
                self.settings.database))
            dbcreated = True
            self.conn.database = self.settings.database
            cursor.execute('SET FOREIGN_KEY_CHECKS=0')
            self.conn.commit()
            cursor.execute(
                """
CREATE TABLE `channel` (
    `id`            int(11)         NOT NULL AUTO_INCREMENT,
    `dtCreated`     timestamp       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `touched`       smallint(1)     NOT NULL DEFAULT '1',
    `channel`       varchar(64)     NOT NULL,
    PRIMARY KEY                     (`id`),
    KEY             `channel`       (`channel`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
                """
            )
            self.conn.commit()

            cursor.execute("""
CREATE TABLE `film` (
    `id`            int(11)         NOT NULL AUTO_INCREMENT,
    `idhash`        char(32)        DEFAULT NULL,
    `dtCreated`     timestamp       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `touched`       smallint(1)     NOT NULL DEFAULT '1',
    `channelid`     int(11)         NOT NULL,
    `showid`        int(11)         NOT NULL,
    `title`         varchar(128)    NOT NULL,
    `search`        varchar(128)    NOT NULL,
    `aired`         datetime        NULL DEFAULT NULL,
    `duration`      time            DEFAULT NULL,
    `size`          int(11)         DEFAULT NULL,
    `description`   longtext,
    `website`       varchar(384)    DEFAULT NULL,
    `url_sub`       varchar(384)    DEFAULT NULL,
    `url_video`     varchar(384)    DEFAULT NULL,
    `url_video_sd`  varchar(384)    DEFAULT NULL,
    `url_video_hd`  varchar(384)    DEFAULT NULL,
    `airedepoch`    int(11)         DEFAULT NULL,
    PRIMARY KEY                     (`id`),
    KEY             `index_1`       (`showid`,`title`),
    KEY             `index_2`       (`channelid`,`title`),
    KEY             `dupecheck`     (`idhash`),
    CONSTRAINT `FK_FilmChannel` FOREIGN KEY (`channelid`) REFERENCES `channel` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION,
    CONSTRAINT `FK_FilmShow` FOREIGN KEY (`showid`) REFERENCES `show` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
            """)
            self.conn.commit()

            cursor.execute("""
CREATE TABLE `show` (
    `id`            int(11)         NOT NULL AUTO_INCREMENT,
    `dtCreated`     timestamp       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `touched`       smallint(1)     NOT NULL DEFAULT '1',
    `channelid`     int(11)         NOT NULL,
    `show`          varchar(128)    NOT NULL,
    `search`        varchar(128)    NOT NULL,
    PRIMARY KEY                     (`id`),
    KEY             `show`          (`show`),
    KEY             `search`        (`search`),
    KEY             `combined_1`    (`channelid`,`search`),
    KEY             `combined_2`    (`channelid`,`show`),
    CONSTRAINT `FK_ShowChannel` FOREIGN KEY (`channelid`) REFERENCES `channel` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
            """)
            self.conn.commit()

            cursor.execute("""
CREATE TABLE `status` (
    `modified`      int(11)         NOT NULL,
    `status`        varchar(255)    NOT NULL,
    `lastupdate`    int(11)         NOT NULL,
    `filmupdate`    int(11)         NOT NULL,
    `fullupdate`    int(1)          NOT NULL,
    `add_chn`       int(11)         NOT NULL,
    `add_shw`       int(11)         NOT NULL,
    `add_mov`       int(11)         NOT NULL,
    `del_chm`       int(11)         NOT NULL,
    `del_shw`       int(11)         NOT NULL,
    `del_mov`       int(11)         NOT NULL,
    `tot_chn`       int(11)         NOT NULL,
    `tot_shw`       int(11)         NOT NULL,
    `tot_mov`       int(11)         NOT NULL,
    `version`       int(11)         NOT NULL DEFAULT 2
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
            """)
            self.conn.commit()

            cursor.execute(
                'INSERT INTO `status` VALUES (0,"IDLE",0,0,0,0,0,0,0,0,0,0,0,0,3);')
            self.conn.commit()

            cursor.execute('SET FOREIGN_KEY_CHECKS=1')
            self.conn.commit()

            cursor.execute("""
CREATE PROCEDURE `ftInsertChannel`(
    _channel    VARCHAR(255)
)
BEGIN
    DECLARE channelid_  INT(11);
    DECLARE touched_    INT(1);
    DECLARE added_      INT(1) DEFAULT 0;

    SELECT  `id`,
            `touched`
    INTO    channelid_,
            touched_
    FROM    `channel`
    WHERE   ( `channel`.`channel` = _channel );

    IF ( channelid_ IS NULL ) THEN
        INSERT INTO `channel` (
            `channel`
        )
        VALUES (
            _channel
        );
        SET channelid_  = LAST_INSERT_ID();
        SET added_ = 1;
    ELSE
        UPDATE  `channel`
        SET     `touched` = 1
        WHERE   ( `id` = channelid_ );
    END IF;

    SELECT  channelid_  AS `id`,
            added_      AS `added`;
END
            """)
            self.conn.commit()

            cursor.execute("""
CREATE PROCEDURE `ftInsertShow`(
    _channelid  INT(11),
    _show       VARCHAR(255),
    _search     VARCHAR(255)
)
BEGIN
    DECLARE showid_     INT(11);
    DECLARE touched_    INT(1);
    DECLARE added_      INT(1) DEFAULT 0;

    SELECT  `id`,
            `touched`
    INTO    showid_,
            touched_
    FROM    `show`
    WHERE   ( `show`.`channelid` = _channelid )
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
        SET showid_ = LAST_INSERT_ID();
        SET added_ = 1;
    ELSE
        UPDATE  `show`
        SET     `touched` = 1
        WHERE   ( `id` = showid_ );
    END IF;


    SELECT  showid_     AS `id`,
            added_      AS `added`;
END
            """)
            self.conn.commit()

            cursor.execute("""
CREATE PROCEDURE `ftUpdateEnd`(
    _full   INT(1)
)
BEGIN
    DECLARE     del_chn_        INT DEFAULT 0;
    DECLARE     del_shw_        INT DEFAULT 0;
    DECLARE     del_mov_        INT DEFAULT 0;
    DECLARE     cnt_chn_        INT DEFAULT 0;
    DECLARE     cnt_shw_        INT DEFAULT 0;
    DECLARE     cnt_mov_        INT DEFAULT 0;

    IF ( _full = 1 ) THEN
        SELECT      COUNT(*)
        INTO        del_chn_
        FROM        `channel`
        WHERE       ( `touched` = 0 );

        SELECT      COUNT(*)
        INTO        del_shw_
        FROM        `show`
        WHERE       ( `touched` = 0 );

        SELECT      COUNT(*)
        INTO        del_mov_
        FROM        `film`
        WHERE       ( `touched` = 0 );

        DELETE FROM `show`
        WHERE       ( `show`.`touched` = 0 )
                    AND
                    ( ( SELECT SUM( `film`.`touched` ) FROM `film` WHERE `film`.`showid` = `show`.`id` ) = 0 );

        DELETE FROM `film`
        WHERE       ( `touched` = 0 );
    ELSE
        SET del_chn_ = 0;
        SET del_shw_ = 0;
        SET del_mov_ = 0;
    END IF;

    SELECT  del_chn_    AS  `del_chn`,
            del_shw_    AS  `del_shw`,
            del_mov_    AS  `del_mov`,
            cnt_chn_    AS  `cnt_chn`,
            cnt_shw_    AS  `cnt_shw`,
            cnt_mov_    AS  `cnt_mov`;
END
            """)
            self.conn.commit()

            cursor.execute("""
CREATE PROCEDURE `ftUpdateStart`(
    _full   INT(1)
)
BEGIN
    DECLARE     cnt_chn_        INT DEFAULT 0;
    DECLARE     cnt_shw_        INT DEFAULT 0;
    DECLARE     cnt_mov_        INT DEFAULT 0;

    SELECT  COUNT(id)
    INTO    cnt_chn_
    FROM    `channel`;

    SELECT  COUNT(id)
    INTO    cnt_shw_
    FROM    `show`;

    SELECT  COUNT(id)
    INTO    cnt_mov_
    FROM    `film`;

    IF ( _full = 1 ) THEN
        UPDATE  `channel`
        SET     `touched` = 0;

        UPDATE  `show`
        SET     `touched` = 0;

        UPDATE  `film`
        SET     `touched` = 0;
    END IF;
    
    SELECT  cnt_chn_    AS `cnt_chn`,
            cnt_shw_    AS `cnt_shw`,
            cnt_mov_    AS `cnt_mov`;
END
            """)
            self.conn.commit()

            cursor.close()
            self.logger.info('Database creation successfully completed')
            return True
        except mysql.connector.Error as err:
            self.logger.error('=== DATABASE CREATION ERROR: {} ===', err)
            self.notifier.show_database_error(err)
            try:
                if dbcreated:
                    cursor.execute('DROP DATABASE `{}`'.format(
                        self.settings.database))
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
        return False
