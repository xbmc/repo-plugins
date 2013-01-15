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

import qobuz
from flag import NodeFlag as Flag
from inode import INode
from playlist import Node_playlist
from debug import warn
from gui.util import color, getImage, runPlugin, containerRefresh, \
    containerUpdate, notifyH, executeBuiltin, getSetting, lang
from api import api
'''
    @class Node_friend:
'''

class Node_friend(INode):

    def __init__(self, parent=None, parameters=None, progress=None):
        super(Node_friend, self).__init__(parent, parameters)
        self.type = Flag.FRIEND
        self.image = getImage('artist')
        self.name = ''
        self.set_name(self.get_parameter('name'))
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
        url = super(Node_friend, self).make_url(**ka) + "&name=" + self.name
        return url

    def create(self, name=None):
        if not name:
            from gui.util import Keyboard
            kb = Keyboard(str(self.get_parameter('name')), 
                          str(lang(41102)))
            kb.doModal()
            name = ''
            if not kb.isConfirmed():
                warn(self, 'Nothing to do')
                return False
            name = kb.getText()
        friendpl = qobuz.registry.get(
            name='user-playlists', username=name, id=name)['data']
        if not friendpl:
            return False
        user = qobuz.registry.get(name='user')
        if not user:
            return False
        friends = user['data']['user']['player_settings']
        if not 'friends' in friends:
            friends = []
        else:
            friends = friends['friends']
        if name in friends:
            notifyH('Qobuz', 'Already friend with %s' % (name))
            return False
        friends.append(name)
        newdata = {'friends': friends}
        qobuz.registry.get(name='user')
        if not api.user_update(player_settings=json.dumps(newdata)):
            notifyH('Qobuz', "Cannot updata friend's list...", 
                    'icon-error-256')
            return False
        notifyH('Qobuz', 'Friend %s added' % (name))
        qobuz.registry.delete(name='user')
        executeBuiltin(containerRefresh())
        return True

    def remove(self):
        name = self.get_parameter('name')
        if not name:
            return False
        user = qobuz.registry.get(name='user')
        if not user:
            return False
        friends = user['data']['user']['player_settings']
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
        qobuz.registry.delete(name='user')
        executeBuiltin(containerRefresh())
        return True

    def _build_down(self, xbmc_directory, lvl, whiteFlag, blackFlag):
        data = qobuz.registry.get(
            name='user-playlists', username=self.name, id=self.name)['data']
        if not data:
            warn(self, "No friend data")
            return False
        from friend_list import Node_friend_list
        self.add_child(Node_friend_list(self, self.parameters))
        for pl in data['playlists']['items']:
            node = Node_playlist()
            node.data = pl
            if node.get_owner() == self.label:
                self.id = node.get_owner_id()
            self.add_child(node)
        return True

    def attach_context_menu(self, item, menu):
        colorWarn = getSetting('color_item_caution')
        url=self.make_url()
        menu.add(path='friend', label=self.name, cmd=containerUpdate(url))
        cmd = runPlugin(self.make_url(type=Flag.FRIEND, nm="remove"))
        menu.add(path='friend/remove', label='Remove', cmd=cmd, 
                 color=colorWarn)

        ''' Calling base class '''
        super(Node_friend, self).attach_context_menu(item, menu)
