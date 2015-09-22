__author__ = 'bromix'

import os
import datetime

from .storage import Storage
from ..items import create_item_hash
from .watch_later_list_v2 import WatchLaterListV2


class WatchLaterListV3(Storage):
    def __init__(self, filename):
        Storage.__init__(self, filename + '.v3')

        self._convert(filename)
        pass

    def _convert(self, filename):
        v2 = WatchLaterListV2(filename)
        if os.path.exists(v2.get_filename()):
            v2_items = v2.list()
            for v2_item in v2_items:
                v3_item = {'type': 'video',
                           'title': v2_item['data']['_name'],
                           'plot': v2_item['data']['_plot'],
                           'published': v2_item['data']['_premiered'],
                           'duration': v2_item['data'].get('_duration', None),
                           'season': v2_item['data'].get('_season', None),
                           'episode': v2_item['data'].get('_episode', None),
                           'uri': v2_item['data']['_uri'],
                           'images': {'fanart': v2_item['data']['_fanart'],
                                      'thumbnail': v2_item['data']['_image']}}
                self.add(v3_item)
                pass

            v2.clear()
            v2._close()
            os.remove(v2.get_filename())
            pass
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
            return video_item['date']

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
