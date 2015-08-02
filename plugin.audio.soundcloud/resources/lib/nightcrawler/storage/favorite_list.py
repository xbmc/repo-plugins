__author__ = 'bromix'

from .storage import Storage
from ..items import create_item_hash


class FavoriteList(Storage):
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

        def _sort(_item):
            return _item['title'].upper()

        return sorted(result, key=_sort, reverse=False)

    def add(self, item):
        item_hash = create_item_hash(item)
        self._set(item_hash, item)
        pass

    def remove(self, item):
        item_hash = create_item_hash(item)
        self._remove(item_hash)
        pass