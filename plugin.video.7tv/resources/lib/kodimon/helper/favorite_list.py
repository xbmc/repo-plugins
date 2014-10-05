__author__ = 'bromix'

from storage import Storage


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
            item = self._get(key)
            if item is not None:
                result.append(item[0])
            pass

        from .. import sort_items_by_name
        return sort_items_by_name(result)

    def add(self, base_item):
        self._set(base_item.get_id(), base_item)
        pass

    def remove(self, base_item):
        self._remove(base_item.get_id())
        pass