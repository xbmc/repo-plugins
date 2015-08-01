__author__ = 'bromix'

import hashlib

from . import utils


def create_item_hash(item):
    m = hashlib.md5()
    m.update(utils.strings.to_utf8(item['uri']))
    return m.hexdigest()


def create_next_page_item(context, thumbnail=None, fanart=None):
    if not fanart:
        fanart = context.get_fanart()
        pass
    page = int(context.get_param('page', 1)) + 1

    new_params = {}
    new_params.update(context.get_params())
    new_params['page'] = unicode(page)

    title = context.localize(30106)
    if title.find('%d') != -1:
        title %= page
        pass

    return {'type': 'folder',
            'title': title,
            'uri': context.create_uri(context.get_path(), new_params),
            'images': {'thumbnail': thumbnail,
                       'fanart': fanart}}


def create_search_item(context, thumbnail=None, fanart=None):
    if not thumbnail:
        thumbnail = context.create_resource_path('media/search.png')
        pass
    if not fanart:
        fanart = context.get_fanart()
        pass

    uri = context.create_uri('search/list')
    if context.get_search_history().get_max_item_count() == 0:
        uri = context.create_uri('search/query')
        pass

    return {'type': 'folder',
            'title': context.localize(30102),
            'uri': uri,
            'images': {'thumbnail': thumbnail,
                       'fanart': fanart}}


def create_watch_later_item(context, thumbnail=None, fanart=None):
    if not thumbnail:
        thumbnail = context.create_resource_path('media/watch_later.png')
        pass
    if not fanart:
        fanart = context.get_fanart()
        pass
    return {'type': 'folder',
            'title': context.localize(30107),
            'uri': context.create_uri('watch_later/list'),
            'images': {'thumbnail': thumbnail,
                       'fanart': fanart}}