__author__ = 'bromix'

import datetime

from .storage import Storage
from ..items import create_item_hash


class WatchLaterListV2(Storage):
    def __init__(self, filename):
        Storage.__init__(self, filename)
        pass

    def clear(self):
        self._clear()
        pass

    def list(self):
        result = []

        for key in self._get_ids():
            data = self._get(key)
            item = data[0]
            result.append(item)
            pass

        def _sort(video_item):
            return video_item['data']['_date']

        self.sync()

        sorted_list = sorted(result, key=_sort, reverse=False)
        return sorted_list

    def add(self, item):
        item['date'] = str(datetime.datetime.now())
        item_hash = create_item_hash(item)
        self._set(item_hash, item)
        pass

    def remove(self, item):
        item_hash = create_item_hash(item)
        self._remove(item_hash)
        pass