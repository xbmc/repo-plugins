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

import qobuz
from constants import Mode
from flag import NodeFlag as Flag
from inode import INode
from debug import info, warn
from exception import QobuzXbmcError
from gui.util import notifyH, color, lang, getImage, runPlugin, \
    containerRefresh, containerUpdate, executeBuiltin, getSetting
from util import  getNode
from renderer import renderer
from gui.contextmenu import contextMenu
from api import api

'''
    @class Node_playlist:
'''
from track import Node_track

registryKey = 'user-playlist'
registryCplID = 'user-current-playlist-id'

dialogHeading = 'Qobuz playlist'

class Node_playlist(INode):

    def __init__(self, parent=None, parameters=None, progress=None):
        super(Node_playlist, self).__init__(parent, parameters)
        self.type = Flag.PLAYLIST
        self.label = "Playlist"
        self.current_playlist_id = None
        self.b_is_current = False
        self.is_my_playlist = False
        self.url = None
        self.is_folder = True
        self.packby = ''
        if self.packby == 'album':
            self.content_type = 'albums'
        else:
            self.content_type = 'songs'
        self.offset = self.get_parameter('offset') or 0
        self.image = getImage('song')

    def get_label(self):
        return self.get_name() or self.label

    def set_is_my_playlist(self, b):
        self.is_my_playlist = b

    def set_is_current(self, b):
        self.b_is_current = b

    def is_current(self):
        return self.b_is_current

    def hook_post_data(self):
        if not self.data:
            return
        self.id = self.get_property('id')
        self.label = self.get_name() or 'No name...'
        
    def pre_build_down(self, Dir, lvl, whiteFlag, blackFlag):
        limit = getSetting('pagination_limit')
        data = qobuz.registry.get(
            name=registryKey, id=self.id, playlist_id=self.id, 
            offset=self.offset, limit=limit, extra='tracks')
        if not data:
            warn(self, "Build-down: Cannot fetch playlist data")
            return False
        self.data = data['data']
        return True
    
    def _build_down(self, Dir, lvl, whiteFlag, blackFlag):
        for track in self.data['tracks']['items']:
            node = Node_track()
            node.data = track
            self.add_child(node)
        return True
        
    def get_name(self):
        name = self.get_property('name') 
        if name: return name
        name = self.get_property('title')
        if name: return name
        return ''
    
    def get_owner(self):
        return self.get_property('owner/name')

    def get_owner_id(self):
        return self.get_property('owner/id')

    def get_description(self):
        return self.get_property('description')

    def makeListItem(self, replaceItems=False):
        colorItem = getSetting('color_item')
        colorPl = getSetting('color_item_playlist')
        label = self.get_name()
        image = self.get_image()
        owner = self.get_owner()
        url = self.make_url()
        if self.b_is_current:
            label = ''.join(('-o] ', color(colorItem, label), ' [o-'))
        if not self.is_my_playlist:
            label = color(colorItem, owner) + ' - ' + self.get_name()
        label = color(colorPl, label)
        item = xbmcgui.ListItem(label,
                                owner,
                                image,
                                image,
                                url)
        if not item:
            warn(self, "Error: Cannot make xbmc list item")
            return None
        item.setPath(url)
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), replaceItems)
        return item

    def attach_context_menu(self, item, menu):
        login = getSetting('username')
        isOwner = True
        if login != self.get_property('owner/name'):
            isOwner = False
        label = self.get_label()
        
        if isOwner:
            url = self.make_url(type=Flag.PLAYLIST, mode=Mode.VIEW,
                                nm='set_as_current')
            menu.add(path='playlist/set_as_current', label=lang(39007), 
                    cmd=containerUpdate(url))

            url = self.make_url(type=Flag.PLAYLIST, nm='gui_rename')
            menu.add(path='playlist/rename', label=lang(39009), 
                        cmd=runPlugin(url))

        else:
            url = self.make_url(type=Flag.PLAYLIST, nm='subscribe')
            menu.add(path='playlist/subscribe', label=lang(39012), 
                    cmd=runPlugin(url))

        url = self.make_url(type=Flag.PLAYLIST, nm='gui_remove')
        menu.add(path='playlist/remove', label=lang(39010), 
                 cmd=runPlugin(url))

        ''' Calling base class '''
        super(Node_playlist, self).attach_context_menu(item, menu)

    def remove_tracks(self, tracks_id):
        info(self, "Removing tracks: " + tracks_id)
        qobuz.registry.get(name='user')
        result = api.playlist_deleteTracks(
            playlist_id=self.id, playlist_track_ids=tracks_id)
        if not result:
            return False
        return True

    def gui_remove_track(self):
        qid = self.get_parameter('qid')
        print "Removing track %s from playlist %s" % (qid, self.id)
        if not self.remove_tracks(qid):
            notifyH(dialogHeading, 'Cannot remove track!', 'icon-error-256')
            return False
        self.delete_cache(self.id)
        print "Error API: %s (%s)" % (api.error, api.status_code)
        notifyH(dialogHeading, 'Track removed from playlist')
        executeBuiltin(containerRefresh())
        return True
    
    def gui_add_to_current(self):
        cpl = qobuz.registry.get(name=registryCplID)
        if not cpl or not cpl['data']:
            notifyH('Qobuz', "No current playlist")
            warn(self, "No current playlist")
            return False
        cid = cpl['data']
        qnt = int(self.get_parameter('qnt'))
        qid = self.get_parameter('qid')
        nodes = []
        if qnt & Flag.SEARCH:
            self.del_parameter('query')
        if qnt & Flag.TRACK == Flag.TRACK:
            node = getNode(qnt, {'nid': qid})
            node.pre_build_down(None, None, None, Flag.NONE)
            nodes.append(node)
        else:
            render = renderer(qnt, self.parameters)
            render.depth = -1
            render.whiteFlag = Flag.TRACK
            render.asList = True
            render.run()
            nodes = render.nodes
        ret = xbmcgui.Dialog().select('Add to current playlist', [
           node.get_label() for node in nodes                              
        ])
        if ret == -1:
            return False
        ret = self._add_tracks(cid, nodes)
        if not ret:
            notifyH('Qobuz', 
                'Failed to add tracks') 
            return False
        self.delete_cache(cid)
        notifyH('Qobuz / Tracks added', 
                '%s added' % (len(nodes))) 
        return True
           
    def _add_tracks(self, playlist_id, nodes):
        if len(nodes) < 1:
            warn(self, 'Empty list...')
            return False
        strtracks=''
        for node in nodes:
            if node.type != Flag.TRACK:
                warn(self, "Not a Node_track node")
                continue
            strtracks+='%s,' % (str(node.id))
        return api.playlist_addTracks(
            playlist_id=playlist_id, track_ids=strtracks)

    def gui_add_as_new(self, name=None):
        nodes = []
        qnt = int(self.get_parameter('qnt'))
        qid = self.get_parameter('qid')
        if qnt & Flag.SEARCH:
            self.del_parameter('query')
        if qnt & Flag.TRACK == Flag.TRACK:
            # print "Adding one track"
            node = getNode(qnt, {'nid': qid})
            node.pre_build_down(None,None,None, Flag.NONE)
            nodes.append(node)
        else:
            render = renderer(qnt, self.parameters)
            render.depth = -1
            render.whiteFlag = Flag.TRACK
            render.asList = True
            render.run()
            nodes = render.nodes
            if not name and render.root.get_parameter('query', unQuote=True):
                name = render.root.get_parameter('query', unQuote=True)
        if not name:
            name = self.get_parameter('query', 
                                      unQuote=True) or self.get_label()
        ret = xbmcgui.Dialog().select('Create playlist %s' % (name), [
           node.get_label() for node in nodes                              
        ])
        if ret == -1:
            return False
        playlist = self.create(name)
        if not playlist:
            notifyH('Qobuz', 'Playlist creationg failed', 'icon-error-256')
            warn(self, "Cannot create playlist...")
            return False
        if not self._add_tracks(playlist['id'], nodes):
            notifyH('Qobuz / Cannot add tracks', 
                    "%s" % (name), 'icon-error-256')
            return False
        self.delete_cache(playlist['id'])
        notifyH('Qobuz / Playlist added', 
                '[%s] %s' % (len(nodes), name)) 
        return True
    
    def set_as_current(self, nid = None):
        if not nid: nid = self.id
        if not nid:
            raise QobuzXbmcError(who=self, what='node_without_id')
        qobuz.registry.set(
            name=registryCplID, id=0, value=nid)
        return True

    '''
        Rename playlist
    '''
    def gui_rename(self, ID = None):
        if not ID:
            ID = self.id
        if not ID:
            warn(self, "Can't rename playlist without id")
            return False
        from gui.util import Keyboard
        offset = self.get_parameter('offset') or 0
        limit = getSetting('pagination_limit')
        info(self, "renaming playlist: " + str(ID))
        playlist = qobuz.registry.get(
            name=registryKey, id=ID, playlist_id=ID, offset=offset, limit=limit)
        self.data = playlist['data']
        if not playlist:
            warn(self, "Something went wrong while renaming playlist")
            return False
        currentname = self.get_name()
        k = Keyboard(currentname, lang(30078))
        k.doModal()
        if not k.isConfirmed():
            return False
        newname = k.getText()
        newname = newname.strip()
        if not newname:
            notifyH(dialogHeading, "Don't u call ure child something?", 
                    'icon-error-256')
            return False
        if newname == currentname:
            return True
        res = api.playlist_update(playlist_id=ID, name=newname)
        if not res:
            warn(self, "Cannot rename playlist with name %s" % (newname) )
            return False
        self.delete_cache(ID)
        notifyH(lang(30078), (u"%s: %s") % (lang(39009), currentname))
        executeBuiltin(containerRefresh())
        return True
    
    def create(self, name, isPublic=True, isCollaborative=False):
        return api.playlist_create(name=name, 
                                        is_public=isPublic, 
                                        is_collaborative=isCollaborative)
    
    def gui_create(self):
        query = self.get_parameter('query', unQuote=True)
        #!TODO: Why we are no more logged ...
        qobuz.registry.get(name='user')
        if not query:
            from gui.util import Keyboard
            k = Keyboard('', lang(42000))
            k.doModal()
            if not k.isConfirmed():
                warn(self, 'Creating playlist aborted')
                return None
            query = k.getText()
        ret = self.create(query)
        if not ret:
            warn(self, "Cannot create playlist named '" + query + "'")
            return None
        self.set_as_current(ret['id'])
        qobuz.registry.delete(name='user-playlists')
        qobuz.registry.delete(name='user-playlist', id=ret['id'])
        url = self.make_url(type=Flag.USERPLAYLISTS, nt='')
        executeBuiltin(containerUpdate(url))
        return ret['id']

    '''
        Remove playlist
    '''
    def gui_remove(self):
        import xbmcgui
        import xbmc
        cpl = qobuz.registry.get(name=registryCplID)
        ID = int(self.get_parameter('nid'))
        login = getSetting('username')
        offset = self.get_parameter('offset') or 0
        limit = getSetting('pagination_limit')
        data = qobuz.registry.get(
            name=registryKey, id=ID, playlist_id=ID, offset=offset, 
            limit=limit)['data']
        name = ''
        if 'name' in data:
            name = data['name']
        ok = xbmcgui.Dialog().yesno(lang(39010),
                                    lang(30052),
                                    color('FFFF0000', name))
        if not ok:
            info(self, "Deleting playlist aborted...")
            return False
        res = False
        if data['owner']['name'] == login:
            info(self, "Deleting playlist: " + str(ID))
            res = api.playlist_delete(playlist_id=ID)
        else:
            info(self, 'Unsuscribe playlist' + str(ID))
            res = api.playlist_unsubscribe(playlist_id=ID)
        if not res:
            warn(self, "Cannot delete playlist with id " + str(ID))
            notifyH(lang(42001), lang(42004) +
                    name, getImage('icon-error-256'))
            return False
        self.delete_cache(ID)
        if cpl and cpl['data'] == ID:
            qobuz.registry.delete(name=registryCplID)
        notifyH(lang(42001), (lang(42002) + "%s" + lang(42003)) % (name))
        url = self.make_url(type=Flag.USERPLAYLISTS, mode=Mode.VIEW, nm='', 
                            nid='', nt='')
        executeBuiltin(containerUpdate(url, True))
        return False
    
    def subscribe(self):
        ID = self.id
        if api.playlist_subscribe(playlist_id=ID):
            from gui.util import notifyH, isFreeAccount, lang
            notifyH(lang(42001), lang(42005))
            qobuz.registry.delete(name='user-playlists')
            return True
        else:
            return False

    def delete_cache(self, ID):
        qobuz.registry.delete(name=registryKey, id=ID)
        qobuz.registry.delete(name='user-playlists')
        