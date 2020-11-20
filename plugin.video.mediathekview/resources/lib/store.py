# -*- coding: utf-8 -*-
"""
The database wrapper module

Copyright 2017-2019, Leo Moll
SPDX-License-Identifier: MIT
"""

import time

from resources.lib.storemysql import StoreMySQL
from resources.lib.storesqlite import StoreSQLite


class Store(object):
    """
    The database wrapper class

    Args:
        logger(KodiLogger): a valid `KodiLogger` instance

        notifier(Notifier): a valid `Notifier` instance

        settings(Settings): a valid `Settings` instance
    """

    def __init__(self, logger, notifier, settings):
        self.logger = logger
        self.notifier = notifier
        self.settings = settings
        # load storage engine
        if settings.type == 0:
            self.logger.info('Database driver: Internal (sqlite)')
            self.database = StoreSQLite(logger.get_new_logger(
                'StoreSQLite'), notifier, self.settings)
        elif settings.type == 1:
            self.logger.info('Database driver: External (mysql)')
            self.database = StoreMySQL(logger.get_new_logger(
                'StoreMySQL'), notifier, self.settings)
        else:
            self.logger.warn('Unknown Database driver selected')
            self.database = None

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
        if self.database is not None:
            return self.database.init(reset, convert)
        return False

    def exit(self):
        """ Shutdown of the database system """
        if self.database is not None:
            self.database.exit()

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
        # pylint: disable=line-too-long
        return self.database.search(search, filmui, extendedsearch) if self.database is not None else 0

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
        return self.database.get_recents(channelid, filmui) if self.database is not None else 0

    def get_live_streams(self, filmui):
        """
        Populates the current UI directory with the live
        streams

        Args:
            filmui(FilmUI): an instance of a film model view used
                for populating the directory
        """
        return self.database.get_live_streams(filmui) if self.database is not None else 0

    def get_channels(self, channelui):
        """
        Populates the current UI directory with the list
        of available channels

        Args:
            channelui(ChannelUI): an instance of a channel model
                view used for populating the directory
        """
        if self.database is not None:
            self.database.get_channels(channelui)

    def get_recent_channels(self, channelui):
        """
        Populates the current UI directory with the list
        of channels having recent film additions based on
        the configured interval.

        Args:
            channelui(ChannelUI): an instance of a channel model
                view used for populating the directory
        """
        if self.database is not None:
            self.database.get_recent_channels(channelui)

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
        if self.database is not None:
            self.database.get_initials(channelid, initialui)

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
        if self.database is not None:
            self.database.get_shows(channelid, initial, showui)

    def get_films(self, showid, filmui):
        """
        Populates the current UI directory with a list
        of films of a specific show.

        Args:
            showid(id): database id of the selected show.

            filmui(FilmUI): an instance of a film model view
                used for populating the directory
        """
        return self.database.get_films(showid, filmui) if self.database is not None else 0

    def retrieve_film_info(self, filmid):
        """
        Retrieves the spcified film information
        from the database

        Args:
            filmid(id): database id of the requested film
        """
        if self.database is not None:
            return self.database.retrieve_film_info(filmid)
        else:
            return None

    def get_status(self):
        """ Retrieves the database status information """
        if self.database is not None:
            return self.database.get_status()
        else:
            return {
                'modified': int(time.time()),
                'status': 'UNINIT',
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

    # pylint: disable=line-too-long
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
        if self.database is not None:
            self.database.update_status(
                status,
                lastupdate,
                filmupdate,
                fullupdate,
                add_chn, add_shw, add_mov,
                del_chn, del_shw, del_mov,
                tot_chn, tot_shw, tot_mov
            )

    def supports_update(self):
        """
        Returns `True` if the selected database driver supports
        updating a local copy
        """
        if self.database is not None:
            return self.database.supports_update()
        return False

    def supports_native_update(self, full):
        """
        Returns `True` if the selected database driver supports
        updating a local copy with native functions and files

        Args:
            full(bool): if `True` a full update is requested
        """
        if self.database is not None:
            return self.database.supports_native_update(full)
        return False

    def get_native_info(self, full):
        """
        Returns a tuple containing:
        - The URL of the requested update type dispatcher
        - the base name of the downloadable file

        Args:
            full(bool): if `True` a full update is requested
        """
        if self.database is not None:
            return self.database.get_native_info(full)
        return None

    def native_update(self, full):
        """
        Performs a native update of the database.

        Args:
            full(bool): if `True` a full update is started
        """
        if self.database is not None:
            return self.database.native_update(full)
        return False

    def ft_init(self):
        """
        Initializes local database for updating
        """
        if self.database is not None:
            return self.database.ft_init()
        return False

    def ft_update_start(self, full):
        """
        Begins a local update procedure

        Args:
            full(bool): if `True` a full update is started
        """
        if self.database is not None:
            return self.database.ft_update_start(full)
        return (0, 0, 0, )

    def ft_update_end(self, delete):
        """
        Finishes a local update procedure

        Args:
            delete(bool): if `True` all records not updated
                will be deleted
        """
        if self.database is not None:
            return self.database.ft_update_end(delete)
        return (0, 0, 0, 0, 0, 0, )

    def ft_insert_film(self, film, commit=True):
        """
        Inserts a film emtry into the database

        Args:
            film(Film): a film entry

            commit(bool, optional): the operation will be
                commited immediately. Default is `True`
        """
        if self.database is not None:
            return self.database.ft_insert_film(film, commit)
        return (0, 0, 0, 0, )
