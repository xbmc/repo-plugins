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
import qobuz

from debug import warn
from flag import NodeFlag
from inode import INode
from product import Node_product
from track import Node_track
from product_by_artist import Node_product_by_artist
from exception import QobuzXbmcError
from gui.util import notifyH, lang, getImage, getSetting
import urllib
from api import api

class Node_search(INode):

    def __init__(self, parent=None, params=None):
        super(Node_search, self).__init__(parent, params)
        self.type = NodeFlag.SEARCH
        self.search_type = self.get_parameter('search-type') or 'albums'
        self.query = self.get_parameter('query', unQuote=True)
        self.offset = self.get_parameter('offset') or 0

    def get_label(self):
        return self.label

    def get_description(self):
        return self.get_label()

    ''' Property / search_type '''
    @property
    def search_type(self):
        return self._search_type

    @search_type.setter
    def search_type(self, st):
        if st == 'artists':
            self.label = lang(30015)
            self.content_type = 'files'
            self.image = getImage('artist')
        elif st == 'albums':
            self.label = lang(30014)
            self.content_type = 'albums'
            self.image = getImage('album')
        elif st == 'tracks':
            self.label = lang(30013)
            self.content_type = 'songs'
            self.image = getImage('song')
        else:
            raise QobuzXbmcError(who=self, what='invalid_type', additional=st)
        self._search_type = st

    @search_type.getter
    def search_type(self):
        return self._search_type

    def make_url(self, **ka):
        url = super(Node_search, self).make_url(**ka)
        url += '&search-type=' + self.search_type
        if self.query:
            url += '&query=' + self.query
        return url

    def pre_build_down(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        stype = self.search_type
        query = self.get_parameter('query', unQuote=True)
        if not query:
            from gui.util import Keyboard
            k = Keyboard('', stype)
            k.doModal()
            if not k.isConfirmed():
                return False
            query = k.getText()
        query.strip()
        data = api.search_getResults(
            query=query, type=stype, limit=limit, offset=self.offset)
        if not data:
            warn(self, "Search return no data")
            return False
        if data[stype]['total'] == 0:
            return False
        if not 'items' in data[stype]:
            return False
        self.set_parameter('query', query, quote=True)
        self.data = data
        return True
    
    def _build_down(self, Dir, lvl, whiteFlag, blackFlag):
        if self.search_type == 'albums':
            for album in self.data['albums']['items']:
                node= Node_product()
                node.data = album
                self.add_child(node)
        elif self.search_type == 'tracks':
            for track in self.data['tracks']['items']:
                node = Node_track()
                node.data = track
                self.add_child(node)
        elif self.search_type == 'artists':
            for artist in self.data['artists']['items']:
                node = Node_product_by_artist()
                node.data = artist
                self.add_child(node)
        return True
