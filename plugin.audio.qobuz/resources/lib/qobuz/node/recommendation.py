# -*- coding: UTF-8 -*-
'''
    qobuz.node.recommendation
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from api import api
from inode import INode
from node import getNode, Flag
from gui.util import getSetting, lang, getImage
from debug import warn

RECOS_TYPE_IDS = {
    1: 'new-releases',
    2: 'press-awards',
    3: 'best-sellers',
    4: 'editor-picks',
    5: 'most-featured',
    6: 'most-streamed'
}

RECOS_TYPES = {
    1: lang(30086),
    2: lang(30085),
    3: lang(30087),
    4: lang(30088),
    5: lang(30103),
    6: lang(30192)
}

RECOS_GENRES = {
    2: lang(30095),
    10: lang(30097),
    6: lang(30092),
    59: lang(30100),
    73: lang(30105),
    80: lang(30091),
    64: lang(30106),
    91: lang(30096),
    94: lang(30094),
    112: lang(30089),
    127: lang(30104),
    123: lang(30107),
    'null': 'All',
}


class Node_recommendation(INode):
    """Recommendation node, displaying music ordered by category and genre
    """

    def __init__(self, parent=None, parameters=None):
        super(Node_recommendation, self).__init__(parent, parameters)
        self.nt = Flag.RECOMMENDATION
        self.genre_id = self.get_parameter('genre-id')
        self.genre_type = self.get_parameter('genre-type')
        self.set_label(lang(30084))
        self.image = getImage('album')
        self.offset = self.get_parameter('offset') or 0

    def make_url(self, **ka):
        url = super(Node_recommendation, self).make_url(**ka)
        if self.genre_type:
            url += '&genre-type=' + str(self.genre_type)
        if self.genre_id:
            url += '&genre-id=' + str(self.genre_id)
        return url

    def myid(self):
        if not self.genre_id or not self.genre_type:
            return None
        return str(self.genre_type) + '-' + str(self.genre_id)

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        if not (self.genre_type and self.genre_id):
            return True
        offset = self.offset or 0
        limit = getSetting('pagination_limit')
        data = api.get('/album/getFeatured',
                       type=RECOS_TYPE_IDS[int(self.genre_type)],
                       genre_id=self.genre_id,
                       limit=limit,
                       offset=offset)
        if not data:
            warn(self, "Cannot fetch data for recommendation")
            return False
        self.data = data
        return True

    def __populate_type(self, Dir, lvl, whiteFlag, blackFlag):
        """Populate type, we don't have genre_type nor genre_id
        """
        for gid in RECOS_TYPE_IDS:
            node = getNode(Flag.RECOMMENDATION, {'genre-type': gid})
            node.set_label(
                self.label + ' - ' + RECOS_TYPES[gid])
            self.add_child(node)
        return True

    def __populate_genre(self, Dir, lvl, whiteFlag, blackFlag):
        """Populate genre, we have genre_type but no genre_id
        """
        for genre_id in RECOS_GENRES:
            node = getNode(Flag.RECOMMENDATION, {'genre-type': self.genre_type,
                                                 'genre-id': genre_id})
            label = '%s - %s / %s' % (self.label,
                                      RECOS_TYPES[int(self.genre_type)],
                                      RECOS_GENRES[genre_id])
            node.label = label
            self.add_child(node)
        return True

    def __populate_type_genre(self, Dir, lvl, whiteFlag, blackFlag):
        """Populate album selected by genre_type and genre_id
        """
        if self.data is None:
            return False
        if 'albums' not in self.data:
            warn(self, "Recommendation data doesn't contain 'albums' key")
            return False
        if self.data['albums'] is None or 'items' not in self.data['albums']:
            warn(self, "Recommendation data['albums'] doesn't contain items")
            return False
        for product in self.data['albums']['items']:
            node = getNode(Flag.ALBUM)
            node.data = product
            self.add_child(node)
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        """We are populating our node based on genre_type and genre_id
        """
        if not self.genre_type:
            return self.__populate_type(Dir, lvl, whiteFlag, blackFlag)
        elif not self.genre_id:
            return self.__populate_genre(Dir, lvl, whiteFlag, blackFlag)
        self.content_type = 'albums'
        return self.__populate_type_genre(Dir, lvl, whiteFlag, blackFlag)
