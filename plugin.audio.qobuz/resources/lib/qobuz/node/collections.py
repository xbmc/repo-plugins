'''
    qobuz.node.collections
    ~~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from inode import INode
from gui.util import lang, getImage
from node import getNode, Flag


class Node_collections(INode):

    def __init__(self, parent=None, parameters=None):
        super(Node_collections, self).__init__(parent, parameters)
        self.nt = Flag.COLLECTIONS
        self.label = lang(30194)
        self.content_type = 'albums'
        self.image = getImage('album')

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        for kind in ['artists', 'albums', 'tracks']:
            self.add_child(getNode(Flag.COLLECTION, {'search-type': kind}))
        return True
