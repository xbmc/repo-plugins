'''
    qobuz.dog
    ~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import re


class dog():
    '''Checking script parameter against regular expression
    '''

    def __init__(self):
        self.allowed_keys = {
            'mode': '^\d{1,10}$',  # Mode View/Scan/BigDir ...
            'nid':  '^\w{1,14}$',  # Node id (node.nid)
            'nt':   '^\d{1,10}$',  # Node type (node.type)
            'qnt':  '^\d{1,20}$',  # Node type in query
            'qid':  '^\w{1,14}$',  # Node id in query
            'nm': "^[\w\d_]+$",    # Method to be called on node
            'genre-type': '^(\d+|null)$',  # Reco params
            'genre-id': '^(\d+|null)$',    # Reco params
            'search-type': "^(artists|tracks|albums|articles|all)$",
            'depth': "^(-)?\d+$",
            'query': "^.*$",
            'track-id': "^\w{1,10}$",
            'parent-id': "^\w{1,10}$",
            'offset': "^\d{1,10}$",
            'source': '^(all|playlists|purchases|favorites)$'
        }

    def kv_is_ok(self, key, value):
        if key not in self.allowed_keys:
            return False
        match = None
        try:
            match = re.match(self.allowed_keys[key], value)
        except:
            pass
        if not match:
            return False
        return True
