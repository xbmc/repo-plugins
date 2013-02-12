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
from inode import INode
from gui.util import getImage, getSetting, lang
from api import api
from node import Flag, getNode
from node.recommendation import RECOS_TYPE_IDS

class Node_genre(INode):
    '''
    @class Node_genre:
    '''
    def __init__(self, parent=None, parameters=None):
        super(Node_genre, self).__init__(parent, parameters)
        self.nt = Flag.GENRE
        self.set_label(lang(42101))
        self.is_folder = True
        self.image = getImage('album')
        self.offset = self.get_parameter('offset') or 0
        
    def make_url(self, **ka):
        url = super(Node_genre, self).make_url(**ka)
        if self.parent and self.parent.nid:
            url += "&parent-id=" + self.parent.nid
        return url

    def hook_post_data(self):
        self.label = self.get_property('name')

    def get_name(self):
        return self.get_property('name')

    def populate_reco(self, Dir, lvl, whiteFlag, blackFlag, ID):
        for gtype in RECOS_TYPE_IDS:
            node = getNode(
                Flag.RECOMMENDATION, {'parent': self, 'genre-id': ID, 'genre-type': gtype})
            node.populating(Dir, 1, Flag.ALBUM, blackFlag)
        return True

    def fetch(self, Dir, lvl , whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = api.get('/genre/list', parent_id=self.nid, offset=self.offset, 
                       limit=limit)
        if not data: 
            self.data = None
            return True # Nothing return trigger reco build in build_down
        self.data = data
        g = self.data['genres']
        if 'parent' in g and int(g['parent']['level']) > 1:
            self.populate_reco(Dir, lvl, whiteFlag, blackFlag, 
                                  g['parent']['id'])
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        if not self.data or len(self.data['genres']['items']) == 0:
            return self.populate_reco(Dir, lvl, 
                                         whiteFlag, blackFlag, self.nid)
        for genre in self.data['genres']['items']:
            node = Node_genre(self, {'nid': genre['id']})
            node.data = genre
            self.add_child(node)
        return True
