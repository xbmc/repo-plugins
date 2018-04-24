# -*- coding: utf-8 -*-
"""HTTP File cache and helpers"""
__author__ = "fraser"

import sqlite3
import time
import xbmcvfs
from datetime import datetime, timedelta, tzinfo
from os import path

try:
    import _pickle as cpickle
except ImportError:
    import cPickle as cpickle

import logging
from . import kodilogging

kodilogging.config()
logger = logging.getLogger(__name__)

HTTPDATE_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"


def httpdate_to_datetime(input_date):
    # type (str) -> datetime
    if input_date is None:
        return None
    try:
        return datetime.strptime(input_date, HTTPDATE_FORMAT)
    except TypeError:
        return datetime(*(time.strptime(input_date, HTTPDATE_FORMAT)[0:6]))
    except ValueError as e:
        logger.debug(e)
        return None


def datetime_to_httpdate(input_date):
    # type (datetime) -> str
    if input_date is None:
        return None
    try:
        return input_date.strftime(HTTPDATE_FORMAT)
    except (ValueError, TypeError) as e:
        logger.debug(e)
        return None


class GMT(tzinfo):
    """GMT Time Zone"""

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "GMT"

    def dst(self, dt):
        return timedelta(0)


class Blob(object):
    """Blob serialisation class"""

    def __init__(self, data):
        self.data = data

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            # return cpickle.dumps(self.data, 1)
            return sqlite3.Binary(cpickle.dumps(self.data, -1))

    @staticmethod
    def deserialise(data):
        # type (sqlite3.Binary) -> Any
        return cpickle.loads(bytes(data))


class Cache(object):
    """
    HTTP control directive based cache
    https://docs.python.org/2/library/sqlite3.html
    https://tools.ietf.org/html/rfc7234
    """

    def __init__(self, name=None):
        self.connection = None
        if not xbmcvfs.exists(name):
            xbmcvfs.mkdirs(path.dirname(name))
        if name:
            self._open(name)

    def get(self, uri):
        # type: (str) -> Union[sqlite3.Row, None]
        """Retrieve a partial entry from the cache"""
        query = ("select blob, last_modified, etag, immutable, "
                 "case"
                 "  when max_age then max(age, max_age)"
                 "  else case"
                 "      when expires then expires - http_date"
                 "      else cast((datetime('now') - last_modified) / 10 as int)"
                 "  end "
                 "end >= strftime('%s', datetime('now')) - strftime('%s', http_date) as fresh "
                 "from data where uri=?")
        result = self._execute(query, (uri,))
        return None if result is None else result.fetchone()

    def set(self, uri, content, headers=None):
        # type: (str, Any, dict) -> None
        """Add or update a complete entry in the cache"""
        if headers is None:
            headers = {
                "date": datetime_to_httpdate(datetime.now(GMT())),
                "cache-control": "immutable, max-age=31556926"  # 1 year
            }
        directives = self._parse_cache_control(headers.get("cache-control"))
        if "no-store" in directives:
            return
        query = ("REPLACE INTO data (uri, blob, http_date, "
                 "age, etag, expires, last_modified, max_age, immutable) "
                 "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)")
        values = (
            uri,
            Blob(content),
            httpdate_to_datetime(headers.get("date")),
            headers.get("age", 0),
            headers.get("etag"),
            httpdate_to_datetime(headers.get("expires")),
            httpdate_to_datetime(headers.get("last-modified")),
            directives.get("max-age"),
            directives.get("immutable"))
        self._execute(query, values)

    def touch(self, uri, headers):
        # type (str, dict) -> None
        """Updates the meta data on an entry in the cache"""
        directives = self._parse_cache_control(headers.get("cache-control"))
        query = "UPDATE data SET http_date=?, age=?, expires=?, last_modified=?, max_age=? WHERE uri=?"
        values = (
            httpdate_to_datetime(headers.get("date")),
            headers.get("age"),
            httpdate_to_datetime(headers.get("expires")),
            httpdate_to_datetime(headers.get("last-modified")),
            directives.get("max-age"),
            uri)
        self._execute(query, values)

    def delete(self, uri):
        # type (str) -> None
        """Remove an entry from the cache via uri"""
        query = "DELETE FROM data WHERE uri=?"
        self._execute(query, (uri,))

    def domain(self, domain, limit=25):
        # type (str, int) -> list
        """Get items where uri like %domain%"""
        query = "select * from data where uri like ? order by http_date limit ?"
        cursor = self._execute(query, ('%{}%'.format(domain), limit))
        return [] if cursor is None else cursor.fetchall()

    def clear(self):
        # type: () -> None
        """Truncates the cache data and vacuums"""
        self._execute("DELETE FROM data")
        self._execute("VACUUM")

    @staticmethod
    def _parse_cache_control(header):
        # type: (str) -> dict
        # format: https://tools.ietf.org/html/rfc7234#section-5.2
        if header is None:
            return {}
        return {
            parts[0].strip():
                [int(parts[1]) if len(parts) > 1 else True][0]
            for directive in header.split(",")
            for parts in [directive.split("=")]
        }

    @staticmethod
    def _row_factory(cursor, row):
        # type: (sqlite3.Cursor, tuple) -> dict
        """Alternative row format as opposed to tuple or (Cache default) sqlite3.Row"""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def _execute(self, query, values=None):
        # type (str, tuple) -> sqlite3.cursor
        if values is None:
            values = ()
        try:
            # Automatically commits or rolls back on exception
            with self.connection:
                return self.connection.execute(query, values)
        except (sqlite3.IntegrityError, sqlite3.OperationalError) as e:
            logger.debug(e.message)
            return

    def _open(self, name):
        # type: (str) -> None
        sqlite3.enable_callback_tracebacks(True)
        sqlite3.register_converter("BLOB", Blob.deserialise)
        try:
            self.connection = sqlite3.connect(name,
                                              timeout=1,
                                              detect_types=sqlite3.PARSE_DECLTYPES)
        except sqlite3.Error as e:
            logger.debug(e.message)
            return
        # see: https://docs.python.org/2/library/sqlite3.html#sqlite3.Connection.row_factory
        self.connection.row_factory = sqlite3.Row
        self.connection.text_factory = sqlite3.OptimizedUnicode
        self._create_table()

    def _close(self):
        # type: () -> None
        """Closes any open connection and cursor"""
        if self.connection:
            self.connection.cursor().close()
            self.connection.close()

    def _create_table(self):
        # type: () -> None
        data = ("CREATE TABLE IF NOT EXISTS data ("
                "uri TEXT PRIMARY KEY NOT NULL,"
                "blob BLOB NOT NULL,"
                "http_date TIMESTAMP NOT NULL,"
                "age INTEGER DEFAULT 0,"
                "etag TEXT,"
                "expires TIMESTAMP,"
                "last_modified TIMESTAMP,"
                "max_age INTEGER,"
                "immutable INTEGER DEFAULT 0"
                ")")
        self._execute(data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._close()
