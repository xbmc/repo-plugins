'''
    qobuz.node.flag
    ~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from exception import QobuzXbmcError
from debug import warn


class FlagEnum(object):
    NODE = 1 << 1
    TRACK = 1 << 2
    PLAYLIST = 1 << 3
    USERPLAYLISTS = 1 << 4
    RECOMMENDATION = 1 << 5
    ROOT = 1 << 6
    ALBUM = 1 << 7
    PURCHASES = 1 << 8
    SEARCH = 1 << 9
    ARTIST = 1 << 10
    SIMILAR_ARTIST = 1 << 11
    FAVORITES = 1 << 12
    FRIEND = 1 << 13
    FRIENDS = 1 << 14
    GENRE = 1 << 15
    LABEL = 1 << 16
    ALBUMS = 1 << 17
    ARTICLES = 1 << 18
    ARTICLE = 1 << 19
    ARTICLE_RUBRICS = 1 << 20
    ALBUMS_BY_ARTIST = 1 << 21
    PUBLIC_PLAYLISTS = 1 << 22
    COLLECTION = 1 << 23
    COLLECTIONS = 1 << 24
    FAVORITE = 1 << 25
    PURCHASE = 1 << 26

    STOPBUILD = 1 << 100
    NONE = 1 << 101

    def __init__(self):

        self.totalFlag = 26
        self.ALL = 0
        for i in range(1, self.totalFlag + 1):
            self.ALL |= (1 << i)

    @classmethod
    def to_s(cls, flag):
        if not flag:
            warn(cls, "Missing flag parameter")
            return ''
        flag = int(flag)
        if flag & cls.TRACK == cls.TRACK:
            return "track"
        elif flag & cls.PLAYLIST == cls.PLAYLIST:
            return "playlist"
        elif flag & cls.USERPLAYLISTS == cls.USERPLAYLISTS:
            return "user_playlists"
        elif flag & cls.RECOMMENDATION == cls.RECOMMENDATION:
            return "recommendation"
        elif flag & cls.ROOT == cls.ROOT:
            return "root"
        elif flag & cls.ALBUM == cls.ALBUM:
            return "album"
        elif flag & cls.PURCHASES == cls.PURCHASES:
            return "purchases"
        elif flag & cls.PURCHASE == cls.PURCHASE:
            return "purchase"
        elif flag & cls.FAVORITES == cls.FAVORITES:
            return "favorites"
        elif flag & cls.FAVORITE == cls.FAVORITE:
            return "favorite"
        elif flag & cls.SEARCH == cls.SEARCH:
            return "search"
        elif flag & cls.ARTIST == cls.ARTIST:
            return "artist"
        elif flag & cls.SIMILAR_ARTIST == cls.SIMILAR_ARTIST:
            return "similar_artist"
        elif flag & cls.FRIEND == cls.FRIEND:
            return "friend"
        elif flag & cls.FRIENDS == cls.FRIENDS:
            return "friends"
        elif flag & cls.GENRE == cls.GENRE:
            return "genre"
        elif flag & cls.LABEL == cls.LABEL:
            return "label"
        elif flag & cls.NODE == cls.NODE:
            return "inode"
        elif flag & cls.STOPBUILD == cls.STOPBUILD:
            return "stop_build_down"
        elif flag & cls.ARTICLES == cls.ARTICLES:
            return "articles"
        elif flag & cls.ARTICLE == cls.ARTICLE:
            return "article"
        elif flag & cls.PUBLIC_PLAYLISTS == cls.PUBLIC_PLAYLISTS:
            return "public_playlists"
        elif flag & cls.ARTICLE_RUBRICS == cls.ARTICLE_RUBRICS:
            return "article_rubrics"
        elif flag & cls.ALBUMS_BY_ARTIST == cls.ALBUMS_BY_ARTIST:
            return "albums_by_artist"
        elif flag & cls.COLLECTION == cls.COLLECTION:
            return "collection"
        elif flag & cls.COLLECTIONS == cls.COLLECTIONS:
            return "collections"
        else:
            raise QobuzXbmcError(
                who=cls, what='invalid_flag', additional=repr(flag))

Flag = FlagEnum()
