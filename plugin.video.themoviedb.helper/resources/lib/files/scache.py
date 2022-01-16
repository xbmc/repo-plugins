#!/usr/bin/python
# -*- coding: utf-8 -*-
import zlib
import xbmcvfs
from xbmcgui import Window
from xbmc import Monitor, sleep
from contextlib import contextmanager
from resources.lib.addon.plugin import get_setting
from resources.lib.addon.logger import kodi_log
from resources.lib.addon.tmdate import set_timestamp
from resources.lib.files.futils import get_file_path
from resources.lib.files.futils import json_loads as data_loads
from json import dumps as data_dumps
import sqlite3


DATABASE_NAME = 'database_v5'
TIME_MINUTES = 60
TIME_HOURS = 60 * TIME_MINUTES
TIME_DAYS = 24 * TIME_HOURS


class SimpleCache(object):
    '''simple stateless caching system for Kodi'''
    _exit = False
    _auto_clean_interval = 4 * TIME_HOURS
    _win = None
    _busy_tasks = []
    _database = None

    def __init__(self, folder=None, filename=None, mem_only=False, delay_write=False):
        '''Initialize our caching class'''
        folder = folder or DATABASE_NAME
        basefolder = get_setting('cache_location', 'str') or ''
        basefolder += folder
        filename = filename or 'defaultcache.db'
        self._win = Window(10000)
        self._monitor = Monitor()
        self._db_file = get_file_path(basefolder, filename, join_addon_data=basefolder == folder)
        self._sc_name = f'{folder}_{filename}_simplecache'
        self._mem_only = mem_only
        self._queue = []
        self._delaywrite = delay_write
        self._connection = None
        self.check_cleanup()
        kodi_log("CACHE: Initialized")

    def close(self):
        '''tell any tasks to stop immediately (as we can be called multithreaded) and cleanup objects'''
        self._exit = True
        # wait for all tasks to complete
        while self._busy_tasks and not self._monitor.abortRequested():
            sleep(25)
        kodi_log(f'CACHE: Closed {self._sc_name}', 2)

    def __del__(self):
        '''make sure close is called'''
        if self._queue:
            kodi_log(f'CACHE: Write {len(self._queue)} Items in Queue\n{self._sc_name}', 2)
        for i in self._queue:
            self._set_db_cache(*i)
        self._queue = []
        self.close()

    @contextmanager
    def busy_tasks(self, task_name):
        self._busy_tasks.append(task_name)
        try:
            yield
        finally:
            self._busy_tasks.remove(task_name)

    def get(self, endpoint, no_hdd=False):
        '''
            get object from cache and return the results
            endpoint: the (unique) name of the cache object as reference
        '''
        cur_time = set_timestamp(0, True)
        result = self._get_mem_cache(endpoint, cur_time)  # Try from memory first
        if result is not None or self._mem_only or no_hdd:
            return result
        return self._get_db_cache(endpoint, cur_time)  # Fallback to checking database if not in memory

    def set(self, endpoint, data, cache_days=30):
        """ set data in cache """
        with self.busy_tasks(f'set.{endpoint}'):
            expires = set_timestamp(cache_days * TIME_DAYS, True)
            data = data_dumps(data, separators=(',', ':'))
            self._set_mem_cache(endpoint, expires, data)
            if self._mem_only:
                return
            if self._delaywrite:
                self._queue.append((endpoint, expires, data))
                return
            self._set_db_cache(endpoint, expires, data)

    def check_cleanup(self):
        '''check if cleanup is needed - public method, may be called by calling addon'''
        if self._mem_only:
            return
        # cur_time = get_datetime_now()
        cur_time = set_timestamp(0, True)
        lastexecuted = self._win.getProperty(f'{self._sc_name}.clean.lastexecuted')
        if not lastexecuted:
            self._win.setProperty(f'{self._sc_name}.clean.lastexecuted', str(cur_time - self._auto_clean_interval + 600))
        elif (int(lastexecuted) + self._auto_clean_interval) < cur_time:
            self._do_cleanup()

    def _get_mem_cache(self, endpoint, cur_time):
        '''
            get cache data from memory cache
            we use window properties because we need to be stateless
        '''
        # Check expiration time
        expr_endpoint = f'{self._sc_name}_expr_{endpoint}'
        expr_propdata = self._win.getProperty(expr_endpoint)
        if not expr_propdata or int(expr_propdata) <= cur_time:
            return

        # Retrieve data
        data_endpoint = f'{self._sc_name}_data_{endpoint}'
        data_propdata = self._win.getProperty(data_endpoint)
        if not data_propdata:
            return

        return data_loads(data_propdata)

    def _set_mem_cache(self, endpoint, expires, data):
        '''
            window property cache as alternative for memory cache
            usefull for (stateless) plugins
        '''
        expr_endpoint = f'{self._sc_name}_expr_{endpoint}'
        data_endpoint = f'{self._sc_name}_data_{endpoint}'
        self._win.setProperty(expr_endpoint, str(expires))
        self._win.setProperty(data_endpoint, data)

    def get_id_list(self):
        query = "SELECT id FROM simplecache"
        cache_data = self._execute_sql(query)
        if not cache_data:
            return
        return {job[0] for job in cache_data}

    def _get_db_cache(self, endpoint, cur_time):
        '''get cache data from sqllite _database'''
        result = None
        query = "SELECT expires, data, checksum FROM simplecache WHERE id = ? LIMIT 1"
        cache_data = self._execute_sql(query, (endpoint,))
        if not cache_data:
            return
        cache_data = cache_data.fetchone()
        if not cache_data or int(cache_data[0]) <= cur_time:
            return
        try:
            data = str(zlib.decompress(cache_data[1]), 'utf-8')
        except TypeError:
            data = cache_data[1]
        self._set_mem_cache(endpoint, cache_data[0], data)
        result = data_loads(data)
        return result

    def _set_db_cache(self, endpoint, expires, data):
        ''' store cache data in _database '''
        query = "INSERT OR REPLACE INTO simplecache( id, expires, data, checksum) VALUES (?, ?, ?, ?)"
        data = zlib.compress(bytes(data, 'utf-8'))
        self._execute_sql(query, (endpoint, expires, data, 0))

    def _do_delete(self):
        '''perform cleanup task'''
        if self._exit or self._monitor.abortRequested():
            return

        with self.busy_tasks(__name__):
            cur_time = set_timestamp(0, True)
            kodi_log(f'CACHE: Deleting {self._sc_name}...')

            self._win.setProperty(f'{self._sc_name}.cleanbusy', "busy")

            query = 'DELETE FROM simplecache'
            self._execute_sql(query)
            self._execute_sql("VACUUM")

        # Washup
        self._win.setProperty(f'{self._sc_name}.clean.lastexecuted', str(cur_time))
        self._win.clearProperty(f'{self._sc_name}.cleanbusy')
        kodi_log(f'CACHE: Delete {self._sc_name} done')

    def _do_cleanup(self, force=False):
        '''perform cleanup task'''
        if self._exit or self._monitor.abortRequested():
            return

        with self.busy_tasks(__name__):
            cur_time = set_timestamp(0, True)
            kodi_log(f"CACHE: Running cleanup...\n{self._sc_name}", 1)
            if self._win.getProperty(f'{self._sc_name}.cleanbusy'):
                return
            self._win.setProperty(f'{self._sc_name}.cleanbusy', "busy")

            query = "SELECT id, expires FROM simplecache"
            for cache_data in self._execute_sql(query).fetchall():
                cache_id = cache_data[0]
                cache_expires = cache_data[1]
                if self._exit or self._monitor.abortRequested():
                    return
                # always cleanup all memory objects on each interval
                self._win.clearProperty(cache_id)
                # clean up db cache object only if expired
                if force or int(cache_expires) < cur_time:
                    query = 'DELETE FROM simplecache WHERE id = ?'
                    self._execute_sql(query, (cache_id,))
                    kodi_log(f'CACHE: delete from db {cache_id}')

            # compact db
            self._execute_sql("VACUUM")

        # Washup
        self._win.setProperty(f'{self._sc_name}.clean.lastexecuted', str(cur_time))
        self._win.clearProperty(f'{self._sc_name}.cleanbusy')
        kodi_log(f"CACHE: Cleanup complete...\n{self._sc_name}", 1)

    def _set_pragmas(self, connection):
        if not self._connection:
            connection.execute("PRAGMA synchronous=normal")
            connection.execute("PRAGMA journal_mode=WAL")
            # connection.execute("PRAGMA temp_store=memory")
            # connection.execute("PRAGMA mmap_size=2000000000")
            # connection.execute("PRAGMA cache_size=-500000000")
        if self._delaywrite:
            self._connection = connection
        return connection

    def _get_database(self, attempts=2):
        '''get reference to our sqllite _database - performs basic integrity check'''
        try:
            connection = self._connection or sqlite3.connect(self._db_file, timeout=5, isolation_level=None, check_same_thread=not self._delaywrite)
            connection.execute('SELECT * FROM simplecache LIMIT 1')
            return self._set_pragmas(connection)
        except Exception:
            # our _database is corrupt or doesn't exist yet, we simply try to recreate it
            if xbmcvfs.exists(self._db_file):
                kodi_log(f'CACHE: Deleting Corrupt File: {self._db_file}...', 1)
                xbmcvfs.delete(self._db_file)
            try:
                kodi_log(f'CACHE: Initialising: {self._db_file}...', 1)
                connection = self._connection or sqlite3.connect(self._db_file, timeout=5, isolation_level=None, check_same_thread=not self._delaywrite)
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS simplecache(
                    id TEXT UNIQUE, expires INTEGER, data TEXT, checksum INTEGER)""")
                connection.execute("CREATE INDEX idx ON simplecache(id)")
                return self._set_pragmas(connection)
            except Exception as error:
                kodi_log(f'CACHE: Exception while initializing _database: {error} ({attempts})', 1)
                if attempts < 1:
                    return
                attempts -= 1
                self._monitor.waitForAbort(1)
                return self._get_database(attempts)

    def _execute_sql(self, query, data=None):
        '''little wrapper around execute and executemany to just retry a db command if db is locked'''
        retries = 10
        result = None
        error = ''
        # always use new db object because we need to be sure that data is available for other simplecache instances
        with self._get_database() as _database:
            while retries > 0 and not self._monitor.abortRequested():
                if self._exit:
                    return None
                try:
                    if isinstance(data, list):
                        result = _database.executemany(query, data)
                    elif data:
                        result = _database.execute(query, data)
                    else:
                        result = _database.execute(query)
                    return result
                except sqlite3.OperationalError as err:
                    error = err
                    try:
                        if "database is locked" == f'{error}':
                            kodi_log("CACHE: Locked: Retrying DB commit...", 1)
                            retries -= 1
                            self._monitor.waitForAbort(0.5)
                        else:
                            break
                    except TypeError:
                        break
                except Exception:
                    break
            kodi_log(f'CACHE: _database ERROR ! -- {error}', 1)
        return None
