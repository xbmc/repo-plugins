import datetime
from storage import Storage


class SearchHistory(Storage):
    def __init__(self, filename, max_items=10):
        Storage.__init__(self, filename, max_item_count=max_items)
        pass

    def is_empty(self):
        return self._is_empty()

    def list(self):
        result = []

        for key in self._get_ids():
            item = self._get(key)
            if item is not None:
                result.append(item[0])
            pass

        from .. import sort_items_by_info_label, BaseItem
        return sort_items_by_info_label(result, BaseItem.INFO_DATEADDED, True)

    def clear(self):
        self._clear()

    def remove(self, base_item):
        self._remove(base_item.get_id())
        pass

    def update(self, base_item):
        now = datetime.datetime.now()
        base_item.set_date_added(now.year, now.month, now.day, now.hour, now.minute, now.second)
        self._set(base_item.get_id(), base_item)
        pass

    pass