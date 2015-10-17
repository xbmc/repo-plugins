'''
    qobuz.node.purchases
    ~~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from inode import INode
from gui.util import lang, getImage
from node import getNode, Flag


class Node_purchases(INode):
    """Our root node, we are displaying all qobuz nodes from here
    """

    def __init__(self, parent=None, parameters=None):
        super(Node_purchases, self).__init__(parent, parameters)
        self.nt = Flag.PURCHASES
        self.label = lang(30101)
        self.content_type = 'files'
        self.image = getImage('album')

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        for kind in ['all', 'albums', 'tracks']:
            self.add_child(getNode(Flag.PURCHASE, {'search-type': kind}))
        return True
