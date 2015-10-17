'''
    qobuz.node.label
    ~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from inode import INode
from debug import warn
from gui.util import getImage, getSetting, lang
from node import Flag
from api import api


class Node_label(INode):
    '''
    @class Node_label:
    '''

    def __init__(self, parent=None, parameters=None):
        super(Node_label, self).__init__(parent, parameters)
        self.nt = Flag.LABEL
        self.set_label(lang(30188))
        self.url = None
        self.is_folder = True
        self.image = getImage('album')

    def hook_post_data(self):
        self.label = self.get_property('name')
        self.nid = self.get_property('nid')

    def populate(self, xbmc_directory, lvl, whiteFlag, blackFlag):
        offset = self.get_parameter('offset') or 0
        #@bug: Qobuz service seam do don't return total so pagination is broken
        limit = getSetting('pagination_limit')
        data = api.get('/label/list', limit=limit, offset=offset)
        if not data:
            warn(self, "No label data")
            return False
        for item in data['labels']['items']:
            node = Node_label()
            node.data = item
            self.add_child(node)
        return True
