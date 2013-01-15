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

import qobuz
from flag import NodeFlag
from inode import INode
from product import Node_product
from debug import warn
from gui.util import getSetting
from gui.contextmenu import contextMenu
import xbmcgui

'''
    @class Node_artist(Inode): Artist
'''

class Node_artist(INode):

    def __init__(self, parent=None, parameters=None, progress=None):
        super(Node_artist, self).__init__(parent, parameters)
        self.type = NodeFlag.ARTIST
        self.set_label(self.get_name())
        self.is_folder = True
        self.slug = ''
        self.content_type = 'albums'
        self.offset = self.get_parameter('offset') or 0
        
    def hook_post_data(self):
        self.name = self.get_property('name')
        self.image = self.get_image()
        self.slug = self.get_property('slug')
        self.label = self.name
        
    def pre_build_down(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = qobuz.registry.get(name='artist',id=self.id,
            artist_id=self.id, limit=limit, offset=self.offset, extra='albums')
        if not data:
            warn(self, "Build-down: Cannot fetch artist data")
            return False
        self.data = data['data']
        return True
    
    def _build_down(self, Dir, lvl, whiteFlag, blackFlag):
        node_artist = Node_artist()
        node_artist.data = self.data
        node_artist.label = '[ %s ]' % (node_artist.label)
        if not 'albums' in self.data: 
            return True
        for pData in self.data['albums']['items']:
            node = Node_product()
            node.data = pData
            self.add_child(node)
        return True

        del self._data['tracks']

    def get_artist_id(self):
        return self.id

    def get_image(self):
        image = self.get_property(['image/extralarge', 
                                   'image/mega', 
                                   'picture'])
        if image: 
            image = image.replace('126s', '_')
        return image
    
    def get_title(self):
        return self.get_name()
    
    def get_artist(self):
        return self.get_name()
    
    def get_name(self):
        return self.get_property('name')

    def get_owner(self):
        return self.get_property('owner/name')

    def get_description(self):
        return self.get_property('description')

    def makeListItem(self, replaceItems=False):
        image = self.get_image()
        url = self.make_url()
        name = self.get_label()
        item = xbmcgui.ListItem(name,
                                name,
                                image,
                                image,
                                url)
#        item.setInfo('music', {
#                    'artist': self.get_label(),
#        })
        if not item:
            warn(self, "Error: Cannot make xbmc list item")
            return None
        item.setPath(url)
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), replaceItems)
        return item
