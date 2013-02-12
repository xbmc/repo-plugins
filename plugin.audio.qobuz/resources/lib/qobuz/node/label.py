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
        self.set_label(lang(42100))
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
