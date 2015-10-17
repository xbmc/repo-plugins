'''
    qobuz.node.collection
    ~~~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from inode import INode
from node import Flag, getNode
from api import api
from debug import info
from gui.util import getImage, getSetting, lang


dialogHeading = 'Qobuz collection'


class Node_collection(INode):
    """@class Node_collection:
    """

    def __init__(self, parent=None, parameters=None):
        super(Node_collection, self).__init__(parent, parameters)
        self.nt = Flag.COLLECTION
        self.url = None
        self.is_folder = True
        self.image = getImage('songs')
        self.search_type = self.get_parameter('search-type', default='tracks')
        self.query = self.get_parameter('query', unQuote=True)
        self.offset = self.get_parameter('offset') or 0
        self.source = self.get_parameter('source')
        self.seen_artist = {}
        self.seen_album = {}
        self.seen_track = {}
        self.data = None
        self.label = '%s - %s' % (lang(30194),  self.search_type.capitalize())

    def make_url(self, **ka):
        url = super(Node_collection, self).make_url(**ka)
        if self.search_type:
            url += '&search-type=' + str(self.search_type)
        return url

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit', isInt=True)
        self.data = None
        query = self.query
        if not query:
            from gui.util import Keyboard
            k = Keyboard('', 'My %s' % self.search_type)
            k.doModal()
            if not k.isConfirmed():
                return False
            query = k.getText()
        query.strip()
        info(self, 'search_type: %s, query: %s' % (self.search_type, query))
        source = self.source
        kwargs = {'query': query,
                  'limit': limit,
                  }
        if source is not None:
            kwargs['source'] = source
        data = None
        if self.search_type == 'albums':
            data = api.get('/collection/getAlbums', **kwargs)
        elif self.search_type == 'artists':
            data = api.get('/collection/getArtists', **kwargs)
        elif self.search_type == 'tracks':
            data = api.get('/collection/getTracks', **kwargs)
        if data is None:
            return False
        self.data = data
        return True

    def get_description(self):
        return None

    def _populate_albums(self, data):
        """helper"""
        node = getNode(Flag.ALBUM)
        node.data = data
        self.add_child(node)
        return True

    def _populate_tracks(self, data):
        """helper"""
        node = getNode(Flag.TRACK)
        node.data = data
        self.add_child(node)
        return True

    def _populate_artists(self, data):
        """helper"""
        node = getNode(Flag.ARTIST)
        node.data = data
        self.add_child(node)
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        if self.data is None:
            return False
        # Call helper method on each item
        method = getattr(self, '_populate_%s' % self.search_type)
        for item in self.data['items']:
            method(item)
        return True
