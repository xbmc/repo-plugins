'''
    qobuz.node.user_playlist
    ~~~~~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from node import Flag, getNode
from inode import INode
from debug import warn, error
from gui.util import lang, getImage, getSetting
from api import api


class Node_user_playlists(INode):
    """User playlists node
        This node list playlist made by user and saved on Qobuz server
    """

    def __init__(self, parent=None, parameters=None):
        super(Node_user_playlists, self).__init__(parent, parameters)
        self.label = lang(30021)
        self.image = getImage('userplaylists')
        self.nt = Flag.USERPLAYLISTS
        self.content_type = 'files'
        display_by = self.get_parameter('display-by')
        if not display_by:
            display_by = 'songs'
        self.set_display_by(display_by)
        display_cover = getSetting('userplaylists_display_cover', isBool=True)
        self.display_product_cover = display_cover
        self.offset = self.get_parameter('offset') or 0

    def set_display_by(self, dtype):
        vtype = ('product', 'songs')
        if not dtype in vtype:
            error(self, "Invalid display by: " + dtype)
        self.display_by = dtype

    def get_display_by(self):
        return self.display_by

    def set_current_playlist_id(self, playlist_id):
        userdata = self.get_user_storage()
        userdata['current_playlist'] = int(playlist_id)
        userdata.sync()

    def get_current_playlist_id(self):
        userdata = self.get_user_storage()
        if not 'current_playlist' in userdata:
            return None
        return int(userdata['current_playlist'])

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = api.get('/playlist/getUserPlaylists', limit=limit,
                       offset=self.offset, user_id=api.user_id)
        if not data:
            warn(self, "Build-down: Cannot fetch user playlists data")
            return False
        self.data = data
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        login = getSetting('username')
        cid = self.get_current_playlist_id()
        for data in self.data['playlists']['items']:
            node = getNode(Flag.PLAYLIST, {'offset': 0})
            node.data = data
            if self.display_product_cover:
                pass
            if (cid and cid == node.nid):
                node.set_is_current(True)
            if node.get_owner() == login:
                node.set_is_my_playlist(True)
            self.add_child(node)
        return True
