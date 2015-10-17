'''
    qobuz.node.favoritess
    ~~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from inode import INode
from gui.util import lang, getImage
from node import getNode, Flag


class Node_favorites(INode):
    """Our root node, we are displaying all qobuz nodes from here
    """

    def __init__(self, parent=None, parameters=None):
        super(Node_favorites, self).__init__(parent, parameters)
        self.nt = Flag.FAVORITES
        self.label = lang(30081)
        self.content_type = 'files'
        self.image = getImage('album')

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        for kind in ['all', 'albums', 'tracks', 'artists']:
            self.add_child(getNode(Flag.FAVORITE, {'search-type': kind}))
        return True
