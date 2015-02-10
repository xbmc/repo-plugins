'''
    qobuz.node.public_playlists
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from node import Flag, getNode
from inode import INode
from gui.util import lang, getImage, getSetting
from api import api

class Node_public_playlists(INode):
    '''
    @class Node_public_playlists
    '''
    def __init__(self, parent=None, parameters=None):
        super(Node_public_playlists, self).__init__(parent, parameters)
        self.nt = Flag.PUBLIC_PLAYLISTS
        self.set_label(lang(42102))
        self.is_folder = True
        self.image = getImage('userplaylists')
        self.offset = self.get_parameter('offset') or 0

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = api.get('/playlist/getPublicPlaylists', offset=self.offset, 
                       limit=limit, type='last-created')
        if not data:
            return False
        # @bug: we use pagination_limit as limit for the search so we don't 
        # need offset... (Fixed if qobuz fix it :p)
        if not 'total' in data['playlists']:
            data['playlists']['total'] = data['playlists']['limit']
        self.data = data
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        for item in self.data['playlists']['items']:
            node = getNode(Flag.PLAYLIST)
            node.data = item
            self.add_child(node)
        return True
