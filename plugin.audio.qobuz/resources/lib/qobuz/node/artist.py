'''
    qobuz.node.artist
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from inode import INode
from debug import warn
from gui.util import getSetting
from gui.contextmenu import contextMenu
from api import api
from node import getNode, Flag
'''
    @class Node_artist(Inode): Artist
'''

class Node_artist(INode):

    def __init__(self, parent=None, parameters=None):
        super(Node_artist, self).__init__(parent, parameters)
        self.nt = Flag.ARTIST
        self.set_label(self.get_name())
        self.is_folder = True
        self.slug = ''
        self.content_type = 'artists'
        self.offset = self.get_parameter('offset') or 0
        
    def hook_post_data(self):
        self.nid = self.get_property('id')
        self.name = self.get_property('name')
        self.image = self.get_image()
        self.slug = self.get_property('slug')
        self.label = self.name
        
    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = api.get('/artist/get', artist_id=self.nid, limit=limit, 
                           offset=self.offset, extra='albums')
        if not data:
            warn(self, "Build-down: Cannot fetch artist data")
            return False
        self.data = data
        return True
    
    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        node_artist = getNode(Flag.ARTIST)
        node_artist.data = self.data
        node_artist.label = '[ %s ]' % (node_artist.label)
        if not 'albums' in self.data: 
            return True
        for pData in self.data['albums']['items']:
            node = getNode(Flag.ALBUM)
            node.data = pData
            self.add_child(node)
        return True

        del self._data['tracks']

    def get_artist_id(self):
        return self.nid

    def get_image(self):
        image = self.get_property(['image/extralarge',
                                   'image/mega',
                                   'image/large',
                                   'image/medium',
                                   'image/small',
                                   'picture'])
        if image: 
            image = image.replace('126s', '_')
        return image
    
    def get_title(self):
        return self.get_name()
    
    def get_artist(self):
        return self.get_name()
    
    def get_name(self):
        return self.get_property('name')

    def get_owner(self):
        return self.get_property('owner/name')

    def get_description(self):
        return self.get_property('description')

    def makeListItem(self, replaceItems=False):
        import xbmcgui
        image = self.get_image()
        url = self.make_url()
        name = self.get_label()
        item = xbmcgui.ListItem(name,
                                name,
                                image,
                                image,
                                url)
        if not item:
            warn(self, "Error: Cannot make xbmc list item")
            return None
        item.setPath(url)
        item.setInfo('music' , infoLabels={
#            'genre': 'reggae', # self.get_genre(),
#            'year': '2000', # self.get_year(),
            'artist': self.get_artist(),           
#            'album': self.get_title(),
            'comment': self.get_description()
#           'Artist_Description': 'coucou'
        })
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), replaceItems)
        return item
