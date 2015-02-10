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
import xbmcgui
import xbmc
import json

from inode import INode
from debug import warn
from gui.util import color, getImage, runPlugin, containerRefresh, \
    containerUpdate, notifyH, executeBuiltin, getSetting, lang
from api import api
from cache import cache

from node import Flag, getNode

class Node_friend(INode):
    '''
    @class Node_friend:
    '''

    def __init__(self, parent=None, parameters=None):
        super(Node_friend, self).__init__(parent, parameters)
        self.nt = Flag.FRIEND
        self.image = getImage('artist')
        self.name = ''
        self.set_name(self.get_parameter('query'))
        self.set_label(self.name)
        self.url = None
        self.is_folder = True

    def set_label(self, label):
        colorItem = getSetting('color_item')
        self.label = color(colorItem, label)

    def set_name(self, name):
        self.name = name or ''
        self.set_label(self.name)
        return self

    def make_url(self, **ka):
        url = super(Node_friend, self).make_url(**ka) + "&query=" + self.name
        return url

    def gui_create(self):
        name = self.get_parameter('query')
        if not name:
            from gui.util import Keyboard
            kb = Keyboard('', 
                          str(lang(41102)))
            kb.doModal()
            name = ''
            if not kb.isConfirmed():
                return False
            name = kb.getText().strip()
        if not name:
            return False
        if not self.create(name):
            notifyH('Qobuz', 'Cannot add friend %s' % (name))
            return False
        notifyH('Qobuz', 'Friend %s added' % (name))
        return True
    
    def create(self, name=None):
        username = api.username
        password = api.password
        friendpl = api.get('/playlist/getUserPlaylists', username=name)
        if not friendpl:
            return False
        user = api.get('/user/login', username=username, password=password)
        if user['user']['login'] == name:
            return False
        if not user:
            return False
        friends = user['user']['player_settings']
        if not 'friends' in friends:
            friends = []
        else:
            friends = friends['friends']
        if name in friends:
            return False
        friends.append(name)
        newdata = {'friends': friends}
        #easyapi.get(name='user')
        if not api.user_update(player_settings=json.dumps(newdata)):
            return False
#        qobuz.registry.delete(name='user')
        executeBuiltin(containerRefresh())
        return True

    def delete_cache(self):
        key = cache.make_key('/user/login', username=api.username, 
                             password=api.password)
        cache.delete(key)
        
    def remove(self):
        name = self.get_parameter('query')
        if name == 'qobuz.com':
            return False
        if not name:
            return False
        user = self.get_user_data()
        if not user:
            return False
        friends = user['player_settings']
        if not 'friends' in friends:
            notifyH('Qobuz', "You don't have friend", 
                    'icon-error-256')
            warn(self, "No friends in user/player_settings")
            return False
        friends = friends['friends']
        if not name in friends:
            notifyH('Qobuz', "You're not friend with %s" % (name), 
                    'icon-error-256')
            warn(self, "Friend " + repr(name) + " not in friends data")
            return False
        del friends[friends.index(name)]
        newdata = {'friends': friends}
        if not api.user_update(player_settings=json.dumps(newdata)):
            notifyH('Qobuz', 'Friend %s added' % (name))
            notifyH('Qobuz', "Cannot updata friend's list...", 
                    'icon-error-256')
            return False
        notifyH('Qobuz', 'Friend %s removed' % (name))
        self.delete_cache()
        executeBuiltin(containerRefresh())
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        data = api.get('/playlist/getUserPlaylists', username=self.name)
        if not data:
            warn(self, "No friend data")
            return False
        if lvl != -1:
            self.add_child(getNode(Flag.FRIEND_LIST, self.parameters))
        for pl in data['playlists']['items']:
            node = getNode(Flag.PLAYLIST)
            node.data = pl
            if node.get_owner() == self.label:
                self.nid = node.get_owner_id()
            self.add_child(node)
        return True

    def attach_context_menu(self, item, menu):
        colorWarn = getSetting('item_caution_color')
        url=self.make_url()
        menu.add(path='friend', label=self.name, cmd=containerUpdate(url))
        cmd = runPlugin(self.make_url(nt=Flag.FRIEND, nm="remove"))
        menu.add(path='friend/remove', label='Remove', cmd=cmd, 
                 color=colorWarn)

        ''' Calling base class '''
        super(Node_friend, self).attach_context_menu(item, menu)
