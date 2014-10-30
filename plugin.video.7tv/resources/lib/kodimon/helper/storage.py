import os
import sqlite3
import datetime

try:
    import cPickle as pickle
except ImportError:
    import pickle
    pass

__author__ = 'bromix'


class Storage(object):
    def __init__(self, filename, max_item_count=1000, max_file_size_kb=-1):
        self._tablename = 'storage'
        self._filename = filename
        if not self._filename.endswith('.sqlite'):
            self._filename = self._filename+'.sqlite'
            pass
        self._file = None
        self._cursor = None
        self._max_item_count = max_item_count
        self._max_file_size_kb = max_file_size_kb
        pass

    def set_max_item_count(self, max_item_count):
        self._max_item_count = max_item_count
        pass

    def set_max_file_size_kb(self, max_file_size_kb):
        self._max_file_size_kb = max_file_size_kb
        pass

    def __del__(self):
        self._close()
        pass

    def _open(self):
        if self._file is None:
            self._optimize_file_size()

            path = os.path.dirname(self._filename)
            if not os.path.exists(path):
                os.makedirs(path)
                pass

            self._file = sqlite3.connect(self._filename, detect_types=sqlite3.PARSE_DECLTYPES)
            self._cursor = self._file.cursor()
            self._create_table()
        pass

    def _close(self):
        if self._file is not None:
            self._file.commit()
            self._cursor.close()
            self._cursor = None
            self._file.close()
            self._file = None
            pass
        pass

    def _optimize_file_size(self):
        # do nothing - only we have given a size
        if self._max_file_size_kb <= 0:
            return

        # do nothing - only if this folder exists
        path = os.path.dirname(self._filename)
        if not os.path.exists(path):
            return

        if not os.path.exists(self._filename):
            return

        file_size_kb = os.path.getsize(self._filename) / 1024
        if file_size_kb >= self._max_file_size_kb:
            os.remove(self._filename)
            pass
        pass

    def _create_table(self):
        self._open()
        query = 'CREATE TABLE IF NOT EXISTS %s (key TEXT PRIMARY KEY, time TIMESTAMP, value BLOB)' % self._tablename
        self._cursor.execute(query)
        pass

    def sync(self):
        if self._file is not None:
            self._file.commit()
            pass
        pass

    def _set(self, item_id, item):
        def _encode(obj):
            return sqlite3.Binary(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))

        self._open()
        now = datetime.datetime.now()
        query = 'REPLACE INTO %s (key,time,value) VALUES(?,?,?)' % self._tablename
        self._cursor.execute(query, [item_id, now, _encode(item)])
        self._optimize_item_count()
        pass

    def _optimize_item_count(self):
        self._open()
        query = 'SELECT key FROM %s ORDER BY time LIMIT -1 OFFSET %d' % (self._tablename, self._max_item_count)
        result = self._cursor.execute(query)
        if result is not None:
            for item in result:
                self._remove(item[0])
                pass

            self.sync()
            pass
        pass

    def _clear(self):
        self._open()
        query = 'DELETE FROM %s' % self._tablename
        self._cursor.execute(query)
        self.sync()
        self._create_table()
        self.sync()
        pass

    def _is_empty(self):
        self._open()
        query = 'SELECT exists(SELECT 1 FROM %s LIMIT 1);' % self._tablename
        result = self._cursor.execute(query)
        for item in result:
            return item[0] == 0

        return False

    def _get_ids(self, oldest_first=True):
        self._open()
        query = 'SELECT key FROM %s' % self._tablename
        if oldest_first:
            query = '%s ORDER BY time ASC' % query
        else:
            query = '%s ORDER BY time DESC' % query
            pass

        query_result = self._cursor.execute(query)

        result = []
        for item in query_result:
            result.append(item[0])
            pass

        return result

    def _get(self, item_id):
        def _decode(obj):
            return pickle.loads(bytes(obj))

        self._open()
        query = 'SELECT time, value FROM %s WHERE key=?' % self._tablename
        result = self._cursor.execute(query, [item_id])
        if result is None:
            return None

        item = result.fetchone()
        if item is None:
            return None

        return _decode(item[1]), item[0]

    def _remove(self, item_id):
        self._open()
        query = 'DELETE FROM %s WHERE key = ?' % self._tablename
        self._cursor.execute(query, [item_id])
        pass

    pass