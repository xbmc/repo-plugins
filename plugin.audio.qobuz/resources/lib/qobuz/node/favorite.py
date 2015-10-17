'''
    qobuz.node.favorite
    ~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import xbmcgui  # @UnresolvedImport
from inode import INode
from debug import warn
from gui.util import lang, getSetting
from gui.util import getImage, notifyH, executeBuiltin, containerUpdate
from node import getNode, Flag
from renderer import renderer
from api import api
from exception import QobuzXbmcError as Qerror
from cache import cache

dialogHeading = lang(30083)


class Node_favorite(INode):
    """Displaying user favorites (track and album)
    """

    def __init__(self, parent=None, parameters=None):
        super(Node_favorite, self).__init__(parent, parameters)
        self.nt = Flag.FAVORITE

        self.name = lang(30073)
        self.image = getImage('favorites')
        self.method = self.get_parameter('nm')
        self.search_type = self.get_parameter('search-type')
        self.content_type = 'files'
        if self.search_type == 'all':
            self.search_type = None
        elif self.search_type == 'albums':
            self.content_type = 'albums'
        elif self.search_type == 'tracks':
            self.content_type = 'files'
        elif self.search_type == 'artists':
            self.content_type = 'artists'
        if self.search_type is None:
            self.label = '%s - %s' % (lang(30081), lang(30098))
        else:
            self.label = '%s - %s' % (lang(30081),
                                      self.search_type.capitalize())
        self.offset = self.get_parameter('offset') or 0

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = None
        if self.search_type != 'all':
            data = api.get('/favorite/getUserFavorites',
                           user_id=api.user_id,
                           type=self.search_type,
                           limit=limit,
                           offset=self.offset)
        else:
            data = api.get('/favorite/getUserFavorites',
                           user_id=api.user_id,
                           limit=limit,
                           offset=self.offset)
        if not data:
            warn(self, "Build-down: Cannot fetch favorites data")
            return False
        self.data = data
        return True

    def make_url(self, **ka):
        url = super(Node_favorite, self).make_url(**ka)
        if self.search_type:
            url += '&search-type=' + str(self.search_type)
        return url

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        if self.method is not None:
            return True
        ret = False
        all_kind = ('artists', 'albums', 'tracks')
        search_for = (self.search_type, )
        if self.search_type is None:
            search_for = all_kind
        for kind in search_for:
            method = '_populate_%s' % kind
            if not hasattr(self, method):
                warn(self, 'No method named %s' % method)
                continue
            if getattr(self, method)(Dir, lvl, whiteFlag, blackFlag):
                ret = True
        return ret

    def _populate_tracks(self, Dir, lvl, whiteFlag, blackFlag):
        ret = False
        if not 'tracks' in self.data:
            return False
        for track in self.data['tracks']['items']:
            node = getNode(Flag.TRACK)
            node.data = track
            self.add_child(node)
            ret = True
        return ret

    def _populate_albums(self, Dir, lvl, whiteFlag, blackFlag):
        ret = False
        if not 'albums' in self.data:
            return False
        for album in self.data['albums']['items']:
            node = getNode(Flag.ALBUM)
            node.data = album
            self.add_child(node)
            ret = True
        return ret

    def _populate_artists(self, Dir, lvl, whiteFlag, blackFlag):
        ret = False
        if not 'artists' in self.data:
            return False
        for artist in self.data['artists']['items']:
            node = getNode(Flag.ARTIST)
            node.data = artist
            node.fetch(None, None, None, Flag.NONE)
            self.add_child(node)
            ret = True
        return ret

    def get_description(self):
        return self.get_property('description')

    def gui_add_albums(self):
        qnt, qid = int(self.get_parameter('qnt')), self.get_parameter('qid')
        nodes = self.list_albums(qnt, qid)
        if len(nodes) == 0:
            notifyH(dialogHeading, lang(30143))
            return False
        ret = xbmcgui.Dialog().select(lang(30144), [
            node.get_label() for node in nodes
        ])
        if ret == -1:
            return False
        album_ids = ','.join([node.nid for node in nodes])
        if not self.add_albums(album_ids):
            notifyH(dialogHeading, 'Cannot add album(s) to favorite')
            return False
        self._delete_cache()
        notifyH(dialogHeading, 'Album(s) added to favorite')
        return True

    def gui_add_artists(self):
        qnt, qid = int(self.get_parameter('qnt')), self.get_parameter('qid')
        nodes = self.list_artists(qnt, qid)
        if len(nodes) == 0:
            notifyH(dialogHeading, lang(30143))
            return False
        ret = xbmcgui.Dialog().select(lang(30146), [
            node.get_label() for node in nodes
        ])
        if ret == -1:
            return False
        artist_ids = ','.join([str(node.nid) for node in nodes])
        if not self.add_artists(artist_ids):
            notifyH(dialogHeading, 'Cannot add artist(s) to favorite')
            return False
        self._delete_cache()
        notifyH(dialogHeading, 'Artist(s) added to favorite')
        return True

    def list_albums(self, qnt, qid):
        album_ids = {}
        nodes = []
        if qnt & Flag.ALBUM == Flag.ALBUM:
            node = getNode(Flag.ALBUM, {'nid': qid})
            node.fetch(None, None, None, None)
            album_ids[str(node.nid)] = 1
            nodes.append(node)
        elif qnt & Flag.TRACK == Flag.TRACK:
            render = renderer(qnt, self.parameters)
            render.depth = 1
            render.whiteFlag = Flag.TRACK
            render.blackFlag = Flag.NONE
            render.asList = True
            render.run()
            if len(render.nodes) > 0:
                node = getNode(Flag.ALBUM)
                node.data = render.nodes[0].data['album']
                album_ids[str(node.nid)] = 1
                nodes.append(node)
        else:
            render = renderer(qnt, self.parameters)
            render.depth = -1
            render.whiteFlag = Flag.ALBUM
            render.blackFlag = Flag.STOPBUILD & Flag.TRACK
            render.asList = True
            render.run()
            for node in render.nodes:
                if node.nt & Flag.ALBUM:
                    if not str(node.nid) in album_ids:
                        album_ids[str(node.nid)] = 1
                        nodes.append(node)
                if node.nt & Flag.TRACK:
                    render = renderer(qnt, self.parameters)
                    render.depth = 1
                    render.whiteFlag = Flag.TRACK
                    render.blackFlag = Flag.NONE
                    render.asList = True
                    render.run()
                    if len(render.nodes) > 0:
                        newnode = getNode(Flag.ALBUM)
                        newnode.data = render.nodes[0].data['album']
                        if not str(newnode.nid) in album_ids:
                            nodes.append(newnode)
                            album_ids[str(newnode.nid)] = 1
        return nodes

    def add_albums(self, album_ids):
        ret = api.favorite_create(album_ids=album_ids)
        if not ret:
            return False
        self._delete_cache()
        return True

    def add_artists(self, artist_ids):
        ret = api.favorite_create(artist_ids=artist_ids)
        if not ret:
            return False
        self._delete_cache()
        return True

    def gui_add_tracks(self):
        qnt, qid = int(self.get_parameter('qnt')), self.get_parameter('qid')
        nodes = self.list_tracks(qnt, qid)
        if len(nodes) == 0:
            # ERROR: Missing translation for 3600
            notifyH(dialogHeading, lang(3600))
            return False
        ret = xbmcgui.Dialog().select(lang(30145), [
            node.get_label() for node in nodes
        ])
        if ret == -1:
            return False
        track_ids = ','.join([str(node.nid) for node in nodes])
        if not self.add_tracks(track_ids):
            notifyH(dialogHeading, 'Cannot add track(s) to favorite')
            return False
        self._delete_cache()
        notifyH(dialogHeading, 'Track(s) added to favorite')
        return True

    def list_tracks(self, qnt, qid):
        track_ids = {}
        nodes = []
        if qnt & Flag.TRACK == Flag.TRACK:
            node = getNode(Flag.TRACK, {'nid': qid})
            node.fetch(None, None, None, Flag.NONE)
            track_ids[str(node.nid)] = 1
            nodes.append(node)
        else:
            render = renderer(qnt, self.parameters)
            render.depth = -1
            render.whiteFlag = Flag.TRACK
            render.asList = True
            render.run()
            for node in render.nodes:
                if not str(node.nid) in track_ids:
                    nodes.append(node)
                    track_ids[str(node.nid)] = 1
        return nodes

    def list_artists(self, qnt, qid):
        artist_ids = {}
        nodes = []
        if qnt & Flag.ARTIST == Flag.ARTIST:
            node = getNode(Flag.ARTIST, {'nid': qid})
            node.fetch(None, None, None, Flag.NONE)
            artist_ids[str(node.nid)] = 1
            nodes.append(node)
        else:
            render = renderer(qnt, self.parameters)
            render.depth = -1
            render.whiteFlag = Flag.ALBUM & Flag.TRACK
            render.blackFlag = Flag.TRACK & Flag.STOPBUILD
            render.asList = True
            render.run()
            for node in render.nodes:
                artist = getNode(Flag.ARTIST, {'nid': node.get_artist_id()})
                if not artist.fetch(None, None, None, Flag.NONE):
                    continue
                if not str(artist.nid) in artist_ids:
                    nodes.append(artist)
                    artist_ids[str(artist.nid)] = 1
        return nodes

    def add_tracks(self, track_ids):
        ret = api.favorite_create(track_ids=track_ids)
        if not ret:
            return False
        self._delete_cache()
        return True

    def _delete_cache(self):
        limit = getSetting('pagination_limit')
        keys = []
        keys.append(cache.make_key('/favorite/getUserFavorites',
                                   user_id=api.user_id,
                                   limit=limit,
                                   offset=self.offset))
        for kind in ['artists', 'albums', 'tracks']:
            keys.append(cache.make_key('/favorite/getUserFavorites',
                                       user_id=api.user_id,
                                       limit=limit,
                                       type=kind,
                                       offset=self.offset))
        ret = False
        for key in keys:
            if cache.delete(key):
                ret = True
        return ret

    def del_track(self, track_id):
        if api.favorite_delete(track_ids=track_id):
            self._delete_cache()
            return True
        return False

    def del_album(self, album_id):
        if api.favorite_delete(album_ids=album_id):
            self._delete_cache()
            return True
        return False

    def del_artist(self, artist_id):
        if api.favorite_delete(artist_ids=artist_id):
            self._delete_cache()
            return True
        return False

    def gui_remove(self):
        qnt, qid = int(self.get_parameter('qnt')), self.get_parameter('qid')
        node = getNode(qnt, {'nid': qid})
        ret = None
        if qnt & Flag.TRACK == Flag.TRACK:
            ret = self.del_track(node.nid)
        elif qnt & Flag.ALBUM == Flag.ALBUM:
            ret = self.del_album(node.nid)
        elif qnt & Flag.ARTIST == Flag.ARTIST:
            ret = self.del_artist(node.nid)
        else:
            raise Qerror(who=self, what='invalid_node_type',
                         additional=self.nt)
        if not ret:
            notifyH(dialogHeading,
                    'Cannot remove item: %s' % (node.get_label()))
            return False
        notifyH(dialogHeading,
                'Item successfully removed: %s' % (node.get_label()))
        url = self.make_url(nt=self.nt, nid='', nm='')
        executeBuiltin(containerUpdate(url, True))
        return True
