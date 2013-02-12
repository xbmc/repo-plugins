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
from node import getNode, Flag
from gui.util import lang, getSetting
from api import api

'''
    NODE ARTIST
'''

class Node_similar_artist(INode):

    def __init__(self, parent=None, parameters=None):
        super(Node_similar_artist, self).__init__(parent, parameters)
        self.nt = Flag.SIMILAR_ARTIST
        self.content_type = 'artists'
        self.offset = self.get_parameter('offset') or 0

    def get_label(self):
        return lang(39000)

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = api.get('/artist/getSimilarArtists', artist_id=self.nid, 
                           offset=self.offset, limit=limit)
        if not data:
            return False
        self.data = data
        return len(data['artists']['items'])

    def populate(self, Dir, lvl, whiteflag, blackFlag):
        for aData in self.data['artists']['items']:
            artist = getNode(Flag.ARTIST, {'offset': 0, 'nid': aData['id']})
            artist.data = aData
            self.add_child(artist)
        return True
