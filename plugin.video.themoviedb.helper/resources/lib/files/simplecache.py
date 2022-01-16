#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Modification of marcelveldt's simplecache plugin
Code cleanup
- Removal of json methods
- Leia/Matrix Python-2/3 cross-compatibility
- Allow setting folder and filename of DB
"""

import xbmcvfs
import xbmcgui
import xbmc
import sqlite3
from contextlib import contextmanager
from resources.lib.addon.plugin import kodi_log
from resources.lib.addon.timedate import set_timestamp
from resources.lib.files.utils import get_file_path

from resources.lib.files.utils import json_loads as data_loads
from json import dumps as data_dumps
DATABASE_NAME = 'database_v4'

# data_loads = eval
# data_dumps = repr
# DATABASE_NAME = 'database_v3'

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
        filename = filename or 'defaultcache.db'
        self._win = xbmcgui.Window(10000)
        self._monitor = xbmc.Monitor()
        self._db_file = get_file_path(folder, filename)
        self._sc_name = u'{}_{}_simplecache'.format(folder, filename)
        self._mem_only = mem_only
        self._queue = []
        self._delaywrite = delay_write
        self.check_cleanup()
        kodi_log("CACHE: Initialized")

    def close(self):
        '''tell any tasks to stop immediately (as we can be called multithreaded) and cleanup objects'''
        self._exit = True
        # wait for all tasks to complete
        while self._busy_tasks and not self._monitor.abortRequested():
            xbmc.sleep(25)
        kodi_log("CACHE: Closed {}".format(self._sc_name), 2)

    def __del__(self):
        '''make sure close is called'''
        if self._queue:
            kodi_log("CACHE: Write {} Items in Queue\n{}".format(len(self._queue), self._sc_name), 2)
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
        with self.busy_tasks(u'set.{}'.format(endpoint)):
            expires = set_timestamp(cache_days * TIME_DAYS, True)
            data = data_dumps(data)
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
        lastexecuted = self._win.getProperty(u"{}.clean.lastexecuted".format(self._sc_name))
        if not lastexecuted:
            self._win.setProperty(u"{}.clean.lastexecuted".format(self._sc_name), str(cur_time))
        elif (int(lastexecuted) + set_timestamp(self._auto_clean_interval, True)) < cur_time:
            self._do_cleanup()

    def _get_mem_cache(self, endpoint, cur_time):
        '''
            get cache data from memory cache
            we use window properties because we need to be stateless
        '''
        # Check expiration time
        expr_endpoint = u'{}_expr_{}'.format(self._sc_name, endpoint)
        expr_propdata = self._win.getProperty(expr_endpoint)
        if not expr_propdata or int(expr_propdata) <= cur_time:
            return

        # Retrieve data
        data_endpoint = u'{}_data_{}'.format(self._sc_name, endpoint)
        data_propdata = self._win.getProperty(data_endpoint)
        if not data_propdata:
            return

        return data_loads(data_propdata)

    def _set_mem_cache(self, endpoint, expires, data):
        '''
            window property cache as alternative for memory cache
            usefull for (stateless) plugins
        '''
        expr_endpoint = u'{}_expr_{}'.format(self._sc_name, endpoint)
        data_endpoint = u'{}_data_{}'.format(self._sc_name, endpoint)
        self._win.setProperty(expr_endpoint, str(expires))
        self._win.setProperty(data_endpoint, data)

    def get_id_list(self):
        query = "SELECT id FROM simplecache"
        cache_data = self._execute_sql(query)
        if not cache_data:
            return
        return [job[0] for job in cache_data]

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
        self._set_mem_cache(endpoint, cache_data[0], cache_data[1])
        result = data_loads(cache_data[1])
        return result

    def _set_db_cache(self, endpoint, expires, data):
        ''' store cache data in _database '''
        query = "INSERT OR REPLACE INTO simplecache( id, expires, data, checksum) VALUES (?, ?, ?, ?)"
        self._execute_sql(query, (endpoint, expires, data, 0))

    def _do_delete(self):
        '''perform cleanup task'''
        if self._exit or self._monitor.abortRequested():
            return

        with self.busy_tasks(__name__):
            cur_time = set_timestamp(0, True)
            kodi_log("CACHE: Deleting {}...".format(self._sc_name))

            self._win.setProperty(u"{}.cleanbusy".format(self._sc_name), "busy")

            query = 'DELETE FROM simplecache'
            self._execute_sql(query)
            self._execute_sql("VACUUM")

        # Washup
        self._win.setProperty(u"{}.clean.lastexecuted".format(self._sc_name), str(cur_time))
        self._win.clearProperty(u"{}.cleanbusy".format(self._sc_name))
        kodi_log("CACHE: Delete {} done".format(self._sc_name))

    def _do_cleanup(self, force=False):
        '''perform cleanup task'''
        if self._exit or self._monitor.abortRequested():
            return

        with self.busy_tasks(__name__):
            cur_time = set_timestamp(0, True)
            kodi_log("CACHE: Running cleanup...")
            if self._win.getProperty(u"{}.cleanbusy".format(self._sc_name)):
                return
            self._win.setProperty(u"{}.cleanbusy".format(self._sc_name), "busy")

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
                    kodi_log(u"CACHE: delete from db {}".format(cache_id))

            # compact db
            self._execute_sql("VACUUM")

        # Washup
        self._win.setProperty(u"{}.clean.lastexecuted".format(self._sc_name), str(cur_time))
        self._win.clearProperty(u"{}.cleanbusy".format(self._sc_name))
        kodi_log("CACHE: Auto cleanup done")

    def _get_database(self, attempts=2):
        '''get reference to our sqllite _database - performs basic integrity check'''
        try:
            connection = sqlite3.connect(self._db_file, timeout=30, isolation_level=None)
            connection.execute('SELECT * FROM simplecache LIMIT 1')
            return connection
        except Exception:
            # our _database is corrupt or doesn't exist yet, we simply try to recreate it
            if xbmcvfs.exists(self._db_file):
                xbmcvfs.delete(self._db_file)
            try:
                connection = sqlite3.connect(self._db_file, timeout=30, isolation_level=None)
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS simplecache(
                    id TEXT UNIQUE, expires INTEGER, data TEXT, checksum INTEGER)""")
                connection.execute("CREATE INDEX idx ON simplecache(id)")
                return connection
            except Exception as error:
                kodi_log(u"CACHE: Exception while initializing _database: {} ({})".format(error, attempts), 1)
                if attempts < 1:
                    return
                attempts -= 1
                self._monitor.waitForAbort(1)
                return self._get_database(attempts)

    def _execute_sql(self, query, data=None):
        '''little wrapper around execute and executemany to just retry a db command if db is locked'''
        retries = 0
        result = None
        error = None
        # always use new db object because we need to be sure that data is available for other simplecache instances
        with self._get_database() as _database:
            while not retries == 10 and not self._monitor.abortRequested():
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
                except sqlite3.OperationalError as error:
                    try:
                        if "database is locked" in error:
                            kodi_log("CACHE: Locked: Retrying DB commit...")
                            retries += 1
                            self._monitor.waitForAbort(0.5)
                        else:
                            break
                    except TypeError:
                        break
                except Exception:
                    break
            kodi_log(u"CACHE: _database ERROR ! -- {}".format(error), 1)
        return None
