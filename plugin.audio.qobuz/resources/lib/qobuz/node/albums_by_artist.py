'''
    qobuz.node.albums_by_artist
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import xbmcgui  # @UnresolvedImport
from inode import INode
from debug import warn
import weakref
from api import api
from gui.contextmenu import contextMenu
from gui.util import getSetting
from node import getNode, Flag


class Node_albums_by_artist(INode):
    """@class Node_product_by_artist:
    """

    def __init__(self, parent=None, parameters=None):
        super(Node_albums_by_artist, self).__init__(parent, parameters)
        self.nt = Flag.ALBUMS_BY_ARTIST
        self.content_type = 'albums'
        self.offset = self.get_parameter('offset') or 0

    def get_label(self):
        return self.get_artist()

    def get_image(self):
        image = self.get_property('picture')
        # get max size image from lastfm
        # Qobuz default is a crappy 126p large one
        # perhaps we need a setting for low bw users
        image = image.replace('126s', '_')
        return image

    def get_artist(self):
        return self.get_property('name')

    def get_slug(self):
        return self.get_property('slug')

    def get_artist_id(self):
        return self.nid

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = api.get('/artist/getSimilarArtist', artist_id=self.nid,
                       limit=limit, offset=self.offset, extra='albums')
        if not data:
            warn(self, "Cannot fetch albums for artist: " + self.get_label())
            return False
        self.data = data
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        count = 0
        total = len(self.data['albums']['items'])
        for album in self.data['albums']['items']:
            keys = ['artist', 'interpreter', 'composer', 'performer']
            for k in keys:
                try:
                    if k in self.data['artist']:
                        album[k] = weakref.proxy(self.data['artist'][k])
                except:
                    warn(self, "Strange thing happen")
                    pass
            node = getNode(Flag.ALBUM)
            node.data = album
            count += 1
            Dir.update(count, total, "Add album:" + node.get_label(), '')
            self.add_child(node)
        return True

    def makeListItem(self, replaceItems=False):
        item = xbmcgui.ListItem(self.get_label(),
                                self.get_label(),
                                self.get_image(),
                                self.get_image(),
                                self.make_url(),
                                )
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), replaceItems)
        return item
