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

import ast
import hashlib
import re
import time
import json
import six
from kodi_six import xbmc, xbmcvfs
try:
    from sqlite3 import dbapi2 as db, OperationalError
except ImportError:
    from pysqlite2 import dbapi2 as db, OperationalError


TRANSLATEPATH = xbmcvfs.translatePath if six.PY3 else xbmc.translatePath
cacheFile = TRANSLATEPATH('special://profile/addon_data/plugin.video.imdb.trailers/cache.db')
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
            return ast.literal_eval(cache_result['value'].encode('utf-8') if six.PY2 else cache_result['value'])

    fresh_result = function(*args, **kwargs)

    if not fresh_result:
        # If the cache is old, but we didn't get fresh result, return the
        # old cache
        if cache_result:
            return cache_result
        return None

    cache_insert(key, repr(fresh_result))
    return ast.literal_eval(repr(fresh_result).encode('utf-8') if six.PY2 else repr(fresh_result))


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
        "CREATE TABLE IF NOT EXISTS %s (key TEXT, value TEXT, date INTEGER, UNIQUE(key))" %
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
    [md5_hash.update(str(arg) if six.PY2 else str(arg).encode()) for arg in args]
    md5_hash.update(json.dumps(kwargs) if six.PY2 else json.dumps(kwargs).encode())
    return md5_hash.hexdigest()


def _is_cache_valid(cached_time, cache_timeout):
    now = int(time.time())
    diff = now - cached_time
    return (cache_timeout * 3600) > diff
