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
from inode import INode
from debug import info, warn
from gui.util import getImage, runPlugin, containerUpdate, lang
from api import api
from node import getNode, Flag

class Node_friend_list(INode):
    '''
    @class Node_friend_list:
    '''
    def __init__(self, parent=None, parameters=None):
        super(Node_friend_list, self).__init__(parent, parameters)
        self.nt = Flag.FRIEND_LIST
        self.name = self.get_parameter('query')
        self.image = getImage('artist')
        self.label = str(self.name) + lang(41100) if (
            self.name) else lang(41101)
        self.url = None
        self.is_folder = True
        self.content_type = 'artists'

    def make_url(self, **ka):
        url = super(Node_friend_list, self).make_url(**ka)
        if self.name:
            url += "&query=" + self.name
        return url

    def get_image(self):
        return ''
#        data = easyapi.get('user/login', user)
#        if not data:
#            return ''
#        return data['data']['user']['avatar']
        
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
        menu.add(path='friend/add', label='Add', cmd=runPlugin(url))

        ''' Calling base class '''
        super(Node_friend_list, self).attach_context_menu(item, menu)
