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
        from .. import json_to_item
        result = []

        for key in self._get_ids():
            data = self._get(key)
            item = json_to_item(data[0])
            result.append(item)
            pass

        from .. import sort_items_by_name
        return sort_items_by_name(result)

    def add(self, base_item):
        from .. import item_to_json
        item_json_data = item_to_json(base_item)
        self._set(base_item.get_id(), item_json_data)
        pass

    def remove(self, base_item):
        self._remove(base_item.get_id())
        pass