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

from flag import NodeFlag
from inode import INode
from product import Node_product
from debug import warn
import weakref
from api import api
from gui.contextmenu import contextMenu
from gui.util import getSetting

'''
    @class Node_product_by_artist:
'''

class Node_product_by_artist(INode):

    def __init__(self, parent=None, parameters=None):
        super(Node_product_by_artist, self).__init__(parent, parameters)
        self.type = NodeFlag.ARTIST
        self.content_type = 'albums'
        self.offset = self.get_parameter('offset') or 0
    '''
        Getter
    '''
    def get_label(self):
        return self.get_artist()

    def get_image(self):
        image = self.get_property('picture')
        # get max size image from lastfm, Qobuz default is a crappy 126p large one
        # perhaps we need a setting for low bw users
        image = image.replace('126s', '_')
        return image

    def get_artist(self):
        return self.get_property('name')

    def get_slug(self):
        return self.get_property('slug')

    def get_artist_id(self):
        return self.id

    '''
        Build Down
    '''
    def pre_build_down(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = api.artist_get(
            artist_id=self.id, limit=limit, offset=self.offset, extra='albums')
        if not data:
            warn(self, "Cannot fetch albums for artist: " + self.get_label())
            return False
        self.data = data
        return True
    
    def _build_down(self, Dir, lvl, whiteFlag, blackFlag):
        count = 0
        total = len(self.data['albums']['items'])
        for album in self.data['albums']['items']:
            keys = ['artist', 'interpreter', 'composer', 'performer']
            for k in keys:
                try:
                    if k in self.data['artist']:
                        album[k] = weakref.proxy(self.data['artist'][k])
                except:
                    warn(self, "Strange thing happen")
                    pass
            node = Node_product()
            node.data = album
            count += 1
            Dir.update(count, total, "Add album:" + node.get_label(), '')
            self.add_child(node)
        return True

    '''
        Make XbmcListItem
    '''
    def makeListItem(self, replaceItems=False):
        item = xbmcgui.ListItem(self.get_label(),
                                self.get_label(),
                                self.get_image(),
                                self.get_image(),
                                self.make_url(),
                                )
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), replaceItems)
        return item
