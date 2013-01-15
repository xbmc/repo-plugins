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
import xbmcgui
import xbmc

import qobuz
from flag import NodeFlag
from inode import INode
from debug import log, warn
from gui.util import getImage, getSetting, lang

'''
    @class Node_label:
'''


class Node_label(INode):

    def __init__(self, parent=None, parameters=None, progress=None):
        super(Node_label, self).__init__(parent, parameters)
        self.type = NodeFlag.LABEL
        self.set_label(lang(42100))
        self.url = None
        self.is_folder = True
        self.image = getImage('album')

    def hook_post_data(self):
        self.label = self.get_property('name')
        self.id = self.get_property('id')

    def _build_down(self, xbmc_directory, lvl, whiteFlag, blackFlag):
        offset = self.get_parameter('offset') or 0
        #@bug: Qobuz service seam do don't return total so pagination is broken
        limit = getSetting('pagination_limit')
        data = qobuz.registry.get(
            name='label-list', id=self.id, limit=limit, offset=offset)
        if not data:
            warn(self, "No label data")
            return False
        for item in data['data']['labels']['items']:
            node = Node_label()
            node.data = item
            self.add_child(node)
        return True
