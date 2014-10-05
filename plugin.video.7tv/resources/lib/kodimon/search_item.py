import json

__author__ = 'bromix'

from directory_item import DirectoryItem


class SearchItem(DirectoryItem):
    def __init__(self, name, image=u'', search_type=None):
        from . import create_content_path, AbstractProvider, item_to_json

        DirectoryItem.__init__(self, name, create_content_path(AbstractProvider.PATH_SEARCH), image=image)

        # only create a clone of this item if use it to query, so the caller can extract this item of the param 'item'
        if search_type == 'query':
            self._params['item'] = json.dumps(item_to_json(self))
            pass

        self._path = create_content_path(AbstractProvider.PATH_SEARCH, search_type)
        pass

    pass
