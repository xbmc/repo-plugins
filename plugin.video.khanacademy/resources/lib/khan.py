'''
    resources.lib.khan
    ~~~~~~~~~~~~~~~~~~~

    This module interfaces with the remote Khan Academy API.

    :copyright: (c) 2013 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''

import requests
import collections


API_URL = 'http://www.khanacademy.org/api/v1/topictree'


def _video(item):
    '''Returns a video dict of values parsed from the json dict.'''
    return {
        'title': item['title'],
        'description': item['description'],
        'thumbnail': (item['download_urls'] or {}).get('png'),
        'youtube_id': item['youtube_id'],
        'mp4_url': (item['download_urls'] or {}).get('mp4'),
    }


def _topic(item):
    '''Returns a topic dict of values parsed from the json dict.'''
    return {
        'id': item['id'],
        'title': item['title'],
    }


_KINDS = {
    'Topic': _topic,
    'Video': _video,
}


def _flatten(item):
    '''Returns a new dict which is a flattened version of the provided item.
    The provided item can have an arbitrary depth, since each item can possibly
    have a 'children' entry. Since all items have unique ids, this method
    creates a flat dictionary, where the key is each item's unique id and the
    value is the item's children if present.

    >>> item = {
    ...     'id': 'root',
    ...     'children': [
    ...         {
    ...             'id': 'Algebra',
    ...              'children': [
    ...                 { 'id': 'Lesson 1'},
    ...                 { 'id': 'Lesson 2'},
    ...              ],
    ...         },
    ...         {
    ...              'id': 'Calculus',
    ...         },
    ...     ]
    ... }
    >>> _flatten(item).keys()
    ['root', 'Algebra']
    '''
    tree = collections.defaultdict(list)
    queue = [(child, 'root') for child in item['children']]
    while queue:
        item, parent_id = queue.pop(0)
        tree[parent_id].append(item)
        if 'children' in item.keys():
            current_id = item['id']
            queue.extend((child, current_id) for child in item['children'])
    return tree


def load_topic_tree():
    '''The main entry point for this module. Returns a dict keyed by Topic id.
    The value of the dict is the topic's children which are either topic dicts
    or video dicts. To hierarchichally descend through topics, start with the
    key 'root', and then look up each child topic's 'id' in this tree to get
    its children.
    '''
    _json = requests.get(API_URL).json()
    flattened = _flatten(_json)

    tree = {}
    for item_id, children in flattened.items():
        tree[item_id] = [_KINDS[child['kind']](child) for child in children
                         if child['kind'] in _KINDS.keys()]

    return tree
