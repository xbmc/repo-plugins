__author__ = 'bromix'

import xbmc

from ..abstract_playlist import AbstractPlaylist
from . import kodi_items


class KodiPlaylist(AbstractPlaylist):
    def __init__(self, playlist_type, context):
        AbstractPlaylist.__init__(self)

        self._context = context
        self._playlist = None
        if playlist_type == 'video':
            self._playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            pass
        elif playlist_type == 'audio':
            self._playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
            pass
        pass

    def clear(self):
        self._playlist.clear()
        pass

    def add(self, item):
        kodi_item = kodi_items.create_kodi_item(self._context, item)
        self._playlist.add(item['uri'], listitem=kodi_item)
        pass

    def shuffle(self):
        self._playlist.shuffle()
        pass

    def unshuffle(self):
        self._playlist.unshuffle()
        pass

    pass