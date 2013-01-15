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
#import xbmcgui

import qobuz

from flag import NodeFlag as Flag
from inode import INode
from artist import Node_artist
from gui.util import lang, getSetting

'''
    NODE ARTIST
'''

class Node_similar_artist(INode):

    def __init__(self, parent=None, parameters=None):
        super(Node_similar_artist, self).__init__(parent, parameters)
        self.type = Flag.SIMILAR_ARTIST
        self.content_type = 'artists'
        self.offset = self.get_parameter('offset') or 0

    def get_label(self):
        return lang(39000)

    def pre_build_down(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = qobuz.registry.get(name='artist-similar', id=self.id,
            artist_id=self.id, offset=self.offset, limit=limit)
        if not data:
            return False
        self.data = data['data']
        return len(data['data']['artists']['items'])

    def _build_down(self, Dir, lvl, whiteflag, blackFlag):
        for aData in self.data['artists']['items']:
            artist = Node_artist(self, {'offset': 0, 'nid': aData['id']})
            artist.data = aData
            self.add_child(artist)
        return True
