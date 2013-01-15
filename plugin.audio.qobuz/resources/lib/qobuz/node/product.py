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
from flag import NodeFlag as Flag
from inode import INode
from debug import warn
from gui.util import getImage, getSetting
from gui.contextmenu import contextMenu

'''
    @class Node_product:
'''

from track import Node_track

SPECIAL_PURCHASES = ['0000020110926', '0000201011300', '0000020120220',
                     '0000020120221']


class Node_product(INode):

    def __init__(self, parent=None, params=None):
        super(Node_product, self).__init__(parent, params)
        self.type = Flag.PRODUCT
        self.image = getImage('album')
        self.content_type = 'songs'
        self.is_special_purchase = False
        self.offset = None
        self.imageDefaultSize = 'large'
        self.label = 'Album'
        try:
            self.imageDefaultSize = getSetting('image_default_size')
        except:
            pass

    def pre_build_down(self, Dir, lvl, whiteFlag, blackFlag):
        data = None
        if self.is_special_purchase:
            data = qobuz.registry.get(name='purchase', id=self.id)
        else:
            data = qobuz.registry.get(name='product', id=self.id)
        if not data:
            warn(self, "Cannot fetch product data")
            return False
        self.data = data['data']
        return True
    
    def _build_down(self, Dir, lvl, whiteFlag, blackFlag):
        for track in self.data['tracks']['items']:
            node = Node_track()
            if not 'image' in track:
                track['image'] = self.get_image()
            node.data = track
            
            self.add_child(node)
        return len(self.data['tracks']['items'])

    def make_url(self, **ka):
        if 'asLocalURL' in ka and ka['asLocalURL']:
            from constants import Mode
            ka['mode'] = Mode.SCAN
        return super(Node_product, self).make_url(**ka)
    
    def makeListItem(self, replaceItems=False):
        import xbmc, xbmcgui
        image = self.get_image()
        thumb = xbmc.getCacheThumbName(image)
        item = xbmcgui.ListItem(
            label=self.get_label(),
            label2=self.get_label(),
            iconImage=image,
            thumbnailImage=image,
            path=self.make_url(),
        )
        item.setInfo('music', infoLabels={
            'genre': self.get_genre(),
            'year': self.get_year(),
            'artist': self.get_artist(),
            'title': self.get_title(),
            'album': self.get_title(),
        })
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), replaceItems)
        return item

    '''
    PROPERTIES
    '''
    def get_artist(self):
        return self.get_property(['artist/name',
                               'interpreter/name', 
                               'composer/name'])

    def get_album(self):
        album = self.get_property('name')
        if not album:
            return ''
        return album

    def get_artist_id(self):
        a = self.get_property(['artist/id',
                               'interpreter/id',
                              'composer/id'])
        if a:
            return int(a)
        return ''

    def get_title(self):
        return self.get_property('title')

    def get_image(self, size = None):
        if not size:
            size = self.imageDefaultSize
        return self.get_property(['image/%s' % (size),
                                   'image/large', 
                                   'image/small',
                                   'image/thumbnail'])

    def get_label(self):
        artist = self.get_artist() or 'VA'
        label = '%s - %s' % (artist, self.get_title())
        return label

    def get_genre(self):
        return self.get_property('genre/name')

    def get_year(self):
        import time
        date = self.get_property('released_at')
        year = 0
        try:
            year = time.strftime("%Y", time.localtime(date))
        except:
            pass
        return year

    def get_description(self):
        return self.get_property('description')
