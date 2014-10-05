import os
import shelve
import time

__author__ = 'bromix'


class Storage(object):
    def __init__(self, filename, max_item_count=1000):
        self._filename = filename
        self._file = None
        self._max_item_count = max_item_count
        pass

    def __del__(self):
        if self._file is not None:
            self._file.sync()
            self._file.close()
            self._file = None
            pass
        pass

    def _open(self):
        if self._file is None:
            path = os.path.dirname(self._filename)
            if not os.path.exists(path):
                os.makedirs(path)
                pass

            self._file = shelve.open(self._filename, writeback=True)
        pass

    def sync(self):
        if self._file is not None:
            self._file.sync()
            pass
        pass

    def _set(self, item_id, item):
        self._open()
        now = time.time()
        self._file[item_id] = (item, now)
        self._optimize()
        pass

    def _optimize(self):
        def _sort(x):
            return x[1][1]

        try:
            if len(self._file) > self._max_item_count:
                cut_off = len(self._file) - self._max_item_count
                items = sorted(self._file.items(), key=_sort, reverse=False)

                for i in range(cut_off):
                    item = items[i]
                    self._remove(item[0])
                    pass
                pass
        except Exception, ex:
            self._reset("Failed to optimize", ex.__str__())
            pass
        pass

    def _clear(self):
        self._open()
        self._file.clear()
        pass

    def _is_empty(self):
        self._open()
        return len(self._file) == 0

    def _get_ids(self):
        self._open()
        return self._file.keys()

    def _get(self, item_id):
        self._open()
        try:
            # we check for tuple so old data will be discarded
            result = self._file.get(item_id, None)
            if isinstance(result, tuple):
                return result

            return None
        except Exception, ex:
            self._reset("Failed to load item with id '%s'" % item_id, ex.__str__())
            pass
        pass

    def _reset(self, text, cause):
        from .. import log, constants
        log("%s (%s)" % (text, cause), constants.LOG_ERROR)
        log("Resetting database...", constants.LOG_INFO)

        if self._file is not None:
            self._file.close()
            self._file = None
            pass

        if os.path.exists(self._filename):
            os.remove(self._filename)
            pass

        log("Resetting database...Done", constants.LOG_INFO)
        pass

    def _remove(self, item_id):
        self._open()
        if item_id in self._file:
            del self._file[item_id]
            pass
        pass

    pass