'''
    qobuz.node.search
    ~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from debug import warn
from inode import INode
from exception import QobuzXbmcError
from gui.util import lang, getImage, getSetting
from api import api
from node import getNode, Flag


class Node_search(INode):

    def __init__(self, parent=None, parameters=None):
        super(Node_search, self).__init__(parent, parameters)
        self.nt = Flag.SEARCH
        self.search_type = self.get_parameter('search-type') or 'albums'
        self.query = self.get_parameter('query', unQuote=True)
        self.offset = self.get_parameter('offset') or 0

    def get_label(self):
        return self.label

    def get_description(self):
        return self.get_label()

    @property
    def search_type(self):
        """Property / search_type
        """
        return self._search_type

    @search_type.setter
    def search_type(self, st):
        if st == 'artists':
            self.label = lang(30017)
            self.content_type = 'files'
            self.image = getImage('artist')
        elif st == 'albums':
            self.label = lang(30016)
            self.content_type = 'albums'
            self.image = getImage('album')
        elif st == 'tracks':
            self.label = lang(30015)
            self.content_type = 'songs'
            self.image = getImage('song')
        elif st == 'collection':
            self.label = lang(30018)
            self.content_type = 'files'
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

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
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
        data = api.get('/search/getResults', query=query, type=stype,
                       limit=limit, offset=self.offset)
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

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        if self.search_type == 'albums':
            for album in self.data['albums']['items']:
                node = getNode(Flag.ALBUM)
                node.data = album
                self.add_child(node)
        elif self.search_type == 'tracks':
            for track in self.data['tracks']['items']:
                node = getNode(Flag.TRACK)
                node.data = track
                self.add_child(node)
        elif self.search_type == 'artists':
            for artist in self.data['artists']['items']:
                node = getNode(Flag.ARTIST)
                node.data = artist
                self.add_child(node)
        return True
