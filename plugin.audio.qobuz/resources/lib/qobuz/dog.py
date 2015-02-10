#     Copyright 2011 Joachim Basmaison, Cyril Leclerc
#
#     This file is part of xbmc-qobuz.
#
#     xbmc-qobuz is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     xbmc-qobuz is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with xbmc-qobuz.   If not, see <http://www.gnu.org/licenses/>.
import re

class dog():
    '''Checking script parameter against regular expression
    '''
    def __init__(self):
        self.allowed_keys = {
            'mode': '^\d{1,10}$', # Mode View/Scan/BigDir ...
            'nid':  '^\d{1,14}$', # Node id (node.nid)
            'nt':   '^\d{1,10}$', # Node type (node.type)
            'qnt':  '^\d{1,20}$', # Node type in query
            'qid':  '^\d{1,14}$', # Node id in query
            'nm': "^[\w\d_]+$",   # Method to be called on node
            'genre-type': '^(\d+|null)$', # Reco params
            'genre-id': '^(\d+|null)$',   # Reco params
            'search-type': "^(artists|tracks|albums)$",
            'depth': "^(-)?\d+$",
            'query': "^.*$",
            'track-id': "^\d{1,10}$",
            'parent-id': "^\d{1,10}$",
            'offset': "^\d{1,10}$",
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
