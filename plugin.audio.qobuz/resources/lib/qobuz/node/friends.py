'''
    qobuz.node.friend_list
    ~~~~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
from inode import INode
from debug import info, warn
from gui.util import getImage, runPlugin, containerUpdate, lang
from api import api
from node import getNode, Flag


class Node_friends(INode):
    """@class Node_friend_list:
    """

    def __init__(self, parent=None, parameters=None):
        super(Node_friends, self).__init__(parent, parameters)
        self.nt = Flag.FRIENDS
        self.name = self.get_parameter('query')
        self.image = getImage('artist')
        self.label = str(self.name) + lang(30179) if (
            self.name) else lang(30180)
        self.url = None
        self.is_folder = True
        self.content_type = 'artists'

    def make_url(self, **ka):
        url = super(Node_friends, self).make_url(**ka)
        if self.name:
            url += "&query=" + self.name
        return url

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        node = getNode(Flag.FRIEND)
        node.create('qobuz.com')
        return True

    def populate(self, xbmc_directory, lvl, whiteFlag, blackFlag):
        username = api.username
        password = api.password
        user_id = api.user_id
        user_data = api.get('/user/login', username=username,
                            password=password)
        if not 'user' in user_data:
            return False
        friend_data = user_data['user']['player_settings']['friends']
        info(self, "Build-down friends list " + repr(self.name))
        if self.name:
            data = api.get('/playlist/getUserPlaylists',
                           username=self.name, limit=0)
        else:
            data = api.get('/playlist/getUserPlaylists',
                           user_id=user_id, limit=0)
        if not data:
            warn(self, "No friend data")
            return False
        # extract all owner names from the list
        friend_list = []
        for item in data['playlists']['items']:
            if item['owner']['name'] == user_data['user']['login']:
                continue
            friend_list.append(item['owner']['name'])
        # add previously stored
        if (not self.name):
            for name in friend_data:
                friend_list.append(str(name))
        # remove duplicates
        keys = {}
        for e in friend_list:
            keys[e] = 1
        friend_list = keys.keys()
        # and add them to the directory
        for name in friend_list:
            node = getNode(Flag.FRIEND, {'query': str(name)})
            if name == self.name:
                continue
            if name in friend_data:
                node.label = 'Friend / %s' % (node.label)
            self.add_child(node)

    def attach_context_menu(self, item, menu):
        label = self.get_label()
        url = self.make_url()
        menu.add(path='friend', label=label, cmd=containerUpdate(url))
        url = self.make_url(nt=Flag.FRIEND, nm='gui_create', nid=self.nid)
        menu.add(path='friend/add', label=lang(30181), cmd=runPlugin(url))
        super(Node_friends, self).attach_context_menu(item, menu)
