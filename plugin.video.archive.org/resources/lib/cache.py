# -*- coding: utf-8 -*-
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import hashlib
import json
import pickle
import re
import time
import zlib
import xbmcvfs
import xbmcaddon
from sqlite3 import dbapi2 as db, OperationalError, Binary

cacheFile = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile') + '/cache.db')
cache_table = 'cache'


def get(function, duration, *args, **kwargs):
    # type: (function, int, object) -> object or None
    """
    Gets cached value for provided function with optional arguments, or executes and stores the result
    :param function: Function to be executed
    :param duration: Duration of validity of cache in hours
    :param args: Optional arguments for the provided function
    :param kwargs: Optional keyword arguments for the provided function
    """

    key = _hash_function(function, *args, **kwargs)
    cache_result = cache_get(key)

    if cache_result:
        if _is_cache_valid(cache_result['date'], duration):
            return pickle.loads(zlib.decompress(cache_result['value']))

    fresh_result = function(*args, **kwargs)

    if not fresh_result:
        # If the cache is old, but we didn't get fresh result, return the
        # old cache
        if cache_result:
            return pickle.loads(zlib.decompress(cache_result['value']))
        return None

    cache_insert(key, Binary(zlib.compress(pickle.dumps(fresh_result))))
    return fresh_result


def remove(function, *args, **kwargs):
    key = _hash_function(function, *args, **kwargs)
    cursor = _get_connection_cursor()
    cursor.execute("DELETE FROM %s WHERE key = ?" % cache_table, [key])
    cursor.connection.commit()


def timeout(function, *args, **kwargs):
    key = _hash_function(function, *args, **kwargs)
    result = cache_get(key)
    return int(result['date'])


def cache_get(key):
    # type: (str, str) -> dict or None
    try:
        cursor = _get_connection_cursor()
        cursor.execute("SELECT * FROM %s WHERE key = ?" % cache_table, [key])
        return cursor.fetchone()
    except OperationalError:
        return None


def cache_insert(key, value):
    # type: (str, str) -> None
    cursor = _get_connection_cursor()
    now = int(time.time())
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS %s (key TEXT, value BINARY, date INTEGER, UNIQUE(key))" %
        cache_table)
    cursor.execute(
        "CREATE UNIQUE INDEX if not exists index_key ON %s (key)" % cache_table)
    update_result = cursor.execute(
        "UPDATE %s SET value=?,date=? WHERE key=?"
        % cache_table, (value, now, key))

    if update_result.rowcount == 0:
        cursor.execute(
            "INSERT INTO %s Values (?, ?, ?)"
            % cache_table, (key, value, now)
        )

    cursor.connection.commit()


def cache_clear():
    cursor = _get_connection_cursor()

    for t in [cache_table, 'rel_list', 'rel_lib']:
        try:
            cursor.execute("DROP TABLE IF EXISTS %s" % t)
            cursor.execute("VACUUM")
            cursor.commit()
        except BaseException:
            pass


def _get_connection_cursor():
    conn = _get_connection()
    return conn.cursor()


def _get_connection():
    conn = db.connect(cacheFile)
    conn.row_factory = _dict_factory
    return conn


def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def _hash_function(function_instance, *args, **kwargs):
    return _get_function_name(function_instance) + _generate_md5(*args, **kwargs)


def _get_function_name(function_instance):
    return re.sub(
        r'.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+',
        '',
        repr(function_instance))


def _generate_md5(*args, **kwargs):
    md5_hash = hashlib.md5()
    [md5_hash.update(str(arg).encode()) for arg in args]
    md5_hash.update(json.dumps(kwargs).encode())
    return md5_hash.hexdigest()


def _is_cache_valid(cached_time, cache_timeout):
    now = int(time.time())
    diff = now - cached_time
    return (cache_timeout * 3600) > diff
