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
from flag import NodeFlag as Flag
from inode import INode
from article import Node_article
from gui.util import getImage, getSetting

'''
    @class Node_articles
'''

class Node_articles(INode):

    def __init__(self, parent=None, parameters=None):
        super(Node_articles, self).__init__(parent, parameters)
        self.type = Flag.ARTICLES
        self.is_folder = True
        self.image = getImage('album')
        self.offset = self.get_parameter('offset') or 0

    
    def get_label(self):
        l = self.get_property('title')
        if not l: return "Articles"
        return l

    def pre_build_down(self, Dir, lvl , whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = qobuz.registry.get(name='article_listlastarticles',
                                      id=self.id, 
                                      rubric_ids=self.id,
                                      offset=self.offset, 
                                      limit=limit)
        if not data: 
            return False
        self.data = data['data']
        return True

    def _build_down(self, Dir, lvl, whiteFlag, blackFlag):
        for article in self.data['articles']['items']:
            node = Node_article(self, {'nid': article['id']})
            node.data = article
            self.add_child(node)
