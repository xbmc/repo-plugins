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

from exception import QobuzXbmcError
from debug import warn

class __NodeFlag():
    def __init__(self):
        self.NODE = 1 << 1
        self.TRACK = 1 << 2
        self.PLAYLIST = 1 << 3
        self.USERPLAYLISTS = 1 << 4
        self.RECOMMENDATION = 1 << 5
        self.ROOT = 1 << 6
        self.PRODUCT = 1 << 7
        self.PURCHASES = 1 << 8
        self.SEARCH = 1 << 9
        self.ARTIST = 1 << 10
        self.SIMILAR_ARTIST = 1 << 11
        self.FAVORITES = 1 << 12
        self.FRIEND = 1 << 13
        self.FRIEND_LIST = 1 << 14
        self.GENRE = 1 << 15
        self.LABEL = 1 << 16
        self.PRODUCTS = 1 << 17
        self.ARTICLES = 1 << 18
        self.ARTICLE = 1 << 19
        self.ARTICLE_RUBRICS = 1 << 20
        
        self.STOPBUILD = 1 <<  100
        self.NONE = 1 << 101
        
        
        self.totalFlag = 20
        self.ALL = 0
        for i in range(1, self.totalFlag+1):
            self.ALL |= (1 << i)
        
    def to_s(self, flag):
        if not flag:
            warn(self, "Missing flag parameter")
            return ''
        flag = int(flag)
        if flag & self.TRACK == self.TRACK:
            return "track"
        elif flag & self.PLAYLIST == self.PLAYLIST:
            return "playlist"
        elif flag & self.USERPLAYLISTS == self.USERPLAYLISTS:
            return "user_playlists"
        elif flag & self.RECOMMENDATION == self.RECOMMENDATION:
            return "recommendation"
        elif flag & self.ROOT == self.ROOT:
            return "root"
        elif flag & self.PRODUCT == self.PRODUCT:
            return "product"
        elif flag & self.PURCHASES == self.PURCHASES:
            return "purchases"
        elif flag & self.FAVORITES == self.FAVORITES:
            return "favorites"
        elif flag & self.SEARCH == self.SEARCH:
            return "search"
        elif flag & self.ARTIST == self.ARTIST:
            return "artist"
        elif flag & self.SIMILAR_ARTIST == self.SIMILAR_ARTIST:
            return "similar_artist"
        elif flag & self.FRIEND == self.FRIEND:
            return "friend"
        elif flag & self.FRIEND_LIST == self.FRIEND_LIST:
            return "friend_list"
        elif flag & self.GENRE == self.GENRE:
            return "genre"
        elif flag & self.LABEL == self.LABEL:
            return "label"
        elif flag & self.NODE == self.NODE:
            return "inode"
        elif flag & self.PRODUCTS == self.PRODUCTS:
            return "products"
        elif flag & self.STOPBUILD == self.STOPBUILD:
            return "stop_build_down"
        elif flag & self.ARTICLES == self.ARTICLES:
            return "articles"
        elif flag & self.ARTICLE == self.ARTICLE:
            return "article"
        elif flag & self.ARTICLE_RUBRICS == self.ARTICLE_RUBRICS:
            return "article_rubrics"
        else:
            raise QobuzXbmcError(
                who=self, what='invalid_flag', additional=repr(flag))
            
NodeFlag = __NodeFlag()
