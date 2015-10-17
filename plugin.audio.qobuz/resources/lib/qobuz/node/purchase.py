'''
    qobuz.node.purchase
    ~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from inode import INode
from debug import warn
from api import api
from node import Flag, getNode
from gui.util import lang, getImage, getSetting


class Node_purchase(INode):
    """Displaying product purchased by user (track and album)
    """

    def __init__(self, parent=None, parameters=None):
        super(Node_purchase, self).__init__(parent, parameters)
        self.nt = Flag.PURCHASE
        self.content_type = 'albums'
        self.image = getImage('album')
        self.search_type = self.get_parameter('search-type') or 'all'
        self.offset = self.get_parameter('offset') or 0
        if self.search_type == 'all':
            self.label = '%s - %s' % (lang(30101), lang(30098))
        else:
            self.label = '%s - %s' % (lang(30101),
                                      self.search_type.capitalize())

    def make_url(self, **ka):
        url = super(Node_purchase, self).make_url(**ka)
        if self.search_type:
            url += '&search-type=' + str(self.search_type)
        return url

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = api.get('/purchase/getUserPurchases', limit=limit,
                       offset=self.offset, user_id=api.user_id)
        if not data:
            warn(self, "Cannot fetch purchases data")
            return False
        self.data = data
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        wanted = ['albums', 'tracks']
        if self.search_type != 'all':
            wanted = [self.search_type]
        ret = False
        for kind in wanted:
            method = '_populate_%s' % kind
            if not hasattr(self, method):
                warn(self, "No method named %s" % method)
                continue
            if getattr(self, method)(Dir, lvl, whiteFlag, blackFlag):
                ret = True
        return ret

    def _populate_albums(self, Dir, lvl, whiteFlag, blackFlag):
        ret = False
        for album in self.data['albums']['items']:
            node = getNode(Flag.ALBUM)
            node.data = album
            self.add_child(node)
            ret = True
        return ret

    def _populate_tracks(self, Dir, lvl, whiteFlag, blackFlag):
        ret = False
        for track in self.data['tracks']['items']:
            node = getNode(Flag.TRACK)
            node.data = track
            self.add_child(node)
            ret = True
        return ret
